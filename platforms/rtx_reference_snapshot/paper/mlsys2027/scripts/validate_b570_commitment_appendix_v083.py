#!/usr/bin/env python3
"""Independently compare displayed appendix values with Phase-1 ledger data."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "paper/mlsys2027/evidence/B570_PREDICTION_COMMITMENT_LEDGER_V083.json"
TABLE = ROOT / "paper/mlsys2027/manuscript/tables/b570_prediction_commitment_v083.tex"
APPENDIX = ROOT / "paper/mlsys2027/manuscript/appendix.tex"


def verify(condition, label):
    if not condition:
        raise AssertionError(label)


def duration(later, earlier):
    parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parse(later) - parse(earlier)).total_seconds()


def main():
    ledger = json.loads(LEDGER.read_text())
    latex = TABLE.read_text()
    appendix = APPENDIX.read_text()
    verify(latex.startswith("% AUTO-GENERATED FROM VERIFIED PHASE-1 LEDGER.\n% DO NOT EDIT RESULT VALUES BY HAND."), "generator markers")
    verify(appendix.count(r"\input{tables/b570_prediction_commitment_v083.tex}") == 1, "appendix integration")
    counts = ledger["aggregate_checks"]
    verify((counts["reserved_prompt_count"], counts["repetition_count_per_prompt"], counts["prediction_count"],
            counts["predictor_live_exact_pairs"], counts["reference_live_exact_pairs"],
            counts["prompt_classification_matches"], counts["divergent_pair_first_index_matches"],
            counts["divergent_pair_count"], counts["divergent_prompt_count"]) ==
           (24, 3, 72, 72, 60, 24, 12, 12, 4), "Phase-1 critical claims")
    verify(len(ledger["per_run_records"]) == 72 and len(ledger["per_prompt_summary"]) == 24, "source record counts")
    digest = ledger["commitment"]["prediction_file_sha256"]
    verify(digest[:32] in latex and digest[32:] in latex and
           latex.index(digest[:32]) < latex.index(digest[32:]), "full prediction content digest")
    verify("digest identifies the frozen contents" in latex and "rather than from the digest alone" in latex, "digest interpretation")
    verify("prompt IDs are excluded" in latex and "At most 128 committed generated IDs" in latex and
           "earlier terminal end-of-generation (EOG) ID" in latex and "No mismatch is discarded" in latex and
           "complete sequences" in latex and "zero-based" in latex, "endpoint display")
    summary_pattern = re.compile(r"^Frozen (UB128/reference trajectory|UB1 target-only predictor) & (\d+)/(\d+) \\\\$", re.M)
    summary = dict((label, (int(n), int(d))) for label, n, d in summary_pattern.findall(latex))
    verify(summary == {"UB128/reference trajectory": (60, 72), "UB1 target-only predictor": (72, 72)}, "summary table")
    verify("primary mechanism-validation endpoint" in latex and "already-observed comparison" in latex and
           "60/72 reference result remains BLOCKED" in latex, "comparison caption")
    anchor = latex.index(r"\label{tab:b570-commitment-ledger}")
    full_table = latex[anchor:latex.index(r"\end{table*}", anchor)]
    row_pattern = re.compile(r"^HE/(\d+) & ([\d/]+) & (\d+)/3 & (\d+)/3 & \\texttt\{([0-9a-f]+)\} & (.+) \\\\$", re.M)
    rows = row_pattern.findall(full_table)
    verify(len(rows) == 24, "exactly 24 displayed prompt rows")
    source = ledger["per_prompt_summary"]
    verify(len(set(task for task, *_ in rows)) == 24, "duplicate displayed task")
    prefixes = []
    for displayed, record in zip(rows, source):
        number, length, pred_exact, ref_exact, prefix, divergence = displayed
        verify("HumanEval/" + number == record["task_id"], "task identity/order")
        lengths = [record[f"sequence_length_r{i}"] for i in (1, 2, 3)]
        expected_length = str(lengths[0]) if len(set(lengths)) == 1 else "/".join(str(n) for n in lengths)
        verify(length == expected_length, "displayed sequence length")
        verify(int(pred_exact) == record["predictor_live_exact_count"] and
               int(ref_exact) == record["reference_live_exact_count"], "displayed equality counts")
        verify(record["repeat_stable_predictor"] and record["repeat_stable_live"], "repeat stability")
        prediction_hashes = {record[f"predicted_hash_r{i}"] for i in (1, 2, 3)}
        live_hashes = {record[f"live_hash_r{i}"] for i in (1, 2, 3)}
        verify(len(prediction_hashes) == len(live_hashes) == 1 and prediction_hashes == live_hashes, "shared digest validity")
        complete_hash = next(iter(prediction_hashes))
        verify(len(complete_hash) == 64 and complete_hash.startswith(prefix), "displayed digest mapping")
        prefixes.append(prefix)
        expected_divergence = "--" if record["first_divergence_index"] is None else (
            f"{record['first_divergence_index']}: {record['reference_token']} $\\rightarrow$ {record['live_token']}")
        verify(divergence == expected_divergence, "displayed divergence")
    verify(len(set(prefixes)) == 24, "digest-prefix collision")
    verify(len({len(prefix) for prefix in prefixes}) == 1 and len(prefixes[0]) in (12, 16), "digest-prefix width")
    expected_width = 12 if len({r["predicted_hash_r1"][:12] for r in source}) == 24 else 16
    verify(len(prefixes[0]) == expected_width, "digest-prefix fallback")
    verify(f"first {expected_width} hex characters" in latex, "digest caption width")
    divergent = [r for r in source if r["reference_live_exact_count"] == 0]
    mini = latex[latex.index(r"\textbf{Informative reference-divergent prompts."):latex.index(r"\begin{table*}[t]")]
    mini_pattern = re.compile(r"^HE/(\d+) & (\d+) & (\d+) \$\\rightarrow\$ (\d+) & (\d+)/3 \\\\$", re.M)
    mini_rows = mini_pattern.findall(mini)
    verify(len(mini_rows) == len(divergent) == 4, "divergent block count")
    for shown, record in zip(mini_rows, divergent):
        verify(shown == (record["task_id"].split("/")[1], str(record["first_divergence_index"]),
                         str(record["reference_token"]), str(record["live_token"]),
                         str(record["predictor_live_exact_count"])), "divergent block values")
    verify("12/12 repetition pairs" in mini and "reference-divergent but predictor/live-identical" in mini, "informative case interpretation")
    chronology = {row["event"]: row["recorded_utc"] for row in ledger["chronology"]}
    t0 = chronology["H1 hypothesis freeze"]
    prediction = chronology["prediction file completed"]
    live = chronology["first live serialized outcome"]
    timeline = re.findall(r"^(72 prediction arrays finalized|First live reserved outcome) & \$T_0 \+ ([0-9]+\.[0-9]{2})\\,\\mathrm\{s\}\$ \\\\$", latex, re.M)
    verify(len(timeline) == 2 and timeline[0][0] == "72 prediction arrays finalized" and timeline[1][0] == "First live reserved outcome", "timeline rows")
    verify(timeline[0][1] == f"{duration(prediction, t0):.2f}" and
           timeline[1][1] == f"{duration(live, t0):.2f}", "relative chronology arithmetic")
    verify(f"{duration(live, prediction):.2f}\\,s interval" in latex, "prediction-to-live lead")
    verify("independently timestamped" not in latex.lower() and "push" not in latex.lower(), "push claim")
    prohibited = ["leecdiang", "github.com", "/Users/", "Projects/HeteroSpec", "paper/mlsys",
                  "paper/mlsys2027-reviewer-convergence-v0.8.3", "machine hostname",
                  ledger["commitment"]["hypothesis_freeze_commit"], ledger["commitment"]["prediction_freeze_commit"]]
    for term in prohibited:
        verify(term.lower() not in latex.lower() and term.lower() not in appendix.lower(), "identifying text: " + term)
    print("PASS: 24 rows, source values, digests, chronology, comparison, endpoint and anonymity")


if __name__ == "__main__":
    main()
