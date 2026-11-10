import copy
import json
import unittest
from pathlib import Path

from design_checks import check_admission, plan, validate


class DesignChecks(unittest.TestCase):
    def test_complete_design(self):
        result = validate(plan())
        self.assertTrue(result["passed"])
        self.assertEqual(result["b2_post_requests"], 2037)

    def test_deterministic(self):
        self.assertEqual(plan(), plan())

    def test_missing_measurement(self):
        p = plan()
        p["q32_panel"][0]["operations"].pop()
        with self.assertRaises(ValueError):
            validate(p)

    def test_mismatched_warm_input(self):
        p = plan()
        p["q32_panel"][0]["operations"][0]["slot"] = 99
        with self.assertRaises(ValueError):
            validate(p)

    def test_duplicate_id(self):
        p = plan()
        p["q32_panel"][1]["id"] = p["q32_panel"][0]["id"]
        with self.assertRaises(ValueError):
            validate(p)

    def test_missing_backend_arm(self):
        p = plan()
        w = p["q32_panel"][1]
        w["arm"] = "G"
        for o in w["operations"]:
            o["arm"] = "G"
        with self.assertRaises(ValueError):
            validate(p)

    def test_b2_unbalanced_warm_order(self):
        p = plan()
        for o, path in zip(p["b2"][4]["operations"][:4], "ABBA"):
            o["path"] = path
        with self.assertRaises(ValueError):
            validate(p)

    def test_b2_hidden_rows(self):
        p = plan()
        p["b2"][0]["operations"][0]["reserved_rows"] = 8
        with self.assertRaises(ValueError):
            validate(p)

    def test_template_blocks(self):
        data = json.loads(Path(__file__).with_name("ADMISSION.template.json").read_text())
        with self.assertRaises(ValueError):
            check_admission(data)

    @staticmethod
    def fake_shape_complete():
        """Only synthetic test data, never evidence or authorization."""
        d = json.loads(Path(__file__).with_name("ADMISSION.template.json").read_text())
        d.update(status="ADMITTED", gpu_execution_authorized=True, authorization_reference="SYNTHETIC TEST ONLY",
                 allocation_reference="SYNTHETIC TEST ONLY", phase="B2", source_commit="1" * 40,
                 allocation_start_utc="2099-01-01T00:00:00Z", last_new_worker_utc="2099-01-01T01:00:00Z",
                 delivery_deadline_utc="2099-01-01T02:00:00Z", guards_passed=True, qualification_passed=True,
                 resource_and_whole_panel_cost_passed=True, prospective_request_ceiling=2048,
                 prospective_row_ceiling=8000000, exact_incremental_requests=128,
                 exact_incremental_reserved_rows=33024, failure_closure_reserve_requests=8)
        for key in d:
            if key.endswith("_sha256"):
                d[key] = "1" * 64
        d["historical_8b"]["ledger_prefix_sha256"] = "1" * 64
        return d

    def test_shape_only_never_admits(self):
        r = check_admission(self.fake_shape_complete())
        self.assertFalse(r["execution_admitted_by_this_script"])

    def test_overbudget(self):
        d = self.fake_shape_complete()
        d["exact_incremental_requests"] = 140
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_deadline_order(self):
        d = self.fake_shape_complete()
        d["delivery_deadline_utc"] = d["allocation_start_utc"]
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_b2_silent_budget_increase(self):
        d = self.fake_shape_complete()
        d["prospective_request_ceiling"] = 2200
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_absent_qualification(self):
        d = copy.deepcopy(self.fake_shape_complete())
        d["qualification_passed"] = False
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_replica_counts_and_balance(self):
        r = validate(plan())
        self.assertEqual(r["request_counts"]["optional_second_device_panel"], 108)
        self.assertEqual(set(r["q32_replica_balance"]["positions"].values()), {6})

    def test_replica_no_root_substitution(self):
        p = plan()
        p["q32_replica"][0]["primary_root_slot"] = 11
        with self.assertRaises(ValueError):
            validate(p)

    def test_replica_missing_arm(self):
        p = plan()
        p["q32_replica"].pop()
        with self.assertRaises(ValueError):
            validate(p)

    def test_graph_probe_real_replay_slot_required(self):
        p = plan()
        p["graph_probe"][0]["operations"][1]["kind"] = "capture"
        with self.assertRaises(ValueError):
            validate(p)

    def test_graph_all_three_paths_required(self):
        p = plan()
        p["graph_probe"][0]["arm"] = "C"
        with self.assertRaises(ValueError):
            validate(p)

    def test_optional_never_autoactivates(self):
        p = plan()
        p["optional_status"]["second_device"] = "ACTIVE"
        with self.assertRaises(ValueError):
            validate(p)

    def fake_replica(self):
        d = self.fake_shape_complete()
        d.update(phase="Q32_REPLICA", exact_incremental_requests=108, prospective_request_ceiling=1346,
                 prospective_row_ceiling=2000000, failure_closure_reserve_requests=16,
                 selected_graph_policy="off", graph_policy_decision_sha256="1" * 64,
                 second_device_separately_authorized=True, replica_frozen_before_primary_results=True,
                 quiet_windows_nonoverlapping=True, own_device_R_sha256="2" * 64,
                 primary_device_binding_sha256="3" * 64, replica_device_binding_sha256="4" * 64)
        d["historical_q32"]["ledger_prefix_sha256"] = "1" * 64
        return d

    def test_replica_structural_pass_not_execution(self):
        self.assertFalse(check_admission(self.fake_replica())["execution_admitted_by_this_script"])

    def test_replica_no_separate_permission(self):
        d = self.fake_replica()
        d["second_device_separately_authorized"] = False
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_replica_overlapping_windows(self):
        d = self.fake_replica()
        d["quiet_windows_nonoverlapping"] = False
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_replica_same_device(self):
        d = self.fake_replica()
        d["replica_device_binding_sha256"] = d["primary_device_binding_sha256"]
        with self.assertRaises(ValueError):
            check_admission(d)

    def test_graph_off_registration_cannot_silently_switch_on(self):
        d = self.fake_replica()
        d["selected_graph_policy"] = "on"
        with self.assertRaises(ValueError):
            check_admission(d)


if __name__ == "__main__":
    unittest.main()
