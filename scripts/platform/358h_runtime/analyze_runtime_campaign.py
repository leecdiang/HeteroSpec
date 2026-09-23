#!/usr/bin/env python3
"""Deterministic analysis for the prospective 358H R2 runtime campaign."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np

BOOTSTRAP_SEED = 20260923
BOOTSTRAP_N = 10000
EXPECTED_PROMPTS = 30
EXPECTED_REPS = 3


def gm(values: list[float]) -> float:
    a = np.asarray(values, dtype=float)
    if len(a) == 0 or np.any(a <= 0):
        raise ValueError("geometric mean requires positive non-empty values")
    return float(math.exp(np.mean(np.log(a))))


def bootstrap_gm(values: list[float]) -> list[float]:
    a = np.asarray(values, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(a), size=(BOOTSTRAP_N, len(a)))
    draws = np.exp(np.mean(np.log(a[idx]), axis=1))
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def task_num(task_id: str) -> int:
    return int(task_id.split("/")[-1])


def prompt_median_ratios(
    left: dict[tuple[str, int], dict],
    right: dict[tuple[str, int], dict],
    numerator: Callable[[dict], float],
    denominator: Callable[[dict], float],
) -> tuple[list[dict[str, Any]], list[float]]:
    by_prompt: dict[str, list[float]] = defaultdict(list)
    pair_rows = []
    keys = sorted(set(left) & set(right), key=lambda x: (task_num(x[0]), x[1]))
    if len(keys) != EXPECTED_PROMPTS * EXPECTED_REPS:
        raise RuntimeError(f"paired comparison has {len(keys)} pairs; expected 90")
    for key in keys:
        n = float(numerator(left[key]))
        d = float(denominator(right[key]))
        if n <= 0 or d <= 0:
            raise RuntimeError(f"non-positive timing in pair {key}: {n}, {d}")
        ratio = n / d
        by_prompt[key[0]].append(ratio)
        pair_rows.append({"task_id": key[0], "repetition": key[1], "ratio": ratio})
    medians = []
    for prompt in sorted(by_prompt, key=task_num):
        vals = by_prompt[prompt]
        if len(vals) != EXPECTED_REPS:
            raise RuntimeError(f"{prompt}: expected 3 repetitions, got {len(vals)}")
        medians.append(float(np.median(vals)))
    if len(medians) != EXPECTED_PROMPTS:
        raise RuntimeError(f"expected 30 prompt medians, got {len(medians)}")
    return pair_rows, medians


def ratio_summary(medians: list[float]) -> dict[str, Any]:
    return {
        "geometric_mean_ratio": gm(medians),
        "median_prompt_ratio": float(np.median(medians)),
        "bootstrap_ci95": bootstrap_gm(medians),
        "prompts_ratio_gt_1": int(sum(x > 1.0 for x in medians)),
        "total_prompts": len(medians),
        "bootstrap_unit": "HumanEval prompt; input is per-prompt median across 3 repetitions",
        "bootstrap_resamples": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }


def draft_total(row: dict) -> float:
    t = row["timing"]
    return float(
        t.get("draft_begin_ns", 0)
        + t.get("draft_checkpoint_ns", 0)
        + t.get("draft_propose_ns", 0)
        + t.get("draft_reconcile_ns", 0)
        + t.get("draft_finish_ns", 0)
    )


def index_rows(rows: list[dict], path: str) -> dict[tuple[str, int], dict]:
    subset = [r for r in rows if r["path"] == path]
    index = {(r["task_id"], int(r["repetition"])): r for r in subset}
    if len(subset) != len(index):
        raise RuntimeError(f"duplicate task/repetition observations for {path}")
    return index


def arithmetic_decomposition(rows: list[dict]) -> dict[str, Any]:
    fields = [
        "end_to_end_ns",
        "draft_begin_ns",
        "draft_checkpoint_ns",
        "draft_propose_ns",
        "draft_reconcile_ns",
        "draft_finish_ns",
        "target_verification_ns",
        "runtime_residual_ns",
    ]
    means = {f.replace("_ns", "_ms"): float(np.mean([r["timing"].get(f, 0) for r in rows]) / 1e6) for f in fields}
    spec_mean = means["end_to_end_ms"]
    draft_ms = sum(means[x] for x in [
        "draft_begin_ms", "draft_checkpoint_ms", "draft_propose_ms", "draft_reconcile_ms", "draft_finish_ms"
    ])
    means["draft_total_ms"] = draft_ms
    means["draft_fraction"] = draft_ms / spec_mean if spec_mean else None
    means["target_fraction"] = means["target_verification_ms"] / spec_mean if spec_mean else None
    means["residual_fraction"] = means["runtime_residual_ms"] / spec_mean if spec_mean else None
    return means


def acceptance_summary(rows: list[dict]) -> dict[str, Any]:
    proposed = sum(int(r.get("proposed", 0)) for r in rows)
    accepted = sum(int(r.get("accepted", 0)) for r in rows)
    rounds = [q for r in rows for q in r.get("rounds", []) if not q.get("native_initial_target_only")]
    committed = sum(int(q.get("C", 0)) for q in rounds)
    rc = Counter(int(q.get("accepted", 0)) for q in rounds)
    return {
        "proposed_tokens": proposed,
        "accepted_draft_tokens": accepted,
        "weighted_acceptance_rate": accepted / proposed if proposed else None,
        "speculative_rounds": len(rounds),
        "mean_committed_tokens_per_round_C": committed / len(rounds) if rounds else None,
        "rounds_by_accepted_draft_tokens": {str(k): int(rc[k]) for k in (0, 1, 2)},
    }


def state_accounting(rows: list[dict]) -> dict[str, Any]:
    rounds = [q for r in rows for q in r.get("rounds", []) if not q.get("native_initial_target_only")]
    return {
        "checkpoint_bytes_mean_per_round": float(np.mean([q.get("checkpoint_bytes", 0) for q in rounds])) if rounds else 0.0,
        "checkpoint_bytes_max": int(max([q.get("checkpoint_bytes", 0) for q in rounds], default=0)),
        "state_transfer_bytes_mean_per_round": float(np.mean([q.get("state_transfer_bytes", 0) for q in rounds])) if rounds else 0.0,
        "state_transfer_bytes_max": int(max([q.get("state_transfer_bytes", 0) for q in rounds], default=0)),
        "fallback_events": int(sum(len(q.get("fallback_events", [])) for q in rounds)),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    status = json.loads((args.campaign_dir / "R2_STATUS.json").read_text(encoding="utf-8"))
    rows = json.loads((args.campaign_dir / "observations.resolved.json").read_text(encoding="utf-8"))
    if status.get("formal") is not True or not status.get("complete"):
        raise RuntimeError("R2 campaign is not a complete formal study")
    conditions = list(status.get("conditions", []))
    if not conditions or conditions[0] != "TARGET_UB1":
        raise RuntimeError("TARGET_UB1 reference missing from frozen condition set")
    expected_rows = EXPECTED_PROMPTS * EXPECTED_REPS * len(conditions)
    if len(rows) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} observations, got {len(rows)}")

    exact_counts = status.get("exact_counts", {})
    admissible = {
        name: bool(exact_counts.get(name, {}).get("performance_admissible"))
        for name in conditions
    }
    if not admissible.get("TARGET_UB1"):
        raise RuntimeError("TARGET_UB1 reference itself is not exact/admissible")

    target = index_rows(rows, "TARGET_UB1")
    summary: dict[str, Any] = {
        "schema": "heterospec.358h.runtime.r2_analysis.v1",
        "campaign": str(args.campaign_dir),
        "formal": True,
        "energy": "NOT_CLAIMED",
        "conditions": conditions,
        "admissible": admissible,
        "system": {},
        "component_state_reuse": {},
        "target_path": {},
        "decomposition": {},
        "acceptance": {},
        "state_accounting": {},
        "interpretation_rule": "component improvement and system profitability are separate outcomes; correctness-blocked timing remains diagnostic only",
    }
    prompt_rows: list[dict[str, Any]] = []

    for name in conditions:
        subset = [r for r in rows if r["path"] == name]
        summary["decomposition"][name] = arithmetic_decomposition(subset)
        summary["acceptance"][name] = acceptance_summary(subset)
        summary["state_accounting"][name] = state_accounting(subset)
        if name == "TARGET_UB1" or not admissible[name]:
            continue
        cand = index_rows(rows, name)
        pairs, medians = prompt_median_ratios(
            target,
            cand,
            numerator=lambda r: r["timing"]["end_to_end_ns"],
            denominator=lambda r: r["timing"]["end_to_end_ns"],
        )
        system = ratio_summary(medians)
        system["definition"] = "TARGET_UB1 post-prefill decode time / runtime path post-prefill decode time"
        summary["system"][name] = system
        by_prompt = defaultdict(list)
        for p in pairs:
            by_prompt[p["task_id"]].append(p["ratio"])
        for task in sorted(by_prompt, key=task_num):
            prompt_rows.append({
                "comparison": f"SYSTEM:{name}",
                "task_id": task,
                "prompt_median_ratio": float(np.median(by_prompt[task])),
            })

    # Primary state-reuse comparison: same frontend/device/target ubatch.
    for device in ("CPU", "NPU"):
        replay = f"OPTIMUM_REPLAY_{device}_UB1"
        persist = f"PERSIST_{device}_UB1"
        if replay in conditions and persist in conditions and admissible.get(replay) and admissible.get(persist):
            left = index_rows(rows, replay)
            right = index_rows(rows, persist)
            _, medians = prompt_median_ratios(left, right, draft_total, draft_total)
            result = ratio_summary(medians)
            result["definition"] = "same-frontend replay complete draft-subsystem time / persistent complete draft-subsystem time"
            summary["component_state_reuse"][device] = result

    # Target-path comparison: same draft frontend/state policy/device, UB1 vs UB2.
    ub2_pairs = [
        ("PERSIST_NPU_UB1", "PERSIST_NPU_UB2"),
        ("LEGACY_NPU_UB1", "LEGACY_NPU_UB2"),
    ]
    for ub1, ub2 in ub2_pairs:
        if ub1 in conditions and ub2 in conditions and admissible.get(ub1) and admissible.get(ub2):
            left = index_rows(rows, ub1)
            right = index_rows(rows, ub2)
            _, medians = prompt_median_ratios(
                left,
                right,
                numerator=lambda r: r["timing"]["target_verification_ns"],
                denominator=lambda r: r["timing"]["target_verification_ns"],
            )
            result = ratio_summary(medians)
            result["definition"] = "same-policy UB1 target-verification time / UB2 target-verification time"
            result["ub1"] = ub1
            result["ub2"] = ub2
            summary["target_path"]["NPU"] = result
            break

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "runtime_r2_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_csv(args.output_dir / "runtime_r2_prompt_ratios.csv", prompt_rows)

    decomposition_rows = []
    for name, values in summary["decomposition"].items():
        decomposition_rows.append({"path": name, **values})
    write_csv(args.output_dir / "runtime_r2_decomposition.csv", decomposition_rows)

    print(json.dumps({
        "system": summary["system"],
        "component_state_reuse": summary["component_state_reuse"],
        "target_path": summary["target_path"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
