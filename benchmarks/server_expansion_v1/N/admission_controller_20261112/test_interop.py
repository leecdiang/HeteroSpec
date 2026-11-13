"""Actual std-only C++ client <-> Python controller CPU test, not a model run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import subprocess
import threading
import time
from controller import Controller, Broker, process_identity, sha, encoded
from generate_manifest import instantiate_cpu_manifest, finalize_manifest_cpu

class SyntheticPolicy:
    def check(self, snapshot, now, phase="DURING_WORK"):
        return {"status":"PASS","native_execution_authorized":False,
                "scope":"EXPLICIT_CPU_INTEROP_FIXTURE_NO_RESOURCE_ADMISSION"}

class NeverVerifier:
    def verify(self, stage):
        raise RuntimeError("this partial CPU IPC fixture has no raw stage dataset")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe",required=True);p.add_argument("--sha256",required=True)
    p.add_argument("--out",required=True);args=p.parse_args()
    root=Path(args.out)
    if not root.is_absolute() or root.exists():
        raise RuntimeError("fresh absolute short output directory required")
    binary=Path(args.probe)
    raw=binary.read_bytes()
    if len(raw)>4*1024*1024 or sha(raw)!=args.sha256:
        raise RuntimeError("std-only probe identity mismatch")
    elf=subprocess.run(["readelf","-d",str(binary)],capture_output=True,text=True,check=True)
    needed=re.findall(r"Shared library: \[([^]]+)\]",elf.stdout)
    allowed={"libstdc++.so.6","libgcc_s.so.1","libc.so.6","libm.so.6"}
    if not needed or "libstdc++.so.6" not in needed or set(needed)-allowed:
        raise RuntimeError("non-standard/model/GPU ELF refused before execution")
    root.mkdir(mode=0o700);(root/"capture").mkdir(mode=0o700)
    manifest=instantiate_cpu_manifest("std-only-controller-client-interop",time.time(),time.monotonic(),60)
    manifest["identity_bindings"]={"scope":"SYNTHETIC_CPU_INTEROP", "probe_sha256":args.sha256}
    for w in manifest["workers"]:w["executable_sha256"]=args.sha256
    manifest=finalize_manifest_cpu(manifest)
    controller=Controller(root/"run",manifest,NeverVerifier(),SyntheticPolicy(),
                          lambda:{},lambda:manifest["identity_bindings"])
    for d in manifest["deployments"]:
        if d["kind"]=="PREFLIGHT":controller.synthetic_preflight(d["id"])
    worker=manifest["workers"][0];lease="b"*64
    requests=root/"REQUESTS.txt"
    requests.write_text("\n".join(worker["request_ids"])+"\n")
    owner=process_identity()
    broker=Broker(controller,str(root/"control.sock"),timeout=3)
    argv=[str(binary),"--cpu-only-probe",str(root/"control.sock"),manifest["run_id"],
          controller.store.fingerprint,worker["id"],lease,str(root/"capture"),
          str(owner["pid"]),str(owner["start_ticks"]),owner["boot_id"],
          worker["deployment_id"],str(requests)]
    env=os.environ.copy();env["CUDA_VISIBLE_DEVICES"]=""
    child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,text=True,env=env)
    errors=[];thread=None;peer=None
    try:
        peer=process_identity(child.pid)
        ready,_,_=select.select([child.stdout],[],[],5)
        if not ready:raise RuntimeError("owned CPU probe ready timeout")
        first=child.stdout.readline()
        if first.strip()!="CPU_ONLY_PROBE_READY":raise RuntimeError("wrong CPU barrier")
        if process_identity(child.pid)!=peer:raise RuntimeError("CPU barrier process identity changed")
        controller.start_mock_worker(worker["id"],peer,lease,args.sha256)
        def serve():
            try:broker.serve_one()
            except BaseException as e:errors.append(str(e))
        thread=threading.Thread(target=serve);thread.start()
        child.stdin.write("1\n");child.stdin.flush()
        # Observe kernel zombie status without reaping: controller then owns waitpid.
        deadline=time.monotonic()+10
        while True:
            observed=os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
            if observed is not None:break
            if time.monotonic()>=deadline:raise RuntimeError("owned CPU probe timeout")
            time.sleep(.005)
        thread.join(4)
        if thread.is_alive() or errors:raise RuntimeError("IPC failed: "+str(errors))
        # This test owns the child and drains its known tiny CPU output before
        # presenting a source-derived witness, never a submitted PASS receipt.
        def observed_exit(bound_peer):
            if process_identity(child.pid)!=bound_peer:raise RuntimeError("exit owner changed")
            pid,code=os.waitpid(child.pid,0)
            out=first+child.stdout.read(4097);err=child.stderr.read(4097)
            child.returncode=os.WEXITSTATUS(code) if os.WIFEXITED(code) else -1
            (root/"STDOUT.log").write_text(out);(root/"STDERR.log").write_text(err)
            clean=(len(out.encode())<=4096 and len(err.encode())<=4096 and
                   "CPU_ONLY_INTEROP_PROBE_PASS" in out and not err)
            return {"peer":bound_peer,"exited":os.WIFEXITED(code),
                "exit_code":child.returncode,"exit_confirmed":pid==bound_peer["pid"],
                "supervisor_status":"OWNED_CHILD_EXITED" if clean else "OUTPUT_FAILURE",
                "logs_status":"COMPLETE" if clean else "FAIL"}
        controller.exit_probe=observed_exit
        state=controller.confirm_worker_exit(worker["id"])
        if state["worker_index"]!=1 or state["stage_index"]!=0:
            raise RuntimeError("IPC closure fabricated a stage qualification")
        counts=state["counts"]
        if counts["requests"]!=8 or counts["rows"]!=8 or counts["placements"]!=3:
            raise RuntimeError("mock cumulative budget mismatch")
        report={"status":"PASS_STD_ONLY_CPP_PYTHON_INTEROP","probe_sha256":args.sha256,
                "NEEDED":needed,"request_events":8,"row_reservations":8,
                "counts_scope":"SYNTHETIC_ACCOUNTING_NOT_MODEL_WORK",
                "counts":counts,"observed_owned_child_exit":0,
                "partial_stage":"R natural worker only; no checkpoint or native qualification",
                "model_creations":0,"backend_initializations":0,"GPU_contexts":0,
                "actual_placement_actions":0,"model_forwards":0,
                "native_ELF_invocations":0}
        (root/"RESULT.json").write_bytes(encoded(report))
        print(json.dumps(report))
    finally:
        if thread is not None:thread.join(4)
        if child.returncode is None:
            # Only this just-spawned, identity-bound CPU child is ours to stop.
            try:
                if process_identity(child.pid)==peer:
                    child.kill();child.wait(timeout=3)
            except (FileNotFoundError,ProcessLookupError,UnboundLocalError):
                pass
        broker.close();controller.store.close()

if __name__=="__main__":main()

