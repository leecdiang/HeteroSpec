"""Risk-focused CPU tests; all observations below are fabricated test fixtures."""
import collections
import copy
import unittest
from analyze import analyze, check_records, summarize
from study import ARMS, make_plan, validate_plan


def receipts(plan, case_ids=None, means=None, one_session=False):
    case_ids = case_ids or {"q2-k256-v0", "q2-k256-v1"}
    means = means or {"PQ": 180., "QB_A": 100., "QB_B": 100., "QH_C": 120.}
    rows = []
    for t in plan["tasks"]:
        if t["stage"] != "confirm" or t["case_id"] not in case_ids:
            continue
        row = dict(task_id=t["task_id"], attempt_id="synthetic-"+t["task_id"],
                   plan_sha256=plan["plan_sha256"], observed_layout=t["layout"],
                   status="QUALIFIED", numerical_qualified=True, environment_qualified=True,
                   method="H1", cost_view="resident_graph",
                   session_id="one" if one_session else t["session"],
                   measured_us=[means[t["arm"]]]*t["measured_calls"],
                   host_binary_sha256="1"*64, runtime_manifest_sha256="2"*64,
                   execution_policy_sha256="3"*64, input_sha256="4"*64,
                   reference_sha256="5"*64, evidence_receipt_sha256="6"*64)
        rows.append(row)
    return rows


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = make_plan()

    def test_counts_and_no_gpu_state(self):
        p = self.plan
        self.assertEqual(p["scientific_state"], "NOT_RUN")
        self.assertEqual(len(p["cases"]), 64)
        self.assertEqual(len(p["factor_edges"]), 20)
        expected = {"reference/core": (296, 296), "reference/optional": (72, 72),
                    "qualification/core": (328, 11152), "qualification/optional": (72, 2448),
                    "aa_pilot/core": (192, 7296), "confirm/core": (1664, 63232),
                    "holdout/optional": (384, 14592)}
        self.assertEqual(set(p["counts"]), set(expected))
        for key, (hosts, calls) in expected.items():
            self.assertEqual(p["counts"][key], dict(native_hosts=hosts, graph_calls=calls))

    def test_order_balance_and_carryovers(self):
        self.assertTrue(validate_plan(self.plan))
        rows = [t for t in self.plan["tasks"] if t["stage"] == "confirm" and t["case_id"] == "q2-k256-v0"]
        positions = collections.Counter((t["arm"], t["position"]) for t in rows)
        self.assertEqual(set(positions.values()), {2})
        self.assertEqual(len(positions), 16)
        for t in rows:
            if t["arm"].startswith("QB_"):
                self.assertEqual(t["layout"], "QB")

    def test_aa_labels_balanced_within_method(self):
        for method in ("H0", "H1"):
            for cid in self.plan["aa_anchor_ids"]:
                rows = [t for t in self.plan["tasks"] if t["stage"] == "aa_pilot" and t["method"] == method and t["case_id"] == cid]
                self.assertEqual(len(rows), 12)
                self.assertEqual(set(collections.Counter((t["arm"], t["position"]) for t in rows).values()), {3})

    def test_fixed_factors_and_reproducibility(self):
        self.assertEqual(self.plan, make_plan())
        self.assertNotEqual(self.plan["plan_sha256"], make_plan(samples=50)["plan_sha256"])
        with self.assertRaises(ValueError):
            make_plan(samples=1000)
        bad = copy.deepcopy(self.plan)
        bad["cases"][0]["keys"] += 1
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_plan(bad)

    def test_fallback_method_requires_matching_full_qualification(self):
        p = make_plan(qualification_method="H0")
        full = [t for t in p["tasks"] if t["stage"] == "qualification" and t["method"] == "H0"]
        self.assertEqual(len(full), 64*3*2)
        self.assertNotEqual(p["plan_sha256"], self.plan["plan_sha256"])
        with self.assertRaises(ValueError):
            make_plan(qualification_method="unqualified")

    def test_holdout_uses_new_seeds_and_remains_optional(self):
        p = self.plan
        old = {c["seed"] for c in p["cases"] if c["cohort"] == "confirmation"}
        new = {c["seed"] for c in p["cases"] if c["cohort"] == "holdout"}
        self.assertFalse(old & new)
        ids = {c["case_id"] for c in p["cases"] if c["cohort"] == "holdout"}
        self.assertTrue(all(t["optional"] for t in p["tasks"] if t["case_id"] in ids))
        self.assertTrue(all("prediction_freeze" in t["requires"] for t in p["tasks"] if t["case_id"] in ids))


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = make_plan()

    def result(self, rows):
        return analyze(self.plan, rows, draws=100)

    def geometry(self, result):
        return next(g for g in result["geometry_summaries"] if g["geometry_id"] == "q2-k256")

    def test_known_ratio_direction_and_block_unit(self):
        result = self.result(receipts(self.plan))
        g = self.geometry(result)
        self.assertAlmostEqual(g["comparisons"]["QB_QH"]["ratio"], 100/120)
        self.assertAlmostEqual(g["comparisons"]["PQ_QB"]["ratio"], 1.8)
        self.assertEqual(g["comparisons"]["AA"]["n_blocks"], 8)
        self.assertEqual(g["comparisons"]["AA"]["sessions"], 2)
        self.assertEqual(g["QB_QH_decision"]["status"], "NUMERATOR_LOWER_COST")
        self.assertEqual(g["PQ_QB_decision"]["status"], "DENOMINATOR_LOWER_COST")

    def test_aa_detects_label_bias_and_swapped_baseline(self):
        rows = receipts(self.plan, means={"PQ": 180., "QB_A": 100., "QB_B": 125., "QH_C": 120.})
        g = self.geometry(self.result(rows))
        self.assertEqual(g["QB_QH_decision"]["status"], "UNRESOLVED_AT_TARGET_SCALE")
        self.assertFalse(g["QB_QH_decision"]["aa_inside_target_margin"])

    def test_q1_common_path_is_not_forced_to_gain(self):
        ids = {"q1-short-v0", "q1-short-v1"}
        result = self.result(receipts(self.plan, ids, dict.fromkeys(ARMS, 100.)))
        g = next(g for g in result["geometry_summaries"] if g["geometry_id"] == "q1-short")
        self.assertEqual(g["QB_QH_decision"]["status"], "UNRESOLVED_AT_TARGET_SCALE")

    def test_failed_arm_preserves_scope_and_does_not_pool_successes(self):
        rows = receipts(self.plan)
        rows[0].update(status="EXECUTION_FAILED", numerical_qualified=False, measured_us=[],
                       evidence_receipt_sha256=None, failure_reason="synthetic crash before final receipt")
        result = self.result(rows)
        self.assertEqual(sum(c["status"] == "EXECUTION_FAILED" for c in result["cells"]), 1)
        self.assertEqual(self.geometry(result)["comparisons"]["AA"]["n_blocks"], 7)
        self.assertEqual(self.geometry(result)["QB_QH_decision"]["status"], "DESCRIPTIVE_INCOMPLETE_OR_SINGLE_SESSION")
        panel = next(p for p in result["full_panel_summaries"] if p["stratum"] == "q>1")
        self.assertEqual(panel["comparisons"]["AA"]["n_blocks"], 0)
        self.assertEqual(panel["planned_geometries"], 24)

    def test_missing_realization_never_becomes_complete_geometry(self):
        result = self.result(receipts(self.plan, {"q2-k256-v0"}))
        self.assertEqual(self.geometry(result)["comparisons"]["AA"]["n_blocks"], 0)

    def test_single_actual_session_is_descriptive(self):
        g = self.geometry(self.result(receipts(self.plan, one_session=True)))
        self.assertEqual(g["QB_QH_decision"]["status"], "DESCRIPTIVE_INCOMPLETE_OR_SINGLE_SESSION")

    def test_reject_duplicate_and_unknown_task(self):
        rows = receipts(self.plan)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.result(rows+[rows[0]])
        rows[0]["task_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.result(rows)

    def test_reject_boolean_nonfinite_timer_and_wrong_call_count(self):
        for value in (True, float("nan"), float("inf"), -1, 0):
            rows = receipts(self.plan)
            rows[0]["measured_us"][0] = value
            with self.assertRaisesRegex(ValueError, "finite positive"):
                self.result(rows)
        rows = receipts(self.plan)
        rows[0]["measured_us"].pop()
        with self.assertRaisesRegex(ValueError, "call count"):
            self.result(rows)

    def test_reject_input_drift_and_mixed_runtime(self):
        for key in ("input_sha256", "reference_sha256", "runtime_manifest_sha256", "host_binary_sha256"):
            rows = receipts(self.plan)
            rows[-1][key] = "f"*64
            with self.assertRaises(ValueError):
                self.result(rows)

    def test_reject_relabelled_layout_wrong_view_plan_or_method(self):
        for key, value in (("observed_layout", "MQ"), ("cost_view", "kernel"), ("plan_sha256", "0"*64), ("method", "unknown")):
            rows = receipts(self.plan)
            rows[0][key] = value
            with self.assertRaises(ValueError):
                self.result(rows)

    def test_more_inner_calls_do_not_create_more_blocks(self):
        p50 = make_plan(samples=50)
        a = self.geometry(self.result(receipts(self.plan)))["comparisons"]["QB_QH"]
        b = self.geometry(analyze(p50, receipts(p50), draws=100))["comparisons"]["QB_QH"]
        self.assertEqual(a, b)

    def test_full_panel_preserves_geometry_weights_and_controls(self):
        ids = {c["case_id"] for c in self.plan["cases"] if c["cohort"] == "confirmation"}
        rows = receipts(self.plan, ids)
        taskmap = {t["task_id"]: t for t in self.plan["tasks"]}
        for row in rows:
            if taskmap[row["task_id"]]["geometry_id"].startswith("q1-"):
                row["measured_us"] = [100.] * len(row["measured_us"])
        result = self.result(rows)
        panel = next(p for p in result["full_panel_summaries"] if p["stratum"] == "q>1")
        control = next(p for p in result["full_panel_summaries"] if p["stratum"] == "q1")
        self.assertEqual(panel["planned_geometries"], 24)
        self.assertEqual(panel["comparisons"]["QB_QH"]["n_blocks"], 8)
        self.assertAlmostEqual(panel["comparisons"]["QB_QH"]["ratio"], 100/120)
        self.assertEqual(panel["QB_QH_decision"]["status"], "NUMERATOR_LOWER_COST")
        self.assertAlmostEqual(control["comparisons"]["QB_QH"]["ratio"], 1)
        self.assertEqual(control["QB_QH_decision"]["status"], "UNRESOLVED_AT_TARGET_SCALE")

    def test_factor_difference_of_log_ratios(self):
        ids = {f"q2-k{k}-v{v}" for k in (255, 256) for v in (0, 1)}
        rows = receipts(self.plan, ids)
        taskmap = {t["task_id"]: t for t in self.plan["tasks"]}
        for row in rows:
            t = taskmap[row["task_id"]]
            if t["geometry_id"] == "q2-k255" and t["arm"] == "QH_C":
                row["measured_us"] = [100.] * t["measured_calls"]
        result = self.result(rows)
        edge = next(e for e in result["factor_contrasts"] if e["base"] == "q2-k255" and e["changed"] == "q2-k256" and e["comparison"] == "QB_QH")
        self.assertAlmostEqual(edge["effect"]["ratio"], 100/120)


if __name__ == "__main__":
    unittest.main()
