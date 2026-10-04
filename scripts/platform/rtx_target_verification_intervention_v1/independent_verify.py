"""Independent raw parser and complete-cohort audit; imports no study helpers."""
import argparse, collections, csv, hashlib, json, pathlib, re
from datetime import datetime, timezone

def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canon(o):return json.dumps(o,separators=(',',':'),ensure_ascii=True).encode()
EOG={128247,151643,151645,151662,151663,151664}

def endpoint(ids,stops=None):
    assert ids and len(ids)<=128 and all(type(i)==int and 0<=i<151936 for i in ids)
    assert not any(i in EOG for i in ids[:-1])
    terminal=ids[-1] in EOG;assert terminal or len(ids)==128
    expected=(['limit','EOS'] if terminal else ['limit']) if len(ids)==128 else ['EOS']
    if stops is not None:assert stops==expected
    return {'ids':ids,'endpoint':'EOS' if terminal else 'limit'}

def parse_native(p):
    s=p.read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
    rows=re.findall(r'^\d+\.\d{2}\.\d{3}\.\d{3} D slot process_toke: id\s+(\d+) \| task (\d+) \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(-?\d+) ',s,re.M)
    assert rows and {r[0] for r in rows}=={'0'} and len({r[1] for r in rows})==1
    assert [int(r[2]) for r in rows]==list(range(1,len(rows)+1))
    assert all(int(r[3])==128-int(r[2]) for r in rows)
    ids=[int(r[4]) for r in rows]
    stops=re.findall(r'slot process_toke: id\s+0 \| task \d+ \| stopped by (EOS|limit)',s)
    count=re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',s)
    assert count==[str(len(ids))]
    result=endpoint(ids,stops)
    result['offload']=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',s)
    result['devices']=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',s)
    result['ubatches']=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',s)))
    assert all(d.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for d in result['devices'])
    result['stop_markers']=stops
    result['thread_counts']=[tuple(map(int,x)) for x in re.findall(r'system_info: n_threads = (\d+) \(n_threads_batch = (\d+)\)',s)]
    # Actual prefill IDs appear in the native caller dump; ignore decoded pieces.
    count_match=re.search(r'new prompt,.*task.n_tokens = (\d+)',s);assert count_match
    count=int(count_match.group(1));tail=s[count_match.end():];end=tail.find('slot process_toke:');assert end>=0
    pattern=re.compile(r'ubatch_print:\s+\d+: id =\s+(\d+) \([\s\S]*?\), pos =\s+(\d+), n_seq_id =\s+(\d+), seq_id = \[([^\]]*)\], output = (\d+)')
    seen={}
    for match in pattern.finditer(tail[:end]):
        token,pos,ns,seq,mask=match.groups();pos=int(pos);assert ns=='1' and seq=='0'
        if pos<count:assert pos not in seen or seen[pos]==int(token);seen[pos]=int(token)
    assert set(seen)==set(range(count)),('incomplete native prompt capture',p,len(seen),count)
    result['prompt_ids']=[seen[i] for i in range(count)]
    return result

def parse_h(d):
    events=[json.loads(s) for s in (d/'R-wire.jsonl').read_text(encoding='utf-8').splitlines()]
    rows=[r for r in events if r['event'] in ['init','verify']]
    assert rows and rows[0]['event']=='init'
    prompt=rows[0]['response']['prompt_ids'];ids=[];pos=len(prompt);raw_samples=[]
    for index,row in enumerate(rows):
        x=row['response'];committed=x['committed_ids'];samples=x['samples']
        if index:
            q=row['request'];assert q['round']==index-1 and q['position']==pos and q['pending']==ids[-1]
            assert len(q['proposal_ids'])<=2 and len(x['decode']['tokens'])==len(q['proposal_ids'])+1
            assert x['decode']['tokens']==[ids[-1]]+q['proposal_ids'] and x['decode']['logits_mask']==[1]*len(x['decode']['tokens'])
            assert [r['selected_id'] for r in samples]==x['sampled_ids']
            pos=x['next_position']
        assert [r['selected_id'] for r in samples[:len(committed)]]==committed
        raw_samples.extend(r['selected_id'] for r in samples);ids.extend(committed)
        assert x['terminal']==(ids[-1] in EOG or len(ids)==128)
    result=endpoint(ids);result['prompt_ids']=prompt;result['transfer']=rows[0]['response'].get('transfer');result['raw_sample_count']=len(raw_samples)
    # Check proposals originated in P and tape persisted the exact request.
    pe=[json.loads(s) for s in (d/'P-wire.jsonl').read_text(encoding='utf-8').splitlines()]
    pi=[r for r in pe if r['event']=='init'];assert len(pi)==1 and pi[0]['response']['prompt_ids']==prompt
    proposals=[r for r in pe if r['event']=='propose'];updates=[r for r in pe if r['event']=='update']
    tape=[json.loads(s) for s in (d/'tape.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(proposals)==len(updates)==len(tape)==len(rows)-1
    previous='0'*64;prefix=rows[0]['response']['committed_ids'].copy()
    for i,(p,u,tr,v) in enumerate(zip(proposals,updates,tape,rows[1:])):
        value=dict(tr);h=value.pop('event_hash');assert hashlib.sha256(canon(value)).hexdigest()==h and tr['previous_hash']==previous;previous=h
        assert tr['request']==v['request'] and tr['request']['proposal_ids']==p['response']['proposal_ids']
        assert tr['past_prefix_count']==len(prefix) and tr['past_prefix_sha256']==hashlib.sha256(canon(prefix)).hexdigest()
        assert u['request']['verified_batch']==[prefix[-1]]+p['response']['proposal_ids'] and u['request']['retain_count']==v['response']['retain_count']
        prefix.extend(v['response']['committed_ids'])
    return result

def transfer_check(d,t,expected):
    assert t and t['source_ub']==2 and t['destination_ub']==expected
    assert t['state_equal'] and t['source_unchanged'] and t['state_bytes']==t['consumed_bytes']
    assert t['before']==t['after']==t['source_after'] and t['before']['min']==0
    prefix='R-transfer' if (d/'R-wire.jsonl').exists() else 'trace.jsonl'
    hashes=[sha(d/(prefix+s)) for s in ['.source_before.kv','.destination.kv','.source_after.kv']];assert len(set(hashes))==1
    assert (d/(prefix+'.pending_logits.f32')).stat().st_size==151936*4
    assert (d/(prefix+'.source_before.kv')).stat().st_size==t['state_bytes']
    if 'sampler_chain' in t:
        assert t['sampler_chain']==t['clone_chain'] and t['history']==t['clone_history'] and t['seed']==t['clone_seed']==123

def normalize(d,kind):
    result=[]
    if kind=='H':
        for p in sorted(d.glob('[PR]-wire.jsonl')):
            for line in p.read_text(encoding='utf-8').splitlines():
                x=json.loads(line)
                if x['event'] in ['startup','request_sent','close']:continue
                def clean(o):
                    if isinstance(o,dict):return {k:clean(v) for k,v in o.items() if k not in ['transfer','logits_sha256','logits_bytes']}
                    if isinstance(o,list):return [clean(v) for v in o]
                    return o
                result.append((p.name[0],x['event'],x['request'],clean(x['response'])))
    else:
        for line in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines():
            x=json.loads(line)
            if x['event'] in ['transfer','first_pending']:continue
            x.pop('sequence')
            if x['event']=='sample' and x['role']=='draft':x.pop('selected_id');x.pop('selected_score')
            result.append(x)
    return result

def main():
    args=argparse.ArgumentParser();args.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);args.add_argument('--output',type=pathlib.Path);a=args.parse_args()
    root=a.root;doc=root/'benchmarks/rtx_target_verification_intervention_v1';out=root/'work/rtx-target-v1';report=a.output or out/'independent-recompute';report.mkdir(parents=True,exist_ok=True)
    queue=load(doc/'QUEUE.json');assert len(queue)==645 and len({q['id'] for q in queue})==645
    protocol=load(doc/'PROTOCOL.json');inputs=load(out/'INPUTS.json');expected=load(doc/'HISTORICAL_EXPECTED.json');raw={};records={};checks=0;graph_rows=[]
    freeze=load(doc/'FREEZE.json');omissions=load(doc/'ARCHIVE_OMISSIONS.json') if (doc/'ARCHIVE_OMISSIONS.json').exists() else {'paths':[]};omitted=set(omissions['paths'])
    for name,h in freeze['files'].items():
        if name in omitted and not (root/name).exists():continue
        assert sha(root/name)==h,name;checks+=1
    for q in queue:
        base=out/'formal'/(q['task'].replace('/','-')+'-'+q['condition']+'-r'+str(q['rep']));rec=load(base/'result.json')
        assert rec['valid'] and rec['unit_id']==q['id'];assert rec['freeze_sha256']==sha(doc/'FREEZE.json')
        for name,h in rec['files'].items():assert sha(base/name)==h;checks+=1
        attempts=list(base.glob('attempt-*'));d=base/pathlib.Path(next(iter(rec['files']))).parts[0]
        x=parse_h(d) if q['condition'].startswith('H') else parse_native(d/'native.log')
        assert x['ids']==rec['ids'] and x['endpoint']==rec['endpoint'];checks+=2
        prompt=load(root/inputs[q['task']]['ids'])
        assert x['prompt_ids']==prompt,('prompt mismatch',q['id'],len(x['prompt_ids']),len(prompt))
        if q['condition'].startswith('H'):
            transfer_check(d,x['transfer'],1 if q['condition']=='H1' else 2);assert x['transfer']['pending_id']==x['ids'][0]
            for role in ['P','R']:
                ev=[json.loads(s) for s in (d/(role+'-wire.jsonl')).read_text(encoding='utf-8').splitlines()]
                ready=ev[0]['response'];assert ready['context']['n_ubatch']==2 and ready['context']['threads']==24
                assert ready['context']['flash_attention']=='off'
                for r in ev:
                    req=r['request'];assert not any(k in req for k in ['future_native_ids','reference','prediction_ids','sealed_tape'])
                    response=r['response'];decodes=([response['decode']] if 'decode' in response else [])+response.get('decodes',[])
                    for decode in decodes:
                        phase='prefill' if r['event']=='init' else 'continuation'
                        graph_rows.append({'unit_id':q['id'],'condition':q['condition'],'role':'draft' if role=='P' else 'target','phase':phase,'caller_batch':len(decode['tokens']),'occupied':[v['ne'][1] for v in decode['graphs'] if v['name']=='attn_norm-0'],'logits_outputs':[v['ne'][1] for v in decode['graphs'] if v['name']=='result_output'],'positions_start':decode['positions_start'],'logits_mask':decode['logits_mask']})
        else:
            assert x['thread_counts']==[(24,24)]
            assert x['offload']==([('37','37')] if q['condition']=='R' else [('37','37'),('29','29')])
            assert x['ubatches']==([1] if q['condition']=='R' else [2,2,1 if q['condition']=='N1' else 2])
            command=rec['commands'][0]
            assert not any('tape' in v.lower() or 'prediction' in v.lower() for v in command)
            if q['condition']!='R':
                tr=[json.loads(s) for s in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
                move=[r for r in tr if r['event']=='transfer'];assert len(move)==1;transfer_check(d,move[0],1 if q['condition']=='N1' else 2)
                assert move[0]['pending_id']==x['ids'][0]
                for r in tr:
                    if r['event']=='decode':
                        assert r['caller_batch']==len(r['tokens'])==len(r['positions'])==len(r['sequence_ids'])==len(r['logits_mask'])
                        assert all(s==[0] for s in r['sequence_ids']) and r['returncode']==0
                        assert r['ub_capacity']==(2 if r['role']=='draft' or r['phase']=='prefill' else 1 if q['condition']=='N1' else 2)
                        graph_rows.append({'unit_id':q['id'],'condition':q['condition'],'role':r['role'],'phase':r['phase'],'caller_batch':r['caller_batch'],'occupied':[v['ne'][1] for v in r['graphs'] if v['name']=='attn_norm-0'],'logits_outputs':[v['ne'][1] for v in r['graphs'] if v['name']=='result_output'],'positions':r['positions'],'logits_mask':r['logits_mask'],'ub_capacity':r['ub_capacity']})
        raw[q['id']]=x;records[q['id']]=rec
        if q['task'].startswith('HumanEval/') and q['condition'] in ['R','H0','N0']:
            old=expected[f"{q['task']}/{q['condition']}/{q['rep']}"];assert x['ids']==old['ids'] and x['endpoint']==old['endpoint'];checks+=1
    # Recompute every qualification array and the actual pair witnesses from raw.
    g0=load(doc/'G0.json');assert g0['arrays']==120 and len(g0['records'])==120;grows={}
    for r in g0['records']:
        base=root/r['path'];d=base if (base/'native.log').exists() else next(base.glob('attempt-*'))
        c='R' if r['variant'].startswith('R') else 'H0' if r['variant'].startswith('H') else 'N0'
        x=parse_h(d) if c=='H0' else parse_native(d/'native.log');old=expected[f"{r['task']}/{c}/{r['rep']}"]
        assert x['ids']==old['ids'] and x['endpoint']==old['endpoint'];grows[r['task'],r['rep'],r['variant']]=d;checks+=1
    for task in protocol['g0_tasks']:
        for rep in range(1,4):
            for kind in ['H','N']:assert normalize(grows[task,rep,kind+'_plain'],kind)==normalize(grows[task,rep,kind+'_sham'],kind);checks+=1
    ledger=[json.loads(s) for s in (out/'LEDGER.jsonl').read_text(encoding='utf-8').splitlines()];previous='0'*64
    for i,r in enumerate(ledger):
        value=dict(r);h=value.pop('hash');assert r['sequence']==i and r['previous_hash']==previous and hashlib.sha256(canon(value)).hexdigest()==h;previous=h
    seals=[r for r in ledger if r['event']=='PREDICTION_SEALED'];assert len(seals)==1
    seal=load(out/'PREDICTION_SEAL.json');assert seals[0]['seal_sha256']==sha(out/'PREDICTION_SEAL.json') and seal['freeze_sha256']==sha(doc/'FREEZE.json')
    predkeys={q['id'] for q in queue if q['condition'] in ['H0','H1']};assert set(seal['predictions'])==predkeys and len(predkeys)==258
    for key,r in seal['predictions'].items():assert sha(root/r['result'])==r['sha256'] and r['ids']==raw[key]['ids'] and r['endpoint']==raw[key]['endpoint']
    starts=[r for r in ledger if r['event']=='NATIVE_FORMAL_START'];assert len(starts)==258 and min(r['sequence'] for r in starts)>seals[0]['sequence']
    completed={r['unit_id'] for r in ledger if r['event']=='UNIT_VALID' and r.get('condition') in ['R','H0','H1'] and r['sequence']<seals[0]['sequence']};assert len(completed)==387
    mode=load(out/'SEAL_MODE.json')
    if mode['mode']=='REMOTE_BEFORE_NATIVE':
        remote=[r for r in ledger if r['event']=='REMOTE_READBACK_PASS'];assert len(remote)==1 and remote[0]['sequence']<min(r['sequence'] for r in starts)
    table=[];comparisons=[('H0','N0'),('H1','N1'),('N0','R'),('N1','R')]
    def key(t,c,r):return f"{protocol['study']}/v1/{t}/{c}/{r}"
    def equals(a,b):return a['ids']==b['ids'] and a['endpoint']==b['endpoint']
    for t in protocol['tasks']:
        row={'task':t,'group':'old19' if t.startswith('HumanEval/') else 'new24','comparisons':{}}
        for left,right in comparisons:
            detail=[]
            for rep in range(1,4):
                x,y=raw[key(t,left,rep)],raw[key(t,right,rep)];first=next((i for i,(u,v) in enumerate(zip(x['ids'],y['ids'])) if u!=v),None)
                if first is None and len(x['ids'])!=len(y['ids']):first=min(len(x['ids']),len(y['ids']))
                detail.append({'rep':rep,'equal':equals(x,y),'first_difference':first,'left_id':x['ids'][first] if first is not None and first<len(x['ids']) else None,'right_id':y['ids'][first] if first is not None and first<len(y['ids']) else None,'left_length':len(x['ids']),'right_length':len(y['ids']),'left_endpoint':x['endpoint'],'right_endpoint':y['endpoint']})
            row['comparisons'][left+'/'+right]={'matches':sum(r['equal'] for r in detail),'denominator':3,'detail':detail}
        row['stable']=all(len({json.dumps({'ids':raw[key(t,c,r)]['ids'],'endpoint':raw[key(t,c,r)]['endpoint']},sort_keys=True) for r in range(1,4)})==1 for c in protocol['conditions'])
        old=row['comparisons']['N0/R']['matches'];new=row['comparisons']['N1/R']['matches']
        row['reference_change']='new_regression' if old==3 and new<3 else 'restored' if old<3 and new==3 else 'unchanged_match' if old==new==3 else 'remaining_deviation'
        table.append(row)
    groups={}
    for group in ['old19','new24']:
        rows=[r for r in table if r['group']==group];groups[group]={'tasks':len(rows),'pairs':3*len(rows),'comparisons':{a+'/'+b:sum(r['comparisons'][a+'/'+b]['matches'] for r in rows) for a,b in comparisons},'restored':[r['task'] for r in rows if r['reference_change']=='restored'],'new_regressions':[r['task'] for r in rows if r['reference_change']=='new_regression'],'repeat_stable_tasks':sum(r['stable'] for r in rows)}
    failures=[str(p.relative_to(root)).replace('\\','/') for p in (out/'formal').rglob('FAILURE.json')]
    summary={'status':'VERIFIED_COMPLETE','planned':645,'valid':645,'invalid_units':0,'unexecuted':0,'failed_attempts':len(failures),'failed_attempt_records':failures,'g0_arrays':120,'sham_pairs':30,'historical_comparisons':171,'groups':groups,'known_cases':{t:next(r for r in table if r['task']==t)['reference_change'] for t in ['HumanEval/15','HumanEval/18','HumanEval/25']},'seal_mode':mode['mode'],'task_unit':43,'checks':checks,'timestamp_scope':'local ledger and remote content/order support; no independent absolute timestamp','external_omissions':sorted(omitted),'created_utc':datetime.now(timezone.utc).isoformat()}
    graph_summary={}
    for r in graph_rows:
        label=r['condition']+'/'+r['role']+'/'+r['phase'];entry=graph_summary.setdefault(label,{'caller_lengths':set(),'occupied_counts':set(),'logits_output_counts':set(),'decode_calls':0});entry['caller_lengths'].add(r['caller_batch']);entry['occupied_counts'].update(r['occupied']);entry['logits_output_counts'].update(r['logits_outputs']);entry['decode_calls']+=1
    graph_summary={k:{field:sorted(v) if isinstance(v,set) else v for field,v in values.items()} for k,values in graph_summary.items()}
    for candidate in ['H1','N1']:assert graph_summary[candidate+'/target/continuation']['occupied_counts']==[1]
    summary['graph_summary']=graph_summary
    (report/'GRAPH_OBSERVATIONS.json').write_text(json.dumps({'summary':graph_summary,'rows':graph_rows},indent=2)+'\n',encoding='utf-8')
    (report/'SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (report/'TASK_COMPARISONS.json').write_text(json.dumps(table,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (report/'TASK_COMPARISONS.csv').open('w',encoding='utf-8',newline='') as f:
        cols=['task','group','H0/N0','H1/N1','N0/R','N1/R','stable','reference_change'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in table:w.writerow({**{k:r[k] for k in ['task','group','stable','reference_change']},**{k:v['matches'] for k,v in r['comparisons'].items()}})
    print(json.dumps({'status':'PASS','valid':645,'checks':checks,'groups':groups,'cases':summary['known_cases']}),flush=True)

if __name__=='__main__':main()
