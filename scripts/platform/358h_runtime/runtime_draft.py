#!/usr/bin/env python3
from __future__ import annotations

import copy
import os
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import openvino as ov

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from runtime_legacy_draft_v02 import DRAFT_IR, OpenVINODraftReplay  # noqa: E402
from runtime_types import (  # noqa: E402
    DraftCapabilities,
    DraftStepTiming,
    PathIdentity,
    Proposal,
)


def _ns() -> int:
    return time.perf_counter_ns()


def _as_list(x) -> list[str]:
    if isinstance(x, str):
        return [x]
    return [str(v) for v in x]


def _tensor_nbytes(x: Any) -> int:
    if isinstance(x, (tuple, list)):
        return sum(_tensor_nbytes(v) for v in x)
    if hasattr(x, "nbytes"):
        return int(x.nbytes)
    if hasattr(x, "byte_size"):
        return int(x.byte_size)
    return 0


class LegacyGenAIReplayDraft:
    """Byte-compatible control around the closed Phase-3 replay frontend."""

    def __init__(self, device: str, target_ubatch: int = 1):
        self.device = device
        self._legacy = OpenVINODraftReplay(device)
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
            actual_execution_devices=list(self._legacy.execution_devices),
            state_policy="FULL_PREFIX_REPLAY",
            supports_persistent_state=False,
            supports_checkpoint=False,
            supports_partial_reconcile=False,
            hidden_full_prefix_replay=True,
            state_kind="NONE / REPLAY",
        )

    def begin(self, committed_prefix: Sequence[int]) -> tuple[int, dict[str, Any]]:
        self._logical = list(map(int, committed_prefix))
        return 0, {"begin_policy": "NO_OP; replay paid in propose"}

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        if list(map(int, committed_prefix)) != self._logical:
            raise AssertionError("legacy replay logical prefix drift")
        tokens, elapsed = self._legacy.propose(list(map(int, committed_prefix)), int(width))
        return Proposal(tokens=list(tokens), timing=DraftStepTiming(propose_ns=int(elapsed)))

    def reconcile(
        self,
        committed_prefix_before: Sequence[int],
        proposals: Sequence[int],
        accepted: int,
        committed_this_round: Sequence[int],
    ) -> tuple[int, dict[str, Any]]:
        expected = list(map(int, committed_prefix_before))
        if expected != self._logical:
            raise AssertionError("legacy replay reconcile prefix drift")
        self._logical.extend(map(int, committed_this_round))
        return 0, {"reconcile_policy": "LOGICAL_ONLY; next proposal replays complete prefix"}

    def logical_state_length(self) -> int | None:
        return len(self._logical)

    def finish(self) -> tuple[int, dict[str, Any]]:
        self._logical = []
        return 0, {"finish_policy": "LOGICAL_RESET"}


class OptimumDraftEngine:
    """Small forward-only wrapper for the frozen OpenVINO causal-LM IR.

    R0 decides whether a device exposes external past_key_values or an internal
    VariableState representation.  No result from this class is admissible until
    the complete path passes the prospective exactness gates.
    """

    def __init__(self, device: str, *, ov_config: dict[str, Any] | None = None):
        import torch
        from optimum.intel.openvino import OVModelForCausalLM

        self.torch = torch
        self.device = device
        self.model = OVModelForCausalLM.from_pretrained(
            str(DRAFT_IR), device=device, compile=True, ov_config=ov_config or {}
        )
        self.model.compile()
        self.stateful = bool(getattr(self.model, "stateful", False))
        self.use_cache = bool(getattr(self.model, "use_cache", False))
        self.request = getattr(self.model, "request", None)
        if self.request is None:
            raise RuntimeError("Optimum model compiled without an accessible InferRequest")
        compiled = self.request.get_compiled_model()
        self.execution_devices = _as_list(compiled.get_property("EXECUTION_DEVICES"))
        if self.execution_devices != [device]:
            raise RuntimeError(f"execution binding mismatch: requested {device}, got {self.execution_devices}")
        self.variable_states = list(self.request.query_state())
        self.state_kind = (
            "OPENVINO_VARIABLE_STATE"
            if self.stateful or self.variable_states
            else "EXPLICIT_PAST_KEY_VALUES"
        )

    def forward(self, token_ids: Sequence[int], past_key_values=None):
        ids = self.torch.tensor([list(map(int, token_ids))], dtype=self.torch.long)
        out = self.model(input_ids=ids, past_key_values=past_key_values)
        logits = out.logits
        next_token = int(self.torch.argmax(logits[0, -1]).item())
        return next_token, out.past_key_values

    def reset_internal_state(self) -> None:
        try:
            self.request.reset_state()
        except Exception:
            for state in self.request.query_state():
                state.reset()
        if hasattr(self.model, "_past_length"):
            self.model._past_length = 0
        if hasattr(self.model, "next_beam_idx"):
            self.model.next_beam_idx = None

    @staticmethod
    def _read_state_tensor(state):
        try:
            return state.state
        except Exception:
            return state.get_state()

    @staticmethod
    def _write_state_tensor(state, tensor) -> None:
        # This OpenVINO 2026.3 binding exposes a read/write `state` property,
        # but no set_state() method. R0 reads back every restored tensor.
        state.state = tensor

    def snapshot_internal_state(self) -> tuple[list[tuple[str, np.ndarray]], dict[str, Any], int]:
        """Deep-copy internal VariableState and the Optimum bookkeeping needed to restore it."""
        start = _ns()
        snapshot: list[tuple[str, np.ndarray]] = []
        for state in self.request.query_state():
            tensor = self._read_state_tensor(state)
            # R0 must reject a device/type for which a lossless host copy cannot be made.
            arr = np.array(tensor.data, copy=True)
            name = getattr(state, "name", None)
            if name is None:
                try:
                    name = state.get_name()
                except Exception:
                    name = "<unknown>"
            snapshot.append((str(name), arr))
        bookkeeping = {
            "_past_length": copy.deepcopy(getattr(self.model, "_past_length", None)),
            "next_beam_idx": copy.deepcopy(getattr(self.model, "next_beam_idx", None)),
        }
        return snapshot, bookkeeping, _ns() - start

    def restore_internal_state(
        self, snapshot: list[tuple[str, np.ndarray]], bookkeeping: dict[str, Any]
    ) -> tuple[int, int]:
        start = _ns()
        states = list(self.request.query_state())
        if len(states) != len(snapshot):
            raise RuntimeError("VariableState cardinality changed between checkpoint and restore")
        transferred = 0
        for state, (saved_name, arr) in zip(states, snapshot):
            name = getattr(state, "name", None)
            if name is None:
                name = state.get_name()
            if str(name) != saved_name:
                raise RuntimeError(f"VariableState restore order drift: {name} != {saved_name}")
            transferred += int(arr.nbytes)
            self._write_state_tensor(state, ov.Tensor(arr))
            if os.environ.get("HETEROSPEC_R0_VERIFY_RESTORE") == "1":
                restored = np.array(self._read_state_tensor(state).data, copy=True)
                if restored.shape != arr.shape or restored.dtype != arr.dtype or restored.tobytes() != arr.tobytes():
                    raise RuntimeError(
                        f"VariableState restore readback mismatch: {saved_name}; "
                        f"saved={arr.shape}/{arr.dtype} restored={restored.shape}/{restored.dtype}"
                    )
        if bookkeeping.get("_past_length") is not None:
            self.model._past_length = copy.deepcopy(bookkeeping["_past_length"])
        if "next_beam_idx" in bookkeeping:
            self.model.next_beam_idx = copy.deepcopy(bookkeeping["next_beam_idx"])
        return _ns() - start, transferred


class OptimumReplayDraft:
    """Same-frontend replay control for isolating frontend changes from state reuse."""

    def __init__(self, device: str, target_ubatch: int = 1, *, ov_config: dict[str, Any] | None = None):
        self.engine = OptimumDraftEngine(device, ov_config=ov_config)
        self.device = device
        self._logical: list[int] = []
        self.identity = PathIdentity(
            name=f"OPTIMUM_REPLAY_{device}_UB{target_ubatch}",
            target_ubatch=target_ubatch,
            draft_device=device,
            draft_frontend="OPTIMUM_OVMODEL",
            state_policy="FULL_PREFIX_REPLAY",
        )
        self.capabilities = DraftCapabilities(
            frontend="OPTIMUM_OVMODEL",
            requested_device=device,
            actual_execution_devices=self.engine.execution_devices,
            state_policy="FULL_PREFIX_REPLAY",
            supports_persistent_state=False,
            supports_checkpoint=False,
            supports_partial_reconcile=False,
            hidden_full_prefix_replay=True,
            state_kind=self.engine.state_kind,
        )

    def begin(self, committed_prefix: Sequence[int]) -> tuple[int, dict[str, Any]]:
        self._logical = list(map(int, committed_prefix))
        return 0, {"begin_policy": "NO_OP; replay paid in propose"}

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        prefix = list(map(int, committed_prefix))
        if prefix != self._logical:
            raise AssertionError("same-frontend replay logical prefix drift")
        start = _ns()
        if self.engine.stateful:
            self.engine.reset_internal_state()
        next_token, past = self.engine.forward(prefix, past_key_values=None)
        out: list[int] = []
        for _ in range(int(width)):
            token = int(next_token)
            out.append(token)
            next_token, past = self.engine.forward([token], past_key_values=past)
        elapsed = _ns() - start
        return Proposal(tokens=out, timing=DraftStepTiming(propose_ns=elapsed))

    def reconcile(
        self,
        committed_prefix_before: Sequence[int],
        proposals: Sequence[int],
        accepted: int,
        committed_this_round: Sequence[int],
    ) -> tuple[int, dict[str, Any]]:
        if list(map(int, committed_prefix_before)) != self._logical:
            raise AssertionError("same-frontend replay reconcile prefix drift")
        self._logical.extend(map(int, committed_this_round))
        return 0, {"reconcile_policy": "LOGICAL_ONLY"}

    def logical_state_length(self) -> int | None:
        return len(self._logical)

    def finish(self) -> tuple[int, dict[str, Any]]:
        self._logical = []
        if self.engine.stateful:
            self.engine.reset_internal_state()
        return 0, {"finish_policy": "RESET"}


class OptimumPersistentDraft:
    """Persistent draft adapter with exact checkpoint/reconcile semantics.

    External-PKV models retain immutable committed past_key_values and speculate
    into a local work state.  Internal-state models take a deep VariableState
    checkpoint before speculation and restore it on partial rejection.  Any copy
    or restore cost is charged to checkpoint/reconcile and therefore to the
    primary end-to-end boundary.
    """

    def __init__(self, device: str, target_ubatch: int = 1, *, ov_config: dict[str, Any] | None = None):
        self.engine = OptimumDraftEngine(device, ov_config=ov_config)
        self.device = device
        self.identity = PathIdentity(
            name=f"PERSIST_{device}_UB{target_ubatch}",
            target_ubatch=target_ubatch,
            draft_device=device,
            draft_frontend="OPTIMUM_OVMODEL",
            state_policy="PERSISTENT_RECONCILABLE",
        )
        supports = self.engine.use_cache and (
            (not self.engine.stateful) or bool(self.engine.variable_states)
        )
        self.capabilities = DraftCapabilities(
            frontend="OPTIMUM_OVMODEL",
            requested_device=device,
            actual_execution_devices=self.engine.execution_devices,
            state_policy="PERSISTENT_RECONCILABLE",
            supports_persistent_state=bool(supports),
            supports_checkpoint=bool(supports),
            supports_partial_reconcile=bool(supports),
            hidden_full_prefix_replay=False,
            state_kind=self.engine.state_kind,
            notes=["R0 forced-state tests are mandatory before qualification"],
        )
        if not supports:
            raise RuntimeError(f"frontend does not expose a reconcilable cache on {device}")
        self._logical: list[int] = []
        self._past = None
        self._next_token: int | None = None
        self._marker = None
        self._checkpoint = None
        self._proposal_past = None
        self._proposal_next: int | None = None

    def begin(self, committed_prefix: Sequence[int]) -> tuple[int, dict[str, Any]]:
        prefix = list(map(int, committed_prefix))
        start = _ns()
        if self.engine.stateful:
            self.engine.reset_internal_state()
        next_token, past = self.engine.forward(prefix, past_key_values=None)
        elapsed = _ns() - start
        self._logical = prefix
        self._next_token = int(next_token)
        self._past = past
        self._marker = past
        self._checkpoint = None
        return elapsed, {
            "state_kind": self.engine.state_kind,
            "state_bytes": _tensor_nbytes(past),
            "policy": "one draft prompt initialization charged inside primary decode window",
        }

    def _advance_external(self, tokens: Sequence[int], past, next_token: int | None):
        cur_past = past
        cur_next = next_token
        for token in map(int, tokens):
            cur_next, cur_past = self.engine.forward([token], past_key_values=cur_past)
        return cur_past, int(cur_next) if cur_next is not None else None

    def _advance_internal(self, tokens: Sequence[int], marker):
        cur_marker = marker
        cur_next = self._next_token
        for token in map(int, tokens):
            cur_next, cur_marker = self.engine.forward([token], past_key_values=cur_marker)
        return cur_marker, int(cur_next) if cur_next is not None else None

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        prefix = list(map(int, committed_prefix))
        if prefix != self._logical:
            raise AssertionError("persistent draft logical prefix drift before propose")
        timing = DraftStepTiming()
        metadata: dict[str, Any] = {"state_kind": self.engine.state_kind}

        if self.engine.stateful:
            snap, bookkeeping, checkpoint_ns = self.engine.snapshot_internal_state()
            timing.checkpoint_ns = checkpoint_ns
            timing.checkpoint_bytes = sum(arr.nbytes for _, arr in snap)
            self._checkpoint = (snap, bookkeeping)
            work_marker = self._marker
            next_token = self._next_token
            out: list[int] = []
            start = _ns()
            for _ in range(int(width)):
                if next_token is None:
                    raise RuntimeError("persistent draft has no next-token logits")
                token = int(next_token)
                out.append(token)
                next_token, work_marker = self.engine.forward([token], past_key_values=work_marker)
            timing.propose_ns = _ns() - start
            self._proposal_past = work_marker
            self._proposal_next = int(next_token) if next_token is not None else None
        else:
            # Optimum's stateless explicit-PKV path copies every present tensor out
            # of the InferRequest, so retaining `self._past` is a logical checkpoint
            # without a full state copy. R0 still verifies that the object is not
            # mutated by proposal inference.
            timing.checkpoint_bytes = _tensor_nbytes(self._past)
            self._checkpoint = self._past
            work_past = self._past
            next_token = self._next_token
            out = []
            start = _ns()
            for _ in range(int(width)):
                if next_token is None:
                    raise RuntimeError("persistent draft has no next-token logits")
                token = int(next_token)
                out.append(token)
                next_token, work_past = self.engine.forward([token], past_key_values=work_past)
            timing.propose_ns = _ns() - start
            self._proposal_past = work_past
            self._proposal_next = int(next_token) if next_token is not None else None

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
        if not proposals:
            # Initial target-only token or output-boundary target-only round.
            if self.engine.stateful:
                marker, next_token = self._advance_internal(committed, self._marker)
                self._marker, self._next_token = marker, next_token
            else:
                past, next_token = self._advance_external(committed, self._past, self._next_token)
                self._past, self._next_token = past, next_token
        elif accepted == len(proposals):
            # Proposal state already contains every accepted draft token. Only the
            # final target bonus must be incorporated into the committed draft state.
            bonus = committed[-1]
            if self.engine.stateful:
                self._marker = self._proposal_past
                self._next_token = self._proposal_next
                marker, next_token = self._advance_internal([bonus], self._marker)
                self._marker, self._next_token = marker, next_token
            else:
                self._past = self._proposal_past
                self._next_token = self._proposal_next
                past, next_token = self._advance_external([bonus], self._past, self._next_token)
                self._past, self._next_token = past, next_token
        else:
            # Restore the committed checkpoint, then advance only the actually
            # committed accepted prefix and target correction. At k=2 this is at
            # most two tokens, never a full-prefix rebuild.
            if self.engine.stateful:
                if self._checkpoint is None:
                    raise RuntimeError("missing VariableState checkpoint")
                snap, bookkeeping = self._checkpoint
                _, transferred = self.engine.restore_internal_state(snap, bookkeeping)
                self._marker = self._past
                marker, next_token = self._advance_internal(committed, self._marker)
                self._marker, self._next_token = marker, next_token
            else:
                self._past = self._checkpoint
                past, next_token = self._advance_external(committed, self._past, self._next_token)
                self._past, self._next_token = past, next_token

        elapsed = _ns() - start
        self._logical.extend(committed)
        self._checkpoint = None
        self._proposal_past = None
        self._proposal_next = None
        return elapsed, {
            "state_transfer_bytes": int(transferred),
            "accepted": int(accepted),
            "committed": committed,
            "state_kind": self.engine.state_kind,
            "checkpoint_restored": bool(proposals and accepted < len(proposals)),
        }

    def logical_state_length(self) -> int | None:
        return len(self._logical)

    def finish(self) -> tuple[int, dict[str, Any]]:
        start = _ns()
        if self.engine.stateful:
            self.engine.reset_internal_state()
        self._logical = []
        self._past = None
        self._marker = None
        self._next_token = None
        self._checkpoint = None
        self._proposal_past = None
        self._proposal_next = None
        return _ns() - start, {"finish_policy": "request state invalidated"}


__all__ = [
    "LegacyGenAIReplayDraft",
    "OptimumReplayDraft",
    "OptimumPersistentDraft",
    "OptimumDraftEngine",
]
