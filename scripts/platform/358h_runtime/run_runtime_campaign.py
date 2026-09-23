#!/usr/bin/env python3
"""Future R2 entrypoint; formal timing is measured inside the v0.2 target worker."""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

import psutil

from run_runtime_qualification import (DATASET_SHA256, FULL, OUTPUT_CAP, assert_host_gate,
    formatted_prompt, load_tasks, sha256, utc, write_json)
from runtime_factory import parse_path
from runtime_freeze import verify_freeze_manifest
from runtime_process_v02 import apply_affinity
from runtime_session_v02 import RuntimeProcessSession, draft_groups, prepare_legacy_npu_cache
from runtime_types import first_divergence

SEED = 20260925


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--freeze-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    assert_host_gate()
    freeze = verify_freeze_manifest(args.freeze_manifest)
    freeze_sha = sha256(args.freeze_manifest)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if registry.get("status") != "FROZEN_FOR_R2" or registry.get("selection_uses_performance_timing") is not False:
        raise RuntimeError("registry is not frozen with timing-independent selection")
    if registry.get("freeze_manifest_sha256") != freeze_sha or registry.get("freeze_source_commit") != freeze["source_commit"]:
        raise RuntimeError("registry and source/environment freeze differ")
    for key in ("state_tests_sha256", "capability_sha256", "process_isolation_sha256", "status_sha256"):
        if registry.get("r0", {}).get(key) != freeze.get("r0", {}).get(key):
            raise RuntimeError(f"registry uses different R0 provenance: {key}")
    conditions = list(registry.get("formal_conditions", []))
    if not conditions or conditions[0] != "TARGET_UB1" or len(conditions) != len(set(conditions)):
        raise RuntimeError("invalid formal condition set")
    for name in conditions:
        parse_path(name)
    tasks = load_tasks()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if any(p.startswith("LEGACY_NPU_") for p in conditions):
        write_json(args.output_dir / "legacy_npu_cache.json", prepare_legacy_npu_cache(args.output_dir))
    mask = sorted(psutil.Process().cpu_affinity())
    apply_affinity(mask)
    groups = draft_groups(conditions)
    session = RuntimeProcessSession(mask, tuple(groups))
    schedule = []
    for task_id in FULL:
        for rep in range(3):
            order = list(conditions)
            random.Random(SEED + task_id * 1009 + rep).shuffle(order)
            schedule.append({"task_id": task_id, "repetition": rep, "conditions": order})
    write_json(args.output_dir / "schedule.json", schedule)
    try:
        init = session.initialize(conditions)
        info = init["process_info"]
        if not info["target"]["target_import_clean"] or any(
                not d["draft_import_clean"] for d in info["drafts"].values()):
            raise RuntimeError("backend import boundary violated")
        if info["target"]["affinity"] != mask or any(
                d["affinity"] != mask for d in info["drafts"].values()):
            raise RuntimeError("worker affinity mismatch")
        session_info = {"schema": "heterospec.358h.runtime.r2_session.v0.2",
            "registry": str(args.registry), "registry_sha256": sha256(args.registry),
            "freeze_manifest_sha256": freeze_sha, "freeze_source_commit": freeze["source_commit"],
            "conditions": conditions, "session_affinity_mask": mask,
            "process_start_method": session.start_method, "process_info": info,
            "target_bindings": init["target_init"]["bindings"],
            "draft_init": init["draft_init"],
            "accounting_boundary": "post target prefill in target worker; all draft RPC included",
            "energy": "NOT_CLAIMED"}
        write_json(args.output_dir / "session.json", session_info)
        warm = []
        for name in conditions:
            outcome = session.run(name, formatted_prompt(tasks[0]), 8, f"warmup-{name}")
            warm.append({"path": name, "tokens": outcome["result"]["tokens"],
                         "claim_status": "NON_FORMAL / INVALID_FOR_CLAIMS"})
        write_json(args.output_dir / "warmup.json", warm)
        status = {"schema": "heterospec.358h.runtime.r2_status.v0.2", "formal": True,
            "formal_data_started": True, "formal_data_started_at_utc": utc(),
            "registry_sha256": sha256(args.registry), "freeze_manifest_sha256": freeze_sha,
            "freeze_source_commit": freeze["source_commit"], "dataset_sha256": DATASET_SHA256,
            "conditions": conditions, "fixed_process_affinity": mask,
            "expected_observations": len(FULL) * 3 * len(conditions),
            "completed_observations": 0, "complete": False}
        write_json(args.output_dir / "R2_STATUS.json", status)
        rows = []
        for unit in schedule:
            task_id, rep = unit["task_id"], unit["repetition"]
            formatted = formatted_prompt(tasks[task_id])
            for name in unit["conditions"]:
                observation_id = f"r2-HumanEval-{task_id}-rep-{rep}-{name}"
                started = utc()
                outcome = session.run(name, formatted, OUTPUT_CAP, observation_id)
                r = outcome["result"]
                spec = parse_path(name)
                timing = r["timing_v02"]
                if sum(timing[k] for k in ("draft_total_realized_ns", "target_verification_ns", "runtime_residual_ns")) != timing["end_to_end_ns"]:
                    raise RuntimeError("v0.2 primary timing invariant violated")
                row = {"schema": "heterospec.358h.runtime.r2_observation.v0.2",
                    "formal": True, "task_id": f"HumanEval/{task_id}", "repetition": rep,
                    "path": name, "observation_id": observation_id,
                    "started_at_utc": started, "ended_at_utc": utc(),
                    "prompt_token_count": outcome["prompt_tokens"],
                    "generated_token_ids": r["tokens"], "output_token_count": len(r["tokens"]),
                    "timing": timing, "harness_roundtrip_ns_diagnostic": outcome["harness_roundtrip_ns"],
                    "rounds": r["rounds"], "proposed": r["proposed"], "accepted": r["accepted"],
                    "committed": r["committed"], "process_affinity": mask,
                    "target_binding": init["target_init"]["bindings"][f"UB{spec['ubatch']}"],
                    "draft_capabilities": r.get("draft_capabilities"),
                    "exact_vs_reference": None, "first_divergence": None,
                    "errors": [], "warnings": []}
                rows.append(row)
                with (args.output_dir / "observations.jsonl").open("a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                    f.flush(); os.fsync(f.fileno())
                status["completed_observations"] += 1
                status["last_observation"] = observation_id
                write_json(args.output_dir / "R2_STATUS.json", status)
        refs = {(r["task_id"], r["repetition"]): r["generated_token_ids"]
                for r in rows if r["path"] == "TARGET_UB1"}
        if len(refs) != 90:
            raise RuntimeError("R2 lacks 90 contemporary target references")
        counts = {}
        for row in rows:
            ref = refs[(row["task_id"], row["repetition"])]
            row["exact_vs_reference"] = row["generated_token_ids"] == ref
            row["first_divergence"] = first_divergence(ref, row["generated_token_ids"])
        for name in conditions:
            subset = [r for r in rows if r["path"] == name]
            exact = sum(r["exact_vs_reference"] for r in subset)
            counts[name] = {"exact": exact, "total": len(subset),
                            "performance_admissible": exact == len(subset) == 90}
        write_json(args.output_dir / "observations.resolved.json", rows)
        status.update(complete=True, completed_at_utc=utc(), exact_counts=counts)
        write_json(args.output_dir / "R2_STATUS.json", status)
        print(json.dumps(counts, indent=2))
        return 0 if all(x["performance_admissible"] for x in counts.values()) else 2
    finally:
        write_json(args.output_dir / "process_shutdown.json", session.close())


if __name__ == "__main__":
    raise SystemExit(main())
