"""Windows host runner: admission -> pilot -> qualification -> paired timing.
User authorization is already given for this bounded study. No historical UUID is reused.
"""
from __future__ import annotations
import argparse, ctypes, datetime as dt, os, queue, shutil, subprocess, sys, threading, time
from pathlib import Path
from common import *
from model_inspect import inspect, target_contract
from design import input_check, slots, qualification, record_check, load_cycle_validator, analyze
DRAFT_SHA='9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
SOURCE_SHA='62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e'

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

class Job:
    """Kill-on-close Windows Job; assigned while native waits for host RUN."""
    def __init__(self,process):
        from ctypes import wintypes as w
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.CreateJobObjectW.restype=w.HANDLE;self.k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR]
        self.k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        self.k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        self.k.CloseHandle.argtypes=[w.HANDLE]
        self.k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT]
        self.k.QueryInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p]
        class BASIC(ctypes.Structure):
            _fields_=[('p',ctypes.c_longlong),('j',ctypes.c_longlong),('flags',w.DWORD),
                      ('minws',ctypes.c_size_t),('maxws',ctypes.c_size_t),('active',w.DWORD),
                      ('affinity',ctypes.c_size_t),('priority',w.DWORD),('sched',w.DWORD)]
        class IO(ctypes.Structure):_fields_=[(k,ctypes.c_ulonglong) for k in ('r','w','o','rb','wb','ob')]
        class EXT(ctypes.Structure):
            _fields_=[('basic',BASIC),('io',IO),('pm',ctypes.c_size_t),('jm',ctypes.c_size_t),('ppm',ctypes.c_size_t),('pjm',ctypes.c_size_t)]
        self.handle=self.k.CreateJobObjectW(None,None);need(self.handle,'CreateJobObject')
        x=EXT();x.basic.flags=0x2000
        try:
            need(self.k.SetInformationJobObject(self.handle,9,ctypes.byref(x),ctypes.sizeof(x)), 'SetInformationJobObject')
            need(self.k.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))), 'AssignProcessToJobObject')
        except BaseException:
            self.k.CloseHandle(self.handle);self.handle=None;raise
    def active(self):
        from ctypes import wintypes as w
        class ACCOUNT(ctypes.Structure):
            _fields_=[('u',ctypes.c_longlong),('k',ctypes.c_longlong),('pu',ctypes.c_longlong),('pk',ctypes.c_longlong),
                      ('faults',w.DWORD),('total',w.DWORD),('active',w.DWORD),('terminated',w.DWORD)]
        x=ACCOUNT();need(self.k.QueryInformationJobObject(self.handle,1,ctypes.byref(x),ctypes.sizeof(x),None),'Job accounting')
        return x.active
    def terminate(self):
        if self.handle:need(self.k.TerminateJobObject(self.handle,3),'job termination failed')
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None

def available_ram():
    class MEM(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page','apage','virtual','avirtual','extended')]
    m=MEM();m.length=ctypes.sizeof(m)
    need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)),'RAM query')
    return int(m.available)

def probe():
    need(os.name=='nt','native study requires the RTX Windows host')
    query=['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.free','--format=csv,noheader,nounits']
    p=subprocess.run(query,capture_output=True,text=True,timeout=30,check=True)
    return {'utc':utc(),'platform':sys.platform,'ram_available_bytes':available_ram(),
            'gpu_csv':p.stdout.strip(),'query':query,'native_model_requests':0}

def source_locks():
    return {p.name:file_hash(p) for p in Path(__file__).parent.glob('*.py')}

def check_locks(bundle):
    pins=read(bundle/'FREEZE.json')
    need(pins['code']==source_locks(),'host code changed after freeze; create documented successor epoch')
    for name,h in pins['files'].items():need(file_hash(bundle/name)==h,'frozen bundle changed: '+name)
    local=read(bundle/'LOCAL_PATHS.json')
    for name,p in local['assets'].items():
        need(file_hash(p)==pins['assets'][name],'asset changed: '+name)
    return local

def prepare(config,pilot,panel,out):
    need(os.name=='nt','prepare actual assets on native Windows; CPU tests use pure helpers')
    c=read(config);out=Path(out);need(not out.exists(),'new epoch root required')
    need(c.get('study_id')==STUDY and c.get('user_authorized') is True,'wrong study/authorization')
    exact_int(c['threads'],24,24,'thread policy')
    res=c['resources']
    for k in ('worker_timeout_seconds','total_native_seconds','max_payload_bytes','min_disk_free_bytes','min_ram_free_bytes','min_vram_free_bytes'):
        positive(res[k],k)
    need(res['min_ram_free_bytes']>=8*1024**3 and res['min_vram_free_bytes']>=1024**3,'do not waive headroom')
    need(res['min_disk_free_bytes']>=20*1024**3,'insufficient disk reserve policy')
    need(0<res['worker_timeout_seconds']<=res['total_native_seconds'],'timeout budget')
    pil,pan=read(pilot),read(panel)
    need(len(pil['inputs'])==4 and len(pan['inputs'])==12,'pilot/formal size')
    for x in pil['inputs']+pan['inputs']:input_check(x)
    for field in ('id','text_sha256','prompt_ids_sha256'):
        need(len({x[field] for x in pan['inputs']})==12,'duplicate formal '+field)
        need(not {x[field] for x in pil['inputs']}&{x[field] for x in pan['inputs']},'pilot/formal overlap: '+field)
    from design import STRATA
    for k,(lo,hi) in STRATA.items():
        group=[x for x in pan['inputs'] if (x.get('domain'),x.get('stratum'))==k]
        need(len(group)==3 and all(lo<=len(x['prompt_ids'])<=hi for x in group),'formal strata not balanced')
    target=Path(c['target']);draft=Path(c['draft']);worker=Path(c['worker']);build=read(c['build_receipt'])
    info=target_contract(inspect(target));draftinfo=inspect(draft)
    need(file_hash(target)==TARGET_SHA256,'wrong target weights')
    need(file_hash(draft)==DRAFT_SHA,'historical draft changed')
    need(build['status']=='BUILT_NOT_QUALIFIED' and build['source_zip_sha256']==SOURCE_SHA,'wrong inherited source cohort')
    need(file_hash(worker)==build['executable_sha256'],'worker/build mismatch')
    need(len(build['numerical_modules'])==21,'original 21 DLL cohort missing')
    assets={'target':str(target.resolve()),'draft':str(draft.resolve()),'worker':str(worker.resolve()),
            'build_receipt':str(Path(c['build_receipt']).resolve())}
    for n,h in build['numerical_modules'].items():
        p=worker.parent/n;need(file_hash(p)==h,'DLL differs: '+n);assets['dll:'+n]=str(p.resolve())
    # Preparation receipts can be revised by the agent before freezing, but never fabricated.
    prep=read(c['preparation_receipt'])
    need(all(prep.get(k) is True for k in ('natural_inputs_checked','exposure_scan_complete','tokenizer_template_checked','gpu_exclusive')),'preparation incomplete')
    assets['preparation_receipt']=str(Path(c['preparation_receipt']).resolve())
    for i,lp in enumerate(c.get('prior_ledgers',[])):assets['prior_ledger:'+str(i)]=str(Path(lp).resolve())
    need(c['gpu_uuid'] and c['gpu_lock_file'],'host GPU identity/coordination lock missing')
    actual=probe();need(c['gpu_uuid'] in actual['gpu_csv'] and '5070' in actual['gpu_csv'],'wrong GPU')
    out.mkdir(parents=True)
    identity={'source_variant':'original','source_zip_sha256':SOURCE_SHA,'executable_sha256':build['executable_sha256'],
      'core_sha256':build['core_sha256'],'worker_source_sha256':build['worker_source_sha256'],
      'numerical_modules':build['numerical_modules'],
      'models':{'target':{'sha256':TARGET_SHA256,'bytes':target.stat().st_size},'draft':{'sha256':DRAFT_SHA,'bytes':draft.stat().st_size}},
      'target_geometry':info['metadata'],'gpu_uuid':c['gpu_uuid']}
    binding={'study_id':STUDY,'status':'PREPARED_RESOURCE_ADMISSION_ONLY','is_synthetic':False,
             'families':{'Qwen':identity},'dense14b':{'threads':24,'target_gpu_layers':24,
              'min_vram_free_bytes':res['min_vram_free_bytes'],'min_ram_free_bytes':res['min_ram_free_bytes']}}
    save(out/'BINDING.json',binding);save(out/'PILOT.json',pil);save(out/'PANEL.json',pan)
    save(out/'CONFIG.json',c);save(out/'HOST_PROBE.json',actual)
    save(out/'PLAN.json',{'study_id':STUDY,'context':{'n_ctx':1024,'n_batch':1024,'target_ub':4,'draft_ub':1,'threads':24,'kv':'F16','flash':False},
        'service_timer_definition':'native resident-model request including state reset, prefill, generation, counters and output assembly; model load/pool provisioning and post-clock raw writes excluded'})
    save(out/'LOCAL_PATHS.json',{'assets':assets,'repo':str(Path(c['repo']).resolve())})
    save(out/'INITIAL_ASSET_HASHES.json',{k:file_hash(v) for k,v in assets.items()})
    save(out/'STATE.json',{'status':'PREPARED','completed_units':[],'pending_units':['admit','pilot','qualification','formal/s0','formal/s1','formal/s2','formal/s3']})
    (out/'LEDGER.jsonl').touch(exist_ok=False)
    return out

def payload_bytes(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def run_unit(bundle,unit,panel,planned,admit=False,validator=None):
    c=read(bundle/'CONFIG.json');local=read(bundle/'LOCAL_PATHS.json');binding=read(bundle/'BINDING.json')
    paths=local['assets'];unitdir=bundle/'units'/unit.replace('/','_')
    if unitdir.exists():
        receipt=read(unitdir/'RECEIPT.json')
        need(receipt.get('success') is True and receipt.get('active_processes_after_wait')==0,'prior attempt incomplete/failed; no automatic retry')
        need(read(unitdir/'SLOTS.json')==planned and read(unitdir/'PANEL.json')==panel,'recovery plan differs')
        result=read(unitdir/'native'/'result.json')
        need(result['status']==('RESOURCE_ADMITTED' if admit else 'COMPLETE'),'incomplete native result')
        if not admit:
            need(len(result['requests'])==len(planned),'incomplete recoverable request set')
            for slot in planned:
                r=read(confined(unitdir/'native',slot['slot_id']+'.json'))
                if validator:validator(r,slot,panel['inputs'][slot['source_index']])
        return unitdir/'native'
    need(not unitdir.exists(),'fresh attempt required')
    unitdir.mkdir(parents=True);out=unitdir/'native';save(unitdir/'PANEL.json',panel);save(unitdir/'SLOTS.json',planned)
    ledger=[json.loads(line) for lp in [bundle/'LEDGER.jsonl',*[Path(x) for x in c.get('prior_ledgers',[])]] for line in lp.read_text().splitlines() if line]
    used=sum(x.get('reserved_requests',0) for x in ledger if x.get('event')=='START')
    need(used+(0 if admit else len(planned))<=800,'cumulative request ceiling')
    spent=sum(x.get('seconds',0) for x in ledger if x.get('event')=='END')
    need(spent<c['resources']['total_native_seconds'],'native time exhausted')
    need(shutil.disk_usage(bundle).free>=c['resources']['min_disk_free_bytes'],'disk reserve')
    need(available_ram()>=c['resources']['min_ram_free_bytes'],'RAM reserve')
    argv=[paths['worker'],str(out),paths['target'],paths['draft'],str(unitdir/'PANEL.json'),str(unitdir/'SLOTS.json'),'Qwen',str(bundle/'BINDING.json'),str(bundle/'PLAN.json')]+(['--admit-pools'] if admit else [])
    env=dict(os.environ)
    for k in list(env):
        if k.startswith(('HS_','HSC_','JSA_','GGML_')):del env[k]
    env['CUDA_VISIBLE_DEVICES']=c['gpu_uuid']
    append(bundle/'LEDGER.jsonl',{'event':'START','unit':unit,'utc':utc(),'reserved_requests':0 if admit else len(planned),'argv':argv})
    start=time.monotonic();p=None;job=None;success=False;err=None;active=None;events=[]
    q=queue.Queue()
    try:
        with (unitdir/'stderr.log').open('xb') as stderr:
            p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,encoding='utf-8',env=env,
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
            job=Job(p)
            def reader():
                try:
                    for line in p.stdout:q.put(line)
                finally:q.put(None)
            thread=threading.Thread(target=reader,daemon=True);thread.start();index=0;ready=False
            timeout=min(c['resources']['worker_timeout_seconds'],c['resources']['total_native_seconds']-spent)
            while True:
                need(time.monotonic()-start<timeout,'owned worker timeout')
                need(available_ram()>=c['resources']['min_ram_free_bytes'],'runtime RAM reserve exhausted')
                try:line=q.get(timeout=.5)
                except queue.Empty:continue
                if line is None:break
                event=json.loads(line);events.append(event)
                with (unitdir/'events.jsonl').open('a',encoding='utf-8') as f:f.write(line)
                if event['event']=='POOLS_READY':
                    need(not ready,'duplicate ready');ready=True
                    mem=read(out/'PROVISIONED.json')['memory_after_provisioning']
                    need(mem['free_bytes']>=c['resources']['min_vram_free_bytes'],'VRAM reserve')
                    p.stdin.write('RUN\n');p.stdin.flush()
                elif event['event']=='REQUEST_COMPLETED':
                    need(index<len(planned) and event['slot_id']==planned[index]['slot_id'],'out-of-order native slot')
                    r=read(confined(out,planned[index]['slot_id']+'.json'))
                    if validator:validator(r,planned[index],panel['inputs'][planned[index]['source_index']])
                    need(payload_bytes(bundle)<c['resources']['max_payload_bytes'],'payload ceiling')
                    need(shutil.disk_usage(bundle).free>=c['resources']['min_disk_free_bytes'],'disk exhausted')
                    p.stdin.write('CONTINUE\n');p.stdin.flush();index+=1
                else:raise ValueError('unknown worker event')
            code=p.wait(timeout=30);need(code==0,'native process failed')
            result=read(out/'result.json')
            need(result['status']==('RESOURCE_ADMITTED' if admit else 'COMPLETE'),'native terminal status')
            need(result.get('normal_cleanup_returned') is True,'native cleanup missing')
            need(admit or index==len(planned),'incomplete native slot count')
            active=job.active();need(active==0,'job still owns live processes');success=True
    except BaseException as exc:
        err=repr(exc)
        if job:
            job.terminate()
        elif p and p.poll() is None:p.kill()
        if p:p.wait(timeout=30)
        if job:active=job.active()
        raise
    finally:
        if job:job.close()
        if p:
            if p.stdin:p.stdin.close()
            if p.stdout:p.stdout.close()
        receipt={'event':'END','unit':unit,'utc':utc(),'seconds':time.monotonic()-start,'success':success,'error':err,
                 'pid':p.pid if p else None,'active_processes_after_wait':active,'native_completed_events':sum(e.get('event')=='REQUEST_COMPLETED' for e in events)}
        save(unitdir/'RECEIPT.json',receipt);append(bundle/'LEDGER.jsonl',receipt)
    return out

def advance(bundle):
    need(os.name=='nt','native execution only on Windows RTX host')
    bundle=Path(bundle).resolve();c=read(bundle/'CONFIG.json');state=read(bundle/'STATE.json')
    lock=Path(c['gpu_lock_file']);lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('x',encoding='utf-8') as f:f.write(json.dumps({'pid':os.getpid(),'bundle':str(bundle),'utc':utc()}))
    try:
        pil,pan=read(bundle/'PILOT.json'),read(bundle/'PANEL.json');binding=read(bundle/'BINDING.json')
        if state['status']=='PREPARED':
            for k,h in read(bundle/'INITIAL_ASSET_HASHES.json').items():need(file_hash(read(bundle/'LOCAL_PATHS.json')['assets'][k])==h,'prepared asset changed')
            admitted=False
            for layers in (24,20,16):
                binding['dense14b']['target_gpu_layers']=layers;save(bundle/'BINDING.json',binding)
                try:
                    run_unit(bundle,'admit_'+str(layers),pil,slots(pil,'pilot')[:1],admit=True);admitted=True;break
                except (ValueError,subprocess.SubprocessError,OSError):
                    # Only an identified memory-capacity refusal may choose the next smaller placement.
                    rr=bundle/'units'/('admit_'+str(layers))/'native'/'result.json'
                    if not rr.exists():raise
                    msg=read(rr).get('error','').lower()+' '+(rr.parent.parent/'stderr.log').read_text(errors='replace').lower()
                    if not any(t in msg for t in ('headroom','out of memory','failed to allocate','not enough memory')):raise
            need(admitted,'none of the three predetermined placements admitted; no quantization/model fallback')
            binding['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST';save(bundle/'BINDING.json',binding)
            frozen=('CONFIG.json','PANEL.json','PILOT.json','BINDING.json','PLAN.json','LOCAL_PATHS.json')
            save(bundle/'FREEZE.json',{'utc':utc(),'code':source_locks(),'files':{n:file_hash(bundle/n) for n in frozen},'assets':read(bundle/'INITIAL_ASSET_HASHES.json')},exclusive=True)
            state.update(status='ADMITTED');state['pending_units'].remove('admit');save(bundle/'STATE.json',state)
        local=check_locks(bundle);binding=read(bundle/'BINDING.json');cycle=load_cycle_validator(local['repo'])
        validate=lambda r,s,x:record_check(r,s,x,binding,cycle)
        for name,panel in (('pilot',pil),('qualification',pan)):
            if name in state['completed_units']:continue
            schedule=slots(panel,name);out=run_unit(bundle,name,panel,schedule,validator=validate)
            result=qualification(out,panel,schedule,binding,cycle);save(bundle/(name.upper()+'_AUDIT.json'),result)
            need(result['status']=='PASS',name+' not qualified; retain full counterexample matrix, do not time')
            state['completed_units'].append(name);state['pending_units'].remove(name);state['status']=name.upper()+'_PASS';save(bundle/'STATE.json',state)
        qa=read(bundle/'QUALIFICATION_AUDIT.json');need(qa['status']=='PASS','missing qualification')
        seal=bundle/'QUALIFICATION_SEAL.json'
        if seal.exists():need(read(seal)['sha256']==file_hash(bundle/'QUALIFICATION_AUDIT.json'),'qualification summary changed')
        else:save(seal,{'sha256':file_hash(bundle/'QUALIFICATION_AUDIT.json'),'utc':utc()},exclusive=True)
        # Reconstruct the qualification from raw artifacts, not only saved booleans.
        live=qualification(bundle/'units'/'qualification'/'native',pan,slots(pan,'qualification'),binding,cycle)
        need(live==qa,'qualification artifacts changed after original audit')
        refs=qa['references'];qualroot=bundle/'units'/'qualification'/'native'
        qslots=slots(pan,'qualification');byref={}
        for s in qslots:
            if s['observer']=='off':byref[(s['source_index'],s['arm'])]=read(confined(qualroot,s['slot_id']+'.json'))
        def timed_validate(r,s,x):
            validate(r,s,x);need(endpoint(r)==refs[x['id']],'timed endpoint does not preserve R')
            old=byref[s['source_index'],s['arm']]
            for k in ('cycles','target_final_kv','draft_final_kv'):need(r[k]==old[k],'timed state/work changed')
        for session in range(4):
            name='formal/s'+str(session)
            if name in state['completed_units']:continue
            check_locks(bundle);run_unit(bundle,name,pan,slots(pan,'formal',session),validator=timed_validate)
            state['completed_units'].append(name);state['pending_units'].remove(name);state['status']='PARTIAL_TIMING';save(bundle/'STATE.json',state)
        records=[]
        for s in range(4):
            out=bundle/'units'/('formal_s'+str(s))/'native'
            for slot in slots(pan,'formal',s):
                r=read(confined(out,slot['slot_id']+'.json'));timed_validate(r,slot,pan['inputs'][slot['source_index']]);records.append(r)
        result=analyze(records)
        result['paired_internal_diagnostics']=qa['paired_diagnostics']
        result['isolated_recorded_work_comparison']=all(x['logical_work_equal'] for x in qa['paired_diagnostics'])
        result['interpretation']='matched recorded work' if result['isolated_recorded_work_comparison'] else 'complete-request joint path effect; do not claim isolated layout execution cost'
        save(bundle/'ANALYSIS.json',result)
        state.update(status='COMPLETE',pending_units=[]);save(bundle/'STATE.json',state)
        return result
    finally:
        # Native job closes before control returns here. A failed termination must be checked by the host.
        entries=[json.loads(x) for x in (bundle/'LEDGER.jsonl').read_text().splitlines() if x]
        last=entries[-1] if entries else {}
        unresolved=last.get('event')=='START' or (last.get('pid') is not None and last.get('active_processes_after_wait')!=0)
        if not unresolved:lock.unlink()
        else:save(bundle/'LOCK_REQUIRES_HOST_INSPECTION.json',{'utc':utc(),'lock':str(lock),'reason':'owned-process emptiness not established; do not remove lock without checking actual host'})

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('probe')
    p=sub.add_parser('prepare')
    for x in ('config','pilot','panel','out'):p.add_argument('--'+x,type=Path,required=True)
    p=sub.add_parser('advance');p.add_argument('--bundle',type=Path,required=True)
    a=ap.parse_args()
    if a.cmd=='probe':print(json.dumps(probe(),indent=2))
    elif a.cmd=='prepare':print(prepare(a.config,a.pilot,a.panel,a.out))
    else:
        try:print(json.dumps(advance(a.bundle),indent=2))
        except Exception as e:
            save(a.bundle/'BLOCKED.json',{'utc':utc(),'status':'STOPPED_REVIEW_REQUIRED','error':str(e),'next_action':'Repair permitted technical cause using ENGINEERING_POLICY.md; do not change reference to erase a numerical failure.'})
            raise
