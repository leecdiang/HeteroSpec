"""Fixed-slot RTX execution. The resident HTTP clock and request recipe are inherited."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORK=REPO.parent
sys.path.insert(0,str(WORK/'cpu-deps'))
import psutil

def read(path):return json.loads(Path(path).read_bytes())
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def require(ok,message):
    if not ok:raise ValueError(message)
def signature(record):return {k:record['output'][k] for k in ['ids','eog_flags','length','terminal_id','stop_reason','cached_tokens','truncated']}

class Ledger:
    def __init__(self,root,budget):
        self.root=root;self.budget=budget;self.events=[read(p) for p in (root/'ledger').glob('*.json')]
        self.life=sum(read(p)['seconds'] for p in (root/'runs').rglob('LIFETIME.json')) if (root/'runs').exists() else 0
    def lifetime(self):return self.life
    def charge(self,family,phase,kind,slot):
        require(not any(e['slot']==slot for e in self.events),'scientific slot already started; no retry')
        require(self.life<self.budget['owned_seconds']-self.budget['cleanup_seconds'],'owned-time budget exhausted')
        require(sum(e['kind']=='load' for e in self.events)<self.budget['model_workers'] if kind=='load' else sum(e['kind']!='load' for e in self.events)<self.budget['model_requests'],'model-process/request ceiling')
        event={'family':family,'stage':phase,'kind':kind,'slot':slot,'epoch':time.time()}
        save(self.root/'ledger'/f'{len(self.events):06d}.json',event);self.events.append(event)

def check_freeze(config,commit,registration):
    require(not sys.flags.optimize,'optimized Python disables inherited guards')
    body=subprocess.check_output(['git','show',commit+':'+registration],cwd=REPO)
    require(body==Path(config).read_bytes(),'local freeze differs')
    remote=subprocess.check_output(['gh','api','repos/leecdiang/HeteroSpec/contents/'+registration+'?ref='+commit,'-H','Accept: application/vnd.github.raw+json'],cwd=REPO)
    require(remote==body,'authenticated freeze readback differs')
    frozen=read(config)
    for pin in frozen['files']:
        require(Path(pin['path']).stat().st_size==pin['bytes'] and sha(pin['path'])==pin['sha256'],'frozen bytes drift: '+pin['path'])
    return frozen

def setup(config):
    root=Path(config['run_root']);root.mkdir(exist_ok=True)
    sys.path.insert(0,config['legacy'])
    common=importlib.import_module('run_common');native=importlib.import_module('resident')
    for module in (common,native):module.LOCAL=root;module.PUB=root;module.PORT=config['port']
    for name,path in config['inherited_public_files'].items():
        dest=root/name
        if not dest.exists():dest.write_bytes(Path(path).read_bytes())
    build_state={};original_read=native.read
    def bound_read(path):
        if Path(path).resolve()==(root/'NATIVE_BUILD.json').resolve():return build_state['build']
        return original_read(path)
    native.read=bound_read
    return root,native,build_state

def host_gate(native,config):
    sample=native.host()
    require(all(sample[k]==config['host'][k] for k in ['gpu','driver','total_MiB','power_scheme_guid']),'host identity/power scheme drift')
    require(sample['AC']==1,'AC power required')
    require(sample['temp']<=config['budget']['maximum_temperature_C'],'host temperature ceiling')
    require(shutil_disk_free(Path(config['run_root']))>=config['budget']['minimum_free_bytes'],'storage headroom exhausted')
    used=sum(path.stat().st_size for path in Path(config['run_root']).rglob('*') if path.is_file())
    require(used<config['budget']['storage_bytes'],'study storage ceiling exhausted')
    for process in psutil.process_iter(['name','pid']):
        require(not (process.info['name'] or '').lower().startswith('llama-server'),'another model worker is active')
    return sample

def shutil_disk_free(root):
    import shutil
    return shutil.disk_usage(root).free

def condition(arm):
    return {'name':arm,'prefill_ub':1 if arm=='R' else 4,'maximum_k':0 if arm=='R' else 3,
            'mask':0 if arm in ['R','NATIVE_FAST'] else 3,'spec':arm!='R',
            'required_output_rows':1 if arm=='R' else 4,'layout':'PQ' if arm.startswith('PQ') else 'QB'}

def worker(native,root,state,ledger,config,family,arm,stage,ident):
    variant='metadata4' if family in ['SmolLM2','Llama'] and arm.startswith('PQ') else 'original'
    build=config['builds'][variant];state['build']=build
    c=condition(arm);runtime=Path(build['server']).parent
    class BoundResident(native.Resident):
        def __init__(self):
            super().__init__(ledger,family,c,stage,ident)
            self.cmd[0]=build['server'];self.done=False;self.watch_stop=threading.Event();self.watch_failure=None
            if arm=='NATIVE_FAST':self.cmd[self.cmd.index('--flash-attn')+1]='on'
        def __enter__(self):
            def environment(mask,trace):
                env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
                env.update(HS_SCOPE_MASK=str(mask),HS_Q95_LAYOUT=c['layout'],HS_NATIVE_CAPTURE=str(trace),
                           HS_JSA_CAPTURE=str(self.d/'capture'),HS_JSA_LAYERS=','.join(map(str,config['layers'][family])))
                return env
            native.clean_env=environment
            result=super().__enter__()
            def watch():
                while not self.watch_stop.wait(1):
                    if self.p.poll() is not None:return
                    try:
                        if time.perf_counter()-self.start>config['budget']['per_worker_timeout_seconds']:raise RuntimeError('worker timeout')
                        if psutil.Process(self.p.pid).memory_info().rss>config['budget']['memory_bytes']:raise RuntimeError('worker memory ceiling')
                        if shutil_disk_free(root)<config['budget']['minimum_free_bytes']:raise RuntimeError('storage headroom ceiling')
                    except (psutil.NoSuchProcess,ProcessLookupError):return
                    except Exception as error:
                        self.watch_failure=repr(error);self.p.terminate();return
            self.watch=threading.Thread(target=watch,daemon=True);self.watch.start()
            return result
        def verify_modules(self,observation):
            if self.module_receipt:return
            found={};executable=[]
            for name in observation['modules']:
                path=Path(name);base=path.name
                if base in build['numerical_DLL_sha256']:
                    require(path.resolve().parent==runtime.resolve() and sha(path)==build['numerical_DLL_sha256'][base],'actual numeric module differs')
                    found[base]=sha(path)
                elif base.lower()=='llama-server.exe':executable.append(str(path.resolve()))
                elif base.lower()=='llama.dll':raise ValueError('unexpected shared llama core')
            require(executable==[str(Path(build['server']).resolve())],'actual executable differs')
            require({'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublasLt64_12.dll','cudart64_12.dll'}<=set(found),'actual numerical modules missing')
            self.module_receipt={'pid':self.p.pid,'executable':executable,'modules':found,'verified':True}
            save(self.d/'MODULE_IDENTITY.json',self.module_receipt)
        def complete(self,task,slot,mode,warmup=False):
            ledger.charge(family,stage,'warmup' if warmup else 'request',slot)
            path=self.d/'requests'/hashlib.sha256(slot.encode()).hexdigest()[:24];path.mkdir(parents=True,exist_ok=False)
            body=dict(prompt=task['prompt_ids'],n_predict=128,temperature=0,top_k=0,top_p=1,min_p=0,seed=123,cache_prompt=False,return_tokens=True,stream=False,hs_closeout_mode=mode)
            save(path/'REQUEST_STARTED.json',{'slot':slot,'body':body,'freeze_commit':config['freeze_commit'],'epoch':time.time()})
            try:
                start=time.perf_counter_ns();response=self.request('/completion',body)
                output,valid,observation=native.normalize(response,task,family,c,mode,self.eog)
                end=time.perf_counter_ns()
                self.verify_modules(observation)
                require(valid and output['cached_tokens']==0,'endpoint or prompt-reset contract failed')
                work=observation['workload'];work['counter_semantics_sha256']=sha(root/'COUNTER_SEMANTICS.md')
                native.mechanism.workload_metrics(work,len(output['ids']))
                require(work['unsupported_replay'] is False and work['draft_continuation_calls']==work['draft_continuation_rows'],'workload/draft-UB1 contract')
                record={'slot':slot,'stage':stage,'family':family,'arm':arm,'task_id':task['id'],'warmup':warmup,'mode':mode,
                        'seconds':(end-start)/1e9,'request_start_ns':start,'request_end_ns':end,'output':output,'response':response,
                        'workload':work,'contract_valid':valid,'freeze_commit':config['freeze_commit'],'status':'COMPLETED'}
                save(path/'RECORD.json',record);return record
            except BaseException as error:
                save(path/'FAILED.json',{'slot':slot,'error':repr(error),'traceback':traceback.format_exc()});raise
        def __exit__(self,*args):
            if self.done:return
            self.done=True;self.watch_stop.set()
            if hasattr(self,'p'):
                super().__exit__(*args)
                save(self.d/'CLEANUP.json',{'pid':self.p.pid,'exit_code':self.p.returncode,'exit_verified':self.p.poll() is not None,
                     'termination_requested_after_requests':True,'watchdog_failure':self.watch_failure})
    return BoundResident()

def vectors(root):
    capture=root/'capture';events=[json.loads(line) for line in (capture/'observer.jsonl').read_bytes().splitlines()]
    blob=(capture/'logits.f32').read_bytes();rows=[]
    for event in events:
        if event['event']=='decision_vector':
            offset=event['offset'];data=blob[offset:offset+event['floats']*4]
            require(len(data)==event['floats']*4,'truncated decision vector')
            rows.append((event['role'],event['row'],event['position'],event['input_id'],hashlib.sha256(data).hexdigest()))
    geometry=[event for event in events if event['event']=='geometry']
    return rows,geometry

def run_calibration(config,root,native,state,ledger):
    results=[]
    for family in ['Qwen','SmolLM2','Llama']:
        for index,task in enumerate(config['calibration'][family]):
            for arm in ['R','PQ','QB','NATIVE_FAST']:
                ident=f'{index}_{arm}';host=host_gate(native,config);save(root/'host'/('cal_'+family+'_'+ident+'.json'),host)
                records=[]
                try:
                    with worker(native,root,state,ledger,config,family,arm,'calibration',ident) as active:
                        for mode in ['heavy','counts']:records.append(active.complete(task,f'CAL/{family}/{index}/{arm}/{mode}',mode))
                    rows,geometry=vectors(active.d)
                    equal=signature(records[0])==signature(records[1])==task['reference_output']
                    result={'family':family,'input_index':index,'arm':arm,'status':'QUALIFIED' if equal else 'REFERENCE_OR_OBSERVER_MISMATCH',
                            'records':records,'worker':str(active.d),'decision_vectors':len(rows),'geometry_records':len(geometry)}
                except BaseException as error:
                    result={'family':family,'input_index':index,'arm':arm,'status':'ENGINEERING_FAILURE','records':records,'error':repr(error)}
                save(root/'calibration_results'/(family+'_'+ident+'.json'),result);results.append(result)
                print('CAL',family,index,arm,result['status'],flush=True)
    summary={'stage':'CALIBRATION_COMPLETE','results':results,'eligible_primary':[], 'eligible_fast':[]}
    for family in ['Qwen','SmolLM2','Llama']:
        if all(r['status']=='QUALIFIED' for r in results if r['family']==family and r['arm']!='NATIVE_FAST'):summary['eligible_primary'].append(family)
        if all(r['status']=='QUALIFIED' for r in results if r['family']==family and r['arm']=='NATIVE_FAST'):summary['eligible_fast'].append(family)
    save(root/'CALIBRATION_SUMMARY.json',summary)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--commit',required=True);parser.add_argument('--registration',required=True);parser.add_argument('--stage',choices=['calibration'],required=True);args=parser.parse_args()
    config=check_freeze(args.config,args.commit,args.registration);config['freeze_commit']=args.commit
    root,native,state=setup(config);ledger=Ledger(root,config['budget'])
    with (root/'EXECUTION.lock').open('x') as stream:stream.write(str(os.getpid()))
    try:run_calibration(config,root,native,state,ledger)
    finally:(root/'EXECUTION.lock').unlink()

if __name__=='__main__':main()
