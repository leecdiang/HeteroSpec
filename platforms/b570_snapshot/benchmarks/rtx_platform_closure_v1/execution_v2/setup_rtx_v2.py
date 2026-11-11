from pathlib import Path
import csv,hashlib,json,shutil,uuid
BASE=Path(__file__).resolve().parent;REPO=BASE/'HeteroSpec-rtx-closure';CODE=REPO/'benchmarks/rtx_platform_closure_v1/execution_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
old=Path('D:/hs-qb-confirmation-v02');plan=read(old/'PLAN.json')
names=['MBPP/413','GSM8K/test/120','GSM8K/test/322','GSM8K/test/443']
inputs=[next(x for x in plan['panel']['Qwen'] if x['id']==name) for name in names]
orders=[['R','PQ_A','PQ_B','QB'],['PQ_A','PQ_B','QB','R'],['PQ_B','QB','R','PQ_A'],['QB','R','PQ_A','PQ_B']]
schedule=[]
for session in range(4):
    slots=[]
    for visit in range(4):
        task=(visit+session)%4
        for label in orders[(session+task)%4]:
            for category in ('warmup','measured'):slots.append(dict(task=task,label=label,category=category))
    schedule.append(slots)
save(CODE/'INPUT_PANEL.json',dict(inputs=inputs,schedule=schedule,selection='Previously exposed PR104 panel: shortest/regression, strongest old C positive, intermediate with one negative session, longest. Chosen before new model execution.',cap=128))
endpoints={}
for path in sorted((old/'blocks').glob('*Qwen*.json')):
    for r in read(path)['records']:
        if r['task'] in names and r['condition']=='R' and not r['warmup']:
            x=r['output'];sig={k:x[k] for k in ('ids','length','terminal_id','stop_reason')};sig['eog']=x['eog_flags']
            if r['task'] in endpoints:assert endpoints[r['task']]==sig
            endpoints[r['task']]=sig
assert set(endpoints)==set(names);save(CODE/'HISTORICAL_ENDPOINTS.json',endpoints)
study_uuid=str(uuid.uuid4());raw=BASE/('rtx-study-'+study_uuid);raw.mkdir()
for name in ('INPUT_PANEL.json','HISTORICAL_ENDPOINTS.json'):shutil.copyfile(CODE/name,raw/name)
save(BASE/'RTX_ACTIVE.json',dict(uuid=study_uuid,raw=str(raw),code=str(CODE),exe=str(BASE/'rtx-runtime-v2/bin/rtx-closure.exe')))
identity=read(CODE/'BUILD_MANIFEST.json');audit=REPO/'benchmarks/rtx_platform_closure_v1/e0_20261020'
registration=dict(study='RTX_PLATFORM_CLOSURE_V2_REFERENCE_REPAIR',status='FROZEN_PROSPECTIVE_DESIGN',uuid=study_uuid,
    parent_protocol_pr=136,parent_protocol_head='65b938c19b9856c6c37af6c1d224989c22cd469f',
    supersedes_E0_stop_for_execution_only='9ce906a2-0e2d-4a1b-87e9-5fe3172f5ba2',
    user_authorization='2026-10-20 follow-up: repair engineering issues autonomously and complete the designed experiment; stop only for demonstrated infeasibility or scientific stopping rules',
    historical_reference=dict(status='PRESERVED_INCOMPLETE_FOR_FULL_LOGITS',new_prospective_reference_required=True,reference_uuid=study_uuid+'-REF',
        definition='Four independent reference processes each capture R and PQ k1 from the same pinned native driver, cap128 and old inputs. Both endpoints must equal historical R. Commit complete raw hash manifest before independent E1. No old reference is overwritten.'),
    identity=identity,input_panel_sha256=sha(CODE/'INPUT_PANEL.json'),historical_endpoints_sha256=sha(CODE/'HISTORICAL_ENDPOINTS.json'),
    models=read(old/'MODEL_CONTRACT.json')['families']['Qwen']['models'],tokenizer_contract_sha256=sha(old/'MODEL_CONTRACT.json'),
    output=dict(cap=128,greedy='highest float32 logit; lowest ID wins ties',eog='native vocab flags; include first EOG',sampling_seed='deterministic no RNG'),
    contexts=dict(n_ctx=1024,n_batch=1024,target_only_ubatch=1,speculative_target_ubatch=4,draft_ubatch=1,
        target_outputs_max=4,target_only_outputs_max=1,kv='f16',flash_attention=False,threads=24,draft_weights_resident_in_R=True,
        numerical_CUDA_DLLs='21 original PR104 DLLs unchanged',model_loading='both models once per native process; separately timed'),
    policy=dict(k=1,target_verify_rows=2,prefill='full immutable input batch decomposed by native ubatch',
       pending='initial sampled once; each verified seed already committed; accepted proposal followed by bonus unless terminal; mismatch correction becomes next pending',
       KV='trim target and draft to base+1+accepted after each cycle'),
    qualification=dict(reference_requests=8,independent_E1_requests=12,full_logit_byte_equality=True,
       R='own independent new R reference logits; endpoint must match historical R',PQ_QB='every target/draft decision vector including discarded verification row compared to new PQ reference',
       endpoint_and_cycle_trace_equality=True,real_q2_required=True,all36_target_layers_required=True,first_mismatch_stops_candidate=True,
       operator_tensors='Not requested: asking for raw node readback splits CUDA graph; metadata-only callbacks return false and logits are naturally materialized for greedy decisions'),
    timing=dict(independent_process_sessions=4,measured=64,warmup=64,one_warmup_per_input_arm_session=True,
       primary='native fresh-context creation and graph reservation through prefill/generation/full output and state handling/synchronization/teardown',
       shared_model_load='excluded and separately recorded',secondary='after contexts created through output/state handling before teardown',
       order='INPUT_PANEL.json schedule; four rotations balance each input and arm position across sessions',no_retry=True,no_outlier_removal=True,
       endpoint_checks='outside service timer against E1',no_node_observer_or_raw_IO_in_timed_request=True),
    analysis=dict(script_sha256=sha(CODE/'analyze.py'),primary='equal-input GM over four sessions of QB / arithmetic mean(PQ_A,PQ_B)',
       secondary='same equal-input GM of QB/R',AA='largest abs(input GM(PQ_A/PQ_B)-1)',
       engineering_screen='reduction > max(2%,AA), every session aggregate QB/dualPQ<1, all reference gates pass',
       E3='skip if practical screen fails OR QB/R>1.02; otherwise consider separately frozen sparse clean/profile/clean diagnostic',
       significance_or_equivalence=False),
    budget=dict(new_native_process_reservation=12,reference_processes=4,qualification_processes=4,timing_processes=4,
        requests=148,reference_requests=8,qualification_requests=12,warmups=64,measured=64,
        owned_native_seconds_cap=7200,storage_cap_bytes=8*1024**3,packaging_reserve_bytes=2*1024**3,
        preparation_compiler_processes_already_started=5,compiler_wall='not captured before staging error; logs retained',
        RTX_prior_ledger_sha256=sha(audit/'RTX_LEDGER_RECONCILIATION.json'),prior_ledgers_preserved=True,B570_allowance_transferred=False,
        note='New explicit RTX scope under user execution/repair authorization; no claim of a reconstructed global historical remaining balance'),
    stop_rules=['No clock deadline','First scientific mismatch stops the candidate and is preserved','No same-source scientific retry','A repaired implementation needs a new UUID/source freeze','No result-based input removal or profiling expansion'],
    raw_root=str(raw),first_native_start_receipt=None,freeze_commit='external commit receipt; no self-referential hash')
save(CODE/'PREREGISTRATION.json',registration)
save(CODE/'DESIGN_SHA256.json',dict(files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(CODE.iterdir()) if p.is_file() and p.name not in ('DESIGN_SHA256.json',)]))
shutil.copyfile(__file__,CODE/'setup_rtx_v2.py')
print(json.dumps(dict(uuid=study_uuid,raw=str(raw),inputs=[(x['id'],x['prompt_token_count']) for x in inputs])))
