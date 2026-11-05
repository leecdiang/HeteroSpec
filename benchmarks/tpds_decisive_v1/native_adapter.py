"""Original-host native batches with one durable all-lane resource ledger."""
from bridge_host import Memory,LIMITS
from build_host import OLD,ROOT,sha,put
from runner import Ledger,kill_owned
from pathlib import Path
import argparse,ctypes,json,os,subprocess,time,shutil
RUNS=Path('D:/rtx184-runs')
def execute(job,output=None):
    out=Path(output) if output else RUNS/job['attempt_id'];out.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(job['attempt_id'],job['reservation'])
    put(out/'job.json',job);p=None;owned=False;status='FAILED';code=None;start=time.monotonic();samples=[]
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock');exe=Path(job['exe']);b=job.get('build_manifest') or json.loads((exe.parent.parent/'BUILD.json').read_bytes())
    try:
        assert sha(exe)==b.get('exe',b.get('executable_sha256'))
        for name,h in b.get('modules',b.get('numerical_modules',{})).items():assert sha(exe.parent/name)==h
        with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=job['attempt_id']),f)
        owned=True
        for name in ('binding','panel','slots','plan','forced','operator_service'):
            if name in job:put(out/(name+'.json'),job[name])
        models=['D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf','D:/HeteroSpec-PC/models/gguf/Qwen3-0.6B-Q8_0.gguf']
        if 'operator_service' in job:cmd=[str(exe),*models,str(out/'operator_service.json'),str(out/'native')];stdin=None
        elif 'forced' in job:cmd=[str(exe),str(out/'native'),*models,str(out/'forced.json'),str(out/'binding.json')];stdin=None
        else:cmd=[str(exe),str(out/'native'),*models,str(out/'panel.json'),str(out/'slots.json'),'Qwen',str(out/'binding.json'),str(out/'plan.json')];stdin=subprocess.PIPE
        put(out/'launch.json',dict(argv=cmd,exe_sha256=sha(exe),reservation=job['reservation'],limits=dict(wall_s=job.get('timeout_s',1800),disk_free_bytes=20*1024**3,ram_free_bytes=4*1024**3)))
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr,(out/'live-resources.jsonl').open('x') as telemetry:
            env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
            p=subprocess.Popen(cmd,stdin=stdin,stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            admitted=False
            while p.poll() is None:
                m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
                row=dict(seconds=time.monotonic()-start,disk_free=shutil.disk_usage(out).free,ram_free=m.available)
                if not samples or len(samples)%5==0:
                    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=10).strip().splitlines()
                    assert len(gpu)==1;row['gpu_free_bytes']=int(gpu[0])*1024**2
                    if row['gpu_free_bytes']<128*1024**2:raise RuntimeError('live GPU reserve below 128 MiB')
                if stdin and not admitted and (out/'native/PROVISIONED.json').exists():
                    provision=json.loads((out/'native/PROVISIONED.json').read_bytes());memory=provision['memory_after_provisioning']
                    assert 256*1024**2<=memory['free_bytes']<=memory['total_bytes'],'insufficient admitted GPU reserve'
                    p.stdin.write(b'RUN\n'+b'CONTINUE\n'*len(job['slots']));p.stdin.flush();p.stdin.close();admitted=True
                telemetry.write(json.dumps(row)+'\n');telemetry.flush();samples.append(row)
                if row['seconds']>job.get('timeout_s',1800) or row['disk_free']<20*1024**3 or row['ram_free']<4*1024**3:raise RuntimeError('live resource limit')
                time.sleep(1)
            code=p.returncode
        assert code==0,f'native exit {code}'
        service=job.get('operator_service')
        if service and 'forced' not in service:
            result=dict(status='COMPLETE',requests=[dict(record=s['id']+'/receipt.json') for block in service['blocks'] for s in block['slots']])
            slots=[dict(slot_id=s['id'],arm=block['arm'],input_id=s['input']['id']) for block in service['blocks'] for s in block['slots']]
        else:
            result=json.loads((out/'native/result.json').read_bytes());assert result['status']=='COMPLETE';slots=job.get('slots',[])
        records=[]
        if 'forced' in job or (service and 'forced' in service):actual=dict(requests=result['requests'],token_rows=result['token_rows'],operators=0)
        else:
            actual=dict(requests=len(result['requests']),token_rows=0,operators=0)
            for x,slot in zip(result['requests'],slots):
                r=json.loads((out/'native'/x['record']).read_bytes());n=len(r['prompt_ids']);cycles=r['cycles']
                actual['token_rows']+=n+(n+len(cycles)*8 if r['draft_enabled'] else len(r['ids'])-1)
                records.append(dict(slot=slot['slot_id'],arm=slot.get('study_arm',slot['arm']),kind=slot.get('kind','qualification'),input_id=r.get('input_id',slot.get('input_id')),service_s=r['service_seconds'],status='COMPLETE',endpoint=r['endpoint'],native_record=x['record'],executable_sha256=sha(exe)))
        if service:
            observed={}
            for phase in ('before','after'):
                path=out/'native'/('modules-'+phase+'.json')
                if not path.exists():continue # Unchanged historical oracle predates this diagnostic.
                observed[phase]=[];seen=set()
                for value in json.loads(path.read_bytes()):
                    pth=Path(value);key=pth.name.lower();assert key not in seen;seen.add(key);h=sha(pth);observed[phase].append(dict(path=value,sha256=h))
                    if pth.name in b['modules']:assert h==b['modules'][pth.name]
                    elif key.startswith(('ggml','cublas','cudart')):raise RuntimeError('unbound numerical module '+value)
            put(out/'ACTUAL_MODULES.json',observed)
        for k in actual:assert actual[k]<=job['reservation'][k],(k,actual,job['reservation'])
        put(out/'session-result.json',dict(attempt_id=job['attempt_id'],completed=True,actual_work=actual,records=records,qualification_claim=False))
        status='COMPLETE';return out
    except BaseException as e:put(out/'failure.json',dict(error=repr(e)));raise
    finally:
        if p is not None:kill_owned(p)
        if owned:lock.unlink()
        put(out/'exit.json',dict(status=status,code=code,seconds=time.monotonic()-start));ledger.finish(job['attempt_id'],status,code);ledger.close()
def draft_job(label,arm='D1',modes=('heavy','off'),source_index=0):
    admit=OLD.parent/'admission-Qwen-v4';panel=json.loads((admit/'PANEL.json').read_bytes());templates=json.loads((admit/'SLOTS.json').read_bytes())
    use='D1' if arm=='M' else arm;ub=int(use[1:]);exe=ROOT/'draft-v3'/use/'bin/worker.exe'
    binding=json.loads((admit/'BINDING.json').read_bytes());binding['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST';binding['families']['Qwen'].update(executable_sha256=sha(exe),draft_ubatch=ub)
    plan=json.loads((admit/'PLAN.json').read_bytes());plan['context']['draft_ubatch']=ub
    template=next(x for x in templates if x['arm']==('M_QB' if arm=='M' else 'C_QB') and x['source_index']==source_index)
    slots=[dict(template,slot_id=kind,observer='heavy' if kind=='heavy' else 'off',study_id='tpds_decisive_rtx_draft_v1',draft_ubatch=ub,study_arm=arm) for kind in modes]
    return dict(attempt_id=label,exe=str(exe),binding=binding,panel=panel,slots=slots,plan=plan,reservation=dict(requests=len(slots),token_rows=8000*len(slots),operators=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session-job',type=Path);p.add_argument('--output-dir',type=Path);p.add_argument('--development-arm');a=p.parse_args()
    if a.development_arm:execute(draft_job('development-v3-'+a.development_arm,a.development_arm))
    else:execute(json.loads(a.session_job.read_bytes()),a.output_dir)
