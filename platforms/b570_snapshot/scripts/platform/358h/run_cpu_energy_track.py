#!/usr/bin/env python3
"""Frozen formal 358H CPU package-energy Track E.

Latency from this runner is boundary metadata only and is never a Track-L result.
Each formal energy repetition contains three identical 128-token generations so
the qualified 1000-ms PDH collector has enough in-window samples.  Energy is
normalized by exactly 3 * 128 generated output tokens.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino_genai as ov_genai
import psutil

from run_phase1_draft_characterization import MODEL, PREREG, active_power_scheme, prepared_input, readiness

ROOT = Path(__file__).resolve().parents[3]
ADDENDUM = ROOT / "benchmarks/358h_threshold_validation/protocol_addendum_v1.json"
SAMPLER = ROOT / "scripts/platform/358h/sample_windows_energy_meter.py"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def generate(pipe, inputs, config) -> dict:
    start = time.perf_counter_ns()
    result = pipe.generate(inputs, config)
    end = time.perf_counter_ns()
    tokens = [int(v) for v in result.tokens[0]]
    return {
        "start_qpc_ns": start,
        "end_qpc_ns": end,
        "boundary_duration_ms": (end - start) / 1e6,
        "output_tokens": len(tokens),
        "token_ids_sha256": hashlib.sha256(np.asarray(tokens, dtype=np.int64).tobytes()).hexdigest(),
        "throughput_tokens_s_for_warmup_only": float(result.perf_metrics.get_throughput().mean),
    }


def interpolate(a, b, t):
    if b[0] == a[0]:
        return a[1]
    return a[1] + (b[1] - a[1]) * ((t - a[0]) / (b[0] - a[0]))


def integrate(csv_path: Path, start_ns: int, end_ns: int) -> dict:
    rows = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("package_power_w") not in (None, "", "None"):
                rows.append((int(row["qpc_midpoint_ns"]), float(row["package_power_w"])))
    rows.sort()
    if len(rows) < 2 or start_ns < rows[0][0] or end_ns > rows[-1][0]:
        raise RuntimeError("Track-E boundary lacks bracketing PDH samples")
    points = []
    boundary_values = {}
    for label, bound in (("start", start_ns), ("end", end_ns)):
        pair = next(((a, b) for a, b in zip(rows, rows[1:]) if a[0] <= bound <= b[0]), None)
        if pair is None:
            raise RuntimeError(f"no bracketing samples for {label} boundary")
        watts = interpolate(pair[0], pair[1], bound)
        points.append((bound, watts))
        boundary_values[label] = {"qpc_ns": bound, "interpolated_power_w": watts,
                                  "bracket_qpc_ns": [pair[0][0], pair[1][0]]}
    interior = [(t, p) for t, p in rows if start_ns < t < end_ns]
    if len(interior) < 2:
        raise RuntimeError("fewer than two interior 1000-ms samples in repeated Track-E window")
    points.extend(interior)
    points.sort()
    joules = sum(((b[0] - a[0]) / 1e9) * (a[1] + b[1]) / 2 for a, b in zip(points, points[1:]))
    duration_s = (end_ns - start_ns) / 1e9
    return {"method": "QPC-midpoint, linear boundary interpolation, trapezoidal integration",
            "energy_j": joules, "duration_s": duration_s, "package_average_w": joules / duration_s,
            "valid_rows_total": len(rows), "interior_rows": len(interior), "boundaries": boundary_values}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--execute-formal", action="store_true")
    args = parser.parse_args()
    try:
        _, prereg = readiness()
        addendum = json.loads(ADDENDUM.read_text(encoding="utf-8-sig"))
        if addendum.get("status") != "FROZEN" or addendum.get("formal_data_seen_before_addendum") is not False:
            raise RuntimeError("pre-data addendum is not frozen")
    except Exception as exc:
        print(json.dumps({"ready": False, "reason": str(exc)}, indent=2))
        return 2
    if args.check:
        print(json.dumps({"ready": True}, indent=2))
        return 0
    if not args.execute_formal:
        parser.error("formal execution requires --execute-formal")

    phase = prereg["phase1_primary_latency_track"]
    design = addendum["cpu_track_e"]
    psutil.Process().cpu_affinity(design["workload_affinity"])
    tokenizer = ov_genai.Tokenizer(MODEL)
    inputs = {c: prepared_input(tokenizer, c, phase["prompt_construction"]["token_id_sha256_by_context"][str(c)])
              for c in design["context_order"]}
    config = ov_genai.GenerationConfig()
    config.max_new_tokens = config.min_new_tokens = design["output_tokens_per_generation"]
    config.ignore_eos = True
    config.do_sample = False
    config.apply_chat_template = False
    pipe = ov_genai.LLMPipeline(str(MODEL), "CPU", {"PERFORMANCE_HINT": "LATENCY"})
    run_id = "358h-p1-energy-cpu-" + datetime.now().strftime("%Y%m%dT%H%M%S")
    out = ROOT / "runs/358h/phase1" / run_id
    out.mkdir(parents=True, exist_ok=False)
    session = {"schema": "heterospec.358h.cpu_energy_track_e.v1", "formal": True,
               "latency_claim_prohibited": True, "run_id": run_id, "started": now(), "cells": []}
    for context in design["context_order"]:
        tokenized, prompt_hash = inputs[context]
        warmups = []
        stable = False
        for index in range(1, design["warmup"]["maximum"] + 1):
            row = generate(pipe, tokenized, config)
            warmups.append({"index": index, "throughput_tokens_s": row.pop("throughput_tokens_s_for_warmup_only")})
            if index >= design["warmup"]["minimum"]:
                a, b = warmups[-2]["throughput_tokens_s"], warmups[-1]["throughput_tokens_s"]
                if abs(a - b) / ((a + b) / 2) <= design["warmup"]["stability_fraction"]:
                    stable = True
                    break
        if not stable:
            raise RuntimeError(f"Track-E warm-up failed at context {context}")
        cell = {"context_tokens": context, "prompt_token_ids_sha256": prompt_hash, "warmups": warmups, "runs": []}
        for repetition in range(1, design["repetitions_per_context"] + 1):
            stem = f"c{context}-r{repetition}"
            csv_path, meta_path, stop_path = out/f"{stem}.pdh.csv", out/f"{stem}.pdh.json", out/f"{stem}.stop"
            cmd = [sys.executable, str(SAMPLER), "--output-csv", str(csv_path), "--metadata-json", str(meta_path),
                   "--period-ms", "1000", "--duration-seconds", "600", "--affinity-cpus",
                   ",".join(map(str, design["collector_affinity"])), "--stop-file", str(stop_path), "--formal-measurement"]
            collector = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(design["collector_lead_seconds"])
            repeats = [generate(pipe, tokenized, config) for _ in range(design["generations_per_energy_window"])]
            start_ns, end_ns = repeats[0]["start_qpc_ns"], repeats[-1]["end_qpc_ns"]
            time.sleep(design["collector_tail_seconds"])
            stop_path.touch()
            stdout, stderr = collector.communicate(timeout=20)
            if collector.returncode:
                raise RuntimeError(f"PDH collector failed: {stderr[-2000:]}")
            if any(r["output_tokens"] != design["output_tokens_per_generation"] for r in repeats):
                raise RuntimeError("Track-E output-token contract failed")
            integ = integrate(csv_path, start_ns, end_ns)
            normalized_tokens = design["generations_per_energy_window"] * design["output_tokens_per_generation"]
            result = {"context_tokens": context, "repetition": repetition, "formal": True,
                      "latency_claim_prohibited": True, "repeated_generations": repeats,
                      "integration": integ, "normalization_output_tokens": normalized_tokens,
                      "package_j_per_output_token": integ["energy_j"] / normalized_tokens,
                      "pdh_csv_sha256": sha256(csv_path), "pdh_metadata_sha256": sha256(meta_path),
                      "sampler_stdout": stdout, "sampler_stderr": stderr}
            result_path = out/f"{stem}.energy.json"
            result_path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
            cell["runs"].append(result_path.name)
        session["cells"].append(cell)
    battery = psutil.sensors_battery()
    session["ended"] = now()
    session["postflight"] = {"power_plugged": battery.power_plugged if battery else None,
                             "power_scheme": active_power_scheme()[0]}
    session["status"] = "COMPLETE"
    (out/"session.json").write_text(json.dumps(session, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"run_id": run_id, "status": "COMPLETE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

