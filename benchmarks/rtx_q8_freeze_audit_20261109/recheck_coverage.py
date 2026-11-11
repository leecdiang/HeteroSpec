"""Check actual coverage, fixture dataflow and immutable runtime/source bindings."""
from pathlib import Path
import collections,json,time
from core import RECORDS,WORK,ARCHIVE,ORIGINAL,OUT,PIN,R_SHA,read,put,git,digest,ledger

def bindings():
    start=time.monotonic();archive=read(RECORDS/'ARCHIVE_READBACK.json');idxraw=(ARCHIVE/'ARCHIVE_INDEX.json').read_bytes();assert digest(idxraw)==archive['index_sha256']
    # Bind metadata to the reviewed public commit, not only local pass files.
    rel='benchmarks/rtx_q8_transfer_20261109/results_20261109/'
    assert json.loads(git('show',PIN+':'+rel+'ARCHIVE_READBACK.json'))==archive
    bound=read(RECORDS/'SOURCE_BINDINGS.json');files=[]
    for p,meta in bound['files'].items():
        h=digest(Path(p).read_bytes());assert h==meta['sha256'];files.append(dict(path=p,sha256=h,role=meta['role']))
    original=Path('D:/rtx192-review-v2/R-Qwen/bin/worker.exe');assert digest(original.read_bytes())==R_SHA
    source=read(WORK/'SOURCE-v2.json')
    for name,h in source['frontend'].items():assert digest((WORK/'frontend-v2'/name).read_bytes())==h
    versions=collections.defaultdict(lambda:dict(qualification_workers=[],diagnostic_workers=[],live_workers=[]));module_sets={}
    for a in ledger():
        j=read(WORK/'runs'/a['id']/'JOB.json');assert digest(Path(j['exe']).read_bytes())==j['exe_sha256']
        if j['exe_sha256']!=R_SHA:
            versions[j['exe_sha256']][a['stage']+'_workers'].append(a['id'])
        p=WORK/'runs'/a['id']/'ACTUAL_MODULES.json'
        if p.exists():module_sets[a['id']]=read(p)
    raw_modules=read(WORK/'runs/live-s0-p0-a0/ACTUAL_MODULES.json')
    # Existing loaded-module records are evidence of reported load identity;
    # they cannot establish historical in-memory contents independently.
    put('SOURCE_RUNTIME_RECHECK.json',dict(passed=True,source_files_rehashed=len(files),files=files,versions=dict(versions),loaded_module_records_read=len(module_sets),
        module_record_example=raw_modules,reference_executable_sha256=R_SHA,source_v2_sha256=digest((WORK/'SOURCE-v2.json').read_bytes()),archive_index_sha256=digest(idxraw),
        limits='Current bytes and original load inventories are rechecked; no independent historical process-memory attestation or new model execution.',wall_seconds=time.monotonic()-start,new_GPU_requests=0))

def gates():
    attempts=ledger();jobs={a['id']:read(WORK/'runs'/a['id']/'JOB.json') for a in attempts}
    assert len({a['id'] for a in attempts})==183 and {p.name for p in (WORK/'runs').iterdir() if p.is_dir()}==set(jobs),'Unledgered/duplicate run directory'
    assert collections.Counter(a['status'] for a in attempts)=={'COMPLETE':175,'EXPECTED_REJECT':8}
    roots=read(RECORDS/'QUALIFICATION_TASKS.json')['roots'];old=read('D:/rtx188/Qwen-EXPOSED-ROOTS.json')['inputs']
    assert len(roots)==4 and [x['id'] for x in roots]==[x['id'] for x in old]
    for i,(a,b) in enumerate(zip(roots,old)):assert a['prompt_ids']==b['prompt_ids'] and a['cap']==(128 if i==0 else 32)
    controls=[];bridges=[];tape_vectors=0;tape_missing_producer_bytes=0
    greedy=read(WORK/'runs/lifecycle-v2-R-free-r0/native/free/receipt.json')['ids'];root0=roots[0]
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                natural=jobs[f'lifecycle-v2-{core}-{cut}-k{k}'];entries=natural['job']['inputs']
                assert [(e['input']['id'],e['input']['cap'],e['capture']) for e in entries]==sum(([(x['id'],x['cap'],True),(x['id'],x['cap'],False)]+([(x['id'],1,True),(x['id'],1,False)] if i==0 else []) for i,x in enumerate(roots)),[])
                cj=jobs[f'extra-v2-controls-{core}-{cut}-k{k}'];expected=[(f'reject-{r}',r+2,r) for r in range(k)]+[(f'cap-{cap}',cap,None) for cap in range(2,k+2)]+[('bonus',k+2,None),('cap1',1,None),('bonus-resume',k+3,None),('correction-resume',k+3,0)]
                assert len(cj['job']['inputs'])==len(expected)
                for entry,(name,cap,reject) in zip(cj['job']['inputs'],expected):
                    assert entry['name']==name and entry['input']['cap']==cap
                    tape=entry['input']['proposal_tape'];assert tape['prompt_ids']==root0['prompt_ids']
                    for i,row in enumerate(tape['rows']):
                        want=greedy[i+1:i+8].copy()
                        if i==0 and reject is not None:want[reject]=(want[reject]+1)%151936
                        assert row==dict(base=len(root0['prompt_ids'])+i,seed=greedy[i],proposals=want)
                    controls.append(dict(arm=f'{core}-{cut}-k{k}',case=name,cap=cap,R_only_construction=True))
                for j in (natural,jobs[f'extra-v2-EOG-{core}-{cut}-k{k}'],jobs[f'tapes-v2-replay-{core}-{cut}-k{k}']):
                    for heavy in [e for e in j['job']['inputs'] if e['capture']]:
                        clean=next(e for e in j['job']['inputs'] if e['name']==heavy['name'].replace('heavy','clean'))
                        a=read(WORK/'runs'/j['id']/'native'/heavy['name']/'receipt.json');b=read(WORK/'runs'/j['id']/'native'/clean['name']/'receipt.json')
                        assert heavy['input']==clean['input']
                        for field in ('ids','eog','endpoint','cycles','target_final_kv','draft_final_kv','executions','target_physical_width_hist','draft_physical_width_hist'):
                            assert a[field]==b[field],('Heavy/clean semantic mismatch',j['id'],heavy['name'],field)
                        bridges.append(dict(job=j['id'],heavy=heavy['name'],clean=clean['name'],semantic_fields_equal=True))
                producer=read(RECORDS/'OWNED_TAPES.json')['tapes']
                for index in range(5):
                    j=natural if index<4 else jobs[f'extra-v2-EOG-{core}-{cut}-k{k}'];name=f'r{index}-heavy' if index<4 else 'eog-heavy';native=WORK/'runs'/j['id']/'native'/name
                    r=read(native/'receipt.json');tape=producer[str(index)]['tape'];bybase={x['base']:x for x in tape['rows']}
                    for c in r['cycles']:
                        t=bybase[c['base']];assert c['seed']==t['seed'] and c['proposals']==t['proposals'][:k]
                        for z in range(k):assert digest((native/'draft'/f"proposal-{c['cycle']}-{z}.f32").read_bytes())==t['proposal_vector_sha256'][z];tape_vectors+=1
                tape_missing_producer_bytes=5
    rjobs=[j for j in jobs.values() if j['exe_sha256']==R_SHA]
    assert all(set(j['job'])<=set(('target_model','draft_model','target_sha256','draft_sha256','lowering','inputs','cases')) for j in rjobs)
    for j in rjobs:
        for case in j['job'].get('cases',[]):
            assert set(case)<=set(('name','forced','observe_positions','state_positions'))
            assert all(isinstance(v,int) and 0<=v<151936 for c in case['forced'] for v in c['ids'])
    # Recompute all equal-work timings directly from worker receipts, retaining
    # the unfavorable single-origin cell rather than read summary pass flags.
    manifest=read(RECORDS/'JOB_MANIFEST_DIAGNOSTIC_CLEAN.json');sums=collections.defaultdict(lambda:[0.,0.]);per=collections.defaultdict(lambda:[0.,0.]);probes=[]
    for j in manifest['jobs']:
        assert read(WORK/'runs'/j['id']/'JOB.json')==j
        for p in j['job']['same_work']:
            r=read(WORK/'runs'/j['id']/'native'/p['name']/'receipt.json')
            probes.append((p['origin'],p['geometry'],j['projection'],p['execution'],p['kind']))
            if p['kind']!='measurement':continue
            z=0 if p['execution']=='q4pair' else 1;key=(j['projection'],p['geometry']);sums[key][z]+=r['operation_seconds'];per[key+(p['origin'],)][z]+=r['operation_seconds']
    summary=read(RECORDS/'SAME_WORK_RESULTS.json')
    for r in summary['tables']:
        a,b=sums[(r['projection'],r['geometry'])];assert abs(a-r['q4pair_total_s'])<1e-12 and abs(b-r['q8_total_s'])<1e-12
    put('COVERAGE_DATAFLOW_RECHECK.json',dict(passed=True,all_run_directories_accounted=True,status_counts=dict(collections.Counter(a['status'] for a in attempts)),
        development_roots=[dict(id=x['id'],tokens=len(x['prompt_ids']),cap=x['cap']) for x in roots],historical_long_failure_root_retained=True,
        controlled_cases=controls,controlled_fixture_token_construction_recomputed=True,reference_input_scope='R receives only models/token IDs/positions and capture selection; no candidate floats/expected values. Forced R paths are selected from candidate trace by the declared coverage factory and thus outcome-dependent inputs.',
        heavy_clean_bridges=bridges,live_proposal_vectors_rehashed=tape_vectors,producer_roots_with_only_hash_exports=tape_missing_producer_bytes,
        same_work_cells=[dict(projection=k[0],geometry=k[1],q4pair_s=v[0],q8_s=v[1],change_pct=(v[1]/v[0]-1)*100) for k,v in sums.items()],
        same_work_per_origin=[dict(projection=k[0],geometry=k[1],origin=k[2],q4pair_s=v[0],q8_s=v[1],change_pct=(v[1]/v[0]-1)*100) for k,v in per.items()],
        limitations='No claim of never-tried unlogged inputs; no native negative rerun; no producer full-vector byte exports to reread. Finite stored coverage only.',new_GPU_requests=0))

if __name__=='__main__':
    bindings();print('BINDINGS_RECHECK',flush=True);gates();print('COVERAGE_DATAFLOW_RECHECK',flush=True)
