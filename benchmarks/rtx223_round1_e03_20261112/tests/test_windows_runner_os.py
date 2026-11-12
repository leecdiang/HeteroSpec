"""Own-child Windows OS tests only. No CUDA/model executables are called."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE_PYTHON = getattr(sys, "_base_executable", sys.executable)
sys.path.insert(0, str(ROOT / "continuation/safety"))
import windows_runner as wr


@unittest.skipUnless(os.name == "nt", "Windows OS mechanism tests")
class WindowsRunnerOS(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "continuation/safety")
        self.root = Path(self.temp.name)
        self.uuid = "CPU-TEST-" + uuid.uuid4().hex
        self.plan = json.loads((ROOT / "RESOURCE_PLAN.json").read_bytes())
        self.plan["epoch"] = self.uuid
        self.plan["maximums"]["native_gpu_seconds"] = 8
        self.parent = {"reserved": {k: 0 for k in wr.KEYS}, "attempts": [], "fixture": "CPU_TEST_ONLY"}
        self.ledger = wr.FamilyLedger(self.root / "ledger.sqlite", self.plan, self.parent, wr.canonical(self.plan), self.uuid + "-e02")
        self.observations = []

    def tearDown(self):
        self.ledger.close()
        keep = os.environ.get("HS_SAFETY_KEEP_ROOT")
        if keep:
            destination = Path(keep) / self._testMethodName
            shutil.copytree(self.root, destination, ignore=shutil.ignore_patterns("*.lock"))
            (destination / "OS_OBSERVATIONS.json").write_text(json.dumps(self.observations, indent=2), encoding="utf8")
        self.temp.cleanup()

    def lock(self):
        return wr.DeviceLock(self.root / "gpu.lock", self.uuid, [self.root / "foreign.lock"])

    def run_fixture(self, mode, timeout=2, heartbeat_timeout=0.7):
        reservation = {k: (timeout + 0.5 if k == "native_gpu_seconds" else 0) for k in wr.KEYS}
        return wr.run_owned_cpu_fixture(self.ledger, self.lock(), "attempt-" + mode,
                 [BASE_PYTHON, wr.__file__, "--cpu-fixture", mode], self.root / mode,
                 timeout=timeout, heartbeat_timeout=heartbeat_timeout, startup_grace=0.7, reservation=reservation)

    def test_process_bound_lock_release_and_unknown_marker_refusal(self):
        with self.lock():
            self.assertTrue((self.root / "gpu.lock").exists())
        self.assertFalse((self.root / "gpu.lock").exists())
        marker = self.root / "gpu.lock"
        marker.write_text("unknown owner", encoding="utf8")
        with self.assertRaises(wr.Refusal):
            self.lock().acquire()
        self.assertEqual(marker.read_text(encoding="utf8"), "unknown owner")

    def test_cross_process_lock_contention(self):
        script = ("import sys;sys.path.insert(0," + repr(str(ROOT / 'continuation/safety')) + ");"
                  "import windows_runner as w;"
                  "lock=w.DeviceLock(" + repr(str(self.root / 'gpu.lock')) + "," + repr(self.uuid) + ");"
                  "\ntry: lock.acquire()\nexcept w.Refusal: sys.exit(23)\nelse: lock.close();sys.exit(0)")
        with self.lock():
            p = subprocess.run([sys.executable, "-B", "-c", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        self.assertEqual(p.returncode, 23, p.stdout.decode(errors="replace"))

    def test_legacy_lock_never_modified(self):
        f = self.root / "foreign.lock"
        f.write_bytes(b"unknown original task")
        with self.assertRaisesRegex(wr.Refusal, "legacy"):
            self.lock().acquire()
        self.assertEqual(f.read_bytes(), b"unknown original task")

    def test_contained_success_records_pid_and_final_counters(self):
        r = self.run_fixture("success")
        self.assertEqual(r["status"], "COMPLETE", r)
        self.assertGreater(r["worker_pid"], 0)
        self.assertEqual(r["actual"]["kernel_launches"], 0)
        self.assertEqual(self.ledger.snapshot()["attempts"][0]["status"], "COMPLETE")

    def test_crash_charges_reservation_and_stops_family(self):
        r = self.run_fixture("crash")
        self.assertEqual(r["status"], "FAILED", r)
        self.assertEqual(r["exit_code"], 17)
        self.assertIsNone(r["actual"]["kernel_launches"])
        with self.assertRaisesRegex(wr.Refusal, "stopped"):
            self.ledger.reserve("retry", "failure_margin", {k: 0 for k in wr.KEYS})
        self.assertEqual(self.ledger.totals()["native_gpu_seconds"], 2.5)

    def test_timeout_kills_only_owned_worker(self):
        r = self.run_fixture("timeout", timeout=0.4)
        self.assertEqual(r["status"], "TIMEOUT", r)
        self.assertFalse((self.root / "gpu.lock").exists())
        self.assertTrue((self.root / "timeout/worker.log").exists())

    def test_missing_heartbeat_stops_owned_worker(self):
        r = self.run_fixture("silent", timeout=2, heartbeat_timeout=0.1)
        self.assertEqual(r["status"], "HEARTBEAT_LOST", r)

    def test_same_family_window_survives_reopen(self):
        remaining = self.ledger.start_window()
        self.assertGreater(remaining, 0)
        first = self.ledger.snapshot()["global_window"]["wall_deadline"]
        self.ledger.close()
        self.ledger = wr.FamilyLedger(self.root / "ledger.sqlite", self.plan, self.parent, wr.canonical(self.plan), self.uuid + "-e03")
        self.assertEqual(self.ledger.snapshot()["global_window"]["wall_deadline"], first)
        self.assertLessEqual(self.ledger.start_window(), remaining)

    def test_parent_binding_cannot_reset_budget(self):
        altered = copy.deepcopy(self.parent)
        altered["reserved"]["model_requests"] = 1
        with self.assertRaisesRegex(wr.Refusal, "binding changed"):
            wr.FamilyLedger(self.root / "ledger.sqlite", self.plan, altered, wr.canonical(self.plan), "new")

    def test_native_boolean_cannot_release_gpu(self):
        with self.assertRaisesRegex(wr.Refusal, "native gate"):
            wr.run_owned_cpu_fixture(self.ledger, self.lock(), "wrong", [sys.executable, "-c", "pass"], self.root / "wrong", native_release={"gpu_admitted": True})

    def test_native_release_function_stays_closed_without_authority(self):
        with self.assertRaisesRegex(wr.Refusal, "native gate"):
            wr.validate_native_release("not-a-proof.json", "a" * 64, "b" * 64, BASE_PYTHON)

    def test_complete_cannot_hide_unknown_actual_counts(self):
        a = {k: 0 for k in wr.KEYS}
        self.ledger.reserve("unknown-complete", "failure_margin", a)
        actual = {k: None for k in wr.KEYS}
        status = self.ledger.finish("unknown-complete", "COMPLETE", actual)
        self.assertEqual(status, "COUNTER_INVALID")
        self.assertIsNotNone(self.ledger.snapshot()["global_window"]["stop_reason"])

    def test_observed_counter_overrun_is_retained_and_charged(self):
        r = self.run_fixture("overrun")
        self.assertEqual(r["status"], "OVERRUN", r)
        self.assertEqual(r["actual"]["kernel_launches"], 1)
        self.assertTrue(r["actual_counts_are_lower_bounds"])
        self.assertEqual(self.ledger.totals()["kernel_launches"], 1)

    def test_late_legacy_marker_stops_only_owned_process(self):
        r = self.run_fixture("legacy_marker")
        self.assertEqual(r["status"], "FAILED", r)
        self.assertIn("legacy/foreign", r["reason"])
        self.assertEqual((self.root / "foreign.lock").read_text(encoding="utf8"), "OWN CPU FIXTURE simulated legacy task")

    def test_timeout_contains_owned_descendant(self):
        r = self.run_fixture("descendant", timeout=0.5)
        self.assertEqual(r["status"], "TIMEOUT", r)
        record = json.loads((self.root / "descendant/descendant.json").read_bytes())
        self.observe_terminated(record)

    def test_controller_crash_releases_lock_and_kills_owned_job(self):
        target = self.root / "controller-owned.json"
        lock_path = self.root / "controller.lock"
        script = ("import sys,os,json;from pathlib import Path;sys.path.insert(0," + repr(str(ROOT / "continuation/safety")) + ");import windows_runner as w;"
                  "lock=w.DeviceLock(" + repr(str(lock_path)) + "," + repr(self.uuid) + ");lock.acquire();"
                  "worker=w.JobWorker([" + repr(BASE_PYTHON) + ",' -c'.strip(),'import time;time.sleep(30)']," + repr(str(self.root)) + ",os.environ.copy()," + repr(str(self.root / 'controller-child.log')) + ").spawn_suspended();worker.resume();"
                  "Path(" + repr(str(target)) + ").write_text(json.dumps({'pid':worker.pid,'creation':worker.creation}));os._exit(19)")
        p = subprocess.run([BASE_PYTHON, "-B", "-c", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        self.assertEqual(p.returncode, 19, p.stdout.decode(errors="replace"))
        record = json.loads(target.read_bytes())
        self.observe_terminated(record)
        self.assertFalse(lock_path.exists(), "Dead controller retained delete-on-close lock")

    def observe_terminated(self, record):
        handle = wr.OpenProcess(0x00100000 | 0x1000, False, record["pid"])
        if handle:
            try:
                self.assertEqual(wr.process_creation(handle), record["creation"])
                result = wr.Wait(handle, 1000)
                self.observations.append({"pid": record["pid"], "creation": record["creation"], "query": "PROCESS_HANDLE", "wait": result})
                self.assertEqual(result, 0, "Owned process outlived closed Job object")
            finally:
                wr.CloseHandle(handle)
        else:
            error = wr.C.get_last_error()
            self.observations.append({"pid": record["pid"], "creation": record["creation"], "query": "OPEN_PROCESS_NULL", "winerror": error})
            self.assertEqual(error, 87, "OpenProcess absence not established: access denied is not termination")

    def test_failure_before_assignment_kills_new_suspended_child(self):
        worker = wr.JobWorker([BASE_PYTHON, "-c", "import time;time.sleep(30)"], self.root, os.environ.copy(), self.root / "preassign.log")
        original = wr.process_creation
        birth = []
        def fail_after_read(handle):
            birth.append(original(handle))
            raise wr.Refusal("injected creation-time read postcheck failure")
        with mock.patch.object(wr, "process_creation", side_effect=fail_after_read):
            with self.assertRaisesRegex(wr.Refusal, "injected"):
                worker.spawn_suspended()
        self.assertIsNone(worker.process)
        self.assertIsNone(worker.job)
        self.observe_terminated({"pid": worker.pid, "creation": birth[0]})

    def test_exit_observed_after_deadline_is_not_complete(self):
        original = wr.JobWorker.exit_code
        def delayed_query(worker):
            time.sleep(0.25)
            return original(worker)
        with mock.patch.object(wr.JobWorker, "exit_code", delayed_query):
            r = self.run_fixture("success", timeout=0.05)
        self.assertEqual(r["status"], "TIMEOUT", r)


if __name__ == "__main__":
    unittest.main()
