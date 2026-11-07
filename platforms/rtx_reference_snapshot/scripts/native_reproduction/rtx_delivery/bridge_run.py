"""Bounded owned worker; immutable attempt directories and atomic checkpoint."""
import argparse,datetime,json,os,pathlib,subprocess,time,sys
# Helpers are shipped alongside this portable adapter.
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import sha,read
P=pathlib.Path
def save(p,d):
    p=P(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def run(root,plan,name,timeout=1800):
    root=P(root).resolve();plan=P(plan).resolve();dest=root/name;receipt=root/(name+'-PROCESS.json')
    if dest.exists() or receipt.exists():raise RuntimeError('Existing attempt: inspect receipt, never silently rerun')
    pair=read(root/'MODEL_CONTRACT.json')['families']['Qwen']['models'];exe=root/'bridge-build-v2/bin/rtx-bridge.exe'
    cmd=[str(exe),str(dest),pair['target']['path'],pair['draft']['path'],str(root/'PANEL.json'),str(plan)]
    rec=dict(status='RUNNING',argv=cmd,plan_sha256=sha(plan),exe_sha256=sha(exe),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),timeout_seconds=timeout)
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
    save(receipt,rec);start=time.perf_counter();p=None
    try:
        with (root/(name+'.stdout.log')).open('xb') as out,(root/(name+'.stderr.log')).open('xb') as err:
            p=subprocess.Popen(cmd,stdout=out,stderr=err,env=env,creationflags=subprocess.CREATE_NO_WINDOW);rec['pid']=p.pid;save(receipt,rec)
            try:rc=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
                rec['status']='INTERRUPTED_TIMEOUT';raise
            rec['status']='COMPLETE' if rc==0 else 'FAILED';rec['exit_code']=rc
    finally:
        if p and p.poll() is None:p.terminate();p.wait(timeout=10)
        rec['owned_seconds']=time.perf_counter()-start;rec['cleanup']=p is None or p.poll() is not None
        if (dest/'result.json').exists():rec['result_sha256']=sha(dest/'result.json')
        save(receipt,rec)
    print(json.dumps({k:rec[k] for k in ('status','owned_seconds','cleanup')}),flush=True)
    return rec
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('plan');ap.add_argument('name');ap.add_argument('--timeout',type=int,default=1800);a=ap.parse_args();run(a.root,a.plan,a.name,a.timeout)
