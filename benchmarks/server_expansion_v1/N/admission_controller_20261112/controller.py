"""CPU-only durable stage/accounting controller. There is no native launch grant.

A mock reservation is not a hardware operation. The fixed C++ ProductionGate is
unchanged and every real launcher below fails before fork/exec or placement.
"""
import copy
import fcntl
import hashlib
import json
import math
import os
import secrets
import socket
import stat
import struct
import threading
import time
from functools import wraps
from pathlib import Path

STAGES = ("RESIDENT_R", "REPEAT_RESIDENT_R", "COLD_CANONICAL_ORACLE",
          "STRONG_WHOLE_RECHUNK_LOOP4")
STAGE_CHECKS = dict(zip(STAGES, (27, 81, 72, 81)))
PARENT = "f9a10b9cba9ae29b331ade43c0e92d67afd4c27c"
MAX_INT = (1 << 63) - 1


class Closed(RuntimeError):
    pass


def need(ok, message):
    if not ok:
        raise Closed(message)


def integer(value, minimum=0):
    need(type(value) is int and minimum <= value <= MAX_INT, "bounded integer required")
    return value


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def manifest_fingerprint(value):
    body = {k: v for k, v in value.items() if k != "manifest_sha256"}
    return sha(json.dumps(body, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode())


def strict_json(data):
    def pairs(items):
        out = {}
        for k, v in items:
            need(k not in out, "duplicate JSON member")
            out[k] = v
        return out
    def bad_constant(value):
        raise Closed("nonfinite JSON value: " + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)


def identifier(value):
    need(isinstance(value, str) and 0 < len(value) <= 4096 and
         all(32 <= ord(c) < 127 and c not in "\t\r\n" for c in value),
         "unsafe identity")
    return value


def digest(value):
    need(isinstance(value, str) and len(value) == 64 and
         all(c in "0123456789abcdef" for c in value), "SHA256 required")
    return value


def trusted_dir(path):
    p = Path(path)
    need(p.is_absolute() and ".." not in p.parts, "absolute trusted path required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            nf = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nf
        return fd
    except BaseException:
        os.close(fd)
        raise


def process_identity(pid=None):
    pid = os.getpid() if pid is None else integer(pid, 1)
    raw = Path("/proc", str(pid), "stat").read_text()
    close = raw.rfind(")")
    fields = raw[close + 2:].split()
    return {"pid": pid, "start_ticks": int(fields[19]),
            "uid": Path("/proc", str(pid)).stat().st_uid,
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


class Clock:
    def wall(self):
        return time.time()
    def mono(self):
        return time.monotonic()


class IO:
    def write(self, fd, data):
        return os.write(fd, data)
    def sync(self, fd):
        os.fsync(fd)


class Store:
    """One fresh controller STATE and one capped journal. Existing STATE never resumes."""
    def __init__(self, root, manifest, clock=None, io=None):
        self.root = Path(root)
        self.clock, self.io = clock or Clock(), io or IO()
        self.owner = process_identity()
        self.owner["nonce"] = secrets.token_hex(32)
        self.fd = self.lock_fd = self.journal_fd = None
        self._event_lock = threading.RLock()
        self.state_binding = None
        self.dead = False
        self.error = None
        self.seq, self.chain, self.journal_bytes = 0, "0" * 64, 0
        self.manifest = copy.deepcopy(manifest)
        need(manifest.get("mode") == "CPU_MOCK_ONLY", "CPU mock mode only; no native authority")
        need(manifest.get("approval") is None, "CPU manifest cannot carry a native approval")
        identifier(manifest["run_id"])
        need(manifest.get("native_execution_authorized") is False, "manifest cannot grant native execution")
        self.fingerprint = manifest_fingerprint(manifest)
        need(manifest.get("manifest_sha256") == self.fingerprint,
             "manifest fingerprint stale/changed")
        self.full_manifest_sha256 = sha(encoded(manifest))
        ceilings = {"requests": 76, "rows": 85738, "placements": 10,
            "backend_inits": 10, "models": 10, "contexts": 10,
            "raw_bytes": 143804276736, "metadata_bytes": 398458880,
            "capture_bytes": 144202735616, "journal_bytes": 536870912}
        for key, ceiling in ceilings.items():
            integer(manifest["limits"][key])
            need(manifest["limits"][key] <= ceiling, "unapproved quota expansion: " + key)
        self.start_wall, self.start_mono = self.clock.wall(), self.clock.mono()
        self.max_seconds = integer(manifest["limits"]["deadline_seconds"], 1)
        need(self.max_seconds <= 18000, "five-hour ceiling cannot expand")
        self.end_wall = self.start_wall + self.max_seconds
        self.end_mono = self.start_mono + self.max_seconds
        window = manifest.get("window", {})
        for key in ("deadline_wall", "deadline_mono"):
            need(type(window.get(key)) in (int, float) and math.isfinite(window[key]),
                 "bound dual-clock deadline required")
        self.end_wall = min(self.end_wall, window["deadline_wall"])
        self.end_mono = min(self.end_mono, window["deadline_mono"])
        need(self.end_wall > self.start_wall and self.end_mono > self.start_mono,
             "expired window cannot create a fresh controller")
        self.state = {"schema": "hs.N1controller.STATE.v1", "mode": "CPU_MOCK_ONLY",
                      "native_execution_authorized": False, "run_id": manifest["run_id"],
                      "manifest_sha256": self.fingerprint, "owner": self.owner,
                      "status": "PREPARING", "stage_index": 0, "worker_index": 0,
                      "active_worker": None, "completed_workers": [],
                      "completed_worker_bindings": {}, "preflights": [],
                      "stage_reports": {}, "counts": {k: 0 for k in
                          ("requests", "rows", "placements", "backend_inits", "models",
                           "contexts", "raw_bytes", "metadata_bytes", "capture_bytes")},
                      "requests": {}, "deployments": [], "stop_reason": None,
                      "journal_seq": 0, "journal_chain": self.chain}
        parent = trusted_dir(self.root.parent)
        try:
            os.mkdir(self.root.name, 0o700, dir_fd=parent)
            self.fd = os.open(self.root.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=parent)
            self.directory_identity = self._inode(self.fd)
            need(os.fstat(self.fd).st_uid == os.geteuid(), "run directory owner mismatch")
            self.lock_fd = os.open("LOCK", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                   0o600, dir_fd=self.fd)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_identity = self._inode(self.lock_fd)
            self._write_exact(self.lock_fd, encoded(self.owner))
            self.io.sync(self.lock_fd)
            self.journal_fd = os.open("journal.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                      os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
            self.journal_identity = self._inode(self.journal_fd)
            self._immutable("MANIFEST.json", encoded(manifest))
            self._atomic_state(self.state)
            self.event("OPEN_CPU_ONLY", {"owner": self.owner},
                       lambda v: v.update(status="READY"))
        except BaseException as e:
            self.poison("constructor failure: " + str(e))
            self.close_fds()
            raise
        finally:
            os.close(parent)

    @staticmethod
    def _inode(fd):
        s = os.fstat(fd)
        return s.st_dev, s.st_ino

    def _write_exact(self, fd, data):
        need(self.io.write(fd, data) == len(data),
             "short durable write; uncertain reservation retained, no retry")

    def _immutable(self, name, data):
        need("/" not in name and len(data) <= 8 * 1024 * 1024, "bounded immutable record")
        f = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600, dir_fd=self.fd)
        try:
            self._write_exact(f, data)
            self.io.sync(f)
        finally:
            os.close(f)
        self.io.sync(self.fd)

    def _atomic_state(self, value):
        raw = encoded(value)
        need(len(raw) <= 512 * 1024, "STATE bound exceeded")
        name = "STATE-" + secrets.token_hex(16) + ".pending"
        f = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600, dir_fd=self.fd)
        try:
            self._write_exact(f, raw)
            self.io.sync(f)
        finally:
            os.close(f)
        os.replace(name, "STATE.json", src_dir_fd=self.fd, dst_dir_fd=self.fd)
        self.io.sync(self.fd)
        st = os.stat("STATE.json", dir_fd=self.fd, follow_symlinks=False)
        self.state_binding = (st.st_dev, st.st_ino, st.st_size, sha(raw))

    def healthy(self):
        need(not self.dead, "run poisoned; inspect only, no restart")
        need(self.state_binding is not None and sha(encoded(self.state)) == self.state_binding[3],
             "in-memory controller state changed outside journal")
        need(sha(encoded(self.manifest)) == self.full_manifest_sha256,
             "in-memory frozen manifest changed")
        need(process_identity() == {k: self.owner[k] for k in
                                    ("pid", "start_ticks", "uid", "boot_id")},
             "controller owner changed")
        need(self.clock.wall() < self.end_wall and self.clock.mono() < self.end_mono,
             "absolute or monotonic deadline expired")
        need(self.fd is not None and self._inode(self.fd) == self.directory_identity,
             "directory identity lost")
        pathfd = trusted_dir(self.root)
        try:
            need(self._inode(pathfd) == self.directory_identity, "run directory replaced")
        finally:
            os.close(pathfd)
        current = os.stat("LOCK", dir_fd=self.fd, follow_symlinks=False)
        need(stat.S_ISREG(current.st_mode) and
             (current.st_dev, current.st_ino) == self.lock_identity and
             self._inode(self.lock_fd) == self.lock_identity, "owner LOCK lost/replaced")
        need(os.pread(self.lock_fd, 8193, 0) == encoded(self.owner), "LOCK owner contents changed")
        sf = os.open("STATE.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self.fd)
        try:
            ss = os.fstat(sf)
            need((ss.st_dev, ss.st_ino, ss.st_size) == self.state_binding[:3] and
                 ss.st_size <= 512 * 1024 and
                 sha(os.pread(sf, ss.st_size + 1, 0)) == self.state_binding[3],
                 "published STATE identity/bytes changed")
        finally:
            os.close(sf)
        mf = os.open("MANIFEST.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self.fd)
        try:
            size = os.fstat(mf).st_size
            need(size <= 1024 * 1024 and sha(os.pread(mf, size + 1, 0)) ==
                 self.full_manifest_sha256, "immutable manifest file changed")
        finally:
            os.close(mf)
        journal = os.stat("journal.jsonl", dir_fd=self.fd, follow_symlinks=False)
        need(stat.S_ISREG(journal.st_mode) and
             (journal.st_dev, journal.st_ino) == self.journal_identity and
             journal.st_size == self.journal_bytes, "journal replaced or modified")
        # Kernel owner proof, never a reacquisition attempt: a second-open
        # conflict alone could be an unknown competing holder after lock loss.
        holders = []
        device, inode = self.lock_identity
        for line in Path("/proc/locks").read_text().splitlines():
            p = line.split()
            if len(p) >= 8 and p[1:4] == ["FLOCK", "ADVISORY", "WRITE"]:
                pieces = p[5].split(":")
                if len(pieces) == 3 and (int(pieces[0], 16), int(pieces[1], 16),
                    int(pieces[2])) == (os.major(device), os.minor(device), inode):
                    holders.append(int(p[4]))
        need(holders == [self.owner["pid"]],
             "kernel FLOCK holder is absent/unknown/not the controller owner")

    def event(self, kind, detail, mutate):
        with self._event_lock:
            return self._event(kind, detail, mutate)

    def _event(self, kind, detail, mutate):
        try:
            self.healthy()
            next_state = copy.deepcopy(self.state)
            mutate(next_state)                    # validate every limit before journal append
            # Record only changed fields, not a growing copy of all72requests
            # on every1MiB write. The shared512MiB ceiling remains unchanged.
            delta = {}
            for key, value in next_state.items():
                if key in ("journal_seq", "journal_chain"):
                    continue
                if key in ("requests", "counts", "stage_reports", "completed_worker_bindings"):
                    changed = {k: v for k, v in value.items()
                               if self.state[key].get(k) != v}
                    if changed:
                        delta[key] = changed
                elif value != self.state.get(key):
                    delta[key] = value
            record = {"seq": self.seq + 1, "previous": self.chain, "kind": kind,
                      "detail": detail, "delta": delta}
            if self.seq == 0:
                record["initial_state"] = self.state
            raw0 = encoded(record)
            new_chain = sha(raw0)
            raw = encoded({"record": record, "sha256": new_chain})
            need(len(raw) <= 2048, "compact journal record bound; no silent quota expansion")
            need(self.journal_bytes + len(raw) <= self.manifest["limits"]["journal_bytes"],
                 "combined journal hard ceiling")
            pending = copy.deepcopy(self.state)
            pending.update(status="UNCERTAIN", pending_event={"kind": kind,
                "seq": self.seq + 1, "detail": detail,
                "counts_charge_upper_bound": next_state["counts"]})
            self._atomic_state(pending)           # failure before append still blocks reentry
            self._write_exact(self.journal_fd, raw)
            self.io.sync(self.journal_fd)
            self.seq += 1
            self.chain, self.journal_bytes = new_chain, self.journal_bytes + len(raw)
            next_state.update(journal_seq=self.seq, journal_chain=self.chain)
            self._atomic_state(next_state)
            self.state = next_state
            return copy.deepcopy(self.state)
        except BaseException as e:
            self.poison(str(e))
            raise

    def save_report(self, stage, report):
        self.healthy()
        name = "CHECKPOINT-" + stage + ".json"
        raw = encoded(report)
        self._immutable(name, raw)
        return {"file": name, "bytes": len(raw), "sha256": sha(raw)}

    def read_immutable(self, descriptor):
        self.healthy()
        filename = descriptor["file"]
        need("/" not in filename and descriptor["bytes"] <= 8 * 1024 * 1024,
             "bounded controller record descriptor")
        f = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self.fd)
        try:
            info = os.fstat(f)
            need(stat.S_ISREG(info.st_mode) and info.st_size == descriptor["bytes"],
                 "controller record length changed")
            data = os.pread(f, info.st_size + 1, 0)
            need(len(data) == info.st_size and sha(data) == descriptor["sha256"],
                 "controller immutable record changed")
            return strict_json(data)
        finally:
            os.close(f)

    def poison(self, reason):
        self.dead, self.error = True, str(reason)
        if self.fd is not None:
            try:
                self._immutable("STOP.json", encoded({"status": "STOPPED_OR_UNCERTAIN",
                    "reason": str(reason)[:4096], "owner": self.owner,
                    "native_execution_authorized": False,
                    "last_known_counts": self.state["counts"]}))
            except BaseException:
                pass                       # inability to write is never converted into success

    def close_fds(self):
        for name in ("journal_fd", "lock_fd", "fd"):
            fd = getattr(self, name, None)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)

    def close(self):
        self.close_fds()                    # never removes STATE/LOCK or restarts a worker

    @staticmethod
    def inspect(root, manifest):
        """Read-only recovery. A valid journal is not a restart permit."""
        root = Path(root)
        fd = trusted_dir(root)
        try:
            def read(name, cap):
                f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    s = os.fstat(f)
                    need(stat.S_ISREG(s.st_mode) and s.st_size <= cap, "recovery file bound")
                    out = bytearray()
                    while True:
                        b = os.read(f, min(8192, cap + 1 - len(out)))
                        if not b:
                            return bytes(out)
                        out.extend(b)
                        need(len(out) <= cap, "recovery byte ceiling")
                finally:
                    os.close(f)
            original = strict_json(read("MANIFEST.json", 1024 * 1024))
            need(original == manifest, "recovery manifest identity changed")
            state = strict_json(read("STATE.json", 512 * 1024))
            pending_files = [x for x in os.listdir(fd) if x.endswith(".pending")]
            lock_owner = strict_json(read("LOCK", 8192))
            lock = os.open("LOCK", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
            held = False
            try:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    held = True
                chain, seq, replay, incomplete = "0" * 64, 0, None, None
                f = os.open("journal.jsonl", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    total = 0
                    with os.fdopen(f, "rb") as stream:
                        while True:
                            line = stream.readline(2049)
                            if not line:
                                break
                            total += len(line)
                            need(total <= manifest["limits"]["journal_bytes"], "journal bound")
                            if len(line) > 2048 or not line.endswith(b"\n"):
                                incomplete = "PARTIAL_JOURNAL_RECORD"
                                break
                            v = strict_json(line)
                            r = v["record"]
                            need(r["seq"] == seq + 1 and r["previous"] == chain and
                                 sha(encoded(r)) == v["sha256"], "journal chain changed")
                            if seq == 0:
                                replay = r["initial_state"]
                                need(replay["manifest_sha256"] == manifest_fingerprint(manifest),
                                     "journal manifest changed")
                            for key, value in r["delta"].items():
                                if key in ("requests", "counts", "stage_reports", "completed_worker_bindings"):
                                    replay[key].update(value)
                                else:
                                    replay[key] = value
                            chain, seq = v["sha256"], r["seq"]
                finally:
                    pass
                if replay is not None:
                    replay.update(journal_seq=seq, journal_chain=chain)
                consistent = (replay is not None and encoded(state) == encoded(replay)
                              and lock_owner == state.get("owner"))
                stopped = os.path.lexists(root / "STOP.json")
                complete = (replay is not None and replay.get("status") == "COMPLETE"
                            and replay.get("stage_index") == 4
                            and replay.get("worker_index") == 8
                            and len(replay.get("completed_workers", [])) == 8
                            and len(replay.get("stage_reports", {})) == 4
                            and replay.get("active_worker") is None)
                clean = (complete and not held and
                         incomplete is None and consistent and not stopped and not pending_files)
                upper = dict(state.get("counts", {}))
                for observed in ((replay or {}).get("counts", {}),
                                 state.get("pending_event", {}).get(
                                     "counts_charge_upper_bound", {})):
                    for key, amount in observed.items():
                        integer(amount)
                        upper[key] = max(upper.get(key, 0), amount)
                return {"status": "SEALED_INSPECT_ONLY" if clean else "UNCLEAN_OR_ACTIVE_INSPECT_ONLY",
                        "lock_held": held,
                        "last_readable_valid_journal_counts": replay["counts"] if replay else {},
                        "state_counts": state.get("counts"), "journal_seq": seq,
                        "journal_chain": chain, "incomplete": incomplete,
                        "state_journal_consistent": consistent,
                        "counts_charge_upper_bound": upper, "pending_files": pending_files,
                        "STOP_exists": stopped,
                        "native_execution_authorized": False, "resume_authorized": False}
            finally:
                os.close(lock)
        finally:
            os.close(fd)


def stop_on_error(fn):
    @wraps(fn)
    def call(self, *args, **kwargs):
        with self._entry_lock:
            try:
                return fn(self, *args, **kwargs)
            except BaseException as error:
                self.store.poison(str(error))
                raise
    return call


class Controller:
    def __init__(self, root, manifest, verifier, policy, probe,
                 identity_probe, clock=None, io=None, peer_probe=None, executable_probe=None,
                 exit_probe=None):
        self.manifest = copy.deepcopy(manifest)
        self.clock = clock or Clock()
        self.verifier, self.policy, self.probe = verifier, policy, probe
        self.identity_probe = identity_probe
        self.peer_probe = peer_probe or process_identity
        self.executable_probe = executable_probe or self._executable_hash
        self.exit_probe = exit_probe or self._reap_owned_child
        self.store = Store(root, manifest, self.clock, io)
        self._entry_lock = threading.RLock()
        self.workers = self.manifest["workers"]
        self.worker_by_id = {w["id"]: w for w in self.workers}
        self.deploy_by_id = {d["id"]: d for d in self.manifest["deployments"]}
        self.claimed = set()
        self.request_ids = set(manifest["requests"])
        self.sealed_files = {}

    @staticmethod
    def _executable_hash(pid):
        h = hashlib.sha256()
        with open("/proc/" + str(pid) + "/exe", "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _reap_owned_child(peer):
        # waitpid cannot reap an unrelated process. A PID from a JSON receipt
        # is never permission to signal/kill it or manufacture a clean exit.
        current = process_identity(peer["pid"])
        need(current == peer, "exit owner changed")
        pid, code = os.waitpid(peer["pid"], os.WNOHANG)
        if pid == 0:
            return None
        return {"peer": peer, "exited": os.WIFEXITED(code),
                "exit_code": os.WEXITSTATUS(code) if os.WIFEXITED(code) else None,
                "raw_wait_status": code, "exit_confirmed": True,
                "supervisor_status": "BLOCKED_NO_BOUNDED_LOG_DRAIN_RESULT",
                "logs_status": "NOT_RUN"}

    def _check_sealed_files(self):
        if self.sealed_files:
            result = self.verifier.verify_sealed(copy.deepcopy(self.sealed_files))
            need(result["status"] == "PASS", "prior capture seal changed: " + str(result))

    def _reference_certificate(self):
        from late_bind import validate_reference_inputs
        descriptor = self.state.get("reference_input_certificate")
        need(isinstance(descriptor, dict), "verified R input certificate is absent")
        certificate = self.store.read_immutable(descriptor)
        need(certificate.get("schema") == "hs.N1controller.R-input-certificate.v1" and
             certificate.get("run_id") == self.manifest["run_id"] and
             certificate.get("native_execution_authorized") is False and
             certificate.get("scope") == "PROVIDED_R_SELF_CHECKS_NOT_COLD_EQUIVALENCE",
             "R input certificate run/scope changed")
        validate_reference_inputs(None, self.manifest["run_id"],
                                  certificate["reference_inputs"])
        return certificate

    @stop_on_error
    def prepare_stage_inputs(self, stage):
        from late_bind import prepare_stage_jobs
        self._guard()
        need(self.state["stage_index"] < len(STAGES) and
             stage == STAGES[self.state["stage_index"]] and
             self.state["active_worker"] is None, "stage input handoff order changed")
        self._check_sealed_files()
        certificate = None if stage == STAGES[0] else self._reference_certificate()
        return prepare_stage_jobs(None, self.manifest, stage, certificate)

    @property
    def state(self):
        return copy.deepcopy(self.store.state)

    def _guard(self, phase="DURING_WORK"):
        try:
            self.store.healthy()
            need(sha(encoded(self.manifest)) == self.store.full_manifest_sha256,
                 "controller manifest changed after freeze")
            need(self.identity_probe() == self.manifest["identity_bindings"],
                 "frozen source/binary/toolchain identity changed")
            active = self.state["active_worker"]
            if active:
                need(self.clock.wall() < active["lease_deadline_wall"] and
                     self.clock.mono() < active["lease_deadline_mono"],
                     "worker lease expired")
                if self.state["status"] != "WORKER_CLOSED_WAIT_EXIT":
                    need(self.peer_probe(active["peer"]["pid"]) == active["peer"],
                         "worker crashed or PID/start/boot owner changed")
            now = {"wall": self.clock.wall(), "mono": self.clock.mono()}
            result = self.policy.check(self.probe(), now, phase=phase)
            need(result["status"] == "PASS", "resource gate: " + str(result))
        except BaseException as e:
            self.store.poison(str(e))
            raise

    def _change(self, kind, detail, fn, phase="DURING_WORK"):
        try:
            self._guard(phase)
            return self.store.event(kind, detail, fn)
        except BaseException as e:
            self.store.poison(str(e))
            raise

    def _increment(self, state, key, n):
        integer(n)
        value = state["counts"][key] + n
        need(value <= self.manifest["limits"][key], key + " ceiling exceeded")
        state["counts"][key] = value

    @stop_on_error
    def synthetic_preflight(self, deployment_id):
        """CPU reservation fixture only; cannot load or place anything."""
        dep = self.deploy_by_id[deployment_id]
        need(dep["kind"] == "PREFLIGHT", "not a preflight fixture")
        def apply(s):
            need(s["active_worker"] is None and not s["completed_workers"] and
                 deployment_id not in s["preflights"], "duplicate/out-of-order preflight")
            for key in ("placements", "backend_inits", "models", "contexts"):
                self._increment(s, key, 1)
            s["preflights"].append(deployment_id)
        return self._change("CPU_MOCK_PREFLIGHT_RESERVATION", {"deployment": deployment_id},
                            apply, phase="BEFORE_PREFLIGHT")

    @stop_on_error
    def start_mock_worker(self, worker_id, peer, lease_sha256, executable_sha256):
        """Bind a CPU test worker. This API NEVER forks/execs any program."""
        self._guard(phase="BEFORE_LAUNCH")
        self._check_sealed_files()
        if self.state["stage_index"] > 0:
            self._reference_certificate()
        identifier(worker_id);digest(lease_sha256);digest(executable_sha256)
        integer(peer["pid"], 1);integer(peer["start_ticks"], 1)
        integer(peer["uid"]);identifier(peer["boot_id"])
        def apply(s):
            need(s["status"] == "READY" and s["active_worker"] is None,
                 "parallel worker or unknown controller state")
            need(len(s["preflights"]) == 2, "resource preflights not registered")
            need(s["worker_index"] < len(self.workers), "all workers already consumed")
            expected = self.workers[s["worker_index"]]
            need(expected["id"] == worker_id and expected["stage"] == STAGES[s["stage_index"]],
                 "stage/worker order violation")
            need(executable_sha256 == expected["executable_sha256"], "worker executable changed")
            need(all(x["peer"] != peer for x in s["completed_worker_bindings"].values()),
                 "independent worker must use a new process identity")
            self._increment(s, "placements", 1)     # before any hypothetical exec
            s["deployments"].append("placement:" + expected["deployment_id"])
            s["active_worker"] = {"id": worker_id, "peer": copy.deepcopy(peer),
                "lease_sha256": lease_sha256, "executable_sha256": executable_sha256,
                "claimed": False,
                "lease_deadline_wall": min(self.store.end_wall,
                    self.clock.wall() + expected["timeout_seconds"]),
                "lease_deadline_mono": min(self.store.end_mono,
                    self.clock.mono() + expected["timeout_seconds"])}
            s["status"] = "WORKER_RESERVED_CPU_ONLY"
        return self._change("CPU_MOCK_PREEXEC_RESERVATION", {"worker": worker_id},
                            apply, phase="BEFORE_LAUNCH")

    @stop_on_error
    def claim(self, run_id, manifest_sha256, worker_id, lease_sha256, actual_peer):
        need(self.executable_probe(actual_peer["pid"]) ==
             self.worker_by_id[worker_id]["executable_sha256"],
             "actual peer executable differs from frozen worker")
        def apply(s):
            a = s["active_worker"]
            need(run_id == self.manifest["run_id"] and manifest_sha256 == self.store.fingerprint,
                 "worker run/manifest identity mismatch")
            need(a is not None and a["id"] == worker_id and not a["claimed"],
                 "unknown/concurrent/reentered worker")
            need(a["lease_sha256"] == lease_sha256 and a["peer"] == actual_peer,
                 "worker owner PID/start/boot/UID or lease mismatch")
            a["claimed"] = True
            s["status"] = "WORKER_ACTIVE_CPU_ONLY"
        return self._change("CLAIM_OWNER", {"worker": worker_id}, apply)

    @stop_on_error
    def command(self, worker_id, kind, ident, amount=0, detail=""):
        identifier(ident);integer(amount)
        def apply(s):
            active = s["active_worker"]
            need(s["status"] == "WORKER_ACTIVE_CPU_ONLY" and active and
                 active["claimed"] and active["id"] == worker_id,
                 "command outside one bound worker")
            expected = self.worker_by_id[worker_id]
            if kind in ("backend", "model", "context", "placement"):
                need(ident == expected["deployment_id"] and amount == 1 and detail == "",
                     "unplanned deployment request")
                axis = {"backend": "backend_inits", "model": "models",
                        "context": "contexts", "placement": "placements"}[kind]
                if kind == "placement":
                    need("placement:" + ident in s["deployments"],
                         "worker lacks durable pre-exec placement")
                else:
                    need(kind + ":" + ident not in s["deployments"],
                         "duplicate deployment initialization")
                    need(kind != "model" or "backend:" + ident in s["deployments"],
                         "model before backend reservation")
                    need(kind != "context" or "model:" + ident in s["deployments"],
                         "context before model reservation")
                    self._increment(s, axis, 1)
                    s["deployments"].append(kind + ":" + ident)
                return
            need(ident in expected["request_ids"], "cross-worker or unplanned request")
            request = self.manifest["requests"][ident]
            if kind == "request":
                need(amount == 1 and detail == "" and "context:" + expected["deployment_id"]
                     in s["deployments"], "request before context reservation")
                need(ident not in s["requests"] and
                     not any(x["status"] == "ACTIVE" for x in s["requests"].values()),
                     "duplicate/concurrent request")
                finished = [x for x in expected["request_ids"] if x in s["requests"]]
                need(ident == expected["request_ids"][len(finished)], "request order changed")
                self._increment(s, "requests", 1)
                s["requests"][ident] = {"status": "ACTIVE", "rows": 0,
                    "raw_bytes": 0, "metadata_bytes": 0, "capture_bytes": 0}
                return
            need(ident in s["requests"] and s["requests"][ident]["status"] == "ACTIVE",
                 "mutation/rows/output after request closure")
            r = s["requests"][ident]
            if kind == "rows":
                need(0 < amount <= 4096 and detail == "", "physical decode row bound")
                need(r["rows"] + amount <= request["row_limit"], "per-request rows exceeded")
                self._increment(s, "rows", amount)
                r["rows"] += amount
            elif kind == "bytes":
                need(0 < amount <= 1024 * 1024 and detail in ("raw", "metadata"),
                     "bounded classified pre-write reservation")
                key = detail + "_bytes"
                need(r[key] + amount <= request[detail + "_byte_limit"],
                     "per-request " + detail + " ceiling")
                need(r["capture_bytes"] + amount <= request["byte_limit"],
                     "per-request total byte ceiling")
                self._increment(s, key, amount)
                self._increment(s, "capture_bytes", amount)
                r[key] += amount
                r["capture_bytes"] += amount
            elif kind == "sync":
                need(amount == 0 and detail in ("file", "directory"), "invalid durable sync guard")
            elif kind == "mutation":
                need(amount == 0 and detail and len(detail) <= 4096, "mutation action bound")
            elif kind == "finish":
                need(amount == 0 and detail == "COMPLETED", "failed/rejected request stops run")
                need(r["rows"] > 0, "complete request has no actual reserved decode work")
                r["status"] = "COMPLETED"
            else:
                raise Closed("unknown accounting command")
        return self._change("RESERVE_" + kind.upper(),
            {"worker": worker_id, "id": ident, "amount": amount, "detail": detail}, apply)

    @stop_on_error
    def close_worker(self, worker_id):
        def apply(s):
            a = s["active_worker"]
            need(a and a["id"] == worker_id and a["claimed"], "unclean worker close")
            w = self.worker_by_id[worker_id]
            need(all(s["requests"].get(i, {}).get("status") == "COMPLETED"
                     for i in w["request_ids"]), "partial worker cannot close")
            need(not any(x["status"] == "ACTIVE" for x in s["requests"].values()),
                 "worker close with active request")
            s["active_worker"]["accounting_closed"] = True
            s["status"] = "WORKER_CLOSED_WAIT_EXIT"
        return self._change("WORKER_CLOSED_CPU_ONLY", {"worker": worker_id}, apply)

    @stop_on_error
    def confirm_worker_exit(self, worker_id):
        self._guard()
        active = self.state["active_worker"]
        need(self.state["status"] == "WORKER_CLOSED_WAIT_EXIT" and active and
             active["id"] == worker_id and active.get("accounting_closed") is True,
             "process exit cannot replace accounting closure")
        witness = self.exit_probe(active["peer"])
        if witness is None:
            return {"status": "WAITING_FOR_OWNED_WORKER_EXIT", "native_authority": False}
        need(witness["peer"] == active["peer"] and witness["exited"] is True and
             witness["exit_code"] == 0 and witness.get("exit_confirmed") is True and
             witness.get("supervisor_status") == "OWNED_CHILD_EXITED" and
             witness.get("logs_status") == "COMPLETE",
             "worker failed/signaled, bounded logs failed, or supervisor evidence missing")
        def apply(s):
            s["completed_workers"].append(worker_id)
            s["completed_worker_bindings"][worker_id] = {
                "peer": copy.deepcopy(s["active_worker"]["peer"]),
                "executable_sha256": s["active_worker"]["executable_sha256"]}
            s["worker_index"] += 1
            s["active_worker"] = None
            s["status"] = "READY"
        return self._change("OWNED_WORKER_EXIT_OBSERVED", {"worker": worker_id,
            "exit_code": 0, "source": "waitpid-owned-child-or-explicit-CPU-test-witness"}, apply)

    @stop_on_error
    def checkpoint(self, stage):
        try:
            self._guard()
            self._check_sealed_files()
            s = self.state
            need(s["active_worker"] is None and s["stage_index"] < len(STAGES) and
                 STAGES[s["stage_index"]] == stage, "checkpoint stage order changed")
            expected = [w["id"] for w in self.workers if w["stage"] == stage]
            need(all(i in s["completed_workers"] for i in expected), "stage has missing workers")
            report = self.verifier.verify(stage)  # internal byte verifier; never accept a caller PASS
            record = self.store.save_report(stage, report)
            checks = report.get("checks", [])
            need(len(checks) == STAGE_CHECKS[stage] and
                 len({x["id"] for x in checks}) == len(checks), "stage raw coverage incomplete")
            graph = self.manifest["stage_check_ids"][stage]
            need({x["id"] for x in checks} == set(graph), "stage raw graph changed")
            need(report["status"] == "PASS" and all(x["status"] == "PASS" for x in checks),
                 "strict stage failure/contract conflict; first difference preserved")
            need(report.get("native_qualified") is False,
                 "provided byte verifier cannot claim native qualification")
            files = report.get("capture_file_sha256")
            need(isinstance(files, dict), "stage report missing immutable capture-file seal")
            for filename, value in files.items():
                identifier(filename);digest(value)
                need(filename not in self.sealed_files or self.sealed_files[filename] == value,
                     "prior immutable capture changed")
            seal_name = "SEAL-" + stage + ".json"
            seal_raw = encoded(files)
            self.store._immutable(seal_name, seal_raw)
            reference_descriptor = None
            if stage == STAGES[0]:
                from late_bind import validate_reference_inputs
                need(isinstance(report.get("reference_inputs"), dict),
                     "strict R checkpoint lacks the verified eighteen-input handoff")
                inputs = validate_reference_inputs(None, self.manifest["run_id"],
                                                   report.get("reference_inputs"))
                certificate = {"schema": "hs.N1controller.R-input-certificate.v1",
                    "run_id": self.manifest["run_id"],
                    "scope": "PROVIDED_R_SELF_CHECKS_NOT_COLD_EQUIVALENCE",
                    "reference_inputs": inputs, "source_stage_report": record,
                    "evidence_scope": report.get("scope"),
                    "native_qualification": "NOT_RUN",
                    "native_execution_authorized": False}
                raw = encoded(certificate)
                self.store._immutable("REFERENCE_INPUTS.json", raw)
                reference_descriptor = {"file": "REFERENCE_INPUTS.json",
                    "bytes": len(raw), "sha256": sha(raw)}
            def apply(v):
                v["stage_reports"][stage] = {**record, "seal_file": seal_name,
                    "seal_sha256": sha(seal_raw), "sealed_files": len(files)}
                if reference_descriptor is not None:
                    v["reference_input_certificate"] = reference_descriptor
                v["stage_index"] += 1
                v["status"] = "COMPLETE" if v["stage_index"] == 4 else "READY"
            result = self._change("STAGE_BYTE_GATE_CPU_ONLY", {"stage": stage,
                "provided_raw_report": record, "native_qualification": "NOT_RUN"}, apply)
            self.sealed_files.update(files)
            return result
        except BaseException as e:
            self.store.poison("checkpoint " + stage + ": " + str(e))
            raise

    @stop_on_error
    def native_launch(self, *args, **kwargs):
        # Never open a native binary, fork it, reserve placement, or initialize.
        self.store.poison("denied native launch attempt")
        raise Closed("NATIVE_PRODUCTION_GATE_CLOSED: separate review and approval required")

    def disconnect(self, why):
        self.store.poison("worker/controller disconnect or crash: " + str(why))


def recv_frame(sock):
    def exact(n):
        out = bytearray()
        while len(out) < n:
            data = sock.recv(n - len(out))
            need(data, "EOF/partial IPC frame")
            out.extend(data)
        return bytes(out)
    n = struct.unpack("!I", exact(4))[0]
    need(0 < n <= 65536, "IPC frame bound")
    return exact(n).decode("ascii")


def send_frame(sock, text):
    data = text.encode("ascii")
    need(0 < len(data) <= 65536, "IPC reply bound")
    sock.sendall(struct.pack("!I", len(data)) + data)


def unhex(value):
    need(len(value) % 2 == 0 and all(c in "0123456789abcdef" for c in value),
         "invalid hex IPC field")
    return bytes.fromhex(value).decode("ascii")


class Broker:
    """One protected socket, one active owner, one controller ledger; CPU only."""
    def __init__(self, controller, path, max_commands=250000, timeout=5):
        self.controller, self.path = controller, Path(path)
        integer(max_commands, 1)
        need(max_commands <= 250000 and 0 < timeout <= 30, "finite broker caps")
        self.max_commands, self.timeout, self.commands = max_commands, timeout, 0
        need(not self.path.exists() and not self.path.is_symlink(), "unknown existing socket")
        parent = trusted_dir(self.path.parent)
        try:
            st = os.fstat(parent)
            need(st.st_uid == os.geteuid() and st.st_mode & 0o077 == 0,
                 "private owner socket parent required")
        finally:
            os.close(parent)
        need(len(str(self.path).encode()) < 108, "UNIX socket path too long")
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(str(self.path))
        os.chmod(self.path, 0o600)
        st = os.lstat(self.path)
        self.identity = (st.st_dev, st.st_ino)
        self.sock.listen(1)
        self.sock.settimeout(timeout)

    def serve_one(self):
        worker = None
        try:
            client, _ = self.sock.accept()
            with client:
                client.settimeout(self.timeout)
                pid, uid, _ = struct.unpack("3i", client.getsockopt(socket.SOL_SOCKET,
                    socket.SO_PEERCRED, struct.calcsize("3i")))
                need(uid == os.geteuid(), "foreign worker UID")
                peer = process_identity(pid)
                fields = recv_frame(client).split("\t")
                need(len(fields) == 6 and fields[:2] == ["HELLO", "2"], "v2 owner HELLO required")
                worker = unhex(fields[4])
                self.controller.claim(unhex(fields[2]), fields[3], worker, fields[5], peer)
                ack = lambda seq: "ACK\t" + str(seq) + "\tACCOUNTING_ONLY_NOT_NATIVE_AUTHORITY\t" + self.controller.store.fingerprint
                send_frame(client, ack(0))
                seq = 0
                while True:
                    self.commands += 1
                    need(self.commands <= self.max_commands, "command ceiling")
                    f = recv_frame(client).split("\t")
                    need(len(f) == 6 and f[0] == "CMD" and f[1] == str(seq + 1),
                         "duplicate/unknown/out-of-order command")
                    need(f[4].isdigit() and len(f[4]) <= 20, "bounded amount syntax")
                    n = integer(int(f[4]))
                    ident, detail = unhex(f[3]), unhex(f[5])
                    if f[2] == "close":
                        need(ident == "worker" and n == 0 and detail == "", "unclean close")
                        self.controller.close_worker(worker)
                        send_frame(client, ack(seq + 1))
                        return
                    self.controller.command(worker, f[2], ident, n, detail)
                    seq += 1
                    send_frame(client, ack(seq))
        except BaseException as e:
            self.controller.disconnect(str(e))
            raise

    def close(self):
        self.sock.close()
        # Preserve socket/owner evidence; never unlink an unknown or old socket.
        try:
            st = os.lstat(self.path)
            need((st.st_dev, st.st_ino) == self.identity, "socket identity lost")
        except FileNotFoundError:
            self.controller.disconnect("broker socket removed")

