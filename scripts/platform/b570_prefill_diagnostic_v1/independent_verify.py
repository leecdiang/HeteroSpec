"""Independent raw-capture audit; never imports the collector or its endpoint function."""
import json,hashlib,pathlib,csv
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1';DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def digest(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def write(p,x):pathlib.Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    protocol=load(DOC/'PROTOCOL.json');queue=load(OUT/'QUEUE.json');records={};raw={};checks=0
    old=load(OUT/'evaluation/HISTORICAL_EXPECTED.json')
    assert len(queue)==360 and len({q['id'] for q in queue})==360
    for p in sorted((OUT/'formal').glob('*/result.json')):
        r=load(p);assert r['unit_id'] not in records;records[r['unit_id']]=r
        assert r['valid'] and r['exit_code']==0 and r['protocol_sha256']==digest(DOC/'PROTOCOL.json');checks+=3
        for f,h in r['files'].items():assert digest(ROOT/f)==h;checks+=1
        x=load(ROOT/r['capture']);ids=x['ids'];flags=x['eog']
        assert ids and len(ids)==len(flags) and all(type(i)==int and 0<=i<151936 for i in ids) and all(type(f)==bool for f in flags)
        first=next((i for i,f in enumerate(flags) if f),None)
        extent=min(128,first+1 if first is not None else len(ids))
        assert extent==128 or flags[extent-1]
        a={'ids':ids[:extent],'eog':flags[:extent],'endpoint':'EOG' if flags[extent-1] else 'CAP128'}
        assert all(a[k]==r[k] for k in a);checks+=5
        raw[r['unit_id']]=a
        if r['variant'] in ['R','T0','N0']:
            h=old[f'{r["task"]}/{r["variant"]}/{r["rep"]}'];assert all(a[k]==h[k] for k in a);checks+=3
        assert x['prompt_ids']==load(OUT/'inputs'/r['task'].replace('/','_')/'prompt_ids.json');checks+=1
        if r['variant']!='R':
            t=x['transfer'];assert t['consumed_bytes']==t['state_bytes'] and t['before']==t['after']==t['source_after']
            assert t['destination_ub']==1 and t['source_ub']==(128 if r['variant'] in ['T1','N1'] else 1)
            assert t['kv_equal'] and t['source_unchanged'] and t['pending_id']==ids[0]
            cap=ROOT/r['capture'];before=digest(str(cap)+'.before.kv')
            assert before==digest(str(cap)+'.restored.kv')==digest(str(cap)+'.source_after.kv');checks+=5
        for d in x['trace']:
            if d['event']!='decode':continue
            assert d['caller_batch_length']==len(d['input_ids'])==len(d['positions'])==len(d['sequence_ids'])
            assert all(s==[0] for s in d['sequence_ids'])
            if d['role']=='draft':assert d['ub_capacity']==1
            if d['role']=='target' and d['phase']=='prefill':assert d['ub_capacity']==(128 if r['variant'] in ['R','T1','N1'] else 1)
            if d['phase']=='continuation':assert d['ub_capacity']==(128 if r['variant']=='R' else 1)
            checks+=3
    assert set(records)=={q['id'] for q in queue}
    events=[json.loads(s) for s in (OUT/'RUN_LEDGER.jsonl').read_text(encoding='utf-8').splitlines()]
    sidx=[i for i,e in enumerate(events) if e['event']=='T1_SEALED'];assert len(sidx)==1
    seal=load(OUT/'T1_SEAL.json');assert events[sidx[0]]['seal_sha256']==digest(OUT/'T1_SEAL.json') and len(seal['predictions'])==72
    assert seal['protocol_sha256']==digest(DOC/'PROTOCOL.json') and seal['manifest_sha256']==digest(DOC/'ASSET_MANIFEST.json')
    for unit,p in seal['predictions'].items():
        assert digest(ROOT/p['path'])==p['sha256'] and all(p[k]==raw[unit][k] for k in ['ids','eog','endpoint']);checks+=4
    for i,e in enumerate(events):
        if e['event']=='ATTEMPT_START' and e.get('variant')=='N1':assert i>sidx[0]
        if e['event']=='ATTEMPT_END' and e.get('formal') and '/T1/' in e.get('unit_id',''):assert i<sidx[0]
    def key(t,c,r):return f'{protocol["study"]}/v1/{t}/{c}/{r}'
    def equals(a,b):return a['ids']==b['ids'] and a['eog']==b['eog'] and a['endpoint']==b['endpoint']
    table=[];comparisons=[('T0','N0'),('T1','N1'),('N0','R'),('N1','R')]
    for t in protocol['tasks']:
        row={'task':t,'group':'diagnostic' if t in protocol['cases'] else 'control'}
        for a,b in comparisons:
            equal=[equals(raw[key(t,a,r)],raw[key(t,b,r)]) for r in range(1,4)]
            row[a+'_'+b+'_matches']=sum(equal)
            pairs=[]
            for r in range(1,4):
                x,y=raw[key(t,a,r)],raw[key(t,b,r)];d=next((i for i,(u,v) in enumerate(zip(x['ids'],y['ids'])) if u!=v),None)
                if d is None and len(x['ids'])!=len(y['ids']):d=min(len(x['ids']),len(y['ids']))
                pairs.append({'repetition':r,'exact':equals(x,y),'first_difference':d,'left_length':len(x['ids']),'right_length':len(y['ids']),'left_endpoint':x['endpoint'],'right_endpoint':y['endpoint']})
            row[a+'_'+b+'_detail']=pairs
        row['stable']=all(len({json.dumps(raw[key(t,c,r)],sort_keys=True) for r in range(1,4)})==1 for c in protocol['conditions'])
        table.append(row)
    write(DOC/'TASK_COMPARISONS.json',table)
    columns=['task','group']+[a+'_'+b+'_matches' for a,b in comparisons]+['stable']
    with (DOC/'TASK_COMPARISONS.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(table)
    totals={a+'_'+b:sum(r[a+'_'+b+'_matches'] for r in table) for a,b in comparisons}
    restored=[r['task'] for r in table if r['group']=='diagnostic' and r['N1_R_matches']==3]
    controls=[r['task'] for r in table if r['group']=='control' and r['N1_R_matches']!=3]
    if totals['T1_N1']==72:
        knowledge='Simplified predictor transfers to this prefill intervention across preserved native/H1 callers; reference recovery is separately bounded to listed tasks.'
    else:knowledge='Previously observed H1/native equality does not fully transfer to this fixed prefill intervention; no inference about necessity of proposals/history.'
    summary={'status':'MEASUREMENTS_VERIFIED_PENDING_ARCHIVE','planned':360,'valid':360,'failed_units':0,'attempts':sum(e['event']=='ATTEMPT_START' and e.get('formal',False) for e in events),'task_units':24,'repeat_stable_tasks':sum(r['stable'] for r in table),'g0':'PASS','seal':'PASS_LOCAL_ORDER_ONLY','comparisons':totals,'diagnostic_reference_recovery':{'count':len(restored),'denominator':4,'tasks':restored},'controls_reference_regressions':{'count':len(controls),'denominator':20,'tasks':controls},'new_knowledge':knowledge,'limitations':['24 previously exposed tasks; repeats support stability only','H1 and native preserve different caller prefill grouping; UB capacity alone is not execution shape','KV serialized bytes and pending sample checked; opaque sampler bytes unavailable','Graph tensor observation does not identify unique backend kernel or hardware cause','Local order has no independent absolute timestamp certification','Windows OS build changed; fresh G0 and all baseline regression required','No performance, energy, correctness or HumanEval functional-pass-rate conclusion'],'created':datetime.now(timezone.utc).isoformat()}
    write(DOC/'SUMMARY.json',summary)
    receipt={'status':'PASS','checks':checks,'raw_units':360,'collector_imported':False,'source_sha256':digest(pathlib.Path(__file__)),'created':summary['created']};write(DOC/'INDEPENDENT_VERIFICATION.json',receipt)
    report='# B570 prefill diagnostic v1\n\n360/360 formal units independently verified; archival completion pending. G0 passed; 72 T1 predictions sealed before first N1. All 24 tasks previously exposed.\n\n'
    report+=' | Task | Group | T0/N0 | T1/N1 | N0/R | N1/R | Stable |\n |---|---|---:|---:|---:|---:|---|\n'
    for r in table:report+=' | '+r['task']+' | '+r['group']+' | '+' | '.join(str(r[a+'_'+b+'_matches'])+'/3' for a,b in comparisons)+' | '+str(r['stable'])+' |\n'
    report+='\n'+knowledge+'\n\n'+json.dumps(summary,indent=2,ensure_ascii=False)+'\n'
    (DOC/'STUDY_REPORT.md').write_text(report,encoding='utf-8')
    print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
