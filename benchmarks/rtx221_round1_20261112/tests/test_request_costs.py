import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("request_costs", Path(__file__).parents[1] / "request/costs.py")
costs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(costs)


def fixture():
    return {"request_id": "fixture", "arm": "control", "source_sha256": "a" * 64,
            "input_sha256": "b" * 64, "clock": "steady_clock_ns", "service": [100, 1100],
            "complete_endpoint": True,
            "spans": [{"category": "reset", "begin": 100, "end": 200},
                      {"category": "verify", "begin": 300, "end": 900},
                      {"category": "sync", "begin": 700, "end": 850},
                      {"category": "reconciliation", "begin": 920, "end": 1000}]}


class CostsTests(unittest.TestCase):
    def test_nested_sync_not_added_to_verify(self):
        r = costs.decompose(fixture())
        self.assertEqual(r["exclusive_ns"]["verify"], 450)
        self.assertEqual(r["exclusive_ns"]["sync"], 150)
        self.assertEqual(sum(r["exclusive_ns"].values()), 1000)

    def test_crossing_overlap_refused(self):
        f = fixture()
        f["spans"].append({"category": "planning", "begin": 600, "end": 950})
        with self.assertRaisesRegex(costs.CostError, "crossing overlapping"):
            costs.decompose(f)

    def test_gpu_clock_must_remain_separate(self):
        f = fixture()
        f["spans"][0]["clock"] = "cuda_event_ms"
        with self.assertRaisesRegex(costs.CostError, "mixed clock"):
            costs.decompose(f)

    def test_different_request_cannot_pair(self):
        a = costs.decompose(fixture())
        b = copy.deepcopy(a)
        b["request_id"] = "other-panel"
        with self.assertRaisesRegex(costs.CostError, "different requests"):
            costs.paired_service(a, b)

    def test_incomplete_endpoint_cannot_establish_service_value(self):
        a = costs.decompose(fixture())
        b = copy.deepcopy(a)
        self.assertTrue(a["complete_endpoint_self_declared"])
        self.assertEqual(a["endpoint_qualification"], "UNVERIFIED")
        with self.assertRaisesRegex(costs.CostError, "independent endpoint proof"):
            costs.paired_service(a, b)

    def test_missing_guard_refused_despite_self_declared_complete(self):
        a = costs.decompose(fixture())
        definition = {"required_categories": ["reset", "guard"],
                      "start": "before_reset_and_per_request_admission",
                      "end": "after_sync_reconciliation_and_response_ready"}
        raw = json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
        admission = {"status": "INDEPENDENT_ENDPOINT_AUDIT_PASSED",
                     "source_sha256": a["source_sha256"], "request_id": a["request_id"],
                     "input_sha256": a["input_sha256"], "definition": definition,
                     "definition_sha256": hashlib.sha256(raw).hexdigest()}
        key = (a["request_id"], a["arm"], a["source_sha256"])
        with self.assertRaisesRegex(costs.CostError, "missing endpoint stage coverage: guard"):
            costs.paired_service(a, copy.deepcopy(a), {key: admission})

    def test_missing_reset_refused_by_frozen_endpoint(self):
        f = fixture()
        f["spans"][0]["category"] = "guard"
        a = costs.decompose(f)
        definition = {"required_categories": ["reset", "guard"],
                      "start": "before_reset_and_per_request_admission",
                      "end": "after_sync_reconciliation_and_response_ready"}
        raw = json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
        admission = {"status": "INDEPENDENT_ENDPOINT_AUDIT_PASSED",
                     "source_sha256": a["source_sha256"], "request_id": a["request_id"],
                     "input_sha256": a["input_sha256"], "definition": definition,
                     "definition_sha256": hashlib.sha256(raw).hexdigest()}
        key = (a["request_id"], a["arm"], a["source_sha256"])
        with self.assertRaisesRegex(costs.CostError, "missing endpoint stage coverage: reset"):
            costs.paired_service(a, copy.deepcopy(a), {key: admission})


if __name__ == "__main__":
    unittest.main()
