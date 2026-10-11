"""Recompute published evidence for planning. Does not recover raw inference archives."""
import argparse, collections, csv, hashlib, json, math, statistics
from pathlib import Path

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))

def rtx(root):
    src = root / "benchmarks/jsa_third_family_v1/RESULTS.json"
    x = load(src)
    assert x["planned"] == x["completed"] == 3456
    assert x["slot_statuses"] == {"COMPLETED": 3456}
    cases = x["native_case_diagnostics"]
    assert len(cases) == len({r["slot"] for r in cases}) == 3456
    assert len(x["ledger"]) == 3456 and all(r["status"] == "COMPLETED" for r in x["ledger"].values())
    assert all(r["contract_valid"] and math.isfinite(r["wall_ms"]) and r["wall_ms"] > 0 for r in cases)
    groups = collections.defaultdict(list)
    for r in cases:
        groups[(r["family"], r["session"], r["task"], r["condition"])].append(r["wall_ms"])
    assert len(groups) == 864 and all(len(v) == 4 for v in groups.values())
    costs = {k: statistics.median(v) for k, v in groups.items()}
    for r in x["task_costs"]:
        key = (r["family"], r["session"], r["task"], r["condition"])
        assert math.isclose(costs[key], r["resident_median_ms"], abs_tol=1e-9, rel_tol=1e-12)
    families = {}
    for family, v in x["families"].items():
        tids = sorted({r["task"] for r in cases if r["family"] == family})
        assert len(tids) == 24 and v["stable_complete_R"] is True
        checks = {}
        for c in v["comparisons"]:
            base, candidate = c["comparison"].split("/")
            effects = [statistics.mean(math.log(costs[(family, session, tid, base)] / costs[(family, session, tid, candidate)])
                                       for tid in tids) for session in range(2)]
            ratio = math.exp(statistics.mean(effects))
            assert math.isclose(ratio, c["diagnostic_complete_cost_ratio"], rel_tol=1e-12)
            allowed = v["qualification"][base]["qualified"] and v["qualification"][candidate]["qualified"]
            assert (c["qualified_ratio"] is not None) == bool(allowed)
            if allowed:
                assert math.isclose(ratio, c["qualified_ratio"], rel_tol=1e-12)
            regressions = sorted(tid for tid in tids if statistics.mean(
                math.log(costs[(family, ss, tid, base)] / costs[(family, ss, tid, candidate)]) for ss in range(2)) < 0)
            assert regressions == sorted(c["regressions"])
            assert c["six_date_95pct_CI"] is None and c["cross_date_positive_decision"] == "UNTESTED"
            checks[c["comparison"]] = {"qualified_ratio": c["qualified_ratio"], "sessions": [math.exp(z) for z in effects],
                                       "regressions": len(regressions), "domains": c["domain_qualified_ratios"]}
        q = v["qualification"]
        assert all(z["planned"] == z["completed"] == 192 for z in q.values())
        assert q["R"]["qualified"] and q["M3"]["qualified"] and q["C3_K3"]["qualified"] and not q["N"]["qualified"]
        unique_bad = {z["slot"].split("|")[-1] for z in q["N"]["mismatches"]}
        families[family] = {"comparisons": checks, "ordinary_speculation_divergent_requests": q["N"]["mismatch_count"],
                            "ordinary_speculation_divergent_tasks": len(unique_bad),
                            "reference_and_candidate_qualification": "READ_FROM_PINNED_EXPORT_NOT_RAW_ARRAY_REVALIDATION"}
    return {"status": "PUBLISHED_EXPORT_COST_RECOMPUTATION_PASS", "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "source_bytes": src.stat().st_size, "formal_requests": 3456, "task_session_arm_medians": 864,
            "comparisons_recomputed": 27, "families": families, "dates": x["dates_in_Asia_Shanghai"],
            "limitations": ["Recomputes from published per-request cost diagnostics, not restored raw token responses.",
                            "Qualification assertions checked at export level; prior native/raw restoration remains author evidence.",
                            "No independent-date confidence interval; all #84 inputs are now exposed."]}

def b570(root):
    base = root / "benchmarks/b570_memory_followup_v1"
    decision = load(base / "DECISION.json")
    eng = load(base / "STANDARD_Q6_ENGINEERING.json")
    with (base / "CANDIDATE_MATRIX.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    primary = [r for r in rows if r["profile"] == "STANDARD_Q6"]
    blocked = [r for r in rows if r["profile"] == "TIGHT_Q8"]
    assert len(primary) == 12 and len(blocked) == 6
    repaired = [r for r in primary if r["complete_raw_equal"] == "True"]
    assert len(repaired) == 6 and all(not r["qualified_ratio"] for r in rows)
    assert decision["state"] == "ENGINEERING_CLOSED_FORMAL_NOT_ADMITTED"
    assert decision["formal_requests"] == 0 and decision["physical_residency"] == "UNKNOWN"
    assert decision["new_generation_requests"] == 550 and decision["new_zero_forward_probes"] == 22
    chosen = next(r for r in primary if r["candidate_id"] == decision["diagnostic_ranked_first"])
    ratios = [float(chosen["ratio_repeat" + str(i) + "_diagnostic"]) for i in (1, 2)]
    assert ratios == decision["diagnostic_R_prod_C_repeats"]
    assert eng["R_prod_ub"] == 512 and eng["R_stock_ub"] == 128
    natural = eng["N_diagnostic"]["first_divergences"]
    assert len(natural) == 8 and len({r["task"] for r in natural}) == 4
    worker = (base / "native/worker.cpp").read_text(encoding="utf-8-sig")
    assert "all_target_continuation_rows_physical_UB1" in worker
    assert "llama_b570_pilot_bind_phase_ubatch(tgt.ctx,1)" in worker
    return {"status": "PUBLISHED_ENGINEERING_BOUNDARY_RECHECK_PASS", "formal_requests": 0,
            "generation_requests": 550, "zero_forward_probes": 22, "new_paid_units": 572,
            "raw_equal_candidates": 6, "raw_divergent_candidates": 6, "memory_blocked_candidates": 6,
            "diagnostic_first": decision["diagnostic_ranked_first"], "diagnostic_ratios": ratios,
            "diagnostic_cost_factors": [1 / r for r in ratios], "physical_residency": "UNKNOWN",
            "qualified_ratios": None, "natural_first_differences": 8, "natural_distinct_tasks": 4,
            "implementation_scope": "prefill selected UB; all target continuation physical UB1",
            "limitations": ["Does not restore CAS or independently revalidate raw IDs or physical allocations.",
                            "CSV and decision consistency is CPU evidence; diagnostic timings remain instrumented.",
                            "No claim that Vulkan allocation mapping proves physical residency."]}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--platform", choices=["RTX", "B570"], required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = rtx(a.root) if a.platform == "RTX" else b570(a.root)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "formal_requests")}, ensure_ascii=False))

