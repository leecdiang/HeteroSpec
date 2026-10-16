"""Independent CPU evidence reconstruction and fixed host/context cost estimators."""
import math,statistics,itertools
from pathlib import Path
from common import V,load,sha,blob
import identity as I

def signature(graph):
    nodes=graph['nodes'];memo={}
    def walk(i):
        if i<0:return ('input',i)
        if i not in memo:
            n=nodes[i];assert n['id']==i
            memo[i]=(n['op'],n['type'],tuple(n['ne']),tuple(n['nb']),tuple(n['op_params']),tuple(walk(x) for x in n['src']))
        return memo[i]
    return walk(len(nodes)-1)

def graphcheck(expected,actual,placement=False):
    def clean(n):return {k:v for k,v in n.items() if k not in ('CUDA_support','placement')}
    assert [clean(n) for n in expected['nodes']]==[clean(n) for n in actual['nodes']]
    assert expected['output']==actual['output'] and expected['common_q1_original_arithmetic_chain']==actual['common_q1_original_arithmetic_chain']
    assert all(type(n['CUDA_support']) is bool and n['CUDA_support'] for n in actual['nodes'])
    if placement:
        required={n['id'] for n in actual['nodes'] if not n['metadata_only']}|{'input'+str(i) for i in range(4)}
        owners=actual['ownership'];assert len(owners)==len(required) and {o['id'] for o in owners}==required
        assert all(o['valid'] and o['has_buffer'] and not o['host'] and o['actual']==o['intended']!=0 for o in owners)

def census(record,plan,expected):
    assert record['graph_computes']==0 and record['GPU_initializations']==1 and len(record['records'])==72
    seen=set();queries=0
    for g in record['records']:
        k=g['descriptor_id'],g['layout'];assert k not in seen;seen.add(k);graphcheck(expected[k],g);queries+=len(g['nodes'])
    assert seen==set(expected) and queries==record['support_queries']
    return dict(supported_graphs=72,support_queries=queries,denied_slots=[],clean_admitted=True,clean_authorization=False)

def intervals(record):
    frequency=record['QPC_frequency'];assert type(frequency)is int and frequency>0
    rows=record['intervals'];count=8 if record['kind']=='clean' else 1
    assert record['warmups']==1 and record['graph_computes']==count+1 and record['measured']==count and len(rows)==count+1
    previous=None;out=[]
    for i,r in enumerate(rows):
        assert r['index']==i and r['warmup']==(i==0)
        ts=[r[k] for k in ['begin','compute_return','sync_return','readback_return','audit_return']]
        assert all(type(t)is int for t in ts) and ts==sorted(ts) and ts[2]>ts[0]
        assert previous is None or ts[0]>=previous;previous=ts[-1]
        scale=1000/frequency;f=(ts[1]-ts[0])*scale;g=(ts[2]-ts[1])*scale;h=(ts[3]-ts[2])*scale
        out.append(dict(warmup=i==0,F_ms=f,G_ms=g,FG_ms=(ts[2]-ts[0])*scale,H_ms=h,resident_call_FGH_ms=(ts[3]-ts[0])*scale,audit_ms=(ts[4]-ts[3])*scale))
    return out

def inspect(slot,directory,f0,plan,expected,root):
    n=directory/'native';r=load(n/'RECORD.json');ident=I.process_identity(directory,'native',dict(f0,executable=f0['hosts']['trace' if slot['kind']=='trace' else 'clean']['path']),60)
    I.process_identity(directory,'readiness',f0);assert r['pid']==ident[0] and r['status']=='COMPLETED' and r['kind']==slot['kind'] and r['layout']==slot['layout']
    I.verify_modules(n,r,dict(f0,executable=f0['hosts'][slot['kind']]['path'],executable_sha256=f0['hosts'][slot['kind']]['sha256']),load(directory/'MODULE_FILES.json'))
    graphcheck(expected,r and load(n/'GRAPH_AND_OWNERSHIP.json'),True)
    assert r['QPC_frequency']==f0['QPC_frequency']
    assert not any((n/(stage+'.BLOB.json')).exists() for stage in ['QK','softmax','AV'])
    ir=intervals(r);assert len(list(n.glob('GRAPH_STARTED_*.json')))==slot['graph_computes']
    meta=next(d['metadata'] for d in plan['descriptors'] if d['id']==slot['descriptor'])
    for role in ['Q','K','V','mask']:
        source=next(p for p in slot['input_files'] if Path(p['path']).name==meta[role]['file'])
        original=blob(root/'cas',source)
        for when in ['before','after']:
            ref=load(n/f'input_{role}.{when}.BLOB.json');assert ref['pid']==r['pid'] and ref['slot']==slot['id'];assert blob(root/'cas',ref)==original
    ordinary=blob(root/'cas',slot['ordinary_reference'])
    for i in range(slot['graph_computes']):
        ref=load(n/f'ordinary_{i}.BLOB.json');assert ref['pid']==r['pid'] and ref['slot']==slot['id'];assert blob(root/'cas',ref)==ordinary
    cost=r['cost_ticks'];assert all(type(t)is int and t>=0 for t in cost.values())
    measured=ir[1:];fg=[x['FG_ms'] for x in measured];full=[x['resident_call_FGH_ms'] for x in measured]
    cold_input_sum=sum(cost[k] for k in ['source_read','CPU_materialize_full_inputs','H2D_and_setup_sync'])*1000/r['QPC_frequency']+ir[0]['resident_call_FGH_ms']
    return dict(id=slot['id'],descriptor=slot['descriptor'],family=slot['family'],phase=slot['phase'],q=slot['q'],layer=slot['layer'],layout=slot['layout'],block=slot['block'],process_identity=list(ident),qualified=True,ordinary_reference_equal_all_calls=True,intervals=ir,mean_FG_ms=statistics.mean(fg),mean_FGH_ms=statistics.mean(full),FG_median_ms=statistics.median(fg),FG_p95_ms=sorted(fg)[math.ceil(.95*len(fg))-1],FG_max_ms=max(fg),cold_input_first_call_disjoint_phase_sum_ms=cold_input_sum,cost_ticks=cost,QPC_frequency=r['QPC_frequency'])

def aggregate(rows,plan):
    table={};ids=set()
    for r in rows:
        key=r['descriptor'],r['layout'],r['block'];assert key not in table and tuple(r['process_identity']) not in ids
        assert r['qualified'] and r['mean_FG_ms']>0 and r['mean_FGH_ms']>=r['mean_FG_ms']
        table[key]=r;ids.add(tuple(r['process_identity']))
    contrasts=[]
    for d in plan['descriptors']:
        for b in range(3):
            for left,right in [('QB','QH_C'),('PQ','QB')]:
                a,z=table.get((d['id'],left,b)),table.get((d['id'],right,b))
                if not a or not z:contrasts.append(dict(descriptor=d['id'],block=b,left=left,right=right,qualified=False,reason='missing/failed coordinate retained'));continue
                contrasts.append(dict(descriptor=d['id'],family=d['family'],phase=d['phase'],q=d['q'],layer=d['layer'],block=b,left=left,right=right,qualified=True,delta_ms=a['mean_FG_ms']-z['mean_FG_ms'],speed_ratio=a['mean_FG_ms']/z['mean_FG_ms'],resident_call_ratio=a['mean_FGH_ms']/z['mean_FGH_ms']))
    complete=len(table)==216
    strata=[]
    if complete:
        for family in ['Qwen','SmolLM2','Llama']:
            for phase in ['prefill','continuation','ALL']:
                for q in [1,2,3,4,'GT1']:
                    for left,right in [('QB','QH_C'),('PQ','QB')]:
                        cs=[r for r in contrasts if r.get('family')==family and (phase=='ALL' or r['phase']==phase) and (r['q']>1 if q=='GT1' else r['q']==q) and r['left']==left]
                        if cs:strata.append(dict(family=family,phase=phase,q=q,left=left,right=right,host_contrasts=len(cs),independent_contexts=len({r['descriptor'] for r in cs}),geometric_speed_ratio=math.exp(statistics.mean(math.log(r['speed_ratio']) for r in cs)),mean_delta_ms=statistics.mean(r['delta_ms'] for r in cs),practical_evidence=(q!=1 and math.exp(statistics.mean(math.log(r['speed_ratio']) for r in cs))>1.02 and statistics.mean(r['delta_ms'] for r in cs)>.001),regression_count=sum(r['speed_ratio']<1 for r in cs)))
    context_repeats=[]
    for d in plan['descriptors']:
        for layout in ['PQ','QB','QH_C']:
            rs=[table.get((d['id'],layout,b)) for b in range(3)]
            good=[r for r in rs if r]
            if len(good)==3:
                values=[r['mean_FG_ms'] for r in rs]
                context_repeats.append(dict(descriptor=d['id'],layout=layout,block_means_ms=values,mean_ms=statistics.mean(values),median_ms=statistics.median(values),minimum_ms=min(values),maximum_ms=max(values),sample_CV=statistics.stdev(values)/statistics.mean(values)))
            else:context_repeats.append(dict(descriptor=d['id'],layout=layout,qualified_hosts=len(good),aggregate=None))
    return dict(context_repeats=context_repeats,status='COMPLETE_CLEAN_PANEL' if complete else 'INCOMPLETE_WITHHOLD_AGGREGATES',qualified_hosts=len(table),contrasts=contrasts,strata=strata,practical_speed_ratio_threshold=1.02,absolute_resolution_floor_ms=.001,confidence_interval=None,request_bootstrap=False,technical8_evaluations_are_not_independent_samples=True,trace_qualification=False,hardware_causality='UNKNOWN')
