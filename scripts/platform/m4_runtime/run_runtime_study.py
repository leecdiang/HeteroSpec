#!/usr/bin/env python3
"""Durable, leakage-gated calibration, qualification, and formal M4 runs."""

import argparse
import hashlib
import json
import math
import random
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"
RUNS = ROOT / "runs/m4/runtime_profitability_control_20260924"
BIN = RUNS / "build/m4-runtime-runner"
TARGET = Path("/Users/lee/.cache/heterospec/models/gguf-qwen3-q8/Qwen3-8B-Q8_0.gguf")
DRAFT = Path("/Users/lee/.cache/heterospec/models/gguf-qwen3-q8/Qwen3-0.6B-Q8_0.gguf")
SEED = 20260924
CAP = 128
REPS = 3
CODE = [
    "scripts/platform/m4_runtime/runtime_runner.cpp",
    "scripts/platform/m4_runtime/build_runtime_runner.py",
    "scripts/platform/m4_runtime/prepare_prompts.py",
    "scripts/platform/m4_runtime/run_runtime_study.py",
    "scripts/platform/m4_runtime/analyze_runtime_study.py",
    "scripts/platform/m4_runtime/runtime_policy.py",
    "scripts/platform/m4_runtime/runtime_logic_unit_tests.py",
    "scripts/platform/m4_runtime/r0_smoke.py",
    "scripts/platform/m4_runtime/validate_r0_traces.py",
    "scripts/platform/m4_runtime/validate_runtime_scaffold.py",
    "scripts/platform/m4_runtime/workload_inventory.py",
    "scripts/platform/m4_runtime/plan_runtime_study.py",
    "benchmarks/m4_runtime/runtime_policy_protocol_v0.json",
    "benchmarks/m4_runtime/POLICY_CANDIDATES.json",
    "benchmarks/m4_runtime/WORKLOAD_INVENTORY.json",
    "benchmarks/m4_runtime/CALIBRATION_SPLIT.json",
    "benchmarks/m4_runtime/QUALIFICATION_SPLIT.json",
    "benchmarks/m4_runtime/HELDOUT_SPLIT.json",
    "benchmarks/m4_runtime/PROMPT_TOKENS.json",
]
CODE += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "scripts/platform/m4_runtime/upstream_headers").glob("*.h"))]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def durable(path, obj):
    with Path(path).open("w", encoding="utf-8") as out:
        json.dump(obj, out, indent=2, ensure_ascii=False)
        out.write("\n")
        out.flush()
        import os
        os.fsync(out.fileno())


def append(path, obj):
    with Path(path).open("a", encoding="utf-8") as out:
        out.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
        out.flush()
        import os
        os.fsync(out.fileno())


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def run_text(*cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=10).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return f"UNAVAILABLE:{type(exc).__name__}"


def machine():
    return {
        "utc": utc(),
        "hardware_model": run_text("sysctl", "-n", "hw.model"),
        "macos": run_text("sw_vers", "-productVersion"),
        "macos_build": run_text("sw_vers", "-buildVersion"),
        "power": run_text("pmset", "-g", "batt"),
        "thermal": run_text("pmset", "-g", "therm"),
        "power_settings": run_text("pmset", "-g", "custom"),
    }


def identity(row):
    return (row["workload_family"], row["task_id"])


def prompts(split):
    data = json.loads((BASE / "PROMPT_TOKENS.json").read_text())["tasks"]
    return [row for row in data if row["split"] == split]


def candidates():
    data = json.loads((BASE / "POLICY_CANDIDATES.json").read_text())
    result = []
    for E in data["exploration_rounds_E"]:
        for margin in data["margins"]:
            result.append((f"E{E}_M{round(100*margin):03d}", E, margin))
    if [x[0] for x in result] != data["candidate_ids"]:
        raise RuntimeError("Candidate grid changed")
    return result


class Runner:
    def __init__(self, stderr_path):
        command = [str(BIN), "--model", str(TARGET), "--model-draft", str(DRAFT),
                   "--device", "MTL0", "--n-gpu-layers", "all", "--spec-type", "draft-simple",
                   "--spec-draft-device", "MTL0", "--spec-draft-ngl", "all",
                   "--spec-draft-n-max", "2", "--spec-draft-n-min", "0",
                   "--temp", "0", "--top-k", "0", "--top-p", "1", "--min-p", "0",
                   "--seed", "123", "--ctx-size", "2048", "--batch-size", "2048"]
        self.stderr = Path(stderr_path).open("w", encoding="utf-8")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr, text=True, bufsize=1)
        if self.process.stdout.readline().strip() != "READY":
            raise RuntimeError("M4 runner failed to initialize")
        self.command = command

    def one(self, row, condition, E=2, margin=0.05, target_ref=0.0):
        line = "\t".join([condition, str(E), str(margin), str(target_ref), str(CAP),
                          ",".join(map(str, row["prompt_token_ids"]))]) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()
        raw = self.process.stdout.readline()
        if not raw:
            raise RuntimeError(f"M4 runner exited unexpectedly: {self.process.poll()}")
        result = json.loads(raw)
        if result.get("status") != "OK":
            raise RuntimeError(f"M4 runner error: {result}")
        ids = result.get("generated_token_ids")
        if not isinstance(ids, list) or not ids or len(ids) > CAP or result["generated_token_count"] != len(ids):
            raise RuntimeError("Invalid direct generated-token record")
        if result["end_to_end_ns"] <= 0 or result["speculative_committed_token_count"] + result["target_only_committed_token_count"] != len(ids):
            raise RuntimeError("Invalid latency or progress accounting")
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write("QUIT\n")
            self.process.stdin.flush()
            self.process.wait(timeout=30)
        self.stderr.close()
        if self.process.returncode:
            raise RuntimeError(f"M4 runner exited {self.process.returncode}")


def attempt(stage, attempt_id):
    if not attempt_id or "/" in attempt_id or ".." in attempt_id:
        raise ValueError("Provide a simple unique attempt ID")
    path = RUNS / stage / attempt_id
    path.mkdir(parents=True, exist_ok=False)
    return path


def schedule(rows, variants, salt):
    rng = random.Random(SEED + salt)
    result = []
    for row in rows:
        for rep in range(REPS):
            order = list(variants)
            rng.shuffle(order)
            for name, condition, E, margin in order:
                result.append((row, rep, name, condition, E, margin))
    return result


def warmup(runner, target_ref):
    reference = json.loads((RUNS / "r0/server_reference.json").read_text())
    row = {"prompt_token_ids": reference["prompt_token_ids"]}
    runs = [runner.one(row, "TARGET_ONLY"), runner.one(row, "ALWAYS_SPEC_K2"),
            runner.one(row, "GUARD_K2", target_ref=target_ref),
            runner.one(row, "GUARD_K2", target_ref=1)]
    if not all(x["generated_token_ids"] == runs[0]["generated_token_ids"] for x in runs):
        raise RuntimeError("Historical warmup direct-ID mismatch")
    return runs


def run_stage(stage, attempt_id, variants, target_ref, salt, freeze_sha=None):
    rows = prompts("CALIBRATION" if stage in ("calibration_baselines", "calibration_candidates")
                   else "QUALIFICATION" if stage == "qualification" else "HELDOUT")
    path = attempt(stage, attempt_id)
    obs = path / "observations.jsonl"
    plan = schedule(rows, variants, salt)
    durable(path / "manifest.json", {
        "schema": "heterospec.m4_runtime.attempt.v0.1", "stage": stage,
        "attempt_id": attempt_id, "created_utc": utc(), "planned_observations": len(plan),
        "binary_sha256": sha(BIN), "prompt_tokens_sha256": sha(BASE / "PROMPT_TOKENS.json"),
        "source_data_sha256": {name: sha(ROOT / name) for name in CODE},
        "build_manifest_sha256": sha(RUNS / "build/manifest.json"),
        "target_reference_ns_per_token": target_ref, "freeze_sha256": freeze_sha,
        "environment_before": machine(),
    })
    runner = Runner(path / "runner_stderr.txt")
    try:
        manifest = json.loads((path / "manifest.json").read_text())
        manifest["runner_command"] = runner.command
        durable(path / "manifest.json", manifest)
        warmups = warmup(runner, target_ref if target_ref > 0 else 1e12)
        durable(path / "warmup.json", {"historical_task_id": "HumanEval/89", "records": warmups,
                                      "timing_role": "NON_FORMAL"})
        for idx, (row, rep, name, condition, E, margin) in enumerate(plan):
            result = runner.one(row, condition, E, margin, target_ref)
            record = {
                "observation_index": idx, "observed_utc": utc(), "stage": stage,
                "task_id": row["task_id"], "workload_family": row["workload_family"],
                "stratum": row["stratum"], "repetition": rep,
                "condition": condition, "candidate_id": name,
                "E": E, "margin": margin,
                "raw_prompt_sha256": row["raw_prompt_sha256"],
                "formatted_prompt_sha256": row["formatted_prompt_sha256"],
                "prompt_token_count": row["prompt_token_count"],
                "power_thermal": machine(), "result": result,
            }
            append(obs, record)
            if stage == "formal" and ("AC Power" not in record["power_thermal"]["power"] or
                                      "No thermal warning level has been recorded" not in record["power_thermal"]["thermal"]):
                raise RuntimeError("Formal power/thermal environment invalidated; retain full attempt")
            if idx % 20 == 0 or idx + 1 == len(plan):
                print(f"{stage}: {idx+1}/{len(plan)}", flush=True)
    except BaseException as exc:
        durable(path / "ABORTED.json", {
            "status": "ABORTED", "aborted_utc": utc(),
            "reason": f"{type(exc).__name__}: {exc}",
            "observations_retained": len(read_jsonl(obs)) if obs.exists() else 0,
            "observations_sha256": sha(obs) if obs.exists() else None,
            "no_selective_rerun": True,
        })
        raise
    finally:
        runner.close()
    durable(path / "completion.json", {
        "status": "COMPLETE", "completed_utc": utc(), "observations": len(plan),
        "observations_sha256": sha(obs), "environment_after": machine(),
    })
    return path


def require_complete(stage, attempt_id, expected):
    path = RUNS / stage / attempt_id
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest["binary_sha256"] != sha(BIN) or manifest["prompt_tokens_sha256"] != sha(BASE / "PROMPT_TOKENS.json"):
        raise RuntimeError(f"Runner or prompt tokens changed since {stage} attempt")
    if manifest["build_manifest_sha256"] != sha(RUNS / "build/manifest.json"):
        raise RuntimeError(f"Build manifest changed since {stage} attempt")
    for name, digest in manifest["source_data_sha256"].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError(f"Source/data changed since {stage} attempt: {name}")
    completed = json.loads((path / "completion.json").read_text())
    rows = read_jsonl(path / "observations.jsonl")
    if completed["status"] != "COMPLETE" or len(rows) != expected or completed["observations_sha256"] != sha(path / "observations.jsonl"):
        raise RuntimeError(f"Incomplete or changed {stage} attempt")
    if sorted(x["observation_index"] for x in rows) != list(range(expected)):
        raise RuntimeError(f"Missing {stage} observation index")
    return path, rows


def baseline_data(attempt_id):
    path, rows = require_complete("calibration_baselines", attempt_id, 40 * REPS * 2)
    by = {(identity(x), x["repetition"], x["condition"]): x for x in rows}
    ratios = []
    for task in prompts("CALIBRATION"):
        target = []
        counts = []
        for rep in range(REPS):
            a = by[(identity(task), rep, "TARGET_ONLY")]["result"]
            b = by[(identity(task), rep, "ALWAYS_SPEC_K2")]["result"]
            if a["generated_token_ids"] != b["generated_token_ids"]:
                raise RuntimeError(f"Baseline direct-ID mismatch: {identity(task)}, repetition {rep}")
            target.append(a["end_to_end_ns"])
            counts.append(a["generated_token_count"])
        count = statistics.median(counts)
        if count <= 0:
            raise RuntimeError("Calibration generated-token count is nonpositive")
        ratios.append(statistics.median(target) / count)
    return path, by, statistics.median(ratios)


def select(baseline_attempt, candidate_attempt):
    base_path, baseline, target_ref = baseline_data(baseline_attempt)
    cand_path, rows = require_complete("calibration_candidates", candidate_attempt, 40 * REPS * 9)
    manifest = json.loads((cand_path / "manifest.json").read_text())
    if manifest["target_reference_ns_per_token"] != target_ref:
        raise RuntimeError("Candidate target reference changed")
    by = {(identity(x), x["repetition"], x["candidate_id"]): x for x in rows}
    scores = []
    for candidate_id, E, margin in candidates():
        regret = []
        overhead = []
        exact = True
        mismatches = []
        for task in prompts("CALIBRATION"):
            tid = identity(task)
            tg = [baseline[(tid, rep, "TARGET_ONLY")]["result"]["end_to_end_ns"] for rep in range(REPS)]
            sp = [baseline[(tid, rep, "ALWAYS_SPEC_K2")]["result"]["end_to_end_ns"] for rep in range(REPS)]
            guard = []
            for rep in range(REPS):
                row = by[(tid, rep, candidate_id)]["result"]
                guard.append(row["end_to_end_ns"])
                overhead.append(row["guard_compute_ns"])
                if row["generated_token_ids"] != baseline[(tid, rep, "TARGET_ONLY")]["result"]["generated_token_ids"]:
                    exact = False
                    mismatches.append({"task": tid, "repetition": rep})
            oracle = min(statistics.median(tg), statistics.median(sp))
            regret.append(statistics.median(guard) / oracle)
        scores.append({
            "candidate_id": candidate_id, "E": E, "margin": margin,
            "direct_id_exact": exact, "mismatches": mismatches,
            "geometric_mean_oracle_regret": math.exp(statistics.mean(map(math.log, regret))),
            "mean_guard_compute_ns": statistics.mean(overhead),
        })
    admissible = [x for x in scores if x["direct_id_exact"]]
    if not admissible:
        raise RuntimeError("No exact calibration candidate")
    winner = min(admissible, key=lambda x: (x["geometric_mean_oracle_regret"],
                                      x["mean_guard_compute_ns"], x["E"], -x["margin"], x["candidate_id"]))
    return base_path, cand_path, target_ref, scores, winner


def freeze(baseline_attempt, candidate_attempt):
    base_path, cand_path, target_ref, scores, winner = select(baseline_attempt, candidate_attempt)
    record = {
        "schema": "heterospec.m4_runtime.calibration_freeze.v0.1",
        "status": "CALIBRATION_FROZEN", "frozen_utc": utc(),
        "formal_heldout_data_seen": False,
        "baseline_attempt": baseline_attempt, "candidate_attempt": candidate_attempt,
        "baseline_observations_sha256": sha(base_path / "observations.jsonl"),
        "candidate_observations_sha256": sha(cand_path / "observations.jsonl"),
        "target_reference_ns_per_token": target_ref,
        "candidate_scores": scores, "selected": winner,
        "source_data_sha256": {name: sha(ROOT / name) for name in CODE},
        "target_sha256": sha(TARGET), "draft_sha256": sha(DRAFT),
        "binary_sha256": sha(BIN),
        "build_manifest_sha256": sha(RUNS / "build/manifest.json"),
        "environment": machine(),
    }
    durable(BASE / "CALIBRATION_FREEZE.json", record)
    print(json.dumps({"selected": winner, "target_reference_ns_per_token": target_ref}, indent=2))


def frozen():
    path = BASE / "CALIBRATION_FREEZE.json"
    data = json.loads(path.read_text())
    if data["status"] != "CALIBRATION_FROZEN" or data["formal_heldout_data_seen"] is not False:
        raise RuntimeError("Invalid calibration freeze")
    for name, digest in data["source_data_sha256"].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError(f"Frozen file changed: {name}")
    for item, path in (("target_sha256", TARGET), ("draft_sha256", DRAFT),
                       ("binary_sha256", BIN), ("build_manifest_sha256", RUNS / "build/manifest.json")):
        if sha(path) != data[item]:
            raise RuntimeError(f"Frozen artifact changed: {item}")
    base_path, cand_path, target_ref, _, winner = select(data["baseline_attempt"], data["candidate_attempt"])
    if sha(base_path / "observations.jsonl") != data["baseline_observations_sha256"] or sha(cand_path / "observations.jsonl") != data["candidate_observations_sha256"]:
        raise RuntimeError("Frozen raw calibration changed")
    if target_ref != data["target_reference_ns_per_token"] or winner != data["selected"]:
        raise RuntimeError("Calibration selection changed")
    return path, data


def qualify(attempt_id):
    path, freeze_data = frozen()
    selected = freeze_data["selected"]
    variants = [("TARGET_ONLY", "TARGET_ONLY", 2, 0.05),
                ("ALWAYS_SPEC_K2", "ALWAYS_SPEC_K2", 2, 0.05),
                (selected["candidate_id"], "GUARD_K2", selected["E"], selected["margin"])]
    run_path = run_stage("qualification", attempt_id, variants,
                         freeze_data["target_reference_ns_per_token"], 2, sha(path))
    _, rows = require_complete("qualification", attempt_id, 16 * REPS * 3)
    by = {(identity(x), x["repetition"], x["condition"]): x for x in rows}
    counts = {"ALWAYS_SPEC_K2": 0, "GUARD_K2": 0}
    mismatches = []
    for task in prompts("QUALIFICATION"):
        for rep in range(REPS):
            target = by[(identity(task), rep, "TARGET_ONLY")]["result"]["generated_token_ids"]
            for condition in counts:
                other = by[(identity(task), rep, condition)]["result"]["generated_token_ids"]
                if target == other:
                    counts[condition] += 1
                else:
                    mismatch_at = next((i for i, (a, b) in enumerate(zip(target, other)) if a != b), min(len(target), len(other)))
                    mismatches.append({"task": identity(task), "repetition": rep,
                                       "condition": condition, "first_mismatch_index": mismatch_at,
                                       "target_id": target[mismatch_at] if mismatch_at < len(target) else None,
                                       "other_id": other[mismatch_at] if mismatch_at < len(other) else None})
    report = {
        "schema": "heterospec.m4_runtime.qualification.v0.1",
        "status": "PASS" if counts == {"ALWAYS_SPEC_K2": 48, "GUARD_K2": 48} else "FAIL",
        "attempt_id": attempt_id, "completed_utc": utc(),
        "counts": counts, "required_per_condition": 48, "mismatches": mismatches,
        "freeze_sha256": sha(path), "observations_sha256": sha(run_path / "observations.jsonl"),
    }
    durable(BASE / "QUALIFICATION_REPORT.json", report)
    print(json.dumps({"status": report["status"], "counts": counts, "mismatches": mismatches[:3]}, indent=2))
    if report["status"] != "PASS":
        raise RuntimeError("Qualification direct-ID exactness failed")


def formal(attempt_id):
    freeze_path, freeze_data = frozen()
    qualification = json.loads((BASE / "QUALIFICATION_REPORT.json").read_text())
    if qualification["status"] != "PASS" or qualification["counts"] != {"ALWAYS_SPEC_K2": 48, "GUARD_K2": 48}:
        raise RuntimeError("Qualification PASS is required")
    if qualification["freeze_sha256"] != sha(freeze_path):
        raise RuntimeError("Qualification freeze hash changed")
    qpath, _ = require_complete("qualification", qualification["attempt_id"], 16 * REPS * 3)
    if qualification["observations_sha256"] != sha(qpath / "observations.jsonl"):
        raise RuntimeError("Qualification raw data changed")
    if git("status", "--porcelain"):
        raise RuntimeError("Formal run requires a clean committed tree")
    current_environment = machine()
    for field in ("hardware_model", "macos", "macos_build", "power_settings"):
        if current_environment[field] != freeze_data["environment"][field]:
            raise RuntimeError(f"Frozen environment changed: {field}")
    if "AC Power" not in current_environment["power"] or "No thermal warning level has been recorded" not in current_environment["thermal"]:
        raise RuntimeError("Formal run requires AC power and no thermal warning")
    build = json.loads((RUNS / "build/manifest.json").read_text())
    if build["upstream_version"] != run_text("/opt/homebrew/bin/llama-server", "--version"):
        raise RuntimeError("Pinned llama.cpp version changed")
    selected = freeze_data["selected"]
    variants = [("TARGET_ONLY", "TARGET_ONLY", 2, 0.05),
                ("ALWAYS_SPEC_K2", "ALWAYS_SPEC_K2", 2, 0.05),
                (selected["candidate_id"], "GUARD_K2", selected["E"], selected["margin"])]
    if (RUNS / "formal" / attempt_id).exists():
        raise RuntimeError("Formal attempt ID already exists")
    marker = RUNS / "FORMAL_DATA_STARTED"
    if not marker.exists():
        durable(marker, {"status": "FORMAL_DATA_STARTED", "started_utc": utc(),
                         "attempt_id": attempt_id, "freeze_sha256": sha(freeze_path),
                         "qualification_sha256": sha(BASE / "QUALIFICATION_REPORT.json"),
                         "head": git("rev-parse", "HEAD")})
    else:
        prior = json.loads(marker.read_text())
        if prior["freeze_sha256"] != sha(freeze_path) or prior["qualification_sha256"] != sha(BASE / "QUALIFICATION_REPORT.json"):
            raise RuntimeError("Formal freeze or qualification changed since first attempt")
    per_attempt_marker = RUNS / f"FORMAL_ATTEMPT_{attempt_id}_STARTED"
    if per_attempt_marker.exists():
        raise RuntimeError("Formal attempt marker already exists")
    durable(per_attempt_marker, {
        "status": "FORMAL_DATA_STARTED", "started_utc": utc(), "attempt_id": attempt_id,
        "freeze_sha256": sha(freeze_path), "qualification_sha256": sha(BASE / "QUALIFICATION_REPORT.json"),
    })
    run_stage("formal", attempt_id, variants,
              freeze_data["target_reference_ns_per_token"], 0, sha(freeze_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("baselines", "candidates", "freeze", "qualify", "formal"):
        item = sub.add_parser(name)
        if name in ("baselines", "candidates", "qualify", "formal"):
            item.add_argument("--attempt", required=True)
        if name in ("candidates", "freeze"):
            item.add_argument("--baseline-attempt", required=True)
        if name == "freeze":
            item.add_argument("--candidate-attempt", required=True)
    args = parser.parse_args()
    if args.action == "baselines":
        run_stage("calibration_baselines", args.attempt,
                  [("TARGET_ONLY", "TARGET_ONLY", 2, 0.05),
                   ("ALWAYS_SPEC_K2", "ALWAYS_SPEC_K2", 2, 0.05)], 0.0, 0)
    elif args.action == "candidates":
        _, _, target_ref = baseline_data(args.baseline_attempt)
        run_stage("calibration_candidates", args.attempt,
                  [(name, "GUARD_K2", E, margin) for name, E, margin in candidates()],
                  target_ref, 1)
    elif args.action == "freeze":
        freeze(args.baseline_attempt, args.candidate_attempt)
    elif args.action == "qualify":
        qualify(args.attempt)
    elif args.action == "formal":
        formal(args.attempt)
