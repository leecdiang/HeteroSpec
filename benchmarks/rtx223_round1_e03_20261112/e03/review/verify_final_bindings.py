"""Independent disk/source audit. No imports of project verifiers or DLLs."""
import collections
import datetime
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent / "FINAL_BINDINGS.json"
errors = []


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(ok, message):
    if not ok:
        errors.append(message)


def hashes(base, expected):
    bad = []
    for rel, digest in expected.items():
        path = base / rel
        actual = sha(path) if path.is_file() else None
        if actual != digest:
            bad.append({"path": rel, "before_sha256": digest, "current_sha256": actual})
    return bad


def no_dangerous_defines(argv):
    # Test string-literal/header paths are not macro definitions.
    definitions = [a for a in argv if a.startswith(("-D", "/D"))]
    return not any(any(x in a for x in (
        "HS_LB_CPU_TEST_ONLY", "GGML_CUDA_USE_GRAPHS", "GGML_USE_NCCL", "GGML_CUDA_USE_PDL"
    )) for a in definitions)


report = {
    "schema": "heterospec.e03.independent-final-bindings.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "Disk bytes, recorded compiler/link commands and source receipts only; no numerical DLL load, CUDA initialization, model or GPU call",
    "reviewer_script_sha256": sha(__file__),
    "old_suites_rerun": False,
}

parent = ROOT.parent / "rtx223-round1-resume-20261112-e02"
parent_manifest = parent / "delivery/DELIVERY_MANIFEST.json"
binding = read("e03/PARENT_BINDING.json")
manifest = json.loads(parent_manifest.read_text(encoding="utf-8"))
parent_expected = {item["path"]: item["sha256"] for item in manifest["files"]}
parent_bad = hashes(parent, parent_expected)
require(sha(parent_manifest) == binding["parent_manifest_sha256"], "e02 parent manifest identity")
require(len(parent_expected) == 764 and not parent_bad, "e02 original parent files changed")
report["preserved_original_parent"] = {
    "path": str(parent), "manifest_sha256": sha(parent_manifest),
    "files_checked": len(parent_expected), "mismatches": parent_bad,
    "current_e03_copied_metadata_can_have_intentional_edits": True,
}

prep = read("runtime/SOURCE_PREPARED.json")
original_bad = hashes(pathlib.Path(prep["old_root"]), prep["old_source_sha256"])
require(len(prep["old_source_sha256"]) == 3540 and not original_bad, "original runtime core changed")
report["preserved_original_runtime_core"] = {
    "files_checked": len(prep["old_source_sha256"]), "mismatches": original_bad,
}

catalog = read("runtime/build-v1/SOURCE_IDENTITIES.json")
catalog_bad = hashes(ROOT / "runtime/source", catalog)
expected_provider = "ggml\\src\\ggml-cuda\\hs_launch_budget.cu"
require(len(catalog_bad) == 1 and catalog_bad[0]["path"] == expected_provider,
        "unexpected v1 source catalog changes")
preserved_provider = ROOT / "e03/launch_budget/cpu-checks-v1/source_snapshot/hs_launch_budget.cpp"
canonical_provider = ROOT / "e03/launch_budget/hs_launch_budget.cpp"
require(sha(preserved_provider) == catalog[expected_provider], "superseded provider body not preserved")
require(catalog_bad and catalog_bad[0]["current_sha256"] == sha(canonical_provider), "provider synchronization mismatch")
# Non-CUDA headers are not in the 283-member compile catalog. Bind their
# present contents to the independently rehashed original copied tree.
outside = {rel: digest for rel, digest in prep["old_source_sha256"].items()
           if rel.replace("/", "\\") not in catalog}
outside_bad = hashes(ROOT / "runtime/source", outside)
require(len(outside_bad) == 1 and outside_bad[0]["path"] == "ggml/src/ggml-cuda/vendors/hip.h",
        "unexpected non-catalog source differences from original")
report["v1_source_catalog"] = {
    "members": len(catalog), "current_mismatches": catalog_bad,
    "recorded_provenance_exception": "Safety actor synchronized the provider body during batch v1; exact time unrecorded, catalog 2026-11-12T09:09:38Z is approximate only; old object is not linked",
    "old_provider_preserved_sha256": sha(preserved_provider),
    "canonical_provider_sha256": sha(canonical_provider),
    "non_catalog_original_members_checked_now": len(outside),
    "non_catalog_current_differences": outside_bad,
    "limit": "No include-trace or per-compiler-invocation full dependency snapshot. This is receipt/catalog plus present source rehash, not an OS attestation that every dependency was immutable at every compile instant.",
}

final = read("runtime/FINAL_SOURCE_IDENTITIES.json")
final_bad = hashes(ROOT / "runtime/final-source", final["source_files_sha256"])
require(len(final["source_files_sha256"]) == 3546 and not final_bad, "final source manifest differs")
override = read("runtime/delta-v2/OVERRIDES.json")
override_index = {x["target_relative_path"]: x for x in override["overrides"]}
for item in outside_bad:
    require(item["path"] in override_index and
            item["current_sha256"] == override_index[item["path"]]["sha256"],
            "non-catalog source difference absent from frozen delta")
delta_bad = []
for item in override["overrides"]:
    for path in [ROOT / "runtime/delta-v2" / item["delta_relative_path"],
                 ROOT / "runtime/final-source" / item["target_relative_path"]]:
        if sha(path) != item["sha256"]:
            delta_bad.append(str(path))
require(len(override["overrides"]) == 66 and not delta_bad, "source delta mismatch")
cmake = (ROOT / "runtime/final-source/ggml/src/ggml-cuda/CMakeLists.txt").read_text()
require(cmake.count("hs_e03_runtime.cpp") == 1, "future CMake runtime implementation count")
report["uniform_future_source"] = {
    "files_checked": len(final["source_files_sha256"]), "mismatches": final_bad,
    "delta_overrides_checked": len(override["overrides"]), "delta_mismatches": delta_bad,
    "provider_body_matches_canonical": sha(ROOT / "runtime/final-source/ggml/src/ggml-cuda/hs_launch_budget.cu") == sha(canonical_provider),
    "provider_header_matches_canonical": sha(ROOT / "runtime/final-source/ggml/src/ggml-cuda/hs_launch_budget.hpp") == sha(ROOT / "e03/launch_budget/hs_launch_budget.hpp"),
    "universal_byte_identical_rebuild": False,
}

objects = read("runtime/build-v3/COMPILE_RECEIPTS.json")
old_objects = {x["object"]: x for x in read("runtime/build-v1/COMPILE_RECEIPTS.json")}
linked = read("runtime/build-v3/LINK.json")
link_object_paths = [x for x in linked["argv"] if x.lower().endswith(".obj")]
require(len(objects) == 145 and len(link_object_paths) == 145 and
        set(link_object_paths) == {x["object"] for x in objects}, "link/object exact set")
obj_bad, source_bad, policy_bad = [], [], []
for item in objects:
    if sha(item["object"]) != item["object_sha256"]:
        obj_bad.append(item["object"])
    if item["kind"] == "REUSED_EXACT_SUCCESSFUL_OBJECT":
        prior = old_objects.get(item["object"])
        require(prior is not None and prior["returncode"] == 0 and
                prior["object_sha256"] == item["object_sha256"], "reused object receipt mismatch")
        argv = prior["argv"]
        rel = str(pathlib.Path(item["source"]).relative_to(ROOT / "runtime/source"))
        if sha(item["source"]) != catalog[rel]:
            source_bad.append(item["source"])
        require(sha(prior["log"]) == prior["log_sha256"], "reused compile log mismatch")
    else:
        argv = item["argv"]
        require(item["returncode"] == 0, "fresh compiler failure")
        if sha(item["source"]) != item["source_sha256"]:
            source_bad.append(item["source"])
    if not no_dangerous_defines(argv):
        policy_bad.append(item["source"])
require(not obj_bad and not source_bad and not policy_bad, "linked object/source/compile policy mismatch")
provider_objs = [x for x in objects if pathlib.Path(x["source"]).stem == "hs_launch_budget"]
require(len(provider_objs) == 1 and provider_objs[0]["source"] == str(canonical_provider),
        "final provider is not uniquely linked canonical source")
require(sha(ROOT / "runtime/build-v3/LINK.rsp") == linked["response_sha256"], "link response mismatch")
lib_bad = [path for path, digest in linked["libraries"].items() if sha(path) != digest]
require(not lib_bad, "numerical link libraries changed")
dll = ROOT / "runtime/build-v3/bin/ggml-cuda.dll"
require(sha(dll) == "bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b", "numerical DLL bytes changed")
report["actual_numerical_link"] = {
    "DLL_sha256": sha(dll), "DLL_bytes": dll.stat().st_size,
    "objects_checked": len(objects), "kinds": dict(collections.Counter(x["kind"] for x in objects)),
    "linked_object_set_equals_receipts": set(link_object_paths) == {x["object"] for x in objects},
    "object_mismatches": obj_bad, "source_mismatches": source_bad,
    "compile_define_policy_mismatches": policy_bad, "link_library_mismatches": lib_bad,
    "final_provider_objects": len(provider_objs), "old_provider_object_excluded": True,
    "all_physical_kernel_qualification": "NOT_QUALIFIED", "normal_LoadLibrary": "NOT_RUN",
}

fs = read("e03/frontend/SOURCE_v4.json")
fb = read("e03/frontend/build-v4/BUILD.json")
front_bad = hashes(ROOT / "e03/frontend/source-v4", fs["files"])
require(not front_bad and fb["source_hashes"] == fs["files"], "frontend source binding mismatch")
require(all(x["returncode"] == 0 for x in fb["commands"]), "frontend recorded build failure")
for arm, item in fb["builds"].items():
    require(sha(item["exe"]) == item["exe_sha256"], "frontend exe mismatch: " + arm)
front_lib_bad = [path for path, digest in fb["linked_input_identities_before_and_after"].items()
                 if sha(path) != digest]
require(not front_lib_bad, "frontend link input mismatch")
preflight = read("e03/frontend/preflight-tests-v4/RESULT.json")
require(len(preflight["records"]) == 22 and all(x["passed"] for x in preflight["records"]), "frontend preflight failure")
preflight_log_bad = []
for item in preflight["records"]:
    # The producer writes one raw combined log named after each fixture.
    path = ROOT / "e03/frontend/preflight-tests-v4" / (item["name"] + ".log")
    if not path.exists() or sha(path) != item["log_sha256"]:
        preflight_log_bad.append(str(path))
require(not preflight_log_bad, "frontend raw preflight log mismatch")
identity_tests = read("e03/frontend/RECEIPT_TESTS_v2.json")
id_log_bad = [x["log"] for x in identity_tests["records"]
              if sha(ROOT / x["log"]) != x["log_sha256"]]
id_source_bad = hashes(ROOT / "e03/frontend", identity_tests["source_sha256"])
require(not id_log_bad and not id_source_bad, "frontend identity test binding mismatch")
report["frontend"] = {
    "source_members": len(fs["files"]), "source_mismatches": front_bad,
    "linked_input_mismatches": front_lib_bad,
    "compiled_preflight_cases_reported_pass": len(preflight["records"]),
    "preflight_raw_log_path_mismatches": preflight_log_bad,
    "identity_reader_cases_per_mode": [x["tests"] for x in identity_tests["records"]],
    "identity_log_mismatches": id_log_bad,
    "new_tests_rerun_by_this_script": False,
    "numeric_DLL_NormalLoad_or_GPU_qualification": "NOT_RUN",
}

report["errors"] = errors
report["passed"] = not errors
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": not errors, "errors": errors,
                  "parent_files": len(parent_expected), "runtime_final_files": len(final["source_files_sha256"]),
                  "linked_objects": len(objects), "frontend_log_path_mismatches": len(preflight_log_bad),
                  "receipt": str(OUT)}))
raise SystemExit(bool(errors))
