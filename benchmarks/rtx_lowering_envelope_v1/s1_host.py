"""Before-start native lifecycle/loaded-module gate. No default GPU permission.

S0 may test dry serialization only. Real execution requires the separately
approved S1A receipt, committed authenticated F0 bytes and all frozen identities.
This first stage controller deliberately admits only the one zero-compute census.
No numerical/timing panel auto-starts when it ends.
"""
import argparse,ctypes,hashlib,json,os,subprocess,time
from pathlib import Path
import audit
import safety
from s0_budget import ROOT,save
from recover_s0 import sha
def admit(f0,approval):
    assert approval['stage']=='S1A_SUPPORT_ONLY' and approval['author_message_sha256'] and approval['approved_F0_sha256']==sha(ROOT/'registration/S1_F0.json')
    remote=audit.load(ROOT/'registration/AUTHENTICATED_S1_F0.json');assert remote['sha256']==approval['approved_F0_sha256']
    assert (ROOT/'registration/REMOTE_S1_F0_BYTES.json').read_bytes()==(ROOT/'registration/S1_F0.json').read_bytes()
    for item in f0['files']:assert sha(item['path'])==item['sha256'],item['path']
    assert f0['stage_limits']['support_host_attempts']==1
def main():
    p=argparse.ArgumentParser();p.add_argument('--approval',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    f0=audit.load(ROOT/'registration/S1_F0.json');approval=audit.load(a.approval);admit(f0,approval)
    root=Path(a.output);assert root.resolve()==Path(f0['execution_root']).resolve(),'fixed one-shot stage root'
    assert not (ROOT/'execution_ledger/S1_CENSUS_STARTED.json').exists(),'census already started; no retry'
    root.mkdir(exist_ok=False)
    safety.query(f0['admission_policy'],root/'HOST_ADMISSION.json')
    # No framework imports or subprocesses can initialize CUDA before this ledger.
    job=audit.load(ROOT/'DESCRIPTOR_PLAN.json');job['approved_stage_F0']=approval['approved_F0_sha256']
    save(root/'ADMITTED_JOB.json',job);exe=ROOT/'native/build/bin/lowering113.exe';command=[str(exe),'--gpu-census',str(root/'ADMITTED_JOB.json'),str(root/'CENSUS.json')]
    receipt=dict(slot='S1/census',epoch=time.time(),command=command,F0_sha256=approval['approved_F0_sha256'],graph_cap=0,operator_host_attempts=1)
    # This global exclusive receipt prevents a second output path from replaying
    # the one census slot. Failures are terminal pending protocol review.
    save(ROOT/'execution_ledger/S1_CENSUS_STARTED.json',receipt);save(root/'BEFORE_START.json',receipt)
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','CUDA_','LLAMA_ARG_'))};env['GGML_CUDA_DISABLE_GRAPHS']='1'
    env['PATH']=job['runtime_directory']+os.pathsep+env.get('PATH','')
    begin=time.perf_counter();native=None;code=-1;failure=None
    try:
        with (root/'native.stdout.log').open('xb') as out,(root/'native.stderr.log').open('xb') as err:
            native=subprocess.Popen(command,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            save(root/'PROCESS.json',dict(pid=native.pid,epoch=time.time(),monitor='owned-PID deadline polling; source module receipt; no periodic GPU sampling or continuous residency claim'))
            while native.poll()is None:
                if time.perf_counter()-begin>240:raise TimeoutError('support host240s ceiling')
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>128*1024*1024:raise RuntimeError('complete support receipt128MiB cap')
                time.sleep(.1)
            code=native.wait();assert code==0,'native census failed; do not retry'
        census=audit.load(root/'CENSUS.json');audit.modules(census['modules'],f0['numerical_DLLs'],job['runtime_directory'])
        decision=audit.census(audit.load(ROOT/'CPU_ACCEPTED/SUPPORT_REGISTRY_S0.json'),census)
        save(root/'PREOUTPUT_SELECTION.json',decision)
    except BaseException as exc:
        failure=repr(exc)
        if native and native.poll()is None:native.kill();native.wait()
        save(root/'FAILED.json',dict(error=failure,already_started_no_scientific_retry=True))
    finally:save(root/'LIFETIME.json',dict(seconds=time.perf_counter()-begin,pid=native.pid if native else None,exit_code=code,failure=failure,graphs=0))
    if failure:raise RuntimeError(failure)
    print('Support-only census ended. Commit/authenticate selection and obtain the next exact authorization before any graph compute.')
if __name__=='__main__':main()
