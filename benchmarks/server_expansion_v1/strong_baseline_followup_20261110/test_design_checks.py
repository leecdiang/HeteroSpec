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


if __name__ == "__main__":
    unittest.main()
