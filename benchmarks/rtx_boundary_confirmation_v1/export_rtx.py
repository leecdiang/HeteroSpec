"""CPU-only raw-byte audit, compact receipt export and planned missingness."""
import argparse,collections,copy,csv,json,math,statistics,sys
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from collect import audit
from analyze import analyze

def rows_csv(path,rows):
    if not rows:return
    columns=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows([{k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows])

def remap(c,raw,original):
    c=copy.deepcopy(c)
    c['root']=str(raw/'inputs'/c['case_id'])
    for l,row in c['references'].items():
        row['path']=str(Path(c['root'])/'ordinary_reference.bin')
        if row['sha256'] is not None and Path(row['path']).exists():assert sha(row['path'])==row['sha256'],'frozen reference identity drift'
    return c

def export(out,draws=4000):
    raw=root();out=Path(out);out.mkdir(exist_ok=False);plan=load(raw/'plan.json');spec=load(raw/'RUN_SPEC.json');frozen=load(raw/'FREEZE.json');cases=load(raw/'INPUTS.json');refs=load(raw/'REFERENCES.json');observations=[];hosts=[];coverage=[];runtime=spec['numerical_DLLs'];attempts=raw/'attempts'
    for key,name in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json')]:assert sha(raw/name)==frozen[key],name+' freeze mismatch'
    for name,digest in frozen['files'].items():assert sha(raw/'SOURCE'/name)==digest,'consumed source snapshot drift'
    if (raw/'HOLDOUT_INPUTS.json').exists():cases.update(load(raw/'HOLDOUT_INPUTS.json'))
    if (raw/'HOLDOUT_FREEZE.json').exists():
        hf=load(raw/'HOLDOUT_FREEZE.json');assert sha(raw/'HOLDOUT_INPUTS.json')==hf['input_index_sha256'] and sha(raw/'PREDICTION_FREEZE.json')==hf['prediction_sha256'],'holdout freeze drift'
    if (raw/'HOLDOUT_REFERENCES.json').exists():refs.update(load(raw/'HOLDOUT_REFERENCES.json'))
    for cid,row in refs.items():
        if cid not in cases:continue
        for l in ['PQ','QB','QH_C']:cases[cid]['references'][l]=dict(path=row['path'],sha256=row['sha256'])
    reference_parts={}
    for t in plan['tasks']:
        path=attempts/t['task_id'];end=load(path/'ENDED.json') if (path/'ENDED.json').exists() else None
        row=dict(task_id=t['task_id'],stage=t['stage'],case_id=t['case_id'],layout=t['layout'],arm=t['arm'],method=t['method'],block=t['block'],position=t['position'],optional=t['optional'],status=end['status'] if end else 'STARTED_INCOMPLETE' if path.exists() else 'UNSTARTED',actual_calls=end['actual_calls'] if end else None)
        coverage.append(row)
        if not end:continue
        job=load(path/'JOB.json');c=cases[t['case_id']];c=remap(c,raw,None)
        assert sha(Path(c['root'])/'INPUT.json')==c['input_sha256'],'input manifest identity'
        if t['stage']=='reference':
            mainroot=Path(c['root']);m=c['metadata'];query=t['query_index'];import numpy as np
            logical=np.ndarray((c['q'],c['Hq'],c['d']),dtype='<f4',buffer=(mainroot/'Q.bin').read_bytes(),strides=(m['Q']['nb'][1],m['Q']['nb'][2],m['Q']['nb'][0]))
            sub=mainroot/f'serial{query}';assert (sub/'Q.bin').read_bytes()==logical[query].copy().tobytes(),'serial query derivation'
            S=c['keys'];assert (sub/'mask.bin').read_bytes()==(mainroot/'mask.bin').read_bytes()[query*S*4:(query+1)*S*4],'serial original mask column'
            assert all(sha(sub/(role+'.bin'))==sha(mainroot/(role+'.bin')) for role in ['K','V']),'serial fullKV identity'
            c.update(q=1,root=str(sub));c['metadata']=load(sub/'snapshot.json');c['inputs']=job['context']['inputs']
            assert all(c['metadata'][key]['op_params_bytes']==m[key]['op_params_bytes'] for key in ['native_QK','native_softmax','native_AV']),'serial op parameters'
            assert c['metadata']['Q']['ne']==[c['d'],1,c['Hq'],1] and c['metadata']['mask']['ne']==[S,1,1,1]
        for source in c['inputs']:
            actual=Path(c['root'])/source['name'];assert actual.stat().st_size==source['bytes'] and sha(actual)==source['sha256'],'frozen input payload drift'
        if not (path/'native/RECORD.json').exists():continue
        rr,receipt=audit(path/'native',c,job);assert receipt==load(path/'EVIDENCE.json'),'fresh evidence mismatch'
        if t['stage']=='reference':
            from collect import occurrence
            reference_parts[t['case_id'],t['query_index'],t['block']]=occurrence(path/'native',rr['calls'][0])
        for b in load(path/'native/BLOBS.json'):assert sha(path/'native'/b['file'])==b['sha256'],'occurrence byte drift'
        life=load(path/'host.LIFETIME.json');assert life['exit_code'] in [0,3] and not load(path/'host.JOB_EVENTS.json')['errors']
        if receipt['numerical_qualified']:assert life['exit_code']==0 and life['error'] is None and end['error'] is None,'monitor/lifecycle exception invalidates successful bytes'
        samples=[(x['sync_return']-x['begin'])*1e6/rr['QPC_frequency'] for x in rr['calls'] if not x['warmup']];calls=[(x['readback_return']-x['begin'])*1e6/rr['QPC_frequency'] for x in rr['calls'] if not x['warmup']];init={k:v*1e6/rr['QPC_frequency'] for k,v in rr['cost_ticks'].items()}
        record=dict(**row,numerical_qualified=receipt['numerical_qualified'],actual_method=rr['observer_method'],host_seconds=life['seconds'],peak_job_commit_bytes=life['peak_job_commit_bytes'],job_processes=life['job_total_processes'],ordinary_occurrences=len(rr['calls']),graph_nodes=len(load(path/'native/GRAPH.json')['nodes']),resident_mean_us=statistics.mean(samples) if samples else None,resident_median_us=statistics.median(samples) if samples else None,resident_p95_us=sorted(samples)[math.ceil(.95*len(samples))-1] if samples else None,resident_max_us=max(samples) if samples else None,completed_call_mean_us=statistics.mean(calls) if calls else None,input_inclusive_first_call_phase_sum_us=init['CPU_materialize']+init['upload_and_sync']+(rr['calls'][0]['readback_return']-rr['calls'][0]['begin'])*1e6/rr['QPC_frequency'],**{k+'_us':v for k,v in init.items()});hosts.append(record)
        if (path/'OBSERVATION.json').exists():
            obs=load(path/'OBSERVATION.json');assert obs['numerical_qualified']==receipt['numerical_qualified'] and obs['measured_us']==samples and obs['evidence_receipt_sha256']==sha(path/'EVIDENCE.json')
            stage=t['stage'];name='aa_pilot' if stage=='aa_pilot' else 'confirm0' if stage=='confirm' and t['block']<4 else 'confirm1' if stage=='confirm' else 'holdout0' if t['block']<4 else 'holdout1';bp=raw/f'{name}_BLOCK_{t["block"]}.json';block=load(bp) if bp.exists() else None
            obs['environment_qualified']=bool(block and block['environment_qualified']);record['environment_qualified']=obs['environment_qualified'];record['session_id']=obs['session_id'];observations.append(obs)
    for cid,reference in refs.items():
        q=cases[cid]['q'];pieces=[]
        for query in range(q):
            x=reference_parts[cid,query,0];y=reference_parts[cid,query,1];assert x==y,'independent serial reference repeat mismatch';pieces.append(x)
        assert b''.join(pieces)==(raw/'inputs'/cid/'ordinary_reference.bin').read_bytes(),'reference query concatenation/order mismatch'
    with (out/'observations.jsonl').open('x',encoding='utf-8') as file:
        for x in observations:file.write(json.dumps(x,separators=(',',':'))+'\n')
    rows_csv(out/'HOSTS.csv',hosts);rows_csv(out/'COVERAGE.csv',coverage);result=analyze(plan,observations,draws=draws);save(out/'ANALYSIS.json',result)
    summary=dict(hosts=len(hosts),graph_calls=sum(x['actual_calls'] or 0 for x in hosts),by_stage={k:dict(hosts=len(v),calls=sum(x['actual_calls'] or 0 for x in v),qualified=sum(x['numerical_qualified'] for x in v)) for k,v in _group(hosts,'stage').items()},observed_timing_hosts=len(observations),bootstrap_draws=draws,raw_byte_audit='ALL_OCCURRENCES_CHECKED',external_independent_review=False,raw_root_location_only=str(raw));save(out/'AUDIT.json',summary);print(json.dumps(summary),flush=True);return result

def _group(rows,key):
    groups=collections.defaultdict(list)
    for r in rows:groups[r[key]].append(r)
    return groups
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--draws',type=int,default=4000);a=ap.parse_args();export(a.out,a.draws)
