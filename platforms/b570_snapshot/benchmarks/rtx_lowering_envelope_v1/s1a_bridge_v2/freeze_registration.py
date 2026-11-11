"""Create one independent CPU-prepared F0. This grants no GPU authority."""
import datetime,json,shutil,subprocess,sys
from pathlib import Path
from common import V,RUN,load,save,sha,pin
from readiness_policy import validate_policy
OLD=Path('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1')
BASE='449ead854424a1ac88d538332994bcf9f8813e1e'

def main():
    assert not (V/'F0.json').exists(), 'do not replace a freeze'
    assert subprocess.check_output(['git','-C',str(OLD),'rev-parse','HEAD'],text=True).strip()==BASE
    assert not subprocess.check_output(['git','-C',str(OLD),'status','--porcelain']).strip()
    assert not subprocess.check_output(['git','-C','D:/hs113','status','--porcelain']).strip()
    history=load(V/'HISTORY_BASELINE.json')
    for row in history['files']:
        assert Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256'], row['path']
    assert (OLD/'closure/ANALYSIS.json').read_bytes()==(OLD/'closure/FRESH_ANALYSIS.json').read_bytes()
    save(V/'HISTORY_UNCHANGED.json',dict(status='PASS',files_checked=len(history['files']),
         baseline_sha256=sha(V/'HISTORY_BASELINE.json'),old_run_terminal=True,old_native_starts=0,
         old_unstarted=240,old_readiness_failure=1,old_raw_archive=pin(OLD/'closure/RAW_BRIDGE.zip'),
         old322_member_fresh_restore_reused_only_as_historical_evidence=True,no_old_result_promoted=True))
    tests=['CPU_READINESS_TESTS.json','CPU_AUTHORIZATION_TESTS.json','CPU_NATIVE_TESTS.json','CPU_ANALYZER_TESTS_v2.json',
           'CPU_BOUNDED_TESTS.json','CPU_CONTROLLER_TESTS_final_v2.json','CPU_LIFECYCLE_TESTS.json',
           'CPU_RESOURCE_TESTS.json','CPU_EVIDENCE_TESTS_final.json','IMPLEMENTATION_REVIEW.json']
    for name in tests:assert load(V/name)['status'].startswith('PASS'),name
    old=load(OLD/'F0.json');plan=load(V/'PLAN.json');budget=load(V/'BUDGET_FINAL.json')
    assert not Path(plan['execution_root']).exists() and not Path('D:/hs114-s1a-bridge-v2-fresh').exists()
    assert not (V/'execution_ledger').exists()
    pins={}
    def add(path):
        row=pin(path);pins[str(Path(row['path']).resolve()).lower()]=row;return row
    # Revalidate inherited sources/headers/system/driver/models without loading them.
    for row in old['files']:
        path=Path(row['path'])
        if not path.is_relative_to(OLD):
            assert sha(path)==row['sha256'],str(path);add(path)
    for row in load(V/'CPU_WIRES.json')['modules']:add(row)
    for name,digest in old['numerical_DLLs'].items():
        path=Path(old['runtime_directory'])/name;assert sha(path)==digest;add(path)
    assert len(old['numerical_DLLs'])==21
    # CPU fixture files are evidence, never stage authorization. Runtime approval
    # must be separately authored against this final F0 and authenticated bytes.
    for path in V.rglob('*'):
        if path.is_file() and path.suffix!='.pdb' and '__pycache__' not in path.parts:
            add(path)
    for name in ['F0.json','closure/RAW_MANIFEST.json','closure/RAW_REMOTE_AUTHENTICATED.json',
                 'closure/FRESH_ANALYSIS.json','numerical_delivery/FINAL_READBACK.json']:
        add(OLD/name)
    policy={k:old['admission_policy'][k] for k in ('gpu','driver','total_MiB','power_scheme_guid','nvidia_smi')}
    policy.update(contract='A_STRICT_IDLE_V1',maximum_utilization_percent=5,
                maximum_temperature_C=55,minimum_free_MiB=512,AC_required=1,attempts_per_slot=1,
                cooldown_or_retry=False,utilization_interpretation='sampled_environment_isolation_not_numerical_theorem')
    validate_policy(policy)
    sources={p.name:sha(p) for p in V.iterdir() if p.suffix in ('.py','.h','.cpp')}
    conflicts=sorted(set(old['conflicting_owned_executables']+[str(OLD/'lowering113_formal.exe'),str(V/'lowering113_formal.exe')]))
    f0=dict(schema=2,run_id=RUN,stage='S1A_BRIDGE_V2',status='CPU_PREPARED_GPU_NOT_AUTHORIZED',
        review_base=BASE,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        execution_root=plan['execution_root'],fresh_restore_root='D:/hs114-s1a-bridge-v2-fresh',
        executable=str(V/'lowering113_formal.exe'),executable_sha256=sha(V/'lowering113_formal.exe'),
        plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=old['runtime_directory'],
        numerical_DLLs=old['numerical_DLLs'],admission_policy=policy,python=add(sys.executable),gh=add(shutil.which('gh')),
        console_helper=old['console_helper'],budget=budget,source_roles=sources,
        reference_index_sha256=sha(V/'REFERENCE_INDEX.json'),CPU_expected_graphs_sha256=sha(V/'CPU_GRAPH_EXPECTED.json'),
        ABI_export_table_sha256=sha(V/'ABI_EXPORTS.json'),
        selected_QH='QH_C',QH_D='fixed contrast; never substitution',independent_contexts=24,
        context_layout_graphs=120,technical_repeats=2,numerical_graph_call_cap=240,
        support_inheritance='NEW_CENSUS_REQUIRED_NO_TRANSFER',
        support_policy=old['support_policy'],numerical_policy=old['numerical_policy'],
        inherited_environment=old['inherited_environment'],
        amendment=dict(path=str(V/'AMENDMENT.md'),sha256=sha(V/'AMENDMENT.md'),scientific24_scope_accepted_in_old_run=True,
                       new_stage_approval_required=True,scope='No old slot/result/authorization/budget inheritance'),
        authorization=dict(current='NOT_GRANTED',first_stage='BRIDGE_V2_CENSUS_ONLY',numerical_stage='BRIDGE_V2_NUMERICAL_EXACT',
            separate_numerical_approval_requires_actual_census_and_decision_hashes=True),
        conflicts='Win32 executable metadata at start and each slot; never terminate unrelated work; not global GPU client attribution',
        conflicting_owned_executables=conflicts,observed_key_semantics=old['observed_key_semantics'],
        old720_resumed=0,old474_or_GPU14_repeats_used=0,closed_Bridge_reused_slots=0,
        new_model_requests=0,new_warmups=0,scientific_retries=0,timing_profile_actor_S2_S3_authorized=False,
        numeric_instrumented_envelopes_are_clean_cost_evidence=False,files=sorted(pins.values(),key=lambda r:r['path'].lower()))
    save(V/'F0.json',f0)
    save(V/'F0_IDENTITY.json',dict(run_id=RUN,F0_sha256=sha(V/'F0.json'),files=len(f0['files']),
        native_SHA256=f0['executable_sha256'],GPU_authorization='NOT_GRANTED',new_census_required=True,
        unique_entry=str(V/'run_bridge.py'),first_stage='census',numerical_requires_separate_authorization=True))
    print('CPU F0 prepared; no GPU authority:',sha(V/'F0.json'))
if __name__=='__main__':main()
