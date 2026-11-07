"""CPU-only full-byte audit and compact descriptive cost export, including gaps."""
import argparse,collections,copy,csv,hashlib,json,math,statistics as st
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root,LAYOUTS
from runner import audit,occurrence,trace_audit
from plan import digest
from analyze import run
def csvfile(path,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('x',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
def graph_signature(g):
    clean=lambda n:{k:v for k,v in n.items() if k not in ['CUDA_support','placement']}
    return digest(dict(nodes=[clean(n) for n in g['nodes']],output=g['output']))
def remap_context(c,r):
    c=copy.deepcopy(c);old=Path(c['root']);c['root']=str(r/'inputs'/old.name)
    # Serial children carry a parent case ID and a serialN final component.
    if old.name.startswith('serial'):c['root']=str(r/'inputs'/old.parent.name/old.name)
    for l,ref in c['references'].items():
        p=Path(ref['path']);ref['path']=str(r/'inputs'/p.parent.name/p.name)
    return c
def export(out,draws=4000):
    r=root();out=Path(out);out.mkdir();p=load(r/'plan.json');s=load(r/'RUN_SPEC.json');f=load(r/('FREEZE_REPAIR1.json' if (r/'FREEZE_REPAIR1.json').exists() else 'FREEZE.json'));planned={t['task_id']:t for t in p['tasks']};coverage=[];hosts=[];observations=[];modes=[];reference_parts={};onproof={};attempts=sorted((r/'attempts').iterdir(),key=lambda x:load(x/'STARTED.json')['epoch'])
    for key,name in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json'),('policy_sha256','EXECUTION_POLICY.json'),('mode_sha256','MODE_EVIDENCE.json')]:assert sha(r/name)==f[key],name+' frozen bytes'
    for name,h in f['files'].items():assert sha(r/f.get('source_subdir','SOURCE')/name)==h,'consumed source identity'
    input_index=load(r/'INPUTS.json')
    for cid,c in input_index.items():
        for item in c['inputs']:assert sha(r/'inputs'/cid/item['name'])==item['sha256'],'full frozen input drift'
    for a in attempts:
        started=load(a/'STARTED.json');t=started['task'];job=load(a/'JOB.json');c=remap_context(job['context'],r);job=copy.deepcopy(job)
        if job.get('alternate_context'):
            ac=job['alternate_context'];ac['root']=str(r/'inputs'/Path(ac['root']).name);ac['reference']=str(Path(ac['root'])/'ordinary_reference.bin')
        end=load(a/'ENDED.json') if (a/'ENDED.json').exists() else {};life=load(a/'host.LIFETIME.json');g=load(a/'native/GRAPH.json') if (a/'native/GRAPH.json').exists() else None
        row=dict(task_id=t['task_id'],stage=t['stage'],case_id=t['case_id'],arm=t.get('arm',t['layout']),layout=t['layout'],mode=t['graph_mode'],block=t.get('block'),profile=job.get('profile',False),status=end.get('status','STARTED_INCOMPLETE'),actual_calls=end.get('actual_calls'),host_seconds=life['seconds'],peak_job_commit_bytes=life['peak_job_commit_bytes'],job_processes=life['job_total_processes'])
        if not (a/'native/RECORD.json').exists():hosts.append(row);continue
        record,receipt=audit(a/'native',c,job);assert receipt==load(a/'EVIDENCE.json'),'independent raw re-audit mismatch'
        for b in load(a/'native/BLOBS.json'):assert sha(a/'native'/b['file'])==b['sha256'],'CAS occurrence corruption'
        assert not load(a/'host.JOB_EVENTS.json')['errors'],'cleanup not established'
        if receipt['numerical_qualified']:assert life['exit_code']==0 and life['error'] is None and end.get('error') is None,'lifecycle invalidates cost'
        if job.get('profile'):
            mode=trace_audit(a/'native',job);assert mode==load(a/'MODE_AUDIT.json');modes.append(dict(task_id=t['task_id'],case_id=t['case_id'],layout=t['layout'],**mode))
            if job['graph_mode']=='ON' and mode['verified']:onproof[graph_signature(g)]=dict(mode_audit_sha256=sha(a/'MODE_AUDIT.json'),trace_sha256=mode['trace_sha256'])
        if job['capture_reference']:
            reference_parts[t['case_id'],t['query_index'],t['block']]=occurrence(a/'native',record['calls'][0])
            # Check serial derivation from all logical head/channel words, original
            # mask column, complete KV and inherited operation parameters.
            import numpy as np
            original=r/'inputs'/Path(c['root']).parent.name;m=load(original/'snapshot.json');q=m['Q']['ne'][1];D=m['Q']['ne'][0];H=m['Q']['ne'][2];j=t['query_index'];logical=np.ndarray((q,H,D),dtype='<f4',buffer=(original/'Q.bin').read_bytes(),strides=(m['Q']['nb'][1],m['Q']['nb'][2],4));assert (Path(c['root'])/'Q.bin').read_bytes()==logical[j].copy().tobytes()
            S=m['K']['ne'][1];assert (Path(c['root'])/'mask.bin').read_bytes()==(original/'mask.bin').read_bytes()[j*S*4:(j+1)*S*4]
            for role in ['K','V']:assert sha(Path(c['root'])/(role+'.bin'))==sha(original/(role+'.bin'))
            for op in ['native_QK','native_softmax','native_AV']:assert c['metadata'][op]==m[op]
        factor=1e6/record['QPC_frequency'];active=[x for x in record['calls'] if not x['warmup']]
        def vals(a,z):return [(x[z]-x[a])*factor for x in active]
        def mean(a,z):return st.mean(vals(a,z)) if active else None
        times=vals('begin','sync_return');call=vals('begin','readback_return');integrated=vals('transaction_begin','readback_return');cost={k:v*factor for k,v in record['cost_ticks'].items()}
        row.update(numerical_qualified=receipt['numerical_qualified'],calls=len(record['calls']),graph_nodes=len(g['nodes']),node_support_API_queries=2*len(g['nodes']),graph_signature=graph_signature(g),resident_mean_us=st.mean(times),resident_median_us=st.median(times),resident_p95_us=sorted(times)[math.ceil(.95*len(times))-1],resident_max_us=max(times),resident_call_mean_us=st.mean(call),integrated_q_update_mean_us=st.mean(integrated) if record['integrated_q_update'] else None,compute_return_mean_us=mean('begin','compute_return'),explicit_sync_mean_us=mean('compute_return','sync_return'),readback_mean_us=mean('sync_return','readback_return'),Q_copy_or_transpose_mean_us=mean('transaction_begin','Q_materialized') if record['integrated_q_update'] else None,Q_upload_and_sync_mean_us=mean('Q_materialized','Q_upload_complete') if record['integrated_q_update'] else None,**{k+'_us':v for k,v in cost.items()})
        hosts.append(row)
        if t['stage'] not in ['confirm','producer']:continue
        assert not job['profile'],'profile costs cannot enter clean'
        if t['graph_mode']=='ON':assert graph_signature(g) in onproof,'missing actual signature mode proof'
        else:assert record['GGML_CUDA_DISABLE_GRAPHS']=='1'
        name=('producer' if t['stage']=='producer' else 'confirm')+str(t['block']//4);bp=r/f'{name}_BLOCK_{t["block"]}.json';block=load(bp) if bp.exists() else None;environment=bool(block and block['environment_qualified']);row['environment_qualified']=environment
        # A logical identity shared across physical compact/permuted producer arms.
        logical=input_index[(f"q{c['q']}-k256-v{c['realization']}") if t['stage']=='producer' else c['case_id']]['input_sha256']
        obs=dict(task_id=t['task_id'],attempt_id=a.name,plan_sha256=p['plan_sha256'],layout=t['layout'],graph_mode=t['graph_mode'],cost_view=t['cost_view'],status='QUALIFIED' if receipt['numerical_qualified'] else 'NUMERICAL_FAILURE',numerical_qualified=receipt['numerical_qualified'],environment_qualified=environment,mode_verified=True,session_id=started['actual_session'],measured_us=integrated if t['stage']=='producer' else times,host_sha256=f['native_sha256'],runtime_sha256=f['runtime_manifest_sha256'],policy_sha256=f['policy_sha256'],logical_input_sha256=logical,physical_input_sha256=c['input_sha256'],reference_sha256=c['references'][t['layout']]['sha256'],mode_evidence_sha256=(onproof[graph_signature(g)]['mode_audit_sha256'] if t['graph_mode']=='ON' else f['mode_sha256']),audit_sha256=sha(a/'EVIDENCE.json'),failure_reason=None if receipt['numerical_qualified'] else 'raw byte control')
        observations.append(obs)
    # Reference pairs must be new-process captures, exact and concatenated in j order.
    refs=load(r/'REFERENCES.json')
    if (r/'PRODUCER_REFERENCES.json').exists():refs.update(load(r/'PRODUCER_REFERENCES.json'))
    for cid,ref in refs.items():
        taskcid='producer-q4-v'+cid[-1] if cid.startswith('q4-') else cid;c=input_index[cid];parts=[]
        for j in range(c['q']):
            x=reference_parts[taskcid,j,0];assert x==reference_parts[taskcid,j,1],'independent serial repeat';parts.append(x)
        assert b''.join(parts)==(r/'inputs'/cid/'ordinary_reference.bin').read_bytes() and sha(r/'inputs'/cid/'ordinary_reference.bin')==ref['sha256']
    # Every planned coordinate, plus genuinely extra capability attempts.
    existing={x['task_id']:x for x in hosts}
    for tid,t in planned.items():coverage.append(dict(task_id=tid,stage=t['stage'],case_id=t['case_id'],mode=t['graph_mode'],layout=t['layout'],status=existing[tid]['status'] if tid in existing else 'UNSTARTED'))
    for stage in ['confirm','producer']:
        actual=[load(a/'STARTED.json')['task']['task_id'] for a in attempts if load(a/'STARTED.json')['task']['stage']==stage];present=set(actual);assert actual==[t['task_id'] for t in p['tasks'] if t['stage']==stage and t['task_id'] in present],'actual order differs'
    csvfile(out/'HOST_COSTS.csv',hosts);csvfile(out/'COVERAGE.csv',coverage);csvfile(out/'MODE_EVIDENCE.csv',modes)
    with (out/'receipts.jsonl').open('x') as file:
        for obs in observations:file.write(json.dumps(obs,separators=(',',':'))+'\n')
    result=run(p,observations,draws);save(out/'ANALYSIS.json',result)
    summary=dict(hosts=len(hosts),graph_calls=sum(x.get('calls',0) for x in hosts),by_stage={k:dict(hosts=len(v),calls=sum(x.get('calls',0) for x in v),qualified=sum(x.get('numerical_qualified',False) for x in v)) for k,v in group(hosts,'stage').items()},node_support_API_queries=sum(x.get('node_support_API_queries',0) for x in hosts),raw_audit='ALL_OUTPUT_OCCURRENCES_AND_INPUTS',fresh_serial_pairs=True,profiled_hosts=sum(x['profile'] for x in hosts),actual_ON_signatures=len(onproof),external_review=False)
    save(out/'AUDIT.json',summary);print(summary,flush=True)
    return result
def group(rows,key):
    d=collections.defaultdict(list)
    for r in rows:d[r[key]].append(r)
    return d
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--draws',type=int,default=4000);a=ap.parse_args();export(a.out,a.draws)
