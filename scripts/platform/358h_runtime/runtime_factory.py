#!/usr/bin/env python3
"""Shared construction logic for prospective 358H runtime paths.

R1 and R2 must instantiate the same physical adapter topology.  In particular,
there is at most one OpenVINO GenAI pipeline and one Optimum compiled engine per
draft device in a process.  Replay/persistent wrappers are state policies over
those caller-owned engines, not independently compiled models.
"""
from __future__ import annotations

from typing import Any

def parse_path(name: str) -> dict[str, Any]:
    if name in ("TARGET_UB1", "TARGET_UB2"):
        return {
            "name": name,
            "kind": "TARGET",
            "device": None,
            "ubatch": 2 if name.endswith("UB2") else 1,
        }

    ubatch = 2 if name.endswith("_UB2") else 1
    if "_NPU_" in name:
        device = "NPU"
    elif "_CPU_" in name:
        device = "CPU"
    else:
        raise ValueError(f"draft path does not encode CPU/NPU device: {name}")

    if name.startswith("LEGACY_"):
        kind = "LEGACY"
    elif name.startswith("OPTIMUM_REPLAY_"):
        kind = "OPTIMUM_REPLAY"
    elif name.startswith("PERSIST_"):
        kind = "PERSIST"
    else:
        raise ValueError(f"unsupported runtime path: {name}")
    return {"name": name, "kind": kind, "device": device, "ubatch": ubatch}


def create_draft_adapters(specs: dict[str, dict[str, Any]]):
    """Create only engines needed by `specs`, sharing one physical engine/device.

    Returns `(adapters, optimum_engines, legacy_engines)`.  A caller must execute
    observations serially; wrappers sharing an engine must never be interleaved.
    """
    # Worker-local imports: parsing a path in the campaign/target process must
    # never initialize OpenVINO, Optimum, or a draft backend.
    from runtime_draft import OpenVINODraftReplay, OptimumDraftEngine
    from runtime_shared_draft import (
        SharedLegacyGenAIReplayDraft,
        SharedOptimumPersistentDraft,
        SharedOptimumReplayDraft,
    )

    adapters: dict[str, Any] = {}
    optimum_engines: dict[str, OptimumDraftEngine] = {}
    legacy_engines: dict[str, Any] = {}

    for device in ("CPU", "NPU"):
        legacy_names = [
            name for name, spec in specs.items()
            if spec["kind"] == "LEGACY" and spec["device"] == device
        ]
        if legacy_names:
            engine = OpenVINODraftReplay(device)
            legacy_engines[device] = engine
            for name in legacy_names:
                adapters[name] = SharedLegacyGenAIReplayDraft(
                    engine, device, specs[name]["ubatch"]
                )

        optimum_names = [
            name for name, spec in specs.items()
            if spec["kind"] in ("OPTIMUM_REPLAY", "PERSIST")
            and spec["device"] == device
        ]
        if optimum_names:
            engine = OptimumDraftEngine(device)
            optimum_engines[device] = engine
            for name in optimum_names:
                spec = specs[name]
                if spec["kind"] == "OPTIMUM_REPLAY":
                    adapters[name] = SharedOptimumReplayDraft(engine, spec["ubatch"])
                else:
                    adapters[name] = SharedOptimumPersistentDraft(engine, spec["ubatch"])

    expected = {name for name, spec in specs.items() if spec["kind"] != "TARGET"}
    missing = sorted(expected - set(adapters))
    if missing:
        raise RuntimeError(f"failed to construct requested draft paths: {missing}")
    return adapters, optimum_engines, legacy_engines


def adapter_reset_barrier(adapter) -> None:
    """Best-effort explicit reset between serial observations.

    `run_speculative` already calls finish() on successful requests.  This barrier
    is for driver-level hygiene before a wrapper that shares the same physical
    engine is handed the next request.  It intentionally adds no measured time.
    """
    try:
        adapter.finish()
    except Exception:
        # A failure here is not silently ignored by formal callers: they invoke
        # the barrier only after a successful observation and may wrap this helper
        # with their own error policy. This fallback exists for idempotent legacy
        # wrappers whose finish is purely logical.
        raise


__all__ = ["parse_path", "create_draft_adapters", "adapter_reset_barrier"]
