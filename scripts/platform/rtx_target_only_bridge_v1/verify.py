"""CPU-only source-bound verifier. Imports neither runner nor its comparison/capture helpers."""
import argparse, collections, csv, hashlib, json, pathlib, re
from datetime import datetime, timezone
EOG={128247,151643,151645,151662,151663,151664}
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()

def endpoint(ids,stops):
    assert ids and len(ids)<=128 and all(type(i)==int and 0<=i<151936 for i in ids)
    assert not any(i in EOG for i in ids[:-1])
    eos=ids[-1] in EOG;assert eos or len(ids)==128
    expected=(['limit','EOS'] if eos else ['limit']) if len(ids)==128 else ['EOS']
    assert stops==expected,'endpoint marker mismatch'
    return 'EOS' if eos else 'limit'

def raw_native(path):
    s=path.read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
    rows=re.findall(r'^\d+\.\d{2}\.\d{3}\.\d{3} D slot process_toke: id\s+(\d+) \| task (\d+) \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(-?\d+) ',s,re.M)
    assert rows and {r[0] for r in rows}=={'0'} and len({r[1] for r in rows})==1
    assert [int(r[2]) for r in rows]==list(range(1,len(rows)+1))
    assert all(int(r[3])==128-int(r[2]) for r in rows)
    ids=[int(r[4]) for r in rows]
    stops=re.findall(r'slot process_toke: id\s+0 \| task \d+ \| stopped by (EOS|limit)',s)
    assert re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',s)==[str(len(ids))]
    ep=endpoint(ids,stops)
    m=re.search(r'new prompt,.*task.n_tokens = (\d+)',s);assert m
    n=int(m.group(1));tail=s[m.end():];stop=tail.find('slot process_toke:');assert stop>=0
    seen={}
    for match in re.finditer(r'ubatch_print:\s+\d+: id =\s+(\d+) \([\s\S]*?\), pos =\s+(\d+), n_seq_id =\s+(\d+), seq_id = \[([^\]]*)\], output = (\d+)',tail[:stop]):
        token,pos,ns,seq,mask=match.groups();pos=int(pos);assert ns=='1' and seq=='0'
        if pos<n:assert pos not in seen or seen[pos]==int(token);seen[pos]=int(token)
    assert set(seen)==set(range(n)),'truncated prompt capture'
    pieces=[]
    # Verify complete byte-piece fields independently; raw text itself is not an array.
    matches=list(re.finditer(r'^\d+\.\d{2}\.\d{3}\.\d{3} D slot process_toke: id\s+\d+ \| task \d+ \| n_gen = \d+, n_remaining = -?\d+, next token:\s+-?\d+ ',s,re.M))
    for match in matches:
        piece=re.match(r"'(.*?)'\n(?=\d+\.\d{2}\.\d{3}\.\d{3} [A-Z] |\Z)",s[match.end():],re.S);assert piece,'truncated token piece'
        pieces.append(piece.group(1).encode('latin-1'))
    return {'ids':ids,'endpoint':ep,'stop_markers':stops,'prompt_ids':[seen[i] for i in range(n)],'pieces_hex':b''.join(pieces).hex(),
            'threads':[list(map(int,x)) for x in re.findall(r'system_info: n_threads = (\d+) \(n_threads_batch = (\d+)\)',s)],
            'threadpools':list(map(int,re.findall(r'llama threadpool init, n_threads = (\d+)',s))),
            'offload':[list(x) for x in re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',s)],
            'devices':re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',s),
            'ubatches':list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',s))),
            'contexts':list(map(int,re.findall(r'llama_context: n_ctx\s*=\s*(\d+)',s))),
            'batches':list(map(int,re.findall(r'llama_context: n_batch\s*=\s*(\d+)',s))),
            'flash':re.findall(r'llama_context: flash_attn\s*=\s*(\w+)',s),
            'cached':re.findall(r'cached n_tokens = (\d+), memory_seq_rm \[0, end\)',s),
            'draft_loads':re.findall(r"loading draft model '([^']+)'",s),'speculative_init':re.findall(r'adding speculative implementation ([^\n]+)',s)}

def difference(x,y):
    a,b=x['ids'],y['ids'];first=next((i for i,(u,v) in enumerate(zip(a,b)) if u!=v),None)
    if first is None and len(a)!=len(b):first=min(len(a),len(b))
    ae=a==b;ee=x['endpoint']==y['endpoint'];count=sum(u!=v for u,v in zip(a,b))+abs(len(a)-len(b))
    return {'array_equal':ae,'endpoint_equal':ee,'joint_equal':ae and ee,'left_length':len(a),'right_length':len(b),'left_endpoint':x['endpoint'],'right_endpoint':y['endpoint'],'first_divergence':first,'left_id':a[first] if first is not None and first<len(a) else None,'right_id':b[first] if first is not None and first<len(b) else None,'position_difference_count':count,'position_difference_fraction':count/max(len(a),len(b))}

def validate_keys(keys,expected):
    assert len(keys)==len(set(keys)),'duplicate matrix keys'
    assert set(keys)==set(expected),'missing or extra matrix keys'

def validate_attempt_files(files,attempt):
    assert {pathlib.PurePosixPath(p).parts[0] for p in files}=={attempt},'mixed attempts'

def trace_check(d,c,x,assets):
    events=[json.loads(line) for line in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [e['sequence'] for e in events]==list(range(len(events)))
    transfers=[e for e in events if e['event']=='transfer'];pending=[e for e in events if e['event']=='first_pending'];assert len(transfers)==len(pending)==1
    t=transfers[0];assert t['source_ub']==2 and t['destination_ub']==(1 if c=='N1' else 2)
    assert t['state_equal'] and t['source_unchanged'] and t['state_bytes']==t['consumed_bytes']
    assert t['before']==t['after']==t['source_after'] and t['pending_id']==pending[0]['pending_id']==x['ids'][0]
    hashes=[sha(d/('trace.jsonl'+suffix)) for suffix in ['.source_before.kv','.destination.kv','.source_after.kv']];assert len(set(hashes))==1
    assert (d/'trace.jsonl.source_before.kv').stat().st_size==t['state_bytes'] and (d/'trace.jsonl.pending_logits.f32').stat().st_size==151936*4
    assert t['sampler_chain']==t['clone_chain'] and t['history']==t['clone_history'] and t['seed']==t['clone_seed']==123
    for module in pending[0]['modules']:
        name=pathlib.PureWindowsPath(module).name
        if name.endswith('.dll') and name.startswith(('ggml','cublas','cudart','libomp')):
            expected=assets.get('qualified_native/'+name);assert expected is not None
            assert pathlib.PureWindowsPath(module)==pathlib.PureWindowsPath(expected['path'])
    graphs={};raw_target=[];decisions=[]
    for e in events:
        if e['event']=='decode':
            assert e['caller_batch']==len(e['tokens'])==len(e['positions'])==len(e['sequence_ids'])==len(e['logits_mask']) and e['returncode']==0
            assert all(v==[0] for v in e['sequence_ids'])
            assert e['ub_capacity']==(2 if e['role']=='draft' or e['phase']=='prefill' else 1 if c=='N1' else 2)
            key=e['role']+'/'+e['phase'];summary=graphs.setdefault(key,{'caller_lengths':set(),'occupied_tokens':set(),'output_counts':set()})
            summary['caller_lengths'].add(e['caller_batch']);summary['occupied_tokens'].update(g['ne'][1] for g in e['graphs'] if g['name']=='attn_norm-0');summary['output_counts'].update(g['ne'][1] for g in e['graphs'] if g['name']=='result_output')
        if e['event']=='sample' and e['role']=='target':raw_target.append(e['selected_id'])
        if e['event']=='verify_decision':decisions.append(e['sampled_ids'])
    assert raw_target[:len(x['ids'])]==x['ids']
    return {'transfer':t,'state_sha256':hashes[0],'graphs':{k:{f:sorted(v) for f,v in row.items()} for k,row in graphs.items()},'raw_target_sample_ids':raw_target,'post_endpoint_sample_tail':raw_target[len(x['ids']):],'raw_verify_decisions':decisions}

def historical(root,doc,contract):
    binding=load(doc/'HISTORICAL_BINDINGS.json');raw={}
    for name,b in binding['files'].items():
        p=doc/'historical_raw'/name;assert sha(p)==b['sha256'] and p.stat().st_size==b['bytes']
    neutral=load(root/'paper/mlsys2027/reviews/reconstruction_v010/rtx/FORMAL_ARRAYS_NEUTRAL.json')
    nc={(r['task'],r['condition'],r['rep']):r for r in neutral['records']}
    for key,b in binding['records'].items():
        x=raw_native(doc/'historical_raw'/b['native_log']);rec=load(doc/'historical_raw'/b['result'])
        assert x['ids']==b['ids']==rec['ids'] and x['endpoint']==b['endpoint']==rec['endpoint']
        t,c,r=rec['task'],rec['condition'],rec['rep'];assert x['ids']==nc[t,c,r]['ids'] and x['endpoint']==nc[t,c,r]['endpoint']
        assert x['prompt_ids']==load(root/contract['inputs'][t]['ids'])
        raw[key]=x
    pred=load(root/'benchmarks/rtx_trajectory_cost_v4/A_trajectory/RESERVED_PREDICTIONS.json');lead=[];old={}
    for row in pred['rows']:
        t,r=row['task_id'],row['repetition'];assert row['input_sha256']==contract['inputs'][t]['prompt_sha256']
        for cond,name in [('U2','A_TARGET_ONLY_UB2'),('reference','A_REFERENCE_UB1')]:
            value=row['conditions'][name];ids=value['generated_ids'];ep=value['termination'];assert endpoint(ids,value.get('native_stop_observations') or ((['limit','EOS'] if ids[-1] in EOG else ['limit']) if len(ids)==128 else ['EOS']))==ep
            old[f'{t}/{cond}/{r}']={'ids':ids,'endpoint':ep}
        u=old[f'{t}/U2/{r}'];lead.append({'task':t,'rep':r,'U2_N0':difference(u,raw[f'{t}/N0/{r}']),'U2_N1':difference(u,raw[f'{t}/N1/{r}'])})
    assert len(lead)==57
    return raw,old,{'pairs':57,'U2_N0':sum(v['U2_N0']['joint_equal'] for v in lead),'U2_N1':sum(v['U2_N1']['joint_equal'] for v in lead),'rows':lead,'scope':'old U2 arrays from pinned source-bound RESERVED_PREDICTIONS; old N0/N1 reparsed from restored CAS raw logs; not a fresh rerun'}

def audit(root,namespace,output):
    doc=root/'benchmarks/rtx_target_only_bridge_v1';out=root/'work/rtx-target-only-bridge-v1';protocol=load(doc/'PROTOCOL.json');contract=load(doc/'INPUT_CONTRACT.json');assets=load(doc/'ASSET_ENVIRONMENT.json')['assets']
    for t,b in contract['inputs'].items():
        assert sha(root/b['prompt'])==b['prompt_sha256'] and sha(root/b['ids'])==b['ids_sha256']
    for name,h in load(doc/'SOURCE_BINDINGS.json')['files'].items():assert sha(root/name)==h
    selected=load(out/'SELECTED_ATTEMPTS.json');subset={k:v for k,v in selected.items() if k.startswith(namespace+'/')}
    if namespace=='engineering':expected=[f'{t}/{c}/1' for t in protocol['engineering_tasks'] for c in protocol['conditions']]
    elif namespace=='formal':expected=[q['key'] for q in protocol['queue']]
    else:expected=[f'{t}/{c}/1' for t in load(doc/'DIAGNOSTIC_SELECTION.json')['tasks'] for c in protocol['conditions']]
    validate_keys([k.removeprefix(namespace+'/') for k in subset],expected)
    if namespace!='engineering':
        freeze=load(doc/'FREEZE_RECEIPT.json')
        for p,h in freeze['files'].items():assert sha(root/p)==h,p
    raw={};records=[];witnesses={};checked=0
    for key,item in subset.items():
        path=root/item['record'];assert sha(path)==item['sha256'];rec=load(path);base=path.parent;d=base/item['attempt']
        assert rec['key']==key.removeprefix(namespace+'/') and rec['namespace']==namespace and rec['attempt']==item['attempt']
        assert rec['exit_code']==0 and rec['process_status']=='exit0' and rec['source_commit']==protocol['source']
        validate_attempt_files(rec['files'],item['attempt'])
        for p,b in rec['files'].items():assert sha(base/p)==b['sha256'] and (base/p).stat().st_size==b['bytes'];checked+=1
        assert set(rec['files'])=={p.relative_to(base).as_posix() for p in d.rglob('*') if p.is_file()}
        for name,h in rec['bindings'].items():assert sha(doc/name)==h
        assert set(rec['bindings'])==({'PROTOCOL.json','INPUT_CONTRACT.json','COHORT.json','ASSET_ENVIRONMENT.json'}|({'FREEZE_RECEIPT.json'} if namespace=='formal' else set()))
        start=load(d/'START.json');proc=load(d/'PROCESS.json');assert start['argv']==rec['argv']==proc['argv']
        for previous in sorted(base.glob('attempt-*')):
            if previous.name<d.name:assert (previous/'FAILURE.json').exists() or not (previous/'transcript.txt').exists(),'earlier complete attempt was skipped'
        t,c=rec['task'],rec['condition'];b=contract['inputs'][t]
        assert start['prompt_sha256']==sha(root/b['prompt']) and start['input_ids_sha256']==sha(root/b['ids'])
        mapping={'{prompt}':str(root/b['prompt']),'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
        # Paths in restored evidence refer to original execution root; check all
        # relative suffixes and exact non-path args rather than rewriting old argv.
        template=protocol['command_templates'][c];assert len(template)==len(rec['argv'])
        for intended,observed in zip(template,rec['argv']):
            if intended in mapping:
                suffix=(pathlib.Path(mapping[intended]).relative_to(root)).as_posix();assert pathlib.PureWindowsPath(observed).as_posix().endswith(suffix)
            else:assert intended==observed
        env=rec['environment_overrides'];assert env['LLAMA_BATCH_DEBUG']=='1'
        x=raw_native(d/'native.log');assert x['ids']==rec['ids']==rec['raw_committed_ids'] and x['endpoint']==rec['endpoint']
        assert x['prompt_ids']==load(root/b['ids']) and x['threads']==[[24,24]]
        assert x['threadpools'] and all(v==24 for v in x['threadpools'])
        assert x['offload']==([['37','37']] if c=='U2' else [['37','37'],['29','29']])
        assert len(x['devices'])==len(x['offload']) and all(s.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for s in x['devices'])
        assert x['ubatches']==([2] if c=='U2' else [2,2,1 if c=='N1' else 2])
        assert x['contexts']==[4096]*(1 if c=='U2' else 3) and x['batches']==[2048]*(1 if c=='U2' else 3)
        assert x['flash']==['disabled']*(1 if c=='U2' else 3) and x['cached']==['0']
        prompt=(root/b['prompt']).read_bytes();prompt=prompt[:-1] if prompt.endswith(b'\n') else prompt
        pieces=bytes.fromhex(x['pieces_hex']);transcript=b'User:\n'+prompt+b'\n\nAssistant:\n'+pieces+(b'' if pieces.endswith(b'\n') else b'\n')+b'\n'
        assert (d/'transcript.txt').read_bytes().replace(b'\r\n',b'\n')==transcript
        if c=='U2':
            assert not any('draft' in arg or 'spec-type' in arg for arg in rec['argv'])
            assert set(env)=={'LLAMA_BATCH_DEBUG'} and not x['draft_loads'] and not x['speculative_init'] and not (d/'trace.jsonl').exists()
            witnesses[key]={'no_draft_argv':True,'one_loaded_model':True,'no_draft_load_or_speculative_init':True,'one_target_context':True,'internal_state':'unobserved on released U2'}
        else:
            assert env['HS_TARGET_CONTINUATION_UB']==('1' if c=='N1' else '2') and set(env)=={'LLAMA_BATCH_DEBUG','HS_NATIVE_CAPTURE','HS_TARGET_CONTINUATION_UB'}
            witnesses[key]=trace_check(d,c,x,assets)
        raw[rec['key']]=x;records.append({'task':t,'condition':c,'rep':rec['rep'],'ids':x['ids'],'endpoint':x['endpoint'],'stop_markers':x['stop_markers'],'raw_committed_overshoot':0,'selected_attempt':item})
    rows=[json.loads(l) for l in (out/'ATTEMPT_LEDGER.jsonl').read_text(encoding='utf-8').splitlines()];previous='0'*64
    for i,row in enumerate(rows):
        content=dict(row);h=content.pop('hash');assert row['sequence']==i and row['previous_hash']==previous and hashlib.sha256(canon(content)).hexdigest()==h;previous=h
    for key,item in subset.items():
        ns,k=key.split('/',1);events=[v for v in rows if v['event']=='ATTEMPT_VALID' and v['namespace']==ns and v['key']==k]
        assert len(events)==1 and events[0]['attempt']==item['attempt'] and events[0]['record_sha256']==item['sha256']
    hist,old,lead=historical(root,doc,contract)
    comparisons=[];summary={};tasks=[]
    if namespace=='formal':
        pairs=[('U2','N1'),('U2','N0'),('N0','N1')]
        for a,b in pairs:
            name=a+'/'+b;detail=[{'task':t,'rep':r,**difference(raw[f'{t}/{a}/{r}'],raw[f'{t}/{b}/{r}'])} for t in protocol['tasks'] for r in [1,2,3]]
            summary[name]={f:sum(d[f] for d in detail) for f in ['array_equal','endpoint_equal','joint_equal']};summary[name].update(run_pairs=57,all_three_equal_tasks=sum(all(v['joint_equal'] for v in detail if v['task']==t) for t in protocol['tasks']),task_units=19)
            comparisons.extend({'pair':name,**d} for d in detail)
        stability={c:sum(all(raw[f'{t}/{c}/1']['ids']==raw[f'{t}/{c}/{r}']['ids'] and raw[f'{t}/{c}/1']['endpoint']==raw[f'{t}/{c}/{r}']['endpoint'] for r in [2,3]) for t in protocol['tasks']) for c in protocol['conditions']}
        bridges={}
        for c in protocol['conditions']:
            details=[{'task':t,'rep':r,**difference(raw[f'{t}/{c}/{r}'],(old if c=='U2' else hist)[f'{t}/{c}/{r}'])} for t in protocol['tasks'] for r in [1,2,3]]
            bridges[c]={'joint_equal':sum(d['joint_equal'] for d in details),'pairs':57,'rows':details,'caveat':'U2 threads12 vs fresh24 observational bridge' if c=='U2' else 'same explicit24 native/frontend; environment identities locally checked'}
        reference={c:sum(difference(raw[f'{t}/{c}/{r}'],old[f'{t}/reference/{r}'])['joint_equal'] for t in protocol['tasks'] for r in [1,2,3]) for c in protocol['conditions']}
        for t in protocol['tasks']:
            taskrows=[d for d in comparisons if d['task']==t]
            tasks.append({'task':t,**{p:sum(d['joint_equal'] for d in taskrows if d['pair']==p) for p in summary},'N0_N1_changed':any(not d['joint_equal'] for d in taskrows if d['pair']=='N0/N1'),'stable':{c:all(difference(raw[f'{t}/{c}/1'],raw[f'{t}/{c}/{r}'])['joint_equal'] for r in [2,3]) for c in protocol['conditions']}})
        label='INCONCLUSIVE' if any(n<19 for n in stability.values()) else 'REFUTED_OR_BOUNDARY_FOUND' if summary['U2/N1']['joint_equal']<57 else 'SUPPORTED_ON_EXPOSED_COHORT'
        result={'status':'PASS','outcome':label,'formal':len(raw),'planned':171,'comparisons':summary,'stability':stability,'historical_bridges':bridges,'historical_reference_matches':reference,'task_table':tasks}
    else: result={'status':'PASS','namespace':namespace,'runs':len(raw),'qualification':'capture/config/input/handoff checks; no inter-condition equality gate','historical_native_smoke_matches':{c:sum(difference(x,hist[k])['joint_equal'] for k,x in raw.items() if k.split('/')[2]==c) for c in ['N0','N1']}}
    result.update(checked_file_hashes=checked,failed_attempts=sum(v['event']=='ATTEMPT_FAILED' and v['namespace']==namespace for v in rows),lead={'U2_N0':lead['U2_N0'],'U2_N1':lead['U2_N1'],'pairs':57},scope='raw/output integrity and recorded settings; no independent authentication of omitted assets or absolute machine clock')
    write(output/'SUMMARY.json',result);write(output/'ARRAYS.json',{'namespace':namespace,'records':records});write(output/'WITNESSES.json',witnesses);write(output/'COMPARISONS.json',comparisons);write(output/'RETROSPECTIVE_LEAD.json',lead)
    if namespace=='formal':
        with (output/'TASK_COMPARISONS.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['task','U2/N1','U2/N0','N0/N1','N0_N1_changed','N0_stable','N1_stable','U2_stable']);w.writeheader()
            for r in tasks:w.writerow({**{k:v for k,v in r.items() if k!='stable'},**{c+'_stable':v for c,v in r['stable'].items()}})
    print(json.dumps({k:v for k,v in result.items() if k not in ['task_table','historical_bridges']}),flush=True)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);p.add_argument('--namespace',choices=['engineering','formal','diagnostic'],default='formal');p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();audit(a.root.resolve(),a.namespace,a.output)
