#!/usr/bin/env python3
"""Independent offline validation of the Phase-1 B570 ledger and its sources."""
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "paper/mlsys2027/evidence"


def check(value, label):
    if not value:
        raise AssertionError(label)


def source_bytes(path):
    local = ROOT / path
    if local.is_file():
        return local.read_bytes()
    return subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT)


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def ids_fingerprint(ids):
    return fingerprint(json.dumps(ids, separators=(",", ":")).encode())


def first_difference(left, right):
    for position in range(min(len(left), len(right))):
        if left[position] != right[position]:
            return position, left[position], right[position]
    if len(left) != len(right):
        position = min(len(left), len(right))
        return position, left[position] if position < len(left) else None, right[position] if position < len(right) else None
    return None, None, None


def csv_rows(name):
    with (EVIDENCE / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    master = json.loads((EVIDENCE / "B570_PREDICTION_COMMITMENT_LEDGER_V083.json").read_text())
    check(master["schema_version"] == "heterospec.b570.prediction_commitment_ledger.v083", "schema")
    check(set(master["source_files"]) == set(master["source_file_sha256"]), "source inventory")
    for path, claimed in master["source_file_sha256"].items():
        check(fingerprint(source_bytes(path)) == claimed, "source digest: " + path)
    check(fingerprint(source_bytes("paper/mlsys2027/scripts/build_b570_prediction_ledger_v083.py")) == master["generator_script_sha256"], "generator digest")
    base = "benchmarks/b570_mechanism_v08/"
    predictions = json.loads(source_bytes(base + "RESERVED_PREDICTIONS.json"))
    freeze = json.loads(source_bytes(base + "hypothesis_freeze.json"))
    selected = json.loads(source_bytes(base + "RESERVED_VALIDATION_SET.json"))["selected_task_ids"]
    raw_predictions = json.loads(source_bytes("artifacts/b570_mechanism_v08/raw/reserved_predictions/executions.json"))["executions"]
    raw_live = json.loads(source_bytes("artifacts/b570_mechanism_v08/raw/reserved_outcomes/executions.json"))["executions"]
    prediction_digest = fingerprint(source_bytes(base + "RESERVED_PREDICTIONS.json"))
    check(prediction_digest == master["commitment"]["prediction_file_sha256"], "prediction file identity")
    check(prediction_digest == source_bytes(base + "RESERVED_PREDICTIONS_SHA256.txt").decode().split()[0], "frozen prediction digest")
    check(fingerprint(source_bytes(base + "hypothesis_freeze.json")) == master["commitment"]["hypothesis_content_sha256"], "hypothesis identity")
    for label, path in (("prediction_freeze_commit", base + "RESERVED_PREDICTIONS.json"),
                        ("hypothesis_freeze_commit", base + "hypothesis_freeze.json")):
        committed = subprocess.check_output(["git", "show", master["commitment"][label] + ":" + path], cwd=ROOT)
        check(committed == source_bytes(path), label + " bytes")
    check(len(selected) == len(set(selected)) == 24 and selected == freeze["reserved_task_ids"], "selected prompts")
    check(freeze["repetitions"] == 3 and freeze["output_cap"] == 128, "frozen endpoint")
    endpoint = master["endpoint"]
    check(endpoint["committed_id_cap"] == 128 and endpoint["first_divergence_index_base"] == 0, "ledger endpoint")
    check("prompt IDs excluded" in endpoint["array"] and "EOG" in endpoint["eog"], "endpoint text")
    expected = {(task, repetition) for task in selected for repetition in (1, 2, 3)}
    pred_index = {(r["task_id"], r["repetition"]): r for r in predictions["predictions"]}
    live_index = {(r["task_id"], r["repetition"]): r for r in raw_live}
    raw_index = {(r["task_id"], r["repetition"], r["n_ubatch"]): r for r in raw_predictions}
    check(len(pred_index) == len(predictions["predictions"]) == 72 and set(pred_index) == expected, "predicted pair coverage")
    check(len(live_index) == len(raw_live) == 72 and set(live_index) == expected, "live pair coverage")
    check(len(raw_index) == len(raw_predictions) == 144, "raw pair coverage")
    check(set(raw_index) == {(task, rep, ub) for task, rep in expected for ub in (1, 128)}, "raw UB coverage")
    rows = master["per_run_records"]
    csv_run = csv_rows("B570_PREDICTION_COMMITMENT_RUNS_V083.csv")
    csv_compact = csv_rows("B570_PREDICTION_COMMITMENT_LEDGER_V083.csv")
    check(len(rows) == len(csv_run) == 72 and len(csv_compact) == 24, "ledger row counts")
    check(len({(r["task_id"], r["repetition"]) for r in rows}) == 72, "duplicate ledger key")
    check(len(master["per_prompt_summary"]) == 24, "prompt summary count")
    observed = Counter()
    per_prompt = {task: [] for task in selected}
    for ledger, csv_row in zip(rows, csv_run):
        key = ledger["task_id"], ledger["repetition"]
        check(key in expected and csv_row["task_id"] == key[0] and int(csv_row["repetition"]) == key[1], "run CSV identity")
        p, live = pred_index[key], live_index[key]
        ref, pred, actual = p["reference_ids"], p["predicted_ids"], live["generated_ids"]
        for name, ids, recorded in (("reference", ref, p["reference_ids_sha256"]), ("predicted", pred, p["predicted_ids_sha256"]), ("live", actual, live["generated_ids_sha256"])):
            digest = ids_fingerprint(ids)
            check(digest == recorded, name + " source array hash")
            ledger_name = "predicted_ids_sha256" if name == "predicted" else name + "_ids_sha256"
            check(ledger[ledger_name] == csv_row[ledger_name] == digest, name + " ledger hash")
            check(0 < len(ids) <= 128, name + " cap")
        for ub, ids in ((1, pred), (128, ref)):
            capture = raw_index[key + (ub,)]
            check(capture["generated_ids"] == ids and capture["generated_ids_sha256"] == ids_fingerprint(ids), "raw inference binding")
        stop = len(live["raw_committed_ids"])
        for index, flag in enumerate(live["raw_eog_flags"]):
            if flag:
                stop = index + 1
                break
        check(actual == live["raw_committed_ids"][:min(stop, 128)], "live semantic boundary")
        check(live["prediction_sha256"] == prediction_digest, "live commitment binding")
        difference = first_difference(ref, actual)
        check(ledger["first_divergence_index_reference_vs_live"] == difference[0], "first divergence")
        check(ledger["reference_token_at_first_divergence"] == difference[1], "reference divergence token")
        check(ledger["live_token_at_first_divergence"] == difference[2], "live divergence token")
        check(ledger["predicted_first_divergence_index_reference"] == first_difference(ref, pred)[0], "predicted divergence")
        for label, value in (("reference_length", len(ref)), ("predictor_length", len(pred)), ("live_length", len(actual))):
            check(ledger[label] == value and int(csv_row[label]) == value, label)
        for label, value in (("predictor_equals_live", pred == actual), ("reference_equals_predictor", ref == pred), ("reference_equals_live", ref == actual)):
            check(ledger[label] is value and csv_row[label] == str(value), label)
        for label, value in (("first_divergence_index_reference_vs_live", difference[0]), ("reference_token_at_first_divergence", difference[1]), ("live_token_at_first_divergence", difference[2])):
            check(csv_row[label] == ("" if value is None else str(value)), "CSV " + label)
        observed["predictor_live_exact_pairs"] += pred == actual
        observed["reference_live_exact_pairs"] += ref == actual
        observed["reference_predictor_exact_pairs"] += ref == pred
        if ref != actual:
            observed["divergent_pair_count"] += 1
            observed["divergent_pair_first_index_matches"] += difference[0] == first_difference(ref, pred)[0]
        per_prompt[key[0]].append((key[1], ref, pred, actual, difference))
    observed["reserved_prompt_count"] = len(selected)
    observed["repetition_count_per_prompt"] = 3
    observed["prediction_count"] = len(rows)
    discovery = json.loads(source_bytes(base + "DISCOVERY_ANALYSIS.json"))["pairs"]
    observed["discovery_H1_exact_pairs"] = sum(r["exact"] and r["execution_valid"] for r in discovery)
    for task, summary, csv_row in zip(selected, master["per_prompt_summary"], csv_compact):
        rr = sorted(per_prompt[task])
        check(summary["task_id"] == csv_row["task_id"] == task and [r[0] for r in rr] == [1, 2, 3], "prompt identity")
        class_ok = all((r[1] == r[2]) == (r[1] == r[3]) for r in rr)
        observed["prompt_classification_matches"] += class_ok
        observed["divergent_prompt_count"] += any(r[1] != r[3] for r in rr)
        check(summary["repetitions"] == 3 and int(csv_row["repetitions"]) == 3, "prompt repetition")
        for name, value in (("predictor_live_exact_count", sum(r[2] == r[3] for r in rr)),
                            ("reference_live_exact_count", sum(r[1] == r[3] for r in rr)),
                            ("reference_predictor_exact_count", sum(r[1] == r[2] for r in rr))):
            check(summary[name] == value and int(csv_row[name]) == value, name)
        for number, (_, _, pred, actual, _) in enumerate(rr, 1):
            for name, value in (("sequence_length_r", len(actual)), ("predicted_hash_r", ids_fingerprint(pred)), ("live_hash_r", ids_fingerprint(actual))):
                field = name + str(number)
                check(str(summary[field]) == csv_row[field] == str(value), field)
        check(summary["repeat_stable_predictor"] == (len({tuple(r[2]) for r in rr}) == 1), "predictor repeat stability")
        check(summary["repeat_stable_live"] == (len({tuple(r[3]) for r in rr}) == 1), "live repeat stability")
        for field in ("repeat_stable_predictor", "repeat_stable_live"):
            check(csv_row[field] == str(summary[field]), "compact CSV " + field)
        for field, value in (("first_divergence_index", rr[0][4][0]), ("reference_token", rr[0][4][1]), ("live_token", rr[0][4][2])):
            check(summary[field] == value and csv_row[field] == ("" if value is None else str(value)), field)
    for key, actual in observed.items():
        check(master["aggregate_checks"].get(key) == actual, "aggregate " + key)
    check((observed["predictor_live_exact_pairs"], observed["reference_live_exact_pairs"], observed["prompt_classification_matches"], observed["divergent_pair_first_index_matches"], observed["divergent_prompt_count"], observed["discovery_H1_exact_pairs"]) == (72, 60, 24, 12, 4, 36), "critical claims")
    timeline = {r["event"]: r["recorded_utc"] for r in master["chronology"]}
    events = ("H1 hypothesis freeze", "first reserved inference", "last reserved inference completed",
              "prediction file completed", "prediction checkpoint Git commit", "first live serialized outcome")
    times = [datetime.fromisoformat(timeline[event].replace("Z", "+00:00")) for event in events]
    check(times == sorted(times) and timeline["prediction checkpoint push"] == "UNKNOWN", "chronology")
    print("PASS: independent source, array, endpoint, CSV, prompt, aggregate and chronology checks")


if __name__ == "__main__":
    main()
