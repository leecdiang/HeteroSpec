#!/usr/bin/env python3
"""Second-party offline RTX audit. Standard library only; no experiment imports.

All selected attempts are resolved from result.files. The restore command hashes
the complete CAS archive and every logical file in a new directory. The audit
command reads raw captures independently, retaining complete output arrays.
"""
import argparse, collections, csv, hashlib, json, pathlib, re, tarfile, os, shutil

SOURCE = '3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4'
EOG = {128247,151643,151645,151662,151663,151664}
DOC = pathlib.Path('benchmarks/rtx_target_verification_intervention_v1')
WORK = pathlib.Path('work/rtx-target-v1')

def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def serial(x): return json.dumps(x,separators=(',',':'),ensure_ascii=True).encode()
def lines(p): return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def safe(s):
    p=pathlib.PurePosixPath(s); assert not p.is_absolute() and '..' not in p.parts
    return pathlib.Path(s)

def restore(repo,dest,out):
    assert not dest.exists() or not list(dest.iterdir()), 'clean destination required'
    dest.mkdir(parents=True,exist_ok=True)
    arch=read(repo/'artifacts/rtx_target_verification_intervention_v1/ARCHIVE.json')
    joined=out/'archive.tar.gz'; out.mkdir(parents=True,exist_ok=True); partrows=[]
    with joined.open('wb') as f:
        for part in arch['parts']:
            p=repo/safe(part['path']); h=sha(p); assert h==part['sha256'] and p.stat().st_size==part['bytes']
            partrows.append({'path':part['path'],'sha256':h,'bytes':p.stat().st_size})
            with p.open('rb') as src: shutil.copyfileobj(src,f,8*1024*1024)
    assert sha(joined)==arch['sha256'] and joined.stat().st_size==arch['bytes']
    cas=dest/'_audit_cas'; cas.mkdir(); blobs={}; manifest=None
    with tarfile.open(joined,'r:gz') as tar:
        for entry in tar:
            assert entry.isfile(), entry.name
            if entry.name=='MANIFEST.json': manifest=json.load(tar.extractfile(entry)); continue
            assert re.fullmatch(r'cas/[a-f0-9]{64}',entry.name), entry.name
            h=entry.name[4:]; p=cas/h
            with p.open('wb') as f: shutil.copyfileobj(tar.extractfile(entry),f,8*1024*1024)
            assert sha(p)==h; blobs[h]=p.stat().st_size
    assert manifest is not None
    rows=[]
    for name,row in manifest['files'].items():
        p=dest/safe(name); p.parent.mkdir(parents=True,exist_ok=True); os.link(cas/row['sha256'],p)
        actual=sha(p); assert actual==row['sha256'] and p.stat().st_size==row['bytes'], name
        rows.append({'path':name,'sha256':actual,'bytes':p.stat().st_size})
    assert len(rows)==arch['logical_files'] and len(blobs)==arch['unique_blobs']
    write(out/'RESTORE.json',{'status':'PASS','source':SOURCE,'parts':partrows,'compressed_bytes':joined.stat().st_size,'archive_sha256':sha(joined),'logical_files':len(rows),'unique_blobs':len(blobs),'manifest_sha256':hashlib.sha256(serial(manifest)).hexdigest()})
    write(out/'RESTORED_FILES.json',rows); write(out/'MANIFEST.json',manifest)

def complete(ids):
    assert ids and all(type(i)==int and 0<=i<151936 for i in ids)
    assert len(ids)<=128 and not any(i in EOG for i in ids[:-1])
    terminal=ids[-1] in EOG; assert terminal or len(ids)==128
    return {'ids':ids,'endpoint':'EOS' if terminal else 'limit','cap':128,'inclusive_eog':terminal,'overshoot':max(0,len(ids)-128)}

def native(d):
    s=(d/'native.log').read_bytes().decode('latin1').replace('\r\n','\n')
    # Parse capture fields line-by-line; generated IDs, ordinal and remaining budget
    # are taken from the native logger, never from the report or result.ids.
    found=[]
    for line in s.splitlines():
        if ' D slot process_toke:' in line and 'next token:' in line:
            m=re.search(r'id\s+(\d+) \| task (\d+) \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(-?\d+) ',line)
            assert m, line; found.append(tuple(map(int,m.groups())))
    assert found and {r[0] for r in found}=={0} and len({r[1] for r in found})==1
    assert [r[2] for r in found]==list(range(1,len(found)+1))
    assert all(r[3]==128-r[2] for r in found)
    x=complete([r[4] for r in found]); stops=re.findall(r'stopped by (EOS|limit)',s)
    wanted=(['limit','EOS'] if x['inclusive_eog'] else ['limit']) if len(x['ids'])==128 else ['EOS']
    assert stops==wanted,(d,stops,wanted); x['raw_stop_markers']=stops
    counts=re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',s)
    assert counts==[str(len(found))], (d,counts,len(found))
    x['threads']=[list(map(int,r)) for r in re.findall(r'system_info: n_threads = (\d+) \(n_threads_batch = (\d+)\)',s)]
    x['offload']=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',s)
    x['ub_capacity']=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',s)))
    x['devices']=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',s)
    assert x['devices'] and all(v.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for v in x['devices'])
    n=re.search(r'new prompt,.*task.n_tokens = (\d+)',s); assert n
    count=int(n.group(1)); tail=s[n.end():]; tail=tail[:tail.index('slot process_toke:')]
    prompt={}
    for m in re.finditer(r'ubatch_print:\s+\d+: id =\s+(\d+) \([\s\S]*?\), pos =\s+(\d+), n_seq_id =\s+(\d+), seq_id = \[([^\]]*)\], output = (\d+)',tail):
        token,pos,ns,seq,mask=m.groups(); pos=int(pos); assert ns=='1' and seq=='0'
        if pos<count: assert pos not in prompt or prompt[pos]==int(token); prompt[pos]=int(token)
    assert set(prompt)==set(range(count)); x['prompt_ids']=[prompt[i] for i in range(count)]
    return x

def predictor(d):
    target=lines(d/'R-wire.jsonl'); draft=lines(d/'P-wire.jsonl')
    steps=[r for r in target if r['event'] in ('init','verify')]
    assert steps and steps[0]['event']=='init'
    generated=[]; proposal=[r for r in draft if r['event']=='propose']; update=[r for r in draft if r['event']=='update']; tape=lines(d/'tape.jsonl')
    assert len(proposal)==len(update)==len(tape)==len(steps)-1
    prompt=steps[0]['response']['prompt_ids']; pinit=[r for r in draft if r['event']=='init']; assert len(pinit)==1 and pinit[0]['response']['prompt_ids']==prompt
    previous='0'*64; pos=len(prompt)
    for index,row in enumerate(steps):
        response=row['response']; emitted=response['committed_ids']
        assert [v['selected_id'] for v in response['samples'][:len(emitted)]]==emitted
        if index:
            request=row['request']; p=proposal[index-1]; u=update[index-1]; t=tape[index-1]
            assert request==t['request'] and request['proposal_ids']==p['response']['proposal_ids']
            assert request['round']==index-1 and request['position']==pos and request['pending']==generated[-1]
            assert len(request['proposal_ids'])<=2
            assert response['decode']['tokens']==[generated[-1]]+request['proposal_ids'] and response['decode']['logits_mask']==[1]*(len(request['proposal_ids'])+1)
            assert [v['selected_id'] for v in response['samples']]==response['sampled_ids']
            assert u['request']['verified_batch']==[generated[-1]]+p['response']['proposal_ids'] and u['request']['retain_count']==response['retain_count']
            hashfields=dict(t); h=hashfields.pop('event_hash'); assert h==hashlib.sha256(serial(hashfields)).hexdigest()
            assert t['previous_hash']==previous and t['past_prefix_count']==len(generated) and t['past_prefix_sha256']==hashlib.sha256(serial(generated)).hexdigest(); previous=h
            pos=response['next_position']
        generated.extend(emitted); assert response['terminal']==(generated[-1] in EOG or len(generated)==128)
    x=complete(generated); x['prompt_ids']=prompt; x['transfer']=steps[0]['response'].get('transfer'); x['wire_stop_markers']=[r['response']['terminal'] for r in steps]
    return x

def selected(base):
    record=read(base/'result.json'); assert record['valid'] and record['files']
    prefixes={safe(p).parts[0] for p in record['files']}; assert len(prefixes)==1
    for p,h in record['files'].items(): assert sha(base/safe(p))==h,(base,p)
    d=base/next(iter(prefixes)); assert d.is_dir()
    return record,d

def transfer(d,row,ub,kind):
    assert row['source_ub']==2 and row['destination_ub']==ub
    assert row['state_equal'] and row['source_unchanged'] and row['state_bytes']==row['consumed_bytes']
    assert row['before']==row['after']==row['source_after'] and row['before']['min']==0
    pre='R-transfer' if kind=='H' else 'trace.jsonl'
    paths=[d/(pre+s) for s in ('.source_before.kv','.destination.kv','.source_after.kv')]
    hashes=[sha(p) for p in paths]; assert len(set(hashes))==1 and paths[0].stat().st_size==row['state_bytes']
    logits=d/(pre+'.pending_logits.f32'); assert logits.stat().st_size==151936*4
    if 'sampler_chain' in row: assert row['sampler_chain']==row['clone_chain'] and row['history']==row['clone_history'] and row['seed']==row['clone_seed']==123
    return {'kv_sha256':hashes[0],'pending_logits_sha256':sha(logits),'state_bytes':row['state_bytes'],'source_ub':2,'destination_ub':ub,'sampler':'opaque, clone/history/seed and behavioral controls; no sampler byte-equality claim'}

def equal(x,y): return x['ids']==y['ids'] and x['endpoint']==y['endpoint']
def difference(x,y):
    ix=next((i for i in range(min(len(x['ids']),len(y['ids']))) if x['ids'][i]!=y['ids'][i]),None)
    if ix is None and len(x['ids'])!=len(y['ids']): ix=min(len(x['ids']),len(y['ids']))
    return {'equal':equal(x,y),'first_difference_zero_based':ix,'left_length':len(x['ids']),'right_length':len(y['ids']),'left_endpoint':x['endpoint'],'right_endpoint':y['endpoint'],'left_id':x['ids'][ix] if ix is not None and ix<len(x['ids']) else None,'right_id':y['ids'][ix] if ix is not None and ix<len(y['ids']) else None}

def sham_projection(d,kind):
    if kind=='H':
        def keep(v):
            if isinstance(v,dict): return {k:keep(x) for k,x in v.items() if k not in ('transfer','logits_sha256','logits_bytes')}
            if isinstance(v,list): return [keep(x) for x in v]
            return v
        return [(p.name,r['event'],r['request'],keep(r['response'])) for p in sorted(d.glob('[PR]-wire.jsonl')) for r in lines(p) if r['event'] not in ('startup','request_sent','close')]
    result=[]
    for r in lines(d/'trace.jsonl'):
        if r['event'] in ('transfer','first_pending'): continue
        r=dict(r); r.pop('sequence')
        if r['event']=='sample' and r['role']=='draft': r.pop('selected_id'); r.pop('selected_score')
        result.append(r)
    return result

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True); doc=root/DOC; work=root/WORK
    protocol=read(doc/'PROTOCOL.json'); queue=read(doc/'QUEUE.json'); freeze=read(doc/'FREEZE.json'); omissions=read(doc/'ARCHIVE_OMISSIONS.json')['paths']; inputs=read(work/'INPUTS.json'); history=read(doc/'HISTORICAL_EXPECTED.json')
    assert len(queue)==645 and len(protocol['tasks'])==43 and protocol['repetitions']==3
    assert len({q['id'] for q in queue})==645
    assert {q['id'] for q in queue}=={f"{protocol['study']}/v1/{t}/{c}/{r}" for t in protocol['tasks'] for c in ('R','H0','H1','N0','N1') for r in range(1,4)}
    binding=[]; unavailable=[]
    for name,h in freeze['files'].items():
        if not (root/name).exists(): assert name in omissions; unavailable.append({'path':name,'sha256':h}); continue
        actual=sha(root/name); assert actual==h; binding.append({'path':name,'sha256':actual})
    records={}; raw={}; selected_attempts=[]; graph=collections.defaultdict(lambda:{'caller_tokens':set(),'occupied_tokens':set(),'logits_outputs':set(),'calls':0}); witnesses=[]; native_threads=collections.Counter(); attempts=[]
    def graphs(label,decode):
        g=graph[label]; g['calls']+=1; g['caller_tokens'].add(decode['caller_batch'] if 'caller_batch' in decode else len(decode['tokens']))
        g['occupied_tokens'].update(r['ne'][1] for r in decode['graphs'] if r['name']=='attn_norm-0'); g['logits_outputs'].update(r['ne'][1] for r in decode['graphs'] if r['name']=='result_output')
    for q in queue:
        base=work/'formal'/(q['task'].replace('/','-')+'-'+q['condition']+'-r'+str(q['rep'])); rec,d=selected(base)
        assert rec['unit_id']==q['id'] and rec['freeze_sha256']==sha(doc/'FREEZE.json')
        for field,name in [('protocol_sha256','PROTOCOL.json'),('cohort_sha256','COHORT.json'),('asset_manifest_sha256','ASSET_ENVIRONMENT.json')]: assert rec[field]==sha(doc/name)
        selected_attempts.append({'unit_id':q['id'],'attempt':str(d.relative_to(root)),'result_path':str((base/'result.json').relative_to(root)),'result_sha256':sha(base/'result.json'),'files':rec['files']})
        for a in base.glob('attempt-*'): attempts.append({'unit_id':q['id'],'attempt':str(a.relative_to(root)),'selected':a==d,'failure':read(a/'FAILURE.json') if (a/'FAILURE.json').exists() else None})
        c=q['condition']; x=predictor(d) if c.startswith('H') else native(d)
        assert x['ids']==rec['ids'] and x['endpoint']==rec['endpoint']; assert x['prompt_ids']==read(root/inputs[q['task']]['ids'])
        if c.startswith('H'):
            tr=x['transfer']; assert tr['pending_id']==x['ids'][0]; witnesses.append({'unit_id':q['id'],**transfer(d,tr,1 if c=='H1' else 2,'H')})
            for role in ('P','R'):
                for row in lines(d/(role+'-wire.jsonl')):
                    if row['event']=='startup':
                        ctx=row['response']['context']; assert ctx['threads']==24 and ctx['n_ubatch']==2 and ctx['n_ctx']==4096 and ctx['n_batch']==2048 and ctx['flash_attention']=='off'
                    req=row['request']; assert not any(k in req for k in ('future_native_ids','reference','prediction_ids','sealed_tape'))
                    allow=protocol['H_input_allowlist'].get(row['event'])
                    if allow: assert set(req)==set(allow)
                    rsp=row['response']
                    for decode in ([rsp['decode']] if 'decode' in rsp else [])+rsp.get('decodes',[]): graphs(c+'/'+('draft' if role=='P' else 'target')+'/'+('prefill' if row['event']=='init' else 'continuation'),decode)
        else:
            assert x['threads']==[[24,24]]; native_threads[tuple(x['threads'][0])]+=1
            assert x['offload']==([('37','37')] if c=='R' else [('37','37'),('29','29')])
            assert x['ub_capacity']==([1] if c=='R' else [2,2,1 if c=='N1' else 2])
            assert not any('tape' in v.lower() or 'prediction' in v.lower() for v in rec['commands'][0])
            if c!='R':
                rows=lines(d/'trace.jsonl'); tr=[r for r in rows if r['event']=='transfer']; assert len(tr)==1 and tr[0]['pending_id']==x['ids'][0]
                witnesses.append({'unit_id':q['id'],**transfer(d,tr[0],1 if c=='N1' else 2,'N')})
                first=[r for r in rows if r['event']=='first_pending']; assert len(first)==1
                for r in rows:
                    if r['event']=='decode':
                        assert r['caller_batch']==len(r['tokens'])==len(r['positions'])==len(r['sequence_ids'])==len(r['logits_mask']) and r['returncode']==0 and all(s==[0] for s in r['sequence_ids'])
                        assert r['ub_capacity']==(2 if r['role']=='draft' or r['phase']=='prefill' else 1 if c=='N1' else 2)
                        graphs(c+'/'+r['role']+'/'+r['phase'],r)
        raw[(q['task'],c,q['rep'])]=x; records[q['id']]=rec
        if q['task'] in protocol['old_tasks'] and c in ('R','H0','N0'): assert x['ids']==history[f"{q['task']}/{c}/{q['rep']}"]['ids'] and x['endpoint']==history[f"{q['task']}/{c}/{q['rep']}"]['endpoint']
    comparisons=(('H0','N0'),('H1','N1'),('N0','R'),('N1','R'),('N0','N1')); tasks=[]
    for t in protocol['tasks']:
        row={'task':t,'cohort':'old19' if t in protocol['old_tasks'] else 'new24','comparisons':{}}
        for a,b in comparisons: row['comparisons'][a+'/'+b]=[{'rep':r,**difference(raw[t,a,r],raw[t,b,r])} for r in range(1,4)]
        stable=all(all(equal(raw[t,c,1],raw[t,c,r]) for r in (2,3)) for c in ('R','H0','H1','N0','N1')); assert stable; row['repeat_stable']=stable
        old=all(r['equal'] for r in row['comparisons']['N0/R']); new=all(r['equal'] for r in row['comparisons']['N1/R'])
        row['transition']='match_to_match' if old and new else 'mismatch_to_match' if new else 'match_to_mismatch' if old else 'mismatch_to_mismatch'
        row['native_output_noop']=all(r['equal'] for r in row['comparisons']['N0/N1']); tasks.append(row)
    groups={}
    for g in ('old19','new24'):
        rr=[r for r in tasks if r['cohort']==g]; groups[g]={'tasks':len(rr),'paired_observations':len(rr)*3,'matches':{a+'/'+b:sum(v['equal'] for r in rr for v in r['comparisons'][a+'/'+b]) for a,b in comparisons},'transitions':dict(collections.Counter(r['transition'] for r in rr)),'repeat_stable_tasks':sum(r['repeat_stable'] for r in rr)}
    g0=read(doc/'G0.json'); assert len(g0['records'])==120; qualification={}; sham=[]; reused=0; rerun=0
    for r in g0['records']:
        b=root/r['path']; d=b if (b/'native.log').exists() else selected(b)[1]; kind=r['variant'][0]; x=predictor(d) if kind=='H' else native(d)
        c='H0' if kind=='H' else 'N0' if kind=='N' else 'R'; old=history[f"{r['task']}/{c}/{r['rep']}"]; assert x['ids']==old['ids'] and x['endpoint']==old['endpoint']
        qualification[r['task'],r['rep'],r['variant']]=d
        if kind=='H': reused+=1
        else: rerun+=1; assert x['threads']==[[24,24]]
    for t in protocol['g0_tasks']:
        for r in range(1,4):
            for k in ('H','N'):
                p,s=qualification[t,r,k+'_plain'],qualification[t,r,k+'_sham']; a,b=sham_projection(p,k),sham_projection(s,k); assert a==b
                xp=predictor(p) if k=='H' else native(p); xs=predictor(s) if k=='H' else native(s); assert equal(xp,xs)
                sham.append({'task':t,'rep':r,'kind':k,'plain':str(p.relative_to(root)),'sham':str(s.relative_to(root)),'behavior_projection_sha256':hashlib.sha256(serial(a)).hexdigest(),'full_ids_endpoint_equal':True})
    ledger=lines(work/'LEDGER.jsonl'); previous='0'*64
    for n,r in enumerate(ledger):
        d=dict(r); h=d.pop('hash'); assert r['sequence']==n and r['previous_hash']==previous and hashlib.sha256(serial(d)).hexdigest()==h; previous=h
    sealed=[r for r in ledger if r['event']=='PREDICTION_SEALED']; remote=[r for r in ledger if r['event']=='REMOTE_READBACK_PASS']; starts=[r for r in ledger if r['event']=='NATIVE_FORMAL_START']; assert len(sealed)==len(remote)==1 and len(starts)==258
    assert sealed[0]['sequence']<remote[0]['sequence']<min(r['sequence'] for r in starts)
    seal=read(work/'PREDICTION_SEAL.json'); assert sha(work/'PREDICTION_SEAL.json')==sealed[0]['seal_sha256'] and seal['freeze_sha256']==sha(doc/'FREEZE.json') and len(seal['predictions'])==258
    for key,r in seal['predictions'].items():
        rec=records[key]; assert sha(root/r['result'])==r['sha256'] and r['ids']==rec['ids'] and r['endpoint']==rec['endpoint']
    assert {r['unit_id'] for r in ledger if r['event']=='UNIT_VALID' and r.get('condition') in ('R','H0','H1') and r['sequence']<sealed[0]['sequence']}=={q['id'] for q in queue if q['condition'] in ('R','H0','H1')}
    graph={k:{f:sorted(v) if isinstance(v,set) else v for f,v in g.items()} for k,g in graph.items()}
    assert graph['H1/target/continuation']['occupied_tokens']==graph['N1/target/continuation']['occupied_tokens']==[1]
    summary={'status':'QUALIFIED_PASS','source_sha':SOURCE,'valid_units':645,'failed_formal_attempts':sum(a['failure'] is not None for a in attempts),'formal_attempts':len(attempts),'selected_attempts':len(selected_attempts),'groups':groups,'g0_arrays':120,'g0_native_rerun_explicit24':rerun,'g0_reused_unchanged_H':reused,'sham_pairs':len(sham),'historical_array_comparisons':171,'native_threads':{str(k):v for k,v in native_threads.items()},'persistent_deviation_output_changes':{r['task']:{'native_output_noop':r['native_output_noop'],'detail':r['comparisons']['N0/N1']} for r in tasks if r['transition']=='mismatch_to_mismatch'},'seal':{'mode':'REMOTE_BEFORE_NATIVE','sequence':sealed[0]['sequence'],'readback_sequence':remote[0]['sequence'],'first_native_sequence':min(r['sequence'] for r in starts),'predictions':258,'ledger_sha256':sha(work/'LEDGER.jsonl'),'scope':'content and local ledger ordering, not independent absolute process time'},'omitted_frozen_files':unavailable,'graph_summary':graph,'performance_claim':False}
    write(out/'RECOMPUTATION.json',summary); write(out/'TASK_TRANSITIONS.json',tasks); write(out/'SELECTED_ATTEMPTS.json',selected_attempts); write(out/'ATTEMPTS.json',attempts); write(out/'TRANSFER_WITNESSES.json',witnesses); write(out/'SHAM_WITNESSES.json',sham); write(out/'SOURCE_BINDINGS.json',binding)
    write(out/'RAW_OUTPUT_ARRAYS.json',[{'task':t,'condition':c,'rep':r,**x} for (t,c,r),x in raw.items()])
    with (out/'TASK_TRANSITIONS.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['task','cohort','H0/N0','H1/N1','N0/R','N1/R','N0/N1','transition','native_output_noop'])
        for r in tasks: w.writerow([r['task'],r['cohort']]+[sum(x['equal'] for x in r['comparisons'][a+'/'+b]) for a,b in comparisons]+[r['transition'],r['native_output_noop']])
    # Downloadable raw witness subset: retain all formal/G0 log captures and ledgers,
    # source and documentation. Large KV witnesses remain audited remotely, with
    # independent hashes in TRANSFER_WITNESSES and RESTORED_FILES.
    with tarfile.open(out/'RAW_WITNESSES.tar.gz','w:gz') as tar:
        for p in root.rglob('*'):
            if not p.is_file() or '_audit_cas' in p.parts: continue
            rel=p.relative_to(root); name=str(rel)
            if name.startswith(('benchmarks/rtx_target_verification_intervention_v1/','scripts/platform/rtx_target_verification_intervention_v1/')) or (name.startswith('work/rtx-target-v1/') and (p.suffix in ('.json','.jsonl','.log','.txt','.md') or '/inputs/' in name)):
                tar.add(p,arcname=name,recursive=False)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['restore','audit']); p.add_argument('--root',type=pathlib.Path,required=True); p.add_argument('--output',type=pathlib.Path,required=True); p.add_argument('--dest',type=pathlib.Path); a=p.parse_args()
    if a.mode=='restore': restore(a.root,a.dest,a.output)
    else: audit(a.root,a.output)
