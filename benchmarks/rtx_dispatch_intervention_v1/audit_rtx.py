"""Full-byte CPU audit and paired exports. Fresh restores remap only UUID paths."""
import argparse,collections,copy,csv,hashlib,math,os,statistics,struct
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
import runner
from analysis_rtx import analyze
from inputs_rtx import verify

def remap(obj,old,new):
    if isinstance(obj,str):return obj.replace(old,str(new))
    if isinstance(obj,list):return [remap(x,old,new) for x in obj]
    if isinstance(obj,dict):return {k:remap(v,old,new) for k,v in obj.items()}
    return obj

def signature(g,job):
    clean=lambda node:{k:v for k,v in node.items() if k not in ['CUDA_support','placement']}
    obj=dict(nodes=[clean(n) for n in g['nodes']],output=g['output'],inputs={role:job['context']['metadata'][role] for role in runner.ROLES})
    return hashlib.sha256(__import__('json').dumps(obj,sort_keys=True).encode()).hexdigest()

def csvwrite(path,rows):
    if not rows:return
    with Path(path).open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def mismatch(actual,expected):
    a=list(struct.unpack('<'+'f'*(len(actual)//4),actual));b=list(struct.unpack('<'+'f'*(len(expected)//4),expected));assert len(a)==len(b)
    def ordered(raw):
        v=struct.unpack('<I',raw)[0];return 0x80000000-v if v&0x80000000 else 0x80000000+v
    wrong=[i for i in range(len(a)) if actual[4*i:4*i+4]!=expected[4*i:4*i+4]]
    return dict(words=len(a),different_words=len(wrong),max_abs=max((abs(x-y) for x,y in zip(a,b)),default=0),max_ULP=max((abs(ordered(actual[4*i:4*i+4])-ordered(expected[4*i:4*i+4])) for i in wrong),default=0),first_word=wrong[0] if wrong else None)

def main(out):
    r=root();out=Path(out);out.mkdir();spec=load(r/'RUN_SPEC.json');original='D:/'+spec['execution_id'];p=load(r/'plan.json');index=remap(load(r/'INPUTS.json'),original,r);f=load(r/'FREEZE.json')
    for name,h in f['files'].items():assert sha(r/'SOURCE'/name)==h,'frozen source/native'
    for name,h in spec['numerical_DLLs'].items():assert sha(Path(spec['runtime_directory'])/name)==h,'runtime drift'
    for c in index.values():
        for row in c['inputs']:assert sha(Path(c['root'])/row['name'])==row['sha256']
        cell=next(x for x in p['cells'] if x['id']==c['cell']);base=index[c['cell']+'/'+cell['arms'][0]['name']];sm=base['metadata']
        for role in runner.ROLES:verify((Path(base['root'])/(role+'.bin')).read_bytes(),sm[role],(Path(c['root'])/(role+'.bin')).read_bytes(),c['metadata'][role],role)
    refs=remap(load(r/'REFERENCES.json'),original,r);parts=collections.defaultdict(list);hosts=[];native=[];mismatches=[];trace=[];calls=0;profile=0
    for a in sorted((r/'attempts').iterdir()):
        start=load(a/'STARTED.json');t=start['task'];j=remap(load(a/'JOB.json'),original,r);n=a/'native';record=load(n/'RECORD.json');c=j['context'];rr,audit=runner.audit(n,c,j);g=load(n/'GRAPH.json');sig=signature(g,j)
        assert sha(a/'JOB.json') and sha(a/'STARTED.json');life=load(a/'host.LIFETIME.json');events=load(a/'host.JOB_EVENTS.json');assert not events['errors'],'cleanup uncertainty';assert life['exit_code']==(0 if audit['numerical_qualified'] else 3),'exit eligibility'
        assert sha(r/'SOURCE/collector.exe')==start['native_sha256'];assert j['execution_id']==spec['execution_id']
        if j['profile']:
            proof=runner.trace_audit(n,j);assert proof==load(a/'MODE_AUDIT.json');trace.append(dict(attempt=a.name,signature=sig,verified=proof['verified'],kernels=proof['actual_kernel_records']));profile+=1
        else:assert not any('cupti' in m.lower() for m in record['modules']),'clean/reference loads observer'
        for b in load(n/'BLOBS.json'):assert sha(n/b['file'])==b['sha256'] and (n/b['file']).stat().st_size==b['bytes'],'raw blob inventory'
        costs={k:v/rr['QPC_frequency']*1e6 for k,v in rr['cost_ticks'].items()};allrows=rr['calls'];formal=[x for x in allrows if not x['warmup']];count=len(allrows);calls+=count
        nr=dict(task_id=a.name,stage=t['stage'],cell=t.get('cell',''),arm=t.get('arm',''),qualified=audit['numerical_qualified'],calls=count,warmup_calls=sum(x['warmup'] for x in allrows),profile=j['profile'],exit_code=life['exit_code'],native_seconds=life['seconds'],peak_commit_bytes=life['peak_job_commit_bytes'],graph_buffer_bytes=rr['graph_buffer_bytes'],persistent_input_bytes=rr['persistent_input_bytes'],signature=sig,**{'setup_'+k+'_us':v for k,v in costs.items()})
        native.append(nr)
        if t['stage']=='reference':
            cid=a.name[len('reference-'):].split('-q')[0];qi=int(a.name.split('-q')[-1].split('-r')[0]);parts[cid,qi].append(runner.occurrence(n,allrows[0]))
        elif not audit['numerical_qualified']:
            ref=Path(c['references'][j['layout']]['path']).read_bytes()
            for row in allrows:
                actual=runner.occurrence(n,row)
                if actual!=ref:mismatches.append(dict(task_id=a.name,index=row['index'],**mismatch(actual,ref)))
        if t['stage']=='timed':
            block=load(r/f"collect{t['session']}_BLOCK_{t['block']}.json");adm=load(r/'ADMISSION.json');canonical=p['cells'][next(i for i,z in enumerate(p['cells']) if z['id']==t['cell'])]['arms'][0]['name'] if t['arm'] in ['native_B','QB_B'] else t['arm'];key=t['cell']+'/'+canonical;gate=adm['arms'][key]
            # Direct matching signature from a qualified profiled value0 host; no mode flag substitution.
            v0=key.replace('-v1/','-v0/');proofs=[]
            for name in load(r/'QUALIFICATION.json')[v0]['attempts']:
                pa=r/'attempts'/name
                if (pa/'MODE_AUDIT.json').exists():
                    pj=remap(load(pa/'JOB.json'),original,r);pg=load(pa/'native/GRAPH.json');mp=runner.trace_audit(pa/'native',pj)
                    if mp['verified']:proofs.append((signature(pg,pj),name))
            assert any(x[0]==sig for x in proofs),'no matching traced ON signature'
            assert gate['eligible'];v=[(x['readback_return']-x['transaction_begin'] if t['panel']=='T0' else x['sync_return']-x['begin'])/rr['QPC_frequency']*1e6 for x in formal]
            h=dict(task_id=a.name,cell=t['cell'],arm=t['arm'],panel=t['panel'],block=t['block'],planned_session=t['session'],actual_session=start['actual_session'],eligible=audit['numerical_qualified'] and block['environment_qualified'],values_us=v,signature=sig,mode='inferred from directly traced matching qualification signatures',cost_view='integrated_Q_transaction' if t['panel']=='T0' else 'completed_graph')
            hosts.append(h)
            for field,beg,end in [('resident_graph','begin','sync_return'),('resident_call','begin','readback_return'),('CPU_Q','transaction_begin','Q_materialized'),('Q_upload_sync','Q_materialized','Q_upload_complete'),('compute_return','begin','compute_return'),('extra_sync','compute_return','sync_return'),('readback','sync_return','readback_return')]:
                vv=[(x[end]-x[beg])/rr['QPC_frequency']*1e6 for x in formal];nr[field+'_mean_us']=statistics.mean(vv)
            nr['primary_mean_us']=statistics.mean(v);nr['primary_median_us']=statistics.median(v);nr['primary_p95_us']=sorted(v)[math.ceil(.95*len(v))-1];nr['primary_max_us']=max(v)
    for cid,ref in refs.items():
        c=next(x for x in p['cells'] if x['id']==cid);joined=[]
        for qi in range(c['q']):assert len(parts[cid,qi])==2 and parts[cid,qi][0]==parts[cid,qi][1];joined.append(parts[cid,qi][0])
        actual=b''.join(joined);assert actual==Path(ref['path']).read_bytes() and hashlib.sha256(actual).hexdigest()==ref['sha256'],'fresh serial derivation'
    assert len(native)<=358 and calls<=11732 and profile<=24
    result=analyze(p,hosts);save(out/'ANALYSIS.json',result);save(out/'HOSTS.json',native);save(out/'TIMED.json',hosts);save(out/'MISMATCHES.json',mismatches);save(out/'TRACE_SIGNATURES.json',trace)
    # Consistent scalar columns for compact public CSV, raw per-call QPC remains in native records.
    keys=sorted(set().union(*(x.keys() for x in native)));csvwrite(out/'HOST_COSTS.csv',[{k:x.get(k) for k in keys} for x in native]);csvwrite(out/'COVERAGE.csv',result['coverage']);csvwrite(out/'MISMATCHES.csv',mismatches)
    save(out/'AUDIT.json',dict(status='PASS',native_hosts=len(native),explicit_graph_calls=calls,profile_attempts=profile,qualified=sum(x['qualified'] for x in native),timed_hosts=len(hosts),mismatched_outputs=len(mismatches),all_inputs_exact=True,all_modules_IAT_verified=True,all_full_ordinary_occurrences=True,all_serial_references_rederived=True,all_clean_signatures_match_traced_ON=True,external_independent_review=False))
    print(load(out/'AUDIT.json'))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);z=a.parse_args();main(z.out)
