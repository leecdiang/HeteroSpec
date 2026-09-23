#!/usr/bin/env python3
"""Hardware-independent v0.2 RPC, lifecycle, and timing-boundary tests."""
from __future__ import annotations

import multiprocessing as mp
import time
from dataclasses import asdict

from runtime_logic_unit_tests import FakeTarget
from runtime_process_v02 import RPCClient, RPCError, RemoteDraftAdapter, VERSION, serve
from runtime_runner import run_speculative, run_target_only
from runtime_types import DraftCapabilities


class ScriptedConnection:
    def __init__(self, response=None, dead=False):
        self.response, self.dead = response, dead
        self.sent = None
    def send(self, msg): self.sent = msg
    def poll(self, timeout): return True
    def recv(self):
        if self.dead: raise EOFError("simulated worker death")
        return self.response(self.sent) if callable(self.response) else self.response


def echo(msg):
    return {k: msg[k] for k in ("version", "rpc_id", "request_id", "observation_id", "path_id", "operation", "round_id")} | {
        "worker_pid": 123, "worker_role": "draft", "status": "OK", "result": {"pong": True}}


def fake_worker(conn, delay):
    logical = []
    active = None
    ops = []
    def handle(msg):
        nonlocal logical, active
        op, p = msg["operation"], msg["payload"]
        ops.append(op)
        if op in {"BEGIN", "PROPOSE", "RECONCILE", "FINISH"}:
            time.sleep(delay)
        if op == "BEGIN":
            if active is not None: raise RuntimeError("request leak")
            active = msg["request_id"]
            logical = p["committed_prefix"][:]
            return {"worker_begin_ns": 100, "metadata": {}, "logical_state_length": len(logical)}
        if op in {"PROPOSE", "RECONCILE", "FINISH"} and active != msg["request_id"]:
            raise RuntimeError("request mismatch")
        if op == "PROPOSE":
            return {"tokens": [11, 12][:p["width"]], "worker_checkpoint_ns": 40,
                    "worker_propose_ns": 100, "checkpoint_bytes": 128,
                    "state_transfer_bytes": 0, "metadata": {}, "logical_state_length": len(logical)}
        if op == "RECONCILE":
            logical.extend(p["committed_this_round"])
            return {"worker_reconcile_ns": 100, "metadata": {"checkpoint_restored": False},
                    "logical_state_length": len(logical)}
        if op == "FINISH":
            active = None
            logical = []
            return {"worker_finish_ns": 100, "metadata": {}, "logical_state_length": 0}
        if op == "RESET":
            active = None
            logical = []
            return {"reset": True}
        if op == "OPS": return {"operations": ops[:]}
        if op == "SHUTDOWN": return {"shutdown": True}
        raise RuntimeError("deliberate worker error")
    serve(conn, "draft", handle)


def test_identity_and_stale_response():
    c = RPCClient(ScriptedConnection(echo), "draft")
    r, _ = c.call("PING", request_id="one")
    assert r["pong"]
    bad = RPCClient(ScriptedConnection(lambda m: echo(m) | {"rpc_id": m["rpc_id"]-1}), "draft")
    try: bad.call("PING")
    except RPCError: pass
    else: raise AssertionError("stale response accepted")
    bad_req = RPCClient(ScriptedConnection(lambda m: echo(m) | {"request_id": "previous"}), "draft")
    try: bad_req.call("PING")
    except RPCError: pass
    else: raise AssertionError("cross-request response accepted")


def test_error_and_death():
    err = RPCClient(ScriptedConnection(lambda m: echo(m) | {"status": "ERROR", "error": {
        "type": "ValueError", "message": "injected", "traceback": "trace", "active_request_id": m["request_id"],
        "active_operation": m["operation"]}}), "draft")
    try: err.call("PROPOSE")
    except RPCError as exc: assert "injected" in str(exc)
    else: raise AssertionError("worker error silently swallowed")
    dead = RPCClient(ScriptedConnection(dead=True), "draft")
    try: dead.call("PING")
    except RPCError as exc: assert "died" in str(exc)
    else: raise AssertionError("worker death silently swallowed")


def run_fake(delay):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe()
    process = ctx.Process(target=fake_worker, args=(child, delay))
    process.start()
    child.close()
    client = RPCClient(parent, "draft", process)
    caps = asdict(DraftCapabilities("FAKE", "CPU", ["CPU"], "PERSISTENT_RECONCILABLE",
                                    True, True, True, False, "FAKE"))
    try:
        # Target-only must not touch the worker.
        only = run_target_only(FakeTarget([10, 11, 12, 13]), [1, 2], 4)
        assert only["tokens"] == [10, 11, 12, 13]
        assert client.call("OPS")[0]["operations"] == ["OPS"]
        boundary = RemoteDraftAdapter(client, "FAKE_CPU_UB1", caps, "req-boundary")
        single = run_speculative(FakeTarget([10]), boundary, [1, 2], 1)
        assert single["proposed"] == 0 and boundary.calls == 3
        assert "PROPOSE" not in client.call("OPS")[0]["operations"]
        client.call("RESET")
        draft = RemoteDraftAdapter(client, "FAKE_CPU_UB1", caps, "req-full")
        full = run_speculative(FakeTarget([10, 11, 12, 13]), draft, [1, 2], 4)
        account = draft.accounting(full["timing"])
        assert full["tokens"] == [10, 11, 12, 13]
        assert account["draft_rpc_calls"] == 5  # begin, initial reconcile, propose, reconcile, finish
        assert account["draft_total_realized_ns"] + account["target_verification_ns"] + account["runtime_residual_ns"] == account["end_to_end_ns"]
        assert account["draft_ipc_overhead_ns"] >= 0
        ops = client.call("OPS")[0]["operations"]
        assert ops[-6:-1] == ["BEGIN", "RECONCILE", "PROPOSE", "RECONCILE", "FINISH"]
        client.call("RESET")
        client.call("SHUTDOWN")
    finally:
        process.join(timeout=5)
    assert process.exitcode == 0
    return account


def test_realized_delay_and_accounting():
    fast = run_fake(0.0)
    slow = run_fake(0.06)
    assert slow["end_to_end_ns"] - fast["end_to_end_ns"] > 200_000_000
    assert slow["draft_total_realized_ns"] - fast["draft_total_realized_ns"] > 200_000_000
    assert slow["worker_draft_begin_ns"]+slow["worker_checkpoint_ns"]+slow["worker_draft_propose_ns"]+slow["worker_draft_reconcile_ns"]+slow["worker_draft_finish_ns"] < slow["draft_total_realized_ns"]
    return {"fast": fast, "slow": slow, "injected_delay_ns_per_rpc": 60_000_000}


def main():
    test_identity_and_stale_response(); print("PASS rpc_identity_and_stale_rejection")
    test_error_and_death(); print("PASS error_propagation_and_worker_death")
    result = test_realized_delay_and_accounting()
    print("PASS request_reset_sequence_target_only_width_zero_and_rpc_delay")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
