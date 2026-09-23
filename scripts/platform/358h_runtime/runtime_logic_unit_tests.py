#!/usr/bin/env python3
"""Hardware-independent tests for the prospective runtime orchestrator.

These tests validate only control-flow/accounting invariants. They do not qualify
OpenVINO, llama.cpp, CPU, NPU, Vulkan, or any performance claim.
"""
from __future__ import annotations

from dataclasses import dataclass

from runtime_runner import run_speculative, run_target_only
from runtime_types import DraftCapabilities, DraftStepTiming, PathIdentity, Proposal, TimingBreakdown


class FakeTarget:
    def __init__(self, stream: list[int]):
        self.stream = list(stream)
        self.prompt_len = 0
        self.history: list[int] = []
        self.identity = PathIdentity("FAKE_TARGET", 1, None, None, None)

    def reset_prefill(self, prompt: list[int]) -> None:
        self.prompt_len = len(prompt)
        self.history = list(prompt)

    def _output_index(self) -> int:
        return len(self.history) - self.prompt_len

    def baseline(self, n: int) -> list[int]:
        start = self._output_index()
        out = self.stream[start : start + int(n)]
        if len(out) != int(n):
            raise RuntimeError("fake target stream exhausted")
        self.history.extend(out)
        return list(out)

    def verify(self, proposals: list[int]) -> list[int]:
        start = self._output_index()
        if not proposals:
            token = self.stream[start]
            self.history.append(token)
            return [token]
        accepted = 0
        while accepted < len(proposals) and proposals[accepted] == self.stream[start + accepted]:
            accepted += 1
        committed = list(proposals[:accepted]) + [self.stream[start + accepted]]
        self.history.extend(committed)
        return committed

    def state_position(self) -> int | None:
        return len(self.history) - 1 if self.history else None


@dataclass
class FakeRoundPlan:
    proposals: list[int]


class FakeDraft:
    def __init__(self, plans: list[FakeRoundPlan], *, forbid_propose: bool = False):
        self.plans = list(plans)
        self.forbid_propose = forbid_propose
        self.round = 0
        self.logical: list[int] = []
        self.propose_calls = 0
        self.identity = PathIdentity("FAKE_DRAFT", 1, "CPU", "FAKE", "PERSISTENT_RECONCILABLE")
        self.capabilities = DraftCapabilities(
            frontend="FAKE",
            requested_device="CPU",
            actual_execution_devices=["CPU"],
            state_policy="PERSISTENT_RECONCILABLE",
            supports_persistent_state=True,
            supports_checkpoint=True,
            supports_partial_reconcile=True,
            hidden_full_prefix_replay=False,
            state_kind="FAKE",
        )

    def begin(self, committed_prefix):
        self.logical = list(map(int, committed_prefix))
        self.round = 0
        return 7, {"fake": True}

    def propose(self, committed_prefix, width):
        self.propose_calls += 1
        if self.forbid_propose:
            raise AssertionError("propose called when forbidden")
        if list(map(int, committed_prefix)) != self.logical:
            raise AssertionError("fake draft logical drift before proposal")
        if self.round >= len(self.plans):
            raise RuntimeError("fake draft proposal plan exhausted")
        tokens = list(self.plans[self.round].proposals)
        self.round += 1
        if len(tokens) != int(width):
            raise AssertionError(f"fake plan width {len(tokens)} != requested {width}")
        return Proposal(
            tokens=tokens,
            timing=DraftStepTiming(
                checkpoint_ns=3,
                propose_ns=11,
                checkpoint_bytes=128,
            ),
        )

    def reconcile(self, committed_prefix_before, proposals, accepted, committed_this_round):
        if list(map(int, committed_prefix_before)) != self.logical:
            raise AssertionError("fake draft logical drift before reconcile")
        self.logical.extend(map(int, committed_this_round))
        return 5, {"state_transfer_bytes": 64 if proposals and accepted == 0 else 0}

    def logical_state_length(self):
        return len(self.logical)

    def finish(self):
        self.logical = []
        return 2, {"fake": True}


def assert_equal(a, b, label: str):
    if a != b:
        raise AssertionError(f"{label}: {a!r} != {b!r}")


def test_target_only() -> None:
    target = FakeTarget([10, 11, 12, 13])
    result = run_target_only(target, [1, 2, 3], 4)
    assert_equal(result["tokens"], [10, 11, 12, 13], "target-only tokens")
    assert_equal(result["committed"], 4, "target-only committed")


def test_mixed_acceptance_and_c() -> None:
    # Initial target-only commits 10. Then:
    # r1 proposals [11,99] => accept1 + correction12 => C=2
    # r2 proposals [77,88] => accept0 + correction13 => C=1
    # r3 width1 proposal [14] => accept1 + bonus15 => C=2
    stream = [10, 11, 12, 13, 14, 15]
    target = FakeTarget(stream)
    draft = FakeDraft([
        FakeRoundPlan([11, 99]),
        FakeRoundPlan([77, 88]),
        FakeRoundPlan([14]),
    ])
    result = run_speculative(target, draft, [1, 2, 3], 6)
    assert_equal(result["tokens"], stream, "mixed generated tokens")
    assert_equal([r["C"] for r in result["rounds"]], [1, 2, 1, 2], "round C")
    assert_equal([r["accepted"] for r in result["rounds"]], [0, 1, 0, 1], "round accepted")
    assert_equal(result["proposed"], 5, "proposed total")
    assert_equal(result["accepted"], 2, "accepted total")
    assert_equal(result["committed"], 6, "committed total")
    assert_equal(result["target_state_position"], 3 + 6 - 1, "target final state")


def test_full_accept_bonus() -> None:
    stream = [20, 21, 22, 23]
    target = FakeTarget(stream)
    draft = FakeDraft([FakeRoundPlan([21, 22])])
    result = run_speculative(target, draft, [7, 8], 4)
    assert_equal(result["tokens"], stream, "bonus tokens")
    assert_equal(result["rounds"][1]["accepted"], 2, "bonus accepted")
    assert_equal(result["rounds"][1]["bonus"], 23, "bonus token")
    assert_equal(result["rounds"][1]["correction"], None, "bonus correction")


def test_one_token_boundary_never_proposes() -> None:
    target = FakeTarget([30])
    draft = FakeDraft([], forbid_propose=True)
    result = run_speculative(target, draft, [4, 5], 1)
    assert_equal(result["tokens"], [30], "one-token output")
    assert_equal(result["proposed"], 0, "one-token proposed")
    assert_equal(draft.propose_calls, 0, "one-token propose calls")
    assert_equal(len(result["rounds"]), 1, "one-token rounds")


def test_timing_double_count_fails() -> None:
    timing = TimingBreakdown(
        draft_begin_ns=10,
        target_verification_ns=10,
        end_to_end_ns=19,
    )
    try:
        timing.reconcile_total()
    except AssertionError:
        return
    raise AssertionError("negative residual/double-count was silently accepted")


def main() -> int:
    tests = [
        test_target_only,
        test_mixed_acceptance_and_c,
        test_full_accept_bonus,
        test_one_token_boundary_never_proposes,
        test_timing_double_count_fails,
    ]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"PASS all {len(tests)} hardware-independent runtime logic tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
