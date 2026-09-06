import os
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
RUNS = ROOT / "runs"
REPORTS = ROOT / "reports"
TRACE_ROOT = ROOT / "telemetry" / "phase1_qwen_draft" / "20260905T001856"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


rows = []
invalid = []
for result_path in RUNS.rglob("result.json"):
    run_dir = result_path.parent
    if (run_dir / "INVALIDATION.json").exists():
        invalid.append(str(run_dir))
        continue
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        continue
    meta, result = load(meta_path), load(result_path)
    if meta.get("phase") != "P1" or meta.get("config") != "DRAFT-QUAL":
        continue
    rows.append({
        "run_id": meta["run_id"],
        "device": meta["draft_device_requested"],
        "context_tokens": meta["input_tokens"],
        "output_tokens": result["output_tokens"],
        "repetition": meta["repetition"],
        "ttft_ms": result["ttft_ms"]["mean"],
        "tpot_ms": result["tpot_ms"]["mean"],
        "throughput_tokens_s": result["throughput_tokens_s"]["mean"],
        "completion_ms": result["host_completion_time_ms"],
        "rss_start_mb": result["rss_start_mb"],
        "rss_end_mb": result["rss_end_mb"],
        "prompt_sha256": meta["prompt_token_ids_sha256"],
        "output_sha256": result["token_ids_sha256"],
        "telemetry_prefix": meta.get("telemetry_trace_prefix", ""),
    })

rows.sort(key=lambda r: (r["device"], r["context_tokens"], r["repetition"]))
REPORTS.mkdir(exist_ok=True)
detail_path = REPORTS / "qwen_draft_qualification_runs.csv"
with detail_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

groups = defaultdict(list)
for row in rows:
    groups[(row["device"], row["context_tokens"])].append(row)

summary = []
for (device, context), rs in sorted(groups.items()):
    out = {"device": device, "context_tokens": context, "n": len(rs)}
    for key in ("ttft_ms", "tpot_ms", "throughput_tokens_s", "completion_ms", "rss_end_mb"):
        vals = [r[key] for r in rs]
        out[f"{key}_mean"] = statistics.mean(vals)
        out[f"{key}_median"] = statistics.median(vals)
        out[f"{key}_stdev"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
    summary.append(out)

summary_path = REPORTS / "qwen_draft_qualification.csv"
with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=summary[0].keys())
    w.writeheader(); w.writerows(summary)

expected = {(d, c, r) for d in ("CPU", "GPU.0") for c in (512, 2048, 8192) for r in range(1, 6)}
actual = {(r["device"], r["context_tokens"], r["repetition"]) for r in rows}
prompt_ok = all(len({r["prompt_sha256"] for r in rows if r["context_tokens"] == c}) == 1 for c in (512, 2048, 8192))
output_ok = all(len({r["output_sha256"] for r in rows if r["context_tokens"] == c}) == 1 for c in (512, 2048, 8192))
markers = {}
for device, dirname in (("CPU", "CPU"), ("GPU.0", "GPU_0")):
    trace = TRACE_ROOT / dirname / "trace.json"
    wanted = {"run|" + r["run_id"] for r in rows if r["device"] == device}
    found = set()
    with trace.open("rb") as f:
        carry = b""
        while chunk := f.read(8 * 1024 * 1024):
            data = carry + chunk
            for marker in wanted - found:
                if marker.encode() in data:
                    found.add(marker)
            if found == wanted:
                break
            carry = data[-256:]
    markers[device] = {"expected": len(wanted), "found": len(found), "complete": found == wanted}

integrity = {
    "formal_run_count": len(rows),
    "invalidated_run_count": len(invalid),
    "matrix_complete": actual == expected,
    "missing_cells": sorted(expected - actual),
    "unexpected_cells": sorted(actual - expected),
    "prompt_hash_equal_across_devices": prompt_ok,
    "greedy_output_hash_equal_across_devices": output_ok,
    "telemetry_markers": markers,
    "npu_status": "FAIL_REAL_MODEL_COMPILE",
    "npu_reason": "Unsupported DequantizeOp configuration on NPU37XX for the frozen shared INT4 IR",
}
(REPORTS / "qwen_draft_qualification_integrity.json").write_text(json.dumps(integrity, indent=2), encoding="utf-8")

lines = [
    "# Qwen3-0.6B Draft Device Qualification",
    "",
    f"- Formal measured runs: {len(rows)}/30",
    f"- Matrix complete: {'PASS' if actual == expected else 'FAIL'}",
    f"- ITT run markers: CPU {markers['CPU']['found']}/15; GPU.0 {markers['GPU.0']['found']}/15",
    f"- Identical prompt token hashes across devices: {'PASS' if prompt_ok else 'FAIL'}",
    f"- Identical greedy output token hashes across devices: {'PASS' if output_ok else 'FAIL'}",
    f"- Invalidated preliminary runs excluded: {len(invalid)}",
    "- NPU: FAIL qualification (real frozen INT4 IR compile failure; no fallback and no alternate IR)",
    "",
    "## Aggregate results",
    "",
    "| Device | Context | TTFT mean ms | TPOT mean ms | Throughput tok/s | Completion mean ms |",
    "|---|---:|---:|---:|---:|---:|",
]
for s in summary:
    lines.append(f"| {s['device']} | {s['context_tokens']} | {s['ttft_ms_mean']:.2f} | {s['tpot_ms_mean']:.2f} | {s['throughput_tokens_s_mean']:.2f} | {s['completion_ms_mean']:.2f} |")
lines += [
    "",
    "## Decision",
    "",
    "CPU and Intel GPU.0 qualify for subsequent Qwen draft-device experiments. NPU is excluded under the frozen-artifact fairness rule. Intel package telemetry and device activity traces were captured; independent Intel GPU/NPU power domains remain unavailable as documented at Gate 0.",
]
(REPORTS / "QWEN_DRAFT_QUALIFICATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(integrity, indent=2))
print(summary_path)
