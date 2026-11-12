"""Retained synthetic CPU fixtures. Never imports a model/backend library."""
import argparse
import copy
import errno
import fcntl
import json
import os
from pathlib import Path
import socket
import threading
import unittest
import controller as C
from generate_manifest import instantiate_cpu_manifest
from late_bind import load_template, prepare_stage_jobs

OUT = None


def synthetic_reference_inputs(manifest):
    """Saved fixed inputs plus artificial responses; NEVER a native R result."""
    out = {}
    for job in load_template()["jobs"]:
        if job["role"] != C.STAGES[0]:
            continue
        for episode in job["episodes"]:
            first = episode["operations"][0]
            prompt = first.get("canonical_ids") or first.get("expected_canonical_ids")
            for op in episode["operations"]:
                ident = op["id"]
                q = op.get("canonical_ids") or op.get("expected_canonical_ids") or prompt + [3]
                generated = op.get("forced_terminal_ids") or [3] * op["cap"]
                snap = lambda phase: {"operation_id":ident,"phase":phase,
                    "run_id":manifest["run_id"],"file":"SYNTHETIC_ONLY/"+C.sha(
                        (ident+phase).encode())+".json","sha256":"a"*64,
                    "executable_sha256":"a"*64}
                out[ident] = {"canonical_ids":q,"retained_head":0,
                    "generated_ids":generated,"generation_cap":op["cap"],
                    "stop_reason":"EOG" if generated[-1] in (128247,151643,151645,
                        151662,151663,151664) else "CAP",
                    "post_reconcile_snapshot":snap("POST_RECONCILE"),
                    "terminal_snapshot":snap("TERMINAL")}
    return out


class FakeClock:
    def __init__(self):
        self.w, self.m = 1700000000., 1000.
    def wall(self):
        return self.w
    def mono(self):
        return self.m


class FakePolicy:
    def check(self, snapshot, now, phase="DURING_WORK"):
        return {"status": snapshot["status"], "gates": [{"scope": "SYNTHETIC_ONLY"}],
                "native_execution_authorized": False}


class FakeVerifier:
    def __init__(self, manifest, fail_stage=None, missing=False, raises=False):
        self.manifest, self.fail_stage = manifest, fail_stage
        self.missing, self.raises, self.calls = missing, raises, []
    def verify(self, stage):
        self.calls.append(stage)
        if self.raises:
            raise OSError("synthetic raw capture short read")
        checks = [{"id": i, "status": "PASS"} for i in self.manifest["stage_check_ids"][stage]]
        if self.missing:
            checks.pop()
        if stage == self.fail_stage:
            checks[0].update(status="NUMERIC_FAIL",
                first_difference={"coordinate": {"layer": 35, "kv_head": 7,
                                                 "position": 0, "dimension": 127},
                                  "left_hex": "003c", "right_hex": "013c"})
        result = {"status": "FAIL" if stage == self.fail_stage else "PASS", "checks": checks,
                "native_qualified": False, "scope": "SYNTHETIC_TEST_VERIFIER_NOT_NATIVE",
                "first_difference": checks[0].get("first_difference"),
                "capture_file_sha256": {}}
        if stage == C.STAGES[0]:
            result["reference_inputs"] = synthetic_reference_inputs(self.manifest)
        return result
    def verify_sealed(self, files):
        return {"status":"PASS","scope":"SYNTHETIC_EMPTY_SEAL_FIXTURE_ONLY"}


class FaultIO(C.IO):
    def __init__(self):
        self.failure = None
    def write(self, fd, data):
        leaf = os.readlink("/proc/self/fd/" + str(fd))
        if self.failure in ("short", "ENOSPC") and leaf.endswith("/journal.jsonl"):
            mode, self.failure = self.failure, None
            if mode == "ENOSPC":
                raise OSError(errno.ENOSPC, "synthetic disk full")
            return os.write(fd, data[:len(data) // 2])
        return super().write(fd, data)
    def sync(self, fd):
        leaf = os.readlink("/proc/self/fd/" + str(fd))
        if self.failure == "fsync" and leaf.endswith("/journal.jsonl"):
            self.failure = None
            raise OSError(errno.EIO, "synthetic fsync failure")
        return super().sync(fd)


class Fixture:
    def __init__(self, name, fail_stage=None, missing=False, io=None, mutate=None):
        self.root = OUT / name
        self.clock = FakeClock()
        self.manifest = instantiate_cpu_manifest(name, self.clock.w, self.clock.m)
        self.manifest["identity_bindings"] = {"bound": C.sha(b"frozen synthetic inputs")}
        self.binary = C.sha(b"synthetic CPU worker, never a native executable")
        for w in self.manifest["workers"]:
            w["executable_sha256"] = self.binary
        if mutate:
            mutate(self.manifest)
        self.manifest["manifest_sha256"] = C.manifest_fingerprint(self.manifest)
        self.identities = copy.deepcopy(self.manifest["identity_bindings"])
        self.resource = {"status": "PASS"}
        self.peer = None
        self.exit = {"exited": True, "exit_code": 0, "exit_confirmed": True,
                     "supervisor_status": "OWNED_CHILD_EXITED", "logs_status": "COMPLETE"}
        self.verifier = FakeVerifier(self.manifest, fail_stage, missing)
        self.ctrl = C.Controller(self.root, self.manifest, self.verifier,
            FakePolicy(), lambda: self.resource, lambda: self.identities,
            self.clock, io, peer_probe=lambda pid: self.peer,
            executable_probe=lambda pid: self.binary,
            exit_probe=lambda peer: None if self.exit is None else {**self.exit, "peer": peer})
        self.lease = "b" * 64
    def preflights(self):
        for d in self.manifest["deployments"]:
            if d["kind"] == "PREFLIGHT":
                self.ctrl.synthetic_preflight(d["id"])
    def begin(self, index=0, actual_peer=None):
        w = self.manifest["workers"][index]
        self.peer = actual_peer or {"pid": 10000 + index, "start_ticks": 100 + index,
                                   "uid": os.getuid(), "boot_id": "synthetic-boot"}
        self.ctrl.start_mock_worker(w["id"], self.peer, self.lease, self.binary)
        self.ctrl.claim(self.manifest["run_id"], self.ctrl.store.fingerprint,
                        w["id"], self.lease, self.peer)
        for k in ("backend", "model", "context", "placement"):
            self.ctrl.command(w["id"], k, w["deployment_id"], 1)
        return w
    def request(self, w, ident):
        self.ctrl.command(w["id"], "request", ident, 1)
        self.ctrl.command(w["id"], "rows", ident, 1)
        self.ctrl.command(w["id"], "bytes", ident, 2, "raw")
        self.ctrl.command(w["id"], "bytes", ident, 1, "metadata")
        self.ctrl.command(w["id"], "sync", ident, 0, "file")
        self.ctrl.command(w["id"], "finish", ident, 0, "COMPLETED")
    def worker(self, index):
        w = self.begin(index)
        for ident in w["request_ids"]:
            self.request(w, ident)
        self.ctrl.close_worker(w["id"])
        self.ctrl.confirm_worker_exit(w["id"])
    def stage(self, stage):
        for i, w in enumerate(self.manifest["workers"]):
            if w["stage"] == stage:
                self.worker(i)
        self.ctrl.checkpoint(stage)
    def close(self):
        self.ctrl.store.close()


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = []
    def fx(self, suffix="", **kwargs):
        f = Fixture(self._testMethodName + suffix, **kwargs)
        self.fixtures.append(f)
        return f
    def tearDown(self):
        for f in self.fixtures:
            f.close()                     # fixtures/STATE/journal remain on disk
    def rejects(self, fn):
        with self.assertRaises((C.Closed, OSError, KeyError)):
            fn()

    def test_full_72_request_stage_order_and_inspect_only(self):
        f = self.fx();f.preflights()
        for stage in C.STAGES:
            f.stage(stage)
        self.assertEqual(f.ctrl.state["status"], "COMPLETE")
        self.assertEqual(f.ctrl.state["counts"]["requests"], 72)
        self.assertEqual(f.ctrl.state["counts"]["rows"], 72)  # mock accounting, no decode
        for key in ("backend_inits", "models", "contexts", "placements"):
            self.assertEqual(f.ctrl.state["counts"][key], 10)
        self.assertEqual(f.verifier.calls, list(C.STAGES))
        f.close()
        r = C.Store.inspect(f.root, f.manifest)
        self.assertEqual(r["status"], "SEALED_INSPECT_ONLY")
        self.assertFalse(r["resume_authorized"])
        self.rejects(lambda: C.Store(f.root, f.manifest, f.clock))

    def test_stage_reordering_stops_before_any_worker(self):
        f = self.fx();f.preflights()
        w = f.manifest["workers"][6]
        self.rejects(lambda: f.ctrl.start_mock_worker(w["id"],
            {"pid": 99, "start_ticks": 1, "uid": os.getuid(), "boot_id": "boot"},
            f.lease, f.binary))
        self.assertTrue(f.ctrl.store.dead)
        self.assertEqual(f.ctrl.state["counts"]["requests"], 0)

    def test_missing_preflight_is_no_launch(self):
        f = self.fx()
        self.rejects(lambda: f.begin())
        self.assertEqual(f.ctrl.state["counts"]["placements"], 0)

    def test_duplicate_worker_and_parallel_worker_are_poisoned(self):
        f = self.fx();f.preflights();f.begin()
        before = copy.deepcopy(f.ctrl.state["counts"])
        self.rejects(lambda: f.begin(1))
        self.assertEqual(f.ctrl.state["counts"], before)
        self.assertTrue(f.ctrl.store.dead)

    def test_same_process_cannot_be_independent_repeat(self):
        f = self.fx();f.preflights();f.worker(0)
        previous = f.peer
        w = f.manifest["workers"][1]
        self.rejects(lambda: f.ctrl.start_mock_worker(w["id"], previous, f.lease, f.binary))
        self.assertTrue(f.ctrl.store.dead)

    def test_close_accounting_waits_for_observed_process_exit(self):
        f = self.fx();f.preflights();w=f.begin()
        for ident in w["request_ids"]:
            f.request(w, ident)
        f.ctrl.close_worker(w["id"]);f.exit=None
        self.assertEqual(f.ctrl.confirm_worker_exit(w["id"])["status"],
                         "WAITING_FOR_OWNED_WORKER_EXIT")
        self.assertEqual(f.ctrl.state["worker_index"], 0)
        self.rejects(lambda: f.begin(1))

    def test_failed_exit_prevents_next_worker(self):
        f = self.fx();f.preflights();w=f.begin()
        for ident in w["request_ids"]:
            f.request(w, ident)
        f.ctrl.close_worker(w["id"]);f.exit={"exited": True, "exit_code": 77}
        self.rejects(lambda: f.ctrl.confirm_worker_exit(w["id"]))
        self.assertEqual(f.ctrl.state["worker_index"], 0)

    def test_identity_change_stops_before_request(self):
        f = self.fx();f.preflights();w=f.begin()
        f.identities={"bound": C.sha(b"changed")}
        self.rejects(lambda: f.ctrl.command(w["id"], "request", w["request_ids"][0], 1))
        self.assertEqual(f.ctrl.state["counts"]["requests"], 0)

    def test_owner_lease_and_actual_binary_bindings(self):
        for field in ("lease", "pid", "binary"):
            f = self.fx("_"+field);f.preflights()
            w=f.manifest["workers"][0];f.peer={"pid":99,"start_ticks":1,
                "uid":os.getuid(),"boot_id":"boot"}
            f.ctrl.start_mock_worker(w["id"],f.peer,f.lease,f.binary)
            if field=="binary":
                f.ctrl.executable_probe=lambda pid:"a"*64
            peer={**f.peer,"pid":100} if field=="pid" else f.peer
            self.rejects(lambda: f.ctrl.claim(f.manifest["run_id"],
                f.ctrl.store.fingerprint,w["id"],"c"*64 if field=="lease" else f.lease,peer))
            self.assertTrue(f.ctrl.store.dead)

    def test_lock_lost_or_replaced_never_deleted(self):
        for mode in ("lost", "replaced"):
            f=self.fx("_"+mode);f.preflights()
            if mode=="lost":
                fcntl.flock(f.ctrl.store.lock_fd,fcntl.LOCK_UN)
            else:
                os.rename(f.root/"LOCK",f.root/"LOCK.original")
                (f.root/"LOCK").write_text("unknown owner")
            self.rejects(lambda:f.begin())
            self.assertTrue((f.root/"LOCK").exists())
            self.assertTrue(f.ctrl.store.dead)

    def test_unknown_existing_state_and_lock_untouched(self):
        root=OUT/(self._testMethodName+"_unknown")
        root.mkdir();(root/"LOCK").write_bytes(b"foreign");(root/"STATE.json").write_bytes(b"old")
        f=self.fx();m=f.manifest
        self.rejects(lambda:C.Store(root,m,f.clock))
        self.assertEqual((root/"LOCK").read_bytes(),b"foreign")
        self.assertEqual((root/"STATE.json").read_bytes(),b"old")

    def test_worker_crash_and_PID_reuse_stop(self):
        f=self.fx();f.preflights();w=f.begin()
        f.peer={**f.peer,"start_ticks":f.peer["start_ticks"]+1}
        self.rejects(lambda:f.ctrl.command(w["id"],"request",w["request_ids"][0],1))
        self.assertEqual(f.ctrl.state["counts"]["requests"],0)

    def test_cold_first_difference_stops_strong_and_preserves_bytes_report(self):
        f=self.fx(fail_stage="COLD_CANONICAL_ORACLE");f.preflights()
        f.stage(C.STAGES[0]);f.stage(C.STAGES[1])
        for i,w in enumerate(f.manifest["workers"]):
            if w["stage"]==C.STAGES[2]:
                f.worker(i)
        self.rejects(lambda:f.ctrl.checkpoint(C.STAGES[2]))
        report=json.loads((f.root/("CHECKPOINT-"+C.STAGES[2]+".json")).read_text())
        self.assertEqual(report["first_difference"]["coordinate"]["layer"],35)
        self.assertEqual(f.ctrl.state["counts"]["requests"],54)
        self.assertFalse(any("STRONG" in w for w in f.ctrl.state["completed_workers"]))
        self.rejects(lambda:f.begin(6))

    def test_repeat_failure_blocks_cold(self):
        f=self.fx(fail_stage="REPEAT_RESIDENT_R");f.preflights();f.stage(C.STAGES[0])
        for i,w in enumerate(f.manifest["workers"]):
            if w["stage"]==C.STAGES[1]:
                f.worker(i)
        self.rejects(lambda:f.ctrl.checkpoint(C.STAGES[1]))
        self.assertEqual(f.ctrl.state["counts"]["requests"],36)
        self.rejects(lambda:f.begin(4))

    def test_missing_raw_coverage_or_reader_failure_blocks_next_stage(self):
        for mode in ("missing","read"):
            f=self.fx("_"+mode,missing=mode=="missing");f.preflights()
            f.worker(0);f.worker(1)
            if mode=="read":
                f.verifier.raises=True
            self.rejects(lambda:f.ctrl.checkpoint(C.STAGES[0]))
            self.assertEqual(f.ctrl.state["worker_index"],2)
            self.assertEqual(f.ctrl.state["stage_index"],0)

    def test_rows_requests_and_raw_metadata_limits_keep_spent_counts(self):
        for mode in ("rows","requests","raw","metadata"):
            mutate=(lambda m:m["limits"].update(requests=0)) if mode=="requests" else None
            if mode in ("raw", "metadata"):
                def mutate(m):
                    first = next(iter(m["requests"].values()))
                    first[mode + "_byte_limit"] = 0
            f=self.fx("_"+mode,mutate=mutate);f.preflights();w=f.begin();ident=w["request_ids"][0]
            if mode=="requests":
                self.rejects(lambda:f.ctrl.command(w["id"],"request",ident,1))
            else:
                f.ctrl.command(w["id"],"request",ident,1)
                if mode=="rows":
                    self.rejects(lambda:f.ctrl.command(w["id"],"rows",ident,
                        f.manifest["requests"][ident]["row_limit"]+1))
                else:
                    self.rejects(lambda:f.ctrl.command(w["id"],"bytes",ident,1,mode))
                self.assertEqual(f.ctrl.state["counts"]["requests"],1)
            self.assertTrue(f.ctrl.store.dead)

    def test_partial_journal_fsync_and_disk_full_no_retry_reentry(self):
        for mode in ("short","fsync","ENOSPC"):
            io=FaultIO();f=self.fx("_"+mode,io=io);f.preflights();w=f.begin();ident=w["request_ids"][0]
            f.ctrl.command(w["id"],"request",ident,1);io.failure=mode
            self.rejects(lambda:f.ctrl.command(w["id"],"rows",ident,1))
            self.assertTrue(f.ctrl.store.dead)
            f.close();report=C.Store.inspect(f.root,f.manifest)
            self.assertEqual(report["status"],"UNCLEAN_OR_ACTIVE_INSPECT_ONLY")
            self.assertFalse(report["resume_authorized"])
            self.assertEqual(report["counts_charge_upper_bound"]["rows"],1)

    def test_resource_insufficiency_unknown_owner_and_timeout_stop(self):
        for mode in ("FAIL","BLOCKED","wall","mono","lease"):
            f=self.fx("_"+mode);f.preflights();w=f.begin()
            if mode in ("FAIL","BLOCKED"):
                f.resource={"status":mode}
            elif mode=="wall":
                f.clock.w+=18001
            elif mode=="mono":
                f.clock.m+=18001
            else:
                f.clock.m+=601
            self.rejects(lambda:f.ctrl.command(w["id"],"request",w["request_ids"][0],1))
            self.assertTrue(f.ctrl.store.dead)

    def test_budget_journal_ceiling_is_not_auto_extended(self):
        f=self.fx();f.preflights();w=f.begin()
        f.ctrl.store.manifest["limits"]["journal_bytes"]=f.ctrl.store.journal_bytes+1
        self.rejects(lambda:f.ctrl.command(w["id"],"request",w["request_ids"][0],1))
        self.assertTrue(f.ctrl.store.dead)

    def test_unknown_request_and_failed_finish_cannot_skip_panel(self):
        for mode in ("unknown","failed","partialclose"):
            f=self.fx("_"+mode);f.preflights();w=f.begin();ident=w["request_ids"][0]
            if mode=="unknown":
                self.rejects(lambda:f.ctrl.command(w["id"],"request","unplanned",1))
            elif mode=="failed":
                f.ctrl.command(w["id"],"request",ident,1)
                self.rejects(lambda:f.ctrl.command(w["id"],"finish",ident,0,"FAILED"))
            else:
                self.rejects(lambda:f.ctrl.close_worker(w["id"]))
            self.assertTrue(f.ctrl.store.dead)

    def test_native_gate_is_closed_before_any_launch_or_placement(self):
        f=self.fx();before=copy.deepcopy(f.ctrl.state["counts"])
        self.rejects(lambda:f.ctrl.native_launch({"approved":True}))
        self.assertEqual(f.ctrl.state["counts"],before)
        self.assertTrue(f.ctrl.store.dead)

    def test_invalid_manifest_expansion_or_stale_hash_creates_no_run(self):
        f=self.fx()
        for mode in ("expansion", "stale", "native"):
            manifest=copy.deepcopy(f.manifest)
            target=OUT/(self._testMethodName+"_"+mode)
            if mode=="expansion":
                manifest["limits"]["requests"]=77
                manifest["manifest_sha256"]=C.manifest_fingerprint(manifest)
            elif mode=="stale":
                manifest["run_id"]="silently-changed"
            else:
                manifest["mode"]="NATIVE"
                manifest["native_execution_authorized"]=True
                manifest["manifest_sha256"]=C.manifest_fingerprint(manifest)
            self.rejects(lambda:C.Store(target,manifest,f.clock))
            self.assertFalse(target.exists())

    def test_worker_exit_zero_does_not_override_output_failure(self):
        f=self.fx();f.preflights();w=f.begin()
        for ident in w["request_ids"]:
            f.request(w,ident)
        f.ctrl.close_worker(w["id"]);f.exit["logs_status"]="OUTPUT_LIMIT"
        self.rejects(lambda:f.ctrl.confirm_worker_exit(w["id"]))
        self.assertEqual(f.ctrl.state["worker_index"],0)

    def test_prior_capture_seal_change_blocks_next_stage_worker(self):
        f=self.fx();f.preflights();f.stage(C.STAGES[0])
        f.ctrl.sealed_files={"frozen.bin":"c"*64}
        f.verifier.verify_sealed=lambda files:{"status":"FAIL","reason":"old bytes changed"}
        self.rejects(lambda:f.begin(2))
        self.assertEqual(f.ctrl.state["counts"]["requests"],18)

    def test_manifest_file_or_memory_change_poisoned(self):
        for mode in ("file","memory"):
            f=self.fx("_"+mode);f.preflights()
            if mode=="file":
                with (f.root/"MANIFEST.json").open("ab") as out:out.write(b" ")
            else:
                f.ctrl.manifest["limits"]["rows"]+=1
            self.rejects(lambda:f.begin())
            self.assertEqual(f.ctrl.state["counts"]["requests"],0)

    def test_caller_input_alias_cannot_rewrite_worker_policy(self):
        f=self.fx();f.preflights()
        expected=copy.deepcopy(f.ctrl.workers[0])
        f.manifest["workers"][0]["request_ids"].clear()
        f.manifest["workers"][0]["deployment_id"]="caller-replaced-policy"
        self.assertEqual(f.ctrl.worker_by_id[expected["id"]],expected)
        f.peer={"pid":10000,"start_ticks":1,"uid":os.getuid(),"boot_id":"boot"}
        f.ctrl.start_mock_worker(expected["id"],f.peer,f.lease,f.binary)
        f.ctrl.claim(f.ctrl.manifest["run_id"],f.ctrl.store.fingerprint,
                     expected["id"],f.lease,f.peer)
        for kind in ("backend","model","context","placement"):
            f.ctrl.command(expected["id"],kind,expected["deployment_id"],1)
        for ident in expected["request_ids"]:
            f.request(expected,ident)
        f.ctrl.close_worker(expected["id"]);f.ctrl.confirm_worker_exit(expected["id"])
        self.assertEqual(f.ctrl.state["counts"]["requests"],8)

    def test_public_state_is_copy_and_internal_state_tamper_stops(self):
        f=self.fx();view=f.ctrl.state
        view["counts"]["requests"]=76;view["stage_index"]=3
        self.assertEqual(f.ctrl.state["counts"]["requests"],0)
        self.assertEqual(f.ctrl.state["stage_index"],0)
        f.ctrl.store.state["stage_index"]=3
        self.rejects(lambda:f.preflights())
        self.assertTrue(f.ctrl.store.dead)

    def test_state_status_only_tamper_never_reports_complete(self):
        f=self.fx();f.preflights();f.close()
        state=json.loads((f.root/"STATE.json").read_text())
        state["status"]="COMPLETE"
        (f.root/"STATE.json").write_bytes(C.encoded(state))
        report=C.Store.inspect(f.root,f.manifest)
        self.assertEqual(report["status"],"UNCLEAN_OR_ACTIVE_INSPECT_ONLY")
        self.assertFalse(report["state_journal_consistent"])
        self.assertFalse(report["resume_authorized"])

    def test_lost_lock_then_competitor_same_inode_is_unknown_holder(self):
        f=self.fx();f.preflights()
        fcntl.flock(f.ctrl.store.lock_fd,fcntl.LOCK_UN)
        ready_read,ready_write=os.pipe();done_read,done_write=os.pipe()
        pid=os.fork()
        if pid==0:
            os.close(ready_read);os.close(done_write)
            fd=os.open(f.root/"LOCK",os.O_RDWR)
            fcntl.flock(fd,fcntl.LOCK_EX)
            os.write(ready_write,b"1");os.read(done_read,1)
            os._exit(0)
        os.close(ready_write);os.close(done_read)
        try:
            self.assertEqual(os.read(ready_read,1),b"1")
            self.rejects(lambda:f.begin())
            self.assertTrue(f.ctrl.store.dead)
            self.assertIn("holder",f.ctrl.store.error)
        finally:
            os.write(done_write,b"1");os.close(done_write);os.close(ready_read)
            os.waitpid(pid,0)

    def test_parallel_entry_reserves_at_most_one_worker(self):
        f=self.fx();f.preflights();worker=f.ctrl.workers[0]
        peers={p:{"pid":p,"start_ticks":1,"uid":os.getuid(),"boot_id":"boot"}
               for p in (10001,10002)}
        f.ctrl.peer_probe=lambda pid:peers[pid]
        barrier=threading.Barrier(2);results=[]
        def start(pid):
            barrier.wait()
            try:
                f.ctrl.start_mock_worker(worker["id"],peers[pid],f.lease,f.binary)
                results.append("RESERVED")
            except C.Closed:
                results.append("STOPPED")
        threads=[threading.Thread(target=start,args=(pid,)) for pid in peers]
        for thread in threads:thread.start()
        for thread in threads:thread.join(5)
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertEqual(sorted(results),["RESERVED","STOPPED"])
        self.assertEqual(f.ctrl.state["counts"]["placements"],3)

    def test_R_handoff_persisted_and_expected_ids_do_not_force_free_producer(self):
        f=self.fx();f.preflights();f.stage(C.STAGES[0])
        repeat=f.ctrl.prepare_stage_inputs(C.STAGES[1])
        self.assertEqual(len(repeat),2)
        for job in repeat:
            self.assertFalse(job["execution_authorized"])
            self.assertIsNone(job["controller_owner"])
            for episode in job["episodes"]:
                for op in episode["operations"]:
                    if episode["kind"]=="NATURAL_FIXED_USER_CONTINUATION":
                        self.assertTrue(op["expected_canonical_ids"])
                        self.assertNotIn("canonical_ids",op)
                        self.assertIn("OWN_FREE",op["input_scope"])
        self.assertTrue((f.root/"REFERENCE_INPUTS.json").is_file())

    def test_cold_job_uses_sealed_R_ids_and_actual_retained_head(self):
        f=self.fx();f.preflights();f.stage(C.STAGES[0]);f.stage(C.STAGES[1])
        jobs=f.ctrl.prepare_stage_inputs(C.STAGES[2])
        cert=f.ctrl._reference_certificate()
        for job in jobs:
            for episode in job["episodes"]:
                for op in episode["operations"]:
                    peer=op["id"].replace("/COLD_CANONICAL_ORACLE/","/RESIDENT_R/")
                    self.assertEqual(op["canonical_ids"],cert["reference_inputs"][peer]["canonical_ids"])
                    self.assertEqual(op["reference_retained_head"],cert["reference_inputs"][peer]["retained_head"])
                    self.assertFalse(job["execution_authorized"])

    def test_R_handoff_tampering_stops_before_repeat(self):
        f=self.fx();f.preflights();f.stage(C.STAGES[0])
        with (f.root/"REFERENCE_INPUTS.json").open("ab") as out:out.write(b" ")
        self.rejects(lambda:f.begin(2))
        self.assertEqual(f.ctrl.state["counts"]["requests"],18)

    def test_missing_R_handoff_cannot_be_replaced_by_PASS_receipt(self):
        f=self.fx();f.preflights();f.worker(0);f.worker(1)
        old=f.verifier.verify
        def stripped(stage):
            r=old(stage);r.pop("reference_inputs",None);return r
        f.verifier.verify=stripped
        self.rejects(lambda:f.ctrl.checkpoint(C.STAGES[0]))
        self.assertEqual(f.ctrl.state["stage_index"],0)

    def test_late_binding_cannot_skip_stage_order(self):
        f=self.fx()
        self.rejects(lambda:f.ctrl.prepare_stage_inputs(C.STAGES[2]))
        self.assertEqual(f.ctrl.state["counts"]["requests"],0)

    def test_real_socket_owner_and_sequence_checks_cpu_only(self):
        f=self.fx();f.preflights();w=f.begin(actual_peer=C.process_identity())
        # The manual begin already claimed; a second HELLO must be rejected.
        broker=C.Broker(f.ctrl,str(f.root/"ipc"),timeout=1)
        errors=[]
        def serve():
            try:broker.serve_one()
            except BaseException as e:errors.append(str(e))
        thread=threading.Thread(target=serve);thread.start()
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
            client.connect(str(f.root/"ipc"))
            C.send_frame(client,"HELLO\t2\t"+f.manifest["run_id"].encode().hex()+"\t"+
                f.ctrl.store.fingerprint+"\t"+w["id"].encode().hex()+"\t"+f.lease)
            with self.assertRaises((C.Closed,ConnectionError,OSError)):
                C.recv_frame(client)
        thread.join(3);broker.close()
        self.assertFalse(thread.is_alive());self.assertTrue(errors)
        self.assertTrue(f.ctrl.store.dead)

    def test_controller_crash_is_inspection_only_and_never_refunds(self):
        f=self.fx();manifest=f.manifest;f.close()
        root=OUT/(self._testMethodName+"_child")
        pid=os.fork()
        if pid==0:
            try:
                clock=FakeClock();manifest=copy.deepcopy(manifest)
                st=C.Store(root,manifest,clock)
                st.event("CPU_CRASH_RESERVATION",{"mock":True},
                    lambda s:s["counts"].update(requests=1,rows=1))
                os._exit(86)
            except BaseException:
                os._exit(87)
        got,status=os.waitpid(pid,0)
        self.assertEqual(got,pid);self.assertEqual(os.WEXITSTATUS(status),86)
        report=C.Store.inspect(root,manifest)
        self.assertEqual(report["last_readable_valid_journal_counts"]["requests"],1)
        self.assertEqual(report["status"],"UNCLEAN_OR_ACTIVE_INSPECT_ONLY")
        self.rejects(lambda:C.Store(root,manifest,FakeClock()))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args,rest=parser.parse_known_args()
    OUT=Path(args.out)
    if not OUT.is_absolute() or OUT.exists():
        raise SystemExit("fresh absolute retained CPU fixture directory required")
    OUT.mkdir(mode=0o700)
    unittest.main(argv=[__file__]+rest,verbosity=2)

