#!/usr/bin/env python3
from __future__ import annotations

from runtime_draft import OptimumDraftEngine, OptimumPersistentDraft, OptimumReplayDraft
from runtime_types import DraftCapabilities, PathIdentity


class SharedOptimumReplayDraft(OptimumReplayDraft):
    """Replay policy over a caller-owned compiled Optimum engine."""

    def __init__(self, engine: OptimumDraftEngine, target_ubatch: int = 1):
        self.engine = engine
        self.device = engine.device
        self._logical: list[int] = []
        self.identity = PathIdentity(
            name=f"OPTIMUM_REPLAY_{self.device}_UB{target_ubatch}",
            target_ubatch=target_ubatch,
            draft_device=self.device,
            draft_frontend="OPTIMUM_OVMODEL",
            state_policy="FULL_PREFIX_REPLAY",
        )
        self.capabilities = DraftCapabilities(
            frontend="OPTIMUM_OVMODEL",
            requested_device=self.device,
            actual_execution_devices=engine.execution_devices,
            state_policy="FULL_PREFIX_REPLAY",
            supports_persistent_state=False,
            supports_checkpoint=False,
            supports_partial_reconcile=False,
            hidden_full_prefix_replay=True,
            state_kind=engine.state_kind,
        )


class SharedOptimumPersistentDraft(OptimumPersistentDraft):
    """Persistent policy over the same compiled engine used by the replay control.

    The formal driver must never interleave two requests on this engine.  Every
    observation calls finish/reset before another policy uses it.
    """

    def __init__(self, engine: OptimumDraftEngine, target_ubatch: int = 1):
        self.engine = engine
        self.device = engine.device
        self.identity = PathIdentity(
            name=f"PERSIST_{self.device}_UB{target_ubatch}",
            target_ubatch=target_ubatch,
            draft_device=self.device,
            draft_frontend="OPTIMUM_OVMODEL",
            state_policy="PERSISTENT_RECONCILABLE",
        )
        supports = engine.use_cache and ((not engine.stateful) or bool(engine.variable_states))
        self.capabilities = DraftCapabilities(
            frontend="OPTIMUM_OVMODEL",
            requested_device=self.device,
            actual_execution_devices=engine.execution_devices,
            state_policy="PERSISTENT_RECONCILABLE",
            supports_persistent_state=bool(supports),
            supports_checkpoint=bool(supports),
            supports_partial_reconcile=bool(supports),
            hidden_full_prefix_replay=False,
            state_kind=engine.state_kind,
            notes=["shared compiled engine; R0 forced-state tests mandatory"],
        )
        if not supports:
            raise RuntimeError(f"frontend does not expose a reconcilable cache on {self.device}")
        self._logical: list[int] = []
        self._past = None
        self._next_token: int | None = None
        self._marker = None
        self._checkpoint = None
        self._proposal_past = None
        self._proposal_next: int | None = None


__all__ = ["SharedOptimumReplayDraft", "SharedOptimumPersistentDraft"]
