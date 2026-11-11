"""Freeze actual CPU-tested Bridge. Never queries a device or loads a plugin."""
import datetime,difflib,json,shutil,subprocess,sys
from pathlib import Path
from common import V,RUN,load,save,sha,pin
from prepare_review import OLD

BASE='64a9feb7b7086ccfde1a98b9514edd812116aa7f'
def main():
    assert not Path('D:/hs113-s1a-bridge-v1').exists() and not (V/'execution_ledger').exists()
    for name in ('CPU_NATIVE_TESTS.json','CPU_ANALYZER_TESTS_bridge.json','CPU_FAST_CONTROLS.json','CPU_BOUNDED_TESTS.json','CPU_CONTROLLER_TESTS_final_v2.json','CPU_LIFECYCLE_TESTS.json','CPU_RESOURCE_TESTS.json','CPU_EVIDENCE_TESTS_final.json'):
        assert load(V/name)['status']=='PASS',name
    assert load(V/'ACTOR_CPU_AUDIT.json')['full_actor_qualification'] is False
    assert load(V/'CPU_CORE_ABI_v2.json')['graph_computes']==0
    assert not subprocess.check_output(['git','-C','D:/hs113','status','--porcelain']).strip()
    assert subprocess.check_output(['git','-C','D:/hs113','rev-parse','HEAD']).decode().strip()==BASE
    history=load(V/'HISTORY_BASELINE.json')
    for p in history['files']:assert sha(p['path'])==p['sha256'],p['path']
    raw=Path('D:/hs113-formal-numerical-v2')
    assert all(not (raw/n).exists() for n in history['old_raw_root_absences'])
    assert all((raw/n).exists() for n in history['old_raw_root_present'])
    save(V/'HISTORY_UNCHANGED.json',dict(status='PASS',files_reverified=len(history['files']),old720=[1,719,0],GPU14=[14,14,0],v2=[474,246],
        original19343_member_remote_restore_and_unchanged_recompute_previously_completed=True,old_locks_failures_and_absences_unchanged=True,history_manifest_sha256=sha(V/'HISTORY_BASELINE.json')))
    old=load(OLD/'repair_timer_v1/GPU14_F0.json');pins={}
    def add(p):
        d=pin(p);pins[str(Path(d['path']).resolve()).lower()]=d;return d
    # Actual unchanged numerical DLLs, models, system/driver modules. No loading.
    for p in old['files']:
        suffix=Path(p['path']).suffix.lower()
        if suffix in ('.dll','.gguf','.sys') or Path(p['path']).name.lower()=='nvidia-smi.exe':
            assert sha(p['path'])==p['sha256'];add(p['path'])
    for name,h in old['numerical_DLLs'].items():assert sha(Path(old['runtime_directory'])/name)==h
    for p in (OLD/'native/source').rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.h','.hpp','.c','.cpp','.cmake','.in'):add(p)
    add(OLD/'native/build/build.ninja')
    for r in load(OLD/'GPU14_EXECUTION/OBSERVED_MODULE_FILES.json')['files']:add(r['path'])
    exclude={'F0.json','F0_IDENTITY.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json','RAW_CPU.zip','RAW_CPU_MANIFEST.json','PREPARATION_REMOTE_VERIFIED.json','RESULT.md','PR_BODY.md'}
    for p in V.rglob('*'):
        if p.is_file() and p.name not in exclude and p.suffix!='.pdb' and '__pycache__' not in p.parts:add(p)
    plan=load(V/'PLAN.json')
    for d in plan['descriptors']:
        for p in d['input_files']:assert sha(p['path'])==p['sha256'];add(p['path'])
    for p in (V/'CPU_WIRES.json',V/'CPU_CORE_ABI_v2.json'):
        for name in load(p)['modules']:add(name)
    python=add(sys.executable);gh=add(shutil.which('gh'));helper=add('C:/Windows/System32/conhost.exe')
    compiler=add(load(V/'LINK_IDENTITY.json')['link_command'][0])
    oldv=OLD/'formal_numerical_v2'
    for n in ('native_formal.cpp','hs113_graph.h','core_gate.h'):assert (V/n).read_bytes()==(oldv/n).read_bytes()
    diff=''.join(difflib.unified_diff((oldv/'formal_gate.h').read_text().splitlines(True),(V/'formal_gate.h').read_text().splitlines(True),fromfile='formal_v2/formal_gate.h',tofile='s1a_bridge_v1/formal_gate.h'))
    save(V/'ARITHMETIC_UNCHANGED.json',dict(status='PASS',byte_identical=['native_formal.cpp','hs113_graph.h','core_gate.h'],native_gate_diff=diff,
        numerical_DLLs=old['numerical_DLLs'],models=[p for p in pins.values() if Path(p['path']).suffix.lower()=='.gguf'],new_executable=pin(V/'lowering113_formal.exe'),compiler=compiler))
    add(V/'ARITHMETIC_UNCHANGED.json');add(V/'HISTORY_UNCHANGED.json')
    budget=load(V/'BUDGET_FINAL.json');assert budget['storage']['all_derived_upper_bound_bytes']<budget['limits']['total_derived_bytes']
    sources=[p.name for p in V.iterdir() if p.suffix in ('.py','.cpp','.h')]
    f0=dict(schema=1,run_id=RUN,stage='S1A_BRIDGE_V1',status='CPU_PREPARED_GPU_NOT_AUTHORIZED',review_base=BASE,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        execution_root=plan['execution_root'],fresh_restore_root='D:/hs113-s1a-bridge-v1-fresh',executable=str(V/'lowering113_formal.exe'),executable_sha256=sha(V/'lowering113_formal.exe'),
        plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=old['runtime_directory'],numerical_DLLs=old['numerical_DLLs'],admission_policy=old['admission_policy'],python=python,gh=gh,console_helper=helper,
        selected_QH='QH_C',QH_D='fixed contrast, never substitution',independent_contexts=24,context_layout_graphs=120,technical_repeats=2,numerical_graph_call_cap=240,
        budget=budget,source_roles={n:sha(V/n) for n in sources},reference_index_sha256=sha(V/'REFERENCE_INDEX.json'),CPU_expected_graphs_sha256=sha(V/'CPU_GRAPH_EXPECTED.json'),ABI_export_table_sha256=sha(V/'ABI_EXPORTS.json'),
        amendment=dict(path=str(V/'AMENDMENT.md'),sha256=sha(V/'AMENDMENT.md'),status='PROPOSED_SEPARATE_AUTHOR_ACCEPTANCE_REQUIRED',scope='Only fixed24 numerical prerequisite for preparing later same24 S1B. No original72/full actor/cost qualification.'),
        authorization=dict(current='NOT_GRANTED',first_stage='BRIDGE_CENSUS_ONLY',numerical_stage='BRIDGE_NUMERICAL_EXACT',separate_numerical_approval_requires_actual_census_and_decision_hashes=True),
        support_policy='New full120 actual stage-output graphs/1806 support queries; per-numerical-host3612 total queries plus actual allocation checks. No automatic old census inheritance. Required MQ/PQ/QB/QH_C or anyq1 unsupported stops; onlyq>1QH_D NOT_SUPPORTED remains explicit.',
        numerical_policy='Complete input before/after,4full outputs,module/graph/device/ownpath/historyPQ-QB/q1/independent repeats. Stop on controls or infrastructure; valid finiteq>1QH differences are retained, not generic MQ equality failure. Full metrics only in separately bounded CPU analysis.',
        inherited_environment=dict(GGML_CUDA_DISABLE_GRAPHS='1',creation_flags=0x08000004),
        conflicts='Process metadata only; never terminate unrelated workloads',conflicting_owned_executables=sorted({str(OLD/'native/build/bin/llama-server.exe'),str(V/'lowering113_formal.exe'),str(oldv/'lowering113_formal.exe'),str(OLD/'repair_timer_v1/lowering113_repair.exe')}),
        old720_resumed=0,old474_or_GPU14_repeats_used=0,new_model_requests=0,new_warmups=0,scientific_retries=0,
        timing_profile_actor_S2_S3_authorized=False,numeric_instrumented_envelopes_are_clean_cost_evidence=False,
        observed_key_semantics='Full exposed PR104 masks determine real visible keys; tensor extent256 includes padding. No unseen prompt or long-context claim.',
        files=sorted(pins.values(),key=lambda r:r['path'].lower()))
    save(V/'F0.json',f0)
    save(V/'F0_IDENTITY.json',dict(run_id=RUN,sha256=sha(V/'F0.json'),bytes=(V/'F0.json').stat().st_size,files=len(f0['files']),
        host_sha256=f0['executable_sha256'],unique_GPU_entry='run_bridge.py --stage census|numerical --approval ACTUAL_SEPARATE_AUTHOR_RECORD',GPU_authorization='NOT_GRANTED'))
    print('F0 PREPARED NOT AUTHORIZED',sha(V/'F0.json'),'files',len(f0['files']))
if __name__=='__main__':main()
