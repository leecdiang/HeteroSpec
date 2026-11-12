"""Complete-lifecycle conditional budget planning; production remains blocked.

No CUDA, ctypes, DLL loader, numeric worker, or production GPU ledger is
imported/opened here. The executable controller is deliberately CPU-mock-only.
A self-issued manifest cannot create a native coverage certificate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from types import MappingProxyType
from typing import Callable

PHYSICAL_LIMIT = 4096
MAX_EXPANSIONS = 8192
REQUIRED_PHASES = (
    "worker_bootstrap", "numerical_dll_load", "cuda_context_init", "library_init",
    "target_model_load", "draft_model_load", "target_kv_init", "draft_kv_init",
    "transfers", "warmup", "target_prefill", "draft_prefill", "draft_generation",
    "target_verify", "reconciliation", "capture", "error_cleanup", "teardown",
)
REQUIRED_ACTORS = ("A", "B", "C", "draft", "reference")
PRODUCTION_PROOF_ALLOWLIST = MappingProxyType({})  # intentionally empty
DISALLOWED_NODE_KINDS = {"while", "conditional", "device_launch", "dynamic",
                         "host_callback", "external_work", "unknown"}


class BudgetRefusal(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        self.total_upper_bound = None
        super().__init__(code + ": " + message)


def need(ok, code, message):
    if not ok:
        raise BudgetRefusal(code, message)


def count(value, label, maximum=PHYSICAL_LIMIT):
    need(type(value) is int and 0 <= value <= maximum, "COUNT", label)
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256_shape(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class Certificate:
    proof_id: str
    phase: str
    route: str
    kind: str
    upper_bound: int
    artifact_sha256: str
    mode: str = "CPU_MOCK_ONLY"


class NativeProofRegistry:
    mode = "NATIVE"

    def lookup(self, phase, node):
        # No JSON loader, self-approval flag or post-run report populates this.
        raise BudgetRefusal("NATIVE_PROOF_MISSING", "No trusted full-physical certificate for " + phase + "/" + node.route)


class MockProofRegistry:
    """Test authority only; it cannot produce native permits."""
    mode = "CPU_MOCK_ONLY"

    def __init__(self, certificates):
        self._certificates = {c.proof_id: c for c in certificates}
        need(len(self._certificates) == len(certificates), "PROOF", "Duplicate mock proof ID")

    def lookup(self, phase, node):
        c = self._certificates.get(node.proof_id)
        need(c is not None, "PROOF", "Missing mock certificate for " + phase + "/" + node.route)
        need(c.mode == self.mode and c.proof_id.startswith("MOCK:"), "PROOF", "Mock proof cannot masquerade as native")
        need((c.phase, c.route, c.kind) == (phase, node.route, node.kind), "PROOF", "Proof scope mismatch")
        need(c.artifact_sha256 == node.artifact_sha256, "IDENTITY", "Route artifact identity changed")
        count(c.upper_bound, "certificate physical upper bound")
        return c


@dataclass(frozen=True)
class Node:
    kind: str
    route: str
    proof_id: str
    artifact_sha256: str
    children: tuple["Node", ...] = ()
    repeat: int = 1


@dataclass(frozen=True)
class Phase:
    name: str
    operations: tuple[Node, ...]


@dataclass(frozen=True)
class Step:
    step_id: str
    phase: str
    route: str
    kind: str
    upper_bound: int
    node_fingerprint: str


@dataclass(frozen=True)
class Plan:
    mode: str
    steps: tuple[Step, ...]
    error_steps: tuple[Step, ...]
    total_upper_bound: int
    policy_digest: str
    plan_fingerprint: str

    def payload(self):
        return {"mode": self.mode, "steps": [asdict(s) for s in self.steps],
                "error_steps": [asdict(s) for s in self.error_steps],
                "total_upper_bound": self.total_upper_bound, "policy_digest": self.policy_digest}

    def validate_identity(self):
        need(fingerprint(self.payload()) == self.plan_fingerprint, "IDENTITY", "Frozen plan mutated")


class Planner:
    def __init__(self, registry):
        self.registry = registry

    def _bound(self, phase, node, stack=()):
        need(isinstance(node, Node), "SHAPE", "Operation must be a frozen Node")
        need(node.kind not in DISALLOWED_NODE_KINDS, "GRAPH_OR_OPAQUE", "Unbounded/dynamic route is not admitted: " + node.kind)
        count(node.repeat, "finite replay bound")
        need(node.repeat > 0, "GRAPH", "Zero replay declarations cannot erase coverage")
        need(node.kind in ("kernel", "wrapper", "static_graph", "opaque"), "ROUTE", "Unknown operation kind")
        need(sha256_shape(node.artifact_sha256), "IDENTITY", "Artifact identity missing")
        need(node.route not in stack and len(stack) < 16, "GRAPH", "Nested graph/wrapper recursion or excessive depth")
        cert = self.registry.lookup(phase, node)  # zero-work also needs a proof
        if node.kind == "kernel":
            need(not node.children and cert.upper_bound == 1, "KERNEL", "Explicit physical kernel primitive must have bound1")
        elif node.kind == "opaque":
            need(not node.children, "OPAQUE", "Opaque work cannot hide child declarations")
        else:
            need(bool(node.children), "GRAPH", "A wrapper/graph needs an explicit closed node set")
        child = sum(self._bound(phase, n, stack + (node.route,)) for n in node.children)
        total = (cert.upper_bound + child) * node.repeat
        need(total <= PHYSICAL_LIMIT, "BUDGET", "One route exceeds the entire physical ceiling")
        return total

    def bind(self, phases, policy_by_actor):
        need(tuple(p.name for p in phases) == REQUIRED_PHASES, "LIFECYCLE", "Every required lifecycle phase must appear exactly once in order")
        need(set(policy_by_actor) == set(REQUIRED_ACTORS), "POLICY", "A/B/C/draft/reference policy bindings required")
        digests = list(policy_by_actor.values())
        need(all(sha256_shape(d) for d in digests) and len(set(digests)) == 1,
             "POLICY", "Graph/library policy differs between actors")
        steps, errors, total = [], [], 0
        for phase in phases:
            need(bool(phase.operations), "LIFECYCLE", "Empty phase is not a certified zero-work phase: " + phase.name)
            for index, node in enumerate(phase.operations):
                bound = self._bound(phase.name, node)
                total += bound
                need(total <= PHYSICAL_LIMIT, "BUDGET", "Whole-lifecycle upper bound exceeds4096")
                for replay in range(node.repeat):
                    s = Step(f"{phase.name}:{index}:replay:{replay}", phase.name, node.route, node.kind, bound // node.repeat, fingerprint(asdict(node)))
                    (errors if phase.name == "error_cleanup" else steps).append(s)
                need(len(steps) + len(errors) <= MAX_EXPANSIONS, "EXPANSION", "Too many finite lifecycle actions")
        payload = {"mode": self.registry.mode, "steps": [asdict(s) for s in steps],
                   "error_steps": [asdict(s) for s in errors], "total_upper_bound": total,
                   "policy_digest": digests[0]}
        return Plan(self.registry.mode, tuple(steps), tuple(errors), total, digests[0], fingerprint(payload))


class MockFamilyLedger:
    """Persistent mock-family reservations, never the canonical GPU ledger.

    Charge the complete prebound lifecycle (including error cleanup) durably
    before the first simulated DLL/init operation. No observation refunds it.
    """
    def __init__(self, path, family_id, parent_binding, inherited_charge=0, *, mock_root):
        raw_root = Path(mock_root).absolute()
        need(raw_root.name.startswith("CPU-MOCK-") and raw_root.is_dir(), "MOCK_ROOT", "Existing dedicated CPU-MOCK workspace required")
        def plain(entry):
            info = entry.lstat()
            need(not entry.is_symlink() and not (getattr(info,"st_file_attributes",0) & 0x400),
                 "MOCK_ALIAS", "Reparse/symlink paths cannot host mock ledgers")
            return info
        plain(raw_root)
        self.path = Path(path).absolute()
        need(self.path.is_relative_to(raw_root), "MOCK_ROOT", "Mock ledger leaves dedicated workspace")
        # Check each existing lexical component before resolving aliases.
        for component in (self.path, *self.path.parents):
            if component.exists() or component.is_symlink():
                info = plain(component)
                if component == self.path:
                    need(info.st_nlink == 1, "MOCK_ALIAS", "Hardlinked ledger paths are refused")
            if component == raw_root:
                break
        need(self.path.resolve().is_relative_to(raw_root.resolve()), "MOCK_ROOT", "Resolved mock path leaves workspace")
        need(self.path.name.startswith("CPU-MOCK-"), "MOCK_ONLY", "Refuse any production/canonical ledger path")
        count(inherited_charge, "inherited family charge")
        need(family_id.startswith("CPU-MOCK-"), "MOCK_ONLY", "Mock family ID required")
        expected = (family_id, PHYSICAL_LIMIT, parent_binding, inherited_charge)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            # Read-only format check BEFORE any CREATE/PRAGMA that can mutate.
            ro = None
            try:
                ro = sqlite3.connect(self.path.as_uri()+"?mode=ro", uri=True)
                need(ro.execute("PRAGMA application_id").fetchone()[0] == 0x48534D4B,
                     "MOCK_FORMAT", "Existing database is not a marked mock ledger")
                tables = {r[0] for r in ro.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                need({"family","leases","observations","events"}.issubset(tables), "MOCK_FORMAT", "Mock ledger schema incomplete")
                need(ro.execute("SELECT id,ceiling,parent,inherited FROM family").fetchall() == [expected],
                     "FAMILY_BINDING", "Existing mock family/parent binding changed")
            except sqlite3.DatabaseError as exc:
                raise BudgetRefusal("MOCK_FORMAT", "Existing path is not a valid marked mock database") from exc
            finally:
                if ro is not None:
                    ro.close()
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.execute("PRAGMA application_id=1213418827")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS family(id TEXT PRIMARY KEY,ceiling INTEGER,parent TEXT,inherited INTEGER,stop_reason TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS leases(id TEXT PRIMARY KEY,epoch TEXT,plan_hash TEXT,reserved INTEGER,status TEXT,emitted INTEGER,reason TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS observations(lease TEXT,payload TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,payload TEXT)")
        rows = self.db.execute("SELECT id,ceiling,parent,inherited FROM family").fetchall()
        if rows and rows != [expected]:
            self.db.close()
            raise BudgetRefusal("FAMILY_BINDING", "New epoch cannot replace family, inherited charge, limit or parent binding")
        if not rows:
            self.db.execute("INSERT INTO family VALUES(?,?,?,?,NULL)", expected)
            self.db.commit()
        self.family_id = family_id

    def _event(self, kind, value):
        self.db.execute("INSERT INTO events(kind,payload) VALUES(?,?)", (kind, json.dumps(value, sort_keys=True)))

    def charged(self):
        base = self.db.execute("SELECT inherited FROM family").fetchone()[0]
        return base + sum(max(reserved, emitted) for reserved, emitted in self.db.execute("SELECT reserved,emitted FROM leases"))

    def reserve(self, lease_id, epoch, plan):
        plan.validate_identity()
        need(plan.mode == "CPU_MOCK_ONLY", "MOCK_ONLY", "Mock ledger cannot authorize native work")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            need(self.db.execute("SELECT stop_reason FROM family").fetchone()[0] is None, "FAMILY_STOPPED", "Prior failure stops the family")
            need(self.db.execute("SELECT COUNT(*) FROM leases WHERE status IN ('RESERVED','RUNNING')").fetchone()[0] == 0,
                 "RECOVERY_REQUIRED", "Pending/unclosed lease blocks automatic new-epoch continuation")
            need(self.charged() + plan.total_upper_bound <= PHYSICAL_LIMIT, "FAMILY_BUDGET", "No new4096 allowance for a new epoch")
            try:
                self.db.execute("INSERT INTO leases VALUES(?,?,?,?,?,0,NULL)", (lease_id, epoch, plan.plan_fingerprint, plan.total_upper_bound, "RESERVED"))
            except sqlite3.IntegrityError as exc:
                raise BudgetRefusal("RETRY", "Duplicate lease ID is not a retry allowance") from exc
            self._event("RESERVED_BEFORE_ANY_MOCK_LIFECYCLE_ENTRY", {"lease": lease_id, "bound": plan.total_upper_bound})

    def mark_running(self, lease_id):
        with self.db:
            r = self.db.execute("UPDATE leases SET status='RUNNING' WHERE id=? AND status='RESERVED'", (lease_id,))
            need(r.rowcount == 1, "LEASE", "Lease is not reserved")

    def finish(self, lease_id, status, emitted, reason=None):
        count(emitted, "observed mock emissions", maximum=2**63-1)
        need(status in ("COMPLETE", "FAILED"), "LEASE", "Unknown terminal status")
        with self.db:
            row = self.db.execute("SELECT reserved,status FROM leases WHERE id=?", (lease_id,)).fetchone()
            need(row is not None and row[1] in ("RESERVED", "RUNNING"), "LEASE", "Lease cannot be reopened")
            if emitted > row[0]:
                status, reason = "OVERRUN", "Observed mock emission count exceeds the prebound reservation"
            self.db.execute("UPDATE leases SET status=?,emitted=?,reason=? WHERE id=?", (status, emitted, reason, lease_id))
            if status != "COMPLETE":
                self.db.execute("UPDATE family SET stop_reason=COALESCE(stop_reason,?)", (reason or "failure",))
            self._event("FINISHED_NO_REFUND", {"lease": lease_id, "status": status, "emitted_mock_only": emitted})
        return status

    def attach_poststats(self, lease_id, report):
        need(self.db.execute("SELECT COUNT(*) FROM leases WHERE id=?", (lease_id,)).fetchone()[0] == 1, "LEASE", "Unknown lease")
        # Record as untrusted annotation only; never update charge/status/proofs.
        with self.db:
            self.db.execute("INSERT INTO observations VALUES(?,?)", (lease_id, json.dumps(report, sort_keys=True)))
            self._event("UNTRUSTED_POSTSTATS_NO_AUTHORITY", {"lease": lease_id})

    def snapshot(self):
        family = self.db.execute("SELECT * FROM family").fetchone()
        return {"scope": "CPU_MOCK_ONLY_NOT_GPU_ACCOUNTING", "family": family[0], "ceiling": family[1],
                "parent_binding": family[2], "inherited_mock_charge": family[3], "stop_reason": family[4],
                "charged_mock_reservations": self.charged(), "refunds": 0,
                "leases": [dict(zip(("id", "epoch", "plan_hash", "reserved", "status", "emitted_mock", "reason"), r)) for r in self.db.execute("SELECT * FROM leases ORDER BY rowid")],
                "poststats": [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM observations")],
                "events": [{"kind": r[0], "value": json.loads(r[1])} for r in self.db.execute("SELECT kind,payload FROM events ORDER BY id")],
                "actual_GPU_calls": 0, "physical_GPU_observations": "NOT_RUN"}

    def close(self):
        self.db.close()


class MockBackend:
    """Pure CPU emission simulator. It contains no loader or GPU API."""
    def __init__(self, scripts=None, on_enter: Callable | None = None):
        self.scripts = scripts or {}
        self.on_enter = on_enter
        self.entered = []
        self.emissions = 0

    def perform(self, step, consume):
        self.entered.append(step.phase)
        if self.on_enter:
            self.on_enter(step)
        script = self.scripts.get(step.phase, {})
        n = script.get("emissions", step.upper_bound)
        count(n, "mock script emissions", maximum=PHYSICAL_LIMIT + 1)
        fail_after = script.get("raise_after")
        for i in range(n):
            if fail_after is not None and i == fail_after:
                raise RuntimeError("Injected mock lifecycle failure")
            consume()  # enforce BEFORE the simulated physical primitive
            self.emissions += 1
        if fail_after is not None and fail_after == n:
            raise RuntimeError("Injected failure after mock emissions")


class MockController:
    def __init__(self, ledger, plan, lease_id, epoch, backend):
        need(isinstance(backend, MockBackend), "MOCK_ONLY", "Only the pure CPU simulator is supported")
        plan.validate_identity()
        need(plan.mode == "CPU_MOCK_ONLY", "NATIVE_BLOCKED", "Native execution is not implemented or authorized")
        self.ledger, self.plan, self.backend = ledger, plan, backend
        self.lease_id, self.epoch = lease_id, epoch
        self.pid, self.owner_thread = os.getpid(), threading.get_ident()
        self.active, self.finished, self.emitted = False, False, 0
        self.running = False
        self.allowed_step = None
        self.seen_steps = set()
        self.step_emitted = 0
        self.lock = threading.RLock()
        ledger.reserve(lease_id, epoch, plan)

    def _check_owner(self):
        need(os.getpid() == self.pid and threading.get_ident() == self.owner_thread, "OWNER", "Wrong process/thread for this lease")

    def _perform(self, step):
        self._check_owner()
        need(not self.active, "REENTRY", "Lifecycle callback cannot recursively dispatch")
        need(self.running and not self.finished and self.allowed_step == step.step_id,
             "ORDER", "Unplanned/out-of-order/replayed lifecycle action")
        need(step.step_id not in self.seen_steps, "REPLAY", "A planned action cannot be executed twice")
        self.plan.validate_identity()
        self.seen_steps.add(step.step_id)
        self.active, self.step_emitted = True, 0
        try:
            def consume():
                self._check_owner()
                need(self.step_emitted < step.upper_bound and self.emitted < self.plan.total_upper_bound,
                     "ENFORCEMENT", "Rejected before extra simulated physical primitive")
                self.step_emitted += 1
                self.emitted += 1
            self.backend.perform(step, consume)
        finally:
            self.active = False

    def run(self):
        self._check_owner()
        need(not self.active, "REENTRY", "Cannot reenter a lifecycle")
        need(not self.finished, "RETRY", "A completed/failed lifecycle is not reusable")
        self.ledger.mark_running(self.lease_id)
        self.running = True
        completed = set()
        failure = None
        try:
            for step in self.plan.steps:
                self.allowed_step = step.step_id
                self._perform(step)
                completed.add(step.step_id)
        except BaseException as exc:
            failure = type(exc).__name__ + ": " + str(exc)
            # These cleanup bounds were reserved before bootstrap, not added now.
            cleanup = (*self.plan.error_steps, *(s for s in self.plan.steps if s.phase == "teardown" and s.step_id not in self.seen_steps))
            for step in cleanup:
                try:
                    self.allowed_step = step.step_id
                    self._perform(step)
                except BaseException as cleanup_error:
                    failure += "; cleanup=" + type(cleanup_error).__name__ + ": " + str(cleanup_error)
                    break
        status = "FAILED" if failure else "COMPLETE"
        status = self.ledger.finish(self.lease_id, status, self.emitted, failure)
        self.finished = True
        self.running = False
        return {"scope": "CPU_MOCK_ONLY", "status": status, "failure": failure,
                "prebound_complete_lifecycle_upper_bound": self.plan.total_upper_bound,
                "reserved_charge_no_refund": self.plan.total_upper_bound,
                "runtime_enforcement": "BEFORE_EACH_SIMULATED_PRIMITIVE_ONLY",
                "observed_mock_emissions": self.emitted, "actual_GPU_calls": 0,
                "physical_GPU_observations": "NOT_RUN", "native_release": False,
                "phases_entered": self.backend.entered}


def inspect_native_candidate(phases, policy_by_actor):
    """A native manifest is a proposal, not proof; no callbacks are accepted."""
    try:
        Planner(NativeProofRegistry()).bind(phases, policy_by_actor)
    except BudgetRefusal as exc:
        return {"decision": "BLOCKED_BEFORE_NUMERICAL_DLL_LOAD", "code": exc.code,
                "reason": str(exc), "complete_lifecycle_upper_bound": None,
                "native_proof_registry_entries": len(PRODUCTION_PROOF_ALLOWLIST),
                "native_release": False, "normal_DLL_loads": 0, "CUDA_calls": 0,
                "physical_GPU_observations": "NOT_RUN"}
    raise RuntimeError("Native proof registry unexpectedly produced a plan")
