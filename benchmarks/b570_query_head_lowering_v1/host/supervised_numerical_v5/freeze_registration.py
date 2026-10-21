"""Freeze this repaired supervisor registration after actual fresh CPU tests."""
import datetime
import hashlib
import importlib.util
import os
import pathlib
import subprocess
import sys
import zipfile
import difflib
from legacy import HERE,OLD,ROOT,OUT,RUN,RUN_ID,BASE,GIT,LIMITS,load,save,sha,need,modules,EXTERNAL_LOG_ROOT,EXTERNAL_RESERVED_BYTES
from registration import plan,serialize

def main():
    need(not (HERE/'F0.json').exists() and not RUN.exists() and not EXTERNAL_LOG_ROOT.exists(),'immutable F0 / both unstarted roots required')
    need(subprocess.check_output([GIT,'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==BASE,'reviewed base')
    need(not subprocess.check_output([GIT,'-C',str(ROOT),'diff','--name-only',BASE],text=True).strip(),'old tracked files immutable')
    spec=importlib.util.spec_from_file_location('_own_prepare',HERE/'prepare_supervision.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
    receipt=sorted((HERE/'preparation').glob('CPU_TESTS_*.json'))[-1];tests=load(receipt);need(tests['success'],'latest CPU suite must pass')
    sources={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in prep.source_files()};need(sources==tests['source_hashes'],'source changed after fresh CPU suite')
    v4=ROOT/'host/supervised_numerical_v4'
    need(sha(v4/'storage.py')==sha(HERE/'storage.py') and sha(v4/'timing.py')==sha(HERE/'timing.py'),'watcher and1s policy byte-identical')
    need(sha(v4/'F0.json')=='5fab2cf08daa2f2ac57537ade5a16648a324ec0c0fcfa9a77d97d9b18bd351f7','v4 immutable F0')
    v4rawroot=ROOT/'host_outputs/supervised_numerical_v4/b570-supervised-numerical-v4-20261016-01'
    for r in load(v4/'results/RAW_MANIFEST.json')['files']:need(sha(v4rawroot/r['path'])==r['sha256'],'v4 failure raw drift')
    need(load(v4rawroot/'CLOSEOUT_COMMITTED.json')['whole_controller_engineering_seconds_through_closeout']==3.156,'old v4 accounting')
    save(HERE/'INTEGRATION_DIFF.json',dict(v4_review_base=BASE,watcher_sha256=sha(HERE/'storage.py'),timing_sha256=sha(HERE/'timing.py'),watcher_exactly_unchanged=True,
        numerical_host_cpp_identical=sha(HERE/'generated/host.cpp')==sha(v4/'generated/host.cpp'),fixture_only_run_id=(HERE/'generated/fixture.hpp').read_bytes()==(v4/'generated/fixture.hpp').read_bytes().replace(b'b570-supervised-numerical-v4-20261016-01',RUN_ID.encode()),
        supervisor_diff=list(difflib.unified_diff((v4/'supervisor.py').read_text().splitlines(),(HERE/'supervisor.py').read_text().splitlines(),fromfile='v4/supervisor.py',tofile='v5/supervisor.py')),
        changes='External bounded PowerShell pipe capture/job ownership/gate and external budget charge; numerical rules/backends unchanged',v4_failure_preserved=True))
    p=plan();save(HERE/'PLAN.json',p);oldf0=load(OLD/'F0.json');runtime=OUT/'build/Release'
    sourcefiles=[dict(path=str(HERE/name),sha256=h) for name,h in sources.items()]
    legacy_paths=subprocess.check_output([GIT,'-C',str(ROOT),'ls-files','--full-name','--',str(OLD)],text=True).splitlines()
    # Git paths are repository-relative, ROOT is benchmark-relative.
    repo=ROOT.parents[1];legacy_files=[dict(path=str(repo/name),sha256=sha(repo/name)) for name in legacy_paths]
    inherited=[]
    for name,h in oldf0['sources'].items():
        need(sha(ROOT/name)==h,'old numerical source drift');inherited.append(dict(path=str(ROOT/name),sha256=h))
    for row in oldf0['history_files']:need(sha(ROOT/row['path'])==row['sha256'],'earlier history drift');inherited.append(dict(path=str(ROOT/row['path']),sha256=row['sha256']))
    build=load(OLD/'BUILD_INPUTS.json')
    for row in build['files']+build['frozen_backend_sources']:
        need(sha(row['path'])==row['sha256'],'frozen build/source drift');inherited.append(dict(path=row['path'],sha256=row['sha256']))
    inputs=load(OLD/'INPUTS.json')
    for row in inputs:need(sha(row['path'])==row['sha256'],'original input bytes');inherited.append(dict(path=row['path'],sha256=row['sha256']))
    oldraw=ROOT/'host_outputs/aligned_numerical_v2/b570-aligned-numerical-v2-20261015-01';manifest=load(OLD/'results/RAW_MANIFEST.json')
    rawfiles=[]
    for row in manifest['files']:
        path=oldraw/row['path'];need(sha(path)==row['sha256'],'old raw bytes changed');rawfiles.append(dict(path=str(path),sha256=row['sha256']))
    previous=load(OLD/'results/RESULT.json');need(previous['totals']['experiment_host_attempts']==37 and abs(previous['totals']['owned_seconds']-41.327)<1e-8 and previous['numerical']['unstarted']==124,'old accounting unchanged')
    dependencies=[]
    for row in oldf0['dependencies']:
        path=runtime/pathlib.Path(row['path']).name;need(sha(path)==row['sha256'],'identical numerical DLL');dependencies.append(dict(path=str(path),sha256=sha(path)))
    for row in oldf0['driver_files']:need(sha(row['path'])==row['sha256'],'driver drift')
    environment={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))};need(environment==oldf0['environment'],'environment drift')
    exe=dict(path=str(runtime/'supervised-host-v5.exe'),sha256=sha(runtime/'supervised-host-v5.exe'))
    py=dict(path=sys.executable,sha256=sha(sys.executable))
    save(HERE/'EXECUTION_BINDING.json',dict(run_id=RUN_ID,review_base=BASE,source_files=sourcefiles,legacy_files=legacy_files,
        inherited=inherited,executable=exe,dependencies=dependencies,driver_files=oldf0['driver_files'],python=py,environment=environment,
        plan_sha256=sha(HERE/'PLAN.json'),CPU_tests_sha256=sha(receipt),new_monitor_policy_sha256=sha(HERE/'POLICY.md'),old_numerical_policy_sha256=sha(OLD/'RULES.md')))
    binding=sha(HERE/'EXECUTION_BINDING.json');wirelist=[];(HERE/'wires').mkdir()
    for s in p['slots']:
        path=HERE/'wires'/(s['id']+'.wire');path.write_bytes(serialize(s,binding))
        wirelist.append(dict(slot_id=s['id'],path='wires/'+path.name,sha256=sha(path),bytes=path.stat().st_size))
    save(HERE/'WIRES.json',wirelist)
    # One compact CPU evidence capsule, including failed preparations, not
    # another numerical report suite or fabricated native/device observation.
    files=sorted(p for p in (OUT/'CPU_TESTS').rglob('*') if p.is_file());entries=[]
    with zipfile.ZipFile(HERE/'CPU_EVIDENCE.zip','x',zipfile.ZIP_DEFLATED) as z:
        for path in files:
            name=str(path.relative_to(OUT/'CPU_TESTS')).replace('\\','/');entries.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path)));z.write(path,name)
    with zipfile.ZipFile(HERE/'CPU_EVIDENCE.zip') as z:
        for row in entries:need(hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'],'CPU evidence readback')
    save(HERE/'CPU_EVIDENCE_MANIFEST.json',dict(files=entries,archive_sha256=sha(HERE/'CPU_EVIDENCE.zip'),archive_bytes=(HERE/'CPU_EVIDENCE.zip').stat().st_size,
        no_GPU_libraries_loaded=True,native_GPU_hosts=0,device_queries=0,graph_computes=0))
    with zipfile.ZipFile(HERE/'NATIVE_BINARY.zip','x',zipfile.ZIP_DEFLATED) as z:z.write(exe['path'],'supervised-host-v5.exe')
    local=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    bound=sourcefiles+legacy_files+inherited+[exe,py]+dependencies+oldf0['driver_files']
    v3=ROOT/'host/supervised_numerical_v3';v3f0=load(v3/'F0.json')
    for row in v3f0['bound_files']:
        need(sha(row['path'])==row['sha256'],'v3 frozen identity drift');bound.append(row)
    v3_paths=subprocess.check_output([GIT,'-C',str(ROOT),'ls-files','--full-name','--',str(v3)],text=True).splitlines()
    bound.extend(dict(path=str(repo/name),sha256=sha(repo/name)) for name in v3_paths)
    bound.append(dict(path=str(runtime/'metadata-host-v5.exe'),sha256=sha(runtime/'metadata-host-v5.exe')))
    for row in load(v4/'F0.json')['bound_files']:need(sha(row['path'])==row['sha256'],'v4 frozen source drift');bound.append(row)
    v4_paths=subprocess.check_output([GIT,'-C',str(ROOT),'ls-files','--full-name','--',str(v4)],text=True).splitlines()
    bound.extend(dict(path=str(repo/name),sha256=sha(repo/name)) for name in v4_paths)
    launcher_initial=load(pathlib.Path(tests['evidence_root'])/'LAUNCHER/normal/external_logs/INITIAL.json')
    bound.extend(dict(path=r['path'],sha256=r['sha256']) for r in launcher_initial['cpu_modules'])
    # Bind actual Python runtime files without loading a numerical backend.
    for row in modules():bound.append(dict(path=row['path'],sha256=row['sha256']))
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and pathlib.Path(path).is_file():bound.append(dict(path=str(pathlib.Path(path).resolve()),sha256=sha(path)))
    bound += [dict(path=str(path),sha256=sha(path)) for path in local]
    bound=list({r['path']:dict(path=r['path'],sha256=r['sha256']) for r in bound}.values())
    save(HERE/'F0.json',dict(status='AWAITING_EXPLICIT_NEW_AUTHOR_APPROVAL_GPU_UNSTARTED',review_base=BASE,run_id=RUN_ID,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_binding_sha256=binding,bound_files=bound,old_raw_files=rawfiles,
        executable=exe,python=py,dependencies=dependencies,driver_files=oldf0['driver_files'],environment=environment,limits=LIMITS,
        historical_raw_manifests=[dict(manifest=str(v3/'results/RAW_MANIFEST.json'),root=str(ROOT/'host_outputs/supervised_numerical_v3/b570-supervised-numerical-v3-20261015-01')),dict(manifest=str(v4/'results/RAW_MANIFEST.json'),root=str(v4rawroot))],
        launcher=dict(script=str(HERE/'launch.ps1'),capture_DLL=str(HERE/'LauncherCapture.dll'),powershell_executable='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
            external_log_root=str(EXTERNAL_LOG_ROOT),protected_roots=[str(HERE),str(OUT)],run_root=str(RUN),owner_sid=launcher_initial['owner_sid'],
            external_actual_bytes_cap=16*1024**2,external_and_export_reserved_bytes=EXTERNAL_RESERVED_BYTES,log_soft_bytes_per_stream=1048576,log_hard_bytes_per_stream=2097152,
            journal_hard_bytes=8*1024**2,initial_receipt_bytes_cap=131072,closing_receipt_bytes_cap=131072,pipe_capacity_sum_max=65536,read_chunk_bytes=4096,
            unknown_external_files='FAIL',existing_external_root='FAIL_NO_RESTART',stdout_stderr_file_creation='CreateNew before controller gate',append='bounded raw redirected pipes',close='job empty and both readers EOF; full size/hash/copy/archive audit after controller exit',
            PowerShell_launcher_processes=1,additional_post_controller_CPU_log_audit_processes=1,explicit_new_GPU_authorization_required=True),
        whole_controller_engineering_seconds=900,complete_slot_engineering_seconds=180,
        engineering_scope='Admission through closeout; includes native/control workers, supervision, all identity/numerical audits, cleanup, comparisons and receipt writes; not old v2 owned definition',
        separate_native_observed_lifetime=True,separate_post_exit_audit=True,actual_dynamic_device_alignment=None,required_deployment_alignment=64,
        experimental_hosts_max=69,graph_calls_max=68,additional_CPU_control_processes_max=138,
        monitor_sampler_threads=2,monitor_main_threads=1,auditor_threads=1,controller_main_threads=1,
        runtime_max_effective_gap_ns=1_000_000_000,numerical_rules_unchanged=True,old_samples_imported=0,
        controller_storage_watch_threads=2,active_slot_reserved_bytes=32*1024**2,active_slot_files_cap=256,
        registration_status='CPU_QUALIFIED_PENDING_SEPARATE_GPU_AUTHORIZATION',budget_derivation_sha256=sha(HERE/'BUDGET.json'),
        new_GPU_hosts_started=0,device_queries=0,model_requests=0,expected_crashes=0,retries=0,warmups=0,
        S2_S3='NOT_ADMITTED',unique_entry='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '+str(HERE/'launch.ps1')+' -AuthorApprovedF0Sha <this exact F0 SHA256>',modules=modules()))
    actual=sum(p.stat().st_size for root in (HERE,OUT) for p in root.rglob('*') if p.is_file());need(actual<1024**3,'1GiB full v4 artifact budget')
    print(dict(F0_sha256=sha(HERE/'F0.json'),run_id=RUN_ID,experimental_hosts=69,CPU_control_workers_max=138,CPU_tests=tests['methods'],prepared_bytes=actual,GPU_started=0))

if __name__=='__main__':main()
