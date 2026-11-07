"""Frozen six-arm Williams confirmation; no candidate rebuild or timing retry."""
from develop import *
from confirmation_select import DEST,SEED,save
from normalize import trace_from_row
from itertools import combinations
import datetime,sqlite3

ARMS=['SIMPLE-M','LOCAL-M','SIMPLE-D1','LOCAL-D1','SIMPLE-D4','LOCAL-D4']
WILLIAMS=[[(v+s)%6 for v in [0,1,5,2,4,3]] for s in range(6)]

def inputs():return json.loads((DEST/'PANELS.json').read_bytes())

def prepare():
    data=inputs();assert all(len(rs)==8 for rs in data.values())
    for family in data:
        for arm in ARMS:assert json.loads((ROOT/f'{family}-{arm}-QUALIFICATION.json').read_bytes())['passed']
    matrix=json.loads((ROOT/'EXACT_FINAL_MATRIX_COMPLETE.json').read_bytes());assert matrix['cells_per_lowering']==48
    frozen=json.loads((ROOT/'SHARED_RULE_FREEZE.json').read_bytes())
    for row in matrix['actual_GPU_qualification_receipts']:
        p=Path(row['path']);assert sha(p)==row['sha256'];q=json.loads(p.read_bytes());assert q['all_passed']
        assert json.loads((Path(q['candidate'])/'binding.json').read_bytes())==frozen['runtimes'][row['method']]['build']
    assert (ROOT/'ZERO_CHANGE_SMOL_TRANSFER.json').exists()
    for family in data:
        for method in ('SIMPLE','LOCAL'):
            trace=json.loads((ROOT/f'{family}-{method}-CUDA-TRACE.json').read_bytes())
            assert trace['dropped_records']==0 and trace['endpoint_prefix_matches_independent_original_R']
    from collections import Counter
    assert set(Counter((r[i],r[i+1]) for r in WILLIAMS for i in range(5)).values())=={1}
    schedule=[]
    for session in range(6):
        for family in (['Qwen','Smol'] if session%2==0 else ['Smol','Qwen']):
            order=sorted(range(8),key=lambda i:hashlib.sha256(f'{SEED}|order|{session}|{family}|{data[family][i]["id"]}'.encode()).hexdigest())
            for ix in order:
                for arm_index in WILLIAMS[(session+ix)%6]:
                    arm=ARMS[arm_index];schedule.append(dict(label=f'confirm-s{session}-{family}-r{ix}-{arm}',session=session,family=family,root_index=ix,root=data[family][ix]['id'],arm=arm))
    assert len(schedule)==576
    # Ceilings include every failed/teacher/warm request already reserved.
    db=sqlite3.connect(ROOT/'ledger.sqlite');used=db.execute('select sum(requests),sum(token_rows),sum(operators) from attempts').fetchone();db.close()
    rows=0
    for s in schedule:
        r=data[s['family']][s['root_index']];n=len(r['prompt_ids']);draft=not s['arm'].endswith('-M');rows+=2*(n+(n+8*127 if draft else 127))
    rrows=sum(len(r['prompt_ids'])+127 for rs in data.values() for r in rs)
    assert used[0]+1152+16<=LIMITS['requests'] and used[1]+rows+rrows<=LIMITS['token_rows']
    plan=dict(arms=ARMS,sessions=6,natural_roots_per_family=8,families=['Qwen','Smol'],balanced_domains_per_family=dict(math=4,code=4),measurements=576,immediate_same_arm_warmups=576,additional_original_R_clean_requests=16,context=1024,k=3,cap=128,reference_reserve=1,candidate_reserve=4,shared_rule_commit='f9c9289a2fc3516558d12ce15c1fa00f06419a94',runtimes=json.loads((ROOT/'SHARED_RULE_FREEZE.json').read_bytes())['runtimes'],lifecycle='Each arm/root pair uses a fresh worker with both model weights and both contexts provisioned. Immediate same-arm warmup followed by resident measurement on those contexts. No context construction, full-KV export/import or numerical reference replay in service. Model/context setup and warmup retained separately.',reference_scope='Each lane already passed original-R/observer, complete requested-vector and selected committed-state development qualification. New blind roots get independent unchanged original-R free endpoints; every warm/measure endpoint and full producer/pending/termination trace is checked. No full-vector/KV claim is made for clean confirmation slots.',service='Complete synchronized resident service, including reset, planning, requested output copies, decode and teardown; initial plan clock nested in first warm request. Setup outside service is retained, never free.',primary='Per-family ratios of total complete measured resident service: LOCAL-D4/SIMPLE-D4 and LOCAL-D4/min(SIMPLE-M,LOCAL-M). Report BOTH fixed M contrasts with multiplicity adjustment; no corrected-min shortcut.',secondary='Equal-root geometric service ratios; absolute costs, adverse roots, all15 paired contrasts and phase/setup work. Do not pool families or historical samples.',uncertainty='Fixed10000 root-cluster bootstrap draws per family, PCG64 seed SHA256(seed|bootstrap|family) first8bytes little-endian; linear percentile quantiles. Resample8 roots with all6 repetitions and all6 arms together. Primary3 fixed contrasts use Bonferroni98.333333% percentile intervals per contrast within family; all15 descriptive contrasts use Bonferroni99.666667% intervals. Geometric mean of per-root six-session service-sum ratios remains secondary. Bootstrap intervals with8 roots are approximate, no significance target.',failures='Retain every failure, partial output and reservation. A blind numerical/lifecycle mismatch closes this version and stops remaining confirmation; no input replacement or timing retries. Engineering repair cannot replace a completed measurement.',budget=dict(used_before_confirmation=dict(zip(LIMITS,used)),maximum_new_reserved_requests=1168,maximum_new_reserved_rows=rows+rrows,ceilings=LIMITS),GPU_work_stops_after_fixed_confirmation=True)
    save(DEST/'SCHEDULE.json',schedule);save(DEST/'PLAN.json',plan)
    execution_files=['host.py','native_metadata.py','develop.py','confirmation.py','confirmation_select.py','storage.py']
    freeze=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_selection_sha256=sha(DEST/'SOURCE_SELECTION.json'),panels_sha256=sha(DEST/'PANELS.json'),schedule_sha256=sha(DEST/'SCHEDULE.json'),plan_sha256=sha(DEST/'PLAN.json'),shared_rule_freeze_sha256=sha(ROOT/'SHARED_RULE_FREEZE.json'),implementation_files={name:sha(HERE/name) for name in execution_files},inherited_execution_files={name:sha(PREVIOUS/name) for name in ['normalize.py','trace.py','common.py','runner.py','active_kv.py']},test_forward_outputs=0,all_controls_retained=True)
    if not (DEST/'FREEZE.json').exists():put(DEST/'FREEZE.json',freeze)
    print('Confirmation frozen:576 measurements+576 warmups;16 independent R requests',flush=True)

def reservation(rows,draft,count=1):
    return dict(requests=count*len(rows),token_rows=count*sum(len(r['prompt_ids'])+(len(r['prompt_ids'])+8*127 if draft else 127) for r in rows),operators=0)

def validate(r,root,meta,reference):
    assert r['endpoint']==reference['endpoint'],'blind original-R endpoint failure'
    r['study_cap']=root['cap'];_,d=trace_from_row(r,r['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
    assert all(v==0 for v in r['observed_API_calls_within_service'].values()),'blind online state-work failure'
    return d

def run():
    assert not (DEST/'CLOSED_NUMERICAL_FAILURE.json').exists()
    published=json.loads((DEST/'PUBLISHED.json').read_bytes());assert published['verified_before_test_outputs']
    freeze=json.loads((DEST/'FREEZE.json').read_bytes())
    for key,name in [('source_selection_sha256','SOURCE_SELECTION.json'),('panels_sha256','PANELS.json'),('schedule_sha256','SCHEDULE.json'),('plan_sha256','PLAN.json')]:assert sha(DEST/name)==freeze[key]
    for name,h in freeze['implementation_files'].items():assert sha(HERE/name)==h,'host execution source changed after freeze'
    for name,h in freeze['inherited_execution_files'].items():assert sha(PREVIOUS/name)==h
    data=inputs();references={}
    for family,rs in data.items():
        label=f'confirm-{family}-independent-original-R';payload=dict(lowering='SIMPLE',draft=False,draft_width=1,inputs=[dict(name=f'r{i}',capture=False,input=r) for i,r in enumerate(rs)])
        out=finished(label,VERSIONS['R-'+family],family,payload,reservation(rs,False))
        references[family]=dict(meta=native_fields(out/'native/result.json',['vocab','eog_ids']),rows=[json.loads((out/'native'/f'r{i}/receipt.json').read_bytes()) for i in range(8)])
    schedule=json.loads((DEST/'SCHEDULE.json').read_bytes())
    for position,s in enumerate(schedule):
        family=s['family'];root=data[family][s['root_index']];arm=s['arm'];method,control=arm.split('-');draft=control!='M'
        payload=dict(lowering=method,draft=draft,draft_width=4 if control=='D4' else 1,inputs=[dict(name=name,capture=False,input=root) for name in ('warmup','measure')])
        out=finished(s['label'],VERSIONS[method],family,payload,reservation([root],draft,2))
        checked=out/'CHECKED.json'
        if not checked.exists():
            try:
                rows=[json.loads((out/'native'/name/'receipt.json').read_bytes()) for name in ('warmup','measure')]
                for r in rows:validate(r,root,references[family]['meta'],references[family]['rows'][s['root_index']])
                assert rows[0]['endpoint']==rows[1]['endpoint']
                put(checked,dict(original_R_endpoint_equal=True,independent_trace_valid=True,zero_online_state_API_calls=True,heavy_development_qualification_separate=True))
            except BaseException as e:
                put(DEST/'CLOSED_NUMERICAL_FAILURE.json',dict(slot=s,error=repr(e),completed_pairs=position+1,all_remaining_slots_retained_in_frozen_schedule=True));raise
        print('Confirmation pair',position+1,'/576 checked',s['label'],flush=True)
    put(DEST/'COMPLETE.json',dict(measurements=576,warmups=576,all_original_R_endpoints_and_traces_passed=True,no_replacement_or_extra_sessions=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');a=p.parse_args()
    if a.action=='prepare':prepare()
    else:run()
