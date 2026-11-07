"""Post-stop publication only: preserve both failed integration revisions."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

sys.dont_write_bytecode=True
DESIGN=Path(__file__).resolve().parents[1]
BASE=Path('C:/hs/b570-paper-support-v1-20261016')
J=BASE/'journals'
DEST=DESIGN/'results'

def need(x,s):
    if not x:raise ValueError(s)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def size(root):return sum((Path(p)/n).stat().st_size for p,ds,fs in os.walk(root) for n in fs)

def main():
    begin=time.monotonic_ns();DEST.mkdir(exist_ok=False)
    assets=load(J/'ASSET_RECOVERY.json')
    for row in assets['assets']:need(Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256'],'inherited asset drift')
    for row in assets['actor_sources']:need(sha(row['path'])==row['sha256'],'copied fixed actor source changed')
    save(DEST/'FINAL_ASSET_RECHECK.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        assets_checked=len(assets['assets']),actor_source_files_checked=len(assets['actor_sources']),all_unchanged=True,
        CPU_wall_seconds=(time.monotonic_ns()-begin)/1e9,GPU_queries=0,model_requests=0))
    sys.path.insert(0,str(DESIGN))
    import study
    plan=study.plan();need(plan==load(DESIGN/'PLAN.json'),'complete fixed abstract plan drift')
    slots=[dict(**p,status='UNSTARTED_NOT_ADMITTED_S0_FAILED',native_PID=None,actual_requests=0,actual_graphs=0,
        requests_status=[dict(request=r,status='UNSTARTED',endpoint=None,paid_seconds=None) for r in p['requests']]) for p in plan['processes']]
    save(DEST/'ALL_SLOTS.json',dict(design_commit='67ef96e1f393231464f7e38ec6c344b784c4b1a4',slots=slots,planned_totals=plan['totals'],
        actual_native_starts=0,actual_model_requests=0,actual_standalone_graph_computes=0,actual_GPU_queries=0,
        S3_panel=None,source='Exact unchanged deterministic design plan; no fake prompts or old sample fills'))
    report=load(J/'INDEPENDENT_S0_RECONSTRUCTION_FINAL.json')
    shutil.copyfile(J/'INDEPENDENT_S0_RECONSTRUCTION_FINAL.json',DEST/'INDEPENDENT_S0_RECONSTRUCTION.json')
    review=load(J/'ACTUAL_IMPLEMENTATION_REVIEW/RECEIPT.json')
    save(DEST/'REVIEW_STATUS.json',dict(design_review='COMPLETED_NO_ACTIONABLE_DESIGN_DEFECTS_NOT_NATIVE_REVIEW',
        actual_implementation_review='INCOMPLETE_300_SECOND_DEADLINE',actual_review_PID=review['PID'],
        actual_review_seconds=review['observed_seconds'],actual_review_exit=review['returncode'],
        clean_actual_implementation_verdict=False,scientific_admission=False,review_log='journals/ACTUAL_IMPLEMENTATION_REVIEW',
        note='Actual configured default reviewer was used. It was not declared unavailable by model-name inference and no clean verdict is invented.'))
    positive=[]
    for row in report['cases']:
        if row['actual_controller_status']=='ADMITTED':
            positive.append(dict(revision=row['revision'],name=row['name'],coverage={s:{k:v for k,v in x.items() if k not in ('values','pending')} for s,x in row['coverage'].items()},
                post_exit_audit_seconds=row['post_exit_audit_seconds']))
    save(DEST/'SUMMARY.json',dict(classification='ENGINEERING_BLOCKED',design_commit='67ef96e1f393231464f7e38ec6c344b784c4b1a4',
        scientific_run_id=None,execution_F0=None,integration_revisions_used=2,integration_revisions_limit=2,
        suites=report['suites'],CPU_test_cases=len(report['cases']),CPU_test_child_starts=report['CPU_test_child_starts'],
        CPU_test_PowerShell_launchers=len(report['PowerShell_launcher_PIDs']),CPU_test_gated_controllers=len(report['gated_CPU_controller_PIDs']),
        CPU_test_child_FILETIME_seconds=report['CPU_FILETIME_lifetime_sum_seconds'],CPU_test_observed_seconds=report['CPU_observed_lifetime_sum_seconds'],
        CPU_case_command_wall_sum_seconds=report['case_command_wall_sum_seconds'],CPU_launcher_engineering_sum_seconds=report['launcher_engineering_sum_seconds'],
        positive_CPU_cases=positive,negative_control_preemptions=report['negative_control_preemptions'],
        native_CPP_actor_compiled=False,CSharp_launcher_compiled=True,S1='NOT_ADMITTED',S2='NOT_ADMITTED',S3='NOT_ADMITTED',
        scientific_native_starts=0,model_requests=0,standalone_graph_computes=0,GPU_queries=0,
        model_processes_unstarted=132,operator_and_census_hosts_unstarted=97,all_native_hosts_unstarted=229,
        model_requests_unstarted=716,standalone_graph_computes_unstarted=96,
        scientific_numerical_relations=None,scientific_endpoints=None,FP64_GPU_errors=None,paid_request_costs=None,acceleration=None,
        gates_missing=['Reliable complete production-path supervision','Required negative controls actually reached','Complete persisted watcher timing','Compiled/validated model capture-replay actor and serializer','Clean actual independent method/code review','Prospective certified execution F0'],
        termination='Bounded S0 integration exhausted; no third repair, scientific start, query or resumed old experiment.'))
    host_hashes={p.name:sha(p) for p in (DESIGN/'host').iterdir() if p.is_file()}
    save(DEST/'S0_EVIDENCE_SNAPSHOT.json',dict(schema='CLOSED_ENGINEERING_EVIDENCE_NOT_EXECUTION_F0',
        adopted_design='67ef96e1f393231464f7e38ec6c344b784c4b1a4',host_hashes=host_hashes,
        analyzer_sha256=sha(DESIGN/'delivery/rebuild_s0.py'),plan_sha256=sha(DESIGN/'PLAN.json'),
        source_lock_sha256=sha(DESIGN/'SOURCE_LOCK.json'),S0_finished=True,approved_for_GPU=False))
    entries=[]
    for namespace,root in [('journals',J),('outputs',BASE/'outputs'),('source-fixtures',BASE/'sources/CPU_INPUT_FIXTURES')]:
        for p in sorted(root.rglob('*')):
            if p.is_file():entries.append((namespace+'/'+p.relative_to(root).as_posix(),p))
    for p in sorted((DESIGN/'host').iterdir()):
        if p.is_file():entries.append(('host-source/'+p.name,p))
    for p in sorted((DESIGN/'cpu_fixture_results').rglob('*')):
        if p.is_file():entries.append(('source-negative-fixtures/'+p.relative_to(DESIGN/'cpu_fixture_results').as_posix(),p))
    for p in sorted(DESIGN.iterdir()):
        if p.is_file() and p.suffix in ('.py','.md','.json') and p.name not in ('RESULT.md','PAPER_EVIDENCE.md'):entries.append(('design/'+p.name,p))
    entries.append(('auditor/rebuild_s0.py',DESIGN/'delivery/rebuild_s0.py'))
    manifest=[];archive=DEST/'RAW_EVIDENCE.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name,p in entries:
            manifest.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p),original_path=str(p)))
            z.write(p,name)
    with zipfile.ZipFile(archive) as z:
        need(len(z.namelist())==len(manifest),'complete source/raw set')
        for row in manifest:
            b=z.read(row['path']);need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'archive member restore')
    save(DEST/'RAW_MANIFEST.json',dict(files=manifest,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
        uncompressed_bytes=sum(x['bytes'] for x in manifest),all_local_members_restored_and_verified=True,
        inherited_assets='Immutable existing models and runtime source copies are referenced by exact hashes and SOURCE_LOCK. They are not new observations and are not falsely claimed inside this CPU-evidence archive.',
        asset_reference_manifest_sha256=sha(J/'ASSET_RECOVERY.json'),archive_copies_limit=2))
    actual_wt=size(DESIGN.parents[1]);actual_external=size(BASE);archive_second_copy=archive.stat().st_size
    restore_reserve=sum(x['bytes'] for x in manifest);small_delivery=16*1024**2
    total=actual_wt+actual_external+archive_second_copy+restore_reserve+small_delivery
    need(total<=12*1024**3,'all new derived data plus recovery/export reservation exceeds12GiB')
    authorization=load(J/'AUTHORIZATION.json')
    save(DEST/'RESOURCE_ACCOUNTING.json',dict(managed_worktree_actual_bytes=actual_wt,external_preparation_actual_bytes=actual_external,
        remote_second_archive_reserved_bytes=archive_second_copy,fresh_uncompressed_restore_reserved_bytes=restore_reserve,
        remaining_delivery_reserved_bytes=small_delivery,total_with_reserves=total,limit_bytes=12*1024**3,
        includes_entire_new_worktree_checkout=True,old_model_copy_bytes=0,old_pressure_tree_copy_bytes=0,
        scientific_stage_CPU_controls_started=0,CPU_case_roles_measured=report['CPU_test_child_starts']+len(report['PowerShell_launcher_PIDs'])+len(report['gated_CPU_controller_PIDs']),
        observed_child_lifetimes_only_seconds=report['CPU_observed_lifetime_sum_seconds'],
        actual_CPU_child_FILETIME_lifetimes_seconds=report['CPU_FILETIME_lifetime_sum_seconds'],
        measured_case_command_wall_sum_seconds=report['case_command_wall_sum_seconds'],
        actual_reviewer_observed_seconds=review['observed_seconds'],
        engineering_elapsed_since_ledger_seconds=(time.monotonic_ns()-authorization['ledger_opened_monotonic_ns'])/1e9,
        separately_reserved_preledger_seconds=authorization['preledger_engineering_reserved_seconds'],
        S0_engineering_limit_seconds=28800,S0_CPU_child_limit_seconds=14400,
        incomplete_CPU_auxiliary_lifecycle_scope='Compiler/Git, initial asset recovery, unittest controllers and design-review helper exact process lifetime totals were not all captured. They are not fabricated or relabeled as measured. No execution F0/resource acceptance is issued.',
        GPU_checkpoint_values=None,scope='CPU engineering and post-stop delivery; no numerical/device/performance evidence. Full copy-count and final storage are checked again after actual remote recovery.'))
    print(json.dumps(dict(classification='ENGINEERING_BLOCKED',raw_members=len(manifest),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),total_bytes_reserved=total,scientific_starts=0)))

if __name__=='__main__':main()
