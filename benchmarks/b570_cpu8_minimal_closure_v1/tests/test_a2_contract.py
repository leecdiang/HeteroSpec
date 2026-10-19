"""Static source-contract regressions. Synthetic fixtures; never Windows/native/GPU."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "source_candidate" / "source"
sys.path.insert(0, str(SRC))
import finalize_review_v6 as source_review
import operation_roles_v7 as roles
import operation_pricing_v7 as pricing


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf8")
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceReviewOnly(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        code = self.root / "source" / "candidate.py"
        code.parent.mkdir()
        code.write_text("answer = 1\n")
        # A fabricated one-file manifest must NOT qualify: enumerate the
        # complete 122-source plus ten auxiliary review input inventory.
        required = [
            "source/operation_guard.py", "source/finalize_review_v6.py",
            "source/verify_cpu8.py", "source/integration_gates.py",
            "source/native_gate_audit.py", "source/engineering_gates_v6.py",
            "source/operation_roles_v7.py", "source/operation_pricing_v7.py",
            "source/b_negative_binding_v7.py", "src/rev2/win.py",
        ]
        paths = ["source/candidate.py"] + required + [
            "source/synthetic%03d.py" % i for i in range(112)
        ]
        source_rows = []
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name != "source/candidate.py":
                path.write_text("synthetic = True\\n")
            source_rows.append({"path": name, "sha256": sha(path),
                                "bytes": path.stat().st_size})
        reference_rows = []
        for i in range(10):
            name = "review-inputs/aux%02d.md" % i
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC ONLY\\n")
            reference_rows.append({"path": name, "sha256": sha(path),
                                   "bytes": path.stat().st_size})
        composition = {"source_import_composition": source_rows,
                       "a2_references": reference_rows}
        cp = dump(self.root / "review" / "PINNED_SOURCE_COMPOSITION.json", composition)
        self.manifest = {
            "schema": "B570_SOURCE_CANDIDATE_V2",
            "candidate_commit": "a" * 40,
            "source_composition_sha256": sha(cp),
            "files": source_rows + reference_rows,
        }
        self.manifest_path = dump(self.root / "review" / "CANDIDATE_MANIFEST.json",
                                  self.manifest)
        self.review = {
            "status": "scoped-clean", "complete": True, "scope": "A_SOURCE_ONLY",
            "candidate_commit": "a" * 40,
            "candidate_manifest_sha256": sha(self.manifest_path),
            "severity_coverage": ["P0", "P1", "P2"],
            "reviewed_files": [x["path"] for x in self.manifest["files"]],
            "findings": [],
            "reviewer": {"identity": "SYNTHETIC_ONLY",
                         "session_or_review_url": "synthetic://not-authentic"},
            "transcript_sha256": "b" * 64,
        }
        dump(self.root / "review" / "FINAL_REVIEW.json", self.review)

    def test_composition_consistent_not_external_pass(self):
        result = source_review.verify(self.root)
        self.assertEqual(result["status"], "SOURCE_REVIEW_EVIDENCE_CONSISTENT")
        self.assertEqual(result["native_qualification"], "NOT_PERFORMED")
        self.assertEqual(result["independent_review_authentication"],
                         "REQUIRES_EXTERNAL_VERIFICATION")

    def test_short_manifest_cannot_qualify(self):
        self.manifest["files"] = self.manifest["files"][:1]
        dump(self.root / "review" / "CANDIDATE_MANIFEST.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "complete source candidate inventory"):
            source_review.verify(self.root)

    def test_tampered_auxiliary_input_cannot_qualify(self):
        (self.root / "review-inputs" / "aux00.md").write_text("MODIFIED")
        with self.assertRaisesRegex(ValueError, "source byte drift"):
            source_review.verify(self.root)

    def test_unreviewed_file_fails(self):
        self.review["reviewed_files"] = []
        dump(self.root / "review" / "FINAL_REVIEW.json", self.review)
        with self.assertRaisesRegex(ValueError, "full file coverage"):
            source_review.verify(self.root)

    def test_unresolved_priority_fails(self):
        self.review["findings"] = [{"severity": "P2", "disposition": "open"}]
        dump(self.root / "review" / "FINAL_REVIEW.json", self.review)
        with self.assertRaisesRegex(ValueError, "unresolved P0-P2"):
            source_review.verify(self.root)

    def test_removed_p2_scope_fails(self):
        self.review["severity_coverage"] = ["P0", "P1"]
        dump(self.root / "review" / "FINAL_REVIEW.json", self.review)
        with self.assertRaisesRegex(ValueError, "complete P0-P2"):
            source_review.verify(self.root)

    def test_modified_source_fails(self):
        (self.root / "source" / "candidate.py").write_text("answer = 999\n")
        with self.assertRaisesRegex(ValueError, "source byte drift"):
            source_review.verify(self.root)

    def test_wrong_commit_fails(self):
        self.review["candidate_commit"] = "c" * 40
        dump(self.root / "review" / "FINAL_REVIEW.json", self.review)
        with self.assertRaisesRegex(ValueError, "review commit identity"):
            source_review.verify(self.root)


class ProspectivePricing(unittest.TestCase):
    def setUp(self):
        self.op = {
            "seconds": 20, "cleanup_seconds": 5, "max_job_processes": 4,
            "starts_bound": 7, "lifetime_bound_seconds": 180,
            "prospective_envelope": {
                "schema": "B570_OWNED_ENVELOPE_V1",
                "provider_bound_status": "BOUNDARY_EVIDENCE_REQUIRED",
                "owned_job_starts_limit": 5, "owned_outer_starts_limit": 2,
                "provider_lifetime_reserve_seconds": 5,
                "provider_proof_sha256": "a" * 64,
            },
        }
        self.op["lifetime_bound_seconds"] = 7 * 25 + 5

    def test_explicit_starts_price_is_conditional_not_proof(self):
        result = pricing.envelope(self.op)
        self.assertEqual(result["max_process_seconds"], 180)
        self.assertEqual(result["status"], "CONDITIONAL_QUOTE_NOT_BOUNDARY_PROOF")

    def test_hidden_plus_two_price_rejected(self):
        self.op["lifetime_bound_seconds"] = (4 + 2) * 25
        with self.assertRaisesRegex(ValueError, "full operation prospective cost"):
            pricing.envelope(self.op)

    def test_zero_unknown_service_rejected(self):
        self.op["prospective_envelope"]["provider_lifetime_reserve_seconds"] = 0
        with self.assertRaisesRegex(ValueError, "provider reserve"):
            pricing.envelope(self.op)

    def test_cumulative_starts_smaller_than_cap_rejected(self):
        self.op["prospective_envelope"]["owned_job_starts_limit"] = 3
        with self.assertRaisesRegex(ValueError, "Job cumulative starts"):
            pricing.envelope(self.op)


class TaskRoleSelection(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        dump(self.root / "CAMPAIGN.json", {"task_uuid": "FRESH-B-UUID"})
        self.op = {"id": "fresh-b01", "task_uuid": "FRESH-B-UUID", "stage": "B"}
        path = dump(self.root / "tools" / "fresh-b01.operation.json", self.op)
        self.roles = {
            "schema": "B570_TASK_OPERATION_ROLES_V1", "task_uuid": "FRESH-B-UUID",
            "phase": "B", "roles": {"B01": {
                "phase": "B", "kind": "entry_positive", "operation_id": "fresh-b01",
                "sha256": sha(path),
            }},
        }
        dump(self.root / "OPERATION_ROLE_MAP.json", self.roles)

    def test_exact_current_role(self):
        opid, op = roles.operation(self.root, "B01", "B", "entry_positive")
        self.assertEqual(opid, "fresh-b01")
        self.assertEqual(op["task_uuid"], "FRESH-B-UUID")

    def test_wrong_uuid_fails(self):
        self.roles["task_uuid"] = "OLD-UUID"
        dump(self.root / "OPERATION_ROLE_MAP.json", self.roles)
        with self.assertRaisesRegex(ValueError, "current task identity"):
            roles.operation(self.root, "B01", "B")

    def test_old_role_id_cannot_be_promoted(self):
        self.roles["roles"]["B01"]["operation_id"] = "038-final-startup"
        dump(self.root / "OPERATION_ROLE_MAP.json", self.roles)
        with self.assertRaisesRegex(ValueError, "current operation id"):
            roles.operation(self.root, "B01", "B")

    def test_wrong_phase_fails(self):
        with self.assertRaisesRegex(ValueError, "current task identity"):
            roles.operation(self.root, "B01", "C")

    def test_wrong_operation_bytes_fails(self):
        self.op["extra"] = "unreviewed"
        dump(self.root / "tools" / "fresh-b01.operation.json", self.op)
        with self.assertRaisesRegex(ValueError, "operation exact bytes not frozen"):
            roles.operation(self.root, "B01", "B")


class IndependentReviewerCapture(unittest.TestCase):
    """Outside-candidate index consistency, NOT provider authority certification."""
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "candidate"
        self.ext = Path(tmp.name) / "external-capture"
        self.root.mkdir(); self.ext.mkdir()
        dump(self.root / "CAMPAIGN.json", {
            "original_root": str(self.root), "external_root": str(self.ext),
            "candidate_author": "synthetic-author",
        })
        self.source = {
            "candidate_commit": "a" * 40,
            "report_sha256": "b" * 64,
            "candidate_manifest_sha256": "c" * 64,
        }
        self.raw = {
            "request": {"repository_full_name": "leecdiang/HeteroSpec",
                        "candidate_commit": "a" * 40,
                        "scope": "FULL_P0_P2_SOURCE_REVIEW"},
            "response": {"report_sha256": "b" * 64,
                         "candidate_manifest_sha256": "c" * 64,
                         "reviewer_identity": "synthetic-independent",
                         "review_url": "synthetic://review-not-real",
                         "status": "COMPLETED"},
            "registered_utc": "2026-10-19T00:00:00+00:00",
            "observed_utc": "2026-10-19T00:01:00+00:00",
            "capture_meta": {"callId": "SYNTHETIC_CALL", "itemId": "SYNTHETIC_ITEM"},
        }
        self.approval = {
            "independent_reviewer_identity": "synthetic-independent",
            "external_provider_reference": "synthetic://review-not-real",
        }

    def persisted(self):
        provider = dump(self.ext / "source-review" / "A01-provider.json", self.raw)
        self.approval["provider_capture_sha256"] = sha(provider)
        dump(self.ext / "source-review" / "A01-index.json", {
            "sha256": sha(provider), "bytes": provider.stat().st_size,
            "capture_meta": self.raw["capture_meta"],
        })

    def check(self):
        import source_review_origin_v7 as origin
        self.persisted()
        return origin.check(self.root, self.approval, self.source)

    def test_consistent_synthetic_index_is_not_authority(self):
        self.assertEqual(self.check()["status"], "A_REVIEW_PROVIDER_CAPTURE_BOUND")
        self.assertIn("external authority", self.check()["scope"])

    def test_wrong_review_commit_fails(self):
        self.raw["request"]["candidate_commit"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "actual provider review request"):
            self.check()

    def test_reviewer_same_as_author_fails(self):
        self.raw["response"]["reviewer_identity"] = "synthetic-author"
        self.approval["independent_reviewer_identity"] = "synthetic-author"
        with self.assertRaisesRegex(ValueError, "not independent"):
            self.check()

    def test_reverse_time_fails(self):
        self.raw["observed_utc"] = "2026-10-18T23:59:59+00:00"
        with self.assertRaisesRegex(ValueError, "captured interval"):
            self.check()

    def test_missing_author_fails(self):
        dump(self.root / "CAMPAIGN.json", {
            "original_root": str(self.root), "external_root": str(self.ext),
        })
        with self.assertRaisesRegex(ValueError, "source author identity required"):
            self.check()


if __name__ == "__main__":
    unittest.main()
