#!/usr/bin/env python3
"""Retrospective E2 draft-profitability analysis; Python standard library only.

Run: python3 scripts/generate_e2_draft_profitability.py [--check]
The default manuscript root is relative to this script, not the cwd.
This reconstructs saved request times; it performs no native/model execution.
"""

import argparse
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "f29eba027022a1fb704bc1fb58ce3fe535d4387cdbec564f8086ac4bfdc08194"
EXPECTED_GIT_BLOB = "975240c96131f28f538314938e8269a08bd0d7d6"
EXPECTED_BYTES = 115850
REVIEWED_HEAD = "85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb"
E2_CAMPAIGN_COMMIT = "f997262d6b0accb126a1217c9356745cc8bbf708"
HEADER = ["session", "family", "arm", "slot", "warmup", "latency_ms",
          "output_length", "stop_reason", "pid", "contract_valid"]
FAMILIES = ("Qwen", "SmolLM2", "Llama")
DISPLAY = {"Qwen": "Qwen3", "SmolLM2": "SmolLM2", "Llama": "Llama"}
SESSIONS = tuple(range(6))
ARMS = ("M_PQ", "M_QB", "C_PQ", "C_QB")
TASKS = ("MBPP/123", "MBPP/140", "MBPP/255", "MBPP/401", "MBPP/413",
         "MBPP/418", "GSM8K/test/111", "GSM8K/test/120", "GSM8K/test/1308",
         "GSM8K/test/141", "GSM8K/test/322", "GSM8K/test/443")
SLOT = re.compile(r"s([0-5])/(Qwen|SmolLM2|Llama)/b([0-9]{2})(?:\|(.+)|/WARM)\Z")
# Two-sided 95% Student t critical value, df = 6 - 1. This fixed constant is
# used only after checking that there are exactly six complete session means.
T_975_DF5 = 2.570581835636314
CONTRASTS = ("D_PQ", "D_QB", "Gamma_QB_from_PQ")


class ValidationError(ValueError):
    """Saved-source structure or pairing differs from the fixed E2 contract."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def mean(values):
    values = list(values)
    require(bool(values), "Cannot average an empty group")
    return math.fsum(values) / len(values)


def load_source(path):
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    require(len(raw) == EXPECTED_BYTES, "Source byte length differs from pinned CSV")
    require(sha256 == EXPECTED_SHA256, "Source SHA256 differs from pinned CSV")
    require(blob == EXPECTED_GIT_BLOB, "Source Git-blob ID differs from pinned CSV")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
    require(reader.fieldnames == HEADER, "CSV schema or column order differs")
    return list(reader), {"filename": path.name, "bytes": len(raw),
                          "sha256": sha256, "git_blob": blob}


def validate_rows(raw_rows):
    """Validate full rows before excluding warmups or R from the contrasts.

    Worker blocks, not unique PIDs, identify source collection units. The CSV
    has no process creation times, and operating systems may recycle PIDs.
    Row order is not assumed to be chronological.
    """
    require(len(raw_rows) == 1620, "Expected all 1,620 source rows")
    rows, identities = [], set()
    blocks = collections.defaultdict(list)
    pairs = collections.defaultdict(lambda: collections.defaultdict(list))
    for line, source in enumerate(raw_rows, start=2):
        require(set(source) == set(HEADER), f"Line {line}: missing or extra CSV field")
        require(all(value is not None for value in source.values()), f"Line {line}: missing field")
        require(source["session"] in {str(s) for s in SESSIONS}, f"Line {line}: invalid session")
        session, family, arm = int(source["session"]), source["family"], source["arm"]
        require(family in FAMILIES, f"Line {line}: unknown family")
        require(arm in (*ARMS, "R"), f"Line {line}: unknown arm")
        require(source["warmup"] in ("True", "False"), f"Line {line}: invalid warmup flag")
        require(source["contract_valid"] == "True", f"Line {line}: contract flag is not True")
        try:
            latency = float(source["latency_ms"])
            output_length, pid = int(source["output_length"]), int(source["pid"])
        except (ValueError, TypeError) as exc:
            raise ValidationError(f"Line {line}: invalid numeric field") from exc
        require(math.isfinite(latency) and latency > 0, f"Line {line}: invalid request duration")
        require(1 <= output_length <= 128, f"Line {line}: invalid output length")
        require(pid > 0, f"Line {line}: invalid PID")
        require(source["stop_reason"] in ("CAP", "EOG"), f"Line {line}: unknown stop reason")
        require(source["stop_reason"] != "CAP" or output_length == 128,
                f"Line {line}: CAP without cap128 length")
        match = SLOT.fullmatch(source["slot"])
        require(match is not None, f"Line {line}: malformed source slot")
        slot_session, slot_family, block_id, task = match.groups()
        require(int(slot_session) == session and slot_family == family,
                f"Line {line}: slot identity conflicts with row")
        require(0 <= int(block_id) < 18, f"Line {line}: unexpected worker block")
        warmup = source["warmup"] == "True"
        require(warmup == (task is None), f"Line {line}: warmup flag/slot conflict")
        require(warmup or task in TASKS, f"Line {line}: task outside fixed panel")
        identity = (session, family, arm, source["slot"])
        require(identity not in identities, f"Line {line}: duplicated source slot")
        identities.add(identity)
        row = {**source, "line": line, "session": session, "latency_ms": latency,
               "output_length": output_length, "pid": pid, "warmup": warmup,
               "task": task, "block_id": int(block_id)}
        rows.append(row)
        blocks[(family, session, int(block_id))].append(row)
        if not warmup:
            pairs[(family, session, task)][arm].append(row)

    expected_blocks = {(f, s, b) for f in FAMILIES for s in SESSIONS for b in range(18)}
    require(set(blocks) == expected_blocks, "Missing or extra family/session/worker block")
    for key, group in blocks.items():
        require(len({r["arm"] for r in group}) == 1, f"Block {key}: mixed arms")
        require(len({r["pid"] for r in group}) == 1, f"Block {key}: mixed PIDs")
        require(sum(r["warmup"] for r in group) == 1, f"Block {key}: expected exactly one warmup")
        measured = [r for r in group if not r["warmup"]]
        arm = group[0]["arm"]
        require(len(measured) == (12 if arm == "R" else 3), f"Block {key}: wrong measurement count")
        require(len({r["task"] for r in measured}) == len(measured), f"Block {key}: duplicated task")
        if arm == "R":
            require({r["task"] for r in measured} == set(TASKS), f"Block {key}: incomplete R task set")

    expected_pairs = {(f, s, task) for f in FAMILIES for s in SESSIONS for task in TASKS}
    require(set(pairs) == expected_pairs, "Missing or extra family/session/task quartet")
    for key, group in pairs.items():
        require(set(group) == {*ARMS, "R"}, f"Pair {key}: missing or extra arm")
        for arm in ARMS:
            require(len(group[arm]) == 1, f"Pair {key}: expected one {arm} measurement")
        require(len(group["R"]) == 2, f"Pair {key}: expected two R measurements")
        require(len({r["block_id"] for r in group["R"]}) == 2,
                f"Pair {key}: R measurements must come from different blocks")
        # This checks recorded metadata only. Full token/vector qualification is
        # inherited from E2; token arrays are not present in this latency CSV.
        endpoint_metadata = {(r["output_length"], r["stop_reason"])
                             for arm_rows in group.values() for r in arm_rows}
        require(len(endpoint_metadata) == 1, f"Pair {key}: inconsistent endpoint metadata")

    for family in FAMILIES:
        for session in SESSIONS:
            group = [r for r in rows if (r["family"], r["session"]) == (family, session)]
            require(len(group) == 90 and sum(r["warmup"] for r in group) == 18,
                    f"{family}/{session}: wrong total/warmup counts")
            for arm in (*ARMS, "R"):
                measured = [r for r in group if r["arm"] == arm and not r["warmup"]]
                require(len(measured) == (24 if arm == "R" else 12),
                        f"{family}/{session}/{arm}: wrong measurement count")
                require({r["task"] for r in measured} == set(TASKS),
                        f"{family}/{session}/{arm}: wrong task set")
    for family in FAMILIES:
        for task in TASKS:
            observed = {(r["output_length"], r["stop_reason"])
                        for r in rows if not r["warmup"] and r["family"] == family and r["task"] == task}
            require(len(observed) == 1, f"{family}/{task}: endpoint metadata differs across sessions")

    counts = {"source_rows": len(rows), "worker_blocks": len(blocks),
              "warmups_excluded": sum(r["warmup"] for r in rows),
              "reference_measurements_excluded": sum(not r["warmup"] and r["arm"] == "R" for r in rows),
              "arm_measurements_used": sum(not r["warmup"] and r["arm"] != "R" for r in rows),
              "complete_four_arm_cells": len(pairs)}
    require(counts == {"source_rows": 1620, "worker_blocks": 324, "warmups_excluded": 324,
                       "reference_measurements_excluded": 432, "arm_measurements_used": 864,
                       "complete_four_arm_cells": 216}, "Source accounting mismatch")
    return rows, pairs, blocks, counts


def log_contrasts(group):
    value = {arm: group[arm][0]["latency_ms"] for arm in ARMS}
    d_pq = math.log(value["M_PQ"]) - math.log(value["C_PQ"])
    d_qb = math.log(value["M_QB"]) - math.log(value["C_QB"])
    gamma = d_qb - d_pq
    alternative = ((math.log(value["C_PQ"]) - math.log(value["C_QB"]))
                   - (math.log(value["M_PQ"]) - math.log(value["M_QB"])))
    require(math.isclose(gamma, alternative, rel_tol=0.0, abs_tol=1e-13),
            "Layout/draft interaction identity failed")
    return {"D_PQ": d_pq, "D_QB": d_qb, "Gamma_QB_from_PQ": gamma}


def summarize(values):
    require(len(values) == 6, "t5 interval requires exactly six session log means")
    estimate = mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(6)
    width = T_975_DF5 * se
    return {"log_estimate": estimate, "ratio": math.exp(estimate),
            "session_log_sd": sd, "session_log_se": se,
            "t5_pointwise95_low": math.exp(estimate - width),
            "t5_pointwise95_high": math.exp(estimate + width),
            "session_count": 6, "sessions_above_parity": sum(v > 0 for v in values),
            "sessions_below_parity": sum(v < 0 for v in values),
            "sessions_at_parity": sum(v == 0 for v in values),
            "session_ratio_min": math.exp(min(values)),
            "session_ratio_max": math.exp(max(values))}


def reconstruct(pairs, blocks):
    paired_rows, session_rows, family_rows = [], [], []
    values = {key: log_contrasts(group) for key, group in pairs.items()}
    for family in FAMILIES:
        for session in SESSIONS:
            for task in TASKS:
                key, group = (family, session, task), pairs[(family, session, task)]
                row = {"family": DISPLAY[family], "session": session, "task": task}
                for arm in ARMS:
                    row[arm + "_ms"] = group[arm][0]["latency_ms"]
                    row[arm + "_source_line"] = group[arm][0]["line"]
                row.update({contrast: math.exp(values[key][contrast]) for contrast in CONTRASTS})
                row["output_length"] = group["R"][0]["output_length"]
                row["stop_reason"] = group["R"][0]["stop_reason"]
                paired_rows.append(row)
            m_blocks = [b for (f, s, b), rs in blocks.items()
                        if (f, s) == (family, session) and rs[0]["arm"].startswith("M_")]
            c_blocks = [b for (f, s, b), rs in blocks.items()
                        if (f, s) == (family, session) and rs[0]["arm"].startswith("C_")]
            source_block_order = "M_before_C" if max(m_blocks) < min(c_blocks) else (
                "C_before_M" if max(c_blocks) < min(m_blocks) else "interleaved")
            for contrast in CONTRASTS:
                logs = [values[(family, session, task)][contrast] for task in TASKS]
                session_rows.append({"family": DISPLAY[family], "session": session,
                                     "contrast": contrast, "task_count": 12,
                                     "session_mean_log_ratio": mean(logs),
                                     "session_ratio": math.exp(mean(logs)),
                                     "tasks_above_parity": sum(z > 0 for z in logs),
                                     "tasks_below_parity": sum(z < 0 for z in logs),
                                     "source_block_order": source_block_order})
        for contrast in CONTRASTS:
            logs = [r["session_mean_log_ratio"] for r in session_rows
                    if r["family"] == DISPLAY[family] and r["contrast"] == contrast]
            result = summarize(logs)
            task_logs = [mean(values[(family, s, task)][contrast] for s in SESSIONS) for task in TASKS]
            result.update({"family": DISPLAY[family], "contrast": contrast,
                           "task_count": 12, "task_aggregates_above_parity": sum(z > 0 for z in task_logs),
                           "task_aggregates_below_parity": sum(z < 0 for z in task_logs)})
            family_rows.append(result)
    return paired_rows, session_rows, family_rows


def csv_text(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def derived_json_equal(actual, expected):
    """Match anc/check_closure.py: only finite derived floats allow one ULP.

    Keeping this small standard-library comparator here makes the reanalysis
    independently runnable. Types, keys, ordering and other leaves stay exact.
    """
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, float):
        return (math.isfinite(actual) and math.isfinite(expected)
                and actual in (expected, math.nextafter(expected, -math.inf),
                               math.nextafter(expected, math.inf)))
    if isinstance(expected, dict):
        return (actual.keys() == expected.keys()
                and all(derived_json_equal(actual[k], v) for k, v in expected.items()))
    if isinstance(expected, list):
        return (len(actual) == len(expected)
                and all(derived_json_equal(a, e) for a, e in zip(actual, expected)))
    return actual == expected


def read_derived_json(text):
    """Reject duplicate keys and nonfinite JSON extensions before comparison."""
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate derived JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValidationError("Non-finite derived JSON number: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def derived_csv_equal(actual, expected):
    """Allow one ULP only in derived floating columns; source values stay exact."""
    floating = {"log_estimate", "ratio", "session_log_sd", "session_log_se",
                "t5_pointwise95_low", "t5_pointwise95_high", "session_ratio_min",
                "session_ratio_max", "session_mean_log_ratio", "session_ratio",
                *CONTRASTS}
    actual_rows = list(csv.reader(io.StringIO(actual, newline="")))
    expected_rows = list(csv.reader(io.StringIO(expected, newline="")))
    if len(actual_rows) != len(expected_rows) or not expected_rows:
        return False
    header = expected_rows[0]
    if actual_rows[0] != header or len(set(header)) != len(header):
        return False
    for actual_row, expected_row in zip(actual_rows[1:], expected_rows[1:]):
        if len(actual_row) != len(header) or len(expected_row) != len(header):
            return False
        for column, a, e in zip(header, actual_row, expected_row):
            if column in floating:
                try:
                    if not derived_json_equal(float(a), float(e)):
                        return False
                except ValueError:
                    return False
            elif a != e:
                return False
    return True


def derived_output_equal(name, actual, expected):
    if name.endswith(".json"):
        try:
            return derived_json_equal(read_derived_json(actual), read_derived_json(expected))
        except ValueError:
            return False
    if name.endswith(".csv"):
        return derived_csv_equal(actual, expected)
    return actual == expected


def tex_outputs(summary):
    lookup = {(r["family"], r["contrast"]): r for r in summary}
    main = [r"\begin{table}[t]\centering\small",
            r"\caption{Retrospective E2 draft values on the fixed 12-input panel: $D_L=T_{M_L}/T_{C_L}>1$ favors drafting. QB intervals are exploratory pointwise 95\% $t_5$ intervals over six session log means. E2 has no GS arm.}\label{tab:e2draft}",
            r"\begin{tabular}{@{}lrrr@{}}\toprule",
            r"Family & $D_{\mathrm{PQ}}$ & $D_{\mathrm{QB}}$ & QB interval\\\midrule"]
    for family in FAMILIES:
        name = DISPLAY[family]
        pq, qb = lookup[(name, "D_PQ")], lookup[(name, "D_QB")]
        main.append(f"{name} & {pq['ratio']:.3f} & {qb['ratio']:.3f} & "
                    f"[{qb['t5_pointwise95_low']:.3f}, {qb['t5_pointwise95_high']:.3f}]" + r"\\")
    main += [r"\bottomrule\end{tabular}", r"\end{table}", ""]
    detailed = [r"\begin{table*}[t]\centering\small",
                r"\caption{Exploratory E2 draft and layout--draft contrasts. Pointwise 95\% $t_5$ intervals use six session mean log ratios and assume independent, approximately normal session means; they are not multiplicity-adjusted. $\Gamma=D_{\mathrm{QB}}/D_{\mathrm{PQ}}$ measures the change in draft value between the two local layouts, not GS/local repair interaction.}\label{tab:e2draftposthocdetail}",
                r"\begin{tabular}{llrrcc}\toprule",
                r"Family & Contrast & Estimate & Pointwise 95\% interval & Sessions $>1$ & Sessions $<1$\\\midrule"]
    labels = {"D_PQ": r"$D_{\mathrm{PQ}}$", "D_QB": r"$D_{\mathrm{QB}}$",
              "Gamma_QB_from_PQ": r"$\Gamma$"}
    for family in FAMILIES:
        for contrast in CONTRASTS:
            r = lookup[(DISPLAY[family], contrast)]
            detailed.append(f"{r['family']} & {labels[contrast]} & {r['ratio']:.6f} & "
                            f"[{r['t5_pointwise95_low']:.6f}, {r['t5_pointwise95_high']:.6f}] & "
                            f"{r['sessions_above_parity']}/6 & {r['sessions_below_parity']}/6" + r"\\")
    detailed += [r"\bottomrule\end{tabular}", r"\end{table*}", ""]
    paragraph = (
        "A retrospective analysis of the separately scheduled E2 requests also compares target-only and speculative execution within each local layout. "
        "Using the same task/session log weights, the target-only-to-speculative ratios are "
        "1.072/1.084 for Qwen3, 0.576/0.597 for SmolLM2 and 1.091/1.105 for Llama (PQ/QB; "
        "Table~\\ref{tab:e2draft}). "
        "All six session means retain these directions: drafting lowers request cost for Qwen3 and Llama, whereas SmolLM2 favors target-only execution. "
        "This reanalysis supports the local-repair draft choices on the fixed panel; it adds no executions and, because E2 has no GS arm, does not independently reproduce the GS-to-local crossover.\n"
    )
    supplement = (
        "For each family, session and input, the reanalysis pairs exactly one non-warmup record from each of "
        "$M_{\\mathrm{PQ}},M_{\\mathrm{QB}},C_{\\mathrm{PQ}},C_{\\mathrm{QB}}$. "
        "There are 216 complete four-arm cells (864 measured requests). "
        "The 324 registered warmups and 432 serial-reference measurements are excluded from these contrasts after their source accounting and recorded endpoint metadata are checked. "
        "Each session averages twelve task log ratios; the reported estimate averages the six session means. "
        "Pointwise exploratory $t_5$ intervals use the six session log means with no multiplicity adjustment. "
        "These contrasts were selected retrospectively and do not replace the original primary E2 comparisons or their registered bootstrap analysis. "
        "These intervals retain the fixed-input, single-host scope of E2 and do not add a native execution or repeat full token-array qualification. "
        "The saved block order is M before C in four of six Qwen3 sessions, three of six SmolLM2 sessions and four of six Llama sessions; the remaining sessions reverse that order. "
        "Thus the M/C contrasts use separately scheduled within-session blocks, not newly randomized adjacent per-input M/C measurements, and do not isolate block-order or temporal-drift effects.\n\n"
        "The local-layout interaction is $\\Gamma=D_{\\mathrm{QB}}/D_{\\mathrm{PQ}}=(C_{\\mathrm{PQ}}/C_{\\mathrm{QB}})/(M_{\\mathrm{PQ}}/M_{\\mathrm{QB}})$. "
        "Its estimates are 1.010828, 1.037008 and 1.013313 for Qwen3, SmolLM2 and Llama. "
        "The exploratory intervals span parity for Qwen3 and Llama; SmolLM2's interval is [1.027962,1.046134]. "
        "Thus an improvement in draft value from QB does not itself imply profitable drafting, as the SmolLM2 result demonstrates.\n"
    )
    return {"tables/e2_draft_profitability.tex": "\n".join(main),
            "tables/e2_draft_profitability_details.tex": "\n".join(detailed),
            "anc/rtx104/e2_draft_profitability_main_text.tex.txt": paragraph,
            "anc/rtx104/e2_draft_profitability_supplement_text.tex.txt": supplement}


def analyse(root=ROOT):
    root = Path(root)
    raw_rows, source = load_source(root / "anc/rtx104/E2_REQUEST_LATENCIES.csv")
    rows, pairs, blocks, counts = validate_rows(raw_rows)
    paired_rows, session_rows, family_rows = reconstruct(pairs, blocks)
    require(len(paired_rows) == 216 and len(session_rows) == 54 and len(family_rows) == 9,
            "Derived output accounting mismatch")
    report = {
        "schema": "heterospec.e2-draft-posthoc/1.0",
        "analysis_status": "RETROSPECTIVE_EXPLORATORY_REANALYSIS",
        "new_native_executions": 0,
        "source": {**source, "repository": "leecdiang/HeteroSpec",
                   "reviewed_pr": 145, "reviewed_head": REVIEWED_HEAD,
                   "source_repository_path": "paper/arxiv_v4_candidate/anc/rtx104/E2_REQUEST_LATENCIES.csv",
                   "original_E2_campaign_commit": E2_CAMPAIGN_COMMIT},
        "validation": {"status": "PASS", **counts,
                       "family_count": 3, "sessions_per_family": 6, "tasks_per_family_session": 12,
                       "source_hashes_verified": True, "duplicate_measurements": 0,
                       "missing_four_arm_cells": 0, "unmatched_task_sets": 0,
                       "warmup_slot_and_flag_checked": True,
                       "recorded_endpoint_metadata_consistent": True,
                       "full_token_arrays_revalidated": False,
                       "worker_note": "324 source worker blocks; PID reuse is allowed and unique PID count is not a worker count."},
        "estimands": {
            "D_PQ": "T(M_PQ)/T(C_PQ); greater than one favors drafting under PQ.",
            "D_QB": "T(M_QB)/T(C_QB); greater than one favors drafting under QB.",
            "Gamma_QB_from_PQ": "D_QB/D_PQ = (C_PQ/C_QB)/(M_PQ/M_QB); greater than one means QB increases draft value relative to PQ, not necessarily above parity."},
        "estimator": "Equal mean of twelve task log contrasts within session, then equal mean of six session means, exponentiated.",
        "interval": {"method": "Two-sided Student t on six session mean log contrasts, exponentiated",
                     "confidence_level": 0.95, "degrees_of_freedom": 5,
                     "critical_value": T_975_DF5, "pointwise": True,
                     "multiplicity_adjusted": False,
                     "assumptions": "Independent, approximately normal session log means; fixed 12-input panel on one host."},
        "limits": ["Post hoc contrasts; not a preregistered primary E2 endpoint.",
                   "No GS arm: no independent replication of the full GS/local repair-by-draft interaction.",
                   "No new native requests, models, hosts, dates or inputs.",
                   "Same output-length/stop metadata and stored contract flags do not revalidate full token arrays.",
                   "M/C comparisons use saved within-session blocks, not newly randomized simultaneous pairs.",
                   "Ratio products do not decompose operator time or isolate a CUDA Graph mechanism."],
        "source_block_order_by_family": {
            DISPLAY[family]: dict(collections.Counter(
                row["source_block_order"] for row in session_rows
                if row["family"] == DISPLAY[family] and row["contrast"] == "D_PQ"))
            for family in FAMILIES},
        "family_results": family_rows, "session_results": session_rows,
    }
    return report, paired_rows


def outputs(root=ROOT):
    """Return manuscript-relative filenames and exact deterministic UTF-8 text."""
    report, paired_rows = analyse(root)
    return {"anc/rtx104/e2_draft_profitability.json": json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            "anc/rtx104/e2_draft_profitability_summary.csv": csv_text(report["family_results"]),
            "anc/rtx104/e2_draft_profitability_sessions.csv": csv_text(report["session_results"]),
            "anc/rtx104/e2_draft_profitability_pairs.csv": csv_text(paired_rows),
            **tex_outputs(report["family_results"])}


def verify(check, root=ROOT):
    """Read-only hook compatible with anc/check.py's check(name, condition)."""
    root = Path(root)
    generated = outputs(root)
    for name, body in generated.items():
        path = root / name
        check("E2 posthoc reconstruction consistency: " + name,
              path.is_file() and derived_output_equal(name, path.read_bytes().decode("utf-8"), body))
    report = json.loads(generated["anc/rtx104/e2_draft_profitability.json"])
    check("E2 posthoc preserves exploratory/no-GS interpretation",
          report["analysis_status"] == "RETROSPECTIVE_EXPLORATORY_REANALYSIS"
          and not report["interval"]["multiplicity_adjusted"]
          and report["new_native_executions"] == 0
          and any("No GS arm" in text for text in report["limits"]))
    return report["validation"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Manuscript root containing anc/rtx104")
    parser.add_argument("--check", action="store_true", help="Check committed derived files without writing")
    args = parser.parse_args(argv)
    if args.check:
        counts = verify(lambda name, condition: require(condition, name), args.root)
    else:
        generated = outputs(args.root)
        for name, text in generated.items():
            target = args.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        counts = json.loads(generated["anc/rtx104/e2_draft_profitability.json"])["validation"]
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write",
                      "complete_four_arm_cells": counts["complete_four_arm_cells"],
                      "arm_measurements_used": counts["arm_measurements_used"],
                      "warmups_excluded": counts["warmups_excluded"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValidationError, OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
