#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Any, Sequence

from runtime_draft import OptimumDraftEngine, OptimumPersistentDraft, OptimumReplayDraft
from runtime_types import DraftCapabilities, DraftStepTiming, PathIdentity, Proposal


def _ns() -> int:
    return time.perf_counter_ns()


def _tensor_nbytes(x: Any) -> int:
    if isinstance(x, (tuple, list)):
        return sum(_tensor_nbytes(v) for v in x)
    if hasattr(x, "nbytes"):
        return int(x.nbytes)
    if hasattr(x, "byte_size"):
        return int(x.byte_size)
    return 0


class SharedLegacyGenAIReplayDraft:
    """Full-prefix replay policy over a caller-owned frozen LLMPipeline."""

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
    """Minimal full-prefix replay oracle over a caller-owned Optimum engine.

    The final candidate is not fed back into the model merely to materialize a
    state that replay will discard. For k=2, full-prefix replay needs one prefix
    forward to obtain d1 and one d1 forward to obtain d2; no d2 forward occurs.
    """

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
            notes=["shared compiled engine; minimal greedy proposal work; final candidate is not materialized into discarded state"],
        )

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        prefix = list(map(int, committed_prefix))
        if prefix != self._logical:
            raise AssertionError("same-frontend replay logical prefix drift")
        if width <= 0:
            return Proposal(tokens=[], timing=DraftStepTiming(), metadata={"zero_width_noop": True})

        start = _ns()
        if self.engine.stateful:
            self.engine.reset_internal_state()
        next_token, past = self.engine.forward(prefix, past_key_values=None)
        out: list[int] = []
        for i in range(int(width)):
            token = int(next_token)
            out.append(token)
            if i + 1 < int(width):
                # Only advance enough state to obtain the next proposal token.
                # Replay discards this state after the call.
                next_token, past = self.engine.forward(
                    [token], past_key_values=past
                )
        elapsed = _ns() - start
        return Proposal(
            tokens=out,
            timing=DraftStepTiming(propose_ns=elapsed),
            metadata={"candidate_tokens_materialized_into_state": max(0, len(out) - 1)},
        )


class SharedOptimumPersistentDraft(OptimumPersistentDraft):
    """Persistent policy with lazy final-candidate state materialization.

    Proposal generation advances state only far enough to compute all candidate
    token IDs. The final candidate is not committed to draft state before target
    verification. Reconcile then keeps the already-valid accepted prefix, restores
    only when the backend state contains a rejected prefix, and incorporates the
    correction/bonus plus any accepted final candidate.
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
            notes=[
                "shared compiled engine; R0 forced-state tests mandatory",
                "final proposal token is materialized only after target acceptance",
            ],
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
        self._proposal_materialized = 0

    def _advance_stateful(self, tokens: Sequence[int]) -> int | None:
        next_token = self._next_token
        marker = self._marker
        for token in map(int, tokens):
            next_token, marker = self.engine.forward([token], past_key_values=marker)
        self._marker = marker
        return int(next_token) if next_token is not None else None

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        prefix = list(map(int, committed_prefix))
        if prefix != self._logical:
            raise AssertionError("persistent draft logical prefix drift before propose")
        if width <= 0:
            return Proposal(tokens=[], timing=DraftStepTiming(), metadata={"zero_width_noop": True})

        timing = DraftStepTiming()
        metadata: dict[str, Any] = {"state_kind": self.engine.state_kind}
        self._proposal_materialized = 0

        if self.engine.stateful:
            snap, bookkeeping, checkpoint_ns = self.engine.snapshot_internal_state()
            timing.checkpoint_ns = checkpoint_ns
            timing.checkpoint_bytes = sum(arr.nbytes for _, arr in snap)
            self._checkpoint = (snap, bookkeeping)
            next_token = self._next_token
            marker = self._marker
            out: list[int] = []
            start = _ns()
            for i in range(int(width)):
                if next_token is None:
                    raise RuntimeError("persistent draft has no next-token logits")
                token = int(next_token)
                out.append(token)
                if i + 1 < int(width):
                    next_token, marker = self.engine.forward([token], past_key_values=marker)
                    self._proposal_materialized += 1
            timing.propose_ns = _ns() - start
            self._proposal_next = int(next_token) if next_token is not None else None
            self._proposal_past = marker
        else:
            # External PKV returned by the frontend is treated as the committed
            # checkpoint only if R0 proves proposal inference does not mutate it.
            timing.checkpoint_bytes = _tensor_nbytes(self._past)
            self._checkpoint = self._past
            work_past = self._past
            next_token = self._next_token
            out = []
            start = _ns()
            for i in range(int(width)):
                if next_token is None:
                    raise RuntimeError("persistent draft has no next-token logits")
                token = int(next_token)
                out.append(token)
                if i + 1 < int(width):
                    next_token, work_past = self.engine.forward([token], past_key_values=work_past)
                    self._proposal_materialized += 1
            timing.propose_ns = _ns() - start
            self._proposal_past = work_past
            self._proposal_next = int(next_token) if next_token is not None else None

        metadata["candidate_tokens_materialized_into_state"] = self._proposal_materialized
        return Proposal(tokens=out, timing=timing, metadata=metadata)

    def reconcile(
        self,
        committed_prefix_before: Sequence[int],
        proposals: Sequence[int],
        accepted: int,
        committed_this_round: Sequence[int],
    ) -> tuple[int, dict[str, Any]]:
        prefix = list(map(int, committed_prefix_before))
        if prefix != self._logical:
            raise AssertionError("persistent draft logical prefix drift before reconcile")
        proposals = list(map(int, proposals))
        committed = list(map(int, committed_this_round))
        if not committed:
            raise AssertionError("each target round must commit at least one token")
        if accepted < 0 or accepted > len(proposals):
            raise AssertionError("invalid accepted count")

        start = _ns()
        transferred = 0
        restored = False

        if not proposals:
            suffix_to_apply = committed
        else:
            materialized = int(self._proposal_materialized)
            expected_materialized = max(0, len(proposals) - 1)
            if materialized != expected_materialized:
                raise AssertionError(
                    f"proposal state materialization drift: {materialized} != {expected_materialized}"
                )

            if accepted < materialized:
                # The speculative backend state contains a rejected candidate.
                # Restore the exact committed checkpoint before applying the
                # accepted prefix and target correction.
                if self.engine.stateful:
                    if self._checkpoint is None:
                        raise RuntimeError("missing VariableState checkpoint")
                    snap, bookkeeping = self._checkpoint
                    _, transferred = self.engine.restore_internal_state(snap, bookkeeping)
                else:
                    self._past = self._checkpoint
                restored = True
                suffix_to_apply = committed
            else:
                # Current proposal state already contains proposals[:materialized],
                # which is a subset of the accepted prefix. Apply only the tokens
                # not yet represented in state plus correction/bonus.
                suffix_to_apply = committed[materialized:]
                if not self.engine.stateful:
                    self._past = self._proposal_past

        if self.engine.stateful:
            next_token = self._advance_stateful(suffix_to_apply)
            self._next_token = next_token
            # Optimum's stateful marker is required on every continuation.
            # Passing None here silently resets VariableState and changes tokens.
        else:
            past = self._past
            next_token = self._next_token
            for token in map(int, suffix_to_apply):
                next_token, past = self.engine.forward([token], past_key_values=past)
            self._past = past
            self._next_token = int(next_token) if next_token is not None else None

        elapsed = _ns() - start
        self._logical.extend(committed)
        self._checkpoint = None
        self._proposal_past = None
        self._proposal_next = None
        self._proposal_materialized = 0
        return elapsed, {
            "state_transfer_bytes": int(transferred),
            "accepted": int(accepted),
            "committed": committed,
            "state_kind": self.engine.state_kind,
            "checkpoint_restored": restored,
            "suffix_tokens_applied_after_verification": list(map(int, suffix_to_apply)),
        }

    def finish(self) -> tuple[int, dict[str, Any]]:
        elapsed, meta = super().finish()
        self._proposal_materialized = 0
        return elapsed, meta


__all__ = [
    "SharedLegacyGenAIReplayDraft",
    "SharedOptimumReplayDraft",
    "SharedOptimumPersistentDraft",
]
