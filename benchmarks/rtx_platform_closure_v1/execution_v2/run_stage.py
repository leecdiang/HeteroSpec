"""Sequential owned-process runner; no same-slot retry."""
import hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
CODE=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def main():
    mode=sys.argv[1];assert mode in ('reference','qual','time')
    reg=read(CODE/'PREREGISTRATION.json');root=Path(reg['raw_root'])
    proof=read(CODE/'FREEZE_RECEIPT.json');assert proof['remote_verified']
    if mode=='qual':assert (CODE/'REFERENCE_FREEZE_RECEIPT.json').exists()
    if mode=='time':assert read(root/'QUALIFICATION_GATE.json')['status']=='ALL_QUALIFIED'
    build=reg['identity'];exe=Path(build['executable']['path'])
    ledger_path=root/'LEDGER.json';ledger=read(ledger_path) if ledger_path.exists() else dict(uuid=reg['uuid'],native_process_starts=0,owned_native_seconds=0,requests_completed=0,receipts=[])
    for i in range(4):
        slot=f'{mode}-{i}';receipt_path=root/(slot+'.PROCESS_RECEIPT.json');assert not receipt_path.exists(),('immutable started slot',slot)
        assert ledger['native_process_starts']<reg['budget']['new_native_process_reservation']
        assert ledger['owned_native_seconds']<reg['budget']['owned_native_seconds_cap']
        assert sha(exe)==build['executable']['sha256']
        for row in build['DLLs']:assert sha(row['path'])==row['sha256']
        assert sha(root/'INPUT_PANEL.json')==reg['input_panel_sha256']
        cmd=[str(exe),str(root/slot),reg['models']['target']['path'],reg['models']['draft']['path'],str(root/'INPUT_PANEL.json'),mode,str(i),str(root)]
        receipt=dict(slot=slot,study_uuid=reg['uuid'],status='STARTING',argv=cmd,started_utc=now(),freeze_commit=proof['commit'],reference_freeze=read(CODE/'REFERENCE_FREEZE_RECEIPT.json')['commit'] if (CODE/'REFERENCE_FREEZE_RECEIPT.json').exists() else None)
        save(receipt_path,receipt);ledger['native_process_starts']+=1;save(ledger_path,ledger)
        start=time.perf_counter()
        with (root/(slot+'.stdout.log')).open('wb') as out,(root/(slot+'.stderr.log')).open('wb') as err:
            env=os.environ.copy()
            removed={k:v for k,v in env.items() if k.startswith(('HS_','GGML_','LLAMA_','CUDA_','OMP_'))}
            for key in removed:env.pop(key)
            save(root/(slot+'.ENVIRONMENT.json'),dict(removed_execution_controls=removed,policy='default CUDA graph mode; explicit executable-local backend DLLs; no observer environment'))
            p=subprocess.Popen(cmd,cwd=exe.parent,stdout=out,stderr=err,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['pid']=p.pid;receipt['status']='STARTED';save(receipt_path,receipt)
            while p.poll() is None:
                if ledger['owned_native_seconds']+time.perf_counter()-start>reg['budget']['owned_native_seconds_cap']:
                    receipt['resource_cap_termination']=True;p.terminate();p.wait();break
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:pass
        elapsed=time.perf_counter()-start
        receipt.update(status='COMPLETED' if p.returncode==0 else 'FAILED',exit_code=p.returncode,exit_observed=True,finished_utc=now(),owned_seconds=elapsed)
        result=read(root/slot/'result.json') if (root/slot/'result.json').exists() else {}
        receipt['native_status']=result.get('status');receipt['normal_cleanup_returned']=result.get('normal_cleanup_returned',False)
        receipt['requests_completed']=len(result.get('requests',[]))
        ledger['owned_native_seconds']+=elapsed;ledger['requests_completed']+=receipt['requests_completed'];ledger['receipts'].append(receipt)
        save(receipt_path,receipt);save(ledger_path,ledger)
        print(json.dumps(receipt),flush=True)
        if p.returncode:raise RuntimeError(f'{slot} failed; preserve and stop: '+result.get('error','no native diagnostic'))
    save(root/(mode.upper()+'_STAGE_COMPLETED.json'),dict(status='COMPLETE',finished_utc=now(),ledger=ledger))
if __name__=='__main__':main()
