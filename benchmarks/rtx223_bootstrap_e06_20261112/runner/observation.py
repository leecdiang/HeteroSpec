"""Parent observations for the one-shot B runner. No DLL is loaded on import.

The runner must pin all allowed paths with verified deny-write/delete handles
before constructing Observer and retain those handles through finish().
"""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import shutil
import threading
import time


GIB = 1024 ** 3
UUID = "GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd"
REQUIRED_AT_LOAD = {
    "ggml-cuda.dll", "ggml-base.dll", "cudart64_12.dll", "cublas64_12.dll",
    "cublaslt64_12.dll", "msvcp140.dll", "vcomp140.dll", "vcruntime140.dll",
    "vcruntime140_1.dll", "cupti64_2025.2.1.dll",
}
DLL_FLAGS = 0x100 | 0x800  # DLL_LOAD_DIR plus SYSTEM32


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def function(dll, name, result, *arguments):
    fn = getattr(dll, name)
    fn.restype, fn.argtypes = result, arguments
    return fn


def open_pinned(path):
    dll = C.WinDLL(str(path), winmode=DLL_FLAGS)
    get_path = function(C.WinDLL("kernel32"), "GetModuleFileNameW", W.DWORD,
                        W.HMODULE, W.LPWSTR, W.DWORD)
    name = C.create_unicode_buffer(32768)
    length = get_path(dll._handle, name, len(name))
    require(0 < length < len(name) and os.path.samefile(path, name.value),
            "observer dependency resolved to another file")
    return dll


class TraceRecord(C.Structure):
    _fields_ = [("pid", W.DWORD), ("event", W.DWORD), ("creation", C.c_ulonglong),
                ("stamp", C.c_longlong), ("path", C.c_wchar * 1024)]


class Module(C.Structure):
    _fields_ = [("size", W.DWORD), ("id", W.DWORD), ("pid", W.DWORD),
                ("global_use", W.DWORD), ("process_use", W.DWORD),
                ("base", C.c_void_p), ("image_size", W.DWORD), ("module", W.HMODULE),
                ("name", C.c_wchar * 256), ("path", C.c_wchar * 260)]


class Memory(C.Structure):
    _fields_ = [(n, C.c_ulonglong) for n in ("total", "free", "used")]


class ComputeProcess(C.Structure):
    _fields_ = [("pid", C.c_uint), ("used_gpu_memory", C.c_ulonglong),
                ("gpu_instance", C.c_uint), ("compute_instance", C.c_uint)]


def validate_watermarks(sample, baseline_used, pid, first):
    total, free, used, disk_free, pids = sample
    require(0 < total and 0 <= used <= total and 0 <= free <= total, "invalid memory data")
    require(free >= (8 if first else 7) * GIB, "device free memory below threshold")
    require(used - baseline_used < GIB, "device memory growth at stop threshold")
    require(disk_free >= (2 if first else 1) * GIB, "disk free below threshold")
    require(all(pid and p == pid for p in pids), "foreign compute context")


class Management:
    """Read-only NVML operations in the parent, never used by CPU substitutes."""
    def __init__(self, path):
        self.lib = open_pinned(path)
        self.active = False
        u, v = C.c_uint, C.c_void_p
        self.init = function(self.lib, "nvmlInit_v2", C.c_int)
        self.shutdown = function(self.lib, "nvmlShutdown", C.c_int)
        self.count = function(self.lib, "nvmlDeviceGetCount_v2", C.c_int, C.POINTER(u))
        self.by_uuid = function(self.lib, "nvmlDeviceGetHandleByUUID", C.c_int, C.c_char_p, C.POINTER(v))
        self.uuid = function(self.lib, "nvmlDeviceGetUUID", C.c_int, v, C.c_char_p, u)
        self.driver = function(self.lib, "nvmlSystemGetDriverVersion", C.c_int, C.c_char_p, u)
        self.mem = function(self.lib, "nvmlDeviceGetMemoryInfo", C.c_int, v, C.POINTER(Memory))
        self.procs = function(self.lib, "nvmlDeviceGetComputeRunningProcesses_v3",
                              C.c_int, v, C.POINTER(u), C.POINTER(ComputeProcess))
        self.device = v()

    def start(self):
        require(self.init() == 0, "NVML unavailable")
        self.active = True
        version = C.create_string_buffer(96)
        require(self.driver(version, len(version)) == 0 and version.value == b"616.92",
                "unapproved management driver")
        require(self.by_uuid(UUID.encode("ascii"), C.byref(self.device)) == 0, "device missing")

    def sample(self, out):
        count, uid = C.c_uint(), C.create_string_buffer(128)
        require(self.count(C.byref(count)) == 0 and count.value == 1, "invalid GPU inventory")
        require(self.uuid(self.device, uid, len(uid)) == 0 and uid.value.decode("ascii") == UUID,
                "device UUID mismatch")
        memory = Memory()
        require(self.mem(self.device, C.byref(memory)) == 0, "device memory unavailable")
        occupants = (ComputeProcess * 32)()
        n = C.c_uint(len(occupants))
        require(self.procs(self.device, C.byref(n), occupants) == 0 and n.value <= len(occupants),
                "compute occupancy unavailable/overflow")
        return (memory.total, memory.free, memory.used, shutil.disk_usage(out).free,
                [occupants[i].pid for i in range(n.value)])

    def close(self):
        if self.active:
            self.active = False
            require(self.shutdown() == 0, "NVML shutdown unknown")


class Observer:
    def __init__(self, policy, emit):
        require(policy["device_uuid"] == UUID, "invalid observation target")
        self.policy, self.emit = policy, emit
        self.output = Path(policy["output_dir"])
        self.by_name = {k.lower(): v for k, v in policy["manifest"].items()}
        candidates = policy.get("candidates", [])
        self.allowed = {os.path.normcase(os.path.realpath(v["path"])): v
                        for v in [*self.by_name.values(), *candidates]}
        self.pid = self.creation = 0
        self.counts = {1: 0, 2: 0, 5: 0, 6: 0}
        self.loaded, self.usages = set(), []
        self.session = False
        self.mgmt = self.thread = self.etw = None
        self.stop = threading.Event()
        self.guard = threading.Lock()
        self.failure, self.last = None, 0.
        self.system = C.WinDLL("kernel32", use_last_error=True)
        self._snapshot = function(self.system, "CreateToolhelp32Snapshot", W.HANDLE, W.DWORD, W.DWORD)
        self._first = function(self.system, "Module32FirstW", W.BOOL, W.HANDLE, C.POINTER(Module))
        self._next = function(self.system, "Module32NextW", W.BOOL, W.HANDLE, C.POINTER(Module))
        self._close = function(self.system, "CloseHandle", W.BOOL, W.HANDLE)
        query = function(self.system, "QueryDosDeviceW", W.DWORD, W.LPCWSTR, W.LPWSTR, W.DWORD)
        self.drives = {}
        for key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = key + ":"
            buffer = C.create_unicode_buffer(32768)
            if query(drive, buffer, len(buffer)):
                self.drives[buffer.value.casefold()] = drive

    def start(self):
        self.etw = open_pinned(self.by_name["observation.dll"]["path"])
        self.begin = function(self.etw, "hs_trace_start", W.DWORD)
        self.bind_trace = function(self.etw, "hs_trace_bind", W.DWORD, W.DWORD)
        self.read_trace = function(self.etw, "hs_trace_next", W.DWORD, C.POINTER(TraceRecord), W.DWORD)
        self.end_trace = function(self.etw, "hs_trace_stop", W.DWORD, C.POINTER(W.DWORD))
        self.health = function(self.etw, "hs_trace_health", W.DWORD)
        self.session = True
        rc = self.begin()
        require(rc == 0, f"ETW session unavailable ({rc})")
        self.mgmt = Management(self.by_name["nvml.dll"]["path"])
        self.mgmt.start()
        first = self.mgmt.sample(self.output)
        validate_watermarks(first, first[2], 0, True)
        self.baseline = first[2]
        self.last = time.monotonic()
        self.emit({"observer": "initial_watermarks", "total": first[0], "free": first[1],
                   "used": first[2], "disk_free": first[3], "compute_processes": len(first[4])})
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def _monitor(self):
        try:
            while not self.stop.wait(.2):
                data = self.mgmt.sample(self.output)
                validate_watermarks(data, self.baseline, self.pid, False)
                with self.guard:
                    now = time.monotonic()
                    require(now - self.last <= 1., "missing one-second resource observation")
                    self.last = now
                    require(len(self.usages) < 512, "resource evidence not draining")
                    self.usages.append({"mono": now, "total": data[0], "free": data[1],
                                        "used": data[2], "disk_free": data[3],
                                        "compute_processes": len(data[4])})
        except Exception as exc:
            with self.guard:
                self.failure = str(exc)

    def _watermarks(self):
        with self.guard:
            require(self.failure is None, self.failure or "monitor failure")
            require(time.monotonic() - self.last <= 1., "stale resource sampler")
            items, self.usages = self.usages, []
        for row in items:
            self.emit({"observer": "watermark", **row})

    def bind(self, pid, creation_filetime):
        require(self.bind_trace(pid) == 0, "ETW process bind failed")
        self.pid, self.creation = pid, creation_filetime

    def _image(self, raw):
        path = raw
        for device, drive in self.drives.items():
            if raw.casefold().startswith(device + "\\"):
                path = drive + raw[len(device):]
                break
        if path.startswith("\\SystemRoot\\"):
            path = os.path.join(os.environ["SystemRoot"], path[len("\\SystemRoot\\"):])
        require(os.path.isabs(path), "relative ETW image path")
        canonical = os.path.normcase(os.path.realpath(path))
        require(canonical in self.allowed, f"unbound process image {path}")
        return self.allowed[canonical]

    def _events(self):
        if not self.pid:
            return
        while True:
            row = TraceRecord()
            status = self.read_trace(C.byref(row), C.sizeof(row))
            if status == 259:  # ERROR_NO_MORE_ITEMS
                return
            require(status == 0, f"ETW incomplete ({status})")
            require(row.pid == self.pid and row.event in self.counts, "ETW identity/type mismatch")
            self.counts[row.event] += 1
            record = {"observer": "ETW", "event_id": row.event, "stamp": row.stamp, "pid": row.pid}
            if row.event in (1, 2):
                require(row.creation == self.creation and self.counts[row.event] == 1,
                        "ETW creation identity or event multiplicity mismatch")
                require(row.event != 2 or self.counts[1] == 1, "ETW exit before start")
            else:
                item = self._image(row.path)
                record.update(path=item["path"], sha256=item["sha256"])
                if row.event == 5:
                    self.loaded.add(Path(item["path"]).name.lower())
            self.emit(record)

    def poll(self):
        self._watermarks()
        require(self.health() == 0, "ETW consumer lost")
        self._events()

    def checkpoint(self, stage):
        self.poll()
        snap = self._snapshot(0x08 | 0x10, self.pid)
        require(snap != W.HANDLE(-1).value, "cannot take child module snapshot")
        seen = {}
        try:
            mod = Module()
            mod.size = C.sizeof(mod)
            require(self._first(snap, C.byref(mod)), "cannot enumerate child modules")
            while True:
                item = self._image(mod.path)
                seen[Path(item["path"]).name.lower()] = item["sha256"]
                if not self._next(snap, C.byref(mod)):
                    require(C.get_last_error() == 18, "module enumeration incomplete")
                    break
        finally:
            self._close(snap)
        self.emit({"observer": "module_snapshot", "stage": stage, "modules": seen})
        require("native-probe.exe" in seen, "missing pinned probe image")
        if stage in {"LOAD", "COUNT", "UUID", "CLOSE"}:
            require("cupti64_2025.2.1.dll" in seen, "metering DLL missing")
        if stage in {"COUNT", "UUID", "CLOSE"}:
            require(REQUIRED_AT_LOAD.issubset(seen), "incomplete loaded numerical module set")

    def finish(self):
        self._watermarks()
        lost = (W.DWORD * 3)()
        rc = self.end_trace(lost)
        self.session = False
        self.emit({"observer": "ETW_end", "status": rc, "loss_counters": list(lost)})
        require(rc == 0 and not any(lost), "trace loss or incomplete drain")
        self._events()
        require(self.counts[1] == self.counts[2] == 1, "process trace endpoints missing")
        require((REQUIRED_AT_LOAD | {"native-probe.exe", "nvcuda.dll"}).issubset(self.loaded),
                "missing required ETW image load")
        self.emit({"observer": "ETW_counts", "counts": self.counts})
        self._watermarks()
        return {"valid": True, "scope": "observed host events and sampled watermarks"}

    def close(self):
        self.stop.set()
        try:
            if self.thread:
                self.thread.join(1)
                require(not self.thread.is_alive(), "management sampler failed to exit")
                self._watermarks()
        finally:
            try:
                if self.session:
                    lost = (W.DWORD * 3)()
                    rc = self.end_trace(lost)
                    self.emit({"observer": "ETW_partial_close", "status": rc, "loss_counters": list(lost)})
                    self.session = False
            finally:
                if self.mgmt and not (self.thread and self.thread.is_alive()):
                    self.mgmt.close()
