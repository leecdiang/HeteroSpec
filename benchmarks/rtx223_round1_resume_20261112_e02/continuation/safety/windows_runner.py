"""Windows-only process containment and same-family resource accounting.

This module does not import CUDA, load a model, or release a native admission
gate. It runs only a hash-bound worker after validating separately reviewed
evidence. CPU integration fixtures exercise the OS mechanisms in test mode.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

KEYS = ("model_requests", "target_draft_rows", "native_gpu_seconds", "kernel_launches", "capture_bytes")
COUNT_KEYS = tuple(k for k in KEYS if k != "native_gpu_seconds")
FINAL = {"COMPLETE", "FAILED", "TIMEOUT", "HEARTBEAT_LOST", "COUNTER_INVALID", "LAUNCH_REFUSED", "OVERRUN"}
CURRENT_NATIVE_GATE = "BLOCKED_ORIGINAL_THREADS_UNVERIFIED"


class Refusal(RuntimeError):
    pass


def need(ok, message):
    if not ok:
        raise Refusal(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf8") as f:
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


def checked_json(path, expected_sha):
    need(isinstance(expected_sha, str) and len(expected_sha) == 64, "Expected artifact hash missing")
    need(sha(path) == expected_sha, "Frozen artifact identity changed: " + str(path))
    return json.loads(Path(path).read_bytes())


def validate_amounts(value, allow_unknown=False):
    need(isinstance(value, dict) and set(value) == set(KEYS), "Incomplete resource vector")
    for key, number in value.items():
        if allow_unknown and number is None:
            continue
        need(type(number) in (int, float) and math.isfinite(number) and number >= 0, "Invalid resource: " + key)
        if key in COUNT_KEYS:
            need(type(number) is int, "Resource count must be integer: " + key)


if os.name == "nt":
    K = C.WinDLL("kernel32", use_last_error=True)
    SIZE = C.c_size_t
    ULONG_PTR = C.c_size_t
    INVALID_HANDLE = C.c_void_p(-1).value

    class SECURITY_ATTRIBUTES(C.Structure):
        _fields_ = [("nLength", W.DWORD), ("lpSecurityDescriptor", C.c_void_p), ("bInheritHandle", W.BOOL)]

    class STARTUPINFO(C.Structure):
        _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                    ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                    ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                    ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                    ("lpReserved2", C.POINTER(C.c_ubyte)), ("hStdInput", W.HANDLE),
                    ("hStdOutput", W.HANDLE), ("hStdError", W.HANDLE)]

    class STARTUPINFOEX(C.Structure):
        _fields_ = [("StartupInfo", STARTUPINFO), ("lpAttributeList", C.c_void_p)]

    class PROCESS_INFORMATION(C.Structure):
        _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]

    class BASIC_LIMIT(C.Structure):
        _fields_ = [("PerProcessUserTimeLimit", C.c_int64), ("PerJobUserTimeLimit", C.c_int64),
                    ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", SIZE), ("MaximumWorkingSetSize", SIZE),
                    ("ActiveProcessLimit", W.DWORD), ("Affinity", ULONG_PTR),
                    ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]

    class IO_COUNTERS(C.Structure):
        _fields_ = [(name, C.c_uint64) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                  "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class EXTENDED_LIMIT(C.Structure):
        _fields_ = [("BasicLimitInformation", BASIC_LIMIT), ("IoInfo", IO_COUNTERS),
                    ("ProcessMemoryLimit", SIZE), ("JobMemoryLimit", SIZE),
                    ("PeakProcessMemoryUsed", SIZE), ("PeakJobMemoryUsed", SIZE)]

    def api(name, restype, *argtypes):
        f = getattr(K, name)
        f.restype, f.argtypes = restype, argtypes
        return f

    CloseHandle = api("CloseHandle", W.BOOL, W.HANDLE)
    CreateMutex = api("CreateMutexW", W.HANDLE, C.c_void_p, W.BOOL, W.LPCWSTR)
    ReleaseMutex = api("ReleaseMutex", W.BOOL, W.HANDLE)
    Wait = api("WaitForSingleObject", W.DWORD, W.HANDLE, W.DWORD)
    CreateFile = api("CreateFileW", W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE)
    WriteFile = api("WriteFile", W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p)
    FlushFileBuffers = api("FlushFileBuffers", W.BOOL, W.HANDLE)
    GetFileSizeEx = api("GetFileSizeEx", W.BOOL, W.HANDLE, C.POINTER(C.c_int64))
    ReadFile = api("ReadFile", W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p)
    GetTickCount64 = api("GetTickCount64", C.c_uint64)
    CreateJob = api("CreateJobObjectW", W.HANDLE, C.c_void_p, W.LPCWSTR)
    SetJob = api("SetInformationJobObject", W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD)
    AssignJob = api("AssignProcessToJobObject", W.BOOL, W.HANDLE, W.HANDLE)
    TerminateJob = api("TerminateJobObject", W.BOOL, W.HANDLE, W.UINT)
    TerminateProcess = api("TerminateProcess", W.BOOL, W.HANDLE, W.UINT)
    ResumeThread = api("ResumeThread", W.DWORD, W.HANDLE)
    GetExitCode = api("GetExitCodeProcess", W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
    GetProcessTimes = api("GetProcessTimes", W.BOOL, W.HANDLE, C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME))
    GetCurrentProcess = api("GetCurrentProcess", W.HANDLE)
    OpenProcess = api("OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
    SetHandleInformation = api("SetHandleInformation", W.BOOL, W.HANDLE, W.DWORD, W.DWORD)
    InitAttrs = api("InitializeProcThreadAttributeList", W.BOOL, C.c_void_p, W.DWORD, W.DWORD, C.POINTER(SIZE))
    UpdateAttrs = api("UpdateProcThreadAttribute", W.BOOL, C.c_void_p, W.DWORD, SIZE, C.c_void_p, SIZE, C.c_void_p, C.c_void_p)
    DeleteAttrs = api("DeleteProcThreadAttributeList", None, C.c_void_p)
    CreateProcess = api("CreateProcessW", W.BOOL, W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL,
                        W.DWORD, C.c_void_p, W.LPCWSTR, C.POINTER(STARTUPINFOEX), C.POINTER(PROCESS_INFORMATION))


def win_error(message):
    return Refusal(message + ": WinError " + str(C.get_last_error()))


def process_creation(handle=None):
    need(os.name == "nt", "Windows required")
    values = [W.FILETIME() for _ in range(4)]
    need(GetProcessTimes(handle or GetCurrentProcess(), *(C.byref(v) for v in values)), "Cannot read process creation time")
    return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime


def clocks():
    need(os.name == "nt", "Windows required")
    return time.time(), GetTickCount64() / 1000.0


def read_shared_json(path):
    """Allow the owned worker's atomic replacement while reading one snapshot."""
    handle = CreateFile(str(path), 0x80000000, 7, None, 3, 0x80, None)
    if handle == INVALID_HANDLE or not handle:
        raise win_error("Cannot open shared worker counter snapshot")
    try:
        size = C.c_int64()
        if not GetFileSizeEx(handle, C.byref(size)):
            raise win_error("Cannot size worker counter snapshot")
        need(0 < size.value <= 1024 * 1024, "Worker counter snapshot outside finite size bound")
        buffer, done = C.create_string_buffer(size.value), W.DWORD()
        if not ReadFile(handle, buffer, size.value, C.byref(done), None):
            raise win_error("Cannot read worker counter snapshot")
        need(done.value == size.value, "Worker counter snapshot truncated")
        return json.loads(buffer.raw)
    finally:
        CloseHandle(handle)


class DeviceLock:
    """One process owns a named mutex and an exclusive delete-on-close file.

    CREATE_NEW never alters an existing unknown marker. A normal/crashed owner
    loses both handles automatically. An old foreign marker is never removed.
    """
    def __init__(self, canonical_path, device_uuid, legacy_paths=(), namespace="Global"):
        self.path = Path(canonical_path).resolve()
        self.uuid = device_uuid
        self.legacy_paths = tuple(Path(p) for p in legacy_paths)
        self.name = namespace + "\\HeteroSpec-" + device_uuid
        self.mutex = self.file = None

    def acquire(self):
        need(os.name == "nt", "Windows required")
        need(all(not p.exists() for p in self.legacy_paths), "Existing legacy or previous-epoch lock; do not remove it")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.mutex = CreateMutex(None, False, self.name)
        if not self.mutex:
            raise win_error("Cannot create named GPU mutex")
        wait = Wait(self.mutex, 0)
        if wait not in (0, 0x80):
            CloseHandle(self.mutex)
            self.mutex = None
            raise Refusal("GPU mutex busy or inaccessible")
        try:
            # GENERIC_READ|WRITE, share=0, CREATE_NEW, DELETE_ON_CLOSE.
            self.file = CreateFile(str(self.path), 0xC0010000, 0, None, 1, 0x04000000 | 0x80, None)
            if self.file == INVALID_HANDLE or not self.file:
                self.file = None
                raise win_error("Existing or inaccessible canonical GPU lock")
            body = json.dumps({"schema": "heterospec.process-gpu-lock.v1", "pid": os.getpid(),
                               "process_creation_filetime": process_creation(), "device_uuid": self.uuid,
                               "utc": utc(), "mutex": self.name}).encode()
            n = W.DWORD()
            if not WriteFile(self.file, body, len(body), C.byref(n), None) or n.value != len(body):
                raise win_error("Cannot persist GPU lock owner")
            if not FlushFileBuffers(self.file):
                raise win_error("Cannot flush GPU lock owner")
            need(all(not p.exists() for p in self.legacy_paths), "Legacy lock appeared during admission")
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.file:
            CloseHandle(self.file)  # only the file created by this instance is deleted
            self.file = None
        if self.mutex:
            ReleaseMutex(self.mutex)
            CloseHandle(self.mutex)
            self.mutex = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *_):
        self.close()


class FamilyLedger:
    """Immutable parent binding, durable reservations, one global native window."""
    def __init__(self, path, plan, parent_snapshot, plan_sha256, epoch):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.plan, self.epoch, self.plan_sha = plan, epoch, plan_sha256
        self.family = plan["epoch"]
        validate_amounts(parent_snapshot["reserved"])
        self.parent = parent_snapshot["reserved"]
        self.binding = canonical({"plan_sha256": plan_sha256, "parent_snapshot": parent_snapshot,
                                  "budget_family": self.family, "maximums": plan["maximums"]})
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("CREATE TABLE IF NOT EXISTS family (id TEXT PRIMARY KEY,binding TEXT NOT NULL,parent TEXT NOT NULL,wall_start REAL,tick_start REAL,wall_deadline REAL,tick_deadline REAL,stop_reason TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY,epoch TEXT,stage TEXT,status TEXT,reserved TEXT,actual TEXT,pid INTEGER,creation INTEGER,exit_code INTEGER,reason TEXT,started_utc TEXT,finished_utc TEXT)")
        row = self.db.execute("SELECT id,binding FROM family").fetchall()
        if row and row != [(self.family, self.binding)]:
            self.db.close()
            raise Refusal("Ledger family/parent/plan binding changed; cannot reset budget")
        if not row:
            self.db.execute("INSERT INTO family(id,binding,parent) VALUES(?,?,?)", (self.family, self.binding, json.dumps(self.parent)))
            self.db.commit()

    def event(self, kind, **values):
        path = self.path.with_suffix(".events.jsonl")
        with path.open("a", encoding="utf8") as f:
            f.write(json.dumps({"utc": utc(), "kind": kind, **values}, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def totals(self):
        total = dict(self.parent)
        for reserved, actual in self.db.execute("SELECT reserved,actual FROM attempts"):
            r, a = json.loads(reserved), json.loads(actual) if actual else {}
            for k in KEYS:
                total[k] += max(r[k], a.get(k) or 0)
        return total

    def remaining_window(self):
        row = self.db.execute("SELECT wall_start,tick_start,wall_deadline,tick_deadline,stop_reason FROM family").fetchone()
        need(not row[4], "Budget family stopped: " + str(row[4]))
        if row[0] is None:
            return None
        wall, tick = clocks()
        if tick < row[1] or abs((wall - tick) - (row[0] - row[1])) > 5:
            self.stop("clock-or-boot-discontinuity")
            raise Refusal("Clock/boot discontinuity; global window cannot be restarted")
        return min(row[2] - wall, row[3] - tick)

    def start_window(self):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT wall_start FROM family").fetchone()
            if row[0] is None:
                wall, tick = clocks()
                limit = self.plan["maximums"]["native_gpu_seconds"]
                self.db.execute("UPDATE family SET wall_start=?,tick_start=?,wall_deadline=?,tick_deadline=?", (wall, tick, wall + limit, tick + limit))
        remaining = self.remaining_window()
        need(remaining is not None and remaining > 0, "Global native window expired")
        return remaining

    def stop(self, reason):
        with self.db:
            self.db.execute("UPDATE family SET stop_reason=COALESCE(stop_reason,?)", (reason,))
        self.event("FAMILY_STOPPED", reason=reason)

    def reserve(self, attempt, stage, amounts):
        validate_amounts(amounts)
        need(stage in self.plan["request_allocations"], "Unknown stage")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            need(not self.db.execute("SELECT stop_reason FROM family").fetchone()[0], "Budget family already stopped")
            need(self.db.execute("SELECT COUNT(*) FROM attempts WHERE status NOT IN ('COMPLETE')").fetchone()[0] == 0, "Prior failure or unclosed reservation blocks automatic continuation")
            total = self.totals()
            for k in KEYS:
                need(total[k] + amounts[k] <= self.plan["maximums"][k], "Family budget exceeded: " + k)
            for k in ("model_requests", "target_draft_rows"):
                stage_total = sum(json.loads(r)[k] for (r,) in self.db.execute("SELECT reserved FROM attempts WHERE stage=?", (stage,)))
                need(stage_total + amounts[k] <= self.plan["request_allocations"][stage][k], "Stage budget exceeded: " + k)
            try:
                self.db.execute("INSERT INTO attempts(id,epoch,stage,status,reserved,started_utc) VALUES(?,?,?,?,?,?)", (attempt, self.epoch, stage, "RESERVED", json.dumps(amounts), utc()))
            except sqlite3.IntegrityError as exc:
                raise Refusal("Duplicate attempt; no automatic retry") from exc
        self.event("RESERVED", attempt_id=attempt, stage=stage, resources=amounts)

    def launched(self, attempt, pid, creation):
        with self.db:
            cur = self.db.execute("UPDATE attempts SET status='RUNNING',pid=?,creation=? WHERE id=? AND status='RESERVED'", (pid, creation, attempt))
            need(cur.rowcount == 1, "Attempt is not reserved")
        self.event("LAUNCHED_SUSPENDED", attempt_id=attempt, pid=pid, process_creation_filetime=creation)

    def finish(self, attempt, status, actual, reason=None, exit_code=None):
        need(status in FINAL, "Invalid final status")
        validate_amounts(actual, allow_unknown=True)
        row = self.db.execute("SELECT reserved,status FROM attempts WHERE id=?", (attempt,)).fetchone()
        need(row is not None and row[1] in ("RESERVED", "RUNNING"), "Attempt is not active")
        reserved = json.loads(row[0])
        if status == "COMPLETE" and any(actual[k] is None for k in KEYS):
            status, reason = "COUNTER_INVALID", "Complete result has unknown actual resource counts"
        overrun = any(actual[k] is not None and actual[k] > reserved[k] for k in KEYS)
        if overrun:
            status, reason = "OVERRUN", "Observed usage exceeds frozen reservation"
        with self.db:
            self.db.execute("UPDATE attempts SET status=?,actual=?,exit_code=?,reason=?,finished_utc=? WHERE id=?", (status, json.dumps(actual), exit_code, reason, utc(), attempt))
            if status != "COMPLETE":
                self.db.execute("UPDATE family SET stop_reason=COALESCE(stop_reason,?)", (status + ": " + str(reason),))
        self.event("FINISHED", attempt_id=attempt, status=status, actual=actual, reason=reason, exit_code=exit_code)
        return status

    def snapshot(self):
        cols = ("id", "epoch", "stage", "status", "reserved", "actual", "pid", "creation", "exit_code", "reason", "started_utc", "finished_utc")
        attempts = [dict(zip(cols, r)) for r in self.db.execute("SELECT * FROM attempts ORDER BY rowid")]
        for a in attempts:
            for k in ("reserved", "actual"):
                a[k] = json.loads(a[k]) if a[k] else None
        family = self.db.execute("SELECT * FROM family").fetchone()
        return {"budget_family": self.family, "epoch": self.epoch, "binding": self.binding,
                "totals_charged": self.totals(), "attempts": attempts,
                "global_window": dict(zip(("id", "binding", "parent", "wall_start", "tick_start", "wall_deadline", "tick_deadline", "stop_reason"), family)),
                "refunds": 0, "automatic_retries": 0}

    def close(self):
        self.db.close()


def validate_native_release(binding_path, externally_frozen_sha, plan_sha, worker_path):
    """No fresh=True/gpu_admitted boolean can satisfy this artifact chain."""
    need(CURRENT_NATIVE_GATE == "READY", "Current native gate remains blocked: original thread clearance and trusted native instrumentation unavailable")
    binding = checked_json(binding_path, externally_frozen_sha)
    fields = ("schema", "decision", "observed_utc", "budget_family", "plan_sha256", "device_uuid", "worker_sha256", "evidence")
    need(all(k in binding for k in fields), "Native release binding incomplete")
    need(binding["schema"] == "heterospec.native-release.v1" and binding["decision"] == "ADMIT_QUALIFICATION", "Native release not admitted")
    need(binding["plan_sha256"] == plan_sha, "Native release names another budget")
    need(binding["worker_sha256"] == sha(worker_path), "Worker executable changed")
    stamp = dt.datetime.fromisoformat(binding["observed_utc"])
    need(stamp.tzinfo is not None and 0 <= (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds() <= 60, "Native release expired")
    required = {"dedup", "device", "source_and_modules", "counter_instrumentation", "qualification_protocol"}
    need(isinstance(binding["evidence"], dict) and set(binding["evidence"]) == required, "Native evidence chain incomplete")
    evidence = {}
    for name, b in binding["evidence"].items():
        need(set(b) == {"path", "sha256"}, "Evidence binding malformed")
        evidence[name] = checked_json(b["path"], b["sha256"])
    need(evidence["dedup"].get("decision") == "VERIFIED_IDLE_OR_COMPLETED", "Original threads not cleared")
    need(evidence["dedup"].get("scope") == [221, 223], "Dedup scope missing #221/#223")
    need(evidence["device"].get("device_uuid") == binding["device_uuid"] and evidence["device"].get("foreign_compute_pids") == [], "Device identity/occupation not cleared")
    need(evidence["source_and_modules"].get("verified") is True, "Source/model/module identities unverified")
    need(evidence["counter_instrumentation"].get("prelaunch_counted_limits") is True, "Kernel/request/row bounds not instrumented")
    need(evidence["qualification_protocol"].get("frozen") is True, "Native qualification protocol not frozen")
    return binding


class JobWorker:
    """A new suspended child is assigned to KILL_ON_JOB_CLOSE before resume."""
    def __init__(self, argv, cwd, environment, log_path):
        self.argv, self.cwd = [str(x) for x in argv], str(Path(cwd).resolve())
        self.env, self.log_path = environment, Path(log_path)
        self.job = self.process = self.thread = None
        self.pid = self.creation = None
        self.assigned = False

    def spawn_suspended(self):
        need(os.name == "nt", "Windows required")
        import msvcrt
        self.job = CreateJob(None, None)
        if not self.job:
            raise win_error("Cannot create own worker Job object")
        limit = EXTENDED_LIMIT()
        limit.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        if not SetJob(self.job, 9, C.byref(limit), C.sizeof(limit)):
            self.close()
            raise win_error("Cannot configure own worker containment")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        attributes = None
        with self.log_path.open("xb") as log, open(os.devnull, "rb") as stdin:
            out_handle, in_handle = msvcrt.get_osfhandle(log.fileno()), msvcrt.get_osfhandle(stdin.fileno())
            for handle in (out_handle, in_handle):
                if not SetHandleInformation(handle, 1, 1):
                    self.close()
                    raise win_error("Cannot configure own child log handles")
            size = SIZE()
            InitAttrs(None, 1, 0, C.byref(size))
            attributes = C.create_string_buffer(size.value)
            if not InitAttrs(attributes, 1, 0, C.byref(size)):
                self.close()
                raise win_error("Cannot initialize child handle allowlist")
            try:
                handles = (W.HANDLE * 2)(out_handle, in_handle)
                if not UpdateAttrs(attributes, 0, 0x00020002, C.cast(handles, C.c_void_p), C.sizeof(handles), None, None):
                    raise win_error("Cannot restrict inherited worker handles")
                info = STARTUPINFOEX()
                info.StartupInfo.cb = C.sizeof(info)
                info.StartupInfo.dwFlags = 0x100
                info.StartupInfo.hStdInput, info.StartupInfo.hStdOutput, info.StartupInfo.hStdError = in_handle, out_handle, out_handle
                info.lpAttributeList = C.cast(attributes, C.c_void_p)
                pi = PROCESS_INFORMATION()
                env = C.create_unicode_buffer("\0".join(k + "=" + v for k, v in sorted(self.env.items(), key=lambda x: x[0].upper())) + "\0\0")
                command = C.create_unicode_buffer(subprocess.list2cmdline(self.argv))
                flags = 0x00000004 | 0x08000000 | 0x00000400 | 0x00080000  # SUSPENDED, NO_WINDOW, UNICODE, EXTENDED
                if not CreateProcess(self.argv[0], command, None, None, True, flags, env, self.cwd, C.byref(info), C.byref(pi)):
                    raise win_error("Cannot create own suspended worker")
                self.process, self.thread, self.pid = pi.hProcess, pi.hThread, pi.dwProcessId
                self.creation = process_creation(self.process)
                if not AssignJob(self.job, self.process):
                    # This process was created suspended by this object; nobody else's PID is touched.
                    TerminateProcess(self.process, 0xEE01)
                    Wait(self.process, 5000)
                    raise win_error("Cannot assign own suspended worker to Job object")
                self.assigned = True
            except BaseException:
                self.close()
                raise
            finally:
                DeleteAttrs(attributes)
                for handle in (out_handle, in_handle):
                    SetHandleInformation(handle, 1, 0)
        return self

    def resume(self):
        need(self.process is not None and self.thread is not None, "No owned suspended worker")
        if ResumeThread(self.thread) == 0xFFFFFFFF:
            raise win_error("Cannot resume own worker")
        CloseHandle(self.thread)
        self.thread = None

    def exit_code(self):
        need(self.process is not None, "No owned worker")
        if Wait(self.process, 0) == 0x102:
            return None
        code = W.DWORD()
        if not GetExitCode(self.process, C.byref(code)):
            raise win_error("Cannot query own worker")
        return code.value

    def kill_owned_tree(self):
        if self.job:
            TerminateJob(self.job, 0xEE02)
            if self.process:
                Wait(self.process, 5000)

    def close(self):
        if self.process and not self.assigned:
            # Only our newly created suspended process can reach this branch.
            TerminateProcess(self.process, 0xEE03)
            Wait(self.process, 5000)
        # Closing this non-inheritable Job handle kills remaining owned descendants.
        if self.job:
            CloseHandle(self.job)
            self.job = None
        for name in ("thread", "process"):
            handle = getattr(self, name)
            if handle:
                CloseHandle(handle)
                setattr(self, name, None)


def validate_counter(value, epoch, attempt, pid, creation, last_sequence=-1):
    need(isinstance(value, dict), "Counter record must be an object")
    need(value.get("epoch") == epoch and value.get("attempt_id") == attempt, "Counter attempt identity mismatch")
    need(value.get("pid") == pid and value.get("process_creation_filetime") == creation, "Counter process identity mismatch")
    seq = value.get("sequence")
    need(type(seq) is int and seq >= last_sequence, "Counter sequence decreased or missing")
    counts = value.get("counts")
    need(isinstance(counts, dict) and set(counts) == set(COUNT_KEYS), "Counter coverage incomplete")
    for k, v in counts.items():
        need(type(v) is int and v >= 0, "Invalid native counter: " + k)
    return seq, counts


def run_owned_cpu_fixture(store, lock, attempt, argv, attempt_dir, timeout=3, heartbeat_timeout=1,
                          startup_grace=1, stage="failure_margin", reservation=None, native_release=None):
    """Contained runner shared with native mode; native mode requires artifact release.

    Native callers MUST supply native_release. The CPU test path is restricted
    to this source file's built-in --cpu-fixture mode and zero GPU/model counts.
    """
    argv = [str(x) for x in argv]
    cpu_fixture = (len(argv) >= 3 and Path(argv[1]).resolve() == Path(__file__).resolve() and argv[2] == "--cpu-fixture")
    if native_release is None:
        allowed_python = {Path(sys.executable).resolve(), Path(getattr(sys, "_base_executable", sys.executable)).resolve()}
        need(cpu_fixture and Path(argv[0]).resolve() in allowed_python, "Native gate closed; only built-in CPU fixture allowed")
    else:
        need(CURRENT_NATIVE_GATE == "READY", "Current native gate remains blocked; no receipt boolean can release it")
        need(isinstance(native_release, tuple) and len(native_release) == 2, "Native release must name externally hash-bound evidence, not a boolean/object")
        binding = validate_native_release(native_release[0], native_release[1], store.plan_sha, argv[0])
        need(binding.get("budget_family") == store.family and binding.get("device_uuid") == lock.uuid, "Native release family/device mismatch")
    attempt_dir = Path(attempt_dir).resolve()
    attempt_dir.mkdir(parents=True, exist_ok=False)
    heartbeat, final = attempt_dir / "heartbeat.json", attempt_dir / "counts-final.json"
    reservation = reservation or {k: (timeout if k == "native_gpu_seconds" else 0) for k in KEYS}
    if native_release is None:
        need(all(reservation[k] == 0 for k in COUNT_KEYS), "CPU fixture cannot reserve model/GPU resources")
    unknown = {k: None for k in KEYS}
    worker, status, reason, exit_code, actual = None, "LAUNCH_REFUSED", None, None, dict(unknown)
    started = None
    with lock:
        store.reserve(attempt, stage, reservation)
        try:
            remaining = store.start_window()
            allowed = min(float(timeout), float(reservation["native_gpu_seconds"]), remaining)
            need(allowed > 0, "No remaining native/worker window")
            env = os.environ.copy()
            env.update(HS_RUNNER_EPOCH=store.epoch, HS_RUNNER_ATTEMPT=attempt,
                       HS_RUNNER_HEARTBEAT=str(heartbeat), HS_RUNNER_COUNTS_FINAL=str(final),
                       CUDA_VISIBLE_DEVICES=lock.uuid)
            worker = JobWorker(argv, attempt_dir, env, attempt_dir / "worker.log").spawn_suspended()
            store.launched(attempt, worker.pid, worker.creation)
            started = time.monotonic()
            worker.resume()
            last_sequence, last_counts, last_beat = -1, {k: 0 for k in COUNT_KEYS}, started
            seen = False
            while True:
                exit_code = worker.exit_code()
                elapsed = time.monotonic() - started
                if elapsed > allowed or store.remaining_window() <= 0:
                    status, reason = "TIMEOUT", "Per-worker or global deadline expired"
                    worker.kill_owned_tree()
                    exit_code = worker.exit_code()
                    break
                if any(p.exists() for p in lock.legacy_paths):
                    status, reason = "FAILED", "A legacy/foreign lock appeared; stop only the owned worker"
                    worker.kill_owned_tree()
                    exit_code = worker.exit_code()
                    break
                if exit_code is not None:
                    status = "COMPLETE" if exit_code == 0 else "FAILED"
                    reason = None if exit_code == 0 else "Owned worker exited nonzero"
                    break
                if heartbeat.exists():
                    try:
                        value = read_shared_json(heartbeat)
                        seq, counts = validate_counter(value, store.epoch, attempt, worker.pid, worker.creation, last_sequence)
                        need(all(counts[k] >= last_counts[k] for k in COUNT_KEYS), "Native counters decreased")
                        if any(counts[k] > reservation[k] for k in COUNT_KEYS):
                            actual.update(counts)  # observed lower bounds must survive refusal
                            last_sequence, last_counts, seen = seq, counts, True
                        need(all(counts[k] <= reservation[k] for k in COUNT_KEYS), "Native counters exceeded reservation")
                        if seq > last_sequence:
                            last_beat, seen = time.monotonic(), True
                        last_sequence, last_counts = seq, counts
                    except (OSError, ValueError, Refusal) as exc:
                        status, reason = "COUNTER_INVALID", str(exc)
                        worker.kill_owned_tree()
                        exit_code = worker.exit_code()
                        break
                if (seen and time.monotonic() - last_beat > heartbeat_timeout) or (not seen and elapsed > startup_grace):
                    status, reason = "HEARTBEAT_LOST", "No fresh bound worker heartbeat"
                    worker.kill_owned_tree()
                    exit_code = worker.exit_code()
                    break
                time.sleep(0.02)
            actual["native_gpu_seconds"] = time.monotonic() - started
            if status == "COMPLETE":
                try:
                    counts_record = read_shared_json(final)
                    _, counts = validate_counter(counts_record, store.epoch, attempt, worker.pid, worker.creation, last_sequence)
                    need(counts_record.get("status") == "COMPLETE", "Final counters not complete")
                    need(all(counts[k] >= last_counts[k] for k in COUNT_KEYS), "Final counters decreased")
                    actual.update(counts)
                except (OSError, ValueError, Refusal) as exc:
                    status, reason = "COUNTER_INVALID", str(exc)
            elif seen:
                # Last heartbeat is a lower bound, not a complete actual cost.
                write_new(attempt_dir / "LAST_COUNTER_LOWER_BOUND.json", {"sequence": last_sequence, "counts": last_counts})
        except BaseException as exc:
            status, reason = "LAUNCH_REFUSED", type(exc).__name__ + ": " + str(exc)
            if started is not None:
                actual["native_gpu_seconds"] = time.monotonic() - started
            if worker:
                worker.kill_owned_tree()
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                reason = "Controller interruption: " + reason
        finally:
            if worker:
                worker.close()
            status = store.finish(attempt, status, actual, reason=reason, exit_code=exit_code)
            receipt = {"attempt_id": attempt, "epoch": store.epoch, "status": status, "reason": reason,
                       "exit_code": exit_code, "actual": actual, "reserved": reservation,
                       "worker_pid": worker.pid if worker else None, "worker_creation_filetime": worker.creation if worker else None,
                       "worker_log_sha256": sha(attempt_dir / "worker.log") if (attempt_dir / "worker.log").exists() else None,
                       "CPU_FIXTURE_ONLY": native_release is None, "finished_utc": utc()}
            receipt["actual_counts_are_lower_bounds"] = status != "COMPLETE"
            write_new(attempt_dir / "RUN_RECEIPT.json", receipt)
    return receipt


def _cpu_fixture(mode):
    """An intentionally tiny own-child fixture, never a model/GPU program."""
    epoch, attempt = os.environ["HS_RUNNER_EPOCH"], os.environ["HS_RUNNER_ATTEMPT"]
    heartbeat, final = Path(os.environ["HS_RUNNER_HEARTBEAT"]), Path(os.environ["HS_RUNNER_COUNTS_FINAL"])
    identity = {"epoch": epoch, "attempt_id": attempt, "pid": os.getpid(), "process_creation_filetime": process_creation()}
    counts = {k: 0 for k in COUNT_KEYS}

    def emit(path, seq, status):
        value = {**identity, "sequence": seq, "utc": utc(), "counts": counts, "status": status}
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(value), encoding="utf8")
        os.replace(temp, path)

    if mode == "crash":
        os._exit(17)
    if mode == "silent":
        time.sleep(10)
    if mode == "descendant":
        p = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"], creationflags=0x08000000)
        Path("descendant.json").write_text(json.dumps({"pid": p.pid, "creation": process_creation(int(p._handle))}), encoding="utf8")
    if mode == "overrun":
        counts["kernel_launches"] = 1  # synthetic counter only; this fixture never calls CUDA
    seq = 0
    for _ in range(100 if mode in ("timeout", "descendant") else 2):
        seq += 1
        emit(heartbeat, seq, "RUNNING")
        if mode == "legacy_marker":
            time.sleep(0.1)
            (Path.cwd().parent / "foreign.lock").write_text("OWN CPU FIXTURE simulated legacy task", encoding="utf8")
            time.sleep(10)
        time.sleep(0.04)
    emit(final, seq + 1, "COMPLETE")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--cpu-fixture":
        _cpu_fixture(sys.argv[2])
    else:
        raise SystemExit("No native CLI admission exists. Import the reviewed adapter with a separately frozen release binding.")
