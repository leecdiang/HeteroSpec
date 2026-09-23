#!/usr/bin/env python3
"""Backend-neutral v0.2 spawn/Pipe protocol and realized-RPC draft adapter.

This module deliberately imports no target or draft backend. Worker-specific
imports happen only inside the respective child entrypoints.
"""
from __future__ import annotations

import os
import pickle
import sys
import time
import traceback
from dataclasses import asdict
from multiprocessing.connection import Connection
from typing import Any

import psutil

from runtime_types import DraftCapabilities, DraftStepTiming, Proposal

VERSION = "heterospec.358h.runtime.rpc.v0.2"
FORBIDDEN_DUPLICATE_OMP = "KMP_DUPLICATE_LIB_OK"


def assert_no_duplicate_omp() -> None:
    if os.environ.get(FORBIDDEN_DUPLICATE_OMP, "").strip().upper() in {"1", "TRUE", "YES", "ON"}:
        raise RuntimeError("duplicate OpenMP workaround is prohibited")


def apply_affinity(mask: list[int]) -> list[int]:
    proc = psutil.Process()
    proc.cpu_affinity(list(map(int, mask)))
    actual = sorted(proc.cpu_affinity())
    if actual != sorted(mask):
        raise RuntimeError(f"affinity mismatch: {actual} != {mask}")
    return actual


def inventory(role: str) -> dict[str, Any]:
    names = sorted(sys.modules)
    loaded = sorted({os.path.basename(m.path).lower() for m in psutil.Process().memory_maps()})
    backend = [n for n in names if n.split(".")[0] in {
        "openvino", "openvino_genai", "optimum", "torch", "runtime_target", "runtime_draft"
    }]
    return {
        "pid": os.getpid(), "role": role,
        "affinity": sorted(psutil.Process().cpu_affinity()),
        "backend_modules": backend,
        "openmp_dlls": [n for n in loaded if "omp" in n and n.endswith(".dll")],
        "runtime_dlls": [n for n in loaded if n.startswith(("ggml", "llama", "openvino")) and n.endswith(".dll")],
        "target_import_clean": not any(n.startswith(("openvino", "optimum", "runtime_draft")) for n in names),
        "draft_import_clean": not any(n.startswith(("runtime_target", "phase3_heterogeneous_runner")) for n in names),
    }


class RPCError(RuntimeError):
    pass


class RPCClient:
    def __init__(self, conn: Connection, role: str, process=None, timeout_s: float = 300):
        self.conn = conn
        self.role = role
        self.process = process
        self.timeout_s = timeout_s
        self.next_id = 1

    def call(self, op: str, *, request_id: str = "session", observation_id: str = "r0",
             path_id: str = "NONE", round_id: int | None = None,
             payload: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, int]]:
        assert_no_duplicate_omp()
        rid = self.next_id
        self.next_id += 1
        msg = {"version": VERSION, "rpc_id": rid, "request_id": request_id,
               "observation_id": observation_id, "path_id": path_id,
               "operation": op, "round_id": round_id, "payload": payload or {}}
        tx = len(pickle.dumps(msg, protocol=pickle.HIGHEST_PROTOCOL))
        start = time.perf_counter_ns()
        try:
            self.conn.send(msg)
            if not self.conn.poll(self.timeout_s):
                state = "dead" if self.process is not None and not self.process.is_alive() else "unresponsive"
                raise RPCError(f"{self.role} {state} during {op} rpc={rid}")
            response = self.conn.recv()
        except (EOFError, BrokenPipeError, OSError) as exc:
            raise RPCError(f"{self.role} died or disconnected during {op} rpc={rid}: {exc}") from exc
        elapsed = time.perf_counter_ns() - start
        rx = len(pickle.dumps(response, protocol=pickle.HIGHEST_PROTOCOL))
        if not isinstance(response, dict) or any(response.get(k) != v for k, v in {
            "version": VERSION, "rpc_id": rid, "request_id": request_id,
            "observation_id": observation_id, "path_id": path_id,
            "operation": op, "worker_role": self.role,
        }.items()):
            raise RPCError(f"stale/mismatched {self.role} response to {op} rpc={rid}: {response!r}")
        if not isinstance(response.get("worker_pid"), int):
            raise RPCError("worker response omitted PID")
        if response.get("status") != "OK":
            error = response.get("error", {})
            raise RPCError(f"{self.role} {op} failed: {error}")
        return response.get("result", {}), {"realized_ns": elapsed, "tx_bytes": tx, "rx_bytes": rx}


def serve(conn: Connection, role: str, handler) -> None:
    assert_no_duplicate_omp()
    while True:
        try:
            msg = conn.recv()
        except EOFError:
            break
        fields = {k: msg.get(k) for k in ("version", "rpc_id", "request_id", "observation_id", "path_id", "operation", "round_id")}
        response = {**fields, "worker_pid": os.getpid(), "worker_role": role}
        try:
            if msg.get("version") != VERSION:
                raise RPCError("protocol version mismatch")
            if not isinstance(msg.get("rpc_id"), int) or not msg.get("request_id"):
                raise RPCError("missing RPC/request identity")
            result = handler(msg)
            response.update(status="OK", result=result or {})
        except BaseException as exc:
            response.update(status="ERROR", error={
                "type": type(exc).__name__, "message": str(exc),
                "traceback": traceback.format_exc(),
                "active_request_id": msg.get("request_id"),
                "active_operation": msg.get("operation"),
            })
        try:
            conn.send(response)
        except (BrokenPipeError, OSError):
            break
        if msg.get("operation") == "SHUTDOWN":
            break
    conn.close()


class RemoteDraftAdapter:
    """Target-owned logical adapter; physical state never crosses the Pipe."""
    def __init__(self, client: RPCClient, path: str, caps: dict[str, Any], request_id: str):
        self.client, self.path, self.request_id = client, path, request_id
        self.capabilities = DraftCapabilities(**caps)
        self.identity = None
        self.logical = None
        self.calls = 0
        self.tx_bytes = self.rx_bytes = 0
        self.worker_begin_ns = self.worker_checkpoint_ns = 0
        self.worker_propose_ns = self.worker_reconcile_ns = self.worker_finish_ns = 0
        self.r0_alias_probe = False

    def _call(self, op: str, payload: dict[str, Any], round_id: int | None = None):
        result, meter = self.client.call(op, request_id=self.request_id,
                                         path_id=self.path, round_id=round_id, payload=payload)
        self.calls += 1
        self.tx_bytes += meter["tx_bytes"]
        self.rx_bytes += meter["rx_bytes"]
        if "logical_state_length" in result:
            self.logical = result["logical_state_length"]
        return result, meter

    def begin(self, committed_prefix):
        r, m = self._call("BEGIN", {"committed_prefix": list(map(int, committed_prefix))})
        self.worker_begin_ns += r["worker_begin_ns"]
        return m["realized_ns"], r.get("metadata", {})

    def propose(self, committed_prefix, width):
        if width <= 0:
            raise AssertionError("width=0 must not cross Draft RPC")
        r, m = self._call("PROPOSE", {"committed_prefix": list(map(int, committed_prefix)),
                                      "width": int(width), "r0_alias_probe": self.r0_alias_probe})
        self.worker_checkpoint_ns += r["worker_checkpoint_ns"]
        self.worker_propose_ns += r["worker_propose_ns"]
        return Proposal(tokens=r["tokens"],
                        timing=DraftStepTiming(propose_ns=m["realized_ns"],
                                               checkpoint_bytes=r["checkpoint_bytes"],
                                               state_transfer_bytes=r["state_transfer_bytes"]),
                        metadata=r.get("metadata", {}))

    def reconcile(self, committed_prefix_before, proposals, accepted, committed_this_round):
        r, m = self._call("RECONCILE", {
            "committed_prefix_before": list(map(int, committed_prefix_before)),
            "proposals": list(map(int, proposals)), "accepted": int(accepted),
            "committed_this_round": list(map(int, committed_this_round)),
        })
        self.worker_reconcile_ns += r["worker_reconcile_ns"]
        return m["realized_ns"], r.get("metadata", {})

    def logical_state_length(self):
        return self.logical

    def finish(self):
        r, m = self._call("FINISH", {})
        self.worker_finish_ns += r["worker_finish_ns"]
        return m["realized_ns"], r.get("metadata", {})

    def accounting(self, timing: dict[str, int]) -> dict[str, int]:
        realized = {"draft_begin_realized_ns": timing["draft_begin_ns"],
                    "draft_propose_realized_ns": timing["draft_propose_ns"],
                    "draft_reconcile_realized_ns": timing["draft_reconcile_ns"],
                    "draft_finish_realized_ns": timing["draft_finish_ns"]}
        total = sum(realized.values())
        internal = sum((self.worker_begin_ns, self.worker_checkpoint_ns,
                        self.worker_propose_ns, self.worker_reconcile_ns, self.worker_finish_ns))
        if internal > total:
            raise AssertionError("worker compute exceeds realized RPC durations")
        return {**realized, "draft_total_realized_ns": total,
                "worker_draft_begin_ns": self.worker_begin_ns,
                "worker_checkpoint_ns": self.worker_checkpoint_ns,
                "worker_draft_propose_ns": self.worker_propose_ns,
                "worker_draft_reconcile_ns": self.worker_reconcile_ns,
                "worker_draft_finish_ns": self.worker_finish_ns,
                "draft_rpc_calls": self.calls, "draft_ipc_overhead_ns": total-internal,
                "draft_ipc_tx_bytes": self.tx_bytes, "draft_ipc_rx_bytes": self.rx_bytes,
                "target_verification_ns": timing["target_verification_ns"],
                "runtime_residual_ns": timing["runtime_residual_ns"],
                "end_to_end_ns": timing["end_to_end_ns"]}
