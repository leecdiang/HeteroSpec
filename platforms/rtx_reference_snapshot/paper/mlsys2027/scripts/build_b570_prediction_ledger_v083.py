#!/usr/bin/env python3
"""Reconstruct the B570 commitment ledger from immutable, existing records."""
import csv
import hashlib
import io
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "benchmarks/b570_mechanism_v08"
OUT = ROOT / "paper/mlsys2027/evidence"
RAW_P = "artifacts/b570_mechanism_v08/raw/reserved_predictions"
RAW_L = "artifacts/b570_mechanism_v08/raw/reserved_outcomes"


def fail_unless(test, message):
    if not test:
        raise RuntimeError(message)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def raw(rel):
    path = ROOT / rel
    return path.read_bytes() if path.exists() else git("show", "HEAD:" + rel)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def array_sha(ids):
    return sha(json.dumps(ids, separators=(",", ":")).encode())


def load(rel, sources):
    content = raw(rel)
    sources[rel] = sha(content)
    return json.loads(content)


def utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def stamp(value):
    return utc(value).isoformat().replace("+00:00", "Z") if value else "UNKNOWN"


def comparison(a, b):
    index = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    if index is None and len(a) != len(b):
        index = min(len(a), len(b))
    return index, (a[index] if index is not None and index < len(a) else None), (b[index] if index is not None and index < len(b) else None)


def commit_time(commit):
    return git("show", "-s", "--format=%cI", commit).decode().strip()


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def main():
    sources = {}
    names = ["HYPOTHESIS_FREEZE.md", "PREDICTION_FREEZE.md", "RESERVED_PREDICTIONS_SHA256.txt",
             "hypothesis_freeze.json", "RESERVED_PREDICTIONS.json", "RESERVED_VALIDATION_SET.json",
             "VALIDATION_ANALYSIS.json", "VALIDATION_REPORT.md", "DISCOVERY_ANALYSIS.json",
             "exposure_inventory.json", "INDEPENDENT_VALIDATION.json", "POST_RUN_INPUT_AUDIT.json",
             "PREDICTION_RAW_MANIFEST.json", "OUTCOME_RAW_MANIFEST.json"]
    docs = {n: load("benchmarks/b570_mechanism_v08/" + n, sources) if n.endswith(".json")
            else raw("benchmarks/b570_mechanism_v08/" + n) for n in names}
    for n in names:
        rel = "benchmarks/b570_mechanism_v08/" + n
        sources.setdefault(rel, sha(raw(rel)))
    for rel in ("scripts/platform/b570_mechanism_v08/study.py", "scripts/platform/b570_direct_id_v1/common.py"):
        sources[rel] = sha(raw(rel))
    prediction_bytes = raw("benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json")
    prediction_sha = sha(prediction_bytes)
    freeze_digest = docs["RESERVED_PREDICTIONS_SHA256.txt"].decode().split()[0]
    fail_unless(prediction_sha == freeze_digest and prediction_sha.encode() in docs["PREDICTION_FREEZE.md"], "Prediction digest differs from freeze")
    hypothesis = docs["hypothesis_freeze.json"]
    predictions = docs["RESERVED_PREDICTIONS.json"]
    reserved = docs["RESERVED_VALIDATION_SET.json"]
    validation = docs["VALIDATION_ANALYSIS.json"]
    discovery = docs["DISCOVERY_ANALYSIS.json"]
    exposure = docs["exposure_inventory.json"]
    fail_unless(docs["INDEPENDENT_VALIDATION.json"]["status"] == "PASS", "Canonical independent validation did not pass")
    h_commit = predictions["hypothesis_freeze_commit"]
    p_commit = next(s for s in docs["PREDICTION_FREEZE.md"].decode().split() if len(s) == 40 and all(c in "0123456789abcdef" for c in s))
    fail_unless(sha(raw("benchmarks/b570_mechanism_v08/hypothesis_freeze.json")) == predictions["hypothesis_sha256"], "Hypothesis content digest mismatch")
    fail_unless(git("show", p_commit + ":benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json") == prediction_bytes, "Prediction commit contains different bytes")
    fail_unless(git("show", h_commit + ":benchmarks/b570_mechanism_v08/hypothesis_freeze.json") == raw("benchmarks/b570_mechanism_v08/hypothesis_freeze.json"), "Hypothesis commit contains different bytes")
    fail_unless(subprocess.run(["git", "merge-base", "--is-ancestor", h_commit, p_commit], cwd=ROOT).returncode == 0, "Freeze commits out of order")
    for rel, manifest in [(RAW_P + "/executions.json", "PREDICTION_RAW_MANIFEST.json"), (RAW_L + "/executions.json", "OUTCOME_RAW_MANIFEST.json")]:
        fail_unless(docs[manifest]["files"][rel] == sha(raw(rel)), "Raw manifest mismatch: " + rel)
    pred_raw = load(RAW_P + "/executions.json", sources)["executions"]
    live_raw = load(RAW_L + "/executions.json", sources)["executions"]
    pred_checkpoint = load(RAW_P + "/checkpoint.json", sources)
    live_checkpoint = load(RAW_L + "/checkpoint.json", sources)
    task_ids = reserved["selected_task_ids"]
    fail_unless(len(task_ids) == len(set(task_ids)) == reserved["count"] == len(hypothesis["reserved_task_ids"]) == 24, "Reserved set mismatch")
    fail_unless(task_ids == hypothesis["reserved_task_ids"] and not exposure["errors"], "Selection/exposure audit mismatch")
    fail_unless(all(exposure["tasks"][t]["status"] == "NO_KNOWN_B570_EXPOSURE" for t in task_ids), "Known exposure in reserved set")
    fail_unless(hypothesis["status"] == "H1_SELECTED" and hypothesis["prediction_algorithm"].find("n_ubatch=1") >= 0, "H1 identity mismatch")
    fail_unless(len(discovery["pairs"]) == 36 and all(p["exact"] and p["execution_valid"] for p in discovery["pairs"]), "Discovery is not 36/36")
    fail_unless(utc(discovery["finished_utc"]) < utc(hypothesis["created_utc"]), "Discovery/freeze order mismatch")
    fail_unless(hypothesis["output_cap"] == 128 and hypothesis["eog"].startswith("inclusive first runtime EOG"), "Endpoint mismatch")
    fail_unless(predictions["actual_serialized_outcomes_observed"] is False and predictions["repeat_stable"], "Prediction freeze status mismatch")
    fail_unless(len(predictions["predictions"]) == len(live_raw) == 72 and len(pred_raw) == 144, "Raw coverage mismatch")
    fail_unless(live_checkpoint["prediction_sha256"] == prediction_sha and live_checkpoint["prediction_commit"] == p_commit, "Live checkpoint mismatch")
    fail_unless(pred_checkpoint["hypothesis_sha256"] == predictions["hypothesis_sha256"], "Predictor checkpoint mismatch")
    first_pred = min(utc(r["start_utc"]) for r in pred_raw)
    last_pred = max(utc(r["end_utc"]) for r in pred_raw)
    first_live = min(utc(r["start_utc"]) for r in live_raw)
    order = [utc(hypothesis["created_utc"]), utc(pred_checkpoint["start_utc"]), first_pred,
             last_pred, utc(predictions["created_utc"]), utc(commit_time(p_commit)),
             utc(live_checkpoint["start_utc"]), first_live]
    fail_unless(order == sorted(order) and utc(commit_time(h_commit)) < first_pred, "Recorded chronology is inconsistent")
    chronology = [
        {"event": "discovery completed", "recorded_utc": stamp(discovery["finished_utc"]), "source": "DISCOVERY_ANALYSIS.json:finished_utc"},
        {"event": "H1 hypothesis freeze", "recorded_utc": stamp(hypothesis["created_utc"]), "source": "hypothesis_freeze.json:created_utc"},
        {"event": "H1 freeze Git commit", "recorded_utc": stamp(commit_time(h_commit)), "source": "Git committer date (repository metadata)"},
        {"event": "reserved inference checkpoint", "recorded_utc": stamp(pred_checkpoint["start_utc"]), "source": RAW_P + "/checkpoint.json:start_utc"},
        {"event": "first reserved inference", "recorded_utc": stamp(min(r["start_utc"] for r in pred_raw)), "source": RAW_P + "/executions.json:start_utc"},
        {"event": "last reserved inference completed", "recorded_utc": stamp(max(r["end_utc"] for r in pred_raw)), "source": RAW_P + "/executions.json:end_utc"},
        {"event": "prediction file completed", "recorded_utc": stamp(predictions["created_utc"]), "source": "RESERVED_PREDICTIONS.json:created_utc"},
        {"event": "prediction checkpoint Git commit", "recorded_utc": stamp(commit_time(p_commit)), "source": "Git committer date (repository metadata)"},
        {"event": "prediction checkpoint push", "recorded_utc": "UNKNOWN", "source": "Outcome stage records a push gate; no independent push timestamp"},
        {"event": "live outcome checkpoint", "recorded_utc": stamp(live_checkpoint["start_utc"]), "source": RAW_L + "/checkpoint.json:start_utc"},
        {"event": "first live serialized outcome", "recorded_utc": stamp(min(r["start_utc"] for r in live_raw)), "source": RAW_L + "/executions.json:start_utc"},
    ]
    key = lambda r: (r["task_id"], r["repetition"])
    pred_by = {key(r): r for r in predictions["predictions"]}
    raw_by = {(r["task_id"], r["repetition"], r["n_ubatch"]): r for r in pred_raw}
    live_by = {key(r): r for r in live_raw}
    expected_keys = {(t, rep) for t in task_ids for rep in range(1, hypothesis["repetitions"] + 1)}
    fail_unless(len(pred_by) == len(live_by) == len(expected_keys) == 72 and set(pred_by) == set(live_by) == expected_keys, "Missing/duplicate prediction or outcome")
    fail_unless(len(raw_by) == len(pred_raw) == 144, "Duplicate raw predictor execution")
    fail_unless(set(raw_by) == {(t, rep, ub) for t, rep in expected_keys for ub in (1, 128)}, "Missing raw predictor execution")
    fail_unless(len({key(r) for r in validation["pairs"]}) == 72, "Validation pairs duplicate or absent")
    runs = []
    grouped = defaultdict(list)
    for task in task_ids:
        for rep in range(1, 4):
            k = (task, rep)
            p, l = pred_by[k], live_by[k]
            ref, pred, actual = p["reference_ids"], p["predicted_ids"], l["generated_ids"]
            for ids, recorded in [(ref, p["reference_ids_sha256"]), (pred, p["predicted_ids_sha256"]), (actual, l["generated_ids_sha256"])]:
                fail_unless(array_sha(ids) == recorded and 0 < len(ids) <= 128, "Array hash or endpoint mismatch: " + str(k))
            for ub, ids in [(128, ref), (1, pred)]:
                r = raw_by[(task, rep, ub)]
                fail_unless(r["generated_ids"] == ids and r["generated_ids_sha256"] == array_sha(ids) and r["execution_valid"], "Prediction/raw mismatch: " + str(k))
            stop = next((i + 1 for i, flag in enumerate(l["raw_eog_flags"]) if flag), len(l["raw_committed_ids"]))
            fail_unless(actual == l["raw_committed_ids"][:min(stop, 128)] and l["execution_valid"], "Live semantic endpoint mismatch: " + str(k))
            fail_unless(l["prediction_sha256"] == prediction_sha and l["prediction_commit"] == p_commit, "Live provenance mismatch")
            index, rt, lt = comparison(ref, actual)
            predicted_index, _, _ = comparison(ref, pred)
            row = {"task_id": task, "repetition": rep, "reference_length": len(ref), "predictor_length": len(pred),
                   "live_length": len(actual), "reference_ids_sha256": array_sha(ref), "predicted_ids_sha256": array_sha(pred),
                   "live_ids_sha256": array_sha(actual), "predictor_equals_live": pred == actual,
                   "reference_equals_predictor": ref == pred, "reference_equals_live": ref == actual,
                   "first_divergence_index_reference_vs_live": index, "reference_token_at_first_divergence": rt,
                   "live_token_at_first_divergence": lt, "predicted_first_divergence_index_reference": predicted_index}
            grouped[task].append(row)
            runs.append(row)
    compact = []
    for task in task_ids:
        rr = grouped[task]
        fail_unless(len(rr) == 3 and [r["repetition"] for r in rr] == [1, 2, 3], "Repetition coverage mismatch")
        divergent = [r for r in rr if not r["reference_equals_live"]]
        fail_unless(len(divergent) in (0, 3), "Reference/live classification not repeat stable")
        if divergent:
            fail_unless(len({(r["first_divergence_index_reference_vs_live"], r["reference_token_at_first_divergence"], r["live_token_at_first_divergence"]) for r in rr}) == 1, "Divergence not repeat stable")
        summary = {"task_id": task, "repetitions": 3, "predictor_live_exact_count": sum(r["predictor_equals_live"] for r in rr),
                   "reference_live_exact_count": sum(r["reference_equals_live"] for r in rr),
                   "reference_predictor_exact_count": sum(r["reference_equals_predictor"] for r in rr),
                   "first_divergence_index": rr[0]["first_divergence_index_reference_vs_live"],
                   "reference_token": rr[0]["reference_token_at_first_divergence"],
                   "live_token": rr[0]["live_token_at_first_divergence"],
                   "repeat_stable_predictor": len({r["predicted_ids_sha256"] for r in rr}) == 1,
                   "repeat_stable_live": len({r["live_ids_sha256"] for r in rr}) == 1}
        for r in rr:
            suffix = str(r["repetition"])
            summary["sequence_length_r" + suffix] = r["live_length"]
            summary["predicted_hash_r" + suffix] = r["predicted_ids_sha256"]
            summary["live_hash_r" + suffix] = r["live_ids_sha256"]
        compact.append(summary)
    class_matches = sum(all(r["reference_equals_live"] == r["reference_equals_predictor"] for r in grouped[t]) for t in task_ids)
    divergent_pairs = [r for r in runs if not r["reference_equals_live"]]
    first_matches = sum(r["first_divergence_index_reference_vs_live"] == r["predicted_first_divergence_index_reference"] for r in divergent_pairs)
    counts = {"reserved_prompt_count": len(task_ids), "repetition_count_per_prompt": 3, "prediction_count": len(runs),
              "predictor_live_exact_pairs": sum(r["predictor_equals_live"] for r in runs),
              "reference_live_exact_pairs": sum(r["reference_equals_live"] for r in runs),
              "reference_predictor_exact_pairs": sum(r["reference_equals_predictor"] for r in runs),
              "prompt_classification_matches": class_matches,
              "divergent_pair_first_index_matches": first_matches, "divergent_pair_count": len(divergent_pairs),
              "divergent_prompt_count": sum(bool([r for r in grouped[t] if not r["reference_equals_live"]]) for t in task_ids),
              "discovery_H1_exact_pairs": sum(r["exact"] and r["execution_valid"] for r in discovery["pairs"])}
    fail_unless((counts["predictor_live_exact_pairs"], counts["reference_live_exact_pairs"], class_matches,
                 first_matches, counts["divergent_pair_count"], counts["divergent_prompt_count"], counts["discovery_H1_exact_pairs"]) ==
                (72, 60, 24, 12, 12, 4, 36), "Critical claim mismatch")
    fail_unless(all(s["repeat_stable_predictor"] and s["repeat_stable_live"] for s in compact), "Repeat instability")
    fail_unless(validation["exact_sequences"] == counts["predictor_live_exact_pairs"] and validation["first_divergence_exact_pairs"] == first_matches, "Old validation disagrees")
    endpoint = {"array": "complete generated-token IDs only; prompt IDs excluded", "committed_id_cap": hypothesis["output_cap"],
                "eog": hypothesis["eog"], "comparison": "complete sequence equality, including length",
                "first_divergence_index_base": 0,
                "live_semantic_rule": "raw committed IDs through first EOG inclusive or 128 IDs, whichever comes first"}
    master = {"schema_version": "heterospec.b570.prediction_commitment_ledger.v083", "source_files": list(sources),
              "source_file_sha256": sources, "generator_script_sha256": sha(Path(__file__).read_bytes()),
              "commitment": {"hypothesis_content_sha256": predictions["hypothesis_sha256"], "hypothesis_freeze_commit": h_commit,
                             "prediction_file_sha256": prediction_sha, "prediction_freeze_commit": p_commit},
              "endpoint": endpoint, "chronology": chronology, "reserved_prompt_ids": task_ids,
              "per_run_records": runs, "per_prompt_summary": compact, "aggregate_checks": counts,
              "exposure_audit_wording": "no known B570 exposure in audited retained records"}
    OUT.mkdir(parents=True, exist_ok=True)
    run_fields = [k for k in runs[0] if k != "predicted_first_divergence_index_reference"]
    compact_fields = list(compact[0])
    (OUT / "B570_PREDICTION_COMMITMENT_RUNS_V083.csv").write_bytes(csv_bytes([{k: r[k] for k in run_fields} for r in runs], run_fields))
    (OUT / "B570_PREDICTION_COMMITMENT_LEDGER_V083.csv").write_bytes(csv_bytes(compact, compact_fields))
    (OUT / "B570_PREDICTION_COMMITMENT_LEDGER_V083.json").write_text(json.dumps(master, indent=2) + "\n")
    write_markdown(master)
    write_audits(master)
    print(json.dumps(counts, sort_keys=True))


def write_markdown(m):
    a, c = m["aggregate_checks"], m["commitment"]
    lines = ["# B570 Prediction Commitment Ledger — v0.8.3", "", "## 1. Scope", "",
             "Existing-record reconstruction only; zero new inference. The reserved set contains 24 prompts, three repetitions each, and 72 complete generated-token-ID predictions. Exposure wording: no known B570 exposure in audited retained records.", "",
             "## 2. Commitment identity", "", f"- Prediction file SHA-256: `{c['prediction_file_sha256']}`.",
             f"- Prediction freeze Git provenance marker: `{c['prediction_freeze_commit']}`.",
             f"- Hypothesis freeze Git provenance marker: `{c['hypothesis_freeze_commit']}`; hypothesis content SHA-256: `{c['hypothesis_content_sha256']}`.", "",
             "A content digest identifies bytes. A Git commit binds those bytes to repository history; the recorded times support ordering. None alone proves wall-clock publication to the world.", "",
             "## 3. Chronology", "", "| Event | Recorded UTC time | Provenance source |", "|---|---|---|"]
    lines += [f"| {r['event']} | {r['recorded_utc']} | `{r['source']}` |" for r in m["chronology"]]
    lines += ["", "## 4. Endpoint rule", "", "Complete generated-token IDs only; prompt IDs excluded. At most 128 committed IDs; an earlier terminal EOG is included. Equality compares the entire sequence including length. First divergence uses zero-based indexing; if one sequence ends first, the absent token is null.", "",
              "## 5. Reserved result summary", "", f"- Frozen UB1 predictor → live serialized complete equality: **{a['predictor_live_exact_pairs']}/{a['prediction_count']}**.",
              f"- UB128 reference trajectory → live serialized equality: **{a['reference_live_exact_pairs']}/{a['prediction_count']}**.",
              f"- Prompt mismatch/no-mismatch classification: **{a['prompt_classification_matches']}/{a['reserved_prompt_count']}**.",
              f"- Divergent repetition-pair first-divergence agreement: **{a['divergent_pair_first_index_matches']}/{a['divergent_pair_count']}**, across **{a['divergent_prompt_count']}** prompts.", "",
              "## 6. 24-prompt compact table", "", "Full digests are in the CSV and JSON ledgers; this table shows their first 12 hex characters.", "",
              "| Task | Pred=Live | Ref=Live | Live length r1/r2/r3 | Pred/live digest r1 | First divergence |", "|---|---:|---:|---|---|---:|"]
    for s in m["per_prompt_summary"]:
        lengths = "/".join(str(s[f"sequence_length_r{i}"]) for i in (1, 2, 3))
        digest = s["predicted_hash_r1"][:12] + "/" + s["live_hash_r1"][:12]
        lines.append(f"| {s['task_id']} | {s['predictor_live_exact_count']}/3 | {s['reference_live_exact_count']}/3 | {lengths} | `{digest}` | {s['first_divergence_index'] if s['first_divergence_index'] is not None else '—'} |")
    lines += ["", "## 7. Divergent prompts", "", "All three repetitions agree within each listed prompt for both predictor and live sequences.", "",
              "| Task | Repetition agreement | First divergence (zero-based) | Reference token | Predicted/live token |", "|---|---|---:|---:|---:|"]
    for s in m["per_prompt_summary"]:
        if s["reference_live_exact_count"] == 0:
            lines.append(f"| {s['task_id']} | 3/3 stable | {s['first_divergence_index']} | {s['reference_token']} | {s['live_token']} |")
    lines += ["", "## 8. Interpretation boundary", "",
              "The target-only UB1 predictor reproduces the tested serialized trajectory. Live draft computation is not required to generate that tested trajectory. The records do not establish a unique numerical root cause, a specific Vulkan kernel, a general B570 law, universal UB1 correctness, an RTX mechanism, or cross-backend transfer.", ""]
    (OUT / "B570_PREDICTION_COMMITMENT_LEDGER_V083.md").write_text("\n".join(lines))


def write_audits(m):
    a, c = m["aggregate_checks"], m["commitment"]
    chronology = {r["event"]: r["recorded_utc"] for r in m["chronology"]}
    source_list = "\n".join("- `" + s + "`" for s in m["source_files"])
    audit = f"""# B570 Prediction Ledger Audit — Phase 1

## Inputs

{source_list}

The two raw execution JSON files are retrieved from tracked Git objects when absent from the checkout. Their bytes match their canonical manifests.

## Reconstruction

{a['prediction_count']} run rows, {a['reserved_prompt_count']} prompts, {a['repetition_count_per_prompt']} repetitions. Complete generated-token IDs, prompt IDs excluded, cap 128, earlier EOG inclusive; full-array equality and zero-based first divergence.

## Commitment verification

Recomputed prediction-file SHA-256: `{c['prediction_file_sha256']}`. Frozen expected SHA-256: `{c['prediction_file_sha256']}`. **PASS**. Git prediction commit contains byte-identical content. Hypothesis content digest is byte-verified against the prediction record and freeze commit.

## Chronology

H1 freeze {chronology['H1 hypothesis freeze']}; reserved inference begins {chronology['first reserved inference']}; prediction file completed {chronology['prediction file completed']}; prediction checkpoint commit {chronology['prediction checkpoint Git commit']}; first live run {chronology['first live serialized outcome']}. Push time UNKNOWN; the outcome stage records that it checked the pushed checkpoint. Git commit times are repository metadata, not independent publication proof.

## Recomputed outcomes

UB1 predictor/live {a['predictor_live_exact_pairs']}/{a['prediction_count']}; UB128 reference/live {a['reference_live_exact_pairs']}/{a['prediction_count']}; prompt classification {a['prompt_classification_matches']}/{a['reserved_prompt_count']}; first divergence {a['divergent_pair_first_index_matches']}/{a['divergent_pair_count']} over {a['divergent_prompt_count']} divergent prompts. Discovery supports H1 in {a['discovery_H1_exact_pairs']}/36 archived pairs.

## Evidence completeness

All 72 predictions and 72 live outcomes exist. Each pair is bound by complete-array SHA-256 and an exact task/repetition key. All 24 prompts fit the compact ledger. The audited retained records report no known B570 exposure; they cannot prove no earlier exposure anywhere.

## CR-01 verdict

**FULLY ADDRESSABLE FROM EXISTING RECORDS.** The evidence gap is NO; the presentation/inspectability gap is YES.

## CR-02 verdict

**ADDRESSABLE FROM EXISTING RECORDS.** Reference trajectory agreement is {a['reference_live_exact_pairs']}/72 versus frozen UB1 predictor agreement {a['predictor_live_exact_pairs']}/72, without a new experiment. UB128 was a reference trajectory, not a prospectively registered failed mechanism predictor.

## Anonymity verdict

Anonymous appendix candidates: content digest, task IDs, lengths, truncated per-sequence digests, event ordering. Review UTC timestamps for linkage risk. Keep Git SHA, repository URL, username, local path, hostname, public artifact URL and identifying branch name out of the anonymous PDF.

## Scientific integrity

No new inference, data substitution, manual result entry, or modification of closed evidence. This Phase 1 file does not revise the manuscript.
"""
    (OUT / "B570_PREDICTION_LEDGER_AUDIT_V083.md").write_text(audit)
    anonymity = """# B570 Ledger Anonymity Audit — v0.8.3

| Field | Rating | Reason |
|---|---|---|
| Prediction-file content SHA-256 | SAFE | Identifies bytes without directly identifying an author; check publication links before release. |
| Reserved task IDs | SAFE | Benchmark identifiers, with no personal identity. |
| Sequence lengths | SAFE | Result metadata. |
| Truncated per-sequence digests | SAFE | Inspectable fingerprint; full digests stay in the artifact ledger. |
| Event ordering | SAFE | Relative sequence of recorded events. |
| Exact UTC timestamps | REVIEW | May link an anonymous submission to public commits or posts. |
| Git commit SHA | DO NOT EXPOSE | Searchable public commit may reveal author identity. |
| Repository URL | DO NOT EXPOSE | Direct author identity link. |
| Username | DO NOT EXPOSE | Direct identifier. |
| Local path | DO NOT EXPOSE | May contain a username or organization. |
| Machine hostname | DO NOT EXPOSE | May identify a person or institution. |
| Public artifact URL | DO NOT EXPOSE | May reveal repository ownership or author. |
| Identifying branch name | DO NOT EXPOSE | Searchable repository linkage. |

This is a field-risk audit, not a final PDF selection. A file digest proves content identity, a Git marker binds bytes to repository history, and recorded times support ordering. None alone cryptographically proves when the material became public.
"""
    (OUT / "B570_LEDGER_ANONYMITY_AUDIT_V083.md").write_text(anonymity)


if __name__ == "__main__":
    main()
