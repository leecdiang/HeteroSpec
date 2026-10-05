"""Hardware-independent one-way policy state machine for trace qualification."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Decision:
    round_number: int
    committed_progress: int
    elapsed_cost_ns: int
    realized_ns_per_token: float | None
    threshold_ns_per_token: float
    action: str


@dataclass
class Guard:
    exploration_rounds: int
    margin: float
    target_reference_ns_per_token: float
    state: str = "SPECULATING"
    rounds: int = 0
    committed_progress: int = 0
    decisions: list[Decision] = field(default_factory=list)

    def __post_init__(self):
        if self.exploration_rounds < 1 or not 0 <= self.margin < 1:
            raise ValueError("Invalid candidate")
        if self.target_reference_ns_per_token <= 0:
            raise ValueError("Target reference must be positive")

    def observe_round(self, committed_total: int, elapsed_cost_ns: int) -> Decision | None:
        if self.state != "SPECULATING":
            raise RuntimeError("No speculation after fallback")
        if committed_total < self.committed_progress or elapsed_cost_ns < 0:
            raise ValueError("Invalid cumulative observation")
        self.rounds += 1
        self.committed_progress = committed_total
        if self.rounds < self.exploration_rounds:
            return None
        rate = elapsed_cost_ns / committed_total if committed_total else None
        threshold = (1 - self.margin) * self.target_reference_ns_per_token
        action = "CONTINUE" if rate is not None and rate <= threshold else "FALLBACK"
        decision = Decision(self.rounds, committed_total, elapsed_cost_ns, rate, threshold, action)
        self.decisions.append(decision)
        if action == "FALLBACK":
            self.state = "TARGET_ONLY"
        return decision
