"""One-unit capture. Predictors and native runners receive separate input contracts."""
import ctypes, importlib.util, queue, threading, time, uuid
from prepare import *

def identity(pid):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
    k.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)];k.CloseHandle.argtypes=[ctypes.c_void_p]
    h=k.OpenProcess(0x1000,0,pid)
    if not h:return None
    try:
        times=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(x) for x in times]):return None
        return str(times[0].value)
    finally:k.CloseHandle(h)

def canonical(x):return json.dumps(x,separators=(',',':'),ensure_ascii=True).encode()
def digest(x):return hashlib.sha256(x).hexdigest()
def env():
    keys=['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']
    return {k:os.environ[k] for k in keys if k in os.environ}

class Worker:
    def __init__(self,role,ub,d,old=False,transfer=0):
        self.role=role;self.d=d;self.log=(d/(role+'-wire.jsonl')).open('wb');self.stderr=(d/(role+'-stderr.log')).open('wb');self.q=queue.Queue();self.n=0;self.failed=False
        executable=OUT/'worker-bin'/(role+('-old' if old else '')+'.exe')
        self.cmd=[str(executable),str(RUNTIME),str(ASSET/('models/gguf/Qwen3-0.6B-Q8_0.gguf' if role=='P' else 'models/gguf/Qwen3-8B-Q8_0.gguf')),str(ub),role]
        if not old:self.cmd.append(str(transfer))
        ev=env();ev.update(HS_WORKER_WITNESS=str(d/(role+'-transfer')),LLAMA_BATCH_DEBUG='1')
        self.p=subprocess.Popen(self.cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,cwd=RUNTIME,env=ev)
        save(d/(role+'-PROCESS.json'),{'pid':self.p.pid,'creation_identity':identity(self.p.pid),'command':self.cmd})
        def read_stdout():
            try:
                for b in self.p.stdout:self.q.put(b)
            finally:self.q.put(None)
        threading.Thread(target=read_stdout,daemon=True).start()
        self.ready=self.response()
        self.record('startup',{},self.ready)
    def response(self):
        b=self.q.get(timeout=300)
        if b is None:raise RuntimeError('worker exit '+str(self.p.poll()))
        x=json.loads(b)
        # Legacy workers send all logits for hashes. Preserve those bytes separately;
        # new workers return selected/top scores and explicit transfer witnesses.
        def strip(o):
            if isinstance(o,dict):
                if 'logits_bytes_hex' in o:
                    blob=bytes.fromhex(o.pop('logits_bytes_hex'));h=digest(blob);p=self.d/'logits'/h;p.parent.mkdir(exist_ok=True)
                    if not p.exists():p.write_bytes(blob)
                    o['logits_sha256']=h;o['logits_bytes']=len(blob)
                for v in o.values():strip(v)
            elif isinstance(o,list):
                for v in o:strip(v)
        strip(x)
        if x.get('event')=='ERROR':
            self.failed=True;self.record('error',{},x);raise RuntimeError(x['error'])
        return x
    def record(self,op,q,r):
        self.log.write(canonical({'sequence':self.n,'event':op,'request':q,'response':r})+b'\n');self.log.flush();self.n+=1
    def call(self,q):
        self.record('request_sent',q,{})
        self.p.stdin.write(canonical(q)+b'\n');self.p.stdin.flush();r=self.response();self.record(q['op'],q,r);return r
    def close(self):
        if self.failed:
            if self.p.poll() is None:self.p.wait(timeout=30)
            self.log.close();self.stderr.close();return
        if self.p.poll() is None:
            try:self.call({'op':'close'});self.p.stdin.close();self.p.wait(timeout=30)
            finally:
                if self.p.poll() is None:self.p.kill();self.p.wait()
        self.log.close();self.stderr.close()

def h_run(t,c,rep,d,old=False,transfer=0):
    text=(ROOT/read(OUT/'INPUTS.json')[t]['prompt']).read_text(encoding='utf-8');workers=[]
    try:
        r=Worker('R',2,d,old,transfer);workers.append(r)
        ri=r.call({'op':'init','formatted_prompt':formatted(text)});ids=ri['committed_ids'].copy();pos=len(ri['prompt_ids']);terminal=ri['terminal'];flags=[ri['samples'][0]['eog']];round=0
        p=Worker('P',2,d,old,0);workers.append(p)
        pi=p.call({'op':'init','formatted_prompt':formatted(text)});assert pi['prompt_ids']==ri['prompt_ids']
        previous='0'*64
        with (d/'tape.jsonl').open('xb') as tape:
            while not terminal:
                pp=p.call({'op':'propose','position':pos,'pending':ids[-1],'max_proposals':min(2,128-len(ids)-1)})
                q={'op':'verify','round':round,'position':pos,'pending':ids[-1],'proposal_ids':pp['proposal_ids']}
                row={'task':t,'rep':rep,'condition':c,'round':round,'past_prefix_sha256':digest(canonical(ids)),'past_prefix_count':len(ids),'request':q,'previous_hash':previous}
                row['event_hash']=digest(canonical(row));previous=row['event_hash'];tape.write(canonical(row)+b'\n');tape.flush();os.fsync(tape.fileno())
                v=r.call(q);p.call({'op':'update','position':pos,'verified_batch':[ids[-1]]+pp['proposal_ids'],'retain_count':v['retain_count']})
                ids+=v['committed_ids'];flags += [s['eog'] for s in v['samples'][:len(v['committed_ids'])]];pos=v['next_position'];terminal=v['terminal'];round+=1
        for w in workers:w.close()
        return {'ids':ids,'eog':flags,'endpoint':'EOS' if flags[-1] else 'limit','prompt_ids':ri['prompt_ids'],'transfer':ri.get('transfer'),'tape_sha256':sha(d/'tape.jsonl'),'commands':[w.cmd for w in workers],'modules':{w.role:w.ready['modules'] for w in workers}}
    finally:
        for w in workers:
            if not w.log.closed:
                try:w.close()
                except Exception:
                    if w.p.poll() is None:w.p.kill();w.p.wait()

def native_run(t,c,rep,d,instrument=False,transfer=0):
    spec=importlib.util.spec_from_file_location('v4_native',ROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    oldc='TARGET_REFERENCE' if c=='R' else 'RTX_BATCHED_K2';cmd=m.templates(m.paths(ASSET))[oldc]
    cmd+=['--threads','24','--threads-batch','24']
    if instrument:cmd[0]=str(OUT/'native-build/bin/llama-cli.exe')
    mapping={'{prompt}':str(ROOT/read(OUT/'INPUTS.json')[t]['prompt']),'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')};cmd=[mapping.get(a,a) for a in cmd]
    ev=env();ev['LLAMA_BATCH_DEBUG']='1'
    if instrument:ev['HS_NATIVE_CAPTURE']=str(d/'trace.jsonl')
    if transfer:ev['HS_TARGET_CONTINUATION_UB']=str(transfer)
    with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
        p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=d,env=ev)
        save(d/'PROCESS.json',{'pid':p.pid,'creation_identity':identity(p.pid),'command':cmd})
        try:rc=p.wait(timeout=300)
        except subprocess.TimeoutExpired:p.kill();p.wait();raise
    if rc:raise RuntimeError('native exit '+str(rc))
    # The original parser checks the source UB and full placement; the separate
    # trace checks continuation capacity and transfer state.
    x=m.parse_capture(d/'native.log',oldc)
    result={'ids':x['generated_ids'],'eog':[i in EOG for i in x['generated_ids']],'endpoint':x['termination'],'commands':[cmd],'placement':x['placement'],'stop_markers':x['native_stop_observations']}
    if instrument:
        traces=[json.loads(s) for s in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
        pending=[r for r in traces if r['event']=='first_pending'];assert len(pending)==1
        result['modules']={'native':pending[0]['modules']}
        moves=[r for r in traces if r['event']=='transfer'];assert len(moves)==(1 if transfer else 0)
        result['transfer']=moves[0] if moves else None
        if moves:assert moves[0]['pending_id']==result['ids'][0]
        decodes=[r for r in traces if r['event']=='decode']
        for r in decodes:
            assert r['returncode']==0 and all(s==[0] for s in r['sequence_ids'])
            assert r['ub_capacity']==(2 if r['role']=='draft' or r['phase']=='prefill' and c!='R' else 1 if c=='R' else transfer or 2)
    return result

def attempt_directory(base):
    attempts=sorted(base.glob('attempt-*'))
    if len(attempts)>=2:raise RuntimeError('attempt budget exhausted')
    if attempts:
        previous=attempts[-1]
        failures=previous/'FAILURE.json'
        if failures.exists() and not read(failures).get('transient_io',False):raise RuntimeError('deterministic failed attempt cannot retry')
        for p in previous.glob('*PROCESS.json'):
            x=read(p)
            if identity(x['pid']) is not None and identity(x['pid'])==x['creation_identity']:raise RuntimeError('registered worker still active')
        save(previous/'RECOVERY.json',{'utc':utc(),'reason':'incomplete attempt or recorded transient I/O; original bytes retained','next_attempt':len(attempts)+1})
    d=base/(f'attempt-{len(attempts)+1:02d}-'+uuid.uuid4().hex);d.mkdir();return d

def unit(t,c,rep,namespace,instrument=False,transfer=0,old=False):
    base=OUT/namespace/(t.replace('/','-')+'-'+c+'-r'+str(rep));base.mkdir(parents=True,exist_ok=True)
    if (base/'result.json').exists():
        cached=read(base/'result.json')
        assert cached['valid']
        for name,h in cached['files'].items():assert sha(base/name)==h
        return cached
    d=attempt_directory(base);before=time.monotonic()
    start={'task':t,'condition':c,'rep':rep,'namespace':namespace,'started_utc':utc(),'started_monotonic_ns':time.monotonic_ns(),'instrument':instrument,'transfer':transfer,'old_worker':old,'formal':namespace=='formal','implementation_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'prompt_sha256':sha(ROOT/read(OUT/'INPUTS.json')[t]['prompt'])}
    save(d/'START.json',start)
    try:
        x=h_run(t,c,rep,d,old,transfer) if c.startswith('H') else native_run(t,c,rep,d,instrument,transfer)
        assert x['ids'] and len(x['ids'])<=128 and len(x['ids'])==len(x['eog']) and (x['eog'][-1] or len(x['ids'])==128) and not any(x['eog'][:-1])
        result={**start,**x,'valid':True,'ended_utc':utc(),'ended_monotonic_ns':time.monotonic_ns(),'elapsed_seconds':time.monotonic()-before}
        result['files']={str(p.relative_to(base)).replace('\\','/'):sha(p) for p in d.rglob('*') if p.is_file()}
        save(base/'result.json',result);return result
    except Exception as exc:
        save(d/'FAILURE.json',{**start,'valid':False,'error':repr(exc),'transient_io':isinstance(exc,OSError),'ended_utc':utc(),'elapsed_seconds':time.monotonic()-before});raise

if __name__=='__main__':
    for instrument,transfer in [(True,0),(True,2)]:
        x=unit('HumanEval/15','N0',1,'pilot-native-'+str(transfer),instrument,transfer)
        print(json.dumps({'instrument':instrument,'transfer':transfer,'ids':len(x['ids']),'elapsed':x['elapsed_seconds'],'historical_equal':x['ids']==read(DOC/'HISTORICAL_EXPECTED.json')['HumanEval/15/N0/1']['ids']}),flush=True)
