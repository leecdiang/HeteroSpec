#!/usr/bin/env python3
"""Hardware-free tests of reproducibility and rejection of changed evidence."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import analyze_guard_always_secondary as analyzer
from recompute_evidence_bundle import extract_verified


class SecondaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="m4-secondary-test-")
        self.root = Path(self.tmp.name)
        self.manifest = extract_verified(analyzer.ARCHIVE, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def rewrite_raw(self, rows):
        raw = self.root / "attempts/formal/observations.jsonl"
        raw.write_text("".join(json.dumps(row) + "\n" for row in rows))
        path = raw.with_name("completion.json")
        completion = json.loads(path.read_text())
        completion["observations_sha256"] = analyzer.digest(raw)
        path.write_text(json.dumps(completion))

    def test_extracted_matches_canonical_result(self):
        manifest = analyzer.verify_extracted(self.root)
        result = analyzer.analyze(self.root, manifest)
        expected = json.loads((analyzer.BASE / "GUARD_ALWAYS_SECONDARY_ANALYSIS.json").read_text())
        self.assertEqual(result, expected)

    def test_wrong_archive_digest_rejected_before_output(self):
        fake = self.root / "changed.tar.gz"
        fake.write_bytes(b"changed evidence")
        completed = subprocess.run([sys.executable, str(Path(analyzer.__file__)), str(fake), "--output-dir", str(self.root / "output")], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Archive SHA-256 differs", completed.stderr)
        self.assertFalse((self.root / "output").exists())

    def test_changed_extracted_payload_rejected(self):
        raw = self.root / "attempts/formal/observations.jsonl"
        raw.write_bytes(raw.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Extracted payload changed"):
            analyzer.verify_extracted(self.root)

    def test_duplicate_condition_rejected(self):
        rows = [json.loads(line) for line in (self.root / "attempts/formal/observations.jsonl").read_text().splitlines()]
        duplicate = copy.deepcopy(rows[0])
        duplicate["observation_index"] = rows[1]["observation_index"]
        rows[1] = duplicate
        self.rewrite_raw(rows)
        with self.assertRaisesRegex(ValueError, "Duplicate, missing, or unexpected"):
            analyzer.analyze(self.root, self.manifest)

    def test_missing_observation_rejected(self):
        rows = [json.loads(line) for line in (self.root / "attempts/formal/observations.jsonl").read_text().splitlines()]
        self.rewrite_raw(rows[:-1])
        with self.assertRaisesRegex(ValueError, "Incomplete formal records"):
            analyzer.analyze(self.root, self.manifest)

    def test_multiple_formal_attempts_rejected(self):
        extra = self.root / "attempts/extra_formal/manifest.json"
        extra.parent.mkdir()
        extra.write_bytes((self.root / "attempts/formal/manifest.json").read_bytes())
        with self.assertRaisesRegex(ValueError, "Exactly one eligible formal dataset"):
            analyzer.analyze(self.root, self.manifest)

    def test_independent_verifier_rejects_changed_result_without_receipt(self):
        result = json.loads((analyzer.BASE / "GUARD_ALWAYS_SECONDARY_ANALYSIS.json").read_text())
        result["guard_over_always_95pct_prompt_bootstrap_ci"][0] += .001
        changed = self.root / "changed_result.json"
        changed.write_text(json.dumps(result))
        receipt = self.root / "must_not_write.json"
        completed = subprocess.run([sys.executable, str(Path(__file__).with_name("verify_guard_always_secondary.py")), "--result", str(changed), "--receipt", str(receipt)], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("both finite-bootstrap endpoints exactly reproduced", completed.stderr)
        self.assertFalse(receipt.exists())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SecondaryTests)
    test_names = sorted(case.id() for case in suite)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        receipt = analyzer.ROOT / "paper/mlsys2027/evidence/M4_GUARD_ALWAYS_SECONDARY_TEST_QA_V06.json"
        receipt.write_text(json.dumps({"status": "PASS", "tests_run": result.testsRun,
                                      "tests": test_names, "new_model_execution": False,
                                      "test_script_sha256": analyzer.digest(Path(__file__))}, indent=2) + "\n")
    sys.exit(not result.wasSuccessful())
