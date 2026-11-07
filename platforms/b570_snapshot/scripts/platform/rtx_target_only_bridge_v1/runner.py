"""Serialized, resumable fresh-process runner. No historical outputs enter model commands."""
import argparse, ctypes, importlib.util, re, time, uuid
from common import *

spec=importlib.util.spec_from_file_location('bridge_native_transport',ROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)

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

def ledger(event,**fields):
    path=OUT/'ATTEMPT_LEDGER.jsonl';rows=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    row={'sequence':len(rows),'previous_hash':rows[-1]['hash'] if rows else '0'*64,'utc':now(),'event':event,**fields}
    row['hash']=hashlib.sha256(canon(row)).hexdigest()
    with path.open('ab') as f:f.write(canon(row)+b'\n');f.flush();os.fsync(f.fileno())

def bindings(formal):
    b={n:sha(DOC/n) for n in ['PROTOCOL.json','INPUT_CONTRACT.json','COHORT.json','ASSET_ENVIRONMENT.json']}
    if formal:b['FREEZE_RECEIPT.json']=sha(DOC/'FREEZE_RECEIPT.json')
    return b

def capture(d,c):
    parsed=native.parse_capture(d/'native.log','H1_TARGET_UB2' if c=='U2' else 'RTX_BATCHED_K2')
    s=(d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
    count_match=re.search(r'new prompt,.*task.n_tokens = (\d+)',s);assert count_match
    count=int(count_match.group(1));tail=s[count_match.end():];end=tail.find('slot process_toke:');assert end>=0
    seen={}
    for m in re.finditer(r'ubatch_print:\s+\d+: id =\s+(\d+) \([\s\S]*?\), pos =\s+(\d+), n_seq_id =\s+(\d+), seq_id = \[([^\]]*)\], output = (\d+)',tail[:end]):
        token,pos,ns,seq,mask=m.groups();pos=int(pos);assert ns=='1' and seq=='0'
        if pos<count:assert pos not in seen or seen[pos]==int(token);seen[pos]=int(token)
    assert set(seen)==set(range(count))
    threads=re.findall(r'system_info: n_threads = (\d+) \(n_threads_batch = (\d+)\)',s);assert threads==[('24','24')]
    pools=list(map(int,re.findall(r'llama threadpool init, n_threads = (\d+)',s)));assert pools and all(n==24 for n in pools)
    ubs=parsed['placement']['context_ubatches'];assert ubs==([2] if c=='U2' else [2,2,1 if c=='N1' else 2])
    assert re.findall(r'llama_context: n_ctx\s*=\s*(\d+)',s)==(['4096']*(1 if c=='U2' else 3))
    assert re.findall(r'llama_context: n_batch\s*=\s*(\d+)',s)==(['2048']*(1 if c=='U2' else 3))
    assert all(x=='disabled' for x in re.findall(r'llama_context: flash_attn\s*=\s*(\w+)',s))
    result={'ids':parsed['generated_ids'],'raw_committed_ids':parsed['generated_ids'],'endpoint':parsed['termination'],'stop_markers':parsed['native_stop_observations'],'prompt_ids':[seen[i] for i in range(count)],'placement':parsed['placement'],'effective_threads':{'target':24,'target_batch':24,'threadpools':pools,'draft':None if c=='U2' else 24,'draft_batch':None if c=='U2' else 24},'raw_commit_overshoot':0}
    if c=='U2':
        assert 'loading draft model' not in s and not (d/'trace.jsonl').exists()
        result['draft_absence_evidence']={'loaded_models':1,'offload_records':[['37','37']],'no_draft_load_marker':True,'no_speculative_init':'adding speculative implementation' not in s}
    else:
        events=[json.loads(l) for l in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
        assert [e['sequence'] for e in events]==list(range(len(events)))
        moves=[e for e in events if e['event']=='transfer'];pending=[e for e in events if e['event']=='first_pending'];assert len(moves)==len(pending)==1
        move=moves[0];assert move['source_ub']==2 and move['destination_ub']==(1 if c=='N1' else 2)
        assert move['state_equal'] and move['source_unchanged'] and move['consumed_bytes']==move['state_bytes']
        assert move['before']==move['after']==move['source_after'] and move['pending_id']==pending[0]['pending_id']==result['ids'][0]
        hs=[sha(d/('trace.jsonl'+suf)) for suf in ['.source_before.kv','.destination.kv','.source_after.kv']];assert len(set(hs))==1
        assert move['sampler_chain']==move['clone_chain'] and move['history']==move['clone_history'] and move['seed']==move['clone_seed']==123
        for e in events:
            if e['event']=='decode':
                assert e['returncode']==0 and e['caller_batch']==len(e['tokens'])==len(e['positions'])==len(e['logits_mask'])
                assert e['ub_capacity']==(2 if e['role']=='draft' or e['phase']=='prefill' else 1 if c=='N1' else 2)
        result.update(transfer=move,modules=pending[0]['modules'],raw_target_samples=[e['selected_id'] for e in events if e['event']=='sample' and e['role']=='target'],raw_verify_decisions=[e['sampled_ids'] for e in events if e['event']=='verify_decision'])
    return result

def run_one(q,namespace):
    t,c,r=q['task'],q['condition'],q['rep'];key=q['key'];formal=namespace=='formal'
    base=OUT/namespace/(t.replace('/','-')+'-'+c+'-r'+str(r));base.mkdir(parents=True,exist_ok=True)
    selected=OUT/'SELECTED_ATTEMPTS.json';chosen=load(selected) if selected.exists() else {}
    if (base/'result.json').exists():
        rec=load(base/'result.json')
        for name,b in rec['files'].items():assert sha(base/name)==b['sha256']
        assert rec['bindings']==bindings(formal)
        # Crash between atomic result and manifest is recovered without model rerun.
        chosen[namespace+'/'+key]={'record':(base/'result.json').relative_to(ROOT).as_posix(),'sha256':sha(base/'result.json'),'attempt':rec['attempt'],'rule':'first complete valid attempt'};save(selected,chosen)
        return rec
    for old in sorted(base.glob('attempt-*')):
        if (old/'PROCESS.json').exists():
            p=load(old/'PROCESS.json');assert identity(p['pid'])!=p['creation_identity'],'prior registered process still alive'
    attempts=sorted(base.glob('attempt-*'))
    for number in range(len(attempts)+1,4):
        if number>1:ledger('RETRY_AFTER_DIAGNOSIS',key=key,namespace=namespace,attempt=number,reason='prior attempt incomplete or infrastructure failure; bytes retained; no outcome-dependent retry')
        d=base/(f'attempt-{number:02d}-'+uuid.uuid4().hex);d.mkdir()
        protocol=load(DOC/'PROTOCOL.json');inputrec=load(DOC/'INPUT_CONTRACT.json')['inputs'][t]
        mapping={'{prompt}':str(ROOT/inputrec['prompt']),'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt'),'{trace}':str(d/'trace.jsonl')}
        cmd=[mapping.get(v,v) for v in protocol['command_templates'][c]]
        overrides={k:mapping.get(v,v) for k,v in protocol['environment_templates'][c].items()};ev=clean_env();ev.update(overrides)
        start={'task':t,'condition':c,'rep':r,'key':key,'namespace':namespace,'attempt':d.name,'started_utc':now(),'started_monotonic_ns':time.monotonic_ns(),'bindings':bindings(formal),'source_commit':PIN,'implementation_head':git('rev-parse','HEAD'),'argv':cmd,'environment_overrides':overrides,'prompt_sha256':sha(ROOT/inputrec['prompt']),'input_ids_sha256':sha(ROOT/inputrec['ids'])}
        save(d/'START.json',start);ledger('ATTEMPT_START',**{k:start[k] for k in ['key','namespace','attempt','bindings']})
        before=time.monotonic();p=None
        try:
            with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
                p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=d,env=ev)
                save(d/'PROCESS.json',{'pid':p.pid,'creation_identity':identity(p.pid),'argv':cmd})
                lastchange=time.monotonic();lastsize=-1
                while p.poll() is None:
                    time.sleep(2)
                    size=sum(f.stat().st_size for f in d.iterdir() if f.is_file())
                    if size!=lastsize:lastsize=size;lastchange=time.monotonic()
                    save(OUT/'HEARTBEAT.json',{'utc':now(),'controller_pid':os.getpid(),'worker_pid':p.pid,'namespace':namespace,'key':key,'elapsed_seconds':time.monotonic()-before,'seconds_since_file_growth':time.monotonic()-lastchange,'selected':len(chosen)})
                    if time.monotonic()-before>300 and time.monotonic()-lastchange>120:raise TimeoutError('stalled own worker after 300s and no file growth120s')
            if p.returncode:raise RuntimeError('process exit '+str(p.returncode))
            rec=capture(d,c);assert rec['prompt_ids']==load(ROOT/inputrec['ids'])
            # Independently retained transcript contains full generated byte pieces.
            prompt=(ROOT/inputrec['prompt']).read_bytes();prompt=prompt[:-1] if prompt.endswith(b'\n') else prompt
            pieces=bytes.fromhex(native.parse_capture(d/'native.log','H1_TARGET_UB2' if c=='U2' else 'RTX_BATCHED_K2')['auxiliary_decoded_bytes_hex'])
            expected=b'User:\n'+prompt+b'\n\nAssistant:\n'+pieces+(b'' if pieces.endswith(b'\n') else b'\n')+b'\n'
            assert (d/'transcript.txt').read_bytes().replace(b'\r\n',b'\n')==expected
            rec={**start,**rec,'process_status':'exit0','exit_code':p.returncode,'ended_utc':now(),'elapsed_seconds':time.monotonic()-before}
            rec['files']={f.relative_to(base).as_posix():{'sha256':sha(f),'bytes':f.stat().st_size} for f in d.rglob('*') if f.is_file()}
            save(base/'result.json',rec)
            chosen[namespace+'/'+key]={'record':(base/'result.json').relative_to(ROOT).as_posix(),'sha256':sha(base/'result.json'),'attempt':d.name,'rule':'first complete valid attempt'};save(selected,chosen)
            ledger('ATTEMPT_VALID',namespace=namespace,key=key,attempt=d.name,record_sha256=sha(base/'result.json'));return rec
        except Exception as exc:
            if p is not None and p.poll() is None:p.kill();p.wait()
            infrastructure=isinstance(exc,(OSError,TimeoutError)) or (isinstance(exc,RuntimeError) and str(exc).startswith('process exit'))
            save(d/'FAILURE.json',{**start,'error':repr(exc),'infrastructure':infrastructure,'ended_utc':now()})
            ledger('ATTEMPT_FAILED',namespace=namespace,key=key,attempt=d.name,error=repr(exc),infrastructure=infrastructure)
            if not infrastructure:raise
    raise RuntimeError('infrastructure attempts exhausted '+key)

def freeze_check():
    receipt=load(DOC/'FREEZE_RECEIPT.json')
    assert git('merge-base',receipt['commit'],git('rev-parse','HEAD'))==receipt['commit']
    for p,h in receipt['files'].items():assert sha(ROOT/p)==h,p
    assert load(DOC/'QUALIFICATION.json')['status']=='PASS'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['engineering','formal','diagnostic']);a=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'LOCK.json'
    if lock.exists():
        x=load(lock);assert identity(x['pid'])!=x['identity'],'controller already active'
        ledger('STALE_LOCK_RECOVERY',previous=x)
        lock.rename(OUT/('LOCK.stale-'+uuid.uuid4().hex+'.json'))
    with lock.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'identity':identity(os.getpid()),'utc':now(),'phase':a.phase},f)
    try:
        protocol=load(DOC/'PROTOCOL.json')
        if a.phase=='engineering':queue=[{'task':t,'condition':c,'rep':1,'key':f'{t}/{c}/1'} for t in protocol['engineering_tasks'] for c in ['N0','N1','U2']]
        elif a.phase=='formal':freeze_check();queue=protocol['queue']
        else:
            freeze_check();selected=load(DOC/'DIAGNOSTIC_SELECTION.json');assert len(selected['tasks'])<=4
            queue=[{'task':t,'condition':c,'rep':1,'key':f'{t}/{c}/1'} for t in selected['tasks'] for c in ['N0','N1','U2']]
        failures=[]
        for i,q in enumerate(queue):
            try:rec=run_one(q,a.phase);print(json.dumps({'completed':i+1,'planned':len(queue),'key':q['key'],'ids':len(rec['ids']),'seconds':round(rec['elapsed_seconds'],2)}),flush=True)
            except Exception as exc:
                failures.append({'key':q['key'],'error':repr(exc)})
                save(OUT/(a.phase+'-FAILURES.json'),failures)
                # Integrity/qualification errors invalidate further dependent execution.
                if not isinstance(exc,RuntimeError) or not str(exc).startswith('infrastructure attempts exhausted'):raise
        save(OUT/(a.phase+'-COMPLETE.json'),{'utc':now(),'planned':len(queue),'failed':failures,'successful':len(queue)-len(failures)})
    finally:
        lock.rename(OUT/('LOCK.finished-'+uuid.uuid4().hex+'.json'))
if __name__=='__main__':main()
