import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windows_epoch import Ledger, ResourceRefusal, admit_live, KEYS


class Resources(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / "RESOURCE_PLAN.json").read_text(encoding="utf8"))
        self.blocked_plan = copy.deepcopy(self.plan)
        self.plan["gpu_admission"] = "READY"  # synthetic host-only ledger; never a GPU receipt
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / "ledger.sqlite", self.plan)
        self.admission = {"status": "ADMITTED", "device_uuid": self.plan["device"]["uuid"]}

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def amounts(self, **kw):
        return {k: kw.get(k, 0) for k in KEYS}

    def test_historic_or_empty_device_observation_cannot_admit(self):
        with self.assertRaisesRegex(ResourceRefusal, "Original thread"):
            admit_live(self.plan, {"foreign_compute_pids": [], "device_uuid": self.plan["device"]["uuid"]}, [])

    def test_frozen_blocked_plan_cannot_admit(self):
        with self.assertRaisesRegex(ResourceRefusal, "Frozen plan"):
            admit_live(self.blocked_plan, {"fresh": True}, [])

    def test_failed_attempt_keeps_all_reserved_budget(self):
        a = self.amounts(model_requests=2, target_draft_rows=100, kernel_launches=3)
        self.ledger.reserve("failure-1", "failure_margin", a, self.admission)
        self.ledger.finish("failure-1", self.amounts(model_requests=1, kernel_launches=1), "FAILED")
        self.assertEqual(self.ledger.totals(), a)
        with self.assertRaisesRegex(ResourceRefusal, "Duplicate attempt"):
            self.ledger.reserve("failure-1", "failure_margin", a, self.admission)

    def test_stage_cap_not_borrowed_from_other_stages(self):
        with self.assertRaisesRegex(ResourceRefusal, "Stage cap"):
            self.ledger.reserve("over", "failure_margin", self.amounts(model_requests=33), self.admission)
        self.assertEqual(self.ledger.snapshot()["attempts"], [])

    def test_nan_and_wrong_device_refuse(self):
        with self.assertRaisesRegex(ResourceRefusal, "Invalid amount"):
            self.ledger.reserve("nan", "failure_margin", self.amounts(native_gpu_seconds=float("nan")), self.admission)
        with self.assertRaisesRegex(ResourceRefusal, "device mismatch"):
            self.ledger.reserve("wrong", "failure_margin", self.amounts(), {"status": "ADMITTED", "device_uuid": "other"})

    def test_epoch_plan_identity_cannot_change(self):
        p = copy.deepcopy(self.plan)
        p["maximums"]["model_requests"] += 1
        with self.assertRaisesRegex(ResourceRefusal, "another epoch or plan"):
            Ledger(self.ledger.path, p)

    def test_fractional_actual_refused_and_overrun_persisted(self):
        self.ledger.reserve("record-overrun", "failure_margin", self.amounts(model_requests=1), self.admission)
        with self.assertRaisesRegex(ResourceRefusal, "Noninteger actual"):
            self.ledger.finish("record-overrun", self.amounts(model_requests=0.5), "FAILED")
        with self.assertRaisesRegex(ResourceRefusal, "overrun persisted"):
            self.ledger.finish("record-overrun", self.amounts(model_requests=2), "FAILED")
        self.assertEqual(self.ledger.totals()["model_requests"], 2)
        self.assertEqual(self.ledger.snapshot()["attempts"][0]["status"], "OVERRUN")
        with self.assertRaisesRegex(ResourceRefusal, "Epoch stopped"):
            self.ledger.reserve("after-overrun", "failure_margin", self.amounts(), self.admission)


if __name__ == "__main__":
    unittest.main()
