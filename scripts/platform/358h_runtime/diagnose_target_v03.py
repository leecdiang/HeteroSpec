#!/usr/bin/env python3
"""Correctness-only target traces for frozen UB1/UB2 divergences."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil

from run_runtime_qualification import FULL, OUTPUT_CAP, formatted_prompt, load_tasks
from runtime_process_v02 import apply_affinity, assert_no_duplicate_omp
from runtime_target import LlamaAPI, RuntimeTargetPool

ROOT = Path(__file__).resolve().parents[3]
R1_NPU = ROOT / "runs/358h/runtime_codesign_v02_qualification_20260923/r1_full_npu_legacy_target_20260924"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite diagnostic evidence: {path}")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def frozen_rows(task_id: int) -> dict[tuple[int, str], dict]:
    rows = json.loads((R1_NPU / "observations.resolved.json").read_text(encoding="utf-8"))
    return {(r["repetition"], r["path"]): r for r in rows if r["task_id"] == f"HumanEval/{task_id}"}


def top2(target) -> dict:
    ptr = target.a.ll.llama_get_logits_ith(target.ctx, -1)
    if not ptr:
        raise RuntimeError("llama_get_logits_ith(-1) returned null")
    logits = np.ctypeslib.as_array(ptr, shape=(target.n_vocab,))
    first = int(np.argmax(logits))
    first_value = float(logits[first])
    second_logits = logits.copy()
    second_logits[first] = -np.inf
    second = int(np.argmax(second_logits))
    second_value = float(logits[second])
    if first != target.next_token():
        raise AssertionError("diagnostic top1 does not equal frozen target argmax")
    return {"top1_token": first, "top1_logit": first_value,
            "top2_token": second, "top2_logit": second_value,
            "top1_top2_margin": first_value - second_value}


def target_trace(target, prompt: list[int], output_cap: int = OUTPUT_CAP) -> dict:
    target.reset_prefill(prompt)
    trace = []
    for i in range(output_cap):
        before = len(target.history)
        before_pos = target.state_position()
        logits = top2(target)
        committed = target.verify([])
        if len(committed) != 1 or committed[0] != logits["top1_token"]:
            raise AssertionError("target-only trace changed greedy semantics")
        trace.append({"output_index": i, "input_prefix_length": before,
                      "generated_token": committed[0], "target_history_length": len(target.history),
                      "target_state_position": target.state_position(),
                      "target_state_position_before": before_pos,
                      "n_ubatch": target.ubatch, **logits})
    return {"tokens": [r["generated_token"] for r in trace], "trace": trace}


def task_prompt(task_id: int, target) -> list[int]:
    if task_id not in FULL:
        raise ValueError("diagnostic task must belong to frozen R1 full set")
    return target.tokenize(formatted_prompt(load_tasks()[task_id]), True)


def base_record(stage: str) -> dict:
    battery = psutil.sensors_battery()
    if battery is None or battery.power_plugged is not True:
        raise RuntimeError("AC power must be positively online")
    if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"):
        raise RuntimeError("RDP session forbidden")
    assert_no_duplicate_omp()
    mask = sorted(psutil.Process().cpu_affinity())
    apply_affinity(mask)
    return {"schema": "heterospec.358h.runtime.v0.3.target_diagnostic",
            "stage": stage, "formal": False,
            "claim_status": "DIAGNOSTIC / INVALID_FOR_PERFORMANCE_CLAIMS",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(), "ac_power_online": True, "affinity": mask,
            "frozen_r1_source": str(R1_NPU / "observations.resolved.json")}


def reproduce54() -> dict:
    record = base_record("reproduce54")
    frozen = frozen_rows(54)
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(54, pool[1])
    runs = []
    for rep in range(3):
        for ub in (1, 2):
            target = pool[ub]
            target.reset_prefill(prompt)
            tokens = target.baseline(OUTPUT_CAP)
            expected = frozen[(rep, f"TARGET_UB{ub}")]["generated_token_ids"]
            runs.append({"repetition": rep, "n_ubatch": ub, "tokens": tokens,
                         "exact_frozen_r1": tokens == expected,
                         "target_history_length": len(target.history),
                         "target_state_position": target.state_position()})
    a = runs[0]["tokens"]
    b = runs[1]["tokens"]
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    record.update({"prompt_token_count": len(prompt), "shared_model": True,
                   "runs": runs, "ub1_repeat_exact": all(r["tokens"] == a for r in runs if r["n_ubatch"] == 1),
                   "ub2_repeat_exact": all(r["tokens"] == b for r in runs if r["n_ubatch"] == 2),
                   "first_divergence_index": first,
                   "first_divergence_tokens": None if first is None else {"UB1": a[first], "UB2": b[first]}})
    record["pass"] = (all(r["exact_frozen_r1"] for r in runs) and record["ub1_repeat_exact"]
                      and record["ub2_repeat_exact"] and first == 26
                      and (a[first], b[first]) == (73594, 151645))
    return record


def trace54() -> dict:
    record = base_record("trace54")
    frozen = frozen_rows(54)
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(54, pool[1])
    traces = {f"UB{ub}": target_trace(pool[ub], prompt) for ub in (1, 2)}
    record["traces"] = traces
    record["focused_window"] = {k: v["trace"][21:32] for k, v in traces.items()}
    record["pass"] = all(traces[f"UB{ub}"]["tokens"] == frozen[(0, f"TARGET_UB{ub}")]["generated_token_ids"]
                         for ub in (1, 2))
    return record


def prefix54() -> dict:
    record = base_record("prefix54")
    frozen = frozen_rows(54)
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(54, pool[1])
    rows = []
    for i in range(22, 28):
        for ub in (1, 2):
            target = pool[ub]
            target.reset_prefill(prompt + reference[:i])
            row = {"output_index": i, "n_ubatch": ub, "teacher_forced_reference_prefix": True,
                   "input_prefix_length": len(target.history),
                   "next_token": target.next_token(), "target_state_position": target.state_position(),
                   **top2(target)}
            rows.append(row)
    record.update({"rows": rows, "shared_model": True,
                   "fresh_state_per_prefix": True,
                   "reference_prefix_sha256": __import__("hashlib").sha256(
                       json.dumps(reference[:27]).encode()).hexdigest()})
    return record


def order54() -> dict:
    record = base_record("order54")
    frozen = frozen_rows(54)
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(54, pool[1])
    orders = [(1, 2), (2, 1), (1, 1, 2), (2, 2, 1)]
    rows = []
    for order in orders:
        this = []
        for ub in order:
            target = pool[ub]
            target.reset_prefill(prompt)
            tokens = target.baseline(OUTPUT_CAP)
            this.append({"n_ubatch": ub, "tokens": tokens,
                         "exact_frozen_r1": tokens == frozen[(0, f"TARGET_UB{ub}")]["generated_token_ids"]})
        rows.append({"order": list(order), "requests": this})
    record["orders"] = rows
    record["order_independent"] = all(r["exact_frozen_r1"] for x in rows for r in x["requests"])
    return record


def isolated54(ub: int) -> dict:
    record = base_record(f"isolated54_UB{ub}")
    frozen = frozen_rows(54)
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(ub,))
    target = pool[ub]
    prompt = task_prompt(54, target)
    rows = []
    for rep in range(3):
        target.reset_prefill(prompt)
        tokens = target.baseline(OUTPUT_CAP)
        rows.append({"repetition": rep, "tokens": tokens,
                     "exact_frozen_r1": tokens == frozen[(rep, f"TARGET_UB{ub}")]["generated_token_ids"]})
    record.update({"rows": rows, "only_context_ubatch": ub,
                   "pass": all(r["exact_frozen_r1"] for r in rows)})
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["reproduce54", "trace54", "prefix54", "order54", "isolated54"], required=True)
    ap.add_argument("--ubatch", type=int, choices=(1, 2))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.stage == "isolated54":
        if args.ubatch is None:
            raise ValueError("isolated54 requires --ubatch")
        result = isolated54(args.ubatch)
    else:
        if args.ubatch is not None:
            raise ValueError("--ubatch is for isolated54 only")
        result = {"reproduce54": reproduce54, "trace54": trace54,
                  "prefix54": prefix54, "order54": order54}[args.stage]()
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k in
                      ("stage", "pass", "first_divergence_index", "first_divergence_tokens", "order_independent")},
                     ensure_ascii=False))
    return 0 if result.get("pass", result.get("order_independent", True)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
