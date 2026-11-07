#!/usr/bin/env python3
"""Check scientific claims that must survive authorized v0.8.3 revisions."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[3]
MS = ROOT / "paper/mlsys2027/manuscript"
EVIDENCE = ROOT / "paper/mlsys2027/evidence"
TITLE = "Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems"


def read(relative):
    return (MS / relative).read_text(encoding="utf-8")


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS:", label)


def main():
    main_tex = read("main.tex")
    abstract = main_tex.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
    intro = read("sections/01_introduction.tex")
    diagnoses = read("sections/05_diagnoses.tex")
    synthesis = read("sections/06_synthesis.tex")
    runtime = read("sections/07_runtime_codesign.tex")
    related = read("sections/08_related_work.tex")
    limitations = read("sections/09_limitations.tex")
    conclusion = read("sections/10_conclusion.tex")
    figure4 = read("figures/04_358h.tex")

    # Phase-4 scientific meaning, independent of its historical edit perimeter.
    check(r"\mlsystitle{" + TITLE + "}" in main_tex, "official title")
    for phrase in ("tested B570 stack", "72/72", "complete generated-token-ID sequences",
                   "24 reserved prompts", "frozen before reserved live outcomes",
                   "reference-divergent trajectories", "target-partition sufficiency"):
        check(phrase in abstract, "abstract: " + phrase)
    check("without identifying a unique numerical cause" in abstract and
          not re.search(r"\b(?:establish(?:es|ed|ing)?|identif(?:y|ies|ied))\s+(?:a\s+)?(?:unique\s+)?(?:root cause|universal UB1 law|cross-backend mechanism)\b",
                        abstract, re.I), "abstract limits causal and cross-backend claims")
    contribution = re.search(r"Our three contributions are (.+?)\n\n", intro, re.S)
    check(bool(contribution) and all(f"({number})" in contribution.group(1) for number in (1, 2, 3))
          and "(4)" not in contribution.group(1), "exactly three headline contributions")
    contributions = contribution.group(1)
    check(contributions.index("fresh direct-ID execution-path qualification") <
          contributions.index("prospectively frozen B570 target-partition predictor") <
          contributions.index("realized 358H state-interface cost"),
          "contributions: qualification, prediction, realized cost")
    check(intro.index("Two prospectively frozen direct-ID studies") <
          intro.index("M4, RTX 5070 Ti Laptop") < intro.index("Our three contributions"),
          "first-page evidence order")
    check(r"\subsection{Controlled B570 target-partition sufficiency}" in diagnoses and
          "mechanism isolation" not in diagnoses.lower() and
          "on the tested B570 configuration" in diagnoses and
          "universal UB1 rule" in diagnoses and "or explain RTX behavior" in diagnoses,
          "B570 subsection retains tested-path sufficiency boundary")
    check("On the tested B570 stack" in synthesis and
          "On the tested B570 stack" in conclusion and
          "72/72 predictor-to-live complete-ID agreement" in conclusion and
          "target-partition sufficiency without a unique numerical cause" in conclusion,
          "conclusion retains sufficient tested path, not unique cause")
    check("one B570 platform, model pair, runtime/build, greedy $k=2$, HumanEval workload, and 24 reserved prompts"
          in limitations, "B570 scope retained in limitations")
    print("Phase 4 current scientific invariants: PASS")

    # Phase-5 boundaries; its own validator separately checks frozen sources.
    for phrase in ("Slowdown and correctness gating are therefore established background",
                   "Numerical path dependence is not new here",
                   "Adaptive control is established prior work"):
        check(phrase in related, "Related Work acknowledges prior art: " + phrase)
    check(not re.search(r"\b(?:first-ever|first to|first-of-its-kind|novelty)\b", related, re.I),
          "Related Work has no firstness claim")
    check("Guard reaches \\RTGuard$\\times$ post-prefill speedup over target-only" in abstract and
          "slower than fixed speculation" in abstract and
          "no incremental control benefit is shown" in abstract and
          "Guard is profitable against target-only" in runtime and
          "post-study paired secondary analysis" in runtime and
          "Guard had higher latency on this comparison" in runtime and
          "post-study paired secondary comparison favors fixed speculation" in conclusion,
          "M4 Guard target-only profitability and adverse paired secondary result")
    check("full committed-prefix replay/reconstruction and proposal" in diagnoses and
          "inseparable in the recorded timing" in diagnoses and
          "replay-plus-proposal call" in figure4 and
          "replay-only time is not measured" in figure4 and
          not re.search(r"(?:replay-only|replay alone|replay penalty)[^.]{0,50}58\.35|"
                        r"58\.35[^.]{0,50}(?:replay-only|replay alone|replay penalty)",
                        diagnoses + runtime + figure4, re.I),
          "358H combined call is inseparable; no replay-only share")
    check("No formal R2 performance run occurred" in runtime and
          "invalid for performance claims" in runtime and
          "later intervention stops at qualification" in conclusion,
          "358H later intervention has no performance endpoint")
    print("Phase 5 current scientific invariants: PASS")

    # Cross-phase evidence labels. Detailed source audits remain in Phase 1-3 validators.
    framework = read("sections/02_framework.tex").lower()
    headline = read("tables/02_headlines_v05.tex")
    direct = read("tables/08_direct_id.tex")
    values = read("tables/direct_id_values.tex")
    appendix = read("appendix.tex")
    check("historical text-path agreement" in framework and
          "Historical text-path" in read("tables/06_verification_lookup_v05.tex") and
          "Text-path" in headline, "historical evidence remains text-path agreement")
    check("Fresh direct-ID qualification" in direct and
          all(value in values for value in (r"\DIRTXBatchedPairs}{75}", r"\DIRTXSerializedPairs}{90}",
                                             r"\DIBFastPairs}{60}", r"\DIBSerializedPairs}{78}")),
          "fresh RTX/B570 qualification remains direct-ID")
    check("Predictor-to-live complete-ID agreement is 72/72" in diagnoses and
          "72/72 predictor-to-live complete-ID agreement" in appendix,
          "B570 predictor/live remains 72/72")
    check("Reference-to-live direct-ID qualification is 60/72" in diagnoses and
          "BLOCKED" in diagnoses and
          "Reference-to-live direct-ID qualification is 60/72 and BLOCKED" in appendix,
          "B570 reference/live remains 60/72 BLOCKED")
    check(r"\input{tables/b570_prediction_commitment_v083.tex}" in appendix and
          (EVIDENCE / "B570_PREDICTION_COMMITMENT_LEDGER_V083.json").is_file() and
          r"\mlsysauthor{Anonymous Authors}{anon}" in main_tex,
          "Phase-2 anonymous ledger remains integrated")
    print("Earlier evidence-class and B570 ledger invariants: PASS")
    print("CURRENT SCIENTIFIC INVARIANTS: PASS")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError) as error:
        print("FAIL:", error, file=sys.stderr)
        sys.exit(1)
