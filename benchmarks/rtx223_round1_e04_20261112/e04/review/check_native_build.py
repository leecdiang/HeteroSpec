"""Independent frozen native-build disk/dependency check; no project imports."""
import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def absolute(path):
    return pathlib.Path(path).resolve()


def key(path):
    return str(absolute(path)).casefold()


def open_path(path):
    result = str(absolute(path))
    if os.name == "nt" and not result.startswith("\\\\?\\"):
        result = "\\\\?\\" + result
    return result


def raw(path):
    with open(open_path(path), "rb") as stream:
        return stream.read()


def sha(path):
    h = hashlib.sha256()
    with open(open_path(path), "rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(raw(path))


def make_tokens(text):
    # Independent lexical decoding of a single Make rule side. Windows path
    # backslashes not escaping Make metacharacters remain literal characters.
    encoded = re.findall(r"(?:\\[^\r\n]|[^\s\\])+", text)
    decoded = []
    for word in encoded:
        if re.search(r"(?<!\\)#", word) or re.search(r"(?<![$\\])\$(?!\$)", word):
            raise ValueError("Unbound Make comment/variable")
        word = re.sub(r"\\([ \t#:$\\])", lambda m: m.group(1), word)
        decoded.append(word.replace("$$", "$"))
    return decoded


def make_dependencies(path, target, source):
    text = raw(path).decode("utf-8")
    if not text.endswith("\n") or "\0" in text or re.search(r"\\[ \t]*(?:\r?\n)?\Z", text):
        raise ValueError("Missing/truncated dependency recipe")
    logical = re.sub(r"\\\r?\n", " ", text).strip()
    if "\n" in logical or "\r" in logical:
        raise ValueError("Multiple Make rules")
    separators = [m.start() for m in re.finditer(r":(?=\s|$)", logical)
                  if len(re.search(r"\\*$", logical[:m.start()]).group()) % 2 == 0]
    if not separators:
        raise ValueError("No Make rule delimiter")
    position = separators[0]
    left, right = make_tokens(logical[:position]), make_tokens(logical[position + 1:])
    if len(left) != 1 or key(left[0]) != key(target) or len(right) < 2:
        raise ValueError("Wrong target or empty header closure")
    matches = [i for i, value in enumerate(right) if key(value) == key(source)]
    if matches not in ([0], [0, 1]):
        raise ValueError("Unexpected source identity/duplicate layout")
    for value in right:
        if not pathlib.Path(value).is_absolute() or any(c in value for c in "|;*?"):
            raise ValueError("Ambiguous dependency path")
    return right


parser = argparse.ArgumentParser()
parser.add_argument("--freeze", required=True)
parser.add_argument("--build", required=True)
parser.add_argument("--expected-freeze-sha256", required=True)
parser.add_argument("--link-freeze", required=True)
parser.add_argument("--link-build", required=True)
parser.add_argument("--expected-link-freeze-sha256", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
freeze_dir, build_dir = ROOT / args.freeze, ROOT / args.build
out = pathlib.Path(__file__).resolve().parent / args.out
if out.exists():
    raise ValueError("Do not overwrite independent native audit receipt")
errors = []


def need(ok, message):
    if not ok:
        errors.append(message)


freeze_path = freeze_dir / "FREEZE.json"
freeze = read(freeze_path)
need(sha(freeze_path) == args.expected_freeze_sha256, "Sealed freeze digest differs")
input_index = {key(path): item for path, item in freeze["inputs"].items()}
need(len(input_index) == len(freeze["inputs"]), "Casefold duplicate freeze members")
input_bad = []
for path, item in freeze["inputs"].items():
    if not absolute(path).is_relative_to(ROOT):
        input_bad.append({"path": path, "reason": "input outside isolated study"})
    elif sha(path) != item["sha256"]:
        input_bad.append({"path": path, "reason": "SHA256 mismatch"})
need(not input_bad, "Frozen input bytes differ")

commands = read(freeze_dir / "COMMANDS.json")
env = read(freeze_dir / "ENVIRONMENT.json")
source_root = pathlib.Path(freeze["copy_inventory"][0]["destination"])
old = ROOT.parent / "rtx223-round1-resume-20261112-e03"
source_expected = read(old / "runtime/FINAL_SOURCE_IDENTITIES.json")["source_files_sha256"]
source_bad = [rel for rel, digest in source_expected.items()
              if input_index.get(key(source_root / rel), {}).get("sha256") != digest]
need(len(source_expected) == 3546 and not source_bad, "Complete source identity differs from canonical e03 tree")
need(len(commands) == 145 and len({x["object"] for x in commands}) == 145,
     "Fresh TU/object command set is not145 unique")
need(collections.Counter(x["kind"] for x in commands) == {"CUDA": 143, "HOST": 2},
     "Expected143CUDA+2HOST command kinds")
old_units = read(old / "runtime/build-v1/COMPILE_RECEIPTS.json")
old_source_root = old / "runtime/source"
expected_relative_units = {pathlib.Path(x["source"]).relative_to(old_source_root).as_posix()
                           for x in old_units}
actual_relative_units = {pathlib.Path(x["source"]).relative_to(source_root).as_posix()
                         for x in commands}
need(actual_relative_units == expected_relative_units and len(actual_relative_units) == 145,
     "Fresh TU source set differs from pinned original numerical build configuration")
need(all(absolute(x["object"]).is_relative_to(build_dir) for x in commands),
     "Old/outside object path in fresh commands")
need(all(not any("HS_LB_CPU_TEST_ONLY" in a or "GGML_CUDA_USE_GRAPHS" in a or
                 "GGML_CUDA_USE_PDL" in a or "GGML_USE_NCCL" in a for a in x["argv"])
         for x in commands), "Forbidden policy/test macro in numerical commands")
need(all("-DGGML_CUDA_NO_VMM" in x["argv"] for x in commands if x["kind"] == "CUDA"),
     "CUDA NO_VMM policy missing")
provider = [x for x in commands if pathlib.Path(x["source"]).name == "hs_launch_budget.cu"]
need(len(provider) == 1 and provider[0]["kind"] == "HOST", "Provider not uniquely compiled once as host source")
provider_sha = sha(provider[0]["source"]) if len(provider) == 1 else None
need(provider_sha == "07f4b16222dc260491592a1f9369ecd829fdb393a1f6991f40eb17647882439c",
     "Canonical native-hardblocked provider body changed")

summary = read(build_dir / "BUILD.json")
admission = read(build_dir / "ADMISSION.json")
need(summary["compile_failures"] == 0 and summary["dependency_closure"] == "PASS",
     "Complete fresh compilation/dependency stage did not pass")
need(summary["reused_objects"] == 0 and summary["fresh_translation_units"] == 145,
     "Fresh build reused objects or omitted units")
need(not summary["input_posthash_changes"] and not summary["input_membership_added"] and
     not summary["input_membership_removed"], "Input posthash/membership differs")
need(summary["freeze_metadata_sha256_before"] == summary["freeze_metadata_sha256_after"] ==
     admission["source_freeze_sha256"] == args.expected_freeze_sha256,
     "Freeze/admission/postcheck digests differ")
need(admission["input_locks"] == len(input_index) + 1, "Unexpected input+manifest lock count")
need(freeze["created_utc"] <= admission["utc"] <= summary["completed_utc"],
     "Freeze/build ordering mismatch")

receipts = read(build_dir / "COMPILE_RECEIPTS.json")
need(len(receipts) == 145, "Not145 actual compile receipts")
units, dep_errors = [], []
suffixes = (".cpp1.ii", ".cpp4.ii", ".cudafe1.cpp", ".cudafe1.stub.c", ".cudafe1.gpu",
            ".cudafe1.c", ".fatbin.c", ".module_id", ".ptx", ".cubin", ".fatbin")
for receipt in receipts:
    index = receipt["index"]
    command = commands[index]
    need(receipt["argv"] == command["argv"] and receipt["source"] == command["source"] and
         receipt["object"] == command["object"], "Actual compiler command differs: " + str(index))
    need(receipt["returncode"] == 0, "Compiler failure: " + str(index))
    for path_field, digest_field in (("object", "object_sha256"), ("log", "log_sha256"),
                                    ("dependency", "dependency_sha256")):
        need(sha(receipt[path_field]) == receipt[digest_field], "Actual build byte mismatch: " + str(index) + ":" + path_field)
    try:
        if receipt["kind"] == "CUDA":
            paths = make_dependencies(receipt["dependency"], receipt["object"], receipt["source"])
        else:
            data = read(receipt["dependency"])["Data"]
            if key(data["Source"]) != key(receipt["source"]) or not isinstance(data["Includes"], list) or not data["Includes"]:
                raise ValueError("HOST source/dependency header closure mismatch")
            paths = [data["Source"], *data["Includes"]]
        log = raw(receipt["log"]).decode("utf-8", errors="replace")
        paths += [line.split("Note: including file:", 1)[1].strip()
                  for line in log.splitlines() if "Note: including file:" in line]
        bound, generated, unknown = set(), set(), set()
        for name in paths:
            path = absolute(name)
            if key(path) in input_index:
                bound.add(str(path))
            elif receipt["kind"] == "CUDA" and path.parent in (
                    pathlib.Path(receipt["generated"]), build_dir / "temp" / str(index)) and (
                    path.name.startswith(pathlib.Path(receipt["source"]).stem + ".") or
                    path.name.startswith("tmpxft_")) and path.name.endswith(suffixes):
                sha(path)
                generated.add(str(path))
            else:
                unknown.add(str(path))
        if unknown:
            raise ValueError("Unfrozen dependencies: " + str(sorted(unknown)))
        units.append({"index": index, "kind": receipt["kind"], "frozen_dependency_count": len(bound),
                      "generated_dependency_count": len(generated)})
    except (OSError, ValueError, KeyError, TypeError) as exc:
        dep_errors.append({"index": index, "error": str(exc)})
need(not dep_errors and len(units) == 145, "Raw actual dependency closure failed")

prior_link = read(build_dir / "LINK.json")
link_freeze = read(build_dir / "LINK_INPUT_FREEZE.json")
expected_link_inputs = {x["object"]: x["object_sha256"] for x in receipts}
expected_link_inputs[str(build_dir / "LINK.rsp")] = sha(build_dir / "LINK.rsp")
need(link_freeze["inputs"] == expected_link_inputs and len(link_freeze["inputs"]) == 146,
     "Generated object/response prelink freeze differs")
need(link_freeze["source_freeze_sha256"] == args.expected_freeze_sha256 and
     sha(build_dir / "LINK_INPUT_FREEZE.json") == prior_link["fresh_link_input_freeze_sha256"] and
     not prior_link["fresh_link_input_posthash_changes"], "Prelink freeze/posthash receipt differs")
link_dir, link_freeze_dir = ROOT / args.link_build, ROOT / args.link_freeze
link_summary = read(link_dir / "BUILD.json")
link_manifest = read(link_freeze_dir / "FREEZE.json")
link_admission = read(link_dir / "ADMISSION.json")
need(sha(link_freeze_dir / "FREEZE.json") == args.expected_link_freeze_sha256 ==
     link_summary["freeze_sha256_before"] == link_summary["freeze_sha256_after"] ==
     link_admission["freeze_sha256"], "Separate link-stage freeze binding differs")
need(link_summary["status"] == "NUMERICAL_DLL_LINKED_NOT_LOADED_NOT_QUALIFIED" and
     link_summary["link_returncode"] == 0 and not link_summary["input_posthash_changes"],
     "Separate link stage failed or inputs changed")
need(link_summary["uninterrupted_compile_link_freeze"] is False and
     link_summary["new_compile_invocations"] == 0 and link_summary["e03_objects"] == 0 and
     link_summary["failed_v1_objects"] == 0, "Wrong link-stage session/reuse claim")
need(link_manifest["prior_full_source_freeze_sha256"] == args.expected_freeze_sha256,
     "Separate link stage bound a different compile freeze")
extra_link_input_bad = []
for path, item in link_manifest["inputs"].items():
    if key(path) in input_index:
        need(item["sha256"] == input_index[key(path)]["sha256"], "Base frozen input changed in link manifest")
    elif sha(path) != item["sha256"]:
        extra_link_input_bad.append(path)
need(not extra_link_input_bad and link_admission["read_handles"] == len(link_manifest["inputs"]) + 1,
     "Additional link-stage inputs/locks differ")
need(all(path in link_manifest["inputs"] and link_manifest["inputs"][path]["sha256"] == digest
         for path, digest in expected_link_inputs.items() if path != str(build_dir / "LINK.rsp")),
     "Fresh compile object identity not carried into link freeze")
new_link_keys = {key(x) for x in link_manifest["inputs"]}
need(all(key(path) in new_link_keys for path in freeze["inputs"]),
     "Separate link freeze omitted a base source/tool input")
new_env = read(link_freeze_dir / "ENVIRONMENT.json")
need({k:v for k,v in new_env.items() if k not in ("TEMP", "TMP")} == env and
     new_env["TEMP"] == new_env["TMP"] == str(link_dir / "temp"), "Link env changed beyond own TEMP/TMP")
link_argv = read(link_freeze_dir / "LINK_COMMAND.json")
expected_argv = [x.replace(str(build_dir / "bin/ggml-cuda.dll"), str(link_dir / "bin/ggml-cuda.dll"))
                .replace(str(build_dir / "ggml-cuda.lib"), str(link_dir / "ggml-cuda.lib"))
                for x in prior_link["argv"]]
need(link_argv == expected_argv, "Link command changed beyond output destinations")
link_objects = [x for x in link_argv if x.lower().endswith(".obj")]
need(set(link_objects) == {x["object"] for x in commands} and
     len(link_objects) == 145, "Fresh link object set differs")
need(sha(link_dir / "LINK.rsp") == link_manifest["inputs"][str(link_dir / "LINK.rsp")]["sha256"],
     "Link response hash differs")
need(sha(link_dir / "link.log") == link_summary["link_log_sha256"], "Link raw trace hash differs")
searched = []
for line in raw(link_dir / "link.log").decode("utf-8", errors="replace").splitlines():
    match = re.match(r"\s*Searching\s+(.+\.(?:lib|a)):\s*$", line, re.IGNORECASE)
    if match:
        path = match.group(1).strip('"')
        if pathlib.Path(path).is_absolute():
            need(key(path) in input_index, "Unfrozen searched linker archive: " + path)
            searched.append(path)
dll = link_dir / "bin/ggml-cuda.dll"
need(sha(dll) == link_summary["DLL_sha256"], "Actual linked DLL differs")
report = {
    "schema": "heterospec.e04.independent-fresh-native-build.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "Source/tooling/dependency/object/link disk receipts only; no numerical DLL load or CUDA call",
    "freeze_sha256": sha(freeze_path), "input_files_independently_rehashed": len(input_index),
    "separate_link_freeze_sha256": sha(link_freeze_dir / "FREEZE.json"),
    "separate_link_input_files": len(link_manifest["inputs"]),
    "extra_link_input_mismatches": extra_link_input_bad,
    "input_bytes": freeze["input_bytes"], "input_mismatches": input_bad,
    "complete_source_members": len(source_expected), "source_mismatches": source_bad,
    "fresh_compile_receipts": len(receipts), "kinds": dict(collections.Counter(x["kind"] for x in receipts)),
    "e03_or_failed_v1_object_reuse": 0, "fresh_e04_v2_objects_in_separate_link_stage": 145,
    "uninterrupted_compile_link_session": False,
    "retained_compile_stage_link_failure": prior_link["returncode"],
    "provider_objects": len(provider), "provider_sha256": provider_sha,
    "independent_raw_dependency_units": units, "dependency_errors": dep_errors,
    "actual_link_objects": len(link_objects), "traced_searched_frozen_archives": sorted(set(searched)),
    "fresh_object_and_response_prelink_freeze": {"inputs": len(link_freeze["inputs"]),
                                                "sha256": sha(build_dir / "LINK_INPUT_FREEZE.json")},
    "DLL_sha256": sha(dll), "DLL_bytes": os.stat(open_path(dll)).st_size,
    "source_freeze_before_compile": "Driver order plus fixed digest/timestamps and own-input lock fixtures; not an OS filesystem-access or memory attestation",
    "scope_limitations": ["Windows runtime DLLs/OS/driver/hardware are not frozen", "Python orchestration stdlib/runtime is not a copied complete runtime freeze", "Dependency files plus include diagnostics are not an OS trace of every compiler file read", "Native linker entire archive containers are frozen; member extraction raw trace retained, no universal linker-read claim", "All-model physical4096 proof and runnable policy remain BLOCKED; source-visible counter is insufficient"],
    "numerical_DLL_normal_LoadLibrary": 0, "CUDA_calls": 0, "GPU_kernel_launches": 0,
    "native_qualification": "NOT_RUN", "errors": errors, "passed_preparation_only": not errors,
    "script_sha256": sha(__file__),
}
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed_preparation_only": not errors, "errors": errors,
                  "inputs": len(input_index), "actual_units": len(units), "receipt": str(out)}))
raise SystemExit(bool(errors))
