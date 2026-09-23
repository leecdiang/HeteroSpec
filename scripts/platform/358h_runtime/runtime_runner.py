#!/usr/bin/env python3
from __future__ import annotations

import time
from dataclasses import asdict
from typing import Sequence

from runtime_types import (
    DraftAdapter,
    RoundRecord,
    TimingBreakdown,
    accepted_prefix_length,
)


def _ns() -> int:
    return time.perf_counter_ns()


def run_target_only(target, prompt_tokens: list[int], output_tokens: int) -> dict:
    """Matched reference: target prompt prefill is outside the primary decode timer."""
    target.reset_prefill(prompt_tokens)
    start = _ns()
    tokens = target.baseline(output_tokens)
    end = _ns()
    timing = TimingBreakdown(
        target_verification_ns=end - start,
        end_to_end_ns=end - start,
    )
    timing.reconcile_total()
    return {
        "tokens": tokens,
        "rounds": [],
        "timing": asdict(timing),
        "proposed": 0,
        "accepted": 0,
        "committed": len(tokens),
        "target_state_position": target.state_position(),
    }


def run_speculative(
    target,
    draft: DraftAdapter,
    prompt_tokens: list[int],
    output_tokens: int,
) -> dict:
    """Run one request under the prospective runtime accounting boundary.

    Only target prompt prefill is excluded.  Draft begin/prefill, checkpoint,
    proposal, reconcile, fallback and finish/reset are all inside end_to_end_ns.
    """
    if output_tokens <= 0:
        raise ValueError("output_tokens must be positive")

    target.reset_prefill(prompt_tokens)
    timing = TimingBreakdown()
    rounds: list[RoundRecord] = []
    out: list[int] = []
    proposed_total = 0
    accepted_total = 0

    start = _ns()
    begin_ns, begin_meta = draft.begin(prompt_tokens)
    timing.draft_begin_ns += int(begin_ns)

    # Preserve the pinned llama.cpp speculative-simple boundary used by the
    # closed campaign: one target-only token precedes the first draft round.
    target_start = _ns()
    first = target.verify([])
    target_end = _ns()
    target_ns = target_end - target_start
    timing.target_verification_ns += target_ns
    first = first[:output_tokens]

    reconcile_ns, reconcile_meta = draft.reconcile(
        prompt_tokens, [], 0, first
    )
    timing.draft_reconcile_ns += int(reconcile_ns)
    out.extend(first)
    rounds.append(
        RoundRecord(
            round_id=0,
            prefix_before=len(prompt_tokens),
            proposals=[],
            accepted=0,
            committed=list(first),
            correction=int(first[0]) if first else None,
            bonus=None,
            C=len(first),
            target_verification_ns=target_ns,
            draft_checkpoint_ns=0,
            draft_propose_ns=0,
            draft_reconcile_ns=int(reconcile_ns),
            checkpoint_bytes=0,
            state_transfer_bytes=int(reconcile_meta.get("state_transfer_bytes", 0)),
            draft_logical_state_length=draft.logical_state_length(),
            target_state_position=target.state_position(),
            fallback_events=list(reconcile_meta.get("fallback_events", [])),
            native_initial_target_only=True,
        )
    )

    if draft.logical_state_length() != len(prompt_tokens) + len(out):
        raise AssertionError("draft state drift after initial target-only token")
    if target.state_position() != len(prompt_tokens) + len(out) - 1:
        raise AssertionError("target state drift after initial target-only token")

    while len(out) < output_tokens:
        remaining = output_tokens - len(out)
        width = min(2, max(0, remaining - 1))
        committed_prefix = prompt_tokens + out

        proposal = draft.propose(committed_prefix, width)
        proposals = list(map(int, proposal.tokens))
        if len(proposals) != width:
            raise AssertionError(f"draft returned {len(proposals)} tokens for requested width {width}")
        timing.draft_checkpoint_ns += int(proposal.timing.checkpoint_ns)
        timing.draft_propose_ns += int(proposal.timing.propose_ns)
        proposed_total += len(proposals)

        target_start = _ns()
        committed = target.verify(proposals)
        target_end = _ns()
        target_ns = target_end - target_start
        timing.target_verification_ns += target_ns
        if len(committed) > remaining:
            raise AssertionError("target committed beyond the frozen output cap")

        accepted = accepted_prefix_length(proposals, committed)
        accepted_total += accepted
        correction = committed[-1] if proposals and accepted < len(proposals) else None
        bonus = committed[-1] if proposals and accepted == len(proposals) else None

        reconcile_ns, reconcile_meta = draft.reconcile(
            committed_prefix, proposals, accepted, committed
        )
        timing.draft_reconcile_ns += int(reconcile_ns)
        out.extend(map(int, committed))

        draft_len = draft.logical_state_length()
        target_pos = target.state_position()
        expected_len = len(prompt_tokens) + len(out)
        if draft_len != expected_len:
            raise AssertionError(f"draft state drift {draft_len} != {expected_len}")
        if target_pos != expected_len - 1:
            raise AssertionError(f"target state drift {target_pos} != {expected_len - 1}")

        rounds.append(
            RoundRecord(
                round_id=len(rounds),
                prefix_before=len(committed_prefix),
                proposals=proposals,
                accepted=accepted,
                committed=list(map(int, committed)),
                correction=int(correction) if correction is not None else None,
                bonus=int(bonus) if bonus is not None else None,
                C=len(committed),
                target_verification_ns=target_ns,
                draft_checkpoint_ns=int(proposal.timing.checkpoint_ns),
                draft_propose_ns=int(proposal.timing.propose_ns),
                draft_reconcile_ns=int(reconcile_ns),
                checkpoint_bytes=int(proposal.timing.checkpoint_bytes),
                state_transfer_bytes=int(
                    proposal.timing.state_transfer_bytes
                    + reconcile_meta.get("state_transfer_bytes", 0)
                ),
                draft_logical_state_length=draft_len,
                target_state_position=target_pos,
                fallback_events=list(reconcile_meta.get("fallback_events", [])),
                native_initial_target_only=False,
            )
        )

    finish_ns, finish_meta = draft.finish()
    timing.draft_finish_ns += int(finish_ns)
    end = _ns()
    timing.end_to_end_ns = end - start
    timing.reconcile_total()

    return {
        "tokens": out,
        "rounds": [asdict(x) for x in rounds],
        "timing": asdict(timing),
        "begin_metadata": begin_meta,
        "finish_metadata": finish_meta,
        "proposed": proposed_total,
        "accepted": accepted_total,
        "committed": sum(x.C for x in rounds),
        "target_state_position": target.state_position(),
        "draft_capabilities": asdict(draft.capabilities),
    }
