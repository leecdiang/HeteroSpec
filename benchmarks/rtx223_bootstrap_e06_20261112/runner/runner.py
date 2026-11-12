"""One-shot bootstrap controller. Native CLI takes an explicitly approved receipt and its external digest."""
import contextlib
import ctypes as C
import datetime as dt
import hashlib
import importlib.util
import json
import math
import msvcrt
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
def sibling(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

win = sibling("winjob")
need = win.need
UUID = "GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd"
PACKAGE = "HeteroSpec.RTX223.Bootstrap.B1"
LOCAL = Path("D:/HeteroSpec-PC")
STATE = LOCAL / "rtx223-bootstrap-b1"
MARKER = STATE / "B1.lock"
STUDY = Path("C:/Users/ASUS/Documents/ChatGPT/HeteroSpec")
LEGACY = (LOCAL/"RTX_EXPERIMENT.lock",) + tuple(STUDY / n / "resources/WINDOWS_RTX_EPOCH.lock" for n in (
    "rtx221-round1-20261112","rtx223-round1-resume-20261112-e02",
    "rtx223-round1-resume-20261112-e03","rtx223-round1-resume-20261112-e04"))
PYTHON = LOCAL / "python311/python.exe"
WINDOW = tuple(dt.datetime.fromisoformat(s).timestamp() for s in (
    "2026-11-13T20:00:00+08:00", "2026-11-13T20:05:00+08:00"))
STAGES = ("METER", "LOAD", "COUNT", "UUID", "CLOSE", "FLUSH")
CONSENT = "AUTHORIZE ONE RTX223 B1 BOOTSTRAP; NO MODELS; ZERO EXPLICIT KERNELS; UNKNOWN IMPLICIT CONTEXTS AND PHYSICAL LAUNCHES; NO RETRY"
CAP = 64 * 1024 ** 2
TERMINAL_SPACE = 64 * 1024
CONTRACT_SHA = "23d7da9d1a7d0a1a668b638ccd69907c16f054073781c5e2ce29b21cbe26dc6e"
NATIVE_SHA = "70fe177f4d7cdacbe25f73aaf27ef617f59f5832335708831185c5f76781b805"
CPU_SHA = "8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb"

def object_pairs(pairs):
    result = {}
    for k,v in pairs:
        need(k not in result, "Duplicate JSON field")
        result[k] = v
    return result

def parse(raw):
    return json.loads(raw,object_pairs_hook=object_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Invalid number "+value)))

def code_digest(raw):
    return hashlib.sha256(raw).hexdigest()

class Pins:
    """Hold the actual readable file objects and ancestor directories without write/delete sharing."""
    def __init__(self):
        self.stack = contextlib.ExitStack()
        self.directories = set()
        self.files = {}

    def close(self):
        self.stack.close()

    def pin(self, record, json_bytes=False):
        path = Path(record["path"])
        need(path.is_absolute() and not str(path).startswith("\\\\"), "Absolute local file path required")
        canonical = path.resolve(strict=True)
        need(canonical == path and all(not item.lstat().st_file_attributes & 0x400
                                      for item in (path,*path.parents)), "Aliased or reparse-point path")
        path = canonical
        sha = record["sha256"]
        need(isinstance(sha,str) and re.fullmatch("[0-9a-f]{64}",sha), "Invalid expected SHA-256")
        if path in self.files:
            actual, pinned_path = self.files[path]
            need(actual == sha, "Conflicting expected hash")
        else:
            for parent in reversed(path.parents):
                if parent in self.directories:
                    continue
                h = win.CreateFile(str(parent),0x80,3,None,3,0x02000000,None)
                win.checked(h and h != win.INVALID_HANDLE, "Pin ancestor directory")
                self.stack.callback(win.CloseHandle,h)
                self.directories.add(parent)
            h = win.CreateFile(str(path),0x80000000,1,None,3,0x80,None)
            win.checked(h and h != win.INVALID_HANDLE, "Pin file "+str(path))
            self.stack.callback(win.CloseHandle,h)
            get_final=win.api("GetFinalPathNameByHandleW",win.W.DWORD,win.W.HANDLE,win.W.LPWSTR,
                              win.W.DWORD,win.W.DWORD)
            final=C.create_unicode_buffer(32768)
            length=get_final(h,final,len(final),0)
            need(0<length<len(final) and Path(final.value.removeprefix("\\\\?\\"))==path,
                 "Pinned file handle resolved to a different path")
            # Keep a kernel handle, not a CRT descriptor, for every inventory item.
            # The restrictive first open prevents modification while hashing via a
            # temporary descriptor for the same resolved path.
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream,"sha256").hexdigest()
            need(actual == sha,"Changed file "+str(path))
            self.files[path] = (actual,path)
        info = path.stat()
        if "bytes" in record:
            need(type(record["bytes"]) is int and info.st_size == record["bytes"],"Size changed")
        if "file_id" in record:
            fid=record["file_id"]
            need(fid == {"volume":info.st_dev,"inode":info.st_ino}, "File ID changed "+str(path))
        if json_bytes:
            need(0 < info.st_size <= 32*1024**2,"Invalid receipt size")
            return parse(path.read_bytes())
        return path

class Journal:
    """CREATE_NEW is the permanent reservation. Never truncate or restart a used attempt."""
    def __init__(self, root, initial):
        self.root=Path(root)
        self.root.mkdir(exist_ok=True)
        h=win.CreateFile(str(self.root/"attempt.jsonl"),0x40000000,1,None,1,0x80000080,None)
        win.checked(h and h != win.INVALID_HANDLE,"Existing/inaccessible B reservation")
        fd=msvcrt.open_osfhandle(h,os.O_WRONLY|os.O_BINARY)
        self.file=os.fdopen(fd,"wb",buffering=0)
        self.lock=threading.Lock()
        self.used=0
        self.poisoned=False
        try:
            self.record(dict(kind="RESERVED",**initial))
        except BaseException:
            self.file.close()
            raise

    def record(self,event,terminal=False):
        raw=(json.dumps({"utc":win.utc(),"event":event},ensure_ascii=True,allow_nan=False)+"\n").encode()
        limit=CAP if terminal else CAP-TERMINAL_SPACE
        with self.lock:
            need(not self.poisoned,"Evidence stream previously wrote a partial or uncertain record")
            need(self.used+len(raw)<=limit,"Evidence byte quota exhausted")
            try:
                written=self.file.write(raw)
                need(type(written) is int and 0<=written<=len(raw),"Unknown evidence write length")
                self.used+=written
                need(written==len(raw),"Short evidence write")
                os.fsync(self.file.fileno())
            except BaseException:
                # A prefix may already exist. Neither append to a torn line nor
                # publish a success/FAILED record when persistence is uncertain.
                self.poisoned=True
                raise

    def close(self):
        self.file.close()

class Deadline:
    def __init__(self, job, hard, work, until=None):
        self.job=job
        self.start=time.monotonic()
        self.wall=time.time()
        self.work=work
        self.hard=min(hard,until-self.wall) if until is not None else hard
        need(self.hard>=work and self.hard>0,"Insufficient window")
        self.done=threading.Event()
        self.expired=threading.Event()
        self.thread=threading.Thread(target=self.watch,daemon=True)
        self.thread.start()

    def watch(self):
        if self.done.wait(self.hard):
            return
        self.expired.set()
        try:
            self.job.kill()  # No blocking component of the protocol owns this thread.
        finally:
            if not self.done.wait(3):
                # Includes the CreateProcessW-in-flight race. Final handle close ensures containment.
                # Keep the durable one-shot reservation as UNKNOWN even if disk or observer is hung.
                os._exit(125)

    def check(self,cleanup=False):
        elapsed=time.monotonic()-self.start
        need(abs((time.time()-self.wall)-elapsed)<1.0,"Wall clock discontinuity")
        need(not self.expired.is_set() and elapsed < (self.hard if cleanup else self.work),
             "Bootstrap deadline reached")

    def close(self):
        self.done.set()
        self.thread.join()

def verify_receipt(value,pid,backend):
    need(isinstance(value,dict),"No structured final probe evidence")
    for key,want in {"schema":"heterospec.e06.probe.v1","backend":backend,"pid":pid,
                     "uuid":UUID,"device_count":1,"device_name":"NVIDIA GeForce RTX 5070 Ti Laptop GPU",
                     "cupti_version":28,"kernel_records":0,"dropped":0,"api_callbacks":4,"flush_ok":True,
                     "drained":True,"physical_upper_bound":None}.items():
        got=value.get(key)
        need(key in value and type(got) is type(want) and got==want,"Receipt mismatch "+key)
    drops=value.get("drop_reads")
    need(isinstance(drops,list) and len(drops)==2 and all(type(n) is int and n==0 for n in drops),
         "Missing complete dropped-record evidence")
    for key in ("count_correlation","uuid_correlation","runtime_records","driver_records",
                "context_records","memcpy_records"):
        need(type(value.get(key)) is int and value[key]>=0,"Invalid count "+key)
    need(value["count_correlation"] and value["uuid_correlation"] and
         value["count_correlation"]!=value["uuid_correlation"] and value["runtime_records"]>=2,
         "Missing two distinct API correlations")

class Protocol:
    def __init__(self,job,observer,guard,log,disk,legacy):
        self.job=job
        self.observer=observer
        self.guard=guard
        self.log=log
        self.disk=disk
        self.legacy=legacy
        self.buffer=b""

    def check(self,cleanup):
        self.guard.check(cleanup)
        need(not any(path.exists() for path in self.legacy),"Legacy lock appeared")
        need(shutil.disk_usage(self.disk).free>=1024**3,"Disk watermark")
        self.observer.poll()
        self.guard.check(cleanup)
        error=self.job.read(self.job.error)
        if error:
            self.log.record({"kind":"probe_stderr","prefix_hex":error[:1024].hex(),"read_bytes":len(error)})
            raise win.Refusal("Unexpected probe diagnostics")

    def line(self,cleanup):
        while True:
            self.check(cleanup)
            if b"\n" in self.buffer:
                line,self.buffer=self.buffer.split(b"\n",1)
                line=line.removesuffix(b"\r")
                need(len(line)<=32768 and line.isascii(),"Invalid probe line")
                self.log.record({"kind":"probe_line","line":line.decode("ascii")})
                return line
            chunk=self.job.read(self.job.output)
            need(chunk is not None,"Truncated probe protocol")
            if not chunk:
                time.sleep(.025)
                continue
            self.buffer+=chunk
            need(len(self.buffer)<=65536,"Oversized probe frame")

    def run(self,backend):
        need(self.line(False)==b"READY","Probe did not become ready")
        for stage in STAGES:
            cleanup=stage in ("CLOSE","FLUSH")
            self.check(cleanup)
            self.observer.checkpoint(stage)
            self.check(cleanup)
            self.log.record({"kind":"stage_permit_consumed","stage":stage})
            self.guard.check(cleanup)
            cmd=("GO_"+stage+"\n").encode("ascii")
            need(os.write(self.job.input,cmd)==len(cmd),"Probe grant pipe short write")
            need(self.line(cleanup)==("OK_"+stage).encode(),"Failed probe stage "+stage)
        line=self.line(True)
        need(line.startswith(b"RECEIPT "),"Missing final receipt")
        verify_receipt(parse(line[len(b"RECEIPT "):]),self.job.pid,backend)
        need(self.line(True)==b"END" and not self.buffer,"Trailing protocol evidence")
        while self.job.exit_code() is None:
            self.check(True)
            need(not self.job.read(self.job.output),"Extra probe bytes after END")
            time.sleep(.025)
        need(self.job.exit_code()==0,"Unverified child exit")
        while self.job.active()!=0:
            self.check(True)
            time.sleep(.025)
        self.check(True)
        need(self.job.read(self.job.output) is None,"Probe pipe not closed or trailing output")


def execute(job, log, observer, argv, cwd, env, backend, work=80, hard=90, until=None,
            legacy=(), package=None, protected=(), readable_images=()):
    """Only main() constructs the native policy. CPU fixture uses the same job/transport."""
    guard=Deadline(job,hard,work,until)
    outcome="FAILED"
    absent=None
    attempted_create=False
    failure=None
    complete=False
    try:
        env=dict(env,HS_B_DEADLINE_TICK=str(win.GetTickCount64()+int((work-(time.monotonic()-guard.start))*1000)))
        observer.start()
        guard.check()
        attempted_create=True
        job.create(argv,cwd,env,package)
        log.record({"kind":"OWNED_SUSPENDED","pid":job.pid,"creation_filetime":job.creation,
                    "job":int(job.job),"active":job.active(),"kill_on_close":True,"active_limit":1,
                    "commit_limit":2*1024**3,"breakaway":False})
        observer.bind(job.pid,job.creation)
        if package:
            win.verify_package_restrictions(job,package,protected,readable_images)
            log.record({"kind":"model_read_denial","paths_checked":len(protected),"package":package})
        guard.check()
        job.resume()
        Protocol(job,observer,guard,log,log.root,legacy).run(backend)
        observation=observer.finish()
        need(isinstance(observation,dict) and observation.get("valid") is True,"Observer cannot certify its coverage")
        guard.check(True)
        complete=True
    except BaseException as exc:
        failure=str(exc)[:1024] or type(exc).__name__
    finally:
        try:
            if not complete:
                job.kill()
            if job.process:
                exited=(win.Wait(job.process,1000)==0)
                stop=time.monotonic()+1
                while exited and job.active() and time.monotonic()<stop:
                    time.sleep(.01)
                absent=exited and job.active()==0
            else:
                absent=(not attempted_create or job.active()==0)
            observer.close()
            guard.check(True)
            if complete and absent:
                outcome="COMPLETE"
        except BaseException as exc:
            failure=(failure+"; " if failure else "")+str(exc)[:1024]
        finally:
            if absent is not True:
                outcome="UNKNOWN"
            try:
                log.record({"kind":outcome,"failure":failure,"owned_process_exit_confirmed":absent,
                            "actual_physical_launches":None,"actual_contexts":None,"retry":False},terminal=True)
            finally:
                guard.close()
    need(outcome=="COMPLETE",outcome+" "+str(failure))
    return outcome

def protected_models():
    root=LOCAL/"models"
    need(root.is_dir(),"Bound model directory missing")
    # Directory-list denial plus read denial for every known model file in that tree;
    # the verifier requests a handle, never reads/maps model contents.
    dirs=[root]
    targets=[]
    for directory,children,names in os.walk(root,onerror=lambda e: (_ for _ in ()).throw(e)):
        dirs.extend(Path(directory)/name for name in children)
        targets.extend(Path(directory)/name for name in names if Path(name).suffix.lower() in
                       {".gguf",".safetensors",".bin",".onnx",".xml"})
    originals={root/"gguf"/x for x in ("Qwen3-8B-Q8_0.gguf","Qwen3-0.6B-Q8_0.gguf")}
    need(originals.issubset(targets),"Original model paths absent")
    return dirs+targets


def runner_context():
    """Digest effective user/groups/privileges, elevation, current logon, OS boot and outer Job presence."""
    import ctypes as C
    from ctypes import wintypes as W
    adv=C.WinDLL("advapi32",use_last_error=True)
    ntdll=C.WinDLL("ntdll",use_last_error=True)
    token=W.HANDLE()
    adv.OpenProcessToken.argtypes=[W.HANDLE,W.DWORD,C.POINTER(W.HANDLE)]
    win.checked(adv.OpenProcessToken(win.GetCurrentProcess(),8,C.byref(token)),"Query controller token")
    adv.GetTokenInformation.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)]
    adv.GetLengthSid.argtypes=[C.c_void_p]
    def block(cls):
        n=W.DWORD()
        adv.GetTokenInformation(token,cls,None,0,C.byref(n))
        need(0<n.value<1024*1024,"Token information unavailable")
        data=C.create_string_buffer(n.value)
        win.checked(adv.GetTokenInformation(token,cls,data,n,C.byref(n)),"GetTokenInformation")
        return data
    def sid(ptr):
        n=adv.GetLengthSid(ptr)
        need(0<n<=256,"Invalid SID size")
        return C.string_at(ptr,n).hex()
    class Group(C.Structure):
        _fields_=[("sid",C.c_void_p),("attrs",W.DWORD)]
    try:
        stats=block(10)
        user=block(1)
        payload={"windows":sys.getwindowsversion().platform_version,"auth":stats.raw[8:16].hex(),
                 "user":sid(C.c_void_p.from_buffer(user)),"privileges":block(3).raw.hex(),
                 "elevation_type":block(18).raw.hex(),"elevated":block(20).raw.hex(),
                 "session":block(12).raw.hex()}
        for cls in (2,11): # TokenGroups, TokenRestrictedSids
            buf=block(cls)
            count=W.DWORD.from_buffer(buf).value
            entries=(Group*count).from_buffer(buf,C.sizeof(C.c_void_p)) if count else ()
            payload[str(cls)]=sorted((sid(e.sid),e.attrs) for e in entries)
        boot=C.create_string_buffer(128)
        n=W.DWORD()
        query=ntdll.NtQuerySystemInformation
        query.argtypes=[W.ULONG,C.c_void_p,W.ULONG,C.POINTER(W.ULONG)]
        need(query(90,boot,C.sizeof(boot),C.byref(n))==0 and n.value>=16,"Boot GUID unavailable")
        payload["boot"]=boot.raw[:16].hex()
        nested=W.BOOL()
        win.checked(win.InJob(win.GetCurrentProcess(),None,C.byref(nested)),"Outer Job presence")
        payload["nested"]=bool(nested.value)
        return code_digest(json.dumps(payload,sort_keys=True,separators=(",",":")).encode())
    finally:
        win.CloseHandle(token)


def live_check():
    """Snapshot all visible Win32 processes while owning the device marker."""
    from ctypes import wintypes as W
    class Entry(C.Structure):
        _fields_=[("size",W.DWORD),("uses",W.DWORD),("pid",W.DWORD),("heap",C.c_size_t),
                  ("module",W.DWORD),("threads",W.DWORD),("parent",W.DWORD),("priority",W.LONG),
                  ("flags",W.DWORD),("name",W.WCHAR*260)]
    snapshot=win.api("CreateToolhelp32Snapshot",W.HANDLE,W.DWORD,W.DWORD)
    first=win.api("Process32FirstW",W.BOOL,W.HANDLE,C.POINTER(Entry))
    nxt=win.api("Process32NextW",W.BOOL,W.HANDLE,C.POINTER(Entry))
    handle=snapshot(2,0)
    win.checked(handle and handle!=win.INVALID_HANDLE,"Live process snapshot")
    count=0
    system=False
    try:
        entry=Entry()
        entry.size=C.sizeof(entry)
        win.checked(first(handle,C.byref(entry)),"Process enumeration")
        while True:
            name=entry.name.lower()
            need(name not in ("worker.exe","native-probe.exe","nvcc.exe") and not name.startswith("llama"),
                 "Visible conflicting worker "+name)
            system|=entry.pid==4
            count+=1
            if not nxt(handle,C.byref(entry)):
                need(C.get_last_error()==18,"Incomplete process snapshot")
                break
    finally:
        win.CloseHandle(handle)
    need(system,"Process snapshot does not cover system namespace")
    return count

def policy_from(pins,approval):
    need(approval["schema"]=="heterospec.e06.owner-approval.v1" and approval["consent"]==CONSENT and
         approval["device_uuid"]==UUID and approval["attempts"]==1 and type(approval["attempts"]) is int and
         approval["window"]==["2026-11-13T20:00:00+08:00","2026-11-13T20:05:00+08:00"] and
         isinstance(approval["owner_confirmation"],str) and bool(approval["owner_confirmation"].strip()) and
         re.fullmatch("[a-f0-9]{32,64}",approval["nonce"]),"Explicit scoped B approval missing")
    need(approval["contract"]["sha256"]==CONTRACT_SHA,"Unreviewed B contract")
    release=pins.pin(approval["release"],True)
    need(release["schema"]=="heterospec.e06.release.v1","Invalid release")
    contract=pins.pin(approval["contract"])
    for r in release["files"]:
        pins.pin(r)
    need(any(Path(r["path"]).resolve()==contract and r["sha256"]==approval["contract"]["sha256"]
             for r in release["files"]),"Contract missing from release")
    deployment=pins.pin(release["deployment"],True)
    need(deployment["schema"]=="heterospec.e06.deployment.v1","Invalid deployment")
    py_inventory=pins.pin(release["python_inventory"],True)
    verify_python_members(py_inventory)
    for r in py_inventory["files"]:
        pins.pin(r)
    manifest=deployment["modules"].copy()
    need(set(manifest)==set("ggml-cuda.dll ggml-base.dll cudart64_12.dll cublas64_12.dll cublaslt64_12.dll msvcp140.dll vcruntime140.dll vcruntime140_1.dll vcomp140.dll cupti64_2025.2.1.dll nvcuda.dll nvml.dll".split()),
         "Incomplete deployed roots")
    for key in ("probe","observation"):
        r=release[key]
        name=Path(r["path"]).name.lower()
        need(name==("native-probe.exe" if key=="probe" else "observation.dll"),"Unexpected binary")
        manifest[name]=r
    need(release["probe"]["sha256"]==NATIVE_SHA and release["cpu_probe"]["sha256"]==CPU_SHA,
         "Production or CPU executable identity mismatch")
    candidates=[r for r in deployment["candidates"] if r.get("reviewed") is True]
    for r in [*manifest.values(),*candidates,deployment["api_set_schema"]]:
        pins.pin(r)
    for p in [HERE/"runner.py",HERE/"winjob.py",HERE/"observation.py",PYTHON]:
        need(p.resolve() in pins.files,"Unpinned controller input "+str(p))
    return dict(manifest=manifest,candidates=candidates,device_uuid=UUID,output_dir=str(STATE)),release

def verify_python_members(inv):
    base=PYTHON.parent
    need(Path(inv["base_root"])==base and inv["schema"]=="heterospec.e06.python-inputs.v1" and
         inv["version"]==sys.version and list(map(Path,inv["path"]))==list(map(Path,sys.path)),
         "Interpreter version/import paths changed")
    need(all(not Path(p).exists() for p in inv["absent"]), "Python startup override appeared")
    actual={p for p in base.iterdir() if p.is_file()}
    for tree in (base/"Lib",base/"DLLs"):
        for parent,children,names in os.walk(tree,onerror=lambda e: (_ for _ in ()).throw(e)):
            if Path(parent)==base/"Lib" and "site-packages" in children:
                children.remove("site-packages")
            actual.update(Path(parent)/n for n in names)
    need(actual=={Path(r["path"]) for r in inv["files"]},"Python input membership changed")

def validate_smokes(pins, approval, release, model_count, image_count):
    etw=pins.pin(approval["etw_smoke"],True)
    acl=pins.pin(approval["appcontainer_smoke"],True)
    context=runner_context()
    for item in (etw,acl):
        observed=dt.datetime.fromisoformat(item["observed_utc"])
        need(observed.tzinfo is not None and observed.timestamp()<=time.time() and
             item.get("runner_context")==context and item.get("pass") is True and
             type(item.get("management_library_loads")) is int and item["management_library_loads"]==0 and
             type(item.get("numerical_DLL_loads")) is int and item["numerical_DLL_loads"]==0,
             "Fresh successful CPU smoke on this Windows boot/token required")
    need(etw["scope"]=="CPU_ETW_ONLY" and etw["observer_sha256"]==release["observation"]["sha256"] and
         all(type(etw[k]) is int and etw[k]==0 for k in ("start_status","stop_status")) and
         len(etw["loss_counters"])==3 and all(type(n) is int and n==0 for n in etw["loss_counters"]) and
         all(type(etw["counts"][k]) is int and etw["counts"][k]==1 for k in ("1","2")) and
         type(etw["counts"]["5"]) is int and etw["counts"]["5"]>0,"ETW CPU endpoint/loss proof missing")
    need(acl["scope"]=="CPU_APPCONTAINER_ONLY" and acl["cpu_probe_sha256"]==release["cpu_probe"]["sha256"] and
         acl["package"]==PACKAGE and acl["principal_model_read_denied"] is True and acl["job_active_limit"]==1 and
         acl["protected_model_paths"]==model_count and acl["readable_image_count"]==image_count,
         "AppContainer CPU Job/image/model ACL proof missing")

def fresh_clearance(pins,approval):
    # A fresh observation can be collected after the owner approves the frozen
    # contract. The approved nonce/dispatcher scope binds it to this one window.
    path=STATE/"dispatch-clearance.json"
    need(path.stat().st_size<=1024**2,"Oversized dispatch clearance")
    sha=code_digest(path.read_bytes())
    receipt=pins.pin({"path":str(path),"sha256":sha},True)
    observed=dt.datetime.fromisoformat(receipt["observed_utc"])
    need(observed.tzinfo is not None and 0<=time.time()-observed.timestamp()<60,"Stale dispatch clearance")
    need(receipt["device_uuid"]==UUID and receipt["nonce"]==approval["nonce"] and
         receipt["source_chats"]==["221","223-interrupted","223-successor"] and
         receipt["pending"]==[] and receipt["other_leases"]==[] and
         receipt["fenced_through"]=="2026-11-13T20:05:00+08:00" and
         isinstance(receipt["dispatcher_ownership"],str) and bool(receipt["dispatcher_ownership"].strip()),
         "External dispatchers not bound to exclusive window")
    host=pins.pin(receipt["host_snapshot"],True)
    end=dt.datetime.fromisoformat(host["end_utc"].replace("Z","+00:00"))
    need(end.tzinfo is not None and 0<=time.time()-end.timestamp()<60,"Stale host evidence")
    need(host["processes"]["system_pid4"]==1 and host["processes"]["candidate_image_hits"]==0 and
         host["task_scheduler"]["rows"]>0 and host["task_scheduler"]["project_matches"]==[] and
         host["services"]["rows"]>0 and host["services"]["project_matches"]==[],"Host/queue evidence incomplete")
    family=STUDY/"rtx223-round1-resume-20261112-e02/continuation/safety/runtime/family-ledger.sqlite"
    pins.pin({"path":str(family),"sha256":"707c029f2511f2449455cf6b461d806e10db6f4de82b1bdee19cce59eb898e7a"})
    need(not any(Path(str(family)+suffix).exists() for suffix in ("-shm","-wal","-journal")),
         "Unresolved original ledger sidecar")
    return {"sha256":sha,"host_snapshot_sha256":receipt["host_snapshot"]["sha256"],
            "observed_utc":receipt["observed_utc"]}

def native(approval_path,expected):
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and
         Path(sys.executable).resolve()==PYTHON.resolve() and sys.version_info[:2]==(3,11),
         "Bound isolated Python 3.11 -I -S -B required")
    need(WINDOW[0]<=time.time()<=WINDOW[1]-90,"Outside approved window")
    with contextlib.ExitStack() as owned:
        pins=Pins()
        owned.callback(pins.close)
        approval=pins.pin({"path":str(Path(approval_path).absolute()),"sha256":expected},True)
        policy,release=policy_from(pins,approval)
        targets=protected_models()
        roots=[Path(v["path"]) for v in policy["manifest"].values()
               if Path(v["path"]).name.lower() not in ("native-probe.exe","observation.dll")]
        validate_smokes(pins,approval,release,len(targets),len(roots))
        need(shutil.disk_usage(LOCAL).free>=2*1024**3,"Insufficient disk headroom")
        STATE.mkdir(exist_ok=True)
        for directory in reversed((STATE,*STATE.parents)):
            need(directory.resolve(strict=True)==directory and
                 not directory.lstat().st_file_attributes & 0x400,"Reparse-point in B state path")
            handle=win.CreateFile(str(directory),0x80,3,None,3,0x02000000,None)
            win.checked(handle and handle!=win.INVALID_HANDLE,"Pin B state directory")
            owned.callback(win.CloseHandle,handle)
        owned.enter_context(win.DeviceLock(MARKER,UUID,LEGACY))
        clearance=fresh_clearance(pins,approval)
        rows=live_check()
        need(WINDOW[0]<=time.time()<=WINDOW[1]-90,"Window no longer fits attempt")
        log=Journal(STATE,{"contract":approval["contract"],"release":approval["release"],
                            "owner_approval_sha256":expected,"nonce":approval["nonce"],"uuid":UUID,
                            "runner_pid":os.getpid(),"runner_creation":win.process_creation(),
                            "process_snapshot_rows":rows,"clearance":clearance,"authorized_attempts":1})
        owned.callback(log.close)
        job=win.AtomicJob()
        owned.callback(job.close)
        observer=sibling("observation").Observer(policy,log.record)
        modules=policy["manifest"]
        system=str(Path(os.environ["SystemRoot"]).resolve())
        need(Path(system)==Path("C:/Windows"),"Unexpected system directory")
        env={"SystemRoot":system,"WINDIR":system,"PATH":system+"\\System32","TEMP":str(STATE),"TMP":str(STATE),
             "CUDA_VISIBLE_DEVICES":UUID,"CUDA_CACHE_DISABLE":"1","GGML_CUDA_DISABLE_GRAPHS":"1",
             "HS_B_UUID":UUID,"HS_B_NUMERIC":modules["ggml-cuda.dll"]["path"],
             "HS_B_CUPTI":modules["cupti64_2025.2.1.dll"]["path"]}
        exe=modules["native-probe.exe"]["path"]
        return execute(job,log,observer,[exe],Path(exe).parent,env,"native",until=WINDOW[1],
                       legacy=LEGACY,package=PACKAGE,protected=targets,readable_images=roots)

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("DENIED: explicit owner approval file and independently supplied SHA-256 required")
    try:
        print(native(*sys.argv[1:]))
    except Exception as exc:
        raise SystemExit("DENIED: "+str(exc))

