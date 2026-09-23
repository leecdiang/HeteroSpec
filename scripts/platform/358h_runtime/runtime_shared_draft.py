#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Sequence

from runtime_draft import OptimumDraftEngine, OptimumPersistentDraft, OptimumReplayDraft
from runtime_types import DraftCapabilities, DraftStepTiming, PathIdentity, Proposal


class SharedLegacyGenAIReplayDraft:
    """Full-prefix replay policy over a caller-owned frozen LLMPipeline.

    One underlying pipeline can serve UB1/UB2 target-path conditions because the
    draft proposal semantics are independent of the target's physical ubatch.
    The wrapper keeps request-local logical bookkeeping and path identity.
    """

    def __init__(self, legacy_engine, device: str, target_ubatch: int = 1):
        self._legacy = legacy_engine
        self.device = device
        self._logical: list[int] = []
        self.identity = PathIdentity(
            name=f"LEGACY_REPLAY_{device}_UB{target_ubatch}",
            target_ubatch=target_ubatch,
            draft_device=device,
            draft_frontend="OPENVINO_GENAI_LLMPipeline",
            state_policy="FULL_PREFIX_REPLAY",
        )
        self.capabilities = DraftCapabilities(
            frontend="OPENVINO_GENAI_LLMPipeline",
            requested_device=device,
            actual_execution_devices=list(legacy_engine.execution_devices),
            state_policy="FULL_PREFIX_REPLAY",
            supports_persistent_state=False,
            supports_checkpoint=False,
            supports_partial_reconcile=False,
            hidden_full_prefix_replay=True,
            state_kind="NONE / REPLAY",
            notes=["shared frozen LLMPipeline; request logical state belongs to wrapper"],
        )

    def begin(self, committed_prefix: Sequence[int]) -> tuple[int, dict[str, Any]]:
        self._logical = list(map(int, committed_prefix))
        return 0, {"begin_policy": "NO_OP; replay paid in propose"}

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        prefix = list(map(int, committed_prefix))
        if prefix != self._logical:
            raise AssertionError("shared legacy replay logical prefix drift")
        if width <= 0:
            return Proposal(tokens=[], timing=DraftStepTiming(), metadata={"zero_width_noop": True})
        tokens, elapsed = self._legacy.propose(prefix, int(width))
        return Proposal(tokens=list(tokens), timing=DraftStepTiming(propose_ns=int(elapsed)))

    def reconcile(
        self,
        committed_prefix_before: Sequence[int],
        proposals: Sequence[int],
        accepted: int,
        committed_this_round: Sequence[int],
    ) -> tuple[int, dict[str, Any]]:
        if list(map(int, committed_prefix_before)) != self._logical:
            raise AssertionError("shared legacy replay reconcile prefix drift")
        self._logical.extend(map(int, committed_this_round))
        return 0, {"reconcile_policy": "LOGICAL_ONLY; next proposal replays complete prefix"}

    def logical_state_length(self) -> int | None:
        return len(self._logical)

    def finish(self) -> tuple[int, dict[str, Any]]:
        self._logical = []
        return 0, {"finish_policy": "LOGICAL_RESET"}


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
            notes=["shared compiled engine; request logical state belongs to wrapper"],
        )


class SharedOptimumPersistentDraft(OptimumPersistentDraft):
    """Persistent policy over the same compiled engine used by the replay control.

    The formal driver must never interleave two requests on this engine. Every
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


__all__ = [
    "SharedLegacyGenAIReplayDraft",
    "SharedOptimumReplayDraft",
    "SharedOptimumPersistentDraft",
]
