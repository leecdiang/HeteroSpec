#!/usr/bin/env python3
"""R0-only forced state-machine tests for the prospective 358H runtime.

No timings emitted by this file are valid performance evidence. The purpose is
semantic qualification: persistent state must be indistinguishable from a
same-frontend full-prefix replay oracle after every forced reconcile pattern.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_draft import OptimumPersistentDraft, OptimumReplayDraft
from runtime_runner import run_speculative
from runtime_target import LlamaAPI, RuntimeLlamaTarget

PROMPT = "Write a Python function that returns the square of an integer."
FORMATTED = (
    f"<|im_start|>user\n{PROMPT}<|im_end|>\n"
    f"<|im_start|>assistant\n<think>\n\n</think>\n\n"
)


def forced_committed(proposals: list[int], accepted: int, vocab_size: int) -> list[int]:
    if accepted < 0 or accepted > len(proposals):
        raise ValueError("invalid forced accepted count")
    if not proposals:
        return [0]
    if accepted == len(proposals):
        bonus = (int(proposals[-1]) + 1) % vocab_size
        return list(proposals) + [bonus]
    mismatch = (int(proposals[accepted]) + 1) % vocab_size
    if mismatch == int(proposals[accepted]):
        mismatch = (mismatch + 1) % vocab_size
    return list(proposals[:accepted]) + [mismatch]


def target_state_cases(ubatch: int) -> dict:
    api = LlamaAPI()
    target = RuntimeLlamaTarget(api, ubatch=ubatch)
    prompt = target.tokenize(FORMATTED, True)
    target.reset_prefill(prompt)
    baseline = target.baseline(12)
    target.reset_prefill(prompt)
    cases = []

    def one(name: str, proposals: list[int], expected: list[int]):
        before = len(target.history)
        got = target.verify(proposals)
        pos = target.state_position()
        ok = got == expected and pos == len(target.history) - 1
        cases.append(
            {
                "case": name,
                "before": before,
                "proposals": proposals,
                "committed": got,
                "expected": expected,
                "state_position": pos,
                "pass": ok,
            }
        )
        if not ok:
            raise AssertionError(cases[-1])

    one("zero_accepted", [baseline[0] + 1, baseline[1]], [baseline[0]])
    one("one_accepted", [baseline[1], baseline[2] + 1], [baseline[1], baseline[2]])
    one("two_accepted_bonus", [baseline[3], baseline[4]], [baseline[3], baseline[4], baseline[5]])
    one("rejection_1", [baseline[6] + 1, baseline[7]], [baseline[6]])
    one("rejection_2", [baseline[7] + 1, baseline[8]], [baseline[7]])
    target.reset_prefill(prompt)
    r1 = target.baseline(8)
    target.reset_prefill(prompt)
    r2 = target.baseline(8)
    cases.append({"case": "reset_repeat", "pass": r1 == r2 == baseline[:8]})
    return {"ubatch": ubatch, "cases": cases, "pass": all(x["pass"] for x in cases)}


class ProposalForbidden:
    """Proxy that makes a width-zero draft call an immediate test failure."""

    def __init__(self, inner):
        self.inner = inner
        self.identity = inner.identity
        self.capabilities = inner.capabilities

    def begin(self, committed_prefix):
        return self.inner.begin(committed_prefix)

    def propose(self, committed_prefix, width):
        raise AssertionError(f"draft.propose must not be called at one-token output boundary; width={width}")

    def reconcile(self, committed_prefix_before, proposals, accepted, committed_this_round):
        return self.inner.reconcile(committed_prefix_before, proposals, accepted, committed_this_round)

    def logical_state_length(self):
        return self.inner.logical_state_length()

    def finish(self):
        return self.inner.finish()


def persistent_vs_replay(device: str, target_ubatch: int) -> dict:
    api = LlamaAPI()
    tokenizer_target = RuntimeLlamaTarget(api, ubatch=1)
    prompt = tokenizer_target.tokenize(FORMATTED, True)
    vocab_size = tokenizer_target.n_vocab

    persistent = OptimumPersistentDraft(device, target_ubatch=target_ubatch)
    oracle = OptimumReplayDraft(device, target_ubatch=target_ubatch)
    persistent.begin(prompt)
    oracle.begin(prompt)
    logical = list(prompt)
    patterns = [0, 1, 2, 0, 2, 1, 0]
    records = []
    first_proposal = None

    for round_id, forced_accept in enumerate(patterns):
        pp = persistent.propose(logical, 2)
        op = oracle.propose(logical, 2)
        proposal_equal = pp.tokens == op.tokens
        if first_proposal is None:
            first_proposal = list(pp.tokens)
        if not proposal_equal:
            raise AssertionError(
                f"persistent proposal diverged from full replay oracle on {device} round {round_id}: "
                f"{pp.tokens} != {op.tokens}"
            )
        committed = forced_committed(pp.tokens, forced_accept, vocab_size)
        _, p_meta = persistent.reconcile(logical, pp.tokens, forced_accept, committed)
        oracle.reconcile(logical, op.tokens, forced_accept, committed)
        logical.extend(committed)
        ok = persistent.logical_state_length() == len(logical)
        records.append(
            {
                "round": round_id,
                "forced_accept": forced_accept,
                "proposal": pp.tokens,
                "oracle_proposal": op.tokens,
                "proposal_equal": proposal_equal,
                "committed": committed,
                "persistent_logical_length": persistent.logical_state_length(),
                "expected_logical_length": len(logical),
                "state_transfer_bytes": p_meta.get("state_transfer_bytes", 0),
                "pass": ok,
            }
        )
        if not ok:
            raise AssertionError(records[-1])

    persistent.finish()
    oracle.finish()

    persistent.begin(prompt)
    oracle.begin(prompt)
    pp = persistent.propose(prompt, 2)
    op = oracle.propose(prompt, 2)
    reset_ok = pp.tokens == op.tokens == first_proposal
    persistent.finish()
    oracle.finish()
    records.append(
        {
            "round": "reset_repeat",
            "persistent": pp.tokens,
            "oracle": op.tokens,
            "first_proposal": first_proposal,
            "pass": reset_ok,
        }
    )

    # Output-budget boundary: with an output cap of one, the runtime should
    # commit the mandatory initial target-only token and terminate without ever
    # invoking the draft proposal API.
    boundary_target = RuntimeLlamaTarget(api, ubatch=1)
    boundary = run_speculative(boundary_target, ProposalForbidden(persistent), prompt, 1)
    boundary_ok = len(boundary["tokens"]) == 1 and boundary["proposed"] == 0 and len(boundary["rounds"]) == 1
    records.append(
        {
            "round": "output_cap_one_no_draft_proposal",
            "generated": boundary["tokens"],
            "proposed": boundary["proposed"],
            "round_count": len(boundary["rounds"]),
            "pass": boundary_ok,
        }
    )
    if not boundary_ok:
        raise AssertionError(records[-1])

    return {
        "device": device,
        "target_ubatch": target_ubatch,
        "persistent_capabilities": persistent.capabilities.__dict__,
        "oracle_capabilities": oracle.capabilities.__dict__,
        "records": records,
        "pass": all(x["pass"] for x in records),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", nargs="+", choices=["CPU", "NPU"], default=["CPU", "NPU"])
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    result = {
        "schema": "heterospec.358h.runtime.r0_state_tests.v1",
        "formal": False,
        "claim_status": "NON_FORMAL / INVALID_FOR_PERFORMANCE_CLAIMS",
        "target": {},
        "draft": {},
        "failures": [],
    }

    for ubatch in (1, 2):
        try:
            result["target"][f"UB{ubatch}"] = target_state_cases(ubatch)
        except Exception as exc:
            result["target"][f"UB{ubatch}"] = {"pass": False, "error": repr(exc)}
            result["failures"].append(f"TARGET_UB{ubatch}: {exc!r}")

    for device in args.devices:
        try:
            result["draft"][device] = persistent_vs_replay(device, 1)
        except Exception as exc:
            result["draft"][device] = {
                "pass": False,
                "status": "IMPLEMENTATION_UNAVAILABLE_OR_STATE_TEST_FAIL",
                "error": repr(exc),
            }
            result["failures"].append(f"{device}: {exc!r}")

    result["pass"] = all(v.get("pass", False) for v in result["target"].values()) and all(
        v.get("pass", False) for v in result["draft"].values()
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "failures": result["failures"]}, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
