#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Protocol, Sequence


class QualificationStatus(str, Enum):
    UNQUALIFIED = "UNQUALIFIED"
    QUALIFIED = "QUALIFIED"
    BLOCKED = "BLOCKED"
    IMPLEMENTATION_UNAVAILABLE = "IMPLEMENTATION_UNAVAILABLE"


@dataclass(frozen=True)
class PathIdentity:
    name: str
    target_ubatch: int
    draft_device: str | None
    draft_frontend: str | None
    state_policy: str | None


@dataclass
class TimingBreakdown:
    draft_begin_ns: int = 0
    draft_checkpoint_ns: int = 0
    draft_propose_ns: int = 0
    draft_reconcile_ns: int = 0
    draft_finish_ns: int = 0
    target_verification_ns: int = 0
    runtime_residual_ns: int = 0
    end_to_end_ns: int = 0

    @property
    def draft_total_ns(self) -> int:
        return (
            self.draft_begin_ns
            + self.draft_checkpoint_ns
            + self.draft_propose_ns
            + self.draft_reconcile_ns
            + self.draft_finish_ns
        )

    def reconcile_total(self) -> None:
        charged = self.draft_total_ns + self.target_verification_ns
        self.runtime_residual_ns = max(0, self.end_to_end_ns - charged)


@dataclass
class DraftStepTiming:
    checkpoint_ns: int = 0
    propose_ns: int = 0
    reconcile_ns: int = 0
    checkpoint_bytes: int = 0
    state_transfer_bytes: int = 0


@dataclass
class Proposal:
    tokens: list[int]
    timing: DraftStepTiming = field(default_factory=DraftStepTiming)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoundRecord:
    round_id: int
    prefix_before: int
    proposals: list[int]
    accepted: int
    committed: list[int]
    correction: int | None
    bonus: int | None
    C: int
    target_verification_ns: int
    draft_checkpoint_ns: int
    draft_propose_ns: int
    draft_reconcile_ns: int
    checkpoint_bytes: int
    state_transfer_bytes: int
    draft_logical_state_length: int | None
    target_state_position: int | None
    fallback_events: list[str] = field(default_factory=list)
    native_initial_target_only: bool = False


@dataclass
class RuntimeObservation:
    schema: str
    formal: bool
    claim_status: str
    path: PathIdentity
    task_id: str
    repetition: int
    prompt_token_count: int
    output_token_count: int
    generated_token_ids: list[int]
    exact_vs_reference: bool | None
    first_divergence: dict[str, Any] | None
    timing: TimingBreakdown
    rounds: list[RoundRecord]
    execution_binding: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DraftCapabilities:
    frontend: str
    requested_device: str
    actual_execution_devices: list[str]
    state_policy: str
    supports_persistent_state: bool
    supports_checkpoint: bool
    supports_partial_reconcile: bool
    hidden_full_prefix_replay: bool
    state_kind: str
    notes: list[str] = field(default_factory=list)


class DraftAdapter(Protocol):
    """Request-scoped draft interface used by the prospective runtime study.

    `begin` is deliberately inside the measured post-target-prefill window.  A
    persistent implementation may prefill the draft exactly once here.  A replay
    implementation may make begin a no-op and pay full-prefix reconstruction in
    every `propose` call.
    """

    identity: PathIdentity
    capabilities: DraftCapabilities

    def begin(self, committed_prefix: Sequence[int]) -> tuple[int, dict[str, Any]]:
        ...

    def propose(self, committed_prefix: Sequence[int], width: int) -> Proposal:
        ...

    def reconcile(
        self,
        committed_prefix_before: Sequence[int],
        proposals: Sequence[int],
        accepted: int,
        committed_this_round: Sequence[int],
    ) -> tuple[int, dict[str, Any]]:
        ...

    def logical_state_length(self) -> int | None:
        ...

    def finish(self) -> tuple[int, dict[str, Any]]:
        ...


class TargetAdapter(Protocol):
    identity: PathIdentity

    def reset_prefill(self, prompt: list[int]) -> None:
        ...

    def baseline(self, n: int) -> list[int]:
        ...

    def verify(self, proposals: list[int]) -> list[int]:
        ...

    def state_position(self) -> int | None:
        ...


def first_divergence(reference: Sequence[int], candidate: Sequence[int]) -> dict[str, Any] | None:
    for i, (a, b) in enumerate(zip(reference, candidate)):
        if a != b:
            return {"index": i, "reference_token": int(a), "candidate_token": int(b)}
    if len(reference) != len(candidate):
        i = min(len(reference), len(candidate))
        return {
            "index": i,
            "reference_token": int(reference[i]) if i < len(reference) else None,
            "candidate_token": int(candidate[i]) if i < len(candidate) else None,
        }
    return None


def accepted_prefix_length(proposals: Sequence[int], committed: Sequence[int]) -> int:
    accepted = 0
    for i, token in enumerate(proposals):
        if i >= len(committed) or int(committed[i]) != int(token):
            break
        accepted += 1
    return accepted
