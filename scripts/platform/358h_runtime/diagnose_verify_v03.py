#!/usr/bin/env python3
"""Correctness-only playback and KV/rollback probes for HumanEval/48."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from diagnose_target_v03 import base_record, frozen_rows, task_prompt, top2, write_json
from runtime_target import LlamaAPI, RuntimeTargetPool
from runtime_types import accepted_prefix_length


def playback_one(target, prompt: list[int], frozen_rounds: list[dict]) -> dict:
    target.reset_prefill(prompt)
    rounds = []
    generated = []
    for row in frozen_rounds:
        before = len(target.history)
        if before != row["prefix_before"]:
            raise AssertionError(f"proposal playback prefix drift at round {row['round_id']}")
        pre = top2(target)
        proposals = list(row["proposals"])
        got = list(map(int, target.verify(proposals)))
        generated.extend(got)
        accepted = accepted_prefix_length(proposals, got)
        correction = (got[-1] if row["round_id"] == 0 else
                      got[-1] if proposals and accepted < len(proposals) else None)
        bonus = got[-1] if proposals and accepted == len(proposals) else None
        record = {"round_id": row["round_id"], "output_span": [len(generated)-len(got), len(generated)],
                  "prefix_before": before, "proposals": proposals,
                  "frozen_accepted": row["accepted"], "accepted": accepted,
                  "frozen_committed": row["committed"], "committed": got,
                  "correction": correction, "bonus": bonus, "C": len(got),
                  "target_state_position": target.state_position(),
                  "target_history": list(target.history),
                  "pre_next_token": pre["top1_token"], "pre_logits": pre,
                  "post_logits": top2(target),
                  "matches_frozen_round": (got == row["committed"] and accepted == row["accepted"]
                                           and correction == row["correction"] and bonus == row["bonus"]
                                           and len(got) == row["C"]
                                           and target.state_position() == row["target_state_position"])}
        rounds.append(record)
        if not record["matches_frozen_round"]:
            break  # Subsequent frozen proposals were conditioned on another prefix.
    return {"n_ubatch": target.ubatch, "generated_token_ids": generated,
            "all_rounds_match_frozen": len(rounds) == len(frozen_rounds)
                and all(r["matches_frozen_round"] for r in rounds),
            "first_mismatched_round": next((r["round_id"] for r in rounds if not r["matches_frozen_round"]), None),
            "rounds": rounds, "focused_rounds": [r for r in rounds if 36 <= r["round_id"] <= 43]}


def playback48() -> dict:
    record = base_record("playback48")
    frozen = frozen_rows(48)
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(48, pool[1])
    result = []
    for rep in range(3):
        source = frozen[(rep, "LEGACY_NPU_UB2")]
        for ub in (1, 2):
            row = playback_one(pool[ub], prompt, source["rounds"])
            row["repetition"] = rep
            row["exact_frozen_legacy_ub2"] = row["generated_token_ids"] == source["generated_token_ids"]
            row["source_proposal_rounds"] = len(source["rounds"])
            result.append(row)
    record.update({"prompt_token_count": len(prompt), "proposal_source": "frozen R1 LEGACY_NPU_UB2 rounds",
                   "draft_inference_executed": False, "runs": result,
                   "ub2_reproduced": all(r["exact_frozen_legacy_ub2"] and r["all_rounds_match_frozen"]
                                         for r in result if r["n_ubatch"] == 2)})
    return record


def divergent_round(source: dict, output_index: int) -> tuple[int, int, dict]:
    offset = 0
    for row in source["rounds"]:
        if offset <= output_index < offset + row["C"]:
            return row["round_id"], offset, row
        offset += row["C"]
    raise RuntimeError("frozen output index not covered by round ledger")


def micro48() -> dict:
    record = base_record("micro48")
    frozen = frozen_rows(48)
    source = frozen[(0, "LEGACY_NPU_UB2")]
    round_id, index, row = divergent_round(source, 100)
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    if source["generated_token_ids"][:index] != reference[:index]:
        raise AssertionError("frozen reference and speculative prefix differ before microtest")
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(48, pool[1])
    tests = []
    for ub in (1, 2):
        target = pool[ub]
        target.reset_prefill(prompt + reference[:index])
        pre = top2(target)
        got = list(map(int, target.verify(row["proposals"])))
        accepted = accepted_prefix_length(row["proposals"], got)
        tests.append({"n_ubatch": ub, "input_prefix_length": len(prompt)+index,
                      "proposal": row["proposals"], "pre_next_token": pre["top1_token"],
                      "pre_logits": pre, "committed": got, "accepted": accepted,
                      "correction": got[-1] if accepted < len(row["proposals"]) else None,
                      "bonus": got[-1] if accepted == len(row["proposals"]) else None,
                      "target_state_position": target.state_position(),
                      "target_history": list(target.history), "post_logits": top2(target)})
    record.update({"first_frozen_divergent_round": round_id, "output_index": index,
                   "frozen_round": row, "fresh_prefix": True, "tests": tests})
    return record


def stress48() -> dict:
    record = base_record("stress48")
    frozen = frozen_rows(48)
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(48, pool[1])
    patterns = [(0,), (1,), (2,), (0, 0), (0, 2), (2, 0), (1, 0, 2)]
    results = []
    for index in (96, 98, 100):
        for ub in (1, 2):
            target = pool[ub]
            prefix = prompt + reference[:index]
            target.reset_prefill(prefix)
            oracle = target.baseline(24)
            for pattern in patterns:
                target.reset_prefill(prefix)
                progress = 0
                rounds = []
                for accepted in pattern:
                    first, second = oracle[progress:progress+2]
                    wrong_first = (first + 1) % target.n_vocab
                    wrong_second = (second + 1) % target.n_vocab
                    proposal = ([wrong_first, wrong_second] if accepted == 0 else
                                [first, wrong_second] if accepted == 1 else [first, second])
                    got = list(map(int, target.verify(proposal)))
                    actual_accepted = accepted_prefix_length(proposal, got)
                    expected = oracle[progress:progress+accepted+1]
                    ok = (actual_accepted == accepted and got == expected
                          and target.state_position() == len(target.history)-1)
                    rounds.append({"forced_accepted": accepted, "actual_accepted": actual_accepted,
                                   "proposal": proposal, "committed": got, "oracle_committed": expected,
                                   "state_position": target.state_position(), "pass": ok})
                    progress += len(got)
                    if not ok:
                        break
                future = list(map(int, target.verify([]))) if all(r["pass"] for r in rounds) else []
                future_ok = future == oracle[progress:progress+1]
                results.append({"prefix_output_index": index, "n_ubatch": ub,
                                "pattern": list(pattern), "rounds": rounds,
                                "future_token": future, "oracle_future": oracle[progress:progress+1],
                                "future_exact": future_ok,
                                "pass": all(r["pass"] for r in rounds) and future_ok})
    record.update({"results": results, "all_pass": all(x["pass"] for x in results),
                   "tested_patterns": [list(x) for x in patterns]})
    return record


def bonus48() -> dict:
    """Isolate the all-accepted batch path just before output index 100."""
    record = base_record("bonus48")
    frozen = frozen_rows(48)
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    source_round = frozen[(0, "LEGACY_NPU_UB2")]["rounds"][39]
    if source_round["round_id"] != 39 or source_round["accepted"] != 2:
        raise AssertionError("frozen round 39 is not the expected full-accept branch")
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(48, pool[1])
    rows = []
    for ub in (1, 2):
        target = pool[ub]
        target.reset_prefill(prompt + reference[:97])
        pre = top2(target)
        committed = list(map(int, target.verify(source_round["proposals"])))
        post = top2(target)
        position_after_bonus = target.state_position()
        future = list(map(int, target.verify([])))
        rows.append({"n_ubatch": ub, "prefix_output_index": 97,
                     "proposals": source_round["proposals"],
                     "pre_logits": pre, "accepted": accepted_prefix_length(source_round["proposals"], committed),
                     "committed": committed, "post_bonus_logits": post,
                     "position_after_bonus": position_after_bonus,
                     "history_length_after_future": len(target.history),
                     "position_after_future": target.state_position(),
                     "future_token": future})
    record.update({"frozen_round_id": 39, "fresh_prefix": True,
                   "frozen_round_proposals": source_round["proposals"],
                   "rows": rows,
                   "reproduces_next_token_divergence":
                       [r["future_token"] for r in rows] == [[151668], [32313]]
                       and all(r["committed"] == source_round["committed"] for r in rows)})
    return record


def tail48(starts: tuple[int, ...]) -> dict:
    """Rebuild a fresh UB2 prefix, then replay progressively longer frozen tails."""
    record = base_record("tail48")
    frozen = frozen_rows(48)
    source = frozen[(0, "LEGACY_NPU_UB2")]
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(2,))
    target = pool[2]
    prompt = task_prompt(48, target)
    rows = []
    for start in starts:
        offset = sum(r["C"] for r in source["rounds"][:start])
        if source["generated_token_ids"][:offset] != reference[:offset]:
            raise AssertionError("frozen playback and reference differ before tail start")
        target.reset_prefill(prompt + reference[:offset])
        first_mismatch = None
        round39_post = None
        round40_pre = None
        last_committed = None
        for step in source["rounds"][start:41]:
            if len(target.history) != step["prefix_before"]:
                raise AssertionError("fresh tail prefix length drift")
            if step["round_id"] == 40:
                round40_pre = top2(target)
            got = list(map(int, target.verify(step["proposals"])))
            last_committed = got
            if step["round_id"] == 39:
                round39_post = top2(target)
            if got != step["committed"]:
                first_mismatch = step["round_id"]
                break
        rows.append({"start_round": start, "start_output_index": offset,
                     "first_mismatched_round": first_mismatch,
                     "round39_post_logits": round39_post,
                     "round40_pre_logits": round40_pre,
                     "last_committed": last_committed,
                     "round40_frozen_reproduced": first_mismatch is None})
    record.update({"n_ubatch": 2, "source": "frozen R1 LEGACY_NPU_UB2 repetition 0",
                   "start_rounds": list(starts),
                   "fresh_state_for_each_tail": True, "rows": rows})
    return record


def pivot48() -> dict:
    """Vary only the round-27 verification shape from an identical fresh prefix."""
    record = base_record("pivot48")
    frozen = frozen_rows(48)
    source = frozen[(0, "LEGACY_NPU_UB2")]
    reference = frozen[(0, "TARGET_UB1")]["generated_token_ids"]
    pivot = source["rounds"][27]
    offset = sum(r["C"] for r in source["rounds"][:27])
    if offset != 75 or pivot["accepted"] != 0 or pivot["committed"] != [151643]:
        raise AssertionError("unexpected frozen round-27 pivot")
    api = LlamaAPI()
    pool = RuntimeTargetPool(api, ubatches=(1, 2))
    prompt = task_prompt(48, pool[1])
    rows = []
    for ub in (1, 2):
        target = pool[ub]
        for shape, proposal in (("frozen_two_rejected", pivot["proposals"]),
                                ("one_rejected", pivot["proposals"][:1]),
                                ("target_only", [])):
            target.reset_prefill(prompt + reference[:offset])
            pre = top2(target)
            committed = list(map(int, target.verify(proposal)))
            after_pivot = top2(target)
            after_pivot_pos = target.state_position()
            if committed != pivot["committed"]:
                raise AssertionError("pivot variant changed committed token")
            first_mismatch = None
            round39_post = None
            round40_pre = None
            for step in source["rounds"][28:41]:
                if step["round_id"] == 40:
                    round40_pre = top2(target)
                got = list(map(int, target.verify(step["proposals"])))
                if step["round_id"] == 39:
                    round39_post = top2(target)
                if got != step["committed"]:
                    first_mismatch = step["round_id"]
                    break
            rows.append({"n_ubatch": ub, "pivot_shape": shape, "pivot_proposals": proposal,
                         "pivot_pre_logits": pre, "pivot_committed": committed,
                         "pivot_post_logits": after_pivot, "pivot_state_position": after_pivot_pos,
                         "round39_post_logits": round39_post,
                         "round40_pre_logits": round40_pre,
                         "first_mismatched_round_against_frozen_ub2": first_mismatch})
    record.update({"pivot_round": 27, "fresh_start_output_index": offset,
                   "one_variable": "round-27 verification shape", "rows": rows})
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["playback48", "micro48", "stress48", "bonus48", "tail48", "pivot48"], required=True)
    ap.add_argument("--tail-starts", default="39,38,36,32,24,16,0",
                    help="comma-separated fresh start rounds, used only for tail48")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = (tail48(tuple(int(x) for x in args.tail_starts.split(","))) if args.stage == "tail48" else
              {"playback48": playback48, "micro48": micro48,
               "stress48": stress48, "bonus48": bonus48, "pivot48": pivot48}[args.stage]())
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k in
                      ("stage", "ub2_reproduced", "all_pass", "reproduces_next_token_divergence")},
                     ensure_ascii=False))
    # Negative microtest/rollback controls are diagnostic observations, not harness failures.
    return 0 if args.stage != "playback48" or result["ub2_reproduced"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
