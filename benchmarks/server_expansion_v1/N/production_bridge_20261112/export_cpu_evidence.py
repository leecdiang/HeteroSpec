"""Read-only independent recount/export of this successor's CPU suite.

Public traces retain accounting/stage events and digests, withholding private
process/job identity bytes. Recount is not a native run or a GPU qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def export(suite_root, output):
    source, output = Path(suite_root), Path(output)
    if not source.is_absolute() or not output.is_absolute() or output.exists():
        raise RuntimeError("existing CPU suite and fresh absolute export only")
    suite = json.loads((source / "SUITE.json").read_bytes())
    if suite["status"] != "PASS_CPU_FIXED_PROCESS_FAULT_SUITE" or len(suite["cases"]) != 14:
        raise RuntimeError("not the complete fixed fourteen-case CPU suite")
    output.mkdir(mode=0o700)
    reports = []
    for case in suite["cases"]:
        name = case["case"]
        if name not in {"normal", "exit_nonzero", "no_close", "stdout_overflow", "stderr_overflow",
                        "no_worker_hello", "before_bind_crash", "after_bind_crash", "parent_disconnect",
                        "job_changed", "job_after_bind_changed", "result_unknown", "log_fsync", "log_partial"}:
            raise RuntimeError("unknown suite entry")
        root = source / name
        result = json.loads((root / "RESULT.json").read_bytes())
        state = json.loads((root / "run/STATE.json").read_bytes())
        attempt = {"suite": source.name, "case": name, "run_id": state["run_id"],
                   "manifest_sha256": state["manifest_sha256"],
                   "actual_job_file_sha256": digest((root / "JOB.json").read_bytes())}
        attempt["attempt_identity_sha256"] = digest(encoded(attempt))
        chain, seq, replay, trace = "0" * 64, 0, None, []
        for raw in (root / "run/journal.jsonl").read_bytes().splitlines(keepends=True):
            if not raw.endswith(b"\n") or len(raw) > 2048:
                raise RuntimeError("partial/oversized journal; cannot export as checked")
            line = json.loads(raw); record = line["record"]
            if record["seq"] != seq + 1 or record["previous"] != chain or digest(encoded(record)) != line["sha256"]:
                raise RuntimeError("original CPU journal chain mismatch")
            if seq == 0:
                replay = record["initial_state"]
            for key, value in record["delta"].items():
                if key in ("requests", "counts", "stage_reports", "completed_worker_bindings"):
                    replay[key].update(value)
                else:
                    replay[key] = value
            seq, chain = record["seq"], line["sha256"]
            keep = {key: record["detail"][key] for key in ("worker", "id", "amount", "detail", "deployment", "stage", "exit_code")
                    if key in record["detail"]}
            trace.append({"seq": seq, "kind": record["kind"], "detail": keep,
                "counts_delta": record["delta"].get("counts", {}),
                "status": record["delta"].get("status"), "original_record_sha256": line["sha256"],
                "bridge": record["delta"].get("bridge")})
        replay.update(journal_seq=seq, journal_chain=chain)
        if encoded(replay) != encoded(state) or state["counts"] != result["counts"] or state["counts"] != case["counts"]:
            raise RuntimeError("CPU state/recount/result mismatch")
        private_index = []
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                raw = path.read_bytes()
                private_index.append({"file": path.relative_to(root).as_posix(), "bytes": len(raw),
                    "sha256": digest(raw), "public_original_bytes": False})
        destination = output / name; destination.mkdir(mode=0o700)
        (destination / "RESULT.json").write_bytes(encoded(result))
        (destination / "ATTEMPT_IDENTITY.json").write_bytes(encoded(attempt))
        (destination / "TRACE_REDACTED.json").write_bytes(encoded({"scope": "DERIVED_CPU_TRACE_NOT_RAW_KERNEL_IDENTITY_PROOF",
            "private_identity_fields": "withheld; exact originals retained privately",
            "original_journal_final_sha256": chain, "events": trace}))
        (destination / "ORIGINAL_PRIVATE_INDEX.json").write_bytes(encoded(private_index))
        reports.append({"case": name, "status": "PASS_ORIGINAL_CPU_JOURNAL_RECOUNT",
                        "events": seq, "counts": state["counts"], "STOP_exists": (root / "run/STOP.json").exists(),
                        "worker_index": state["worker_index"], "stage_index": state["stage_index"]})
    out = {"status": "PASS_INDEPENDENT_CPU_JOURNAL_RECOUNT", "scope": "CPU_TEXT_ONLY_NOT_NATIVE_QUALIFICATION",
           "cases": reports, "all_261_native_checks": "NOT_RUN", "native_GPU_calls": 0,
           "public_identity_validation": "NOT_REPEATED; original proc/job bytes private",
           "request_reservations": sum(x["counts"]["requests"] for x in reports),
           "row_reservations": sum(x["counts"]["rows"] for x in reports)}
    (output / "RECOUNT.json").write_bytes(encoded(out))
    (output / "SUITE.json").write_bytes(encoded(suite))
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--suite", required=True); p.add_argument("--out", required=True)
    a = p.parse_args()
    print(json.dumps(export(a.suite, a.out), sort_keys=True))
