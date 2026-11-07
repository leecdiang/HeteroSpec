"""CPU-only closeout planning and full-output/cost analysis. Never launches inference."""
from __future__ import annotations
import argparse, collections, hashlib, json, math, statistics, unicodedata
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate(design):
    assert design["status"] == "PROSPECTIVE_NOT_EXECUTED"
    assert len(design["base_head"]) == 40
    assert design["sampling"] == "native_greedy_seed123"
    assert design["context"] == 1024 and design["cap"] == 128
    assert design["kv"] == "F16" and design["flash_attention"] is False
    assert design["formal_retry_limit"] == 0 and design["positive_gain_admission"] is False
    assert design["task_count"] == 24 and design["domain_counts"] == {"MBPP": 12, "GSM8K": 12}
    assert design["sessions"] == 2 and design["rounds"] == 5
    assert len(design["conditions"]) == 5
    assert len({c["name"] for c in design["conditions"]}) == 5
    assert not design["cross_date_claim"] and not design["universal_preservation_claim"]
    n = len(design["families"]) * design["sessions"] * design["rounds"] * 5 * 24
    w = len(design["families"]) * design["sessions"] * design["rounds"] * 5
    assert n == design["budgets"]["formal_requests"] and w == design["budgets"]["formal_warmups"]
    assert design["budgets"]["engineering_units"] > 0
    mech = design["mechanism"]
    assert mech["profile_units_per_family"] == 128
    assert mech["profile_request_slots_per_family"] == 96
    assert set(mech["profile_modes"]) == {"baseline", "counts", "lite", "heavy"}
    assert mech["coefficient_source_mode"] == "lite" and mech["model_sealed_before_confirmation"] is True
    assert mech["fit_on_confirmation"] is False and mech["online_selector"] is False
    assert mech["profile_budget_included_in_engineering"] is True
    assert mech["profile_reserved_separately"] is True
    assert mech["validation_source_mode"] == design["formal_observation_mode"] == "counts"
    assert design["formal_observation"] == {"phase_timers": False, "heavy_capture": False, "etw": False, "added_sync": False}
    assert design["budgets"]["engineering_units"] == len(design["families"]) * (
        design["budgets"]["core_engineering_per_family"] + design["budgets"]["profile_units_per_family"])
    assert len(mech["calibration_task_ids"]) == len(set(mech["calibration_task_ids"])) == 6
    assert collections.Counter(t.split("/")[0] for t in mech["calibration_task_ids"]) == {"MBPP": 3, "GSM8K": 3}
    assert set(mech["profile_arms"]) <= {c["name"] for c in design["conditions"]}
    if design["platform"] == "RTX":
        assert design["ordinary_ub_grid"] == [1, 4, 32, 128, 512]
        assert {c["name"] for c in design["conditions"]} == {"R", "M0", "M3", "R_prod", "C3"}
        assert design["effective_logical_batch"] == 1024 and design["requested_logical_batch"] == 2048
    else:
        assert design["platform"] == "B570"
        assert design["required_physical_residency"] is True
        assert design["physical_residency_required_for"] == "fully_resident_claim_only"
        assert design["unknown_residency_blocks_request_study"] is False
        assert design["formal_etw_required"] is False and design["operational_memory_gate_required"] is True
        assert design["signed_dedicated_headroom_bytes"] == 536870912
        assert design["target_quantization"] == "Q6_K" and design["draft_quantization"] == "Q4_K_M"
        assert design["selected_k"] == 1
        assert {c["name"] for c in design["conditions"]} == {"R_stock", "R_prod", "M_match", "N_k1", "C_k1"}
    return {"status": "STATIC_PLAN_VALID", "formal": n, "warmups": w, "native_implementation": "NOT_COMPILED_OR_TESTED"}

def residency_gate(receipt):
    # A signed conclusion alone is insufficient. An independent decoder must bind these
    # normalized fields to retained ETL + allocation-map bytes on the execution host.
    required = {"status", "raw_etl_sha256", "decoder_sha256", "allocation_map_sha256",
                "worker_pids", "adapter_pci", "events_lost", "coverage_complete",
                "weight_kv_allocation_mapping_complete", "dedicated_segments_only",
                "paging_or_eviction_events", "unattributed_allocations",
                "minimum_signed_headroom_bytes", "covered_phases"}
    assert required <= receipt.keys(), "incomplete residency receipt"
    assert receipt["status"] == "OBSERVED_SCOPE_CERTIFIED"
    for key in ("raw_etl_sha256", "decoder_sha256", "allocation_map_sha256"):
        assert len(receipt[key]) == 64 and all(c in "0123456789abcdef" for c in receipt[key])
    assert receipt["worker_pids"] and receipt["adapter_pci"] == "8086:E20C"
    assert receipt["events_lost"] == 0 and receipt["coverage_complete"] is True
    assert receipt["weight_kv_allocation_mapping_complete"] is True
    assert receipt["dedicated_segments_only"] is True
    assert receipt["paging_or_eviction_events"] == 0 and receipt["unattributed_allocations"] == 0
    assert receipt["minimum_signed_headroom_bytes"] >= 536870912
    assert {"load", "prefill", "proposal", "verification", "rollback", "reset", "longest_prompt"} <= set(receipt["covered_phases"])
    return True

def operational_memory_gate(record):
    """Check normalized runtime evidence, not proof of physical residency."""
    m = record.get("operational_memory", {})
    return (type(m.get("minimum_signed_headroom_bytes")) is int
            and m["minimum_signed_headroom_bytes"] >= 536870912
            and m.get("all_weights_and_kv_gpu_placed") is True
            and m.get("allocation_failure") is False and m.get("cpu_offload") is False
            and m.get("known_paging_or_eviction") is False
            and m.get("same_worker_budget_identity_verified") is True
            and isinstance(m.get("raw_evidence_sha256"), str)
            and len(m["raw_evidence_sha256"]) == 64
            and all(c in "0123456789abcdef" for c in m["raw_evidence_sha256"]))

def select_ordinary(rows, design):
    """RTX discovery only: complete 12-task/two-repeat ordinary costs, no confirmation."""
    assert design["platform"] == "RTX"
    result = {}
    for family in design["families"]:
        candidates = []
        for ub in design["ordinary_ub_grid"]:
            subset = [r for r in rows if r["family"] == family and r["ub"] == ub]
            keys = {(r["task"], r["repeat"]) for r in subset}
            valid = (len(subset) == len(keys) == 24 and len({r["task"] for r in subset}) == 12
                     and all(r["phase"] == "exposed_engineering" and r["complete_raw_equal"] is True
                             and r["contract_valid"] is True and r["reference_stable"] is True
                             and math.isfinite(r["wall_ms"]) and r["wall_ms"] > 0 for r in subset))
            if not valid:
                continue
            logs = [math.log(r["wall_ms"]) for r in subset]
            candidates.append((statistics.mean(logs), ub))
        assert candidates, "no complete reference-equivalent ordinary candidate"
        result[family] = min(candidates)[1]
    return result

def normalized_text(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

def cohort_parity(domain, description):
    return int(hashlib.sha256(("heterospec-final-closeout-v1|" + domain + "|" + normalized_text(description)).encode()).hexdigest(), 16) % 2

def schedule(design, inputs, ordinary=None):
    validate(design)
    tasks = inputs["tasks"]
    assert len(tasks) == 24 and len({t["id"] for t in tasks}) == 24
    assert not (set(design["mandatory_excluded_ids"]) & {t["id"] for t in tasks})
    expected_parity = 0 if design["platform"] == "RTX" else 1
    for task in tasks:
        assert cohort_parity(task["domain"], task["description"]) == expected_parity, "other platform owns task bucket"
        for field in ("description", "raw_prompt"):
            if field in task:
                fingerprint = hashlib.sha256(normalized_text(task[field]).encode()).hexdigest()
                assert fingerprint not in design["mandatory_excluded_text_sha256"], "historically exposed description"
    assert collections.Counter(t["domain"] for t in tasks) == design["domain_counts"]
    assert inputs["history_audit"]["completed"] is True
    assert inputs["history_audit"]["by_id_and_description"] is True
    assert inputs["history_audit"]["unknown_hosts_disclosed"] is True
    assert inputs["history_audit"]["training_unseen_claim"] is False
    assert not (set(inputs["history_audit"]["excluded_ids"]) & {t["id"] for t in tasks})
    assert len(inputs["history_audit"]["evidence_sha256"]) == 64
    assert set(inputs["families"]) == set(design["families"])
    conditions = []
    blocks = []
    for family in design["families"]:
        ft = inputs["families"][family]
        assert {t["id"] for t in ft} == {t["id"] for t in tasks}
        assert len(ft) == 24
        for t in ft:
            assert t["cap"] == 128 and 0 < len(t["prompt_ids"]) <= 768
            assert all(type(x) is int and x >= 0 for x in t["prompt_ids"])
            assert len(t["prompt_ids"]) + t["cap"] <= 1024
        fc = []
        for raw in design["conditions"]:
            c = dict(raw)
            if c.get("prefill_ub") == "SELECTED_ORDINARY":
                assert ordinary and ordinary[family] in design["ordinary_ub_grid"]
                c["prefill_ub"] = ordinary[family]
                if c.get("continuation_ub") == "SELECTED_ORDINARY":
                    c["continuation_ub"] = ordinary[family]
            fc.append(c)
            conditions.append({"family": family, **c})
        # Five Latin rows; second session reverses each row. Every arm occupies
        # every block position once per session; no outcome-dependent order.
        for session in range(2):
            for rnd in range(5):
                order = fc[rnd:] + fc[:rnd]
                if session == 1:
                    order = list(reversed(order))
                for position, c in enumerate(order):
                    ordered = sorted(ft, key=lambda t: hashlib.sha256(
                        (design["study_id"] + "|" + family + "|" + str(session) + "|" + str(rnd) + "|" + t["id"]).encode()).hexdigest())
                    slots = [{"slot": family + "/s" + str(session) + "/r" + str(rnd) + "/" + c["name"] + "|" + t["id"],
                              "task": t["id"], "input_sha256": digest(t)} for t in ordered]
                    blocks.append({"family": family, "session": session, "round": rnd,
                                   "position": position, "condition": c, "slots": slots,
                                   "warmup": "ONE_FIXED_SYNTHETIC_CAP128_BEFORE_BLOCK"})
    blocks.sort(key=lambda b: (b["session"], design["families"].index(b["family"]) if b["session"] == 0 else -design["families"].index(b["family"]), b["round"], b["position"]))
    keys = [s["slot"] for b in blocks for s in b["slots"]]
    assert len(keys) == len(set(keys)) == design["budgets"]["formal_requests"]
    return {"study_id": design["study_id"], "design_sha256": digest(design),
            "input_sha256": digest(inputs), "conditions": conditions, "blocks": blocks,
            "planned": len(keys), "warmups": len(blocks), "ordinary_selection": ordinary,
            "status": "PLAN_ONLY_REQUIRES_F0B_REMOTE_BYTE_VERIFICATION"}

def output_valid(record, cap, eog):
    o = record["output"]
    ids = o["ids"]
    return (isinstance(ids, list) and 0 < len(ids) <= cap
            and all(type(i) is int and i >= 0 for i in ids)
            and o["length"] == len(ids) and o["terminal_id"] == ids[-1]
            and len(o["eog_flags"]) == len(ids)
            and all(type(v) is bool for v in o["eog_flags"])
            and o["eog_flags"] == [i in eog for i in ids]
            and not any(o["eog_flags"][:-1])
            and ((ids[-1] in eog and o["stop_reason"] == "EOG")
                 or (ids[-1] not in eog and len(ids) == cap and o["stop_reason"] == "CAP"))
            and o.get("cached_tokens") == 0 and o.get("truncated") is False)

def signature(record):
    o = record["output"]
    return (o["ids"], o["eog_flags"], o["length"], o["terminal_id"], o["stop_reason"])

def analyse(design, plan, inputs, records, freeze, residency=None):
    validate(design)
    assert plan["design_sha256"] == digest(design) and plan["input_sha256"] == digest(inputs)
    assert len(freeze["commit"]) == 40 and freeze["actual_remote_blobs_verified"] is True
    assert freeze["plan_sha256"] == digest(plan) and freeze["input_sha256"] == digest(inputs)
    assert freeze["before_first_formal_forward"] is True
    expected = {s["slot"]: (b, s) for b in plan["blocks"] for s in b["slots"]}
    parsed = {}
    for r in records:
        assert r["slot"] in expected and r["slot"] not in parsed, "unknown or duplicate paid slot"
        assert r["phase"] == "formal" and r["warmup"] is False
        b, s = expected[r["slot"]]
        assert r["freeze_commit"] == freeze["commit"] and r["input_sha256"] == s["input_sha256"]
        assert r["family"] == b["family"] and r["condition"] == b["condition"]["name"]
        assert r["session"] == b["session"] and r["round"] == b["round"] and r["task"] == s["task"]
        if r["status"] == "COMPLETED":
            assert r["runtime_identity_verified"] is True
            assert r["measurement_mode"] == design["formal_observation_mode"]
            assert r["observation"] == design["formal_observation"], "profiler differs from primary channel"
            assert r["actual_condition"] == b["condition"], "runtime differs from frozen arm"
            assert math.isfinite(r["wall_ms"]) and r["wall_ms"] > 0
        parsed[r["slot"]] = r
    allowed_memory = True
    if design["platform"] == "B570":
        try:
            allowed_memory = residency_gate(residency or {})
            if allowed_memory:
                completed = [r for r in parsed.values() if r["status"] == "COMPLETED"]
                allowed_memory = all(r.get("worker_pid") in residency["worker_pids"]
                                     and r.get("adapter_pci") == "8086:E20C"
                                     and r.get("residency_receipt_sha256") == digest(residency) for r in completed)
        except (AssertionError, KeyError, TypeError):
            allowed_memory = False
    result = {}
    for family in design["families"]:
        eog = set(design["assets"][family]["eog"])
        tids = [t["id"] for t in inputs["tasks"]]
        family_rows = {k: v for k, v in parsed.items() if v["family"] == family and v["status"] == "COMPLETED"}
        qual, medians, refs = {}, {}, {}
        refname = "R" if design["platform"] == "RTX" else "R_stock"
        for tid in tids:
            refs[tid] = [r for r in family_rows.values() if r["task"] == tid and r["condition"] == refname]
        reference_ok = all(len(rows) == 10 and all(output_valid(r, 128, eog) for r in rows)
                           and all(signature(r) == signature(rows[0]) for r in rows) for rows in refs.values())
        for c in design["conditions"]:
            name = c["name"]
            rows = [r for r in family_rows.values() if r["condition"] == name]
            valid_rows = [r for r in rows if output_valid(r, 128, eog)]
            mismatches = [r["slot"] for r in valid_rows if refs[r["task"]]
                          and any(signature(r) != signature(q) for q in refs[r["task"]])]
            stable = all(len(rr := [r for r in rows if r["task"] == tid]) == 10
                         and all(signature(r) == signature(rr[0]) for r in rr) for tid in tids)
            native_ok = reference_ok and len(rows) == len(valid_rows) == 240 and stable and not mismatches
            operational_ok = (all(operational_memory_gate(r) for r in rows)
                              if design["platform"] == "B570" else True)
            request_ok = bool(native_ok and operational_ok)
            qual[name] = {"complete": len(rows), "planned": 240, "native_qualified": bool(native_ok),
                          "physical_residency_qualified": allowed_memory if design["platform"] == "B570" else None,
                          "operational_memory_qualified": operational_ok if design["platform"] == "B570" else None,
                          "request_cost_qualified": request_ok,
                          "qualified": bool(request_ok and allowed_memory), "mismatches": mismatches}
            for sess in range(2):
                for tid in tids:
                    times = [r["wall_ms"] for r in rows if r["session"] == sess and r["task"] == tid]
                    medians[(sess, tid, name)] = statistics.median(times) if len(times) == 5 else None
        comparisons = []
        for base, cand in design["comparisons"]:
            ss, by_task = [], collections.defaultdict(list)
            for sess in range(2):
                logs = []
                for tid in tids:
                    a, z = medians[(sess, tid, base)], medians[(sess, tid, cand)]
                    if a is not None and z is not None:
                        v = math.log(a / z)
                        logs.append(v)
                        by_task[tid].append(v)
                ss.append(statistics.mean(logs) if len(logs) == 24 else None)
            ratio = math.exp(statistics.mean(ss)) if all(v is not None for v in ss) else None
            admissible = qual[base]["qualified"] and qual[cand]["qualified"]
            request_admissible = qual[base]["request_cost_qualified"] and qual[cand]["request_cost_qualified"]
            domain_effects = {}
            for domain in ("MBPP", "GSM8K"):
                dt = [t["id"] for t in inputs["tasks"] if t["domain"] == domain]
                vals = [statistics.mean(by_task[t]) for t in dt if len(by_task[t]) == 2]
                domain_effects[domain] = math.exp(statistics.mean(vals)) if len(vals) == 12 else None
            comparisons.append({"comparison": base + "/" + cand,
                                "request_qualified_ratio": ratio if request_admissible else None,
                                "domain_request_qualified_ratios": domain_effects if request_admissible else {k: None for k in domain_effects},
                                "request_cost_scope": "frozen counts channel; physical residency is a separate claim",
                                "domain_qualified_ratios": domain_effects if admissible else {k: None for k in domain_effects},
                                "qualified_ratio": ratio if admissible else None,
                                "diagnostic_complete_cost_ratio": ratio,
                                "session_ratios": [math.exp(v) if v is not None else None for v in ss],
                                "regressions": [t for t, values in by_task.items() if len(values) == 2 and statistics.mean(values) < 0],
                                "cross_date_interval": None})
        result[family] = {"complete_stable_reference": reference_ok, "qualification": qual, "comparisons": comparisons}
    return {"families": result, "planned": len(expected), "paid_records": len(parsed),
            "unexecuted_slots": sorted(set(expected) - set(parsed)),
            "physical_residency_gate": allowed_memory if design["platform"] == "B570" else None,
            "scope": "finite registered native outputs and measured request latency; no date-level inference"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--design", required=True)
    s = p.add_subparsers(dest="action", required=True)
    s.add_parser("validate")
    q = s.add_parser("schedule"); q.add_argument("--inputs", required=True); q.add_argument("--ordinary"); q.add_argument("--out", required=True)
    q = s.add_parser("analyse"); q.add_argument("--plan", required=True); q.add_argument("--inputs", required=True); q.add_argument("--records", required=True); q.add_argument("--freeze", required=True); q.add_argument("--residency"); q.add_argument("--out", required=True)
    q = s.add_parser("select-ordinary"); q.add_argument("--rows", required=True); q.add_argument("--out", required=True)
    a = p.parse_args(); d = read(a.design)
    if a.action == "validate":
        result = validate(d)
    elif a.action == "schedule":
        result = schedule(d, read(a.inputs), read(a.ordinary) if a.ordinary else None)
    elif a.action == "select-ordinary":
        result = select_ordinary(read(a.rows), d)
    else:
        result = analyse(d, read(a.plan), read(a.inputs), read(a.records), read(a.freeze), read(a.residency) if a.residency else None)
    if hasattr(a, "out"):
        Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result if a.action == "validate" else {"status": "CPU_COMPLETE", "output": a.out}, ensure_ascii=False))
if __name__ == "__main__":
    main()

