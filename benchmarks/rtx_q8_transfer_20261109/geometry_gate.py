"""Freeze and execute the first finite, full-output Windows width gate."""
from pathlib import Path
import collections, datetime, hashlib, json, sys, time
from admission import HERE, ROOT, sha, put
from execute import BASE, WORK, execute

def capability(core,cut,k,models):
    gpu='NVIDIA GeForce RTX 5070 Ti Laptop GPU'
    def structure(layers,heads):return dict(layers=layers,query_heads=heads,kv_heads=8,head_k=128,head_v=128,K_elements=1024,V_elements=1024)
    target=structure(36,32);draft=structure(28,16)
    def ctx(ub,n):return dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=n,outputs_per_seq=n,flash_attention=False,type_k='f16',type_v='f16')
    return dict(schema='heterospec.m2.native-capability.v1',target_sha256=models['target_sha256'],draft_sha256=models['draft_sha256'],target_structure=target,draft_structure=draft,
        target_context=ctx(32,8),draft_context=ctx(4,1),target_placement=dict(layers=[gpu]*36,output=gpu),draft_placement=dict(layers=[gpu]*28,output=gpu),
        k=k,draft_width=4,cut=cut,projection=core,proposal_mode='live',target_output_reserve=8,threads=24,greedy=True,
        target_output_policy='PREFILL:last;VERIFY:all_original_rows',draft_output_policy='last',physical_rows_evidence='per-request executions and native physical width histograms')

def freeze():
    inherited=json.loads((ROOT/'CUMULATIVE_LEDGER_INITIAL.json').read_bytes())
    assert inherited['totals']==dict(requests=904,token_rows=557528,operators=0)
    model_file=json.loads((HERE.parent/'tpds_phase1_v1/MODEL_ASSETS.json').read_bytes())['Qwen']
    models={role+suffix:value for role,m in model_file.items() for suffix,value in [('_model','D:/HeteroSpec-PC/models/gguf/'+m['file']),('_sha256',m['sha256'])]}
    original=Path('D:/rtx184-runs/D-main-forced-10/job.json');saved=json.loads(original.read_bytes())['forced'];tape=saved['prompt_ids']+saved['paths'][0]['suffix']
    cases=[]
    for width in (4,8):
        for relation in ('within','cross'):
            p=256-width if relation=='within' else 256-width//2
            cases.append(dict(name=f'{relation}-p{p}-q{width}',forced=[dict(ids=tape[:p],phase='PREFILL',all=False),dict(ids=tape[p:p+width],phase='VERIFY',all=True)],
                observe_positions=list(range(p,p+width+1)),state_positions=[p,p+width]))
    jobs=[]
    def add(label,build,exe,payload,cc):
        jobs.append(dict(id=label,stage='qualification',build=str(build),exe=str(exe),exe_sha256=sha(exe),requests=len(cc),rows=sum(sum(len(x['ids']) for x in c['forced']) for c in cc),job=dict(models,**payload,cases=cc)))
    add('geometry-v1-independent-R',BASE/'R-Qwen/BUILD.json',BASE/'R-Qwen/bin/worker.exe',dict(lowering='SIMPLE'),cases)
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                cc=[c for c in cases if c['name'].endswith('-q'+str(k+1))]
                payload=dict(n_ctx=1024,threads=24,k=k,draft=True,draft_width=4,lowering=cut,residency='matched',profile=False,target_output_reserve=8,proposal_mode='live',capability_request=capability(core,cut,k,models))
                add(f'geometry-v1-{core}-{cut}-k{k}',WORK/core/'BUILD.json',WORK/core/'bin/worker.exe',payload,cc)
    put(ROOT/'JOB_MANIFEST_GEOMETRY.json',dict(status='FROZEN_FINITE_STAGE_B_GEOMETRY_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_sha256=sha(WORK/'SOURCE.json'),fixture_source=str(original),fixture_source_sha256=sha(original),native_extent_expected=256,
        authorization=dict(end='UNLIMITED_USER_AUTHORIZED',timezone='Asia/Shanghai',power_and_performance='KEEP_CURRENT',timeout_seconds=900),
        requests=sum(j['requests'] for j in jobs),rows=sum(j['rows'] for j in jobs),jobs=jobs,
        later_stages='NOT_ADMITTED: full natural/transaction/tape/reset/negative qualification, same-work frontend and exact row manifests must precede clean timing; no timing from this gate'))
    put(ROOT/'PLAN_FREEZE_INITIAL.json',dict(status='ADMISSION_AND_FINITE_GEOMETRY_GATE',design='ad9fb6846dd979c3a76d3c415c74fa9f86565f7d',
        immutable_R=True,reserve8_both_k=True,numerical_core_and_DLL_unchanged=True,
        task_sequence=['Full-vector and active KV geometry against original Windows R (20 requests). Stop at first failed required numerical check.',
        'If geometry passes, implement/freeze remaining complete B manifest within512: four exposed development roots, cap/EOG, all rejection ranks/bonus, pending/rollback, reset, proposal-tape ownership and negatives; bind every actual loaded module.',
        'Freeze exact four-origin equal-work operands and symmetric timer/output ownership;160 clean diagnostic requests after complete qualification.',
        'Reconcile budgets, freeze all64 live workers/1152 requests and independent new R endpoints; confirm complete-panel wall estimate and closure margin before admission.',
        'Run serial; separate optional profiling (<=32); retain failures, all arms, all costs; root-cluster four-contrast analysis; archive readback and offline recomputation.'],
        no_model_output_before_this_freeze=True,new_gpu_requests_before_freeze=0,
        no_optimization_or_favorable_selection=True,full_study_admitted=False))
    print('Frozen geometry',sum(j['requests'] for j in jobs),'requests',sum(j['rows'] for j in jobs),'rows',flush=True)

def check(reference,actual,job):
    import numpy as np
    sys.path.insert(0,str(HERE.parents[2]/'phase188/benchmarks/tpds_decisive_v1'))
    from active_kv import parse
    native=json.loads((actual/'result.json').read_bytes())
    structure=native['model_structure']
    writer=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4/source/src/llama-kv-cache.cpp')
    profile=dict(format='dense_seq_f16_v1',writer_sha256=sha(writer),layer_map_source_sha256=sha(writer),target_model_sha256=job['job']['target_sha256'],host_writer_reviewed=True,capacity=1024,
        layers=[dict(id=i,k_elements=structure['K_elements'],v_elements=structure['V_elements']) for i in range(structure['layers'])])
    rows=[]
    for index,case in enumerate(job['job']['cases']):
        for p in case['observe_positions']:
            a=actual/case['name']/'captures'/str(p);b=reference/case['name']/'captures'/str(p)
            av=(a/'frontier.f32').read_bytes();bv=(b/'frontier.f32').read_bytes();assert len(av)==len(bv)==151936*4
            row=dict(case=case['name'],prefix=p,full_vector_equal=av==bv,actual_sha256=hashlib.sha256(av).hexdigest(),reference_sha256=hashlib.sha256(bv).hexdigest())
            if av!=bv:
                x=np.frombuffer(av,dtype='<f4');y=np.frombuffer(bv,dtype='<f4');diff=np.flatnonzero(x.view('u4')!=y.view('u4'));i=int(diff[0]);row['difference']=dict(entries=int(len(diff)),first=i,actual=float(x[i]),reference=float(y[i]),max_abs=float(np.max(np.abs(x-y))))
            if p in case['state_positions']:
                ax,am=parse((a/'sequence.bin').read_bytes(),list(range(p)),profile);bx,bm=parse((b/'sequence.bin').read_bytes(),list(range(p)),profile)
                row['active_KV_equal']=ax==bx;row['active_bytes']=len(ax)
            rows.append(row)
    passed=all(r['full_vector_equal'] and r.get('active_KV_equal',True) for r in rows)
    proof=dict(passed=passed,reference=str(reference),actual=str(actual),rows=rows,scalar_R_unchanged=True,
        tolerance='Original Windows bitwise full-F32 vector and active F16 KV equality; no tolerance relaxation',qualification_scope='Finite forced append geometry only; not complete B qualification')
    put(ROOT/(job['id']+'-CHECKED.json'),proof)
    assert passed,'Required full-vector/KV geometry gate failed; retain and stop all clean stages'

def main():
    if sys.argv[1]=='freeze':freeze();return
    jobs=json.loads((ROOT/'JOB_MANIFEST_GEOMETRY.json').read_bytes())['jobs'];reference=None
    for job in jobs:
        actual=execute(job)
        if reference is None:reference=actual
        else:check(reference,actual,job)
    put(ROOT/'GEOMETRY_COMPLETE.json',dict(passed=True,requests=20,full_stage_B_qualified=False))

if __name__=='__main__':main()
