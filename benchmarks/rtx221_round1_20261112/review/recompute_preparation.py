"""Independent raw recheck. Never imports producer verifiers or native code."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import math
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def check_vector(item, vocabulary):
    raw = bytes.fromhex(item["bytes_hex"])
    need(item["dtype"] == "F32_LE" and item["shape"] == [vocabulary], "vector shape")
    need(len(raw) == vocabulary * 4 and sha(raw) == item["sha256"], "complete vector/hash")
    values = struct.unpack("<" + "f" * vocabulary, raw)
    need(all(map(math.isfinite, values)), "nonfinite logit")
    return max(range(vocabulary), key=values.__getitem__)


def check_constructed(raw):
    need(raw["coverage"] == "CONSTRUCTED_LOGICAL_FIXTURE" and raw["native_qualification"] is False, "fixture boundary")
    vocabulary, cap = raw["vocabulary"], raw["cap"]
    pending = check_vector(raw["initial_vector"], vocabulary)
    target, draft, emitted = list(raw["prompt_ids"]), list(raw["prompt_ids"]), [pending]
    vector_count = 1
    results = []
    for c in raw["cycles"]:
        k, proposals = c["k"], c["proposals"]
        need(c["seed"] == pending and c["base"] == len(target), "actual prior consumer not next seed")
        need(c["state_before"] == {"target": target, "draft": draft}, "before state")
        need(len(c["vectors"]) == k + 1 and c["requested_mask"] == [True] * (k + 1), "original full requested output")
        decisions = [check_vector(v, vocabulary) for v in c["vectors"]]
        vector_count += len(decisions)
        need(decisions == c["decisions"], "full-vector decisions")
        target = target + [pending] + proposals
        draft = draft + [pending] + proposals
        need(c["state_untrimmed"] == {"target": target, "draft": draft}, "untrimmed state")
        accepted = 0
        kind, consumed_row = None, None
        for j in range(k):
            if len(emitted) == cap or emitted[-1] in raw["eog_ids"]:
                break
            if decisions[j] == proposals[j]:
                accepted += 1
                emitted.append(proposals[j])
                kind = "accepted"
            else:
                pending, kind, consumed_row = decisions[j], "correction", j
                emitted.append(pending)
                break
        if accepted == k and len(emitted) < cap and emitted[-1] not in raw["eog_ids"]:
            pending, kind, consumed_row = decisions[k], "bonus", k
            emitted.append(pending)
        need(accepted == c["accepted"] and kind == c["commit_kind"], "accepted/commit kind")
        if consumed_row is not None:
            consumer = c["decision_consumer"]
            need(consumer["row"] == consumed_row and consumer["vector_sha256"] == c["vectors"][consumed_row]["sha256"], "real decision vector ownership")
        keep = c["base"] + 1 + accepted
        target, draft = target[:keep], draft[:keep]
        need(keep == c["keep"] and c["state_after"] == {"target": target, "draft": draft}, "trim/state")
        need(c["ids"] == emitted, "emission")
        results.append({"k": k, "seed": c["seed"], "accepted": accepted, "commit_kind": kind, "consumer_row": consumed_row, "keep": keep})
    need(emitted == raw["ids"] and target == raw["final_target"] and draft == raw["final_draft"], "final request")
    need(len(emitted) == cap and raw["stop_reason"] == "CAP", "main fixture CAP")
    need(results[0]["k"] == 3 and results[0]["accepted"] == 3 and results[0]["commit_kind"] == "bonus", "k3 allaccept bonus")
    need(results[1]["k"] == 7 and results[1]["accepted"] == 4 and results[1]["consumer_row"] == 4 and results[1]["commit_kind"] == "correction", "L4 fifth proposal rejection")
    return {"status": "PASS_CONSTRUCTED_LOGICAL_FIXTURE_ONLY", "full_vectors_recomputed": vector_count, "cycles": results, "native_KV_or_geometry": "NOT_CHECKED_NOT_CAPTURED", "natural_request_coverage": False}


def main():
    OUT.mkdir(exist_ok=True)
    result = {"observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "reviewer": "independent subagent", "model_requests": 0, "kernel_launches": 0, "native_execution": "NOT_RUN", "imports_producer_verifier": False}
    commits = []
    for name in ("UPSTREAM_FETCH.json", "EXTRA_SOURCE_FETCH.json"):
        for f in read(ROOT / "provenance" / name)["files"]:
            raw = (ROOT / f["path"]).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            need(blob == f["git_blob"] and sha(raw) == f["sha256"], "upstream snapshot mismatch: " + f["path"])
            commits.append({"path": f["path"], "bytes": len(raw), "git_blob": blob, "sha256": sha(raw)})
    result["upstream_files_independently_rehashed"] = commits
    base = ROOT / "audit/recovered_operand"
    provenance = read(base / "PROVENANCE.json")
    for f in provenance["recovered_files"]:
        raw = Path(f["path"]).read_bytes()
        need(len(raw) == f["bytes"] and sha(raw) == f["sha256"], "recovered hash")
    a = (base / "backend_loop4_historical_q8_output.bin").read_bytes()
    b = (base / "packed_historical_q8_output.bin").read_bytes()
    need(a == b and len(a) == 4096 * 8 * 4, "historical A/B output bytes")
    need(all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", a)), "historical output finite")
    original_input = Path(provenance["original_files"][0]["path"]).read_bytes()
    need(original_input[:4096 * 8 * 4] == (base / "input_q8_from_q32.bin").read_bytes(), "derived real input prefix")
    result["historical_operand_check"] = {"status": "PASS_OFFLINE_RECOVERY_ONLY", "historical_AB_equal": True, "output_float_entries_each": len(a) // 4, "output_sha256": sha(a), "input": "real q32 capture first eight columns", "new_ABC_pair": False, "actual_q8_model_capture": False, "new_performance": False}
    result["constructed_request_check"] = check_constructed(read(ROOT / "request/cpu_result/CONSTRUCTED_RAW.json"))
    checked = []
    for name in ("src/admission.py", "src/windows_epoch.py", "request/state_machine.py", "request/costs.py"):
        raw = (ROOT / name).read_bytes()
        tree = ast.parse(raw.decode("utf8"))
        need(not any(isinstance(n, ast.Assert) for n in ast.walk(tree)), "removable assertion in critical source")
        checked.append({"path": name, "sha256": sha(raw), "removable_assert_statements": 0})
    result["critical_sources"] = checked
    tests = []
    for flag, label in (([], "normal"), (["-O"], "optimized")):
        args = [sys.executable, "-B"] + flag + ["-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"]
        run = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=90)
        log = run.stdout + run.stderr
        (OUT / ("all_tests_" + label + ".log")).write_bytes(log)
        tests.append({"mode": label, "argv": args, "returncode": run.returncode, "log_sha256": sha(log)})
        need(run.returncode == 0, "host tests failed: " + label)
    result["test_runs"] = tests
    result["decision"] = "INCONCLUSIVE_NO_GPU_OR_SERVICE_RESULT"
    result["limitations"] = ["Original execution thread remains unverified; present no-compute-pid observation is not an exclusive reservation", "Native qualification is NOT_RUN; CPU checks do not qualify clean execution", "Operator executable requires an external admitted launcher and ledger binding; gpu_admitted boolean alone is not proof", "Cost complete_endpoint marker requires bound instrumentation evidence before service admission", "C source retains per-output arithmetic organization but bitwise replay and compiler/resource runtime effects are untested", "Historical A/B equality and constructed request fixture do not supply new A/B/C timings or a natural dynamic request"]
    (OUT / "INDEPENDENT_RAW_CHECK.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"decision": result["decision"], "upstream_files": len(commits), "historical_output_entries": len(a) // 4, "fixture_vectors": result["constructed_request_check"]["full_vectors_recomputed"], "test_runs": tests}, indent=2))


if __name__ == "__main__":
    main()
