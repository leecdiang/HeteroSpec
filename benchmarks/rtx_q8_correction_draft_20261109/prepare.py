"""Complete a reviewable correction plan; no native/GPU launch code."""
from pathlib import Path
import collections,copy,ctypes,datetime,hashlib,json,shutil,sqlite3,subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
AUDIT=REPO.parent/'q8rtx213-audit/benchmarks/rtx_q8_freeze_audit_20261109'
ORIGINAL=REPO.parent/'q8rtx211/benchmarks/rtx_q8_transfer_20261109/results_20261109'
WORK=Path('D:/rtx211-q8-20261109')
RUNTIME=REPO.parent/'q8rtx213-supplement-runtime-20261109'
AUDIT_PIN='4da44bc0882d3d0a6c1ac72399091ab19825199c'

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def put(name,value):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(value,f,indent=2,ensure_ascii=False)
def db_rows(p):
    c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    rows=[dict(x) for x in c.execute('SELECT * FROM attempts ORDER BY started')];c.close();return rows

def main():
    old=read(AUDIT/'evidence/OPTIONAL_SUPPLEMENT_DRAFT.json');assert old['status']=='OFFLINE_DRAFT_ONLY_NOT_AUTHORIZED_TO_RUN'
    raw_plan=subprocess.check_output(['git','-C',str(REPO),'show',AUDIT_PIN+':benchmarks/rtx_q8_freeze_audit_20261109/evidence/OPTIONAL_SUPPLEMENT_DRAFT.json'])
    assert json.loads(raw_plan)==old
    prior=read(ORIGINAL/'CUMULATIVE_LEDGER_INITIAL.json');latest=read(ORIGINAL/'CUMULATIVE_LEDGER.json')
    assert sha(Path(prior['source']))==prior['sha256'] and sha(WORK/'ledger.sqlite')==latest['source_new_ledger_sha256']
    entries=db_rows(WORK/'ledger.sqlite');assert len(entries)==183
    req=sum(a['requests'] for a in entries);rows=sum(a['rows'] for a in entries);qual=sum(a['requests'] for a in entries if a['stage']=='qualification')
    assert (req,rows,qual)==(1775,2296770,463) and prior['totals']['requests']==904 and prior['totals']['token_rows']==557528
    ledger=dict(as_of_bjt=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        legacy=dict(path=prior['source'],sha256=prior['sha256'],requests=904,rows=557528),
        epoch=dict(path=str(WORK/'ledger.sqlite'),sha256=sha(WORK/'ledger.sqlite'),requests=req,rows=rows,qualification_requests=qual),
        cumulative_requests=2679,cumulative_rows=2854298,new_tranche_requests=1775,
        reconciliation='Both known RTX ledgers read-only; no later entries in these pinned ledgers. Executor must discover/reconcile any other or concurrent RTX epoch before admission.',
        new_GPU_requests_this_preparation=0,original_ledgers_unchanged=True)
    put('LEDGER_SNAPSHOT.json',ledger)
    jobs=[]
    for role,items in [('reference',old['reference_jobs']),('candidate',old['candidate_jobs'])]:
        for n,j in enumerate(items):
            exe=Path(j['exe']);assert sha(exe)==j['exe_sha256']
            name=f'rtx213-s1-R-{n:02d}' if role=='reference' else 'rtx213-s1-'+j['id'].removeprefix('SUPPLEMENT-NOT-RUN-')
            original_folder=exe.parent.parent;build=original_folder/'BUILD.json';assert read(build)['exe']==j['exe_sha256']
            item=dict(id=name,source_draft_id=j['id'],stage='qualification',role=role,order=len(jobs),
                exe=str(exe),exe_sha256=j['exe_sha256'],build=str(build),build_sha256=sha(build),requests=j['requests'],rows=j['conservative_rows'],
                job=copy.deepcopy(j['job']),native_job_sha256=canonical(j['job']),output=str(RUNTIME/'runs'/name),max_attempts=1)
            if role=='candidate':item['predicted_capture_bytes']=j['predicted_capture_bytes']
            jobs.append(item)
    assert len(jobs)==16 and sum(j['requests'] for j in jobs)==37 and sum(j['rows'] for j in jobs)==18543
    put('JOB_MANIFEST.json',dict(schema='heterospec.rtx213.correction-draft.v1',status='DRAFT_NOT_EXECUTED',authorization='DRAFT_PREPARATION_ONLY_GPU_NOT_AUTHORIZED',
        parent_audit_commit=AUDIT_PIN,parent_draft_sha256=sha(AUDIT/'evidence/OPTIONAL_SUPPLEMENT_DRAFT.json'),
        qualification_only=True,performance_estimand=None,root=old['selected_root'],output_root=str(RUNTIME),
        all_inputs_prebound=True,reference_first=True,candidate_order='Preserve first original Williams row:0,1,7,2,6,3,5,4; no outcome-based reorder',jobs=jobs,
        budget=old['budget'],original_clean_bindings=old['original_clean_bindings'],new_GPU_requests=0))
    # Reconstruct all numerical lookup prefixes and the complete old branch trace.
    wanted={};states={};crossings=[];traces=[];fixed=read(ORIGINAL/'JOB_MANIFEST_LIVE.json')['jobs']
    for binding,candidate in zip(old['original_clean_bindings'],jobs[8:]):
        folder=WORK/'runs'/binding['original_worker'];p=folder/'native'/binding['item']/'receipt.json';assert sha(p)==binding['clean_receipt_sha256']
        original_job=next(j for j in fixed if j['id']==binding['original_worker']);x=next(e['input'] for e in original_job['job']['inputs'] if e['name']==binding['item'])
        assert x==old['selected_root']==candidate['job']['inputs'][0]['input']
        r=read(p);prefix=list(x['prompt_ids']);wanted[tuple(prefix)]='initial';states[tuple(prefix)]='initial'
        ex=iter(e for e in r['executions'] if e['phase']=='VERIFY')
        for c in r['cycles']:
            full=prefix+[c['seed']]+c['proposals'];wanted.update({tuple(full[:len(prefix)+i]):f"cycle{c['cycle']}/row{i-1}" for i in range(1,r['k']+2)})
            prefix=full[:c['keep']];states[tuple(prefix)]=f"commit{c['cycle']}";count=0;extent=[]
            while count<r['k']+1:e=next(ex);count+=e['width'];extent+=e['expected_extents']
            if len(set(extent))>1:crossings.append(dict(job=candidate['id'],cycle=c['cycle'],base=c['base'],accepted=c['accepted'],rejected=c['rejected'],extents=extent,keep=c['keep']))
        traces.append(dict(job=candidate['id'],old_worker=binding['original_worker'],old_item=binding['item'],old_receipt_sha256=sha(p),
            old_clean_endpoint=r['endpoint'],expected_cycles=r['cycles'],expected_executions=r['executions'],
            expected_target_hist=r['target_physical_width_hist'],expected_draft_hist=r['draft_physical_width_hist'],
            comparison_scope='Full semantic equality only; do not require new timing, graph counts or heavy capture counters to equal old clean values.'))
    lookup={};state_lookup={}
    for j in jobs[:8]:
        for case in j['job']['cases']:
            tape=sum((f['ids'] for f in case['forced']),[])
            for n in case['observe_positions']:
                key=tuple(tape[:n]);assert key in wanted or key in states
                assert key not in lookup,'Reference observation duplicated rather than assigned once'
                lookup[key]=dict(job=j['id'],case=case['name'],position=n,vector_relative=f"{case['name']}/captures/{n}/frontier.f32")
                if n in case['state_positions']:state_lookup[key]=dict(lookup[key],state_relative=f"{case['name']}/captures/{n}/sequence.bin")
    assert set(lookup)==set(wanted)|set(states) and set(state_lookup)==set(states)
    assert len(wanted)==257 and len(states)==40 and len(lookup)==257
    put('REFERENCE_COVERAGE.json',dict(passed_offline_only=True,unique_full_vectors=257,unique_active_state_prefixes=40,independent_R_cases=29,
        vector_map=[dict(prefix_ids=list(k),**v) for k,v in sorted(lookup.items())],state_map=[dict(prefix_ids=list(k),**v) for k,v in sorted(state_lookup.items())],
        target_boundary_cycles=crossings,old_trace_bindings=traces,new_numerical_qualification_pass=None,new_GPU_requests=0))
    payload=old['projected_raw_payload_bytes'];minimum_free=3*payload+2*1024**3+10*1024**3
    resource=dict(as_of_bjt=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        C_free_bytes=shutil.disk_usage('C:/').free,D_free_bytes=shutil.disk_usage('D:/').free,proposed_output_root=str(RUNTIME),
        proposed_runtime_directory_exists=RUNTIME.exists(),predicted_payload_bytes=payload,
        conservative_C_admission_free_bytes=minimum_free,storage_rule='10GiB floor +3x predicted raw payload for runtime/archive/full restore +2GiB metadata margin; no compression/deduplication saving assumed.',
        draft_storage_fits=shutil.disk_usage('C:/').free>=minimum_free,
        GPU_admission='NOT_PERFORMED: no GPU/native invocation. UUID, AC/mode, current compute processes, VRAM/RAM, mutex and time must be checked at actual admission.',
        original_output_floor_bytes=20*1024**3,new_GPU_requests=0)
    put('RESOURCE_DRAFT.json',resource)
    put('OFFLINE_VALIDATION.json',dict(passed=True,scope='Static source/input/coverage/budget validation only, not native numerical qualification.',
        exact_jobs=16,logical_requests=37,conservative_rows=18543,reference_vectors=257,state_prefixes=40,
        reference_cases=29,candidate_arms=8,frozen_boundary_cycle_obligations=len(crossings),
        first_boundary_rejection_k3=any(c['rejected'] and '-k3' in c['job'] for c in crossings),
        first_boundary_rejection_k7=any(c['rejected'] and '-k7' in c['job'] for c in crossings),
        projected_stage_requests=500,qualification_limit=512,remaining_stage_requests=12,projected_cumulative_requests=2716,projected_cumulative_rows=2872841,
        no_borrowing=True,no_refund=True,no_automatic_retry=True,original_ledger_hashes_unchanged=True,new_GPU_requests=0))
    print(json.dumps(dict(draft='READY_FOR_REVIEW_NOT_EXECUTED',jobs=16,requests=37,rows=18543,reference_vectors=257,state_prefixes=40,C_free_GiB=resource['C_free_bytes']/1024**3,C_admission_GiB=minimum_free/1024**3,new_GPU_requests=0)),flush=True)

if __name__=='__main__':main()
