"""Win32 ABI adapted from e02 windows_runner.py. Never opens a foreign PID for termination."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import json
import datetime as dt
import subprocess
import msvcrt
import time
from contextlib import ExitStack

class Refusal(Exception):
    pass

def need(condition, message):
    if not condition:
        raise Refusal(message)

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()
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
    GetTickCount64 = api("GetTickCount64", C.c_uint64)
    CreateJob = api("CreateJobObjectW", W.HANDLE, C.c_void_p, W.LPCWSTR)
    SetJob = api("SetInformationJobObject", W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD)
    TerminateJob = api("TerminateJobObject", W.BOOL, W.HANDLE, W.UINT)
    ResumeThread = api("ResumeThread", W.DWORD, W.HANDLE)
    GetExitCode = api("GetExitCodeProcess", W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
    GetProcessTimes = api("GetProcessTimes", W.BOOL, W.HANDLE, C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME), C.POINTER(W.FILETIME))
    GetCurrentProcess = api("GetCurrentProcess", W.HANDLE)
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
        if wait != 0:
            if wait == 0x80: ReleaseMutex(self.mutex)  # abandoned owner: refuse this admission
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



# Child inherits only the three listed anonymous-pipe endpoints.
QueryJob = api("QueryInformationJobObject", W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD))
InJob = api("IsProcessInJob", W.BOOL, W.HANDLE, W.HANDLE, C.POINTER(W.BOOL))
HandleInfo = api("GetHandleInformation", W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
PeekPipe = api("PeekNamedPipe", W.BOOL, W.HANDLE, C.c_void_p, W.DWORD, C.c_void_p, C.POINTER(W.DWORD), C.c_void_p)

class Accounting(C.Structure):
    _fields_ = [(k, C.c_int64) for k in ("user", "kernel", "period_user", "period_kernel")] + [
        (k, W.DWORD) for k in ("faults", "total", "active", "terminated")]

class Capabilities(C.Structure):
    _fields_ = [("sid", C.c_void_p), ("caps", C.c_void_p), ("count", W.DWORD), ("reserved", W.DWORD)]

def checked(ok, operation):
    if not ok:
        raise win_error(operation)

def no_caps(app_name, stack):
    # Compute SID only. Never create/update profiles or ACLs.
    env = C.WinDLL("userenv", use_last_error=True)
    sid = C.c_void_p()
    derive = env.DeriveAppContainerSidFromAppContainerName
    derive.argtypes = [W.LPCWSTR, C.POINTER(C.c_void_p)]
    derive.restype = C.c_long
    need(derive(app_name, C.byref(sid)) == 0 and sid.value, "AppContainer SID derivation failed")
    adv = C.WinDLL("advapi32")
    free = adv.FreeSid
    free.argtypes, free.restype = [C.c_void_p], C.c_void_p
    stack.callback(free, sid)
    return Capabilities(sid, None, 0, 0)

class AtomicJob:
    def __init__(self):
        self.process = self.thread = self.pid = None
        self.input = self.output = self.error = None
        self.job = CreateJob(None, None)
        checked(self.job, "CreateJobObjectW")
        try:
            flags = W.DWORD()
            checked(HandleInfo(self.job, C.byref(flags)), "GetHandleInformation")
            need(not flags.value & 1, "Inheritable Job handle")
            limits = EXTENDED_LIMIT()
            limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x100 | 0x8
            limits.BasicLimitInformation.ActiveProcessLimit = 1
            limits.ProcessMemoryLimit = 2 * 1024 ** 3
            checked(SetJob(self.job, 9, C.byref(limits), C.sizeof(limits)), "SetInformationJobObject")
            actual = EXTENDED_LIMIT()
            checked(QueryJob(self.job, 9, C.byref(actual), C.sizeof(actual), None), "Read Job limits")
            need(actual.BasicLimitInformation.LimitFlags == limits.BasicLimitInformation.LimitFlags and
                 actual.BasicLimitInformation.ActiveProcessLimit == 1 and
                 actual.ProcessMemoryLimit == limits.ProcessMemoryLimit, "Job limit mismatch")
        except BaseException:
            self.close()
            raise

    def active(self):
        info = Accounting()
        checked(QueryJob(self.job, 1, C.byref(info), C.sizeof(info), None), "Read Job active process count")
        return info.active

    def create(self, argv, cwd, environment, package=None):
        need(self.process is None and self.job, "Repeated or unowned process creation")
        with ExitStack() as child_ends:
            child_fd, self.input = os.pipe()
            child_ends.callback(os.close, child_fd)
            self.output, child_out = os.pipe()
            child_ends.callback(os.close, child_out)
            self.error, child_err = os.pipe()
            child_ends.callback(os.close, child_err)
            handles = (W.HANDLE * 3)()
            for index, fd in enumerate((child_fd, child_out, child_err)):
                os.set_inheritable(fd, True)
                handles[index] = msvcrt.get_osfhandle(fd)
            jobs = (W.HANDLE * 1)(self.job)
            attrs = [(0x20002, handles), (0x2000d, jobs)]
            if package is not None:
                caps = no_caps(package, child_ends)
                attrs.append((0x20009, caps))
            size = SIZE()
            InitAttrs(None, len(attrs), 0, C.byref(size))
            need(0 < size.value < 1024 * 1024, "Invalid STARTUPINFOEX attribute-list size")
            storage = C.create_string_buffer(size.value)
            checked(InitAttrs(storage, len(attrs), 0, C.byref(size)), "InitializeProcThreadAttributeList")
            child_ends.callback(DeleteAttrs, storage)
            for key, value in attrs:
                checked(UpdateAttrs(storage, 0, key, C.byref(value), C.sizeof(value), None, None),
                        "UpdateProcThreadAttribute " + hex(key))
            si = STARTUPINFOEX()
            si.StartupInfo.cb = C.sizeof(si)
            si.StartupInfo.dwFlags = 0x100
            si.StartupInfo.hStdInput, si.StartupInfo.hStdOutput, si.StartupInfo.hStdError = handles
            si.lpAttributeList = C.cast(storage, C.c_void_p)
            flags = 0x00000004 | 0x08000000 | 0x00000400 | 0x00080000
            env = C.create_unicode_buffer("\0".join(k+"="+v for k,v in sorted(environment.items())) + "\0\0")
            cmd = C.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
            pi = PROCESS_INFORMATION()
            checked(CreateProcess(str(argv[0]), cmd, None, None, True, flags, env, str(cwd),
                                  C.byref(si), C.byref(pi)), "Atomic CreateProcessW with Job list")
            self.process, self.thread, self.pid = pi.hProcess, pi.hThread, pi.dwProcessId
            self.creation = process_creation(self.process)
            member = W.BOOL()
            checked(InJob(self.process, self.job, C.byref(member)), "IsProcessInJob")
            need(member.value and self.active() == 1, "Child is not the single member of this Job")

    def resume(self):
        need(self.thread and ResumeThread(self.thread) == 1, "Owned child resume count invalid")
        CloseHandle(self.thread)
        self.thread = None

    def exit_code(self):
        result = Wait(self.process, 0)
        if result == 0x102:
            return None
        need(result == 0, "Owned process wait failed")
        code = W.DWORD()
        checked(GetExitCode(self.process, C.byref(code)), "GetExitCodeProcess")
        return code.value

    def read(self, fd):
        available = W.DWORD()
        if not PeekPipe(msvcrt.get_osfhandle(fd), None, 0, None, C.byref(available), None):
            if C.get_last_error() in (109, 232, 233):
                return None
            raise win_error("Peek pipe")
        if available.value:
            return os.read(fd, min(65536, available.value))
        return b""

    def kill(self):
        if self.job:
            checked(TerminateJob(self.job, 0xe606), "Terminate owned Job")

    def close(self):
        for name in ("job", "thread", "process"):
            handle = getattr(self, name)
            if handle:
                CloseHandle(handle)
                setattr(self, name, None)
        for name in ("input", "output", "error"):
            fd = getattr(self, name)
            if fd is not None:
                os.close(fd)
                setattr(self, name, None)


def verify_package_restrictions(job, package, protected_paths, readable_images):
    """Read the suspended token. Test effective access without reading any model bytes."""
    adv = C.WinDLL("advapi32", use_last_error=True)
    def api_adv(name, *args):
        f = getattr(adv, name)
        f.argtypes, f.restype = args, W.BOOL
        return f
    open_token = api_adv("OpenProcessToken", W.HANDLE, W.DWORD, C.POINTER(W.HANDLE))
    token_info = api_adv("GetTokenInformation", W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD))
    duplicate = api_adv("DuplicateToken", W.HANDLE, C.c_int, C.POINTER(W.HANDLE))
    impersonate = api_adv("ImpersonateLoggedOnUser", W.HANDLE)
    revert = api_adv("RevertToSelf")
    same_sid = api_adv("EqualSid", C.c_void_p, C.c_void_p)
    with ExitStack() as stack:
        primary, limited = W.HANDLE(), W.HANDLE()
        checked(open_token(job.process, 0x000a, C.byref(primary)), "Open owned child token")
        stack.callback(CloseHandle, primary)
        for cls in (29, 30, 31):  # IsAppContainer, Capabilities, AppContainerSid
            size = W.DWORD()
            token_info(primary, cls, None, 0, C.byref(size))
            need(0 < size.value <= 65536, "Invalid token information length")
            data = C.create_string_buffer(size.value)
            checked(token_info(primary, cls, data, size.value, C.byref(size)), "Read sandbox token")
            if cls == 29:
                need(C.c_uint32.from_buffer(data).value == 1, "Not an AppContainer")
            elif cls == 30:
                need(C.c_uint32.from_buffer(data).value == 0, "Unexpected AppContainer capability")
            else:
                expected = no_caps(package, stack)
                need(same_sid(C.c_void_p.from_buffer(data), expected.sid), "Wrong package SID")
        checked(duplicate(primary, 2, C.byref(limited)), "Duplicate owned token for effective access check")
        stack.callback(CloseHandle, limited)
        checked(impersonate(limited), "Impersonate for read-denial checks")
        try:
            for image in readable_images:
                handle = CreateFile(str(image), 0x80000000, 7, None, 3, 0x80, None)
                checked(handle and handle != INVALID_HANDLE,"Sandbox cannot read approved image "+image.name)
                CloseHandle(handle)

            for path in protected_paths:
                handle = CreateFile(str(path), 0x1, 7, None, 3, 0x02000000, None)
                if handle != INVALID_HANDLE and handle:
                    CloseHandle(handle)
                    raise Refusal("Sandbox can read protected model path " + str(path))
                need(C.get_last_error() == 5, "Did not establish ACCESS_DENIED for " + str(path))
        finally:
            if not revert():
                # Cannot safely resume controller work in an unknown security context.
                os._exit(124)

