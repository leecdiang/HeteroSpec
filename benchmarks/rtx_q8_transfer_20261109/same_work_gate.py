"""Four-origin eight-row equal-work eligibility; no clean timing in this gate."""
from pathlib import Path
import hashlib,json,sys
from admission import ROOT,put,sha
from execute import WORK,execute
from lifecycle_gate import read,spec,candidate
from active_kv import parse

MANIFEST='JOB_MANIFEST_SAME_WORK_QUALIFICATION.json'

def freeze():
    base=read(ROOT/'JOB_MANIFEST_LIFECYCLE.json');operands=read(ROOT/'DIAGNOSTIC_OPERANDS.json');assert not operands['shortages']
    models={k:v for k,v in base['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))};jobs=[];cases=[]
    for f in operands['fixtures']:
        p=len(f['prefix_ids']);cases.append(dict(name=f"o{f['index']}-{f['geometry']}",forced=[dict(ids=f['prefix_ids'],phase='PREFILL',all=False),dict(ids=f['append_ids'],phase='VERIFY',all=True)],observe_positions=list(range(p,p+9)),state_positions=[p,p+8]))
    for group in range(2):
        cc=cases[group*4:group*4+4];jobs.append(spec('same-work-v2-R-'+str(group),'R',dict(models,lowering='SIMPLE',cases=cc),len(cc),sum(sum(len(c['ids']) for c in one['forced']) for one in cc)))
    for core in ('loop4','packed'):
        probes=[]
        for f in operands['fixtures']:
            for mode in ('q4pair','q8'):probes.append(dict(f,name=f"o{f['index']}-{f['geometry']}-{mode}",execution=mode,capture=True))
        payload=candidate(core,'LOCAL',7,models);payload['same_work']=probes
        jobs.append(spec('same-work-v2-qualification-'+core,core,payload,len(probes),sum(len(p['prefix_ids'])+8 for p in probes)))
    put(ROOT/MANIFEST,dict(base,status='FROZEN_ALL_FOUR_ORIGINS_AND_EIGHT_CELLS',jobs=jobs,requests=sum(j['requests'] for j in jobs),rows=sum(j['rows'] for j in jobs),
        operands_sha256=sha(ROOT/'DIAGNOSTIC_OPERANDS.json'),timing_scope='QUALIFICATION_ONLY: all operation clocks retained but excluded from clean diagnostics'))
    print('Frozen same-work gate',sum(j['requests'] for j in jobs),'requests',flush=True)

def reference(case):
    for group in range(2):
        p=WORK/'runs'/('same-work-v2-R-'+str(group))/'native'/case
        if p.exists():return p
    raise RuntimeError('Missing exact independent same-work reference '+case)

def profile():
    writer=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4/source/src/llama-kv-cache.cpp')
    return dict(format='dense_seq_f16_v1',writer_sha256=sha(writer),layer_map_source_sha256=sha(writer),target_model_sha256=read(ROOT/MANIFEST)['jobs'][0]['job']['target_sha256'],host_writer_reviewed=True,capacity=1024,
        layers=[dict(id=i,k_elements=1024,v_elements=1024) for i in range(36)])

def check_probe(native,p,core):
    case=f"o{p['index']}-{p['geometry']}";ref=reference(case);actual=native/p['name'];r=read(actual/'receipt.json');head=len(p['prefix_ids']);pro=profile()
    assert r['append_ids']==p['append_ids'] and r['position']==head
    rows=[]
    for i in range(8):
        a=actual/f'row-{i}.f32';b=ref/'captures'/str(head+i+1)/'frontier.f32'
        assert a.stat().st_size==b.stat().st_size==151936*4
        rows.append(dict(index=i,equal=a.read_bytes()==b.read_bytes(),actual_sha256=sha(a),reference_sha256=sha(b)))
    assert (actual/'initial-frontier.f32').read_bytes()==(ref/'captures'/str(head)/'frontier.f32').read_bytes()
    states=[]
    for name,n in [('initial',head),('final',head+8)]:
        a=actual/(name+'-sequence.bin');b=ref/'captures'/str(n)/'sequence.bin'
        av,_=parse(a.read_bytes(),list(range(n)),pro);bv,_=parse(b.read_bytes(),list(range(n)),pro)
        states.append(dict(kind=name,equal=av==bv,active_sha256=hashlib.sha256(av).hexdigest(),reference_sha256=hashlib.sha256(bv).hexdigest(),raw_sha256=sha(a)))
    width=8 if p['execution']=='q8' else 4
    assert r['target_physical_width_hist']=={str(width):8//width} and not r['draft_physical_width_hist']
    assert sum(int(k)*v for k,v in r['prefix_physical_width_hist'].items())==head
    assert r['outputs_survive_next_decode_and_plan_clear']
    assert r['timer_exports']==r['timer_imports']==r['timer_context_creates']==0
    executions=r['executions'];assert len(executions)==8//width
    assert sorted(e['position']-head+i for e in executions for i in e['requested_rows'])==list(range(8))
    expected=[p['extent']]*8 if p['geometry']=='within' else [p['extent']]*4+[p['extent']+256]*4
    assert sum((e['expected_extents'] for e in executions),[])==expected
    assert r['prefix_executions'][-1]['actual_attention_extent']==p['extent']
    if p['capture']:
        graph=[x for x in r['geometry_descriptors'] if x['phase']=='VERIFY' and x['op']=='MUL_MAT'];assert graph
        packed=[x for x in graph if x['name'].startswith('frontier_packed_')]
        if p['execution']=='q4pair':assert not packed
        if p['execution']=='q8' and core=='packed':assert packed and all(x['ne'][1:3]==[4,2] for x in packed)
    proof=dict(passed=all(x['equal'] for x in rows+states),rows=rows,states=states,initial_frontier_equal=True,
        physical_hist=r['target_physical_width_hist'],executions=executions,all_eight_rows_owned=True,zero_draft=True,receipt_sha256=sha(actual/'receipt.json'))
    assert proof['passed'],'Equal-work full-vector/KV qualification failed'
    return proof

def main():
    if sys.argv[1]=='freeze':freeze();return
    manifest=read(ROOT/MANIFEST);proofs=[]
    for job in manifest['jobs']:
        native=execute(job,MANIFEST)
        if 'same_work' not in job['job']:continue
        core='packed' if job['id'].endswith('packed') else 'loop4'
        for p in job['job']['same_work']:
            proof=check_probe(native,p,core);put(ROOT/'same_work_checks'/(job['id']+'-'+p['name']+'.json'),proof);proofs.append(proof)
    put(ROOT/'SAME_WORK_QUALIFICATION_COMPLETE.json',dict(passed=True,origins=4,cells=8,candidate_requests=32,independent_R_requests=8,all_rows_and_states=True,proofs=proofs))

if __name__=='__main__':main()
