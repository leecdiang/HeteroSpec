"""CPU paired analysis of independently verified host receipts.

This checks the compact input contract, not device bytes, process cleanup or raw
archive authenticity. The RTX collector/auditor must supply those qualifications.
Intervals and the A/A-adjusted screen are descriptive, not a calibrated 95% test.
"""
import argparse
import collections
import json
import math
from pathlib import Path
import random
import re
import statistics as st
from study import ARMS, LAYOUT, digest, validate_plan

PAIR_ARMS = {"AA": ("QB_A", "QB_B"), "QB_QH": ("QB_A", "QH_C"),
             "QB_QH_alt": ("QB_B", "QH_C"), "PQ_QB": ("PQ", "QB_A"),
             "PQ_QB_alt": ("PQ", "QB_B")}
HASH_FIELDS = ("host_binary_sha256", "runtime_manifest_sha256", "execution_policy_sha256",
               "input_sha256", "reference_sha256", "evidence_receipt_sha256")
COHORT = ("method", "host_binary_sha256", "runtime_manifest_sha256", "execution_policy_sha256")


def check_records(plan, records):
    tasks = {t["task_id"]: t for t in plan["tasks"]}
    seen, attempts = set(), set()
    observed = {}
    for row in records:
        tid = row.get("task_id")
        if tid not in tasks or tid in seen:
            raise ValueError("unknown or duplicate task_id; select attempts prospectively, never best-of-retry")
        seen.add(tid)
        if not row.get("attempt_id") or row["attempt_id"] in attempts:
            raise ValueError("missing or duplicate attempt identity")
        attempts.add(row["attempt_id"])
        task = tasks[tid]
        if task["stage"] not in ("aa_pilot", "confirm", "holdout"):
            raise ValueError("analysis input is timing receipts only, not qualification/reference captures")
        if row.get("plan_sha256") != plan["plan_sha256"]:
            raise ValueError("receipt does not bind the supplied plan")
        if row.get("observed_layout") != task["layout"]:
            raise ValueError("actual mapping differs from the planned arm")
        if row.get("method") not in ("H0", "H1", "H2") or (task["method"] != "SELECTED" and row["method"] != task["method"]):
            raise ValueError("measurement-method identity mismatch")
        if row.get("cost_view") != "resident_graph":
            raise ValueError("primary analysis accepts only completed resident_graph; other views remain separate")
        for key in ("numerical_qualified", "environment_qualified"):
            if type(row.get(key)) is not bool:
                raise ValueError(f"{key} must be a genuine boolean")
        if not isinstance(row.get("session_id"), str) or not row["session_id"]:
            raise ValueError("actual acquisition session identity missing")
        for key in HASH_FIELDS:
            value = row.get(key)
            if value is None and row.get("status") != "QUALIFIED" and row.get("failure_reason"):
                continue  # Failed attempts may legitimately lack final evidence.
            if not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                raise ValueError(f"invalid/missing {key}")
        values = row.get("measured_us")
        if not isinstance(values, list) or any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values):
            raise ValueError("measured_us must contain only finite positive observations")
        good = row["status"] == "QUALIFIED" and row["numerical_qualified"] and row["environment_qualified"]
        if row["status"] == "QUALIFIED" and (not row["numerical_qualified"] or len(values) != task["measured_calls"]):
            raise ValueError("qualified host has bad numerical status or wrong measured-call count")
        if row["status"] not in ("QUALIFIED", "NUMERICAL_FAILURE", "ENVIRONMENT_INVALID", "EXECUTION_FAILED"):
            raise ValueError("unknown host status")
        observed[tid] = dict(row, task=task, eligible=good, host_mean_us=st.mean(values) if good else None)
    return observed


def paired(a, b, block, session):
    return dict(block=block, session=session, log_ratio=math.log(a / b), difference_us=a-b)


def summarize(pairs, draws=4000):
    if not pairs:
        return dict(n_blocks=0, sessions=0, ratio=None, difference_us=None, log_interval=None,
                    difference_interval=None, ratio_interval=None, leave_one_block_out=[], pairs=[])
    pairs = sorted(pairs, key=lambda x: x["block"])
    if len({p["block"] for p in pairs}) != len(pairs):
        raise ValueError("multiple observations for one acquisition block")
    logs = [p["log_ratio"] for p in pairs]
    diffs = [p["difference_us"] for p in pairs]
    strata = collections.defaultdict(list)
    for i, pair in enumerate(pairs):
        strata[pair["session"]].append(i)
    result = dict(n_blocks=len(pairs), sessions=len(strata), ratio=math.exp(st.mean(logs)),
                  difference_us=st.mean(diffs), log_interval=None, difference_interval=None,
                  ratio_interval=None, leave_one_block_out=[math.exp(st.mean(logs[:i]+logs[i+1:]))
                  for i in range(len(logs))] if len(logs)>1 else [], pairs=pairs)
    if len(pairs) >= 4:
        rng = random.Random(20261018)
        resampled_log, resampled_diff = [], []
        # Retain session composition and resample whole blocks, never inner calls.
        for _ in range(draws):
            chosen = [i for key in sorted(strata) for i in rng.choices(strata[key], k=len(strata[key]))]
            resampled_log.append(st.mean(logs[i] for i in chosen))
            resampled_diff.append(st.mean(diffs[i] for i in chosen))
        def interval(values):
            values = sorted(values)
            return [values[max(0, math.ceil(.025*len(values))-1)], values[math.ceil(.975*len(values))-1]]
        result["log_interval"] = interval(resampled_log)
        result["difference_interval"] = interval(resampled_diff)
        result["ratio_interval"] = [math.exp(x) for x in result["log_interval"]]
    return result


def screen(primary, alternate, aa, complete=True):
    if not complete or min(primary["n_blocks"], alternate["n_blocks"], aa["n_blocks"]) < 8 or min(primary["sessions"], alternate["sessions"], aa["sessions"]) < 2:
        return dict(status="DESCRIPTIVE_INCOMPLETE_OR_SINGLE_SESSION", heuristic=True)
    # This empirical guard uses the SAME estimand/unit as the candidate contrast.
    # Do not compare an aggregate effect against the variance of individual calls.
    noise_log = max(abs(x) for x in aa["log_interval"])
    noise_us = max(abs(x) for x in aa["difference_interval"])
    cut_log, cut_us = math.log(1.02) + noise_log, 1.0 + noise_us
    positive = all(s["log_interval"][0] > cut_log and s["difference_interval"][0] > cut_us for s in (primary, alternate))
    negative = all(s["log_interval"][1] < -cut_log and s["difference_interval"][1] < -cut_us for s in (primary, alternate))
    return dict(status="DENOMINATOR_LOWER_COST" if positive else "NUMERATOR_LOWER_COST" if negative else "UNRESOLVED_AT_TARGET_SCALE",
                heuristic=True, null_log_envelope=noise_log, null_us_envelope=noise_us,
                guarded_log_screen=cut_log, guarded_us_screen=cut_us,
                aa_inside_target_margin=noise_log <= math.log(1.02) and noise_us <= 1.0,
                caution="descriptive conservative guard,not a calibrated significance/equivalence test")


def average_pairs(groups):
    """Equal weight per listed input/realization inside each shared block."""
    if not groups:
        return []
    maps = [{p["block"]: p for p in group} for group in groups]
    common = set.intersection(*(set(m) for m in maps))
    out = []
    for block in sorted(common):
        values = [m[block] for m in maps]
        if len({p["session"] for p in values}) != 1:
            raise ValueError("one planned block spans different actual sessions")
        out.append(dict(block=block, session=values[0]["session"],
                        log_ratio=st.mean(p["log_ratio"] for p in values),
                        difference_us=st.mean(p["difference_us"] for p in values)))
    return out


def analyze(plan, records, draws=4000):
    validate_plan(plan)
    if type(draws) is not int or draws < 100:
        raise ValueError("at least 100 bootstrap draws required")
    observed = check_records(plan, records)
    cells, groups, cohorts, session_maps, case_identities = [], collections.defaultdict(dict), {}, {}, {}
    for t in plan["tasks"]:
        if t["stage"] not in ("aa_pilot", "confirm", "holdout"):
            continue
        row = observed.get(t["task_id"])
        cells.append(dict(task_id=t["task_id"], stage=t["stage"], case_id=t["case_id"], arm=t["arm"],
                          block=t["block"], position=t["position"],
                          status=row["status"] if row else "UNSTARTED", eligible=bool(row and row["eligible"])))
        if not row or not row["eligible"]:
            continue
        identity = (row["input_sha256"], row["reference_sha256"])
        if t["case_id"] in case_identities and case_identities[t["case_id"]] != identity:
            raise ValueError("input/reference identity changed across blocks or methods")
        case_identities[t["case_id"]] = identity
        cohort_key = (t["stage"], row["method"] if t["stage"] == "aa_pilot" else "SELECTED")
        token = tuple(row[k] for k in COHORT)
        if cohort_key in cohorts and cohorts[cohort_key] != token:
            raise ValueError("mixed source/runtime/method cohorts; analyze separate frozen revisions")
        cohorts[cohort_key] = token
        skey = (t["stage"], t["session"])
        if skey in session_maps and session_maps[skey] != row["session_id"]:
            raise ValueError("planned session spans multiple actual sessions; amend plan before collection")
        session_maps[skey] = row["session_id"]
        groupkey = (t["stage"], row["method"], t["case_id"], t["block"])
        if t["arm"] in groups[groupkey]:
            raise ValueError("duplicate arm in a paired block")
        groups[groupkey][t["arm"]] = row
    pairsets = collections.defaultdict(lambda: collections.defaultdict(list))
    missing_groups = []
    for (stage, method, case, block), arms in sorted(groups.items()):
        required = {"QB_A", "QB_B"} if stage == "aa_pilot" else set(ARMS)
        if set(arms) != required:
            missing_groups.append(dict(stage=stage, method=method, case_id=case, block=block, reason="incomplete eligible arm set"))
            continue
        identities = {(r["input_sha256"], r["reference_sha256"], r["session_id"]) for r in arms.values()}
        if len(identities) != 1:
            raise ValueError("paired arms have different input/reference/session identities")
        session = next(iter(arms.values()))["session_id"]
        for label, (a, b) in PAIR_ARMS.items():
            if a in arms and b in arms:
                pairsets[(stage, method, case)][label].append(paired(arms[a]["host_mean_us"], arms[b]["host_mean_us"], block, session))
    cases = {c["case_id"]: c for c in plan["cases"]}
    summaries = []
    for (stage, method, cid), pairs in sorted(pairsets.items()):
        stats = {k: summarize(v, draws) for k, v in pairs.items()}
        row = dict(stage=stage, method=method, case_id=cid, geometry_id=cases[cid]["geometry_id"], comparisons=stats)
        if stage != "aa_pilot":
            row["QB_QH_decision"] = screen(stats["QB_QH"], stats["QB_QH_alt"], stats["AA"])
            row["PQ_QB_decision"] = screen(stats["PQ_QB"], stats["PQ_QB_alt"], stats["AA"])
        summaries.append(row)
    geometry_rows, geometry_pairs, panel_rows = [], {}, []
    for stage in ("confirm", "holdout"):
        selected_method = next((k[1] for k in pairsets if k[0] == stage), None)
        if selected_method is None:
            continue
        expected = [c for c in plan["cases"] if c["cohort"] == ("confirmation" if stage == "confirm" else "holdout")]
        for gid in sorted({c["geometry_id"] for c in expected}):
            ids = [c["case_id"] for c in expected if c["geometry_id"] == gid]
            pairmaps = [pairsets.get((stage, selected_method, cid), {}) for cid in ids]
            pairs = {label: average_pairs([m.get(label, []) for m in pairmaps]) for label in PAIR_ARMS}
            stats = {k: summarize(v, draws) for k, v in pairs.items()}
            geometry_pairs[stage, gid] = pairs
            geometry_rows.append(dict(stage=stage, geometry_id=gid, expected_realizations=len(ids),
                                      comparisons=stats,
                                      QB_QH_decision=screen(stats["QB_QH"], stats["QB_QH_alt"], stats["AA"]),
                                      PQ_QB_decision=screen(stats["PQ_QB"], stats["PQ_QB_alt"], stats["AA"])))
        for subset in ("q>1", "q1"):
            ids = sorted({c["geometry_id"] for c in expected if (c["q"] > 1 if subset == "q>1" else c["q"] == 1)})
            if not ids:
                continue
            # Full planned panel only: do not silently drop failed geometries.
            pairs = {label: average_pairs([geometry_pairs[stage, gid][label] for gid in ids]) for label in PAIR_ARMS}
            stats = {k: summarize(v, draws) for k, v in pairs.items()}
            panel_rows.append(dict(stage=stage, stratum=subset, planned_geometries=len(ids),
                                   comparisons=stats,
                                   QB_QH_decision=screen(stats["QB_QH"], stats["QB_QH_alt"], stats["AA"]),
                                   PQ_QB_decision=screen(stats["PQ_QB"], stats["PQ_QB_alt"], stats["AA"])))
    edges = []
    for edge in plan["factor_edges"]:
        for label in ("QB_QH", "PQ_QB"):
            a = {p["block"]: p for p in geometry_pairs.get(("confirm", edge["base"]), {}).get(label, [])}
            b = {p["block"]: p for p in geometry_pairs.get(("confirm", edge["changed"]), {}).get(label, [])}
            values = []
            for block in sorted(a.keys() & b.keys()):
                if a[block]["session"] != b[block]["session"]:
                    raise ValueError("factor contrast spans sessions within one block")
                values.append(dict(block=block, session=a[block]["session"],
                                   log_ratio=b[block]["log_ratio"]-a[block]["log_ratio"],
                                   difference_us=b[block]["difference_us"]-a[block]["difference_us"]))
            edges.append(dict(edge, comparison=label, effect=summarize(values, draws),
                              scope="difference of mapping log-cost contrasts;exploratory,multiple comparisons"))
    return dict(schema_version=1, plan_sha256=plan["plan_sha256"], observed_hosts=len(observed),
                cells=cells, missing_groups=missing_groups, case_summaries=summaries,
                geometry_summaries=geometry_rows, full_panel_summaries=panel_rows, factor_contrasts=edges,
                raw_authentication="NOT_PERFORMED_BY_THIS_COMPACT_ANALYZER",
                inference="stratified block bootstrap is descriptive;two sessions are not population replication",
                practical_screen="both original and swapped-QB comparisons must exceed practical+same-unit A/A envelope",
                hardware_decision="NOT_INFERRED_FROM_TIMING_ALONE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=4000)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in args.observations.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = analyze(plan, records, args.draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(result, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
    print(json.dumps(dict(observed_hosts=result["observed_hosts"], panel=result["full_panel_summaries"])))


if __name__ == "__main__":
    main()
