"""Freeze only after fresh CPU tests. Does not launch the GPU executable."""
import datetime
import hashlib
import pathlib
import subprocess
import sys
import zipfile
import importlib.util
from panel_common import HERE,ROOT,RUN,RUN_ID,LIMITS,load,save,sha,modules,need
_spec=importlib.util.spec_from_file_location('_aligned_panel_prepare',HERE/'prepare.py')
_prepare=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_prepare)
source_files,GIT,BASE,OUT=(_prepare.source_files,_prepare.GIT,_prepare.BASE,_prepare.OUT)

def main():
    before=modules();need(not (HERE/'F0.json').exists(),'immutable F0 already exists')
    need(not RUN.exists(),'new numerical panel has started unexpectedly')
    binding=load(HERE/'EXECUTION_BINDING.json')
    current={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in source_files()}
    need(all(binding['sources'].get(k)==v for k,v in current.items()),'source changed since CPU tests; prepare again prospectively')
    for name,h in binding['sources'].items():need(sha(ROOT/name)==h,'source drift')
    tests=sorted((HERE/'preparation').glob('CPU_TESTS_*.json'));need(tests and load(tests[-1])['success'],'latest CPU tests must pass')
    cpu=load(HERE/'CPU_NATIVE_MANIFEST.json');need(cpu['requests']==161 and cpu['metadata_graphs']==240 and cpu['device_queries']==0,'native CPU inventory')
    runtime=OUT/'build/Release';prior=load(ROOT/'host/alignment_review_v1/DIAGNOSTIC_F0.json')
    history_names=['host/S1_F0.json','host/S1_RESULT.json','host/S1_RAW.zip','host/S1_RAW_MANIFEST.json',
        'host/alignment_review_v1/DIAGNOSTIC_F0.json','host/alignment_diagnostic_result_v1/RESULT.json',
        'host/alignment_diagnostic_result_v1/DIAGNOSTIC_RAW.zip','host/alignment_diagnostic_result_v1/RAW_MANIFEST.json']
    old=load(ROOT/'host/S1_RESULT.json');diag=load(ROOT/'host/alignment_diagnostic_result_v1/RESULT.json')
    need(old['attempts']==2 and abs(old['owned_wall_s']-5.109)<1e-8 and old['unstarted_slots']==159,'old S1 accounting')
    need(diag['attempts']==7 and abs(diag['owned_wall_s']-13.172)<1e-8 and diag['completed_numerical_graphs']==5 and diag['failed_graphs']==2,'diagnostic accounting')
    for item in prior['driver_files']:need(sha(item['path'])==item['sha256'],'driver changed')
    build=load(HERE/'BUILD_INPUTS.json')
    for item in build['files']+build['frozen_backend_sources']:need(sha(item['path'])==item['sha256'],'frozen build/source identity changed')
    binaries=[runtime/'aligned-metadata-v2.exe',runtime/'aligned-host-v2.exe']
    with zipfile.ZipFile(HERE/'BINARIES.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in binaries:z.write(p,p.name)
    with zipfile.ZipFile(HERE/'BINARIES.zip') as z:
        for p in binaries:need(hashlib.sha256(z.read(p.name)).hexdigest()==sha(p),'binary archive readback')
    save(HERE/'BINARY_MANIFEST.json',dict(files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in binaries],
        archive_sha256=sha(HERE/'BINARIES.zip'),GPU_host_launched=False,CPU_binary_executions=len(tests)))
    artifacts={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix=='.json'}
    for name in ('wires','references'):
        for p in (HERE/name).iterdir():artifacts[str(p.relative_to(HERE)).replace('\\','/')]=sha(p)
    artifacts[cpu['archive_path']]=cpu['archive_sha256']
    artifacts[str(tests[-1].relative_to(HERE)).replace('\\','/')]=sha(tests[-1])
    f0=dict(study='b570-aligned-numerical-v2',run_id=RUN_ID,status='AWAITING_EXPLICIT_AUTHOR_APPROVAL_GPU_UNSTARTED',
        review_base=BASE,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        execution_binding_sha256=sha(HERE/'EXECUTION_BINDING.json'),sources=binding['sources'],artifacts=artifacts,
        executable=dict(path=str(runtime/'aligned-host-v2.exe'),sha256=sha(runtime/'aligned-host-v2.exe')),
        python=dict(path=sys.executable,sha256=sha(sys.executable)),
        dependencies=[dict(path=str(runtime/name),sha256=sha(runtime/name)) for name in ('ggml-base.dll','ggml-vulkan.dll')],
        driver_files=prior['driver_files'],environment=binding['environment'],limits=LIMITS,
        history_files=[dict(path=name,sha256=sha(ROOT/name)) for name in history_names],
        logical_inputs='Original16 S1 serialized input files and accurate logical bytes, exposed synthetic operands',
        primary_candidate='QH_C fixed before outputs',expected_alignment_bytes=64,current_measured_alignment_bytes=None,
        census=dict(charged_hosts=1,complete_graphs=80,graph_calls=0,all_required=True,selection=False),
        numerical_hosts=160,q1_hosts_first=40,independent_repeats=2,expected_crash_slots=0,
        comparison_rules_source='host/aligned_numerical_v2/RULES.md',FP64_tolerance=None,
        resource_scope='All v2 directory/output-root bytes plus one raw export reserve; owned child wall includes setup/copy/logging, not graph latency',
        stop='Any assertion/crash, unsupported graph, wrong device/binding, input mutation, nonfinite output, q1 mismatch, same-mode repeat difference, budget/observer violation or source/runtime drift',
        q_gt1_finite_differences='Retain all10 mode pairs and descriptive FP64 errors; no adaptive tolerance or representation selection',
        old_S1_resume=False,diagnostic_repetition=False,S2_S3='NOT_ADMITTED',performance_experiments=False,
        new_GPU_hosts_started=0,new_device_queries=0,new_model_requests=0,modules_before=before,modules_after=modules())
    save(HERE/'F0.json',f0)
    need(not subprocess.check_output([GIT,'-C',str(ROOT),'diff','--name-only',BASE],text=True).strip(),'old tracked history changed')
    size=sum(p.stat().st_size for base in (HERE,OUT) for p in base.rglob('*') if p.is_file())
    need(size<LIMITS['output_bytes'],'prepared artifact budget')
    save(HERE/'PREPARATION_RESULT.json',dict(status='CPU_PREPARATION_COMPLETE_GPU_UNSTARTED',F0_sha256=sha(HERE/'F0.json'),
        CPU_test_methods=load(tests[-1])['methods'],formal_serialized_wires=161,native_decoded_descriptors=240,
        reference_operands=16,representations=5,repeats=2,planned_hosts=161,planned_graph_calls=160,
        prepared_bytes_before_receipt=size,old_S1_and_seven_diagnostic_accounting_unchanged=True,
        next_step='Exact F0 author confirmation only; no GPU command run during preparation'))
    print(dict(F0_sha256=sha(HERE/'F0.json'),planned_hosts=161,graphs=160,CPU_tests=load(tests[-1])['methods'],GPU_started=0))

if __name__=='__main__':main()
