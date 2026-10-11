"""Single owned native worker, paid immutable slots, inclusive resident request timer."""
from run_common import *
import math, urllib.request, urllib.error
import mechanism

def command(family,c):
    pair=models()[family];exe=LOCAL/'native/build/bin/llama-server.exe'
    a=[str(exe),'--model',pair['target']['path'],'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','2048','--ubatch-size',str(c['prefill_ub']),'--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0','--cache-type-k','f16','--cache-type-v','f16','--host','127.0.0.1','--port',str(PORT),'--no-webui','--no-warmup','--no-cache-prompt']
    if c['spec']:a+=['--spec-type','draft-simple','--model-draft',pair['draft']['path'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max',str(c['maximum_k']),'--spec-draft-n-min','0','--spec-draft-p-min','0','--spec-draft-threads','24','--spec-draft-threads-batch','24','--spec-draft-type-k','f16','--spec-draft-type-v','f16']
    return a

class Ledger:
    def __init__(self):
        self.root=LOCAL/'ledger';self.root.mkdir(exist_ok=True);self.events=[read(p) for p in sorted(self.root.glob('*.json'))]
        self.life=sum(read(p)['seconds'] for p in (LOCAL/'runs').rglob('LIFETIME.json'))
    def lifetime(self):return self.life
    def count(self,family,phase,kind=None):return sum(e['family']==family and e['phase']==phase and (kind is None or e['kind']==kind) for e in self.events)
    def charge(self,family,phase,kind,slot):
        assert not any(e['slot']==slot for e in self.events),'started slot immutable, no retries'
        if phase in ('core','profile'):
            assert self.count(family,phase)<(360 if phase=='core' else 128),'engineering cap exhausted'
        else:
            if kind in ('request','warmup'):assert sum(e['phase']=='formal' and e['kind']==kind for e in self.events)<(3600 if kind=='request' else 150)
        assert self.lifetime()<16*3600-252,'owned lifetime exhausted'
        outer=read(PUB/'F0A.json')['utc'];assert (datetime.now(timezone.utc)-datetime.fromisoformat(outer)).total_seconds()<7*86400
        e=dict(index=len(self.events),utc=now(),family=family,phase=phase,kind=kind,slot=slot,paid_units=0 if phase=='formal' and kind=='load' else 1)
        save(self.root/f'{len(self.events):06d}.json',e);self.events.append(e)
        return e
    def started(self,slot):return any(e['slot']==slot for e in self.events)

def runtime_identity(family):
    b=read(PUB/'NATIVE_BUILD.json');return digest(dict(native_source=b['source_inventory_sha256'],server=b['server_sha256'],DLLs=b['numerical_DLL_sha256'],models=models()[family],contract_sha256=sha(PUB/'MODEL_CONTRACT.json')))

def normalize(response,task,family,c,mode,eog=None):
    ids=response.get('tokens');assert isinstance(ids,list) and all(type(i)is int for i in ids),'invalid native IDs'
    if eog is None:eog=set(read(PUB/'MODEL_CONTRACT.json')['families'][family]['eog'])
    obs=response.get('hs_closeout',{});assert obs['adapter']=='hsc89-v1' and obs['mode']==mode
    assert obs['scope_mask']==c['mask'] and obs['context']==1024 and obs['effective_batch']==1024 and obs['target_ub']==c['prefill_ub']
    assert obs['phase_timers']==(mode in ('lite','heavy')) and obs['heavy_capture']==(mode=='heavy')
    assert obs['added_sync']==(mode=='heavy') and obs['etw'] is False
    # cache_n is reused prompt work. tokens_cached is the final occupied KV length.
    out=dict(ids=ids,eog_flags=[x in eog for x in ids],length=len(ids),terminal_id=ids[-1] if ids else None,stop_reason='EOG' if response.get('stop_type')=='eos' else ('CAP' if response.get('stop_type')=='limit' else response.get('stop_type')),cached_tokens=response.get('timings',{}).get('cache_n'),truncated=response.get('truncated'))
    valid=closeout.output_valid({'output':out},task['cap'],eog) and len(ids)==response.get('tokens_predicted') and response.get('timings',{}).get('prompt_n')==len(task['prompt_ids'])
    return out,bool(valid),obs

class Resident:
    def __init__(self,ledger,family,c,phase,name):
        self.ledger=ledger;self.family=family;self.c=c;self.phase=phase;self.name=name
        self.d=LOCAL/'runs'/phase/family/name;self.cmd=command(family,c)
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));self.module_receipt=None
        self.eog=set(read(PUB/'MODEL_CONTRACT.json')['families'][family]['eog'])
    def request(self,route,body=None,timeout=240):
        data=None if body is None else json.dumps(body,ensure_ascii=False).encode()
        req=urllib.request.Request('http://127.0.0.1:'+str(PORT)+route,data=data,headers={'Content-Type':'application/json'})
        with self.opener.open(req,timeout=timeout) as r:return json.load(r)
    def __enter__(self):
        self.ledger.charge(self.family,self.phase,'load',self.phase+'/'+self.family+'/'+self.name+'/LOAD')
        self.d.mkdir(parents=True,exist_ok=False)
        assert sha(self.cmd[0])==read(PUB/'NATIVE_BUILD.json')['server_sha256']
        save(self.d/'COMMAND.json',dict(command=self.cmd,condition=self.c,family=self.family,phase=self.phase,utc=now(),runtime_identity_sha256=runtime_identity(self.family),hidden_startup_warmup=False))
        self.log=(self.d/'server.log').open('xb');self.start=time.perf_counter()
        self.p=subprocess.Popen(self.cmd,stdout=self.log,stderr=subprocess.STDOUT,env=clean_env(self.c['mask'],self.d/'trace.jsonl'),creationflags=subprocess.CREATE_NO_WINDOW)
        save(self.d/'PROCESS.json',dict(pid=self.p.pid,utc=now()))
        try:
            deadline=time.monotonic()+240
            while True:
                if self.p.poll()is not None:raise RuntimeError('worker exited '+str(self.p.returncode))
                try:
                    if self.request('/health',timeout=2).get('status')=='ok':break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise TimeoutError('native load readiness')
                time.sleep(.5)
            h=host();save(self.d/'LOADED_HOST.json',h)
            assert h['AC']==1 and h['total_MiB']-h['used_MiB']>=512,'loaded GPU headroom or AC failed'
            text=(self.d/'server.log').read_text(encoding='utf-8',errors='replace')
            layers=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',text)
            assert len(layers)==(2 if self.c['spec'] else 1) and all(a==b for a,b in layers),'full offload required; ordinary must not load draft'
            contexts=re.findall(r'n_ctx\s+=\s+(\d+)',text);ubs=re.findall(r'n_ubatch\s+=\s+(\d+)',text)
            assert contexts and all(int(x)==1024 for x in contexts)
            assert int(ubs[0])==self.c['prefill_ub'] and (not self.c['spec'] or int(ubs[-1])==1)
            capacity=re.findall(r'n_outputs_max_per_seq\s+=\s+(\d+)',text)
            assert capacity and int(capacity[0])>=self.c['required_output_rows']
            self.loaded_identity=dict(layers=layers,contexts=contexts,ubs=ubs,output_capacity_per_seq=capacity,log_sha256_at_readiness=sha(self.d/'server.log'),native_parameters=[x for x in text.splitlines() if any(k in x for k in ['n_ctx','n_batch','n_ubatch','KV buffer','compute buffer','n_outputs_max','flash_attn'])])
            save(self.d/'LOAD_IDENTITY.json',self.loaded_identity);return self
        except BaseException:self.__exit__(None,None,None);raise
    def verify_modules(self,obs):
        if self.module_receipt:return
        pinned={n.lower():h for n,h in read(PUB/'NATIVE_BUILD.json')['numerical_DLL_sha256'].items()};seen={};rows=[]
        for name in obs['modules']:
            p=Path(name);n=p.name.lower()
            if n in pinned:
                actual=sha(p);assert actual==pinned[n] and p.resolve().parent==(LOCAL/'native/build/bin').resolve()
                seen[n]=actual;rows.append(dict(path=name,sha256=actual))
            elif n=='llama.dll':raise AssertionError('unexpected shared llama core')
            elif n=='llama-server.exe':assert sha(p)==read(PUB/'NATIVE_BUILD.json')['server_sha256']
        assert {'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=set(seen),'missing actual numeric modules'
        self.module_receipt=dict(pid=self.p.pid,modules=rows,verified=True,utc=now())
        save(self.d/'MODULE_IDENTITY.json',self.module_receipt)
    def complete(self,task,slot,warmup=False,mode='counts',meta=None):
        assert self.ledger.lifetime()+time.perf_counter()-self.start<16*3600-252,'owned lifetime including active worker exhausted'
        self.ledger.charge(self.family,self.phase,'warmup' if warmup else 'request',slot)
        d=self.d/'requests'/hashlib.sha256(slot.encode()).hexdigest()[:24];d.mkdir(parents=True,exist_ok=False)
        phase='formal' if self.phase=='formal' else ('exposed_profile' if self.phase=='profile' else 'exposed_engineering')
        freeze=read(LOCAL/('F0B_REMOTE_RECEIPT.json' if self.phase=='formal' else 'F0A_REMOTE_RECEIPT.json'))
        body=dict(prompt=task['prompt_ids'],n_predict=task['cap'],temperature=0,top_k=0,top_p=1,min_p=0,seed=123,cache_prompt=False,return_tokens=True,stream=False,hs_closeout_mode=mode)
        save(d/'REQUEST_STARTED.json',dict(slot=slot,utc=now(),body=body,input_sha256=digest(task),freeze_commit=freeze['commit'],family=self.family,condition=self.c,phase=phase,warmup=warmup))
        trace=self.d/'trace.jsonl';offset=trace.stat().st_size if trace.exists() else 0
        try:
            start_ns=time.perf_counter_ns();response=self.request('/completion',body)
            out,valid,obs=normalize(response,task,self.family,self.c,mode,self.eog)
            end_ns=time.perf_counter_ns() # Includes complete body/IDs/stop parsing and endpoint checks.
            self.verify_modules(obs) # Hashing outside the primary timer; same process modules verified.
            work=obs.get('workload');err=None
            if work:
                work['counter_semantics_sha256']=sha(PUB/'COUNTER_SEMANTICS.md')
                try:
                    assert work['unsupported_replay'] is False
                    mechanism.workload_metrics(work,len(out['ids']))
                    assert work['draft_continuation_calls']==work['draft_continuation_rows']
                except (AssertionError,KeyError) as e:err=repr(e)
            r=dict(slot=slot,utc=now(),task=task['id'],family=self.family,condition=self.c['name'],phase=phase,warmup=warmup,freeze_commit=freeze['commit'],input_sha256=digest(task),status='COMPLETED',wall_ms=(end_ns-start_ns)/1e6,request_start_ns=start_ns,request_end_ns=end_ns,runtime_identity_verified=True,measurement_mode=mode,observation={k:obs[k] for k in ('phase_timers','heavy_capture','etw','added_sync')},actual_condition=self.c,output=out,contract_valid=valid,response=response,source_identity_sha256=runtime_identity(self.family),workload=work,workload_error=err,feature_units=obs.get('feature_units'),trace_range=dict(start=offset,end=trace.stat().st_size if trace.exists() else 0),**(meta or {}))
            save(d/'RECORD.json',r);save(d/'COMPLETED.json',dict(record_sha256=sha(d/'RECORD.json'),utc=now()))
            return r
        except BaseException as e:
            save(d/'FAILED.json',dict(slot=slot,status='FAILED',utc=now(),error=repr(e)));raise
    def __exit__(self,*args):
        if self.p.poll()is None:
            self.p.terminate()
            try:self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
        self.log.close();seconds=time.perf_counter()-self.start
        save(self.d/'LIFETIME.json',dict(seconds=seconds,utc=now(),pid=self.p.pid,exit_code=self.p.returncode,phase=self.phase));self.ledger.life+=seconds

def cooldown(path):
    start=time.monotonic();time.sleep(120);samples=[];passed=False;expected=read(PUB/'HOST_ADMISSION.json')['sample']
    while time.monotonic()-start+21<=600:
        batch=[]
        for i in range(3):
            batch.append(host())
            if i<2:time.sleep(10)
        samples+=batch
        passed=all(s['AC']==1 and s['util']<=5 and s['temp']<=55 and all(s[k]==expected[k] for k in ['gpu','driver','total_MiB','power_scheme_guid']) for s in batch) and max(s['temp'] for s in batch)-min(s['temp'] for s in batch)<=2
        if passed:break
    save(path,dict(status='PASS' if passed else 'HOST_ADMISSION_FAILED',seconds=time.monotonic()-start,samples=samples,utc=now()))
    assert passed,'cooldown admission failed'
