"""Host admission fixtures. No native model execution or experimental records."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import host
import study as s
from qualify import qualification


class HostAdmission(unittest.TestCase):
    def setUp(self):
        self.slots = s.lines(s.DESIGN / "SLOTS.jsonl")
        self.binding = {"calendar_dates": ["2026-10-29", "2026-10-30", "2026-10-31"],
                        "resource_caps": {"worker_timeout_seconds": 1800}}
        self.first = [r for r in self.slots if r["unit_id"] == "formal/d0/s0/Qwen"]
        self.second = [r for r in self.slots if r["unit_id"] == "formal/d1/s0/Qwen"]
        self.previous = [{"unit_id": "formal/d0/s0/Qwen", "family": "Qwen", "date_slot": 0,
                          "process_start_utc": "2026-10-29T12:00:00Z"}]

    def test_schedule_counts(self):
        self.assertEqual(len(self.first), 91)
        self.assertEqual(sum(r["stage"] == "warmup" for r in self.first), 7)

    def test_local_date_not_utc_date(self):
        host.calendar_gate(self.first, self.binding, [], datetime(2026, 10, 28, 16, 1, tzinfo=timezone.utc))
        with self.assertRaisesRegex(s.ContractError, "Shanghai date"):
            host.calendar_gate(self.first, self.binding, [], datetime(2026, 10, 29, 16, 1, tzinfo=timezone.utc))

    def test_twenty_hour_boundary(self):
        host.calendar_gate(self.second, self.binding, self.previous, datetime(2026, 10, 30, 8, tzinfo=timezone.utc))
        with self.assertRaisesRegex(s.ContractError, "20 hours"):
            host.calendar_gate(self.second, self.binding, self.previous, datetime(2026, 10, 30, 7, 59, 59, tzinfo=timezone.utc))

    def test_missing_prior_date(self):
        with self.assertRaisesRegex(s.ContractError, "previous date"):
            host.calendar_gate(self.second, self.binding, [], datetime(2026, 10, 30, 12, tzinfo=timezone.utc))

    def test_midnight_headroom(self):
        with self.assertRaisesRegex(s.ContractError, "headroom"):
            host.calendar_gate(self.first, self.binding, [], datetime(2026, 10, 29, 15, 30, tzinfo=timezone.utc))

    def test_qualification_has_no_formal_date(self):
        slots = [r for r in self.slots if r["unit_id"] == "qualification/Qwen"]
        host.calendar_gate(slots, self.binding, [], datetime(2026, 10, 28, 15, 59, tzinfo=timezone.utc))

    def test_missing_or_synthetic_bundle_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            s.save_lines(root / "REQUESTS.jsonl", [{"slot_id": "fake", "is_synthetic": True}])
            with self.assertRaises(s.ContractError):
                qualification(s.DESIGN, root, "Qwen")

    def test_payload_tampering_and_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / "payload.json"
            path.write_bytes(b"{}")
            record = host.pin(root, path)
            self.assertEqual(s.payload(root, record), path)
            path.write_bytes(b"[]")
            with self.assertRaises(s.ContractError):
                s.payload(root, record)
            bad = deepcopy(record); bad["path"] = "../payload.json"
            with self.assertRaises(s.ContractError):
                s.payload(root, bad)

    def test_metadata4_observed_query_alias(self):
        tensor = {"name": "jsa_llama_query_batch-7", "ne": [64, 1, 32, 4],
                  "nb": [4, 8192, 256, 8192], "device": "NVIDIA GeForce RTX 5070 Ti Laptop GPU"}
        row = {"scope": "QB", "family": "SmolLM2", "identity": {
            "source_variant": "metadata4", "source_zip_sha256": s.SOURCE_ZIPS["metadata4"]},
            "geometry": [{"name": "kq-7", "op": "MUL_MAT", "sources": [{"name": "cache_k"}, tensor]}]}
        self.assertEqual(s.local_geometry(row), [tensor])
        self.assertIs(s.local_geometry(row)[0], tensor)
        # The collector preserves wrong evidence so the original shape/placement
        # checks still reject it; it must not manufacture the expected geometry.
        tensor["ne"] = [64, 4, 32, 1]
        self.assertEqual(s.local_geometry(row)[0]["ne"], [64, 4, 32, 1])
        for mutation in ("family", "source", "operator", "layer", "operand"):
            bad = deepcopy(row)
            if mutation == "family": bad["family"] = "Qwen"
            if mutation == "source": bad["identity"]["source_zip_sha256"] = "0" * 64
            if mutation == "operator": bad["geometry"][0]["op"] = "VIEW"
            if mutation == "layer": bad["geometry"][0]["name"] = "kq-8"
            if mutation == "operand": bad["geometry"][0]["sources"].reverse()
            with self.subTest(mutation=mutation):
                self.assertEqual(s.local_geometry(bad), [])


if __name__ == "__main__":
    unittest.main()
