"""Freeze actual compiled v2, full CPU receipts, inputs and budget. CPU only."""
import datetime,json,subprocess
from pathlib import Path
from common import V,RUN,load,save,sha,pin
BASE='d4df9f1abaec3b5de4e7331c8ca9820432bc0bcf'
def git(*args):return subprocess.check_output(['git','-C','D:/hs113',*args])
def main():
    B=V.parent;assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('branch','--show-current').decode().strip()=='design/rtx-native-lowering-envelope-20261015'
    assert not git('diff','--name-only',BASE).strip(),'reviewed tracked bytes changed'
    assert not Path('D:/hs113-formal-numerical-v2').exists() and not (V/'execution_ledger').exists()
    for name in ('CPU_NATIVE_TESTS.json','CPU_ANALYZER_TESTS_release.json','CPU_EXTRA_TESTS_release.json','CPU_LIFECYCLE_TESTS_release.json','CPU_CONTRACT_TESTS.json'):assert load(V/name)['status']=='PASS'
    old=load(B/'repair_timer_v1/GPU14_F0.json');files={str(Path(p['path']).resolve()).lower():p for p in old['files']}
    for p in old['files']:assert sha(p['path'])==p['sha256'],p['path']
    stopped=load(B/'S1_NUMERICAL/ANALYSIS.json');assert (stopped['numeric_hosts_started'],stopped['numeric_hosts_failed'],stopped['not_started_due_to_protocol_stop'],stopped['confirmed_completed_graphs'])==(1,1,719,0)
    for m in load(B/'S1_NUMERICAL/RAW_MANIFEST.json')['members']:
        if m['path'].startswith('slots/'):assert sha(Path('D:/hs113-s1-v1')/m['path'])==m['sha256']
    g14=load(B/'GPU14_EXECUTION/ANALYSIS.json');assert (g14['counts']['graph_starts'],g14['counts']['confirmed_completed_graphs'],g14['counts']['failed'])==(14,14,0)
    assert sha(B/'GPU14_EXECUTION/RAW_GPU14.zip')=='f1dc041ad50400b3c11c874d5a94db9fba960d17ec20361df21a2871d8c3102f'
    for m in load(B/'GPU14_EXECUTION/RAW_MANIFEST.json')['members']:
        if m['path'].startswith('raw/'):assert sha(Path('D:/hs113-timer-gpu14-v1')/m['path'][4:])==m['sha256']
    for p in B.joinpath('GPU14_EXECUTION').glob('*'):
        if p.is_file():files[str(p.resolve()).lower()]=pin(p)
    save(V/'HISTORY_UNCHANGED.json',dict(status='PASS',review_base=BASE,old720=[1,719,0],GPU14=[14,14,0],old_live_failed_files=9,GPU14_live_raw_files=493,
        GPU14_archive_sha256=sha(B/'GPU14_EXECUTION/RAW_GPU14.zip'),old_numeric_archive_sha256=sha(B/'S1_NUMERICAL/RAW_NUMERICAL_STOP.zip'),
        no_old_result_input_source_F0_binary_cost_rewrite=True,no_old_budget_or_repeats_reused=True,new_GPU_starts=0))
    # Close all preparation ledgers except this currently running freeze job.
    exits=[load(p) for p in (V/'ledger').glob('*-EXIT.json')]
    charge=sum(r['charged_child_seconds_upper_bound']*(1 if r.get('accounts_console_helpers') else 2) for r in exits)
    save(V/'CPU_ACCOUNTING_AT_FREEZE.json',dict(completed_registered_jobs=len(exits),corrected_conservative_child_seconds=charge,ceiling_seconds=1800,
        correction='Earlier CPU receipts remain byte-identical; their bounds doubled to include observed automatic conhost. New receipts already include console helpers.',
        compilation_attempts=sum('compile_shared_formal' in p.name for p in (V/'ledger').glob('*-START.json')),
        actual_CPU_native_host_launches_direct_ledger=sum(Path(load(p)['command'][0]).name=='lowering113_formal.exe' for p in (V/'ledger').glob('*-START.json')),
        failures_retained=[p.name for p in (V/'ledger').glob('*-EXIT.json') if load(p)['exit_code']!=0],
        text_generation_failures=load(V/'CONTROL_TEXT_FAILURES.json'),GPU_queries=0,CUDA_loads=0,graph_computes=0,model_requests=0,
        scope='CPU preparation only; final freeze/dry/transport/restore and ordinary delivery tooling are reported separately in closure accounting'))
    assert charge<1800
    for path in (B/'GPU14_EXECUTION/OBSERVED_MODULE_FILES.json',V/'CPU_WIRES.json'):
        data=load(path);names=[p['path'] for p in data['files']] if 'files'in data else data['modules']
        for p in names:files[str(Path(p).resolve()).lower()]=pin(p)
    # Exclude active mutable CPU-job files and post-registration closure artifacts.
    exclude={'F0.json','CPU_JOB.lock','RAW_PREPARATION.zip','RAW_PREPARATION_MANIFEST.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json','AUTHENTICATED_PREPARATION.json','FRESH_CPU_RESTORE.json','RESULT.md','PR_BODY.md','DELIVERY.json','CLOSURE_ACCOUNTING.json'}
    active={p.name.split('-')[0] for p in (V/'ledger').glob('*-START.json') if not p.with_name(p.name.replace('-START','-EXIT')).exists()}
    for p in sorted(V.rglob('*')):
        if not p.is_file() or p.name in exclude or '__pycache__' in p.parts:continue
        if 'ledger' in p.parts and p.name.split('-')[0] in active:continue
        files[str(p.resolve()).lower()]=pin(p)
    for p in V.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
    helper=pin(Path('C:/Windows/System32/conhost.exe'));files[str(Path(helper['path']).resolve()).lower()]=helper
    compiler=load(V/'LINK_IDENTITY.json')['link_command'][0];files[str(Path(compiler).resolve()).lower()]=pin(compiler)
    conflict={p['path'] for p in files.values() if Path(p['path']).suffix.lower()=='.exe' and any(s in Path(p['path']).name.lower() for s in ('llama-server','lowering113'))}
    plan=load(V/'PLAN.json');budget=load(V/'BUDGET.json');assert budget['storage']['all_derived_upper_bound_bytes']==3744314580
    sources=['native_formal.cpp','formal_gate.h','core_gate.h','hs113_graph.h','run_formal.py','lifecycle.py','common.py','analyzer.py','raw_math.py','cpu_job.py','seal_census.py','package_formal.py']
    f0=dict(schema=1,run_id=RUN,stage='FORMAL_NUMERICAL_V2',status='PREPARED_NOT_GPU_AUTHORIZED',review_base=BASE,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        execution_root=plan['execution_root'],executable=str(V/'lowering113_formal.exe'),executable_sha256=sha(V/'lowering113_formal.exe'),
        plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=old['runtime_directory'],numerical_DLLs=old['numerical_DLLs'],admission_policy=old['admission_policy'],
        selected_QH='QH_C',QH_D='Fixed original contrast only; never reselected based on new outputs',independent_contexts=72,context_layout_graphs=360,technical_repeats=2,numerical_graph_call_cap=720,
        reference_index_sha256=sha(V/'REFERENCE_INDEX.json'),CPU_expected_graphs_sha256=sha(V/'CPU_GRAPH_EXPECTED.json'),ABI_export_table_sha256=sha(V/'ABI_EXPORTS.json'),
        source_roles={name:sha(V/name) for name in sources},budget=budget,console_helper=helper,conflicting_owned_executables=sorted(conflict),
        inherited_environment=dict(GGML_CUDA_DISABLE_GRAPHS='1',meaning='Original frozen CUDA/graph/precision/runtime configuration unchanged; original NO_WINDOW|SUSPENDED process flags retained'),
        authorization=dict(current='NOT_GRANTED',first_stage='FORMAL_V2_CENSUS_ONLY',numerical_stage='FORMAL_V2_NUMERICAL_EXACT',
            sequence='Explicit author approval of this F0 -> one new complete360 census -> commit/authenticated byte readback of census+decision -> new numerical approval bound to those hashes -> at most720 slots. No automatic subsequent stage.'),
        support_policy='No inheritance from GPU14 or old support census. New5418-node census for all360 stage-output graphs. Required MQ/PQ/QB/QH_C or anyq1 unsupported stops numerical admission. Unsupported q>1 QH_D cells remain NOT_SUPPORTED, not deleted; no replacement byD. Actual per-host10836 node queries/placement still required.',
        census_field_semantics=dict(allocations='Explicit graph tensor allocator calls0; internal CUDA/context/driver allocations UNKNOWN',GPU_initializations='One explicit backend_init_by_name; internal driver queries UNKNOWN',graph_computes=0),
        numerical_policy='Any runtime/module/interface/support/device/input/nonfinite/q1/MQ-ownpath/historicalPQ-QB/repeat failure stops. Finite validq>1 QH differences retained with full bytes/bitwise/absolute error/ULP/first operator and logical position, no generic MQ-equality gate or posthoc tuning.',
        source_change_scope='Minimal run_id/F0/actual-plan wire admission, complete support census path, actual CPU wire/address checks, lossless CAS observations and bounded lifecycle/independent generic analysis. Graph constructor/arithmetic header/CoreGate equal GPU14; numerical DLLs not rebuilt.',
        monitoring_caveats='Process/job commit limits OS enforced; controller private commit and wall/disk observed at requested50ms without guaranteed scheduling bound. Checkpoint readiness is not continuous GPU monitoring/residency. Logical artifact bytes are not NTFS physical allocated bytes; physical free-space guards separate. API-internal driver/kernel counts UNKNOWN.',
        full_request_actor_timing_profile_S2_S3_authorized=False,GPU14_repeats_used_in_formal_panel=0,old720_slots_resumed=0,
        reference_exposure='All72 are known exposed PR104 operator snapshots. Actual finite-mask visible keys and padded extents separately recorded in PLAN and MATRIX; no long/unseen input claim.',
        files=sorted(files.values(),key=lambda p:p['path'].lower()))
    save(V/'F0.json',f0)
    save(V/'F0_IDENTITY.json',dict(sha256=sha(V/'F0.json'),bytes=(V/'F0.json').stat().st_size,executable_sha256=f0['executable_sha256'],files=len(f0['files']),GPU_authorization='NOT_GRANTED',unique_GPU_execution_entry='run_formal.py --stage census|numerical --approval ACTUAL_HUMAN_RECEIPT',new_GPU_queries=0))
    print('PREPARED NOT AUTHORIZED: F0',sha(V/'F0.json'),'files',len(f0['files']),'native',f0['executable_sha256'])
if __name__=='__main__':main()
