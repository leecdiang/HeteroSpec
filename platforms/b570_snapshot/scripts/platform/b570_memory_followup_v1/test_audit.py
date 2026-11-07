"""Refuse misleading interpretations of actual PR86 records; no GPU calls."""
import copy
import json
import unittest
from audit import DOC, historical_observation, memory_sample, run_audit, validate_policy


def rows(name):
    return [json.loads(line) for line in (DOC / "historical_pr86" / name).read_text().splitlines()]


class HistoricalMemoryEvidence(unittest.TestCase):
    def setUp(self):
        self.rows = rows("LLAMA_Q4_UB32_OUT1_LOAD.stdout.jsonl")
        self.loaded = next(r for r in self.rows if r.get("point") == "LOADED")

    def test_actual_loaded_not_unloaded_and_never_runtime_approval(self):
        result = historical_observation(self.rows)
        self.assertEqual(result["headroom_bytes"], 219439104)
        self.assertTrue(result["loaded_sample_meets_128_mib_counterfactual"])
        self.assertFalse(result["loaded_sample_meets_512_mib"])
        self.assertFalse(result["allow_forward"])
        self.assertFalse(result["batched_k3_capacity_certified"])
        self.assertFalse(result["engineering_peak_measured"])
        self.assertEqual(result["target_outputs_capacity"], 1)

    def test_unloaded_sample_refused(self):
        unloaded = next(r for r in self.rows if r.get("point") == "UNLOADED")
        with self.assertRaises(ValueError):
            memory_sample(unloaded, self.loaded["pid"])

    def test_other_process_usage_refused(self):
        forged = copy.deepcopy(self.loaded)
        forged["pid"] += 1
        with self.assertRaises(ValueError):
            memory_sample(forged, self.loaded["pid"])

    def test_system_heap_cannot_fund_headroom(self):
        forged = copy.deepcopy(self.loaded)
        forged["heaps"][1]["device_local"] = True
        with self.assertRaises(ValueError):
            memory_sample(forged, self.loaded["pid"])

    def test_shared_free_added_to_scalar_refused(self):
        forged = copy.deepcopy(self.loaded)
        forged["device_local_headroom_bytes"] += (
            forged["heaps"][1]["budget_bytes"] - forged["heaps"][1]["usage_bytes"])
        with self.assertRaises(ValueError):
            memory_sample(forged, self.loaded["pid"])

    def test_negative_signed_budget_not_rescued_by_lower_threshold(self):
        source = rows("LLAMA_Q8_LOGFIX_UB32_OUT1_LOAD.stdout.jsonl")
        result = historical_observation(source)
        self.assertEqual(result["headroom_bytes"], -218660902)
        self.assertFalse(result["complete_dual_context_loaded"])
        self.assertFalse(result["loaded_sample_meets_128_mib_counterfactual"])
        bad = copy.deepcopy(next(r for r in source if r.get("point") == "DRAFT_WEIGHTS"))
        bad["device_local_headroom_bytes"] %= 2 ** 64
        with self.assertRaises(ValueError):
            memory_sample(bad, bad["pid"])

    def test_hidden_forward_counter_refused(self):
        forged = copy.deepcopy(self.loaded)
        forged["decode_calls"] = 1
        with self.assertRaises(ValueError):
            memory_sample(forged, self.loaded["pid"])

    def test_exact_historical_bindings(self):
        result = run_audit()
        self.assertEqual(result["q6_file_bytes_saved"], 1944764416)
        self.assertFalse(result["allow_forward"])


class ProspectiveProfileGuards(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((DOC / "POLICY.json").read_text())
        self.assets = json.loads((DOC / "ASSETS.json").read_text())

    def test_cross_precision_baseline_relabel_refused(self):
        self.policy["profiles"]["STANDARD_Q6"]["target_asset"] = "Llama_target_Q8_0"
        with self.assertRaises(ValueError):
            validate_policy(self.policy, self.assets)

    def test_positive_only_confirmation_refused(self):
        self.policy["confirmation_admission_requires_positive_gain"] = True
        with self.assertRaises(ValueError):
            validate_policy(self.policy, self.assets)

    def test_ever_lower_threshold_refused(self):
        self.policy["profiles"]["TIGHT_Q8"]["dedicated_headroom_min_bytes"] //= 2
        with self.assertRaises(ValueError):
            validate_policy(self.policy, self.assets)

    def test_unknown_residency_not_qualified(self):
        self.policy["qualified_ratio_on_residency_unknown"] = 1.2
        with self.assertRaises(ValueError):
            validate_policy(self.policy, self.assets)


if __name__ == "__main__":
    unittest.main()
