#!/usr/bin/env python3
"""Runtime policy primitives; intentionally not enabled by the formal R2 study.

The policy architecture is qualification-first: a path that is not admitted by
its correctness registry can never be selected because it appears cheap.  The
profitability guard learns only from complete realized request boundaries.
A formal adaptive-policy claim requires a separately frozen R3 protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CostObservation:
    path: str
    end_to_end_ns: int
    committed_tokens: int

    @property
    def ns_per_committed_token(self) -> float:
        if self.end_to_end_ns <= 0 or self.committed_tokens <= 0:
            raise ValueError("cost observation requires positive time and committed tokens")
        return self.end_to_end_ns / self.committed_tokens


class QualificationRegistry:
    def __init__(self, registry_json: dict[str, Any]):
        if registry_json.get("status") != "FROZEN_FOR_R2":
            raise ValueError("registry must be frozen before policy use")
        self.raw = registry_json
        self.paths = dict(registry_json.get("registry", {}))
        self.formal_conditions = tuple(registry_json.get("formal_conditions", []))

    @classmethod
    def from_path(cls, path: Path) -> "QualificationRegistry":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def qualified(self, path: str) -> bool:
        if path == "TARGET_UB1":
            return True
        row = self.paths.get(path, {})
        return bool(row.get("status") == "QUALIFIED" and row.get("formal_performance_allowed"))

    def require_qualified(self, path: str) -> None:
        if not self.qualified(path):
            raise RuntimeError(f"runtime path is not correctness-qualified: {path}")


class RealizedProfitabilityGuard:
    """Conservative rolling guard based on complete realized request cost.

    This is an architecture hook, not an R2 estimator. It intentionally does not
    infer draft cost from isolated token/s, acceptance alone, or accepted draft
    tokens alone. `committed_tokens` is complete target-visible progress C summed
    over the request.
    """

    def __init__(
        self,
        registry: QualificationRegistry,
        *,
        min_samples: int = 8,
        safety_margin: float = 0.05,
        window: int = 32,
    ):
        if min_samples <= 0 or window < min_samples:
            raise ValueError("invalid guard sample/window configuration")
        if not (0.0 <= safety_margin < 1.0):
            raise ValueError("safety_margin must be in [0,1)")
        self.registry = registry
        self.min_samples = int(min_samples)
        self.safety_margin = float(safety_margin)
        self.window = int(window)
        self._target: list[CostObservation] = []
        self._runtime: dict[str, list[CostObservation]] = {}

    def _append(self, table: list[CostObservation], obs: CostObservation) -> None:
        table.append(obs)
        if len(table) > self.window:
            del table[:-self.window]

    def observe_target(self, end_to_end_ns: int, committed_tokens: int) -> None:
        self._append(
            self._target,
            CostObservation("TARGET_UB1", int(end_to_end_ns), int(committed_tokens)),
        )

    def observe_runtime(self, path: str, end_to_end_ns: int, committed_tokens: int) -> None:
        self.registry.require_qualified(path)
        table = self._runtime.setdefault(path, [])
        self._append(table, CostObservation(path, int(end_to_end_ns), int(committed_tokens)))

    @staticmethod
    def _mean_cost(rows: list[CostObservation]) -> float:
        return sum(x.ns_per_committed_token for x in rows) / len(rows)

    def decision(self, candidate_path: str) -> dict[str, Any]:
        self.registry.require_qualified(candidate_path)
        candidate = self._runtime.get(candidate_path, [])
        if len(self._target) < self.min_samples or len(candidate) < self.min_samples:
            return {
                "use_speculation": False,
                "reason": "INSUFFICIENT_REALIZED_COST_HISTORY",
                "target_samples": len(self._target),
                "candidate_samples": len(candidate),
            }
        target_cost = self._mean_cost(self._target)
        runtime_cost = self._mean_cost(candidate)
        threshold = target_cost * (1.0 - self.safety_margin)
        return {
            "use_speculation": runtime_cost < threshold,
            "reason": "REALIZED_COST_GUARD",
            "target_ns_per_committed_token": target_cost,
            "runtime_ns_per_committed_token": runtime_cost,
            "required_runtime_threshold_ns_per_committed_token": threshold,
            "safety_margin": self.safety_margin,
            "target_samples": len(self._target),
            "candidate_samples": len(candidate),
        }


__all__ = ["CostObservation", "QualificationRegistry", "RealizedProfitabilityGuard"]
