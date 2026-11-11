from __future__ import annotations

import os

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
LOGS = ROOT / "logs"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

RUN_COLUMNS = [
    "run_id", "experiment", "model_pair", "target_size", "config", "k",
    "prompt_id", "task", "input_tokens", "output_tokens", "ttft_ms",
    "completion_ms", "tok_s", "tpot_ms", "itl_p50_ms", "itl_p95_ms",
    "acceptance", "draft_tokens", "accepted_tokens", "verification_rounds",
    "draft_ms", "verify_ms", "sync_ms", "kv_ms", "other_ms", "rtx_avg_W",
    "rtx_peak_W", "rtx_energy_J", "rtx_J_per_token", "cpu_pkg_avg_W",
    "cpu_pkg_peak_W", "cpu_pkg_energy_J", "igpu_avg_W", "npu_avg_W",
    "rtx_peak_vram_MB", "exact_match", "valid", "invalid_reason", "source_file",
]


def load(name: str) -> dict:
    return json.loads((LOGS / name).read_text(encoding="utf-8"))


def k_from_config(config: str):
    if "-k" in config:
        try:
            return int(config.rsplit("-k", 1)[1])
        except ValueError:
            return np.nan
    return np.nan


def flatten_question_log(name: str, experiment: str, model_pair: str, target_size: str,
                         invalid_if_inexact: bool = False) -> tuple[list[dict], list[dict]]:
    data = load(name)
    rows, rounds = [], []
    for question in data.get("questions", []):
        baseline_hash = None
        for cfg in question["configs"]:
            if "baseline" in cfg["config"].lower() or cfg["config"] == "B0":
                baseline_hash = cfg["turns"][0].get("token_sha256") if cfg.get("turns") else None
                break
        for cfg in question["configs"]:
            for turn in cfg.get("turns", []):
                rr = turn.get("rounds") or []
                offered = sum(r.get("offered", 0) for r in rr)
                accepted = sum(r.get("accepted", 0) for r in rr)
                draft_ms = sum(r.get("draft_ms", 0.0) for r in rr)
                verify_ms = sum(r.get("target_ms", 0.0) for r in rr)
                elapsed_ms = turn.get("seconds", cfg.get("seconds", np.nan)) * 1000
                other_ms = max(0.0, elapsed_ms - draft_ms - verify_ms) if rr else np.nan
                exact = cfg.get("exact_match_to_B0", cfg.get("exact_match_to_baseline"))
                if exact is None and baseline_hash is not None:
                    exact = turn.get("token_sha256") == baseline_hash
                invalid = bool(invalid_if_inexact and exact is False)
                output_tokens = turn.get("output_tokens", np.nan)
                seconds = turn.get("seconds", cfg.get("seconds", np.nan))
                rows.append({
                    "run_id": turn.get("run_id"), "experiment": experiment,
                    "model_pair": model_pair, "target_size": target_size,
                    "config": cfg["config"], "k": k_from_config(cfg["config"]),
                    "prompt_id": question["question_id"], "task": question.get("category"),
                    "input_tokens": turn.get("input_tokens"), "output_tokens": output_tokens,
                    "completion_ms": seconds * 1000, "tok_s": output_tokens / seconds if seconds else np.nan,
                    "tpot_ms": seconds * 1000 / output_tokens if output_tokens else np.nan,
                    "acceptance": accepted / offered if offered else np.nan,
                    "draft_tokens": offered, "accepted_tokens": accepted,
                    "verification_rounds": len(rr), "draft_ms": draft_ms or np.nan,
                    "verify_ms": verify_ms or np.nan, "other_ms": other_ms,
                    "rtx_peak_vram_MB": turn.get("peak_cuda_allocated_gib", np.nan) * 1024,
                    "exact_match": exact, "valid": not invalid,
                    "invalid_reason": "exact_output_mismatch" if invalid else "",
                    "source_file": name,
                })
                for index, r in enumerate(rr):
                    rounds.append({
                        "run_id": turn.get("run_id"), "experiment": experiment,
                        "prompt_id": question["question_id"], "task": question.get("category"),
                        "config": cfg["config"], "k": k_from_config(cfg["config"]),
                        "round_index": index, "offered": r.get("offered"),
                        "accepted": r.get("accepted"), "rejected": r.get("offered", 0) - r.get("accepted", 0),
                        "draft_ms": r.get("draft_ms"), "verify_ms": r.get("target_ms"),
                        "precision_guard": r.get("precision_guard", False),
                    })
    return rows, rounds


def normalize_power() -> pd.DataFrame:
    frames = []
    for path in sorted((ROOT / "telemetry").rglob("*.csv")):
        try:
            frame = pd.read_csv(path)
        except (pd.errors.EmptyDataError, UnicodeDecodeError):
            continue
        if "timestamp" not in frame or "power_W" not in frame:
            continue
        frame["source_file"] = str(path.relative_to(ROOT)).replace("\\", "/")
        if "run_id" not in frame:
            frame["run_id"] = ""
        keep = ["timestamp", "run_id", "power_W", "gpu_util_pct", "memory_util_pct",
                "temperature_C", "sm_clock_MHz", "memory_clock_MHz", "vram_used_MB", "source_file"]
        for column in keep:
            if column not in frame:
                frame[column] = np.nan
        frames.append(frame[keep])
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not result.empty:
        result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce", utc=True)
        result = result.sort_values("timestamp")
    return result


def main() -> None:
    specs = [
        ("phase4-specbench-pilot-cap128-formal-20260906.json", "qwen_60q_k_sweep", "Qwen3-0.6B->Qwen3-8B", "8B", False),
        ("phase5-cpu-rtx-root-cause-12q-20260906.json", "root_cause_cpu_custom", "Qwen3-0.6B->Qwen3-8B", "8B", False),
        ("phase5-rtx-rtx-same-harness-12q-20260906.json", "root_cause_rtx_custom", "Qwen3-0.6B->Qwen3-8B", "8B", False),
        ("phase5-rtx-assisted-root-cause-12q-20260906.json", "root_cause_rtx_native", "Qwen3-0.6B->Qwen3-8B", "8B", False),
        ("phase6-qwen3-14b-native-cpu-assist-12q-20260906.json", "crossover_cpu_native", "Qwen3-0.6B->Qwen3-14B", "14B", True),
    ]
    all_runs, all_rounds = [], []
    for spec in specs:
        rows, rounds = flatten_question_log(*spec)
        all_runs.extend(rows)
        all_rounds.extend(rounds)
    runs = pd.DataFrame(all_runs)
    for column in RUN_COLUMNS:
        if column not in runs:
            runs[column] = np.nan
    runs[RUN_COLUMNS].to_csv(OUT / "all_runs.csv", index=False)
    pd.DataFrame(all_rounds).to_csv(OUT / "all_rounds.csv", index=False)
    normalize_power().to_csv(OUT / "all_power_1s.csv", index=False)

    models = pd.DataFrame([
        {"model": "Qwen3-0.6B", "role": "draft", "revision": "see env/model manifest/export metadata", "runtime": "OpenVINO / Transformers"},
        {"model": "Qwen3-8B", "role": "target", "revision": "see env/qwen3-8b-manifest.json", "runtime": "PyTorch CUDA NF4"},
        {"model": "Qwen3-14B", "role": "target", "revision": "40c069824f4251a91eefaf281ebe4c544efd3e18", "runtime": "PyTorch CUDA NF4"},
    ])
    models.to_csv(OUT / "all_models.csv", index=False)
    profile = json.loads((ROOT / "system_profile.json").read_text(encoding="utf-8"))
    pd.json_normalize(profile, sep=".").to_csv(OUT / "all_system_configs.csv", index=False)

    summary = {
        "created_from_existing_logs": True,
        "all_runs_rows": len(runs), "all_rounds_rows": len(all_rounds),
        "all_power_rows": len(normalize_power()),
        "known_missing_fields": ["ttft_ms", "itl_p50_ms", "itl_p95_ms", "sync_ms", "kv_ms",
                                 "cpu_pkg_*", "run-aligned energy for historical runs"],
        "policy": "Missing measurements remain null; no retrospective estimates are represented as measurements.",
    }
    (OUT / "DATASET_STATUS.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
