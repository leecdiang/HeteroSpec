"""Additive final v7 byte-writer recheck, preserving the earlier v5 review."""
from pathlib import Path
import datetime
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    out = HERE / "V7_FINAL_RECHECK.json"
    need(not out.exists(), "new additive receipt required")
    parent = read(ROOT / "continuation/PARENT_BINDING.json")
    archive = ROOT.parent / "HeteroSpec_RTX221_Round1_20261112_v2.zip"
    need(sha(archive) == parent["original_delivery_zip_sha256"], "old archive changed")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("delivery/DELIVERY_MANIFEST.json"))
    changed_copy_metadata = []
    for f in manifest["files"]:
        old = Path(parent["parent_source"]) / f["path"]
        need(sha(old) == f["sha256"], "original e01 file changed: " + f["path"])
        current = ROOT / f["path"]
        if sha(current) != f["sha256"]:
            need(f["path"] in ("README.md", "package_delivery.py"), "unexpected copied parent edit: " + f["path"])
            changed_copy_metadata.append({"path": f["path"], "parent_sha256": f["sha256"], "current_sha256": sha(current), "reason": "Intentional current continuation entrypoint/packaging update; original e01 remains unchanged"})
    inherited = read(ROOT / "continuation/INHERITED_TEST_VALIDITY.json")
    for f in inherited["files"]:
        need(sha(ROOT / f["path"]) == f["parent_sha256"], "inherited critical test/source changed")
    frontend = ROOT / "continuation/frontend"
    recipe = read(frontend / "HOOK_SOURCE_v7.json")
    source = frontend / "hooked_frontend_v7"
    for name, h in recipe["files"].items():
        need(sha(source / name) == h, "v7 source recipe changed")
    build_path = frontend / "hooked-build-v5/BUILD.json"
    build = read(build_path)
    need(build["status"] == "COMPILED_LINKED_NOT_NATIVE_QUALIFIED", "v7 build failed")
    for name, h in build["source_hashes"].items():
        need(sha(source / name) == h, "compiled v7 source differs")
    for path, h in build["linked_input_identities_before_and_after"].items():
        need(sha(path) == h, "v7 linked input differs")
    raw_worker = (source / "worker.cpp").read_text(encoding="utf8")
    need('std::ofstream f(tmp,std::ios::binary)' in raw_worker, "binary JSON writer fix missing")
    need('const auto encoded=j.dump(2)+"\\n";tpds_decisive::reserve_capture_bytes(encoded.size())' in raw_worker, "JSON writer reservation differs")
    need('if(life=="fresh"){target=nullptr;draft=nullptr;}fresh.draft.reset()' in raw_worker, "fresh ownership fix regressed")
    selftest_path = frontend / "hooked-build-v5/HOST_SELFTEST.json"
    selftest = read(selftest_path)
    need(selftest["status"] == "PASS" and selftest["build_receipt_sha256"] == sha(build_path), "v7 host selftest binding")
    fixtures = []
    for record in selftest["records"]:
        need(record["returncode"] == 0 and record["passed"], "v7 selftest failed")
        need(sha(record["argv"][0]) == record["exe_sha256"] == build["builds"][record["core"]]["exe_sha256"], "v7 executable identity")
        log = frontend / "hooked-build-v5" / (record["core"] + "-selftest.log")
        need(sha(log) == record["log_sha256"] and read(log) == record["result"], "v7 raw selftest log")
        need(record["argv"][1] == "--selftest-json" and record["result"]["CUDA_calls"] == 0 and record["result"]["models"] == 0, "v7 selftest scope")
        fixture = record["fixture"]
        raw = Path(fixture["path"]).read_bytes()
        parsed = json.loads(raw)
        expected = (json.dumps({"multiline": [1, 2, 3], "nested": {"key": "value"}, "utf8": "状态捕获"}, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf8")
        need(raw == expected and len(raw) == 109 and raw.count(b"\n") == 11 and b"\r\n" not in raw, "physical UTF8 JSON bytes exceed reserved encoding")
        need(hashlib.sha256(raw).hexdigest() == fixture["sha256"], "v7 raw fixture hash")
        need(record["result"]["multiline_UTF8_JSON_file_checked"] is True and record["result"]["multiline_UTF8_JSON_bytes"] == 109 and record["result"]["capture_ceiling_boundary"] is True, "v7 exact-boundary result missing")
        fixtures.append({"core": record["core"], "physical_bytes": len(raw), "LF": raw.count(b"\n"), "CRLF": raw.count(b"\r\n"), "sha256": hashlib.sha256(raw).hexdigest(), "source_checks_actual_vs_encoded_and_reserved_written": True, "extra_one_byte_refused": True, "new_GPU_or_model_work": 0})
    current = read(HERE / "FINAL_INDEPENDENT_REVIEW.json")
    safety = read(HERE / "safety-independent-v1/RECEIPT.json")
    for path, h in safety["source_sha256"].items():
        need(sha(ROOT / path) == h, "frozen safety source changed")
    result = {"schema": "heterospec.e02.independent-v7-recheck.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS_CURRENT_PREPARATION_REVIEW_NATIVE_GATES_CLOSED", "decision": "INCONCLUSIVE", "current_frontend_source": "hooked_frontend_v7", "current_frontend_build": "hooked-build-v5/BUILD.json", "build_sha256": sha(build_path), "selftest_receipt_sha256": sha(selftest_path), "source_files_rehashed": len(recipe["files"]), "linked_inputs_rehashed": len(build["linked_input_identities_before_and_after"]), "F2": "FIXED_BINARY_JSON_WRITER; REAL_MULTILINE_UTF8_FILE_INDEPENDENTLY_RECOMPUTED", "physical_JSON_fixtures": fixtures, "original_e01_files_rehashed_unchanged": len(manifest["files"]), "copied_metadata_intentionally_changed": changed_copy_metadata, "inherited_critical_sources_tests_rehashed": len(inherited["files"]), "old_41_suite_rerun": False, "OS18_suite_rerun_after_F2": False, "prior_independent_review": "FINAL_INDEPENDENT_REVIEW.json remains valid for its v5 source and earlier time; this additive receipt selects final v7 and records intentional copied metadata edits", "retained_independent_safety_results": [18, 18], "raw_CPU_ledgers_independently_audited": 36, "gate_table": current["gate_table"], "new_model_requests": 0, "new_GPU_kernel_launches": 0, "second_round": "DO_NOT_START", "scope_limit": "Binary mode and actual byte fixture validate this host writer; source-bound model/backend counters, live dedup clearance and native numerical/service qualification remain unavailable. No complete-system GPU capture/timing admission follows."}
    out.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"status": result["status"], "decision": result["decision"], "old_files": result["original_e01_files_rehashed_unchanged"], "current_copy_metadata_edits": [r["path"] for r in changed_copy_metadata], "fixture_bytes": [f["physical_bytes"] for f in fixtures], "build_sha256": result["build_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
