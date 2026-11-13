"""Synthetic fault injection of production-bridge accounting, not native checks."""
import argparse
import copy
import errno
import json
import os
from pathlib import Path
import sys
import threading
import socket
import struct
import time
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from bridge import BridgeController, BridgeBroker, ClosedNativeGate, C
from generate_manifest import instantiate_cpu_manifest, finalize_manifest_cpu
from test_controller import FakeClock, FakePolicy, FakeVerifier, FaultIO

OUT = None


class Fixture:
    def __init__(self, name, io=None, fail_stage=None, limits=None, fixed_scope=False):
        self.root = OUT / name
        self.root.mkdir(mode=0o700)
        self.clock = FakeClock()
        m = instantiate_cpu_manifest(name, self.clock.w, self.clock.m)
        self.worker_sha, self.launcher_sha = C.sha(b"fixed synthetic worker"), C.sha(b"fixed synthetic launcher")
        m["identity_bindings"] = {"source": C.sha(b"immutable source")}
        if fixed_scope:
            m["identity_bindings"]["scope"] = "CPU_FIXED_ELF_ONLY"
        for w in m["workers"]:
            w["executable_sha256"] = self.worker_sha
        if limits:
            m["limits"].update(limits)
        self.manifest = finalize_manifest_cpu(m)
        m = self.manifest
        self.identities = copy.deepcopy(m["identity_bindings"])
        self.verifier = FakeVerifier(m, fail_stage=fail_stage)
        self.ctrl = BridgeController(self.root / "run", m, self.verifier, FakePolicy(),
            lambda: {"status": "PASS"}, lambda: self.identities, clock=self.clock, io=io)
        self.job = self.root / "JOB.json"
        self.job.write_bytes(C.encoded({"CPU_SYNTHETIC_ONLY": True,
            "deadline_wall": self.clock.w + 600, "deadline_mono": self.clock.m + 600}))
        self.lease, self.domain, self.device = (C.sha(x) for x in (b"lease", b"domain", b"NO_GPU"))
    def preflight(self):
        for d in self.manifest["deployments"]:
            if d["kind"] == "PREFLIGHT":
                self.ctrl.synthetic_preflight(d["id"])
    def reserve(self, index=0):
        return self.ctrl.reserve_launch(self.manifest["workers"][index]["id"], self.lease,
            self.job, self.launcher_sha, self.domain, self.device)
    def close(self):
        self.ctrl.store.close()

    def domain_object(self, **changed):
        from resource_domain import DomainBinding, ResourceDomain
        owner = C.process_identity()
        value = {"run_id": self.manifest["run_id"], "manifest_sha256": self.ctrl.store.fingerprint,
            "owner_uid": owner["uid"], "device_uuid_sha256": self.device, "stage": C.STAGES[0],
            "worker_id": self.manifest["workers"][0]["id"], "executable_sha256": self.worker_sha,
            "launcher_executable_sha256": self.launcher_sha, "lease_sha256": self.lease,
            "lease_issuer_sha256": "1" * 64,
            "supervisor": {"pid": owner["pid"], "start_time": owner["start_ticks"], "uid": owner["uid"],
                           "boot_id_sha256": C.sha(owner["boot_id"].encode())},
            "parent": {"path_sha256": "2" * 64, "device": 1, "inode": 1, "uid": owner["uid"],
                       "mount_id": 1, "controllers": ["memory", "pids"]},
            "window": {"start_wall": self.clock.w, "start_mono": self.clock.m,
                "deadline_wall": self.clock.w + 600, "deadline_mono": self.clock.m + 600,
                "last_launch_wall": self.clock.w + 100, "last_launch_mono": self.clock.m + 100}}
        value.update(changed)
        return ResourceDomain(DomainBinding.from_dict(value))


class BridgeFaultTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = []
    def fixture(self, suffix="", **kwargs):
        f = Fixture(self._testMethodName + suffix, **kwargs)
        self.fixtures.append(f)
        return f
    def tearDown(self):
        for f in self.fixtures:
            f.close()
    def rejects(self, fn):
        with self.assertRaises((C.Closed, OSError, KeyError)):
            fn()

    def test_native_gate_has_no_action_or_reservation(self):
        f = self.fixture()
        before = f.ctrl.state["counts"]
        self.rejects(lambda: f.ctrl.native_launch("/not/an/ELF", {"approved": True}))
        self.assertEqual(before, f.ctrl.state["counts"])
        self.assertTrue(f.ctrl.store.dead)

    def test_cpu_proposal_cannot_carry_approval(self):
        f = self.fixture()
        bad = copy.deepcopy(f.manifest); bad["approval"] = {"approved": True}
        bad["manifest_sha256"] = C.manifest_fingerprint(bad)
        self.rejects(lambda: C.Store(f.root / "new", bad, f.clock))
        self.assertFalse((f.root / "new").exists())

    def test_stage_order_denied_before_launcher(self):
        f = self.fixture(); f.preflight()
        self.rejects(lambda: f.reserve(6))
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_preflight_is_mandatory(self):
        f = self.fixture()
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 0)

    def test_legacy_start_bypass_denied(self):
        f = self.fixture(); f.preflight()
        self.rejects(lambda: f.ctrl.start_mock_worker("worker", {}, f.lease, f.worker_sha))
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_legacy_claim_bypass_denied(self):
        f = self.fixture(); f.preflight(); f.reserve()
        self.rejects(lambda: f.ctrl.claim("run", f.ctrl.store.fingerprint, "worker", f.lease, {}))
        self.assertEqual(f.ctrl.state["worker_index"], 0)

    def test_budget_is_reserved_before_any_process(self):
        f = self.fixture(); f.preflight(); result = f.reserve()
        self.assertIsNone(f.ctrl.launcher)
        self.assertIsNone(f.ctrl.state["active_worker"])
        self.assertEqual(f.ctrl.state["counts"]["placements"], 3)
        self.assertEqual(result["phase"], "RESERVED")

    def test_resource_object_other_device_rejected_before_budget(self):
        f = self.fixture(); f.preflight()
        domain = f.domain_object(device_uuid_sha256="3" * 64)
        w = f.manifest["workers"][0]
        self.rejects(lambda: f.ctrl.reserve_launch(w["id"], f.lease, f.job, f.launcher_sha,
            domain.sha256, f.device, domain=domain))
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_resource_object_other_stage_rejected_before_budget(self):
        f = self.fixture(); f.preflight()
        domain = f.domain_object(stage=C.STAGES[2])
        w = f.manifest["workers"][0]
        self.rejects(lambda: f.ctrl.reserve_launch(w["id"], f.lease, f.job, f.launcher_sha,
            domain.sha256, f.device, domain=domain))
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_fixed_process_entry_cannot_omit_resource_object(self):
        f = self.fixture(fixed_scope=True); f.preflight()
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_duplicate_does_not_refund_or_reserve_again(self):
        f = self.fixture(); f.preflight(); f.reserve()
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 3)
        self.assertTrue(f.ctrl.store.dead)

    def test_concurrent_launch_one_slot_and_fail_closed(self):
        f = self.fixture(); f.preflight()
        errors = []
        def call():
            try: f.reserve()
            except BaseException as e: errors.append(str(e))
        threads = [threading.Thread(target=call) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(errors), 1)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 3)
        self.assertTrue(f.ctrl.store.dead)

    def test_changed_source_denied(self):
        f = self.fixture(); f.preflight()
        f.identities["source"] = C.sha(b"replaced source")
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_bridge_record_alias_or_replacement_denied(self):
        f = self.fixture(); f.preflight(); f.reserve()
        path = f.ctrl.store.root / f.ctrl.state["bridge"]["file"]
        with path.open("ab") as out: out.write(b" ")
        self.rejects(f.ctrl._guard)
        self.assertTrue(f.ctrl.store.dead)

    def test_manifest_or_device_cannot_change(self):
        f = self.fixture(); f.preflight(); f.reserve()
        self.rejects(lambda: f.ctrl.hello(f.manifest["run_id"], f.ctrl.store.fingerprint,
            "launch/" + f.manifest["workers"][0]["id"], f.lease, f.ctrl.bridge["job_sha256"],
            f.domain, C.sha(b"different GPU"), C.STAGES[0], C.process_identity()))

    def test_expired_lease_or_deadline_denied(self):
        f = self.fixture(); f.preflight(); f.reserve()
        f.clock.m += 601
        self.rejects(f.ctrl._guard)

    def test_actual_job_shorter_deadline_is_binding(self):
        f = self.fixture(); f.preflight()
        f.job.write_bytes(C.encoded({"deadline_wall": f.clock.w + 3, "deadline_mono": f.clock.m + 3}))
        f.reserve()
        f.clock.m += 3
        self.rejects(f.ctrl._guard)
        self.assertLess(f.clock.m, f.ctrl.store.end_mono)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 3)

    def test_expired_job_denied_before_reservation(self):
        f = self.fixture(); f.preflight()
        f.job.write_bytes(C.encoded({"deadline_wall": f.clock.w, "deadline_mono": f.clock.m + 3}))
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_job_cannot_relax_worker_or_global_deadline(self):
        f = self.fixture(); f.preflight()
        f.job.write_bytes(C.encoded({"deadline_wall": f.clock.w + 601, "deadline_mono": f.clock.m + 601}))
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_nonfinite_job_deadline_denied(self):
        f = self.fixture(); f.preflight()
        f.job.write_bytes(b'{"deadline_wall":NaN,"deadline_mono":1003}')
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_lost_lock_denied_without_removing_old_lock(self):
        import fcntl
        f = self.fixture(); f.preflight(); f.reserve()
        lock = f.ctrl.store.lock_fd
        inode = os.fstat(lock).st_ino
        fcntl.flock(lock, fcntl.LOCK_UN)
        self.rejects(f.ctrl._guard)
        self.assertEqual((f.ctrl.store.root / "LOCK").stat().st_ino, inode)

    def test_unbound_or_replayed_exit_cannot_release_slot(self):
        f = self.fixture(); f.preflight(); f.reserve()
        self.rejects(lambda: f.ctrl.confirm_worker_exit(f.manifest["workers"][0]["id"]))
        self.assertEqual(f.ctrl.state["worker_index"], 0)

    def test_no_result_even_exited_process_is_not_success(self):
        f = self.fixture(); f.preflight(); f.reserve()
        self.rejects(lambda: f.ctrl._bound_exit_probe({"pid": 1, "exited": True, "exit_code": 0}))

    def test_quota_failure_has_no_launcher(self):
        f = self.fixture(limits={"placements": 2}); f.preflight()
        self.rejects(f.reserve)
        self.assertIsNone(f.ctrl.launcher)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_partial_journal_reservation_retains_upper_bound(self):
        io = FaultIO(); f = self.fixture(io=io); f.preflight()
        io.failure = "short"
        self.rejects(f.reserve)
        f.close()
        result = C.Store.inspect(f.ctrl.store.root, f.manifest)
        self.assertFalse(result["resume_authorized"])
        self.assertEqual(result["counts_charge_upper_bound"]["placements"], 3)

    def test_fsync_failure_is_not_success(self):
        io = FaultIO(); f = self.fixture(io=io); f.preflight()
        io.failure = "fsync"
        self.rejects(f.reserve)
        self.assertTrue((f.ctrl.store.root / "STOP.json").exists())
        f.close()
        result = C.Store.inspect(f.ctrl.store.root, f.manifest)
        self.assertEqual(result["counts_charge_upper_bound"]["placements"], 3)
        self.assertFalse(result["resume_authorized"])

    def test_disk_full_does_not_retry(self):
        io = FaultIO(); f = self.fixture(io=io); f.preflight()
        io.failure = "ENOSPC"
        self.rejects(f.reserve)
        self.assertTrue(f.ctrl.store.dead)
        self.rejects(f.reserve)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 2)

    def test_existing_state_is_inspect_only(self):
        f = self.fixture(); f.preflight(); f.reserve(); f.close()
        result = C.Store.inspect(f.ctrl.store.root, f.manifest)
        self.assertFalse(result["resume_authorized"])
        self.rejects(lambda: C.Store(f.ctrl.store.root, f.manifest, f.clock))

    def test_cold_first_difference_preserved_and_strong_never_starts(self):
        f = self.fixture(fail_stage=C.STAGES[2])
        # Explicit synthetic setup, not a completed launch or numerical claim.
        def setup(s):
            s["stage_index"] = 2
            s["worker_index"] = 6
            s["completed_workers"] = [w["id"] for w in f.manifest["workers"][:6]]
        f.ctrl.store.event("SYNTHETIC_STAGE_GATE_FIXTURE", {}, setup)
        f.ctrl._bridge_record({"phase": "COMPLETE", "worker": "SYNTHETIC_ONLY"}, "SYNTHETIC_EXIT_FIXTURE")
        self.rejects(lambda: f.ctrl.checkpoint(C.STAGES[2]))
        report = C.strict_json((f.ctrl.store.root / ("CHECKPOINT-" + C.STAGES[2] + ".json")).read_bytes())
        self.assertEqual(report["first_difference"]["left_hex"], "003c")
        self.assertEqual(report["first_difference"]["right_hex"], "013c")
        self.rejects(lambda: f.reserve(6))
        self.assertEqual(f.ctrl.state["counts"]["requests"], 0)
        self.assertEqual(f.ctrl.state["counts"]["placements"], 0)
        self.assertEqual(f.verifier.calls, [C.STAGES[2]])

    def test_slow_partial_frame_cannot_extend_absolute_deadline(self):
        reader, writer = socket.socketpair()
        stopped = []
        def drip():
            try:
                for byte in struct.pack("!I", 10) + b"0123456789":
                    writer.send(bytes([byte]))
                    time.sleep(.04)
            except OSError:
                stopped.append(True)
            finally:
                writer.close()
        t = threading.Thread(target=drip); t.start()
        start = time.monotonic()
        try:
            self.rejects(lambda: BridgeBroker.receive(reader, start + .1))
        finally:
            reader.close()
            t.join(2)
        self.assertFalse(t.is_alive())
        self.assertLess(time.monotonic() - start, 2)

    def test_exact_bounded_frame(self):
        a, b = socket.socketpair()
        try:
            raw = b"CPU_ONLY"
            b.sendall(struct.pack("!I", len(raw)) + raw)
            self.assertEqual(BridgeBroker.receive(a, time.monotonic() + 1), "CPU_ONLY")
        finally:
            a.close(); b.close()

    def test_truncated_frame_never_becomes_a_result(self):
        a, b = socket.socketpair()
        try:
            b.sendall(struct.pack("!I", 20) + b"PASS")
            b.close()
            self.rejects(lambda: BridgeBroker.receive(a, time.monotonic() + 1))
        finally:
            a.close(); b.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--out", required=True)
    args, rest = p.parse_known_args()
    OUT = Path(args.out)
    if not OUT.is_absolute() or OUT.exists():
        raise RuntimeError("fresh output root required")
    OUT.mkdir(mode=0o700)
    unittest.main(argv=[sys.argv[0]] + rest)
