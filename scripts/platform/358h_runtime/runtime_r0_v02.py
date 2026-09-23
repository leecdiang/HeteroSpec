#!/usr/bin/env python3
"""Non-formal process-isolated R0 only. Never freezes or runs R1/R2."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import psutil

from runtime_process_v02 import apply_affinity, assert_no_duplicate_omp, inventory
from runtime_session_v02 import RuntimeProcessSession as ProcessSession

HERE = Path(__file__).resolve().parent
LEGACY_BINDING = Path.home() / "Documents/ChatGPT/HeteroSpec/runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json"
FORMATTED = ("<|im_start|>user\nWrite a Python function that returns the square of an integer."
             "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def probe_legacy_device(out: Path, mask: list[int], device: str) -> dict:
    """Run one legacy frontend in its own worker; NPU cache source stays read-only."""
    verdict = {"status": "IMPLEMENTATION_UNAVAILABLE", "device": device}
    if device == "NPU":
        verdict["binding_source"] = str(LEGACY_BINDING)
        if not LEGACY_BINDING.is_file():
            verdict["reason"] = "frozen legacy NPU binding evidence missing"
            return verdict
        binding = json.loads(LEGACY_BINDING.read_text(encoding="utf-8-sig"))
        blob = Path(binding["cache_blob"]["path"])
        if not blob.is_file():
            verdict["reason"] = "frozen legacy NPU cache blob missing"
            return verdict
        digest = hashlib.sha256(blob.read_bytes()).hexdigest()
        if digest != binding["cache_blob"]["sha256"]:
            raise RuntimeError("legacy NPU cache blob does not match frozen binding evidence")
        cache = out / "npu_cache_copy"
        cache.mkdir()
        shutil.copy2(blob, cache / blob.name)
        os.environ["HETEROSPEC_RUNTIME_CACHE_DIR"] = str(cache.resolve())
        os.environ["HETEROSPEC_FROZEN_NPU_BINDING"] = str(LEGACY_BINDING.resolve())
        verdict["copied_cache_blob_sha256"] = digest
    session = ProcessSession(mask)
    try:
        session.call("PING")
        paths = [f"LEGACY_{device}_UB1"] + (["LEGACY_NPU_UB2"] if device == "NPU" else [])
        init = session.call("DRAFT_INIT", payload={"paths": paths})
        verdict["draft_capabilities"] = init["capabilities"]
        verdict["process"] = session.call("INFO")
        session.call("INIT")
        baseline = session.call("RUN", payload={"path": "TARGET_UB1", "formatted_prompt": FORMATTED,
                                                "output_cap": 4})["result"]
        verdict["paths"] = {}
        for path in paths:
            legacy = session.call("RUN", payload={"path": path, "formatted_prompt": FORMATTED,
                                                  "output_cap": 4})["result"]
            verdict["paths"][path] = {"generated_token_ids": legacy["tokens"],
                                       "exact_short_r0": legacy["tokens"] == baseline["tokens"]}
        verdict["target_reference_token_ids"] = baseline["tokens"]
        verdict["status"] = "AVAILABLE_R0" if all(x["exact_short_r0"] for x in verdict["paths"].values()) else "CORRECTNESS_BLOCKED_R0"
        verdict["reset_rpc"] = session.call("RESET")["reset"]
    except Exception as exc:
        verdict["reason"] = str(exc)[:4000]
    finally:
        verdict["shutdown"] = session.close()
    return verdict


def probe_multi_worker(mask: list[int]) -> dict:
    """Exercise path routing while Optimum and GenAI own separate draft processes."""
    verdict = {"status": "BLOCKED"}
    session = ProcessSession(mask, groups=("optimum_cpu", "legacy_cpu"))
    try:
        initialized = session.initialize(["OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1",
                                          "LEGACY_CPU_UB1"])
        info = initialized["process_info"]
        baseline = session.run("TARGET_UB1", FORMATTED, 4, "r0-multi-target")["result"]
        paths = {}
        for path in ("OPTIMUM_REPLAY_CPU_UB1", "LEGACY_CPU_UB1"):
            row = session.run(path, FORMATTED, 4, "r0-multi-" + path)["result"]
            paths[path] = {"exact": row["tokens"] == baseline["tokens"],
                           "draft_rpc_calls": row["timing_v02"]["draft_rpc_calls"]}
        drafts = info["drafts"]
        verdict.update({"target": info["target"], "drafts": drafts, "paths": paths,
                        "distinct_pids": len({os.getpid(), info["target"]["pid"],
                                              *(v["pid"] for v in drafts.values())}) == 4,
                        "affinity_equal": info["target"]["affinity"] == mask and all(
                            v["affinity"] == mask for v in drafts.values()),
                        "import_clean": info["target"]["target_import_clean"] and all(
                            v["draft_import_clean"] for v in drafts.values()),
                        "reset_rpc": session.call("RESET")["reset"]})
        verdict["status"] = ("PASS" if verdict["distinct_pids"] and verdict["affinity_equal"]
                             and verdict["import_clean"] and verdict["reset_rpc"]
                             and all(p["exact"] and p["draft_rpc_calls"] > 0 for p in paths.values())
                             else "BLOCKED")
    except Exception as exc:
        verdict["error"] = repr(exc)
    finally:
        verdict["shutdown"] = session.close()
        if not verdict["shutdown"]["shutdown_rpc"]:
            verdict["status"] = "BLOCKED"
    return verdict


def run(out: Path) -> int:
    assert_no_duplicate_omp()
    os.environ["HETEROSPEC_R0_VERIFY_RESTORE"] = "1"
    out.mkdir(parents=True, exist_ok=False)
    mask = sorted(psutil.Process().cpu_affinity())
    apply_affinity(mask)
    battery = psutil.sensors_battery()
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE.parents[2], text=True).strip()
    source_dirty_tracked = subprocess.run(["git", "diff", "--quiet"], cwd=HERE.parents[2]).returncode != 0
    result = {"schema": "heterospec.358h.runtime.r0_v02.status", "formal": False,
              "formal_data_seen": False, "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_branch": "runtime/358h-codesign-v0.2", "session_affinity_mask": mask,
              "source_commit": source_commit, "source_dirty_tracked": source_dirty_tracked,
              "ac_power_online": None if battery is None else bool(battery.power_plugged),
              "stages": {}, "errors": [], "status": "R0_V02_BLOCKED"}
    process = {"schema": "heterospec.358h.runtime.r0_process_isolation.v0.2",
               "driver": inventory("driver"), "start_method": "spawn",
               "session_affinity_mask": mask, "checks": {}}
    state = {"schema": "heterospec.358h.runtime.r0_state_tests.v0.2", "formal": False,
             "claim_status": "NON_FORMAL / INVALID_FOR_PERFORMANCE_CLAIMS",
             "target": {}, "draft": {}, "policy_switch": {}, "combined": {}}

    cap_path = out / "r0_capability.json"
    probe = subprocess.run([sys.executable, "-B", str(HERE / "probe_openvino_state.py"),
                            "--devices", "CPU", "NPU", "--output", str(cap_path)],
                           text=True, capture_output=True)
    (out / "r0_capability.stdout.log").write_text(probe.stdout, encoding="utf-8")
    (out / "r0_capability.stderr.log").write_text(probe.stderr, encoding="utf-8")
    result["stages"]["capability_probe"] = {"exit_code": probe.returncode,
                                             "output_exists": cap_path.is_file()}
    if probe.returncode or not cap_path.is_file():
        result["errors"].append("capability probe failed")
    else:
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
        result["stages"]["optimum_npu"] = (
            "IMPLEMENTATION_UNAVAILABLE" if cap["optimum"]["NPU"]["load_status"] != "PASS"
            else "CAPABILITY_CANDIDATE")

    session = ProcessSession(mask)
    try:
        process["target_pid"] = session.target.pid
        process["draft_pid"] = session.draft.pid
        process["checks"]["ping"] = session.call("PING")["pong"]
        target_init = session.call("INIT")
        process["target_bindings"] = target_init["bindings"]
        draft_init = session.call("DRAFT_INIT", payload={"paths": [
            "OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"]})
        process["shared_engine_ids"] = draft_init["adapter_engine_ids"]
        process["checks"]["same_optimum_engine"] = len(set(draft_init["adapter_engine_ids"].values())) == 1
        info = session.call("INFO")
        process["target"] = info["target"]
        process["draft"] = info["draft"]
        process["checks"]["target_import_clean"] = info["target"]["target_import_clean"]
        process["checks"]["draft_import_clean"] = info["draft"]["draft_import_clean"]
        process["checks"]["affinity_equal"] = (info["target"]["affinity"] == mask == info["draft"]["affinity"])
        process["checks"]["distinct_pids"] = len({os.getpid(), session.target.pid, session.draft.pid}) == 3

        state["target"] = session.call("TARGET_TEST")
        pattern = [0, 1, 2, 0, 2, 1, 0]

        def trace(path, committed_trace=None):
            payload = {"path": path, "formatted_prompt": FORMATTED, "patterns": pattern}
            if committed_trace is not None:
                payload["committed_trace"] = committed_trace
            try:
                return session.call("FORCED_TRACE", payload=payload)
            finally:
                session.call("RESET")

        replay1 = trace("OPTIMUM_REPLAY_CPU_UB1")
        committed = [r["committed"] for r in replay1["rows"]]
        replay2 = trace("OPTIMUM_REPLAY_CPU_UB1", committed)
        replay_equal = [r["proposal"] for r in replay1["rows"]] == [r["proposal"] for r in replay2["rows"]]
        state["draft"]["CPU"] = {"replay_oracle": replay1, "replay_repeat": replay2,
                                   "replay_repeat_exact": replay_equal}
        result["stages"]["optimum_replay_cpu"] = "PASS" if replay_equal else "BLOCKED"
        try:
            persist1 = trace("PERSIST_CPU_UB1", committed)
            persist2 = trace("PERSIST_CPU_UB1", committed)
            persist3 = trace("PERSIST_CPU_UB1", committed)
            replay3 = trace("OPTIMUM_REPLAY_CPU_UB1", committed)
            state["draft"]["CPU"].update({"persistent": persist1,
                                              "persistent_repeat": persist2})
            proposal_sequences = [[r["proposal"] for r in run["rows"]] for run in
                                  (persist1, replay1, persist2, replay2, persist3, replay3)]
            state["policy_switch"] = {
                "sequence_1": ["PERSIST", "REPLAY", "PERSIST"],
                "sequence_2": ["REPLAY", "PERSIST", "REPLAY"],
                "all_proposals_exact": all(p == proposal_sequences[0] for p in proposal_sequences),
                "checkpoint_alias_mutated": any(r.get("checkpoint_alias_mutated")
                    for run in (persist1, persist2, persist3) for r in run["rows"]),
            }
            persistent_ok = state["policy_switch"]["all_proposals_exact"] and not state["policy_switch"]["checkpoint_alias_mutated"]
            result["stages"]["persist_cpu"] = "PASS" if persistent_ok else "BLOCKED"
        except Exception as exc:
            if "VariableState restore readback mismatch" not in str(exc):
                raise
            persistent_ok = False
            state["draft"]["CPU"]["persistent_unavailable"] = {
                "status": "IMPLEMENTATION_UNAVAILABLE", "reason": "lossy UINT8 VariableState restore readback",
                "error": str(exc)[:2000], "frozen_kv_cache_precision": "uint8_t"}
            state["policy_switch"] = {"status": "NOT_TESTABLE_PERSISTENT_UNAVAILABLE"}
            result["stages"]["persist_cpu"] = "IMPLEMENTATION_UNAVAILABLE"
        baseline = session.call("RUN", payload={"path": "TARGET_UB1",
                         "formatted_prompt": FORMATTED, "output_cap": 8})["result"]
        replay_run = session.call("RUN", payload={"path": "OPTIMUM_REPLAY_CPU_UB1",
                         "formatted_prompt": FORMATTED, "output_cap": 8})["result"]
        boundary = session.call("RUN", payload={"path": "OPTIMUM_REPLAY_CPU_UB1",
                         "formatted_prompt": FORMATTED, "output_cap": 1})["result"]
        state["combined"] = {"reference_tokens": baseline["tokens"],
                             "replay_tokens": replay_run["tokens"],
                             "replay_exact": replay_run["tokens"] == baseline["tokens"],
                             "boundary_no_proposal": boundary["proposed"] == 0,
                             "boundary_rpc_calls": boundary["timing_v02"]["draft_rpc_calls"],
                             "replay_timing_diagnostic": replay_run["timing_v02"]}
        if persistent_ok:
            persist_run = session.call("RUN", payload={"path": "PERSIST_CPU_UB1",
                             "formatted_prompt": FORMATTED, "output_cap": 8})["result"]
            state["combined"]["persistent_tokens"] = persist_run["tokens"]
            state["combined"]["persistent_exact"] = persist_run["tokens"] == baseline["tokens"]
            state["combined"]["persistent_timing_diagnostic"] = persist_run["timing_v02"]
            if not state["combined"]["persistent_exact"]:
                result["stages"]["persist_cpu"] = "BLOCKED"
    except Exception as exc:
        result["errors"].append({"type": type(exc).__name__, "message": str(exc),
                                 "traceback": traceback.format_exc()})
    finally:
        process["shutdown"] = session.close()
        process["checks"]["shutdown"] = process["shutdown"]["shutdown_rpc"]
        write_json(out / "r0_process_isolation.json", process)
        write_json(out / "r0_state_tests.json", state)
        process_ok = all(process["checks"].values())
        target_ok = all(v.get("pass") for v in state["target"].values()) if state["target"] else False
        result["status"] = ("R0_V02_PASS" if not result["errors"] and process_ok and target_ok
                            and result["stages"].get("optimum_replay_cpu") == "PASS"
                            and result["stages"].get("persist_cpu") in ("PASS", "IMPLEMENTATION_UNAVAILABLE")
                            and state["combined"].get("replay_exact")
                            and state["combined"].get("boundary_no_proposal")
                            else "R0_V02_BLOCKED")
        result["process_checks_pass"] = process_ok
        result["target_state_pass"] = target_ok
        write_json(out / "r0_status.json", result)
    try:
        for device in ("CPU", "NPU"):
            legacy = probe_legacy_device(out, mask, device)
            key = "legacy_" + device.lower()
            state["draft"][key] = legacy
            result["stages"][key] = legacy["status"]
            process[key + "_worker"] = legacy.get("process")
        process["multi_worker"] = probe_multi_worker(mask)
        result["stages"]["multi_worker"] = process["multi_worker"]["status"]
        if process["multi_worker"]["status"] != "PASS":
            result["status"] = "R0_V02_BLOCKED"
    except Exception as exc:
        result["errors"].append({"type": type(exc).__name__, "message": repr(exc), "stage": "legacy_probe"})
        result["status"] = "R0_V02_BLOCKED"
    write_json(out / "r0_process_isolation.json", process)
    write_json(out / "r0_state_tests.json", state)
    write_json(out / "r0_status.json", result)
    return 0 if result["status"] == "R0_V02_PASS" else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    return run(args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
