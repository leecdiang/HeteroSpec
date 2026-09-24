#!/usr/bin/env python3
"""Distill local v0.3 correctness evidence without performance measurements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/358h/runtime_codesign_v03_diagnostics_20260924"
OUT = ROOT / "benchmarks/358h_runtime/runtime_diagnostic_v0_3_evidence.json"
R1 = ROOT / "runs/358h/runtime_codesign_v02_qualification_20260923/r1_full_npu_legacy_target_20260924/observations.resolved.json"
NAMES = (
    "target54_reproduction", "target54_trace", "target54_fresh_prefix",
    "target54_order", "target54_isolated_ub1", "target54_isolated_ub2",
    "verify48_playback_corrected", "verify48_fresh_micro", "verify48_rollback_stress",
    "verify48_bonus_isolation", "verify48_fresh_tail_scan", "verify48_fresh_tail_refine",
    "verify48_round27_pivot",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> dict:
    return json.loads((RUN / f"{name}.json").read_text(encoding="utf-8"))


def main() -> None:
    data = {name: load(name) for name in NAMES}
    a54 = data["target54_reproduction"]
    p54 = data["target54_fresh_prefix"]
    playback = data["verify48_playback_corrected"]
    stress = data["verify48_rollback_stress"]
    fresh26 = {r["n_ubatch"]: r["next_token"] for r in p54["rows"] if r["output_index"] == 26}
    pivots = data["verify48_round27_pivot"]["rows"]
    tail_rows = data["verify48_fresh_tail_refine"]["rows"]
    if not (a54["pass"] and fresh26 == {1: 73594, 2: 151645}
            and data["target54_order"]["order_independent"]
            and data["target54_isolated_ub1"]["pass"]
            and data["target54_isolated_ub2"]["pass"]
            and playback["ub2_reproduced"]
            and all(r["first_mismatched_round"] == 40 for r in playback["runs"] if r["n_ubatch"] == 1)
            and len(stress["results"]) == 42 and sum(r["pass"] for r in stress["results"]) == 40
            and all(r["first_mismatched_round_against_frozen_ub2"] is None
                    for r in pivots if r["n_ubatch"] == 2)
            and next(r for r in tail_rows if r["start_round"] == 27)["first_mismatched_round"] is None
            and next(r for r in tail_rows if r["start_round"] == 28)["first_mismatched_round"] == 40):
        raise RuntimeError("raw diagnostic evidence changed or no longer supports frozen verdict")
    rows = []
    for run in playback["runs"]:
        r39 = run["rounds"][39]
        r40 = run["rounds"][40]
        rows.append({"repetition": run["repetition"], "n_ubatch": run["n_ubatch"],
                     "matches_frozen_legacy_ub2": run["exact_frozen_legacy_ub2"],
                     "first_mismatched_round": run["first_mismatched_round"],
                     "rounds_0_to_39_match_frozen": all(r["matches_frozen_round"] for r in run["rounds"][:40]),
                     "round39": {"output_span": r39["output_span"], "proposals": r39["proposals"],
                                 "accepted": r39["accepted"], "committed": r39["committed"],
                                 "state_position": r39["target_state_position"],
                                 "post_logits": r39["post_logits"]},
                     "round40": {"output_span": r40["output_span"], "proposals": r40["proposals"],
                                 "accepted": r40["accepted"], "committed": r40["committed"],
                                 "state_position": r40["target_state_position"],
                                 "pre_logits": r40["pre_logits"]}})
    out = {
        "schema": "heterospec.358h.runtime.v0.3.correctness_evidence",
        "status": "CORRECTNESS_ONLY_ROOT_CAUSE_DIAGNOSTICS",
        "claim_status": "DIAGNOSTIC / INVALID_FOR_PERFORMANCE_CLAIMS",
        "source_parent": "503c98f4511a4909f9e433d88e821c442634addc",
        "frozen_r1_sha256": digest(R1),
        "local_raw_evidence_sha256": {f"{name}.json": digest(RUN / f"{name}.json") for name in NAMES},
        "target54": {
            "reproduction_pass": a54["pass"],
            "ub1_repeat_exact": a54["ub1_repeat_exact"],
            "ub2_repeat_exact": a54["ub2_repeat_exact"],
            "first_divergence_index": a54["first_divergence_index"],
            "first_divergence_tokens": a54["first_divergence_tokens"],
            "fresh_prefix_rows": [r for r in p54["rows"] if r["output_index"] in (22, 23, 24, 25, 26, 27)],
            "order_independent": data["target54_order"]["order_independent"],
            "ub1_isolated_pass": data["target54_isolated_ub1"]["pass"],
            "ub2_isolated_pass": data["target54_isolated_ub2"]["pass"],
            "classification": "UBATCH_NUMERICAL_PATH_DIVERGENCE",
        },
        "verify48": {
            "ub2_proposal_playback_reproduced": playback["ub2_reproduced"],
            "draft_inference_executed": playback["draft_inference_executed"],
            "runs": rows,
            "fresh_index100_microtest": [
                {k: r[k] for k in ("n_ubatch", "proposal", "pre_logits", "committed",
                                   "accepted", "target_state_position")}
                for r in data["verify48_fresh_micro"]["tests"]],
            "stress_total": len(stress["results"]),
            "stress_pass": sum(r["pass"] for r in stress["results"]),
            "stress_failures": [
                {k: r[k] for k in ("prefix_output_index", "n_ubatch", "pattern", "rounds")}
                for r in stress["results"] if not r["pass"]],
            "fresh_round39_bonus_isolation": data["verify48_bonus_isolation"]["rows"],
            "tail_scan": [
                {"start_round": r["start_round"], "start_output_index": r["start_output_index"],
                 "first_mismatched_round": r["first_mismatched_round"],
                 "round39_post_top1": None if r["round39_post_logits"] is None else r["round39_post_logits"]["top1_token"]}
                for r in data["verify48_fresh_tail_scan"]["rows"]],
            "tail_refine": [
                {"start_round": r["start_round"], "start_output_index": r["start_output_index"],
                 "first_mismatched_round": r["first_mismatched_round"],
                 "round39_post_top1": None if r["round39_post_logits"] is None else r["round39_post_logits"]["top1_token"]}
                for r in data["verify48_fresh_tail_refine"]["rows"]],
            "round27_shape_control": [
                {k: r[k] for k in ("n_ubatch", "pivot_shape", "pivot_committed",
                                   "pivot_post_logits", "first_mismatched_round_against_frozen_ub2")}
                | {"round39_post_top1": r["round39_post_logits"]["top1_token"]}
                for r in data["verify48_round27_pivot"]["rows"]],
            "classification": "HISTORY_DEPENDENT_TARGET_NUMERICAL_PATH_DIVERGENCE; NO ROLLBACK BOUNDARY BUG PROVEN",
        },
        "correctness_bug_identified": False,
        "target_verification_semantics_changed": False,
        "scientific_verdict": "UB2_INTRINSICALLY_BLOCKED_IN_TESTED_STACK",
        "v0_2_r2_executed": False,
        "formal_performance_data_exist": False,
    }
    OUT.write_bytes((json.dumps(out, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(OUT)


if __name__ == "__main__":
    main()
