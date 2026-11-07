"""One CPU preparation freeze; no backend loads, device queries or approval."""
import ast,datetime,shutil,subprocess,sys
from pathlib import Path
from common import V,RUN,load,save,sha,pin
OLD=Path('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2')
BASE='2b5ed1552263907df3adfdff9b0121d115734a6c'
def main():
    assert not (V/'F0.json').exists()
    for p in V.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    for name in ['CPU_NATIVE_TESTS_FINAL2.json','CPU_GRAPH_REVIEW_FINAL.json','CPU_LOOP_CLEAN_FINAL2.json','CPU_LOOP_TRACE_FINAL2.json','CPU_AUDIT_TESTS_FINAL.json','CPU_READINESS_TESTS.json','CPU_BOUNDED_TESTS.json','CPU_ENGINEERING_TESTS.json','CPU_STATISTICS_TESTS_FINAL.json','CPU_PARTIAL_FAILURE_TESTS.json','CPU_STATS_FINAL_CHECK.json','CPU_HTTPS_TRANSPORT_TEST_FINAL.json','CPU_TERMINAL_AUDIT_TESTS.json']:
        assert load(V/name)['status']=='PASS',name
    assert subprocess.check_output(['git','-C',str(OLD),'rev-parse','HEAD'],text=True).strip()==BASE
    assert not subprocess.check_output(['git','-C',str(OLD),'status','--porcelain']).strip()
    history=load(V/'HISTORY_BASELINE.json')
    for r in history['files']:assert sha(r['path'])==r['sha256'],r['path']
    save(V/'HISTORY_UNCHANGED.json',dict(status='PASS',files=len(history['files']),old_PR116_commit=BASE,old240_results_unchanged=True,old_raw_archive_sha256=sha(OLD/'closure/RAW_BRIDGE.zip')))
    old=load(OLD/'F0.json');pins={}
    def add(path):r=pin(path);pins[r['path'].lower()]=r;return r
    for r in old['files']:
        p=Path(r['path'])
        if not p.is_relative_to(OLD):assert sha(p)==r['sha256'];add(p)
    for name,digest in old['numerical_DLLs'].items():assert sha(Path(old['runtime_directory'])/name)==digest
    for r in load(V/'EVIDENCE_BINDING.json').values():
        if isinstance(r,dict) and 'path' in r:assert sha(r['path'])==r['sha256'];add(r['path'])
    for d in load(V/'PLAN.json')['descriptors']:
        for r in d['input_files']:assert sha(r['path'])==r['sha256'];add(r['path'])
    for s in load(V/'PLAN.json')['clean_slots']:
        for key in ['ordinary_reference','AV_reference']:r=s[key];assert sha(r['path'])==r['sha256'];add(r['path'])
    for p in V.rglob('*'):
        if p.is_file() and p.suffix!='.pdb' and '__pycache__' not in p.parts:add(p)
    for path in load(V/'CPU_GRAPHS_FINAL2.json')['modules']:add(path)
    for r in load(V/'CPU_TRANSPORT_PINS_FINAL.json'):add(r['path'])
    budget=load(V/'BUDGET.json');assert budget['storage']['all_derived_upper_bound_bytes']<4*1024**3
    cpu_spent=sum(load(p)['charged_child_seconds_upper_bound'] for p in (V/'ledger').glob('*-EXIT.json'));assert cpu_spent<1800
    root='D:/hs116-s1b-cost-v1';assert not Path(root).exists() and not Path(root+'-fresh').exists() and not (V/'execution_ledger').exists()
    roles={p.name:sha(p) for p in V.iterdir() if p.suffix in ('.h','.cpp','.py')}
    f=dict(schema=1,registration_revision=3,superseded_unapproved_CPU_candidate='preparation_candidates/F0.json',run_id=RUN,stage='S1B_COST_V1',status='CPU_PREPARED_GPU_NOT_AUTHORIZED',review_base=BASE,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repository='D:/hs116-s1b',branch='research/rtx-s1b-clean-cost-20261016',execution_root=root,fresh_restore_root=root+'-fresh',plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=old['runtime_directory'],numerical_DLLs=old['numerical_DLLs'],admission_policy=old['admission_policy'],hosts={role:add(V/f's1b_{role}.exe') for role in ['clean','trace']},QPC_frequency=load(V/'CPU_LOOP_CLEAN_FINAL2.json')['real_CPU_QPC_frequency'],budget=budget,source_roles=roles,python=add(sys.executable),git=add(shutil.which('git')),gh=add(shutil.which('gh')),console_helper=old['console_helper'],CPU_transport_executables=load(V/'CPU_TRANSPORT_PINS_FINAL.json'),profile=load(V/'PROFILE_REVIEW.json'),inherited_environment=old['inherited_environment'],conflicting_owned_executables=sorted(set(old['conflicting_owned_executables']+[str(V/'s1b_clean.exe'),str(V/'s1b_trace.exe')])),support_status='NEW72_CLEAN_CENSUS_REQUIRED',actual_clean_CUDA_ordinary_qualification='NOT_ESTABLISHED;first original72-host block warmups and all outputs must match PR116',authorization=dict(current='NOT_GRANTED',first='S1B_CENSUS_ONLY',clean='S1B_CLEAN_BLOCK_0_EXACT then separately BLOCK_1/2',trace='NOT_ADMITTED_PROFILE_UNAVAILABLE',amendment_acceptance_required=True),selected_QH='QH_C',reference_evidence=load(V/'EVIDENCE_BINDING.json'),original_S1B_counts=dict(clean=216,trace=72,graph_calls=2088,warmups=288),trace_72_not_removed=True,mathematical_truth_or_kernel_trace_inferred=False,new_model_requests=0,scientific_retries=0,main_paper_actor_S2_S3_RTL_authorized=False,preparation_compile_conservative_child_seconds=cpu_spent,files=sorted(pins.values(),key=lambda r:r['path'].lower()))
    save(V/'F0.json',f);save(V/'F0_IDENTITY.json',dict(run_id=RUN,F0_sha256=sha(V/'F0.json'),hosts=f['hosts'],files=len(f['files']),unique_entry=str(V/'run_s1b.py'),first_stage='census',GPU_authorization='NOT_GRANTED',trace_status=f['profile']['status']))
    print('F0 CPU prepared,no GPU authority',sha(V/'F0.json'))
if __name__=='__main__':main()
