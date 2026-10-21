"""Static source-contract regressions. Synthetic fixtures; never Windows/native/GPU."""
import copy
import ast
import datetime
import hashlib
import json
import os
import sys
import subprocess
import tempfile
import unittest
import unittest.mock as mock
import types
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "source_candidate" / "source"
sys.path.insert(0, str(SRC))
# The real archived evidence_contract dependency is required by the B-negative
# source verifier. Staging it is mandatory; no invented stub is accepted.
ARCHIVED = os.environ.get("B570_A_HISTORICAL_ROOT")
if ARCHIVED:
    sys.path.insert(1, str(Path(ARCHIVED).resolve() / "source"))
import finalize_review_v6 as source_review
import operation_roles_v7 as roles
import operation_pricing_v7 as pricing
import budget_v6 as budgets
import b_negative_binding_v7 as negative_binding


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
        # complete 123-source plus ten auxiliary synthetic review inputs.
        required = [
            "source/operation_guard.py", "source/finalize_review_v6.py",
            "source/verify_cpu8.py", "source/integration_gates.py",
            "source/native_gate_audit.py", "source/engineering_gates_v6.py",
            "source/operation_roles_v7.py", "source/operation_pricing_v7.py",
            "source/b_negative_binding_v7.py", "source/source_review_origin_v7.py",
            "src/rev2/win.py",
        ]
        paths = ["source/candidate.py"] + required + [
            "source/synthetic%03d.py" % i for i in range(111)
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




class RecoverySourceContracts(unittest.TestCase):
    """Parse-only and source-contract regression; never imports Win32 or launches a fixture."""

    def test_all_candidate_python_overlays_parse(self):
        root = SRC.parent
        files = sorted(root.rglob("*.py"))
        self.assertGreaterEqual(len(files), 16)
        for path in files:
            with self.subTest(path=path.relative_to(root)):
                ast.parse(path.read_text(encoding="utf8"), filename=str(path))

    def test_guard_prebooks_unsettled_operation_before_native_job(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("state['open_operations'].count(x['id'])==1", code)
        self.assertLess(code.index("state=snapshot(ROOT,x['stage'])"), code.index("job=make_job()"))
        self.assertIn("fresh task/stage operation binding", code)
        self.assertIn("and code==0 else 'FAILED'", code)

    def test_guard_requires_existing_a2_operation_role_before_native_create(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("from operation_roles_v7 import role_map", code)
        self.assertIn("'unregistered current task operation role'", code)
        self.assertLess(code.index("roles=role_map(ROOT,x['stage'])"),
                        code.index("job=make_job()"))

    def test_owned_start_overrun_does_not_skip_job_close(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("bound_errors.append('OPERATION_OWNED_START_BOUND')", code)
        self.assertIn("bound_errors.append('OPERATION_TOTAL_START_BOUND')", code)
        self.assertLess(code.index("if bound_errors:"), code.index("checked(close(job)"))
        self.assertNotIn("need(total_job_processes<=pricing", code)

    def test_guard_has_native_deadline_event(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("_cleanup_emit('OPERATION_DEADLINE'", code)
        self.assertIn("source='GUARD_MONOTONIC_CHECK'", code)
        self.assertIn("_cleanup_emit('OPERATION_FAILURE'", code)
        self.assertIn("need(not deadline_fired.is_set() and now()<=deadline+1_000_000_000,'OPERATION_DEADLINE')", code)
        self.assertNotIn("'exit deadline'", code)

    def test_budget_never_discounts_higher_settled_charge(self):
        code = (SRC / "budget_v6.py").read_text(encoding="utf8")
        self.assertIn("max(charge,z['charged_process_seconds'])", code)

    def test_b_negative_roles_bind_noninterchangeable_producers(self):
        code = (SRC / "b_negative_binding_v7.py").read_text(encoding="utf8")
        for value in ("FIXTURE_NATIVE_EVENTS.jsonl", "GUARD_MONOTONIC_CHECK",
                      "EXTERNAL_NATIVE_OWNER", "frozen_contract_sha256",
                      "job_total_starts"):
            self.assertIn(value, code)
        self.assertNotIn('row.get("outer_witness_sha256")', code)

    def test_frozen_negative_template_has_no_future_witness_digest(self):
        template = json.loads((SRC.parents[1] / "B_NEGATIVE_CONTRACT.template.json").read_text())
        self.assertEqual(
            {k: row["detector_source"] for k, row in template["cases"].items()},
            {"B02": "FIXTURE_NATIVE", "B03": "GUARD_MONOTONIC",
             "B04": "EXTERNAL_NATIVE_OWNER"})
        self.assertTrue(all("outer_witness_sha256" not in row
                            for row in template["cases"].values()))


class GuardPurePredicates(unittest.TestCase):
    """Run only AST-extracted pure guard predicates; never import win or the runner."""

    def setUp(self):
        path = SRC / "operation_guard.py"
        tree = ast.parse(path.read_text(encoding="utf8"), filename=str(path))
        names = {"_deadline_expired", "_complete_member_inventory"}
        methods = [node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual({m.name for m in methods}, names)
        namespace = {}
        isolated = ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[]))
        exec(compile(isolated, "<source-only-guard-predicates>", "exec"), namespace)
        self.deadline = namespace["_deadline_expired"]
        self.census = namespace["_complete_member_inventory"]

    def test_deadline_text_without_elapsed_time_cannot_qualify(self):
        # An unrelated error that merely says OPERATION_DEADLINE is not evidence.
        self.assertFalse(self.deadline(False, 50, 100))
        self.assertFalse(self.deadline(False, 100, 100))

    def test_deadline_monotonic_expiry_or_rescue(self):
        self.assertTrue(self.deadline(False, 101, 100))
        self.assertTrue(self.deadline(True, 99, 100))

    def test_member_census_rejects_missing_short_lived_child(self):
        root = (123, "134000000000000000")
        observed = [(456, "134000000000000001")]
        self.assertTrue(self.census(2, root, observed))
        self.assertFalse(self.census(3, root, observed))
        self.assertFalse(self.census(1, root, observed))
        self.assertTrue(self.census(2, root, [root] + observed))
        self.assertFalse(self.census(True, root, observed))

    def test_native_source_census_fails_closed_before_closed_receipt(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("bound_errors.append('OPERATION_MEMBER_CENSUS_GAP')", code)
        self.assertIn("if not _complete_member_inventory(total_job_processes", code)
        self.assertLess(code.index("OPERATION_MEMBER_CENSUS_GAP"),
                        code.index("checked(close(job)"))
        self.assertIn("if _deadline_expired(deadline_fired.is_set()", code)
        self.assertNotIn("if 'OPERATION_DEADLINE' in error:", code)


class ProtectedOperationLedger(unittest.TestCase):
    """Actual source-only budget snapshot tests with synthetic, no-child data."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        stamp = (datetime.datetime.now(datetime.timezone.utc) -
                 datetime.timedelta(seconds=5)).isoformat()
        dump(self.root / "CAMPAIGN.json", {
            "task_uuid": "NEW-B-ONLY", "first_preparation_utc": stamp,
        })
        dump(self.root / "OPERATION_POLICY.json", {
            "total_process_seconds": 10000, "total_wall_seconds": 3600,
            "starts_limit": 1000,
            "reserves": {
                "B": {"process_seconds": 0, "wall_seconds": 0, "starts": 0},
                "delivery": {"process_seconds": 0, "wall_seconds": 0, "starts": 0},
            },
        })
        self.op = {
            "id": "b01-native", "task_uuid": "NEW-B-ONLY", "stage": "B",
            "seconds": 5, "cleanup_seconds": 5, "max_job_processes": 2,
            "starts_bound": 3, "lifetime_bound_seconds": 32,
            "prospective_envelope": {
                "schema": "B570_OWNED_ENVELOPE_V1",
                "provider_bound_status": "BOUNDARY_EVIDENCE_REQUIRED",
                "owned_job_starts_limit": 2, "owned_outer_starts_limit": 1,
                "provider_lifetime_reserve_seconds": 2,
                "provider_proof_sha256": "a" * 64,
            },
        }
        self.operation_path = self.root / "tools" / "b01-native.operation.json"
        self.persist()

    def persist(self):
        dump(self.operation_path, self.op)

    def test_exact_new_operation_is_reserved_once(self):
        result = budgets.snapshot(self.root, "B")
        self.assertEqual(result["charged_process_seconds"], 32)
        self.assertEqual(result["charged_starts"], 3)
        self.assertEqual(result["open_operations"], ["b01-native"])
        self.assertEqual(result["scope"].split(";")[0],
                         "Conservative envelope accounting")

    def test_reserved_delivery_stage_reads_current_b_ledger(self):
        result = budgets.snapshot(self.root, "delivery")
        self.assertEqual(result["charged_process_seconds"], 32)

    def test_negative_or_underquoted_lifetime_cannot_credit_budget(self):
        self.op["lifetime_bound_seconds"] = -100
        self.persist()
        with self.assertRaisesRegex(ValueError, "operation upper nonnegative integer"):
            budgets.snapshot(self.root, "B")

    def test_wrong_task_uuid_is_rejected(self):
        self.op["task_uuid"] = "CLOSED-OLD-UUID"
        self.persist()
        with self.assertRaisesRegex(ValueError, "foreign task operation"):
            budgets.snapshot(self.root, "B")

    def test_wrong_phase_is_rejected(self):
        self.op["stage"] = "C"
        self.persist()
        with self.assertRaisesRegex(ValueError, "wrong phase operation"):
            budgets.snapshot(self.root, "B")

    def test_wrong_filename_identity_is_rejected(self):
        wrong = self.operation_path.with_name("unregistered.operation.json")
        self.operation_path.rename(wrong)
        with self.assertRaisesRegex(ValueError, "filename/id mismatch"):
            budgets.snapshot(self.root, "B")

    def test_hidden_outer_starts_underquoted_is_rejected(self):
        self.op["starts_bound"] = 2
        self.persist()
        with self.assertRaisesRegex(ValueError, "complete owned starts bound"):
            budgets.snapshot(self.root, "B")

    def test_unpriced_zero_service_cannot_enter_budget(self):
        self.op["prospective_envelope"]["provider_lifetime_reserve_seconds"] = 0
        self.persist()
        with self.assertRaisesRegex(ValueError, "provider reserve"):
            budgets.snapshot(self.root, "B")


class UnassignedSuspendedRoot(unittest.TestCase):
    """Mock-controlled root recovery: no Win32 backend is imported or started."""

    def setUp(self):
        source = SRC / "operation_guard.py"
        parsed = ast.parse(source.read_text(encoding="utf8"), filename=str(source))
        methods = [node for node in parsed.body
                   if isinstance(node, ast.FunctionDef) and node.name == "_terminate_owned_root"]
        self.assertEqual(len(methods), 1)
        isolated = ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[]))
        scope = {}
        exec(compile(isolated, "<pure-unassigned-root-recovery>", "exec"), scope)
        self.terminate = scope["_terminate_owned_root"]

    def test_failed_job_assignment_directly_kills_suspended_root(self):
        calls = []
        route = self.terminate(False, True,
                               lambda: calls.append("JOB"),
                               lambda: calls.append("DIRECT"))
        self.assertEqual(route, "UNASSIGNED_ROOT")
        self.assertEqual(calls, ["DIRECT"])

    def test_assigned_child_uses_job_termination(self):
        calls = []
        route = self.terminate(True, True,
                               lambda: calls.append("JOB"),
                               lambda: calls.append("DIRECT"))
        self.assertEqual(route, "ASSIGNED_JOB")
        self.assertEqual(calls, ["JOB"])

    def test_already_exited_root_does_not_get_killed_twice(self):
        calls = []
        self.assertEqual(self.terminate(False, False,
                                        lambda: calls.append("JOB"),
                                        lambda: calls.append("DIRECT")), "ALREADY_EXITED")
        self.assertFalse(calls)

    def test_unassigned_exception_does_not_job_kill_before_direct_root_recovery(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        tree = ast.parse(code)
        handlers = [handler for node in ast.walk(tree) if isinstance(node, ast.Try)
                    for handler in node.handlers if isinstance(handler.type, ast.Name)
                    and handler.type.id == "BaseException"]
        recovery = [handler for handler in handlers
                    if any(isinstance(node, ast.Call)
                           and ((isinstance(node.func, ast.Attribute) and node.func.attr == "emit")
                                or (isinstance(node.func, ast.Name)
                                    and node.func.id == "_cleanup_emit"))
                           and node.args and isinstance(node.args[0], ast.Constant)
                           and node.args[0].value == "OPERATION_FAILURE"
                           for node in ast.walk(handler))]
        self.assertEqual(len(recovery), 1)
        calls = [node for node in ast.walk(recovery[0])
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == "terminate_job"]
        self.assertEqual(len(calls), 1)
        self.assertTrue(any(isinstance(node, ast.If)
                            and isinstance(node.test, ast.Name)
                            and node.test.id == "job_assigned"
                            and any(call in ast.walk(node) for call in calls)
                            for node in recovery[0].body))
        self.assertIn("lambda:checked(terminate_process(child.process,125)", code)

    def test_native_source_retains_real_wait_and_filetime_for_unassigned_root(self):
        code = (SRC / "operation_guard.py").read_text(encoding="utf8")
        self.assertIn("UNASSIGNED_SUSPENDED_ROOT_TERMINATION", code)
        self.assertIn("terminate_process(child.process,125)", code)
        self.assertIn("wait_handle(child.process", code)
        self.assertIn("_cleanup_emit('OP_TERMINAL_OS'", code)
        self.assertLess(code.index("checked(job_assign(job,child.process)"),
                        code.index("job_assigned=True"))


class BNegativeIdentityContracts(unittest.TestCase):
    """Actual B negative verifiers on synthetic identities; no provider/network/native."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.sha = "a" * 64
        self.start = {"pid": 41, "created_filetime": "1000", "parent_pid": 40,
                      "intent_sha256": self.sha, "command_sha256": "b" * 64}
        argv = ["C:/Python/python.exe", "-I", "-S", "-B", "fixture.py"]
        self.op = {"root": str(self.root), "task_uuid": "FRESH-B",
                   "argv": argv}
        self.created = {"pid": 42, "created_filetime": "1010",
                        "parent_pid": 41, "image": argv[0], "argv": argv,
                        "command": subprocess.list2cmdline(argv)}
        self.terminal = {"exit_code": 1, "isError": True, "output": "FAIL"}
        self.witness = {
            "owner_pid": 41, "owner_created_filetime": "1000", "guard_parent_pid": 40,
            "guard_command_sha256": "b" * 64,
            "guard_operation_sha256": self.sha,
            "root_pid": 42, "root_created_filetime": "1010",
            "external_owner_pid": 43, "external_owner_created_filetime": "900",
            "external_owner_job_member": False,
            "provider_terminal_sha256": hashlib.sha256(
                json.dumps(self.terminal, sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest(),
        }

    def verify_child(self):
        return negative_binding.native_child_binding(
            self.start, self.created, self.op, self.root, self.sha, "FRESH-B")

    def verify_owner(self):
        return negative_binding.outside_owner_binding(
            self.witness, self.start, self.created, self.sha, self.terminal,
            {(self.created["pid"], self.created["created_filetime"])})

    def test_both_independent_bindings_accept_consistent_fixture(self):
        self.assertTrue(self.verify_child())
        self.assertEqual(self.verify_owner(), self.witness["provider_terminal_sha256"])

    def test_changed_argv_or_parent_pid_rejected(self):
        self.created["parent_pid"] = 99
        with self.assertRaisesRegex(ValueError, "child argv/parent"):
            self.verify_child()
        self.created["parent_pid"] = 41
        self.created["argv"] = ["surprise.exe"]
        with self.assertRaisesRegex(ValueError, "child argv/parent"):
            self.verify_child()

    def test_wrong_guard_intent_and_parent_identity_rejected(self):
        self.start["intent_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "guard operation identity"):
            self.verify_child()
        self.start["intent_sha256"] = self.sha
        self.witness["owner_pid"] = 99
        with self.assertRaisesRegex(ValueError, "owner/guard/child/provider"):
            self.verify_owner()

    def test_witness_guard_parent_mismatch_rejected(self):
        self.witness["guard_parent_pid"] = 9876
        with self.assertRaisesRegex(ValueError, "owner/guard/child/provider"):
            self.verify_owner()

    def test_foreign_external_owner_or_provider_terminal_rejected(self):
        self.witness["external_owner_pid"] = 41
        with self.assertRaisesRegex(ValueError, "B outside owner"):
            self.verify_owner()
        self.witness["external_owner_pid"] = 43
        self.terminal["exit_code"] = 2
        with self.assertRaisesRegex(ValueError, "owner/guard/child/provider"):
            self.verify_owner()

    def test_guard_request_check_runs_before_negative_witness(self):
        code = (SRC / "b_negative_binding_v7.py").read_text(encoding="utf8")
        self.assertIn("request_check(root, operation_id, intent, initial, start, operation_sha)",code)
        self.assertLess(code.index("request_check(root, operation_id"),
                        code.index("terminal_sha = outside_owner_binding(witness, start"))


class NonCircularFormalFreeze(unittest.TestCase):
    """Pre-F0 quote -> immutable F0 -> post-F0 exact operation, entirely synthetic."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.uid = "C-TEST-NONCYCLIC"
        self.opid = "formal-fresh-c"
        dump(self.root/"CAMPAIGN.json", {
            "task_uuid": self.uid,
            "original_root": str(self.root),
            "first_preparation_utc": (datetime.datetime.now(datetime.timezone.utc)-
                                      datetime.timedelta(seconds=3)).isoformat(),
        })
        dump(self.root/"OPERATION_POLICY.json", {
            "total_process_seconds": 10000,
            "total_wall_seconds": 3600,
            "starts_limit": 300,
            "reserves": {"C": {"process_seconds": 0, "wall_seconds": 0, "starts": 0}},
        })
        self.template = {
            "id": self.opid, "task_uuid": self.uid, "stage": "C",
            "root": str(self.root),
            "argv": ["C:/Python/python.exe", "-I", "-S", "-B", "outer_watchdog.py",
                     "--freeze-sha256", roles.F0_SENTINEL],
            "seconds": 10, "cleanup_seconds": 5, "max_job_processes": 2,
            "starts_bound": 3, "lifetime_bound_seconds": 47,
            "prospective_envelope": {
                "schema": "B570_OWNED_ENVELOPE_V1",
                "provider_bound_status": "BOUNDARY_EVIDENCE_REQUIRED",
                "owned_job_starts_limit": 2, "owned_outer_starts_limit": 1,
                "provider_lifetime_reserve_seconds": 2,
                "provider_proof_sha256": "f" * 64,
            },
        }
        self.template_path = dump(
            self.root/"tools"/(self.opid+".operation.template.json"),self.template)
        rolemap = {
            "schema":"B570_TASK_OPERATION_ROLES_V1",
            "task_uuid":self.uid,"phase":"C",
            "roles":{"C-formal-watchdog":{
                "phase":"C","kind":"formal_cpu8",
                "operation_id":self.opid,
                "post_freeze_template":True,
                "template_sha256":sha(self.template_path),
            }},
        }
        self.rolemap_path=dump(self.root/"OPERATION_ROLE_MAP.json",rolemap)
        self.runtime_path=self.root/"tools"/(self.opid+".operation.json")

    def freeze(self,cycle=False):
        files={
            "tools/"+self.opid+".operation.template.json":sha(self.template_path),
            "OPERATION_ROLE_MAP.json":sha(self.rolemap_path),
        }
        if cycle:
            files["tools/"+self.opid+".operation.json"]="0"*64
        dump(self.root/"CAPABILITY_FREEZE.json",{"files":files,"scope":"SYNTHETIC"})
        return self.root/"CAPABILITY_FREEZE.json"

    def test_prefreeze_reserve_once_and_postfreeze_exact_operation(self):
        before=budgets.snapshot(self.root,"C")
        self.assertEqual(before["charged_process_seconds"],47)
        self.assertEqual(before["open_operations"],[self.opid])
        frozen=self.freeze()
        result=roles.materialize_formal_operation(self.root)
        self.assertEqual(result["freeze_sha256"],sha(frozen))
        self.assertEqual(result["status"],"POST_F0_OPERATION_MATERIALIZED_NOT_ADMITTED")
        name,op=roles.operation(self.root,"C-formal-watchdog","C","formal_cpu8")
        self.assertEqual(name,self.opid)
        self.assertIn(sha(frozen),op["argv"])
        self.assertNotIn(roles.F0_SENTINEL,op["argv"])
        after=budgets.snapshot(self.root,"C")
        self.assertEqual(after["charged_process_seconds"],47)
        self.assertEqual(after["charged_starts"],3)
        self.assertEqual(after["open_operations"],[self.opid])
        with self.assertRaises(FileExistsError):
            roles.materialize_formal_operation(self.root)

    def test_runtime_argument_substitution_rejected(self):
        self.freeze()
        roles.materialize_formal_operation(self.root)
        op=json.loads(self.runtime_path.read_text())
        op["argv"][0]="different_python.exe"
        dump(self.runtime_path,op)
        with self.assertRaisesRegex(ValueError,"formal runtime operation"):
            roles.operation(self.root,"C-formal-watchdog","C")

    def test_frozen_runtime_hash_cycle_rejected(self):
        self.freeze(cycle=True)
        with self.assertRaisesRegex(ValueError,"F0 hash cycle"):
            roles.materialize_formal_operation(self.root)

    def test_role_map_or_template_drift_rejected(self):
        self.freeze()
        self.template["argv"][0]="tampered"
        dump(self.template_path,self.template)
        with self.assertRaisesRegex(ValueError,"formal template exact"):
            roles.materialize_formal_operation(self.root)

    def test_changed_f0_bytes_invalidate_runtime(self):
        self.freeze()
        roles.materialize_formal_operation(self.root)
        # A different freeze hash cannot be accepted by an older runtime op.
        frozen=self.root/"CAPABILITY_FREEZE.json"
        doc=json.loads(frozen.read_text())
        doc["extra"]="mutated"
        dump(frozen,doc)
        with self.assertRaisesRegex(ValueError,"formal runtime operation"):
            roles.operation(self.root,"C-formal-watchdog","C")

    def test_freezer_never_seals_postfreeze_runtime_bytes(self):
        code=(SRC/"freeze_cpu8.py").read_text(encoding="utf8")
        self.assertIn("formal_template(ROOT)",code)
        self.assertIn("post-F0 operation exists before freeze",code)
        self.assertIn("F0 cannot hash its own runtime operation",code)



def _review_functions(path, names, namespace):
    tree = ast.parse(Path(path).read_text(encoding="utf8"), filename=str(path))
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if set(n.name for n in selected) != set(names):
        raise AssertionError("incomplete isolated source functions: " + str(names))
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])),
                 str(path), "exec"), namespace)
    return namespace


class PersistentJournalFailure(unittest.TestCase):
    def setUp(self):
        self.events = []
        class BadJournal:
            def emit(self, *args, **kwargs):
                raise OSError("simulated persistent disk/JOURNAL failure")
        self.state = _review_functions(SRC/"operation_guard.py",
                     {"_cleanup_emit", "_terminate_owned_root"},
                     {"j": BadJournal(), "cleanup_log_errors": []})

    def test_logger_failed_before_root_cleanup_cannot_block_direct_kill_wait_close(self):
        log = self.state["_cleanup_emit"]
        terminate = self.state["_terminate_owned_root"]
        log("OPERATION_FAILURE", error="synthetic")
        route = terminate(False, True,
                          lambda: self.events.append("WRONG_JOB_ONLY"),
                          lambda: self.events.append("DIRECT_TERMINATE"))
        log("UNASSIGNED_SUSPENDED_ROOT_TERMINATION")
        self.events.extend(("NATIVE_WAIT", "HANDLE_CLOSE"))
        self.assertEqual(route, "UNASSIGNED_ROOT")
        self.assertEqual(self.events, ["DIRECT_TERMINATE", "NATIVE_WAIT",
                                       "HANDLE_CLOSE"])
        self.assertGreaterEqual(len(self.state["cleanup_log_errors"]), 2)

    def test_no_cleanup_journal_call_can_preempt_direct_root_termination(self):
        code = (SRC/"operation_guard.py").read_text(encoding="utf8")
        main_finally = code.index("\nfinally:\n if child and child.process:")
        end = code.index("\nprint(json.dumps(", main_finally)
        cleanup = code[main_finally:end]
        self.assertLess(cleanup.index("cleanup_route=_terminate_owned_root("),
                        cleanup.index("_cleanup_emit('UNASSIGNED_SUSPENDED_ROOT_TERMINATION'"))
        self.assertNotIn("j.emit(", cleanup)
        failure = code[code.index("\nexcept BaseException as e:\n error=repr(e)"):main_finally]
        self.assertNotIn("j.emit(", failure)
        self.assertIn("CLEANUP_JOURNAL_FAILURE", code)

    def test_log_error_causes_failed_not_closed_receipt(self):
        code = (SRC/"operation_guard.py").read_text(encoding="utf8")
        self.assertIn("if cleanup_log_errors:\n  error=", code)
        self.assertIn("and not cleanup_log_errors and empty", code)


class JobMembershipBeforeRetention(unittest.TestCase):
    def setUp(self):
        self.scope = _review_functions(SRC/"operation_guard.py",
                      {"_require_member_flag"},
                      {"need": lambda ok, why: ok or (_ for _ in ()).throw(RuntimeError(why))})

    def test_job_member_handle_accept_and_foreign_reused_pid_reject(self):
        self.assertTrue(self.scope["_require_member_flag"](True))
        for value in (False, None, 0):
            with self.assertRaisesRegex(RuntimeError, "FOREIGN_OR_REUSED_JOB_PID"):
                self.scope["_require_member_flag"](value)

    def test_win32_isprocessinjob_bound_and_checked_before_retaining(self):
        win = (SRC/"../src/rev2/win.py").resolve().read_text(encoding="utf8")
        guard = (SRC/"operation_guard.py").read_text(encoding="utf8")
        self.assertIn("process_in_job=api(K,'IsProcessInJob'", win)
        self.assertLess(guard.index("checked(process_in_job(h,job,"),
                        guard.index("retained[key]=h;h=None"))


class OutsideOwnerNotJobMember(unittest.TestCase):
    def test_reject_negative_pid_and_pid_of_real_job_child(self):
        fixture = BNegativeIdentityContracts()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.witness["external_owner_pid"] = -15
        with self.assertRaisesRegex(ValueError, "independent outside owner identity"):
            fixture.verify_owner()
        fixture.witness["external_owner_pid"] = 42
        with self.assertRaisesRegex(ValueError, "cannot be guard, child or Job member"):
            fixture.verify_owner()
        fixture.witness["external_owner_pid"] = 43
        fixture.witness["external_owner_job_member"] = True
        with self.assertRaisesRegex(ValueError, "cannot be guard, child or Job member"):
            fixture.verify_owner()


class NativeFreezeSacrificialBaseline(unittest.TestCase):
    def test_identity_input_present_before_freeze_inventory(self):
        code = (SRC/"native_freeze_gates.py").read_text(encoding="utf8")
        self.assertIn("shutil.copyfile(ROOT/'preflight/TOOLS.json',", code)
        self.assertIn("sacrifice/'preflight/TOOLS.json'", code)
        self.assertLess(code.index("shutil.copyfile(ROOT/'preflight/TOOLS.json'"),
                        code.index("files={p.relative_to(sacrifice)"))

    def test_missing_synthetic_tools_input_cannot_be_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def expected():
                return json.loads((root/"preflight/TOOLS.json").read_bytes())["python"]["path"]
            with self.assertRaises(FileNotFoundError):
                expected()
            dump(root/"preflight/TOOLS.json", {"python": {"path": sys.executable}})
            self.assertEqual(expected(), sys.executable)


class CSpecificFrozenWallLimit(unittest.TestCase):
    def setUp(self):
        import math
        self.scope = _review_functions(SRC/"../src/rev2/guards.py",
             {"_frozen_c_limits", "wall_budget", "utc", "finite"},
             {"datetime": datetime, "math": math,
              "require": lambda ok, reason: ok or (_ for _ in ()).throw(ValueError(reason)),
              "revision_budget": lambda regs,policy: {}})
        fake=types.ModuleType("continuation_policy")
        fake.validate=lambda p: None
        self.patch=mock.patch.dict(sys.modules, {"continuation_policy":fake})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.origin="2026-10-19T00:00:00Z"
        self.acq={"first_preparation_utc":self.origin}
        self.freeze={
            "frozen_utc":"2026-10-19T00:00:05Z",
            "review_status":"A_SOURCE_ONLY_EXTERNALLY_APPROVED",
            "cpu8_execution_envelope_sha256":"f"*64,
            "budget":{"task_seconds":9,"delivery_seconds":2}}
        self.start={"started_utc":"2026-10-19T00:00:08Z","begin_ns":0}
        self.receipt={"task_elapsed_before_watchdog_seconds":8,
                      "begin_ns":0,"end_ns":2_000_000_000}

    def evaluate(self, completion=None):
        return self.scope["wall_budget"](self.acq,self.freeze,[],self.start,
                                         self.receipt,completion)

    def test_old_six_hour_constant_cannot_override_frozen_c_limit(self):
        with self.assertRaisesRegex(ValueError, "C_FROZEN_TASK_WALL_LIMIT"):
            self.evaluate()
        self.freeze["budget"]["task_seconds"]=11
        self.assertEqual(self.evaluate()["task_through_watchdog_seconds"],10)

    def test_real_completion_must_fit_frozen_c_and_delivery_caps(self):
        completion={"observed_utc":"2026-10-19T00:00:12Z",
                    "task_elapsed_seconds":12,
                    "restoration_verified":True,"tool_exit_verified":True}
        self.freeze["budget"]["task_seconds"]=11
        with self.assertRaisesRegex(ValueError,"C_FROZEN_TASK_WALL_LIMIT"):
            self.evaluate(completion)
        self.freeze["budget"]["task_seconds"]=13
        self.freeze["budget"]["delivery_seconds"]=1
        with self.assertRaisesRegex(ValueError,"C_FROZEN_DELIVERY_WALL_LIMIT"):
            self.evaluate(completion)
        self.freeze["budget"]["delivery_seconds"]=3
        self.assertEqual(self.evaluate(completion)["task_through_completion_seconds"],12)

    def test_missing_or_bad_new_c_cap_cannot_fallback_to_21600(self):
        del self.freeze["budget"]
        with self.assertRaisesRegex(ValueError,"C_FROZEN_WALL_BUDGET_REQUIRED"):
            self.evaluate()
        self.freeze["budget"]={"task_seconds":False,"delivery_seconds":1}
        with self.assertRaisesRegex(ValueError,"C_FROZEN_TASK_WALL_CAP"):
            self.evaluate()


class SealedPostDeliveryExternalEvidence(unittest.TestCase):
    """Execute only isolated source functions with synthetic files, no connector/Win32."""

    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/"candidate"
        self.outer=Path(tmp.name)/"platform-owned"
        self.root.mkdir();self.outer.mkdir()
        self.uid="NEW-C-TEST"
        dump(self.root/"CAMPAIGN.json",{
            "original_root":str(self.root),"external_root":str(self.outer),
            "task_uuid":self.uid})
        dump(self.root/"CAPABILITY_FREEZE.json",{"status":"SYNTHETIC_ONLY","files":{}})
        self.scope=_review_functions(SRC/"delivery_binding_v6.py",
            {"_postseal_file","postseal_capture","restore_postseal_invocation",
             "utc","load","h","download"},
            {"Path":Path,"datetime":datetime,"hashlib":hashlib,"json":json,
             "subprocess":subprocess,"re":__import__("re"),
             "base64":__import__("base64"),
             "need":lambda value,msg:value or (_ for _ in ()).throw(ValueError(msg))})
        self.op="fresh-restore"
        self.argv=["C:/Python/python.exe","-I","-S","-B","restore.py"]
        self.request={"cmd":"synthetic-restore"}
        self.stdout=b"RECONSTRUCTION_ONLY\\n"
        self.report=self.outer/"report.json"
        self.report.write_bytes(self.stdout)
        self.frozen_sha=sha(self.root/"CAPABILITY_FREEZE.json")
        self.intent={
            "schema":"B570_POSTSEAL_RESTORE_V1","operation_id":self.op,
            "task_uuid":self.uid,"freeze_sha256":self.frozen_sha,
            "registered_utc":"2026-10-19T00:00:00Z",
            "argv":self.argv,"request":self.request}
        self.put("intents",self.op+".json",self.intent)
        self.make_capture(self.op,"initial",self.request,
                          {"session_id":None,"exit_code":0,"isError":False,
                           "output":"RECONSTRUCTION_ONLY\\n"},
                          "2026-10-19T00:00:04Z")
        epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)
        def filetime(iso):
            stamp=datetime.datetime.fromisoformat(iso.replace("Z","+00:00"))
            return str(int((stamp-epoch).total_seconds()*10_000_000))
        self.put("native-exits",self.op+".json",{
            "created_filetime":filetime("2026-10-19T00:00:01Z"),
            "exit_filetime":filetime("2026-10-19T00:00:03Z"),
            "task_uuid":self.uid,"operation_id":self.op,
            "freeze_sha256":self.frozen_sha,
            "intent_sha256":sha(self.outer/"postseal"/"intents"/(self.op+".json")),
            "argv":self.argv,"command":subprocess.list2cmdline(self.argv),
            "pid":41,"parent_pid":40,"image":self.argv[0],
            "exit_code":0,"all_owned_handles_closed":True,
            "descendants_exited":True,"job_empty":True,
            "report_sha256":sha(self.report),
            "stdout_sha256":hashlib.sha256(self.stdout).hexdigest()})
        p=self.outer/"postseal"/"stdout"/(self.op+".bin")
        p.parent.mkdir(parents=True)
        p.write_bytes(self.stdout)

    def put(self,kind,name,obj):
        return dump(self.outer/"postseal"/kind/name,obj)

    def make_capture(self,op,kind,request,response,observed):
        meta={"callId":"synthetic-provider-call","itemId":"synthetic-item"}
        cap={"id":op,"kind":kind,"request":request,"response":response,
             "observed_utc":observed,"capture_meta":meta}
        p=self.put("captures",op+"."+kind+".json",cap)
        self.put("capture-index",op+"."+kind+".json",{
            "path":str(p),"bytes":p.stat().st_size,"sha256":sha(p),
            "capture_meta":meta})
        return p

    def test_restore_succeeds_readonly_with_fully_external_receipts(self):
        before={p.relative_to(self.root).as_posix():sha(p)
                for p in self.root.rglob("*") if p.is_file()}
        data=self.scope["restore_postseal_invocation"](
            self.root,self.op,self.argv,self.report)
        self.assertEqual(data["status"],"POSTSEAL_RESTORE_CAPTURE_BOUND")
        after={p.relative_to(self.root).as_posix():sha(p)
               for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(after,before)
        self.assertFalse((self.root/"tools").exists())

    def test_mutated_outside_capture_index_rejected(self):
        index=self.outer/"postseal"/"capture-index"/(self.op+".initial.json")
        record=json.loads(index.read_text())
        record["path"]=str(self.root/"tools"/(self.op+".initial.json"))
        dump(index,record)
        with self.assertRaisesRegex(ValueError,"postseal capture index/bytes"):
            self.scope["postseal_capture"](self.root,self.op,"initial")

    def test_in_root_postseal_receipt_cannot_replace_missing_external_record(self):
        outside=self.outer/"postseal"/"captures"/(self.op+".initial.json")
        fake=dump(self.root/"tools"/(self.op+".initial.json"),
                  json.loads(outside.read_text()))
        outside.unlink()
        self.assertTrue(fake.is_file())
        with self.assertRaisesRegex(ValueError,"postseal evidence missing"):
            self.scope["postseal_capture"](self.root,self.op,"initial")

    def test_mismatched_recomputation_stdout_rejected(self):
        (self.outer/"postseal"/"stdout"/(self.op+".bin")).write_bytes(b"DIFFERENT")
        with self.assertRaisesRegex(ValueError,"postseal full output bytes"):
            self.scope["restore_postseal_invocation"](
                self.root,self.op,self.argv,self.report)

    def test_download_uses_external_provider_capture_not_root_tools(self):
        content=b"sealed archive chunk"
        chunk=self.outer/"download-chunk.b64"
        import base64 as _b64
        encoded=_b64.b64encode(content)
        chunk.write_bytes(encoded)
        git_sha=hashlib.sha1(b"blob "+str(len(encoded)).encode()+b"\0"+encoded).hexdigest()
        row={"path":str(chunk),"remote_path":"benchmarks/delivery/chunk.b64",
             "remote_blob_sha":git_sha}
        commit="a"*40
        request={"repository_full_name":"leecdiang/HeteroSpec",
                 "ref":commit,"path":row["remote_path"]}
        self.make_capture("fresh-download","download",request,{
            "isError":False,"structuredContent":{
                "sha":git_sha,"encoding":"base64","content":_b64.b64encode(encoded).decode()
            }}, "2026-10-19T00:00:04Z")
        dump(self.outer/"download-intents"/"fresh-download.json",{
            "request":request,"registered_utc":"2026-10-19T00:00:00Z"})
        self.assertEqual(self.scope["download"](self.root,"fresh-download",row,commit)["status"],
                         "ACTUAL_PROVIDER_DOWNLOAD_BOUND")

    def test_delivery_auditor_binds_restored_tool_outside_root(self):
        code=(SRC/"delivery_audit.py").read_text(encoding="utf8")
        self.assertIn("restore_postseal_invocation(root,restore['tool_operation']",code)
        self.assertNotIn("restore_binding=bind_invocation(root,restore",code)

if __name__ == "__main__":
    unittest.main()
