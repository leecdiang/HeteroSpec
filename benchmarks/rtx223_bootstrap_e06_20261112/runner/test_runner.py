"""CPU-only fault injection; no native executable path or arbitrary command is accepted."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("bootstrap_runner",HERE/"runner.py")
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
w=r.win
FAKE=HERE.parent/"build/probes-attempt-002/cpu-probe.exe"
DIGEST="8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb"
PYTHON=Path(sys.executable)

def yes(ok,what):
    if not ok: raise RuntimeError(what)

class MockObserver:
    def __init__(self, fault=""):
        self.fault=fault
        self.verified=[]
    def start(self): pass
    def bind(self,pid,creation): pass
    def poll(self): pass
    def checkpoint(self,stage):
        self.verified.append(stage)
        if self.fault=="CHECKPOINT" and stage=="COUNT":
            raise w.Refusal("Fake foreign module")
        if self.fault=="HANG" and stage=="COUNT":
            time.sleep(20)
    def finish(self): return {"valid":self.fault!="TAIL"}
    def close(self): pass

def fixture_env(fault=""):
    return {"SystemRoot":os.environ["SystemRoot"],"HS_B_FAULT":fault}

def vanished(pid,stamp):
    op=w.api("OpenProcess",w.W.HANDLE,w.W.DWORD,w.W.BOOL,w.W.DWORD)
    h=op(0x00101000,False,pid)
    if not h:
        return ctypes.get_last_error()==87
    try:
        return w.process_creation(h)!=stamp or w.Wait(h,2500)==0
    finally:
        w.CloseHandle(h)

def isolate_death(root,mode):
    log=r.Journal(root,{"scope":"CPU-FIXTURE","mode":mode})
    if mode=="watchdog":
        job=w.AtomicJob()
        r.execute(job,log,MockObserver("HANG"),[FAKE],FAKE.parent,fixture_env(),"cpu-fake",.6,1.2)
        raise RuntimeError("watchdog failed to stop hung owner")
    job=w.AtomicJob()
    if mode=="before_create":
        os._exit(44)
    # Pure Python sleep stays active independently of EOF or a missing controller.
    job.create([PYTHON,"-I","-S","-B","-c","import time;time.sleep(60)"],root,fixture_env())
    log.record({"kind":"OWNED_SUSPENDED","pid":job.pid,"creation_filetime":job.creation,"active":job.active()})
    if mode=="after_resume":
        job.resume()
    os._exit(44)

def events(root):
    return [json.loads(x)["event"] for x in (root/"attempt.jsonl").read_bytes().splitlines()]

def malformed_tail(mode):
    # A CPU protocol adversary with a successful-looking body but invalid ending.
    body=dict(schema="heterospec.e06.probe.v1",backend="cpu-fake",pid=os.getpid(),uuid=r.UUID,
              device_count=1,device_name="NVIDIA GeForce RTX 5070 Ti Laptop GPU",cupti_version=28,
              count_correlation=1,uuid_correlation=2,runtime_records=2,driver_records=0,
              context_records=0,memcpy_records=0,kernel_records=0,api_callbacks=4,drop_reads=[0,0],
              dropped=0,flush_ok=True,drained=True,physical_upper_bound=None)
    if mode=="silent": time.sleep(3)
    print("READY",flush=True)
    for stage in r.STAGES:
        yes(input()=="GO_"+stage,"Stage mismatch")
        print("OK_"+stage,flush=True)
    if mode=="malformed":
        print("RECEIPT {",flush=True)
        return
    print("RECEIPT "+json.dumps(body),flush=True)
    if mode!="no_end": print("END",flush=True)
    if mode=="bad_exit": raise SystemExit(19)
    if mode=="trailing": print("extra",flush=True)

def expect_denied(fn):
    try: fn()
    except (w.Refusal,OSError,ValueError): return
    raise RuntimeError("expected refusal")

def run(root):
    root.mkdir(parents=True,exist_ok=False)
    yes(hashlib.sha256(FAKE.read_bytes()).hexdigest()==DIGEST and FAKE.name=="cpu-probe.exe","CPU fixture identity")
    results=[]
    def record(case,detail): results.append({"case":case,"verified":detail})
    for fault in ("","meter","load","count","uuid","close","flush","drop","incomplete","unattributed",
                  "pool","kernel","count2","wrong_uuid","late","CHECKPOINT","TAIL"):
        case=fault or "complete"
        dest=root/case
        log=r.Journal(dest,{"scope":"CPU-FIXTURE","fault":fault})
        job=w.AtomicJob()
        observer=MockObserver(fault)
        try:
            argv=[FAKE]
            args=job,log,observer,argv,FAKE.parent,fixture_env(fault),"cpu-fake"
            if fault:
                expect_denied(lambda:r.execute(*args,work=4,hard=6))
            else:
                yes(r.execute(*args,work=4,hard=6)=="COMPLETE","Success protocol")
            yes(job.exit_code() is not None and job.active()==0,"Owned child not confirmed exited")
        finally:
            job.close()
            log.close()
        rows=events(dest)
        result=rows[-1]
        yes(result["kind"]==("FAILED" if fault else "COMPLETE") and result["owned_process_exit_confirmed"] is True,case+" terminal")
        yes(rows[1]["kind"]=="OWNED_SUSPENDED" and rows[1]["active"]==1,case+" suspended proof")
        expect_denied(lambda:r.Journal(dest,{}))
        record(case,{"terminal":result,"stages_checked":observer.verified})
    for mode in ("before_create","before_resume","after_resume","watchdog"):
        dest=root/("death-"+mode)
        worker=subprocess.run([PYTHON,"-I","-S","-B",__file__,"--death",str(dest),mode],timeout=12)
        yes(worker.returncode==(125 if mode=="watchdog" else 44),"Fault owner did not exit as expected")
        rows=events(dest)
        claimed=[e for e in rows if e["kind"]=="OWNED_SUSPENDED"]
        if mode!="before_create":
            yes(len(claimed)==1 and vanished(claimed[0]["pid"],claimed[0]["creation_filetime"]),
                "Owned child survived controller death")
        yes(rows[0]["kind"]=="RESERVED" and rows[-1]["kind"] not in ("COMPLETE","FAILED"),"Fabricated outcome")
        expect_denied(lambda:r.Journal(dest,{}))
        record(mode,{"controller_exit":worker.returncode,"remaining_lease":"RESERVED/UNKNOWN","confirmed_gone":len(claimed)})
    # Same UUID, different controller. Different thread is needed for Windows recursive mutex semantics.
    import threading
    lockid="CPU-TEST-"+os.urandom(8).hex()
    with w.DeviceLock(root/"owned.lock",lockid):
        output=[]
        def contender():
            try:
                with w.DeviceLock(root/"other.lock",lockid): output.append("acquired")
            except w.Refusal: output.append("refused")
        th=threading.Thread(target=contender)
        th.start()
        th.join()
        yes(output==["refused"],"Concurrent owner admitted")
    foreign=root/"do-not-remove.lock"
    foreign.write_bytes(b"not ours")
    expect_denied(lambda:w.DeviceLock(root/"own2.lock",lockid,[foreign]).acquire())
    yes(foreign.read_bytes()==b"not ours","Foreign lock changed")
    record("contention_and_foreign_marker",True)
    success=next(x["line"] for x in events(root/"complete") if x.get("line","").startswith("RECEIPT "))
    good=json.loads(success[8:])
    for k,v in (("pid",True),("api_callbacks",2),("drop_reads",[False,0]),("drop_reads",[1,0]),("dropped",1),
                ("uuid_correlation",good["count_correlation"]),("kernel_records",1),("physical_upper_bound",4096),
                ("backend","native")):
        expect_denied(lambda:r.verify_receipt(dict(good,**{k:v}),good["pid"],"cpu-fake"))
    record("forged_receipt",9)
    pinned=root/"fixture-input.txt"
    pinned.write_bytes(b"fixture bytes")
    pins=r.Pins()
    try:
        rpath={"path":str(pinned),"sha256":r.code_digest(pinned.read_bytes())}
        yes(pins.pin(rpath)==pinned,"Wrong held identity")
        expect_denied(lambda:pinned.open("r+b"))
        expect_denied(lambda:pins.pin(dict(rpath,sha256="0"*64)))
    finally:
        pins.close()
    record("pinned_image_write_and_substitution_denied",True)
    # CPU fixtures exercise validation only. Never serialize a native approval.
    ctx=r.runner_context()
    shared=dict(runner_context=ctx,observed_utc=w.utc(),management_library_loads=0,numerical_DLL_loads=0)
    etw=dict(shared,scope="CPU_ETW_ONLY",observer_sha256="ab"*32,start_status=0,stop_status=0,
             loss_counters=[0,0,0],counts={"1":1,"2":1,"5":2},**{"pass":True})
    acl=dict(shared,scope="CPU_APPCONTAINER_ONLY",cpu_probe_sha256=DIGEST,package=r.PACKAGE,
             principal_model_read_denied=True,job_active_limit=1,protected_model_paths=2,
             readable_image_count=12,**{"pass":True})
    class Values:
        def pin(self,record,decode): return record
    rel={"observation":{"sha256":"ab"*32},"cpu_probe":{"sha256":DIGEST}}
    def gate(left,right):
        r.validate_smokes(Values(),{"etw_smoke":left,"appcontainer_smoke":right},rel,2,12)
    gate(etw,acl)
    for key,val in (("start_status",5),("stop_status",4201),("pass",False),("loss_counters",[0,True,0]),
                    ("runner_context","00"*32),("counts",{"1":1,"2":0,"5":2})):
        expect_denied(lambda:gate(dict(etw,**{key:val}),acl))
    for key,val in (("pass",False),("protected_model_paths",1),("readable_image_count",0)):
        expect_denied(lambda:gate(etw,dict(acl,**{key:val})))
    record("CPU_smoke_authority_schema_and_refusals",9)
    quota=r.Journal(root/"quota",{"scope":"CPU-test"})
    try:
        # A synthetic near-full usage value exercises the same write guard without 64 MiB of output.
        quota.used=r.CAP-r.TERMINAL_SPACE-1
        expect_denied(lambda:quota.record({"kind":"over_quota"}))
        quota.record({"kind":"FAILED","reason":"quota"},terminal=True)
    finally:
        quota.close()
    record("bounded_evidence_terminal_space",True)
    torn=root/"short-write"
    journal=r.Journal(torn,{"scope":"CPU-short-write"})
    class PartialFile:
        def __init__(self,f): self.f=f
        def write(self,buf): return self.f.write(buf[:9])
        def close(self): self.f.close()
    before=journal.used
    journal.file=PartialFile(journal.file)
    try:
        expect_denied(lambda:journal.record({"kind":"stage_permit_consumed","stage":"METER"}))
        yes(journal.poisoned and journal.used==before+9,"Partial write accounting")
        expect_denied(lambda:journal.record({"kind":"COMPLETE"},terminal=True))
        expect_denied(lambda:journal.record({"kind":"FAILED"},terminal=True))
    finally:
        journal.close()
    lines=(torn/"attempt.jsonl").read_bytes().splitlines()
    yes(len(lines)==2 and len(lines[1])==9 and json.loads(lines[0])["event"]["kind"]=="RESERVED",
        "Torn write did not preserve known durable prefix")
    expect_denied(lambda:r.Journal(torn,{}))
    record("actual_short_write_poisoned_no_terminal_no_replay",{"partial_bytes":9,"outcome":"UNKNOWN"})
    dest=root/"short-at-first-permit"
    class TornPermit(r.Journal):
        def record(self,event,terminal=False):
            if event.get("kind")=="stage_permit_consumed" and not self.poisoned:
                self.file=PartialFile(self.file)
            super().record(event,terminal)
    log=TornPermit(dest,{"scope":"CPU-short-permit"})
    job=w.AtomicJob()
    try:
        expect_denied(lambda:r.execute(job,log,MockObserver(),[FAKE],FAKE.parent,fixture_env(),"cpu-fake",
                                       work=4,hard=6))
        yes(job.exit_code() is not None and job.active()==0,"Torn grant survived")
    finally:
        job.close()
        log.close()
    lines=(dest/"attempt.jsonl").read_bytes().splitlines()
    yes(len(lines[-1])==9 and json.loads(lines[-2])["event"]["line"]=="READY","Grant escaped torn evidence")
    expect_denied(lambda:r.Journal(dest,{}))
    record("short_write_before_GO_METER_contained",{"last_complete_line":"READY","outcome":"UNKNOWN"})
    # Try creating a second real CPU process from inside an already full Job.
    job=w.AtomicJob()
    try:
        script=("import subprocess,sys\ntry:\n"
                " p=subprocess.Popen([sys.executable,'-I','-S','-B','-c','pass'])\n"
                "except OSError as exc:\n print('REFUSED',exc.winerror,flush=True)\n"
                "else:\n print('ADMITTED',p.wait(),flush=True)\n")
        job.create([PYTHON,"-I","-S","-B","-c",script],root,fixture_env())
        job.resume()
        yes(w.Wait(job.process,3000)==0,"Active-limit CPU test timed out")
        result=job.read(job.output)
        # Kernel accounting may lag the already-signaled process handle.
        stop=time.monotonic()+1
        while job.active() and time.monotonic()<stop:
            time.sleep(.01)
        yes(result and result.strip()==b"REFUSED 1816" and job.active()==0,
            "Missing ERROR_NOT_ENOUGH_QUOTA or Job did not drain: "+repr(result))
    finally:
        job.close()
    record("second_CPU_process_refused_in_one_member_Job",result.decode().strip())
    for mode in ("malformed","no_end","bad_exit","trailing","silent"):
        dest=root/("protocol-"+mode)
        log=r.Journal(dest,{"scope":"CPU-tail","mode":mode})
        job=w.AtomicJob()
        try:
            argv=[PYTHON,"-I","-S","-B",__file__,"--wire",mode]
            expect_denied(lambda:r.execute(job,log,MockObserver(),argv,HERE,fixture_env(),"cpu-fake",
                                           work=.25 if mode=="silent" else 4,hard=6))
        finally:
            job.close()
            log.close()
        terminal=events(dest)[-1]
        yes(terminal["kind"]=="FAILED" and terminal["owned_process_exit_confirmed"],"Bad tail accepted")
        record("protocol_"+mode,terminal)
    payload={"scope":"CPU only","fixture_sha256":DIGEST,"tests":results,
             "normal_numerical_dll_loads":0,"model_loads":0,"gpu_contexts":0,"physical_launches":0}
    (root/"RESULT.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf8")
    print("PASS",len(results),root.name)

if __name__=="__main__":
    if sys.argv[1:2]==["--death"]:
        isolate_death(Path(sys.argv[2]),sys.argv[3])
    elif sys.argv[1:2]==["--wire"]:
        malformed_tail(sys.argv[2])
    else:
        if len(sys.argv)!=2 or not sys.argv[1].isdecimal():
            raise SystemExit("use an unused numeric run ID")
        run(HERE/"cpu-checks"/("run-"+sys.argv[1]))

