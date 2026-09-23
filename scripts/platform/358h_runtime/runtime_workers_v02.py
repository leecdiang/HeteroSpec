#!/usr/bin/env python3
"""v0.2 worker entrypoints. No backend is imported at module load/spawn time."""
from __future__ import annotations

import os
import time
from dataclasses import asdict
from multiprocessing.connection import Connection

from runtime_process_v02 import RPCClient, RemoteDraftAdapter, apply_affinity, assert_no_duplicate_omp, inventory, serve


def draft_worker_entry(conn: Connection, affinity: list[int]) -> None:
    assert_no_duplicate_omp()
    apply_affinity(affinity)
    adapters = {}
    engines = {}
    active = None
    active_request = None

    def handle(msg):
        nonlocal adapters, engines, active, active_request
        op, payload, path = msg["operation"], msg["payload"], msg["path_id"]
        req = msg["request_id"]
        if op == "PING":
            return {"pong": True}
        if op == "INFO":
            return inventory("draft") | {"engine_ids": {k: id(v) for k, v in engines.items()},
                                          "adapter_paths": sorted(adapters)}
        if op == "INIT":
            if adapters:
                raise RuntimeError("draft worker already initialized")
            from runtime_factory import create_draft_adapters, parse_path
            specs = {p: parse_path(p) for p in payload["paths"]}
            adapters, optimum, legacy = create_draft_adapters(specs)
            engines = {"optimum_" + k: v for k, v in optimum.items()} | {"legacy_" + k: v for k, v in legacy.items()}
            return {"capabilities": {p: asdict(a.capabilities) for p, a in adapters.items()},
                    "engine_ids": {k: id(v) for k, v in engines.items()},
                    "adapter_engine_ids": {p: id(a.engine) if hasattr(a, "engine") else id(a._legacy)
                                           for p, a in adapters.items()}}
        if op == "RESET":
            if active is not None:
                adapters[active].finish()
            active = active_request = None
            return {"reset": True}
        if op == "SHUTDOWN":
            if active is not None:
                adapters[active].finish()
            return {"shutdown": True}
        if path not in adapters:
            raise RuntimeError(f"draft path not initialized: {path}")
        a = adapters[path]
        if op == "BEGIN":
            if active is not None:
                raise RuntimeError("previous request not finished/reset")
            elapsed, meta = a.begin(payload["committed_prefix"])
            active, active_request = path, req
            return {"worker_begin_ns": int(elapsed), "metadata": meta,
                    "logical_state_length": a.logical_state_length()}
        if active != path or active_request != req:
            raise RuntimeError(f"active request/path mismatch: {active_request}/{active} != {req}/{path}")
        if op == "PROPOSE":
            if payload["width"] <= 0:
                raise RuntimeError("width=0 PROPOSE RPC is prohibited")
            snapshot = None
            if payload.get("r0_alias_probe") and getattr(a, "engine", None) is not None and a.engine.stateful:
                snapshot, _, _ = a.engine.snapshot_internal_state()
                before = [arr.tobytes() for _, arr in snapshot]
            pp = a.propose(payload["committed_prefix"], payload["width"])
            if snapshot is not None:
                alias_mutated = any(arr.tobytes() != prior for (_, arr), prior in zip(snapshot, before))
                pp.metadata["checkpoint_alias_mutated"] = alias_mutated
                if alias_mutated:
                    raise AssertionError("VariableState checkpoint alias mutated during speculative advance")
            return {"tokens": list(map(int, pp.tokens)),
                    "worker_checkpoint_ns": int(pp.timing.checkpoint_ns),
                    "worker_propose_ns": int(pp.timing.propose_ns),
                    "checkpoint_bytes": int(pp.timing.checkpoint_bytes),
                    "state_transfer_bytes": int(pp.timing.state_transfer_bytes),
                    "metadata": pp.metadata,
                    "logical_state_length": a.logical_state_length()}
        if op == "RECONCILE":
            elapsed, meta = a.reconcile(payload["committed_prefix_before"],
                                        payload["proposals"], payload["accepted"],
                                        payload["committed_this_round"])
            return {"worker_reconcile_ns": int(elapsed), "metadata": meta,
                    "logical_state_length": a.logical_state_length()}
        if op == "FINISH":
            elapsed, meta = a.finish()
            active = active_request = None
            return {"worker_finish_ns": int(elapsed), "metadata": meta,
                    "logical_state_length": a.logical_state_length()}
        raise RuntimeError(f"unsupported draft operation: {op}")

    serve(conn, "draft", handle)


def _target_forced_cases(target) -> dict:
    prompt = target.tokenize("<|im_start|>user\nWrite a Python function that returns the square of an integer.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n", True)
    target.reset_prefill(prompt)
    baseline = target.baseline(12)
    target.reset_prefill(prompt)
    cases = []

    def one(label, proposal, expected):
        got = target.verify(proposal)
        pos = target.state_position()
        ok = got == expected and pos == len(target.history)-1
        row = {"case": label, "proposal": proposal, "committed": got,
               "expected": expected, "state_position": pos, "pass": ok}
        cases.append(row)
        if not ok:
            raise AssertionError(row)

    one("zero_accepted", [baseline[0]+1, baseline[1]], [baseline[0]])
    one("one_accepted", [baseline[1], baseline[2]+1], [baseline[1], baseline[2]])
    one("two_accepted_bonus", [baseline[3], baseline[4]], [baseline[3], baseline[4], baseline[5]])
    one("rejection_1", [baseline[6]+1, baseline[7]], [baseline[6]])
    one("rejection_2", [baseline[7]+1, baseline[8]], [baseline[7]])
    target.reset_prefill(prompt)
    a = target.baseline(8)
    target.reset_prefill(prompt)
    b = target.baseline(8)
    cases.append({"case": "reset_repeat", "pass": a == b == baseline[:8]})
    return {"pass": all(c["pass"] for c in cases), "cases": cases,
            "prompt_token_count": len(prompt)}


def target_worker_entry(driver_conn: Connection, draft_conn: Connection, affinity: list[int]) -> None:
    assert_no_duplicate_omp()
    apply_affinity(affinity)
    draft_client = RPCClient(draft_conn, "draft")
    targets = None
    caps = {}
    request_seq = 0

    def handle(msg):
        nonlocal targets, caps, request_seq
        op, payload = msg["operation"], msg["payload"]
        if op == "PING":
            return {"pong": True}
        if op == "INFO":
            d, _ = draft_client.call("INFO")
            return {"target": inventory("target"), "draft": d}
        if op == "DRAFT_INIT":
            r, _ = draft_client.call("INIT", payload={"paths": payload["paths"]})
            caps.update(r["capabilities"])
            return r
        if op == "INIT":
            if targets is not None:
                raise RuntimeError("target worker already initialized")
            from runtime_target import LlamaAPI, RuntimeTargetPool
            targets = RuntimeTargetPool(LlamaAPI(), ubatches=(1, 2))
            return {"bindings": targets.binding_records()}
        if op == "RESET":
            r, _ = draft_client.call("RESET")
            return {"reset": r["reset"]}
        if op == "SHUTDOWN":
            try:
                draft_client.call("SHUTDOWN")
            finally:
                return {"shutdown": True}
        if targets is None:
            raise RuntimeError("target worker not initialized")
        if op == "TARGET_TEST":
            return {"UB1": _target_forced_cases(targets[1]),
                    "UB2": _target_forced_cases(targets[2])}
        if op in {"RUN", "FORCED_TRACE"}:
            from runtime_factory import parse_path
            from runtime_runner import run_speculative, run_target_only
            spec = parse_path(payload["path"])
            target = targets[spec["ubatch"]]
            prompt = target.tokenize(payload["formatted_prompt"], True)
            if op == "RUN":
                if spec["kind"] == "TARGET":
                    result = run_target_only(target, prompt, int(payload["output_cap"]))
                    result["timing_v02"] = {"draft_total_realized_ns": 0,
                                           "target_verification_ns": result["timing"]["target_verification_ns"],
                                           "runtime_residual_ns": result["timing"]["runtime_residual_ns"],
                                           "end_to_end_ns": result["timing"]["end_to_end_ns"],
                                           "draft_rpc_calls": 0}
                else:
                    if spec["name"] not in caps:
                        raise RuntimeError("draft path not initialized")
                    request_seq += 1
                    adapter = RemoteDraftAdapter(draft_client, spec["name"], caps[spec["name"]],
                                                 f"request-{request_seq}")
                    result = run_speculative(target, adapter, prompt, int(payload["output_cap"]))
                    result["timing_v02"] = adapter.accounting(result["timing"])
                t = result["timing_v02"]
                if t["draft_total_realized_ns"]+t["target_verification_ns"]+t["runtime_residual_ns"] != t["end_to_end_ns"]:
                    raise AssertionError("v0.2 primary timing does not reconcile")
                return {"result": result, "prompt_tokens": len(prompt)}
            if spec["kind"] == "TARGET":
                raise RuntimeError("forced trace requires draft policy")
            if spec["name"] not in caps:
                raise RuntimeError("draft path not initialized")
            request_seq += 1
            adapter = RemoteDraftAdapter(draft_client, spec["name"], caps[spec["name"]],
                                         f"forced-{request_seq}")
            adapter.r0_alias_probe = spec["kind"] == "PERSIST"
            committed = list(prompt)
            rows = []
            patterns = payload.get("patterns", [0, 1, 2, 0, 2, 1, 0])
            adapter.begin(committed)
            for i, accepted in enumerate(patterns):
                pp = adapter.propose(committed, 2)
                if "committed_trace" in payload:
                    forced = payload["committed_trace"][i]
                elif accepted == 2:
                    forced = pp.tokens + [(pp.tokens[-1]+1) % target.n_vocab]
                else:
                    forced = pp.tokens[:accepted] + [(pp.tokens[accepted]+1) % target.n_vocab]
                _, meta = adapter.reconcile(committed, pp.tokens, accepted, forced)
                committed.extend(forced)
                ok = adapter.logical_state_length() == len(committed)
                rows.append({"round": i, "accepted": accepted, "proposal": pp.tokens,
                             "committed": forced, "logical_state_length": adapter.logical_state_length(),
                             "checkpoint_bytes": pp.timing.checkpoint_bytes,
                             "state_transfer_bytes": meta.get("state_transfer_bytes", 0),
                             "checkpoint_restored": meta.get("checkpoint_restored", False),
                             "checkpoint_alias_mutated": pp.metadata.get("checkpoint_alias_mutated"),
                             "pass": ok})
                if not ok:
                    raise AssertionError(rows[-1])
            adapter.finish()
            return {"rows": rows, "prompt_token_count": len(prompt),
                    "draft_rpc_calls": adapter.calls, "draft_ipc_tx_bytes": adapter.tx_bytes,
                    "draft_ipc_rx_bytes": adapter.rx_bytes}
        raise RuntimeError(f"unsupported target operation: {op}")

    serve(driver_conn, "target", handle)
