"""Freeze, then select eight unseen requests and run one prespecified cost panel."""
import collections, math
from execute import *
from audit import unpack
from prepare_pool import digest
CAND='shared-01'
REF='original-final'
ARMS=['R','M_PQ','M_QB','C_PQ','C_QB']
def freeze():
    proofs=[]
    for i in IDS:
        p=ROOT/'units'/f'retained-{i}-{CAND}'/'COMPARISON.json'
        d=read(p);assert all(x['endpoint_equal'] and x['all_committed_equal'] and x['equals_historical_P1'] for x in d['cells']) and all(d['PQ_QB_full_correspondence'].values())
        proofs.extend([p,ROOT/'units'/f'original-{REF}-{i}/ORIGINAL_COMPARISON.json'])
    for p,status in [(ROOT/'units'/('probe-'+CAND)/'PROBE_AUDIT.json','PHYSICAL_BOUNDARY_AND_POLICY_REUSE_PASS'),(ROOT/'units'/('precision-off-'+CAND)/'REVERSAL_AUDIT.json','HISTORICAL_P1_PQ_FAILURE_RESTORED'),(ROOT/'units/llama-controls-01/REGRESSION.json','TWO_LLAMA_CONTROLS_PASS')]:
        assert read(p)['status']==status;proofs.append(p)
    proofs.extend([ROOT/b/'FILES.json' for b in (REF,CAND)]+[ROOT/'MODEL_PINS.json',ROOT/'source-01/SHARED_PLANNER_SOURCE.json'])
    for rel in ['ggml/src/ggml-vulkan/ggml-vulkan.cpp','src/llama-graph.cpp','src/llama-graph.h','src/llama-kv-cache.cpp','src/hs_reference_batching.hpp']:
        proofs.append(ROOT/'source-01'/rel)
    assert not LOCK.exists()
    source_paths=['scripts/b570_qwen_transfer','src/reference_batching']
    subprocess.run(['git','diff','--quiet','HEAD','--',*source_paths],check=True)
    assert not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*source_paths]).strip()
    write(ROOT/'FREEZE.json',dict(utc=now(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],controls='All retained cases, precision reversal, observed prefix split/reuse, two Llama controls and original R adapter verified.',mapping={'producer':'uniform P4T for all integrated candidate arms','precision':True,'prefix':True,'target_gpu_layers':999,'draft_gpu_layers':999,'threads':8,'k':1,'cap':128,'R':'original PR152 scalar UB1, original numerical DLLs'},cost={'sessions':3,'inputs':8,'arms':ARMS,'pairs':120,'no_extension':True},selection={'near':'four natural prompts at244..255','ordinary':'two code and two math, next padding boundary at least64 positions away','reason':'pinned pool has37 near math and no near code; retain multi-domain ordinary coverage'},no_unseen_outputs=True))
def select():
    freeze_file=ROOT/'FREEZE.json';assert freeze_file.is_file()
    rows=read(ROOT/'pool-00/POOL.json')['rows']
    groups=[[x for x in rows if x['band']=='near'],*[ [x for x in rows if x['band']=='ordinary' and x['domain']==d and 256-x['prompt_tokens']%256>=64] for d in ('code','math')]]
    panel=[]
    for g,n in zip(groups,[4,2,2]):
        g.sort(key=lambda x:digest(['qwen-shared-v1',x['id'],x['prompt_ids_sha256']]))
        assert len(g)>=n;panel+=g[:n]
    assert len({x['id'] for x in panel})==len({x['prompt_ids_sha256'] for x in panel})==8
    write(ROOT/'UNSEEN.json',{x['id']:x for x in panel})
    schedule=[]
    for s in range(3):
        session=sorted(panel,key=lambda x:digest(['qwen-cost-v1',s,x['id']]))
        for x in session:
            rotation=(int(digest(x['id'])[:8],16)+s)%5
            for j in (0,1,4,2,3):
                schedule.append(dict(session=s,id=x['id'],arm=ARMS[(rotation+j)%5]))
    assert len(schedule)==120
    write(ROOT/'COST_ORDER.json',schedule)
    write(ROOT/'SELECTION.json',dict(utc=now(),freeze_sha256=sha(freeze_file),pool_sha256=sha(ROOT/'pool-00/POOL.json'),panel_sha256=sha(ROOT/'UNSEEN.json'),order_sha256=sha(ROOT/'COST_ORDER.json'),count=8,new_model_outputs=0))
def slot(x,arm,stage,*,clean=False,phase=False):
    n=x['prompt_tokens'];scalar=arm=='R'
    lengths=[1]*n if scalar else [4]*(n//4)+([2,1] if n%4==3 else [n%4] if n%4 else [])
    layout='QB' if arm.endswith('QB') else 'PQ'
    return dict(slot_id=stage+'/'+arm,input_id=x['id'],prompt_ids_sha256=x['prompt_ids_sha256'],cap=128,k=int(arm.startswith('C')),target_ub=1 if scalar else 4,caller_lengths=lengths,producer='P1' if scalar else 'P4T',producer_layout=layout,consumer='C1' if scalar else layout,route='strict_reference' if scalar else 'natural',observer='off' if clean else 'heavy',clean=clean,phase_clocks=phase,trace=False,stage=stage,compare_slot_id=None,donor_slot_id=None,producer_match_slot_id=None)
def check_seal():
    s=read(ROOT/'SELECTION.json')
    for name,key in [('FREEZE.json','freeze_sha256'),('UNSEEN.json','panel_sha256'),('COST_ORDER.json','order_sha256')]:assert sha(ROOT/name)==s[key]
    for f in read(ROOT/'FREEZE.json')['proofs']:assert sha(f['path'])==f['sha256']
def unit(name,build,slots,pred):
    d=ROOT/'units'/name
    if d.exists():
        assert read(d/'RECEIPT.json')['success'] and read(d/'JOB.json')['slots']==slots
        return read(d/'native/result.json')['requests']
    return record_unit(name,build,slots,ROOT/'UNSEEN.json',pred)['requests']
def qualify():
    check_seal();results=[];panel=read(ROOT/'UNSEEN.json')
    for i,x in enumerate(panel.values()):
        ref=unit(f'qual-{i}-R',REF,[slot(x,'R','qualification')],'Unseen scalar R, exact original numeric contract.')[0]
        arms=ARMS[1:];slots=[slot(x,a,'qualification') for a in arms]
        if i==0:slots.append(slot(x,'C_QB','observer-control',clean=True))
        rows=unit(f'qual-{i}-candidate',CAND,slots,'Uniform P4T target phases; Q8 projection predicted for batched roles. Split only on reached physical boundary; all committed decisions expected equal scalar R.')
        reference=unpack(ref,ROOT/f'units/qual-{i}-R/payload')
        for arm,row in zip(arms,rows[:4],strict=True):
            v=unpack(row,ROOT/f'units/qual-{i}-candidate/payload')
            results.append(dict(input=x['id'],arm=arm,endpoint_equal=row['endpoint']==ref['endpoint'],committed_vectors=len(v),all_committed_equal=v==reference,saved_vectors=len(row['vectors'])))
        for a,b in [(rows[0],rows[1]),(rows[2],rows[3])]:assert a['cycles']==b['cycles'] and a['vectors']==b['vectors']
        if i==0:assert rows[3]['endpoint']==rows[4]['endpoint'] and rows[3]['cycles']==rows[4]['cycles']
    ok=all(r['endpoint_equal'] and r['all_committed_equal'] for r in results)
    write(ROOT/'QUALIFICATION.json',dict(status='PASS' if ok else 'COUNTEREXAMPLE',cells=results,requests=41,reference_inputs=8,matched_full_vectors_and_transactions=True));assert ok
def timing():
    check_seal();assert read(ROOT/'QUALIFICATION.json')['status']=='PASS'
    panel=read(ROOT/'UNSEEN.json');idx={k:i for i,k in enumerate(panel)}
    for j,b in enumerate(read(ROOT/'COST_ORDER.json')):
        x=panel[b['id']];a=b['arm'];ref=read(ROOT/f'units/qual-{idx[x["id"]]}-R/native/result.json')['requests'][0]
        rows=unit(f'cost-{j:03d}',REF if a=='R' else CAND,[slot(x,a,s,clean=True) for s in ('warmup','measured')],'Registered immediate same-arm warmup then measurement; both must reproduce qualified R.')
        for row in rows:
            assert row['endpoint']==ref['endpoint'] and row['performance_eligible'] and not row['vectors'] and math.isfinite(row['service_seconds']) and row['service_seconds']>0;unpack(row)
def phases():
    assert read(ROOT/'QUALIFICATION.json')['status']=='PASS'
    x=next(iter(read(ROOT/'UNSEEN.json').values()))
    for a in ('R','M_QB','C_QB'):
        row=unit('phase-'+a,REF if a=='R' else CAND,[slot(x,a,'phase',clean=True,phase=True)],'Separate predeclared first-panel-input phase diagnostic; exclude from all formal timing.')[0]
        assert row['phase_seconds'] and not row['performance_eligible'] and row['endpoint']==read(ROOT/'units/qual-0-R/native/result.json')['requests'][0]['endpoint']
if __name__=='__main__':
    {'freeze':freeze,'select':select,'qualify':qualify,'time':timing,'phases':phases}[sys.argv[1]]()

