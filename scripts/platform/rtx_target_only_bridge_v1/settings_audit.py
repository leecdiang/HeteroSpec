"""Additive offline audit of raw settings and semantic event boundaries, no controller import."""
import argparse, hashlib, json, pathlib, re
def unique_object(pairs):
    result={}
    for k,v in pairs:
        assert k not in result,'duplicate JSON object key: '+k
        result[k]=v
    return result
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def audit(root):
    doc=root/'benchmarks/rtx_target_only_bridge_v1';out=root/'work/rtx-target-only-bridge-v1'
    protocol=load(doc/'PROTOCOL.json');cohort=load(doc/'COHORT.json');contract=load(doc/'INPUT_CONTRACT.json')
    exact=['HumanEval/'+str(i) for i in [143,31,25,81,15,141,142,18,136,99,148,140,87,76,26,49,40,109,66]]
    assert protocol['tasks']==cohort['tasks']==list(contract['inputs'])==exact
    assert protocol['planned']==cohort['planned']==171 and protocol['repetitions']==3
    assert protocol['conditions']==cohort['conditions']==['N0','N1','U2']
    assert protocol['source']=='16aeada781c475c9641e09c90e93fb0a0e136c34'
    assert contract['cap']==128 and contract['context']==4096 and set(contract['EOG'])=={128247,151643,151645,151662,151663,151664}
    orders=[['N0','N1','U2'],['N1','U2','N0'],['U2','N0','N1']]
    expected=[{'task':t,'condition':c,'rep':r,'key':f'{t}/{c}/{r}'} for r in [1,2,3] for t in exact for c in orders[r-1]]
    assert protocol['queue']==expected
    selected=load(out/'SELECTED_ATTEMPTS.json');ledger=[json.loads(l) for l in (out/'ATTEMPT_LEDGER.jsonl').read_text(encoding='utf-8').splitlines()]
    starts=[r['key'] for r in ledger if r['event']=='ATTEMPT_START' and r['namespace']=='formal' and r['attempt'].startswith('attempt-01-')]
    assert starts==[q['key'] for q in expected]
    rows=[];handovers=0
    for key,b in selected.items():
        path=root/b['record'];rec=load(path);d=path.parent/b['attempt'];c=rec['condition'];s=(d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1')
        f16=re.findall(r'llama_kv_cache: size =[^\n]*K \(([^)]+)\):[^\n]*V \(([^)]+)\):',s)
        assert f16==[('f16','f16')]*(1 if c=='U2' else 3),(key,f16)
        assert re.search(r"n_slots = 1, n_ctx_slot = 4096, kv_unified = 'false'",s)
        assert re.search(r'top_k = 0, top_p = 1\.000, min_p = 0\.000',s) and re.search(r'temp = 0\.000',s)
        argv=rec['argv'];assert argv[argv.index('--seed')+1]=='123' and '--no-warmup' in argv and argv[argv.index('--cache-ram')+1]=='0'
        start=load(d/'START.json');assert start['bindings']==rec['bindings'] and start['condition']==c
        if c in ['N0','N1']:
            assert argv[argv.index('--spec-draft-threads')+1]==argv[argv.index('--spec-draft-threads-batch')+1]=='24'
            assert argv[argv.index('--spec-draft-n-max')+1]=='2' and argv[argv.index('--spec-draft-n-min')+1]=='0'
            events=[json.loads(l) for l in (d/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
            pending=next(e for e in events if e['event']=='first_pending');move=next(e for e in events if e['event']=='transfer')
            target_samples=[e for e in events if e['event']=='sample' and e['role']=='target'];assert target_samples[0]['sequence']<pending['sequence']<move['sequence']<target_samples[1]['sequence']
            assert target_samples[0]['phase']=='prefill' and all(e['phase']=='continuation' for e in target_samples[1:])
            assert move['before']['max']==len(load(root/contract['inputs'][rec['task']]['ids']))-1
            assert move['pending_boundary']=='sample and accept exactly once in source; carry pending ID; no destination resample'
            handovers+=1
        rows.append({'key':key,'raw_f16_contexts':len(f16),'kv_unified':False,'greedy_target':True,'warmup':False,'fresh_cache':True})
    receipt={'status':'PASS','formal':sum(k.startswith('formal/') for k in selected),'engineering':sum(k.startswith('engineering/') for k in selected),'handoffs_checked':handovers,'raw_settings_records':len(rows),'queue_and_cohort_exact':True,'rows':rows,'scope':'raw KV type/config and source-bound handoff sequencing; no serialized opaque sampler or independently authenticated machine clock'}
    (doc/'SETTINGS_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='rows'}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);a=p.parse_args();audit(a.root.resolve())
