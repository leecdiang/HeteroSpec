"""CPU rehearsal of the complete owned launch chain; native admission stays closed.

No driver, backend, model, context, placement, or numerical library is imported.
ProductionGate is not a JSON approval interpreter. The only executable path here
accepts the separately built, frozen, std-only CPU fixture pair.
"""
import copy
import fcntl
import hashlib
import math
import os
from pathlib import Path
import select
import socket
import stat
import struct
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "admission_controller_20261112"
sys.path.insert(0, str(OLD))
import controller as C


def file_hash(path, cap=None):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        s = os.fstat(fd)
        C.need(stat.S_ISREG(s.st_mode) and (cap is None or s.st_size <= cap),
               "regular bounded source/file required")
        h = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return h.hexdigest()
            h.update(chunk)
    finally:
        os.close(fd)


def parent_pid(pid):
    raw = Path("/proc", str(pid), "stat").read_text()
    return int(raw[raw.rfind(")") + 2:].split()[1])


def cgroup_membership(pid):
    # Read-only: not a cgroup activation or evidence of an exclusive GPU window.
    return Path("/proc", str(pid), "cgroup").read_text()


class ClosedNativeGate:
    @staticmethod
    def launch(*args, **kwargs):
        raise C.Closed("NATIVE_PRODUCTION_GATE_CLOSED: no fork, backend, model or placement")


class BridgeController(C.Controller):
    """Binds one launch, one pre-exec child, and its live supervisor to a stage.

    Supplied PASS receipts are never exit authority. A supervisor message must
    arrive on the live source-bound peer's socket; a separately held child pidfd
    must be readable, frozen logs must agree, and this controller must reap its
    own launcher before the old accounting controller may release the worker.
    """
    def __init__(self, *args, **kwargs):
        C.need("exit_probe" not in kwargs, "external exit receipts are forbidden")
        super().__init__(*args, **kwargs)
        self.bridge = None
        self.bridge_seq = 0
        self.launcher = None
        self.launcher_peer = None
        self.child_pidfd = None
        self.domain = None
        self.logs = {}
        self._internal_exit = None
        self._inside_v3_claim = False
        self._inside_v3_confirm = False
        self.exit_probe = self._bound_exit_probe

    def _bridge_record(self, value, kind, detail=None, mutation=None):
        value = copy.deepcopy(value)
        self.bridge_seq += 1
        name = "BRIDGE-%04d.json" % self.bridge_seq
        raw = C.encoded(value)
        C.need(len(raw) <= 32768 and self.bridge_seq <= 128, "bounded bridge evidence")
        self.store._immutable(name, raw)
        descriptor = {"file": name, "bytes": len(raw), "sha256": C.sha(raw),
                      "phase": value["phase"], "worker": value["worker"]}
        def apply(s):
            if mutation:
                mutation(s)
            s["bridge"] = descriptor
        # The original capped journal contains only a compact descriptor; the
        # immutable record is fsynced before the transition/ACK is persisted.
        out = self._change(kind, detail or {}, apply)
        self.bridge = value
        return out

    def _bridge_guard(self):
        if self.bridge is None:
            C.need(self.state.get("bridge") is None, "bridge memory/state divergence")
            return
        C.need(self.store.read_immutable(self.state["bridge"]) == self.bridge,
               "bridge identity changed outside its journal")
        if self.bridge["phase"] == "COMPLETE":
            return
        C.need(self.clock.wall() < self.bridge["deadline_wall"] and
               self.clock.mono() < self.bridge["deadline_mono"], "launch lease/deadline expired")
        if self.domain is not None:
            if self.bridge["phase"] == "REAPED":
                pass  # Domain close is recorded; only the source-bound exit release remains.
            elif self.bridge["phase"] in ("RESERVED", "LAUNCHER_REGISTERED"):
                self.domain.before_launch()
            elif (self.child_pidfd is not None and
                  select.select([self.child_pidfd], [], [], 0)[0]):
                self.domain.assert_after_exit(self.bridge["child_peer"])
            elif self.bridge["phase"] not in ("REAPED",):
                self.domain.assert_live()
        peer = self.bridge.get("launcher_peer")
        if (peer is not None and self.bridge["phase"] not in ("REAPED", "COMPLETE") and
                not getattr(self, "_owner_reaped_pending", False)):
            C.need(C.process_identity(peer["pid"]) == peer,
                   "launch owner disappeared or PID identity changed")
            exited_owned = (self.bridge["phase"] == "SUPERVISOR_CLOSED" and
                os.waitid(os.P_PID, peer["pid"], os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None)
            if not exited_owned:
                C.need(self._executable_hash(peer["pid"]) == self.bridge["launcher_sha256"],
                       "live supervisor executable changed")

    def _guard(self, phase="DURING_WORK"):
        try:
            super()._guard(phase)
            # During construction there is not yet a bridge object.
            if hasattr(self, "bridge"):
                self._bridge_guard()
        except BaseException as error:
            self.store.poison("bridge guard: " + str(error))
            raise

    @C.stop_on_error
    def reserve_launch(self, worker, lease, job_path, launcher_sha256, domain_sha256,
                       device_sha256, domain=None, log_limit=12 * 1024 * 1024):
        self._guard("BEFORE_LAUNCH")
        self._check_sealed_files()
        C.need(self.bridge is None or self.bridge["phase"] == "COMPLETE",
               "one launch only; no duplicate, concurrent or recovered launch")
        state = self.state
        C.need(state["status"] == "READY" and state["active_worker"] is None and
               len(state["preflights"]) == 2, "unready/unknown launch state")
        C.need(state["worker_index"] < len(self.workers), "all workers consumed")
        expected = self.workers[state["worker_index"]]
        C.need(expected["id"] == worker and expected["stage"] == C.STAGES[state["stage_index"]],
               "launch order or stage violation")
        if state["stage_index"]:
            self._reference_certificate()
        for value in (lease, launcher_sha256, domain_sha256, device_sha256):
            C.digest(value)
        C.integer(log_limit, 1)
        C.need(log_limit <= 12 * 1024 * 1024, "per-log pool expansion")
        job_sha256 = file_hash(job_path, 1024 * 1024)
        fd = os.open(job_path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            raw = os.read(fd, 1024 * 1024 + 1)
        finally:
            os.close(fd)
        C.need(len(raw) <= 1024 * 1024 and C.sha(raw) == job_sha256,
               "job changed during deadline/input binding")
        job = C.strict_json(raw)
        for axis, current, ceiling in (("wall", self.clock.wall(), self.store.end_wall),
                                       ("mono", self.clock.mono(), self.store.end_mono)):
            deadline = job.get("deadline_" + axis)
            C.need(type(deadline) in (int, float) and math.isfinite(deadline) and
                   current < deadline <= min(ceiling, current + expected["timeout_seconds"]),
                   "actual job deadline missing/expired/relaxes worker or global window")
        if domain is None:
            C.need(self.manifest["identity_bindings"].get("scope") != "CPU_FIXED_ELF_ONLY",
                   "actual fixed-process bridge requires its bound resource domain")
        else:
            from resource_domain import ResourceDomain
            C.need(type(domain) is ResourceDomain and domain.sha256 == domain_sha256,
                   "resource object is not the frozen canonical domain")
            binding = domain.binding.as_dict()
            owner = C.process_identity()
            expected_binding = {"run_id": self.manifest["run_id"], "manifest_sha256": self.store.fingerprint,
                "worker_id": worker, "stage": expected["stage"], "device_uuid_sha256": device_sha256,
                "lease_sha256": lease, "executable_sha256": expected["executable_sha256"],
                "launcher_executable_sha256": launcher_sha256, "owner_uid": owner["uid"]}
            C.need(all(binding[key] == value for key, value in expected_binding.items()) and
                binding["supervisor"] == {"pid": owner["pid"], "start_time": owner["start_ticks"],
                    "uid": owner["uid"], "boot_id_sha256": C.sha(owner["boot_id"].encode())},
                "resource object and launch tuple/owner differ")
            C.need(all(binding["window"]["deadline_" + axis] >= job["deadline_" + axis]
                       for axis in ("wall", "mono")), "resource lease does not cover actual job")
        value = {"schema": "hs.N1bridge.v3", "scope": "CPU_REHEARSAL_NOT_NATIVE",
            "phase": "RESERVED", "worker": worker, "stage": expected["stage"],
            "run_id": self.manifest["run_id"], "manifest_sha256": self.store.fingerprint,
            "lease_sha256": lease, "job_sha256": job_sha256,
            "worker_sha256": expected["executable_sha256"],
            "launcher_sha256": launcher_sha256, "domain_sha256": domain_sha256,
            "device_sha256": device_sha256, "log_limit": log_limit,
            "controller": C.process_identity(),
            "deadline_wall": job["deadline_wall"], "deadline_mono": job["deadline_mono"],
            "native_execution_authorized": False}
        def reserve(s):
            self._increment(s, "placements", 1)
            s["deployments"].append("placement:" + expected["deployment_id"])
        # Reservation and log credit precede launcher Popen/fork. Failures keep it.
        self._bridge_record(value, "BRIDGE_PRELAUNCH_RESERVE", {"worker": worker}, reserve)
        self.domain = domain
        if self.domain is not None:
            self.domain.before_launch()
        return copy.deepcopy(value)

    @C.stop_on_error
    def register_launcher(self, owned_popen, logs):
        self._guard()
        C.need(self.bridge is not None and self.bridge["phase"] == "RESERVED" and
               self.launcher is None, "launcher already registered or unreserved")
        peer = C.process_identity(owned_popen.pid)
        C.need(parent_pid(peer["pid"]) == os.getpid() and peer["uid"] == os.geteuid(),
               "launcher must be this controller's freshly owned child")
        C.need(self._executable_hash(peer["pid"]) == self.bridge["launcher_sha256"],
               "launcher source/binary identity mismatch")
        C.need(set(logs) == {"stdout", "stderr"}, "both frozen log descriptors required")
        descriptors = {}
        for name, fd in logs.items():
            st = os.fstat(fd)
            C.need(stat.S_ISREG(st.st_mode) and st.st_uid == os.geteuid() and
                   st.st_nlink == 1 and st.st_size == 0, "owned fresh single-link log required")
            descriptors[name] = {"dev": st.st_dev, "ino": st.st_ino}
        C.need(descriptors["stdout"] != descriptors["stderr"], "log alias")
        value = {**self.bridge, "phase": "LAUNCHER_REGISTERED", "launcher_peer": peer,
                 "logs": descriptors}
        self._bridge_record(value, "BRIDGE_BIND_LAUNCHER", {"worker": value["worker"]})
        self.launcher, self.launcher_peer = owned_popen, peer
        self.logs = dict(logs)

    def _hello_binding(self, run, manifest, client, lease, job, domain, device, stage, peer):
        self._guard()
        b = self.bridge
        C.need(b is not None and
            (run, manifest, lease, job, domain, device, stage) ==
            (b["run_id"], b["manifest_sha256"], b["lease_sha256"], b["job_sha256"],
             b["domain_sha256"], b["device_sha256"], b["stage"]),
            "v3 frozen job/run/domain/device/stage/lease mismatch")
        if client == "launch/" + b["worker"]:
            C.need(b["phase"] == "LAUNCHER_REGISTERED" and peer == self.launcher_peer,
                   "launch HELLO outside its bound live owner")
            return "launcher"
        if client == "supervise/" + b["worker"]:
            C.need(b["phase"] == "WORKER_CLOSED" and peer == self.launcher_peer,
                   "supervisor receipt outside its bound source/exit phase")
            return "supervisor"
        C.need(client == b["worker"] and b["phase"] == "LAUNCHER_CLOSED",
               "worker HELLO before durable launcher closure or reused receipt")
        return "worker"

    @C.stop_on_error
    def hello(self, run, manifest, client, lease, job, domain, device, stage, peer):
        b = self.bridge
        if (b is not None and client == b["worker"] and b["phase"] == "LAUNCHER_CLOSED" and
                peer == b["child_peer"] and self.domain is not None):
            C.need((run, manifest, lease, job, domain, device, stage) ==
                (b["run_id"], b["manifest_sha256"], b["lease_sha256"], b["job_sha256"],
                 b["domain_sha256"], b["device_sha256"], b["stage"]), "post-exec identity tuple changed")
            self.domain.observe_postexec(peer)
        role = self._hello_binding(run, manifest, client, lease, job, domain, device, stage, peer)
        if role == "worker":
            self._inside_v3_claim = True
            try:
                super().claim(run, manifest, client, lease, peer)
            finally:
                self._inside_v3_claim = False
            self._bridge_record({**self.bridge, "phase": "WORKER_ACTIVE"},
                                "BRIDGE_WORKER_HELLO", {"worker": client})
        return role

    @C.stop_on_error
    def bind_child(self, peer, child_pid, detail):
        self._guard()
        b = self.bridge
        C.need(b["phase"] == "LAUNCHER_REGISTERED" and peer == self.launcher_peer,
               "BINDCHILD outside the live launch owner")
        C.need(set(detail) == {"child", "parent", "worker_executable_sha256", "worker_executable_fd", "job_fd"},
               "exact BINDCHILD fields required")
        child = C.process_identity(child_pid)
        C.need(detail["child"] == child and detail["parent"] == peer and
               detail["worker_executable_sha256"] == b["worker_sha256"] and
               child["uid"] == peer["uid"] and child["boot_id"] == peer["boot_id"] and
               parent_pid(child_pid) == peer["pid"], "pre-exec child identity/ancestry changed")
        # Child is still in the launcher image behind its private barrier.
        C.need(self._executable_hash(child_pid) == b["launcher_sha256"],
               "child escaped pre-exec barrier before identity binding")
        image_fd = C.integer(detail["worker_executable_fd"], 3)
        C.need(image_fd < 1048576, "bounded pre-exec image FD")
        with open("/proc/%d/fd/%d" % (child_pid, image_fd), "rb") as image:
            C.need(stat.S_ISREG(os.fstat(image.fileno()).st_mode), "worker image must be regular")
            seals = fcntl.fcntl(image.fileno(), fcntl.F_GET_SEALS)
            required_seals = fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE
            C.need(seals & required_seals == required_seals, "CPU worker image must be immutable sealed memfd")
            h = hashlib.sha256()
            for block in iter(lambda: image.read(1024 * 1024), b""):
                h.update(block)
            C.need(h.hexdigest() == b["worker_sha256"], "held pre-exec worker image changed")
        job_fd = C.integer(detail["job_fd"], 3)
        C.need(job_fd < 1048576 and job_fd != image_fd, "bounded distinct frozen job FD")
        with open("/proc/%d/fd/%d" % (child_pid, job_fd), "rb") as job:
            js = os.fstat(job.fileno())
            C.need(stat.S_ISREG(js.st_mode) and 0 < js.st_size <= 1024 * 1024,
                   "held job is not a bounded regular file")
            C.need(fcntl.fcntl(job.fileno(), fcntl.F_GET_SEALS) & required_seals == required_seals,
                   "held job bytes must be an immutable sealed image")
            C.need(C.sha(job.read(1024 * 1024 + 1)) == b["job_sha256"], "held pre-exec job changed")
        C.need(cgroup_membership(child_pid) == cgroup_membership(peer["pid"]),
               "child and launch owner resource domains differ")
        C.need(self.child_pidfd is None, "child pidfd already bound")
        pidfd = os.pidfd_open(child_pid, 0)
        try:
            C.need(C.process_identity(child_pid) == child, "PID reused during pidfd binding")
            if self.domain is not None:
                self.domain.bind_child(child, peer)
            def apply(s):
                C.need(s["active_worker"] is None, "another worker active")
                C.need(all(x["peer"] != child for x in s["completed_worker_bindings"].values()),
                       "independent repeat requires a new process identity")
                s["active_worker"] = {"id": b["worker"], "peer": child,
                    "lease_sha256": b["lease_sha256"], "executable_sha256": b["worker_sha256"],
                    "claimed": False, "lease_deadline_wall": b["deadline_wall"],
                    "lease_deadline_mono": b["deadline_mono"]}
                s["status"] = "WORKER_RESERVED_CPU_ONLY"
            self._bridge_record({**b, "phase": "CHILD_BOUND", "child_peer": child,
                                 "inherited_cgroup_sha256": C.sha(cgroup_membership(child_pid).encode())},
                "BRIDGE_BINDCHILD_PREEXEC", {"worker": b["worker"]}, apply)
            self.child_pidfd = pidfd
        except BaseException:
            os.close(pidfd)
            raise

    @C.stop_on_error
    def close_launcher(self, peer):
        self._guard()
        C.need(self.bridge["phase"] == "CHILD_BOUND" and peer == self.launcher_peer,
               "launcher close requires its bound pre-exec child")
        return self._bridge_record({**self.bridge, "phase": "LAUNCHER_CLOSED"},
                                  "BRIDGE_LAUNCH_SESSION_CLOSED", {"worker": self.bridge["worker"]})

    @C.stop_on_error
    def start_mock_worker(self, *args, **kwargs):
        raise C.Closed("legacy unbound start bypass refused; v3 pre-exec bridge required")

    @C.stop_on_error
    def claim(self, *args, **kwargs):
        raise C.Closed("legacy HELLO/claim bypass refused; use source-bound v3 session")

    @C.stop_on_error
    def command(self, worker, kind, ident, amount=0, detail=""):
        C.need(self.bridge is not None and self.bridge["phase"] == "WORKER_ACTIVE" and
               self.bridge["worker"] == worker, "worker command outside the v3 launch chain")
        return super().command(worker, kind, ident, amount, detail)

    @C.stop_on_error
    def close_worker(self, worker):
        C.need(self.bridge is not None and self.bridge["phase"] == "WORKER_ACTIVE" and
               self.bridge["worker"] == worker, "v3 worker closure order")
        super().close_worker(worker)
        return self._bridge_record({**self.bridge, "phase": "WORKER_CLOSED"},
                                  "BRIDGE_WORKER_ACCOUNTING_CLOSED", {"worker": worker})

    def _verify_log(self, name, count):
        C.integer(count)
        fd = self.logs[name]
        s = os.fstat(fd)
        expected = self.bridge["logs"][name]
        C.need((s.st_dev, s.st_ino) == (expected["dev"], expected["ino"]) and
               stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and
               s.st_size == count and count <= self.bridge["log_limit"],
               "log identity, partial length, link or byte cap failure")
        os.fsync(fd)
        h = hashlib.sha256()
        for offset in range(0, count, 65536):
            raw = os.pread(fd, min(65536, count - offset), offset)
            C.need(len(raw) == min(65536, count - offset), "incomplete supervisor log read")
            h.update(raw)
        return {**expected, "bytes": count, "sha256": h.hexdigest()}

    @C.stop_on_error
    def supervisor_result(self, peer, child_pid, result):
        self._guard()
        b = self.bridge
        C.need(b["phase"] == "WORKER_CLOSED" and peer == self.launcher_peer and
               child_pid == b["child_peer"]["pid"], "unbound or stale supervisor result")
        required = {"status", "child_pid", "exit_confirmed", "wait_status", "stdout_complete",
                    "stderr_complete", "stdout_bytes", "stderr_bytes", "stop_delivered", "output_partial",
                    "stdout", "stderr"}
        C.need(set(result) == required, "exact source-bound supervisor result required")
        # A failed result is persisted before refusal, including logs if readable.
        value = {**b, "phase": "SUPERVISOR_RESULT", "supervisor_result": result}
        self._bridge_record(value, "BRIDGE_BOUND_EXIT_RESULT", {"worker": b["worker"]})
        C.need(self.child_pidfd is not None and select.select([self.child_pidfd], [], [], 0)[0],
               "process exit not independently visible through the bound pidfd")
        C.integer(result["wait_status"])
        C.need(result["child_pid"] == child_pid and result["status"] == "OWNED_CHILD_EXITED" and
               result["exit_confirmed"] is True and result["stdout_complete"] is True and
               result["stderr_complete"] is True and result["output_partial"] is False and
               result["stop_delivered"] is False and os.WIFEXITED(result["wait_status"]) and
               os.WEXITSTATUS(result["wait_status"]) == 0,
               "supervisor uncertain/failure/log incomplete; accounting closure is not exit success")
        logs = {name: self._verify_log(name, result[name + "_bytes"])
                for name in ("stdout", "stderr")}
        for name, descriptor in logs.items():
            C.need(result[name] == {"device": descriptor["dev"], "inode": descriptor["ino"],
                                   "bytes": descriptor["bytes"], "sha256": descriptor["sha256"]},
                   "live supervisor log hash/descriptor differs from independently read held log")
        return self._bridge_record({**self.bridge, "verified_logs": logs},
                                  "BRIDGE_VERIFY_FROZEN_LOGS", {"worker": b["worker"]})

    @C.stop_on_error
    def close_supervisor(self, peer):
        self._guard()
        C.need(self.bridge["phase"] == "SUPERVISOR_RESULT" and peer == self.launcher_peer and
               "verified_logs" in self.bridge, "supervisor cannot close without a verified result")
        return self._bridge_record({**self.bridge, "phase": "SUPERVISOR_CLOSED"},
                                  "BRIDGE_SUPERVISOR_SESSION_CLOSED", {"worker": self.bridge["worker"]})

    @C.stop_on_error
    def reap_launcher(self, timeout=3):
        self._guard()
        C.need(self.bridge["phase"] == "SUPERVISOR_CLOSED" and self.launcher is not None,
               "launcher cannot be reaped as a replacement for missing result")
        C.need(0 < timeout <= 3, "bounded source-bound supervisor reap timeout")
        # Waitid WNOWAIT first preserves PID identity for /proc check before reap.
        until = time.monotonic() + timeout
        while os.waitid(os.P_PID, self.launcher.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            C.need(time.monotonic() < until, "supervisor did not terminate after its closure")
            time.sleep(.005)
        C.need(C.process_identity(self.launcher.pid) == self.launcher_peer,
               "launcher identity changed before reap")
        pid, raw = os.waitpid(self.launcher.pid, 0)
        C.need(pid == self.launcher_peer["pid"] and os.WIFEXITED(raw) and
               os.WEXITSTATUS(raw) == 0, "bound supervisor terminated unsuccessfully")
        self.launcher.returncode = 0
        # After successful waitpid the owner is deliberately gone; persist while
        # bypassing only its liveness check, not the store/resource/deadline gate.
        try:
            self._owner_reaped_pending = True
            self._bridge_record({**self.bridge, "phase": "REAPED"}, "BRIDGE_OWNED_SUPERVISOR_REAPED",
                                {"worker": self.bridge["worker"], "wait_status": raw})
        finally:
            self._owner_reaped_pending = False
        if self.domain is not None:
            self.domain.close_result("OWNED_CPU_CHILD_EXITED")
        self._internal_exit = {"peer": self.bridge["child_peer"], "exited": True,
            "exit_code": 0, "exit_confirmed": True, "supervisor_status": "OWNED_CHILD_EXITED",
            "logs_status": "COMPLETE"}

    def _bound_exit_probe(self, peer):
        C.need(self._inside_v3_confirm and self.bridge["phase"] == "REAPED" and
               self._internal_exit is not None and peer == self._internal_exit["peer"],
               "unbound/replayed exit receipt refused")
        return copy.deepcopy(self._internal_exit)

    @C.stop_on_error
    def confirm_worker_exit(self, worker):
        C.need(self.bridge is not None and self.bridge["phase"] == "REAPED" and
               self.bridge["worker"] == worker, "worker release requires source-bound supervisor closure")
        self._inside_v3_confirm = True
        try:
            super().confirm_worker_exit(worker)
        finally:
            self._inside_v3_confirm = False
        result = self._bridge_record({**self.bridge, "phase": "COMPLETE"},
                                    "BRIDGE_WORKER_SLOT_RELEASED", {"worker": worker})
        os.close(self.child_pidfd)
        self.child_pidfd = None
        self.launcher = self.launcher_peer = self.domain = None
        self._internal_exit = None
        return result

    @C.stop_on_error
    def checkpoint(self, stage):
        C.need(self.bridge is not None and self.bridge["phase"] == "COMPLETE",
               "stage seal cannot bypass pending launch/supervisor")
        return super().checkpoint(stage)

    @C.stop_on_error
    def native_launch(self, *args, **kwargs):
        # No invocation of any supplied executable, no reservation, no context.
        return ClosedNativeGate.launch(*args, **kwargs)


class BridgeBroker(C.Broker):
    """v3 is deliberately incompatible with old unbound v2 owner sessions."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_client = None

    def _end(self):
        end = min(self.controller.store.end_mono, time.monotonic() + self.timeout)
        if self.controller.bridge is not None:
            end = min(end, self.controller.bridge["deadline_mono"])
        return end

    @staticmethod
    def _timeout(sock, end):
        remaining = end - time.monotonic()
        C.need(remaining > 0, "absolute transport/job deadline expired")
        sock.settimeout(remaining)

    @classmethod
    def receive(cls, sock, end):
        def exact(n):
            out = bytearray()
            while len(out) < n:
                cls._timeout(sock, end)
                value = sock.recv(n - len(out))
                C.need(value, "EOF/partial v3 frame before absolute deadline")
                out.extend(value)
            return bytes(out)
        size = struct.unpack("!I", exact(4))[0]
        C.need(0 < size <= 65536, "v3 frame byte cap")
        return exact(size).decode("ascii")

    def _send(self, sock, value):
        self._timeout(sock, self._end())
        C.send_frame(sock, value)

    def serve_one(self):
        try:
            self._timeout(self.sock, self._end())
            client, _ = self.sock.accept()
            self.active_client = client
            with client:
                pid, uid, _ = struct.unpack("3i", client.getsockopt(socket.SOL_SOCKET,
                    socket.SO_PEERCRED, struct.calcsize("3i")))
                C.need(uid == os.geteuid(), "foreign launch/worker UID")
                peer = C.process_identity(pid)
                b = self.controller.bridge
                C.need(b is not None, "unreserved peer before HELLO")
                expected = (b.get("child_peer") if b["phase"] == "LAUNCHER_CLOSED" else
                    b.get("launcher_peer") if b["phase"] in ("LAUNCHER_REGISTERED", "WORKER_CLOSED") else None)
                C.need(expected is not None and peer == expected, "unbound peer rejected before HELLO bytes")
                f = self.receive(client, self._end()).split("\t")
                C.need(len(f) == 10 and f[:2] == ["HELLO", "3"], "frozen v3 HELLO required")
                who = C.unhex(f[4])
                role = self.controller.hello(C.unhex(f[2]), f[3], who, f[5], f[6], f[7], f[8], f[9], peer)
                ack = lambda n: "ACK\t" + str(n) + "\tACCOUNTING_ONLY_NOT_NATIVE_AUTHORITY\t" + self.controller.store.fingerprint
                self._send(client, ack(0))
                seq = 0
                while True:
                    self.commands += 1
                    C.need(self.commands <= self.max_commands, "shared finite bridge command cap")
                    fields = self.receive(client, self._end()).split("\t")
                    C.need(len(fields) == 6 and fields[0] == "CMD" and fields[1] == str(seq + 1),
                           "duplicate/unknown/out-of-order bridge command")
                    C.need(fields[4].isdigit() and len(fields[4]) <= 20, "bounded IPC integer")
                    kind, ident, amount, detail = fields[2], C.unhex(fields[3]), C.integer(int(fields[4])), C.unhex(fields[5])
                    if role == "launcher":
                        if kind == "bind_child":
                            C.need(ident == self.controller.bridge["worker"], "cross-worker BINDCHILD")
                            self.controller.bind_child(peer, amount, C.strict_json(detail))
                        else:
                            C.need(kind == "close" and ident == "launcher" and amount == 0 and detail == "",
                                   "unexpected launch command")
                            self.controller.close_launcher(peer)
                            self._send(client, ack(seq + 1))
                            return "launcher"
                    elif role == "supervisor":
                        if kind == "supervisor_result":
                            C.need(ident == self.controller.bridge["worker"], "cross-worker exit result")
                            self.controller.supervisor_result(peer, amount, C.strict_json(detail))
                        else:
                            C.need(kind == "close" and ident == "supervisor" and amount == 0 and detail == "",
                                   "unexpected supervisor command")
                            self.controller.close_supervisor(peer)
                            self._send(client, ack(seq + 1))
                            return "supervisor"
                    else:
                        if kind == "close":
                            C.need(ident == "worker" and amount == 0 and detail == "", "unclean worker close")
                            self.controller.close_worker(who)
                            self._send(client, ack(seq + 1))
                            return "worker"
                        self.controller.command(who, kind, ident, amount, detail)
                    seq += 1
                    self._send(client, ack(seq))
        except BaseException as error:
            self.controller.disconnect("v3 bridge: " + str(error))
            raise
        finally:
            self.active_client = None

    def close(self):
        if self.active_client is not None:
            try:
                self.active_client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.active_client.close()
        super().close()

