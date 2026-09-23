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

from runtime_draft import OptimumDraftEngine
from runtime_runner import run_speculative
from runtime_shared_draft import SharedOptimumPersistentDraft, SharedOptimumReplayDraft
from runtime_target import LlamaAPI, RuntimeLlamaTarget, RuntimeTargetModel

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


def target_state_cases(target: RuntimeLlamaTarget, ubatch: int) -> dict:
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
    """Proxy that makes any draft proposal at the one-token boundary fail R0."""

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


def persistent_vs_replay(device: str, tokenizer_target: RuntimeLlamaTarget, target_ubatch: int) -> dict:
    prompt = tokenizer_target.tokenize(FORMATTED, True)
    vocab_size = tokenizer_target.n_vocab
    patterns = [0, 1, 2, 0, 2, 1, 0]

    # One physical compiled engine per device. Stateful policies cannot be
    # interleaved on that engine, so run the complete persistent forced trace,
    # reset, then replay the identical committed ledger with the replay oracle.
    engine = OptimumDraftEngine(device)
    persistent = SharedOptimumPersistentDraft(engine, target_ubatch=target_ubatch)
    oracle = SharedOptimumReplayDraft(engine, target_ubatch=target_ubatch)

    persistent.begin(prompt)
    logical = list(prompt)
    persistent_trace = []
    for round_id, forced_accept in enumerate(patterns):
        pp = persistent.propose(logical, 2)
        committed = forced_committed(pp.tokens, forced_accept, vocab_size)
        _, p_meta = persistent.reconcile(logical, pp.tokens, forced_accept, committed)
        logical.extend(committed)
        ok = persistent.logical_state_length() == len(logical)
        row = {
            "round": round_id,
            "forced_accept": forced_accept,
            "proposal": list(pp.tokens),
            "committed": committed,
            "persistent_logical_length": persistent.logical_state_length(),
            "expected_logical_length": len(logical),
            "state_transfer_bytes": p_meta.get("state_transfer_bytes", 0),
            "pass": ok,
        }
        persistent_trace.append(row)
        if not ok:
            raise AssertionError(row)
    persistent.finish()

    oracle.begin(prompt)
    oracle_logical = list(prompt)
    records = []
    for expected in persistent_trace:
        op = oracle.propose(oracle_logical, 2)
        proposal_equal = list(op.tokens) == expected["proposal"]
        committed = list(expected["committed"])
        oracle.reconcile(
            oracle_logical,
            op.tokens,
            int(expected["forced_accept"]),
            committed,
        )
        oracle_logical.extend(committed)
        ok = (
            proposal_equal
            and oracle.logical_state_length() == len(oracle_logical)
            and expected["pass"]
        )
        records.append({
            **expected,
            "oracle_proposal": list(op.tokens),
            "proposal_equal": proposal_equal,
            "oracle_logical_length": oracle.logical_state_length(),
            "pass": ok,
        })
        if not ok:
            raise AssertionError(records[-1])
    oracle.finish()

    first_proposal = persistent_trace[0]["proposal"]
    persistent.begin(prompt)
    pp = persistent.propose(prompt, 2)
    persistent_reset_ok = list(pp.tokens) == first_proposal
    persistent.finish()
    oracle.begin(prompt)
    op = oracle.propose(prompt, 2)
    oracle_reset_ok = list(op.tokens) == first_proposal
    oracle.finish()
    records.append({
        "round": "reset_repeat",
        "persistent": list(pp.tokens),
        "oracle": list(op.tokens),
        "first_proposal": first_proposal,
        "pass": persistent_reset_ok and oracle_reset_ok,
    })

    boundary = run_speculative(tokenizer_target, ProposalForbidden(persistent), prompt, 1)
    boundary_ok = len(boundary["tokens"]) == 1 and boundary["proposed"] == 0 and len(boundary["rounds"]) == 1
    records.append({
        "round": "output_cap_one_no_draft_proposal",
        "generated": boundary["tokens"],
        "proposed": boundary["proposed"],
        "round_count": len(boundary["rounds"]),
        "pass": boundary_ok,
    })
    if not boundary_ok:
        raise AssertionError(records[-1])

    return {
        "device": device,
        "target_ubatch": target_ubatch,
        "persistent_capabilities": persistent.capabilities.__dict__,
        "oracle_capabilities": oracle.capabilities.__dict__,
        "engine_execution_devices": engine.execution_devices,
        "records": records,
        "pass": all(x["pass"] for x in records),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", nargs="+", choices=["CPU", "NPU"], default=["CPU", "NPU"])
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    result = {
        "schema": "heterospec.358h.runtime.r0_state_tests.v3",
        "formal": False,
        "claim_status": "NON_FORMAL / INVALID_FOR_PERFORMANCE_CLAIMS",
        "target": {},
        "draft": {},
        "failures": [],
    }

    api = LlamaAPI()
    host = RuntimeTargetModel(api)
    target_ub1 = None
    try:
        target_ub1 = RuntimeLlamaTarget(api, ubatch=1, shared_model=host)
        result["target"]["UB1"] = target_state_cases(target_ub1, 1)
    except Exception as exc:
        result["target"]["UB1"] = {"pass": False, "error": repr(exc)}
        result["failures"].append(f"TARGET_UB1: {exc!r}")

    try:
        target_ub2 = RuntimeLlamaTarget(api, ubatch=2, shared_model=host)
        result["target"]["UB2"] = target_state_cases(target_ub2, 2)
    except Exception as exc:
        result["target"]["UB2"] = {"pass": False, "error": repr(exc)}
        result["failures"].append(f"TARGET_UB2: {exc!r}")

    if target_ub1 is None:
        for device in args.devices:
            result["draft"][device] = {"pass": False, "status": "NOT_TESTABLE_WITHOUT_TARGET_UB1"}
    else:
        for device in args.devices:
            try:
                result["draft"][device] = persistent_vs_replay(device, target_ub1, 1)
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
