"""Synthetic CPU fixtures only; not scientific inference evidence."""
import copy, json, unittest
from pathlib import Path
from closeout import validate, schedule, analyse, digest, cohort_parity, select_ordinary, residency_gate

ROOT = Path(__file__).resolve().parents[3]
PLATFORM = "rtx" if "rtx_evidence_closeout" in str(Path(__file__).parent) else "b570"
D = json.loads((ROOT / ("docs/experiments/" + PLATFORM + "_evidence_closeout_20261011/DESIGN.json")).read_text())

def inputs():
    tasks = []
    parity = 0 if PLATFORM == "rtx" else 1
    for domain in ("MBPP", "GSM8K"):
        j = 10000
        for i in range(12):
            while cohort_parity(domain, "CPU FIXTURE " + str(j)) != parity:
                j += 1
            tasks.append({"id": domain + "/fixture/" + str(j), "domain": domain, "description": "CPU FIXTURE " + str(j)})
            j += 1
    return {"tasks": tasks, "families": {f: [{"id": t["id"], "prompt_ids": [8, 9], "cap": 128}
                                             for t in tasks] for f in D["families"]},
            "history_audit": {"completed": True, "by_id_and_description": True,
                              "unknown_hosts_disclosed": True, "training_unseen_claim": False,
                              "excluded_ids": D["mandatory_excluded_ids"], "evidence_sha256": "f" * 64}}

def fixture():
    inp = inputs()
    p = schedule(D, inp, {f: 4 for f in D["families"]} if PLATFORM == "rtx" else None)
    freeze = {"commit": "a" * 40, "actual_remote_blobs_verified": True, "before_first_formal_forward": True,
              "plan_sha256": digest(p), "input_sha256": digest(inp)}
    records = []
    for block in p["blocks"]:
        for slot in block["slots"]:
            records.append({"slot": slot["slot"], "family": block["family"],
                            "condition": block["condition"]["name"], "task": slot["task"],
                            "session": block["session"], "round": block["round"],
                            "phase": "formal", "warmup": False, "freeze_commit": freeze["commit"],
                            "input_sha256": slot["input_sha256"], "status": "COMPLETED",
                            "wall_ms": 100.0, "runtime_identity_verified": True,
                            "measurement_mode": "counts", "observation": dict(D["formal_observation"]),
                            "operational_memory": {"minimum_signed_headroom_bytes": 536870912,
                                "all_weights_and_kv_gpu_placed": True, "allocation_failure": False,
                                "cpu_offload": False, "known_paging_or_eviction": False,
                                "same_worker_budget_identity_verified": True, "raw_evidence_sha256": "e"*64},
                            "actual_condition": block["condition"],
                            "output": {"ids": [3] * 128, "eog_flags": [False] * 128,
                                       "length": 128, "terminal_id": 3, "stop_reason": "CAP",
                                       "cached_tokens": 0, "truncated": False}})
    return inp, p, freeze, records

class GuardTests(unittest.TestCase):
    def test_primary_observer_cannot_include_phase_timers_or_etw(self):
        for key in ("phase_timers", "heavy_capture", "etw", "added_sync"):
            i,p,f,rr=fixture();rr[0]["observation"][key]=True
            with self.assertRaises(AssertionError):analyse(D,p,i,rr,f)

    def test_unknown_residency_preserves_complete_request_comparison(self):
        i,p,f,rr=fixture();out=analyse(D,p,i,rr,f)
        pair=out["families"][D["families"][0]]["comparisons"][0]
        self.assertEqual(pair["request_qualified_ratio"],1.0)
        if PLATFORM=="b570":self.assertIsNone(pair["qualified_ratio"])

    def test_resource_failure_or_incomplete_output_still_blocks_request_ratio(self):
        i,p,f,rr=fixture();candidate="C3" if PLATFORM=="rtx" else "C_k1"
        r=next(z for z in rr if z["condition"]==candidate)
        if PLATFORM=="b570":r["operational_memory"]["minimum_signed_headroom_bytes"]=-1
        else:r["status"]="FAILED"
        out=analyse(D,p,i,rr,f)
        pair=out["families"][D["families"][0]]["comparisons"][0]
        self.assertIsNone(pair["request_qualified_ratio"])

    def test_budget_and_position_balance(self):
        inp, p, freeze, records = fixture()
        self.assertEqual(len(records), D["budgets"]["formal_requests"])
        for family in D["families"]:
            for session in range(2):
                for arm in D["conditions"]:
                    pos = [b["position"] for b in p["blocks"] if b["family"] == family
                           and b["session"] == session and b["condition"]["name"] == arm["name"]]
                    self.assertEqual(sorted(pos), [0, 1, 2, 3, 4])

    def test_duplicate_paid_slot_is_rejected(self):
        i, p, f, rr = fixture()
        with self.assertRaises(AssertionError):
            analyse(D, p, i, rr + [rr[0]], f)

    def test_missing_candidate_is_not_positive(self):
        i, p, f, rr = fixture()
        candidate = "C3" if PLATFORM == "rtx" else "C_k1"
        first = next(k for k, z in enumerate(rr) if z["condition"] == candidate)
        rr = [r for j, r in enumerate(rr) if j != first]
        out = analyse(D, p, i, rr, f)
        q = out["families"][D["families"][0]]["qualification"][candidate]
        self.assertFalse(q["qualified"])

    def test_raw_suffix_is_not_truncated_into_a_pass(self):
        i, p, f, rr = fixture()
        name = "C3" if PLATFORM == "rtx" else "C_k1"
        r = next(z for z in rr if z["condition"] == name)
        r["output"]["ids"].append(7); r["output"]["eog_flags"].append(False)
        r["output"]["length"] = 129; r["output"]["terminal_id"] = 7
        out = analyse(D, p, i, rr, f)
        self.assertFalse(out["families"][D["families"][0]]["qualification"][name]["native_qualified"])

    def test_divergent_arm_does_not_erase_unrelated_pair(self):
        i, p, f, rr = fixture()
        name = "M0" if PLATFORM == "rtx" else "N_k1"
        for r in rr:
            if r["condition"] == name:
                r["output"]["ids"][0] = 7
        out = analyse(D, p, i, rr, f)["families"][D["families"][0]]
        self.assertFalse(out["qualification"][name]["native_qualified"])
        pair = next(c for c in out["comparisons"] if c["comparison"] == ("M3/C3" if PLATFORM == "rtx" else "M_match/C_k1"))
        if PLATFORM == "rtx":
            self.assertAlmostEqual(pair["qualified_ratio"], 1)
        else:
            self.assertIsNone(pair["qualified_ratio"])

    def test_future_input_leak_is_rejected(self):
        i = inputs(); i["tasks"][0]["id"] = D["mandatory_excluded_ids"][0]
        with self.assertRaises(AssertionError):
            schedule(D, i, {f: 4 for f in D["families"]} if PLATFORM == "rtx" else None)

    def test_other_platform_bucket_is_rejected(self):
        i = inputs(); i["tasks"][0]["description"] = "WRONG BUCKET"
        while cohort_parity(i["tasks"][0]["domain"], i["tasks"][0]["description"]) == (0 if PLATFORM == "rtx" else 1):
            i["tasks"][0]["description"] += " X"
        with self.assertRaises(AssertionError):
            schedule(D, i, {f: 4 for f in D["families"]} if PLATFORM == "rtx" else None)

    def test_runtime_arm_drift_is_rejected(self):
        i, p, f, rr = fixture()
        rr[0]["actual_condition"] = dict(rr[0]["actual_condition"], prefill_ub=99)
        with self.assertRaises(AssertionError):
            analyse(D, p, i, rr, f)

    def test_post_forward_freeze_is_rejected(self):
        i, p, f, rr = fixture(); f["before_first_formal_forward"] = False
        with self.assertRaises(AssertionError):
            analyse(D, p, i, rr, f)

    def test_undefined_residency_or_negative_budget_cannot_pass(self):
        with self.assertRaises(AssertionError):
            residency_gate({"status": "OBSERVED_SCOPE_CERTIFIED"})
        receipt = {"status": "OBSERVED_SCOPE_CERTIFIED", "raw_etl_sha256": "b"*64,
                   "decoder_sha256": "c"*64, "allocation_map_sha256": "d"*64,
                   "worker_pids": [42], "adapter_pci": "8086:E20C", "events_lost": 0,
                   "coverage_complete": True, "weight_kv_allocation_mapping_complete": True,
                   "dedicated_segments_only": True, "paging_or_eviction_events": 0,
                   "unattributed_allocations": 0, "minimum_signed_headroom_bytes": 536870912,
                   "covered_phases": ["load","prefill","proposal","verification","rollback","reset","longest_prompt"]}
        self.assertTrue(residency_gate(receipt))  # schema fixture only, not a real certificate
        for field, bad in [("minimum_signed_headroom_bytes", -1), ("events_lost", 1),
                           ("weight_kv_allocation_mapping_complete", False)]:
            invalid = dict(receipt); invalid[field] = bad
            with self.assertRaises(AssertionError):residency_gate(invalid)
        i, p, f, rr = fixture()
        if PLATFORM == "b570":
            out = analyse(D, p, i, rr, f)
            self.assertTrue(all(c["qualified_ratio"] is None for c in out["families"]["Llama"]["comparisons"]))
            for row in rr:row.update(worker_pid=42, adapter_pci="8086:E20C", residency_receipt_sha256=digest(receipt))
            row = rr[0];row["worker_pid"] = 43
            out = analyse(D, p, i, rr, f, receipt)
            self.assertFalse(out["physical_residency_gate"])

    @unittest.skipUnless(PLATFORM == "rtx", "RTX ordinary selection only")
    def test_ordinary_selection_does_not_choose_a_fast_mismatch(self):
        rows = []
        for family in D["families"]:
            for ub in D["ordinary_ub_grid"]:
                for tid in range(12):
                    for repeat in range(2):
                        rows.append({"family": family, "ub": ub, "task": str(tid), "repeat": repeat,
                                     "phase": "exposed_engineering", "complete_raw_equal": ub != 512,
                                     "reference_stable": True, "contract_valid": True,
                                     "wall_ms": 0.001 if ub == 512 else 100 + ub})
        self.assertEqual(select_ordinary(rows, D), {f: 1 for f in D["families"]})
        rows[0]["phase"] = "confirmation"
        chosen = select_ordinary(rows, D)
        self.assertEqual(chosen[D["families"][0]], 4)

    def test_signed_headroom_plan_cannot_be_lowered(self):
        d = copy.deepcopy(D)
        if PLATFORM == "b570":
            d["signed_dedicated_headroom_bytes"] = 1
        else:
            d["ordinary_ub_grid"].append(1024)
        with self.assertRaises(AssertionError):
            validate(d)

if __name__ == "__main__":
    unittest.main()

