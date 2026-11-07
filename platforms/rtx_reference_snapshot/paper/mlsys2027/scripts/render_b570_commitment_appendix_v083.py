#!/usr/bin/env python3
"""Render anonymous appendix evidence from the verified Phase-1 ledger."""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "paper/mlsys2027/evidence/B570_PREDICTION_COMMITMENT_LEDGER_V083.json"
OUTPUT = ROOT / "paper/mlsys2027/manuscript/tables/b570_prediction_commitment_v083.tex"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def short_task(task):
    require(task.startswith("HumanEval/") and task.removeprefix("HumanEval/").isdigit(), "Unexpected task ID")
    return "HE/" + task.split("/")[1]


def seconds_after(later, earlier):
    return (datetime.fromisoformat(later.replace("Z", "+00:00")) -
            datetime.fromisoformat(earlier.replace("Z", "+00:00"))).total_seconds()


def main():
    data = json.loads(LEDGER.read_text())
    check = data["aggregate_checks"]
    require(data["schema_version"] == "heterospec.b570.prediction_commitment_ledger.v083", "Wrong source schema")
    require((check["reserved_prompt_count"], check["repetition_count_per_prompt"], check["prediction_count"],
             check["predictor_live_exact_pairs"], check["reference_live_exact_pairs"],
             check["prompt_classification_matches"], check["divergent_pair_first_index_matches"],
             check["divergent_pair_count"], check["divergent_prompt_count"]) ==
            (24, 3, 72, 72, 60, 24, 12, 12, 4), "Phase-1 aggregate changed")
    endpoint = data["endpoint"]
    require(endpoint["committed_id_cap"] == 128 and endpoint["first_divergence_index_base"] == 0
            and "prompt IDs excluded" in endpoint["array"] and "EOG" in endpoint["eog"]
            and "complete sequence equality" in endpoint["comparison"], "Endpoint changed")
    prompts = data["per_prompt_summary"]
    require(len(prompts) == 24 and [p["task_id"] for p in prompts] == data["reserved_prompt_ids"], "Prompt set changed")
    for p in prompts:
        require(p["repeat_stable_predictor"] and p["repeat_stable_live"], "Cannot compress unstable repetitions")
        require(len({p[f"predicted_hash_r{i}"] for i in (1, 2, 3)}) == 1, "Predictor digest instability")
        require(len({p[f"live_hash_r{i}"] for i in (1, 2, 3)}) == 1, "Live digest instability")
        require(p["predicted_hash_r1"] == p["live_hash_r1"], "Unexpected predictor/live mismatch")
    hashes = [p["predicted_hash_r1"] for p in prompts]
    prefix_length = next((n for n in (12, 16) if len({h[:n] for h in hashes}) == len(hashes)), None)
    require(prefix_length is not None, "Digest collision persists at 16 hex characters")
    chronology = {item["event"]: item["recorded_utc"] for item in data["chronology"]}
    t0 = chronology["H1 hypothesis freeze"]
    completed = chronology["prediction file completed"]
    first_live = chronology["first live serialized outcome"]
    dt_completed, dt_live = seconds_after(completed, t0), seconds_after(first_live, t0)
    lead = seconds_after(first_live, completed)
    require(0 < dt_completed < dt_live and 90 < lead < 93, "Chronology changed")
    digest = data["commitment"]["prediction_file_sha256"]
    require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), "Content digest malformed")
    divergent = [p for p in prompts if p["reference_live_exact_count"] != 3]
    require(len(divergent) == 4 and all(p["reference_live_exact_count"] == 0 for p in divergent), "Divergent prompt classification changed")
    lines = [
        "% AUTO-GENERATED FROM VERIFIED PHASE-1 LEDGER.",
        "% DO NOT EDIT RESULT VALUES BY HAND.",
        r"The comparison uses complete generated-token-ID arrays; prompt IDs are excluded.",
        f"At most {endpoint['committed_id_cap']} committed generated IDs are compared, including an earlier terminal end-of-generation (EOG) ID when it ends generation.",
        r"No mismatch is discarded. Equality requires the complete sequences, including lengths, to match; first-divergence indices are zero-based.",
        "",
        f"\\noindent\\textbf{{Content identity.}} The {check['prediction_count']} frozen complete prediction arrays are bound to the following prediction-file content digest (SHA-256; two consecutive 32-character lines):",
        r"\begin{center}\small\texttt{" + digest[:32] + r"}\\\texttt{" + digest[32:] + r"}\end{center}",
        r"The digest identifies the frozen contents; the temporal ordering below comes from the recorded study chronology rather than from the digest alone.",
        "",
        r"\begin{center}",
        r"\small",
        r"\begin{tabular}{@{}ll@{}}",
        r"\toprule",
        r"Recorded event & Time relative to H1 freeze \\",
        r"\midrule",
        r"H1 freeze & $T_0$ \\",
        f"{check['prediction_count']} prediction arrays finalized & $T_0 + {dt_completed:.2f}\\,\\mathrm{{s}}$ " + r"\\",
        f"First live reserved outcome & $T_0 + {dt_live:.2f}\\,\\mathrm{{s}}$ " + r"\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{center}",
        f"The recorded study chronology fixes the prediction file before the first live serialized reserved outcome, with a {lead:.2f}\\,s interval between prediction completion and live start. Identifying repository metadata are omitted for double-blind review.",
        "",
        r"\begin{table}[t]",
        f"\\caption{{Reference trajectory agreement versus frozen UB1 predictor agreement on the same {check['reserved_prompt_count']} reserved prompts $\\times$ {check['repetition_count_per_prompt']} repetitions. Predictor/live complete-sequence equality is the primary mechanism-validation endpoint; reference/live equality is an already-observed comparison. The {check['reference_live_exact_pairs']}/{check['prediction_count']} reference result remains BLOCKED under its qualification contract.}}",
        r"\label{tab:b570-commitment-summary}",
        r"\centering\small",
        r"\begin{tabular}{@{}lr@{}}",
        r"\toprule",
        r"Comparator to live serialized output & Complete equality \\",
        r"\midrule",
        f"Frozen UB128/reference trajectory & {check['reference_live_exact_pairs']}/{check['prediction_count']} " + r"\\",
        f"Frozen UB1 target-only predictor & {check['predictor_live_exact_pairs']}/{check['prediction_count']} " + r"\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
        r"\noindent\textbf{Informative reference-divergent prompts.} These cases are reference-divergent but predictor/live-identical."
    ]
    lines.extend([
        r"\begin{center}\small",
        r"\begin{tabular}{@{}lrrr@{}}",
        r"\toprule",
        r"Task & First index & Ref $\rightarrow$ Pred/Live ID & Pred=Live \\",
        r"\midrule",
    ])
    for p in divergent:
        lines.append(f"{short_task(p['task_id'])} & {p['first_divergence_index']} & {p['reference_token']} $\\rightarrow$ {p['live_token']} & {p['predictor_live_exact_count']}/{check['repetition_count_per_prompt']} " + r"\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{center}",
        f"Across these {len(divergent)} prompts, the predicted and observed first-divergence positions agree in {check['divergent_pair_first_index_matches']}/{check['divergent_pair_count']} repetition pairs.",
        "",
        r"\begin{table*}[t]",
        f"\\caption{{Reviewer-visible B570 reserved commitment ledger. All {check['reserved_prompt_count']} prompts have {check['repetition_count_per_prompt']} repetitions. Pred=Live and Ref=Live count complete generated-ID sequence equality. The displayed digest is the first {prefix_length} hex characters of the complete SHA-256 and is shared across the {check['repetition_count_per_prompt']} repeat-stable predictor/live repetitions for each prompt; complete hashes remain in the verified ledger. The first reference-to-live divergence index is zero-based; -- denotes reference equality.}}",
        r"\label{tab:b570-commitment-ledger}",
        r"\centering\small",
        r"\begin{tabular}{@{}lccccr@{}}",
        r"\toprule",
        r"Task & Live len & Pred=Live & Ref=Live & Pred/Live digest & Ref $\rightarrow$ Live first divergence \\",
        r"\midrule",
    ])
    for p in prompts:
        lengths = [p[f"sequence_length_r{i}"] for i in (1, 2, 3)]
        length_display = str(lengths[0]) if len(set(lengths)) == 1 else "/".join(map(str, lengths))
        divergence = "--" if p["first_divergence_index"] is None else f"{p['first_divergence_index']}: {p['reference_token']} $\\rightarrow$ {p['live_token']}"
        lines.append(f"{short_task(p['task_id'])} & {length_display} & {p['predictor_live_exact_count']}/{check['repetition_count_per_prompt']} & {p['reference_live_exact_count']}/{check['repetition_count_per_prompt']} & \\texttt{{{p['predicted_hash_r1'][:prefix_length]}}} & {divergence} " + r"\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines))
    print(f"PASS: {len(prompts)} rows; digest prefix {prefix_length} hex; lead {lead:.2f} s; {OUTPUT}")


if __name__ == "__main__":
    main()
