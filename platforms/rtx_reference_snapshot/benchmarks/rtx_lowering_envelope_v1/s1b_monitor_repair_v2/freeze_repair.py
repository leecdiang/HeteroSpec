"""CPU-only exact freeze. Never replaces old F0, assets or stopped attempts."""
import datetime,copy,json,os,subprocess
from pathlib import Path
from common import V,load,save,sha,pin
from admission import owned_conflicts
import audit

def main():
    olddir=V.parent/'s1b_exact_repair_v1';old=load(olddir/'F0.json');plan=load(V/'PLAN.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()=='70423817a816406e61a2d91acb2d3d3f848e30b8'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=V).decode().strip()==old['branch']
    assert not Path('D:/hs116-s1b-cost-v1-exact-r2').exists()
    verified=[]
    for row in old['files']:
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path'];verified.append(row)
    hist=load(V/'HISTORY_BEFORE.json')
    for row in hist['files']:
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
    owned_conflicts(old)
    census=Path(old['execution_bound_census']['path']);assert sha(census)=='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256'
    assert sha(V/'s1b_clean.exe')=='073bdc32c6b54866b075d0dc47b5e9a343ec299fa1c87b5cd0937abe32db035b'
    for name,digest in old['numerical_DLLs'].items():assert sha(Path(old['runtime_directory'])/name)==digest
    assert len(old['numerical_DLLs'])==21
    expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_EXPECTED.json')}
    assert audit.census(load(census),plan,expected)==load(old['execution_bound_decision']['path'])
    import identity
    original=load(V.parent/'s1b_cost_v1/F0.json');original_host=original['hosts']['clean']
    original_native=census.parent;original_receipts=original_native.parent
    identity.process_identity(original_receipts,'native',dict(original,executable=original_host['path']),240)
    identity.verify_modules(original_native,load(census),dict(original,executable=original_host['path'],executable_sha256=original_host['sha256']),load(original_receipts/'MODULE_FILES.json'))
    assert load(V/'CPU_GRAPHS.json')['records']==load(V.parent/'s1b_cost_v1/CPU_GRAPHS_FINAL2.json')['records']
    for name in ['native_cost.cpp','graph_base.h','hs113_graph.h','core_gate.h','s1b_gate.h','timing_loop.h','s1b_clean.exe','s1b_trace.exe','CPU_EXPECTED.json','CAS_INDEX.json','ABI_EXPORTS.json']:
        assert sha(V/name)==sha(olddir/name),name
    b=copy.deepcopy(old['budget']);b['stages']={'clean0':b['stages']['clean0']};stage=b['stages']['clean0']
    stage.update(controlled_process_starts=577,controllers=1,readiness_queries=72,CPU_watchdog_processes=144,conhost_helpers=288,maximum_concurrent_controlled_processes=5,conservative_owned_multiplier=5,effective_wall_cap_from_owned_seconds=360,formal_measurements=576,warmups=72,support_API_queries=828)
    b['limits'].update(per_host_nonCAS=6*1024**2,job_active2=False,job_active_process_limit=4,watchdog_extra_job_commit_bytes=128*1024**2,max_monitor_interval_ns=1_000_000_000)
    b['currently_registered_executable_stages']=dict(stage='clean0',native_clean_hosts=72,controllers=1,readiness_queries=72,CPU_watchdogs=144,conhost_helpers=288,total_controlled_starts=577,graph_calls=648,warmups=72,formal_measurements=576,support_API_queries=828,Block1_2_trace_Census=False)
    b['monitoring']='Independent CPU watchdog per registered child;actual monotonic adjacent samples and startup/exit-observation coverage <=1000000000ns inclusive. Requested50ms only. Watchdog loss fails closed. CPU process overhead charged. Post-exit audit separate but stage charged.'
    # Original whole-study raw/storage cap retained. Block0 fit checked from full inputs and readbacks.
    storage=b['storage'];block0_meta=72*6*1024**2;block0_outputs=storage['all_output_no_dedup_bytes']//3
    block0_raw=storage['immutable_full_input_reference_bytes']+block0_meta+block0_outputs+storage['first_mutation_reserve']
    assert block0_raw<=b['limits']['raw_bytes'] and storage['all_derived_upper_bound_bytes']<=4*1024**3
    b['storage']['Block0_strict_monitor_raw_bound_bytes']=block0_raw
    b['storage']['monitor_metadata_basis']='Two <=2MiB journals per coordinate + old1MiB metadata + <=256KiB four-stream logs; <=6MiB per coordinate. 8MiB reservation unchanged. Original794043645 raw cap and4269519081 total derived cap unchanged.'
    save(V/'BUDGET.json',b)
    report=dict(status='PASS',old_frozen_files_verified=len(verified),old_frozen_file_bytes=sum(r['bytes'] for r in verified),historical_files_unchanged=len(hist['files']),native_EXE=pin(V/'s1b_clean.exe'),native_source_unchanged=True,numerical_DLLs=old['numerical_DLLs'],execution_bound_census=pin(census),original_Census_host_module_and_IAT_receipts_rechecked=True,Census_graphs=72,Census_queries=828,all_graph_records_unchanged=True,models_inputs_and_references_unchanged=True,OS_conflict_check='PASS',GPU_queries=0,CUDA_loads=0,graph_calls=0,new_execution_root_absent=True)
    save(V/'PRE_FREEZE_IDENTITY.json',report)
    f=copy.deepcopy(old)
    for key in ['registration_id','superseded_unapproved_CPU_candidate','superseded_unapproved_CPU_candidate','archive_manifest','archive_remote_verification','previous_F0','previous_preflight_stop','previous_404_failure']:f.pop(key,None)
    f.update(schema=3,registration_revision=3,run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',status='CPU_REPAIR_FROZEN_GPU_NOT_AUTHORIZED',review_base=hist['base'],recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_root='D:/hs116-s1b-cost-v1-exact-r2',fresh_restore_root='D:/hs116-s1b-cost-v1-exact-r2-fresh',plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),budget=b)
    f['hosts']={role:pin(V/Path(row['path']).name) for role,row in old['hosts'].items()}
    f['monitor_contract']=dict(run_id=f['run_id'],execution_id=f['execution_id'],max_monitor_interval_ns=1_000_000_000,requested_poll_ns=50_000_000,watchdog_path=str(V/'monitor_worker.py'),watchdog_sha256=sha(V/'monitor_worker.py'),python=old['python'],CPU_fixture_only=False,clock='time.monotonic_ns;Windows QPC',boundary='<= inclusive; > FAIL',qualified_sample='actual target alive + private commit + Job commit + controller/disk/log/process guard;exact chained journal fsync',startup_and_exit_tail_coverage=True,independent_CPU_watchdog=True,no_exit_or_EOF_samples=True)
    f['authorization']=dict(current='NOT_GRANTED',required='S1B_CLEAN_BLOCK_0_EXACT',run_id=f['run_id'],execution_id=f['execution_id'],binds='authorization binds exact bytes consumed by the execution entry',Block1_2_trace_Census_authority=False)
    f['support_status']='REUSE_EXACT_NATIVE_CENSUS_CPU_VERIFIED_NO_NEW_GPU_CENSUS'
    f['historical_F0']=pin(olddir/'F0.json');f['historical_failure_records']=pin(V/'HISTORY_BEFORE.json')
    f['allowed_future_stage']='clean0 only after independent author approval of this exact new F0 and execution_id'
    f['conflicting_owned_executables']+= [str(V/'s1b_clean.exe'),str(V/'s1b_trace.exe')]
    files={r['path']:r for r in old['files']}
    local=[p for p in V.iterdir() if p.is_file() and p.suffix in {'.py','.h','.cpp','.exe','.json','.md'} and p.name!='F0.json']
    for p in local:files[str(p)]=pin(p)
    f['files']=sorted(files.values(),key=lambda x:x['path'])
    f['source_roles']={p.name:sha(p) for p in local if p.suffix in {'.py','.h','.cpp'}}
    f['CPU_tests']={n:pin(V/n) for n in ['CPU_TESTS.json','CPU_MONITOR_TESTS_FINAL.json','CPU_STRICT_AUDIT_TESTS.json','CPU_IDENTITY_CONTRACT_TESTS.json','PRE_FREEZE_IDENTITY.json']}
    save(V/'F0.json',f)
    print('F0',sha(V/'F0.json'),'history',len(hist['files']),'native/DLL/Census unchanged;GPU0')
if __name__=='__main__':main()
