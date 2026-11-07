"""Independent complete-panel raw semantics. CPU only; no native/device launches.

No assumed QH equalities. Exposed operator contexts and process repeats remain
distinct, and every frozen coordinate gets a status even after an early stop.
"""
import argparse,itertools,math,struct
from pathlib import Path
from common import V,load,save,sha,blob,stage_sizes
from raw_math import numeric
STAGES=('QK','softmax','AV','ordinary')
LAYOUTS=('MQ','PQ','QB','QH_C','QH_D')
PAIRS=(('QH_C','PQ'),('QH_C','QB'),('QH_D','PQ'),('QH_C','QH_D'),('PQ','QB'),('QH_D','QB'),('MQ','PQ'),('MQ','QB'),('MQ','QH_C'),('MQ','QH_D'))
def norm(p):return str(Path(p).resolve()).lower()
def finite(b):return len(b)%4==0 and all((u&0x7f800000)!=0x7f800000 for (u,) in struct.iter_unpack('<I',b))
def canonical(b,meta):
    assert meta['type']==0 and len(b)==meta['bytes'];out=bytearray();ne,nb=meta['ne'],meta['nb'];assert ne[3]==1
    for h in range(ne[2]):
        for j in range(ne[1]):
            for k in range(ne[0]):
                offset=k*nb[0]+j*nb[1]+h*nb[2];assert offset+4<=len(b);out.extend(b[offset:offset+4])
    return bytes(out)
def restore(av,meta):
    d,q,h,_=meta['native_AV']['ne'];assert len(av)==d*q*h*4
    return b''.join(av[(a*q+j)*d*4:(a*q+j+1)*d*4] for j in range(q) for a in range(h))
def difference(a,b,dimensions):
    r=numeric(a,b);first=next((i for i in range(len(a)//4) if a[4*i:4*i+4]!=b[4*i:4*i+4]),None)
    r['first_differing_word']=first
    if first is None:r['first_logical_index']=None
    else:
        x=first;idx=[]
        for n in dimensions:idx.append(x%n);x//=n
        assert not x;r['first_logical_index']=idx
    return r
def relation(a,b,meta):
    dims={s:meta['native_'+s]['ne'] for s in STAGES[:-1]};d,q,h,_=meta['native_AV']['ne'];dims['ordinary']=[d*h,q,1,1]
    values={s:difference(a[s],b[s],dims[s]) for s in STAGES}
    return dict(stages=values,first_divergence_operator=next((s for s in STAGES if not values[s]['bitwise_equal']),None))
def verify_numeric(slot,meta,values,reference,historical,previous=None):
    sizes=stage_sizes(meta);assert set(values)==set(STAGES)
    assert all(len(values[s])==sizes[s] and finite(values[s]) for s in STAGES),'full logical size/nonfinite gate'
    assert restore(values['AV'],meta)==values['ordinary'],'own-path ordinary AV restore'
    vs=relation(reference,values,meta)
    if slot['layout']=='MQ' or slot['q']==1:assert all(c['bitwise_equal'] for c in vs['stages'].values()),'MQ own-path / all-five q1 public control'
    if slot['layout'] in ('PQ','QB'):
        assert all(values[s]==historical[s] for s in STAGES[:-1]),'frozen historical PQ/QB correspondence'
    if slot['repeat']==1:
        assert previous is not None and all(previous[s]==values[s] for s in STAGES),'independent-process repeatability'
    return dict(vs_original_MQ=vs,status='BITWISE_MQ_CORRESPONDENCE' if all(c['bitwise_equal'] for c in vs['stages'].values()) else 'FINITE_EMPIRICAL_DIFFERENCE',
        repeatability='BITWISE_PASS' if slot['repeat']==1 else None)
def strip(n):return {k:v for k,v in n.items() if k not in ('CUDA_support','placement')}
def verify_graph(expected,actual,placement=False):
    assert len(actual['nodes'])==len(expected['nodes'])
    assert [strip(n) for n in actual['nodes']]==[strip(n) for n in expected['nodes']],'actual node/geometry/op_params/source identities'
    assert actual['output']==expected['output']
    assert actual['common_q1_original_arithmetic_chain']==expected['common_q1_original_arithmetic_chain']
    full=True
    for n in actual['nodes']:
        assert type(n['CUDA_support'])is bool
        if not n['metadata_only']:
            full &= n['CUDA_support']
            if placement:assert n['CUDA_support'] and n['placement'] and 'CUDA' in n['placement'],'actual node CUDA placement'
    assert actual['full_support'] is full
    if placement:
        assert full and actual['actual_placement']=='CUDA0 direct backend; no scheduler' and actual['all_ownership_checks_passed']
        required={n['id'] for n in actual['nodes'] if not n['metadata_only']};owners=actual['ownership']
        assert {o['node'] for o in owners}==required and len(owners)==len(required)
        assert all(o['valid'] and o['has_buffer'] and not o['buffer_is_host'] and o['actual_device']==o['intended_device']!=0 for o in owners),'actual buffer/device ownership handles'
    return full
def verify_modules(native,record,f0,module_files):
    gate=load(native/'CORE_ADMITTED_BEFORE_CUDA.json');core=gate['core'];exports=load(V/'ABI_EXPORTS.json')
    assert core['sha256']==f0['numerical_DLLs']['ggml-base.dll'] and norm(core['path'])==norm(Path(f0['runtime_directory'])/'ggml-base.dll')
    assert core['ready'] and core['events'].count('dll_initializer_returned')==1
    base=core['module_handle']
    for name,fn in core['functions'].items():
        assert fn['address']==base+exports['core'][name]['RVA'] and norm(fn['owner_path'])==norm(core['path'])
    host=gate['host_import'];assert host['IAT_target']==core['functions']['ggml_init']['address'] and host['module_handle']==base and norm(host['owner_path'])==norm(core['path'])
    reg=gate['registry_import'];assert reg['sha256']==f0['numerical_DLLs']['ggml.dll'] and norm(reg['path'])==norm(Path(f0['runtime_directory'])/'ggml.dll')
    assert reg['backend_load_IAT_target']==reg['owner']+exports['registry']['ggml_backend_load']['RVA']
    plugin=load(native/'PLUGIN_CORE_IMPORTS.json');assert len(plugin)==41 and {p['symbol'] for p in plugin}==set(exports['plugin_core_symbols'])
    assert all(norm(p['owner_path'])==norm(core['path']) and p['target']==base+exports['core'][p['symbol']]['RVA'] for p in plugin)
    inventory={norm(p['path']):p for p in module_files};seen=set()
    for path in record['modules']:
        assert norm(path) in inventory,'every observed module must have a disk identity receipt'
        name=Path(path).name.lower()
        if name in {s.lower() for s in f0['numerical_DLLs']}:
            expected=next(h for n,h in f0['numerical_DLLs'].items() if n.lower()==name)
            assert norm(Path(path).parent)==norm(f0['runtime_directory']) and inventory[norm(path)]['sha256']==expected;seen.add(name)
    assert {'ggml-base.dll','ggml.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=seen
    assert inventory[norm(f0['executable'])]['sha256']==f0['executable_sha256']
    assert norm(f0['executable']) in {norm(p) for p in record['modules']}
    return core
def contexts(plan):return {d['id']:d for d in plan['descriptors']}
def reference_values(descriptor,cas,refs):
    files=refs[descriptor]['files'];meta=load_metadata(descriptor,cas,refs)
    data={s:canonical(blob(cas,files[meta['native_'+s]['file']]),meta['native_'+s]) for s in STAGES[:-1]}
    data['ordinary']=restore(data['AV'],meta);return meta,data
def load_metadata(descriptor,cas,refs):
    import json
    return json.loads(blob(cas,refs[descriptor]['metadata_file']))
def values_for(directory,cas,slot,pid,inputs=True):
    out={}
    names=(*('input_'+role+'.'+when for role in ('Q','K','V','mask') for when in ('before','after')),*STAGES) if inputs else STAGES
    for name in names:
        ref=load(directory/(name+'.BLOB.json'))
        assert ref['artifact']==name and ref['slot']==slot['id'] and ref['pid']==pid
        assert ref['cas_relative']=='cas/'+ref['sha256']+'.bin'
        out[name]=blob(cas,ref)
    return out
def process_identity(directory,prefix,f0):
    proc=load(directory/(prefix+'.PROCESS.json'));life=load(directory/(prefix+'.LIFETIME.json'));events=load(directory/(prefix+'.JOB_EVENTS.json'))
    assert proc['pid']==life['pid']==events['registered_PID'] and type(proc['creation_filetime_100ns'])is int and proc['creation_filetime_100ns']>0
    assert proc['creation_filetime_100ns']==life['creation_filetime_100ns'] and life['error'] is None and life['exit_code']==0
    assert proc['creation_flags']==0x08000000|4 and proc['active_process_limit']==2 and proc['suspended_before_job_assignment']
    assert not events['errors'];started=[e for e in events['events'] if e['message']==6]
    assert {e['pid'] for e in started}==set(events['started_unique_PIDs']) and len(started)==life['job_total_processes']<=2
    assert sum(e['pid']==proc['pid'] for e in started)==1 and not list(directory.glob(prefix+'.*.OVERFLOW.json'))
    expected=f0['executable'] if prefix=='native' else f0['admission_policy']['nvidia_smi']
    for e in started:assert norm(e['image'])==norm(expected if e['pid']==proc['pid'] else f0['console_helper']['path'])
    assert events['console_helper_pin']['sha256']==f0['console_helper']['sha256']
    assert 0<=life['seconds']<= (60 if prefix=='native' else 10)
    return (proc['pid'],proc['creation_filetime_100ns'])
def inspect(slot,directory,f0,plan,refs,expected,prior,root):
    n=directory/'native';record=load(n/'RECORD.json');pid=load(directory/'native.PROCESS.json')['pid']
    assert record['pid']==pid and record['status']=='COMPLETED' and record['layout']==slot['layout'] and record['kind']=='numeric'
    assert record['graph_computes']==1 and record['warmups']==0
    assert load(n/'GRAPH_STARTED_0.json')==dict(index=0,warmup=False) and len(list(n.glob('GRAPH_STARTED_*.json')))==1
    for name in ('GRAPH_CALL_RETURNED.json','SYNCHRONIZATION_RETURNED.json'):
        r=load(n/name);assert r['status']==0 and r['pid']==pid,'call completion/synchronization gate'
    identity=process_identity(directory,'native',f0);ready_identity=process_identity(directory,'readiness',f0);assert identity!=ready_identity
    core=verify_modules(n,record,f0,load(directory/'MODULE_FILES.json'))
    assert core['pid']==pid
    verify_graph(expected,record['nodes'],True)
    assert load(n/'STAGE_DESCRIPTORS.json')==expected['stage_descriptors']
    assert len(record['nodes']['nodes'])==slot['registered_support_queries']
    meta,reference=reference_values(slot['descriptor'],root/'cas',refs)
    all_values=values_for(n,root/'cas',slot,pid)
    for role in ('Q','K','V','mask'):
        original=blob(root/'cas',refs[slot['descriptor']]['files'][meta[role]['file']])
        assert all_values['input_'+role+'.before']==original==all_values['input_'+role+'.after'],'complete before/after input gate'
    values={s:all_values[s] for s in STAGES};previous=None
    if slot['repeat']==1:
        first=prior[slot['descriptor'],slot['layout'],0];assert tuple(first['process_identity'])!=identity
        previous=values_for(root/first['directory']/'native',root/'cas',plan['numerical_slots'][first['index']],first['pid'],False)
        previous={s:previous[s] for s in STAGES}
    historical={s:blob(root/'cas',refs[slot['descriptor']]['historical'][slot['layout']+'-r'+str(slot['repeat'])+'/'+s]) for s in STAGES[:-1]} if slot['layout'] in ('PQ','QB') else None
    result=verify_numeric(slot,meta,values,reference,historical,previous)
    return dict(slot=slot['id'],index=slot['index'],descriptor=slot['descriptor'],family=slot['family'],layer=slot['layer'],phase=slot['phase'],q=slot['q'],
        layout=slot['layout'],repeat=slot['repeat'],pid=pid,process_identity=list(identity),directory=directory.relative_to(root).as_posix(),module_input_graph_placement_completion_controls='PASS',**result)
def census_decision(census,expected,plan):
    assert census['GPU_initializations']==1 and census['graph_computes']==0 and census['allocations']==0
    assert len(census['records'])==360 and census['support_queries']==5418
    table={};queries=0
    for r in census['records']:
        key=(r['descriptor_id'],r['layout']);assert key not in table
        table[key]=verify_graph(expected[key],r);queries+=len(r['nodes'])
    assert set(table)==set(expected) and queries==5418
    denied=[s['id'] for s in plan['numerical_slots'] if not table[s['descriptor'],s['layout']]]
    # Unsupported D at q>1 is retained NOT_SUPPORTED, as the original protocol.
    mandatory_bad=any(not table[s['descriptor'],s['layout']] and (s['q']==1 or s['layout']!='QH_D') for s in plan['numerical_slots'])
    return dict(primary_QH='QH_C',QH_D_never_substitutes=True,support_queries=queries,denied_slots=denied,numerical_admitted=not mandatory_bad,
        rule='Incomplete/failed census or unsupported required MQ/PQ/QB/QH_C or any q1 control stops numerical admission. Unsupported q>1 QH_D stays planned NOT_SUPPORTED, no silent removal.')
def analyze(root,f0,plan,refs,expected):
    prior={};rows=[];failure=None
    decision=load(root/'CENSUS_DECISION.json') if (root/'CENSUS_DECISION.json').exists() else None
    denied=set(decision['denied_slots']) if decision else set()
    for s in plan['numerical_slots']:
        d=root/'numerical'/('%03d'%s['index'])
        if s['id'] in denied:state='NOT_SUPPORTED'
        elif (d/'BEFORE_START.json').exists():
            if not (d/'native/RECORD.json').exists():
                state='STARTED_FAILED_OR_INCOMPLETE' if (d/'native.PROCESS.json').exists() else 'RESERVED_FAILED_BEFORE_PROCESS_RECEIPT'
                failure=failure or state
            elif failure is not None:state='STARTED_AFTER_CONTROL_FAILURE_INVALID'
            else:
                try:
                    r=inspect(s,d,f0,plan,refs,expected[s['descriptor'],s['layout']],prior,root);prior[s['descriptor'],s['layout'],s['repeat']]=r;state='COMPLETED_QUALIFIED'
                except Exception as exc:failure=repr(exc);state='CONTROL_FAILED'
        else:
            state='NOT_STARTED_PROTOCOL_STOP' if (root/'NUMERICAL_FAILED.json').exists() or (root/'CENSUS_FAILED.json').exists() else 'NOT_STARTED_CAPABILITY_STOP' if decision and not decision['numerical_admitted'] else 'NOT_STARTED_NOT_AUTHORIZED'
        rows.append(dict(slot=s['id'],descriptor=s['descriptor'],family=s['family'],layer=s['layer'],phase=s['phase'],q=s['q'],layout=s['layout'],repeat=s['repeat'],status=state,
            native_process_started=(d/'native.PROCESS.json').exists(),graph_started=(d/'native/GRAPH_STARTED_0.json').exists(),
            graph_call_return_recorded=(d/'native/GRAPH_CALL_RETURNED.json').exists(),synchronization_return_recorded=(d/'native/SYNCHRONIZATION_RETURNED.json').exists()))
    details=[]
    for descriptor,d in contexts(plan).items():
        entries={};pairs=[];meta=d['metadata']
        for l in LAYOUTS:entries[l]=[prior.get((descriptor,l,r)) for r in (0,1)]
        for repeat in (0,1):
            for left,right in PAIRS:
                a,b=prior.get((descriptor,left,repeat)),prior.get((descriptor,right,repeat))
                if a and b:
                    va=values_for(root/a['directory']/'native',root/'cas',plan['numerical_slots'][a['index']],a['pid'],False);vb=values_for(root/b['directory']/'native',root/'cas',plan['numerical_slots'][b['index']],b['pid'],False)
                    pairs.append(dict(left=left,right=right,repeat=repeat,**relation({s:va[s] for s in STAGES},{s:vb[s] for s in STAGES},meta)))
                else:pairs.append(dict(left=left,right=right,repeat=repeat,qualified=False,relation=None,reason='Missing/unsupported/failed coordinate retained; comparison withheld'))
        details.append(dict(descriptor=descriptor,family=d['family'],layer=d['layer'],phase=d['phase'],q=d['q'],visibility=d['visibility'],layouts=entries,pairwise=pairs))
    return dict(run_id=plan['run_id'],status='COMPLETE_QUALIFIED_PANEL' if len(prior)==720 else 'INCOMPLETE_OR_UNQUALIFIED_PANEL',planned_cells=720,independent_contexts=72,
        counts={k:sum(r[k] for r in rows) for k in ('native_process_started','graph_started','graph_call_return_recorded','synchronization_return_recorded')},
        completed_qualified=len(prior),control_failure=failure,slots=rows,contexts=details,claims=dict(full_request_qualification=False,cost_qualification=False,unseen_prompts=False,universal_equivalence=False,kernel_reduction_tree='UNKNOWN'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    f0=load(V/'F0.json');plan=load(V/'PLAN.json');refs=load(V/'REFERENCE_INDEX.json');expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}
    save(args.output,analyze(args.root,f0,plan,refs,expected))
if __name__=='__main__':main()
