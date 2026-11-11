"""Freeze concrete S1 inputs/runtime/commands. No device or executable launch."""
import argparse, datetime, os, pathlib, sys
from common import ROOT, load, save, sha, modules
from inputs import write_input
sys.path.insert(0,str(ROOT))
import core, plan

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);a=p.parse_args();before=modules()
    output=ROOT/'host_outputs/S1_inputs';output.mkdir(exist_ok=False);inputs=[]
    for cell in plan.operator_cells():
        key=core.sha(cell);path=output/(key+'.input');digest=write_input(path,cell)
        inputs.append(dict(id=key,cell=cell,path=str(path),sha256=digest,bytes=path.stat().st_size))
    save(ROOT/'host/S1_INPUTS.json',inputs);save(ROOT/'host/S1_PLAN.json',plan.make_plan('operator'))
    runtime=load(a.old/'p0/RUNTIME.json');driver=[]
    for f in runtime['driver_files']:
        if pathlib.Path(f['path']).exists():driver.append(dict(path=f['path'],sha256=sha(f['path']),matches_old=sha(f['path'])==f['sha256']))
    assert all(x['matches_old'] for x in driver)
    executable=ROOT/'build/S1/qh-vulkan.exe'
    sources=[ROOT/'native/query_head.h',ROOT/'native/host/vulkan.cpp',ROOT/'native/host/oracle.hpp',ROOT/'native/host/CMakeLists.txt',ROOT/'host/common.py',ROOT/'host/run_s0.py',ROOT/'host/inputs.py',ROOT/'host/run_s1.py',ROOT/'host/prepare_s1.py',ROOT/'plan.py',ROOT/'evidence.py',ROOT/'core.py']
    f0=dict(study=core.STUDY,phase='S1',status='AWAITING_EXPLICIT_AUTHOR_APPROVAL',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        PR112_parent='7864716787fabb17cb613ed7125c180736c133ef',source_binding_sha256=sha(ROOT/'host/HOST_SOURCE_BINDINGS.json'),
        CPU_result_sha256=sha(ROOT/'host/S0_RESULT.json'),plan_sha256=sha(ROOT/'host/S1_PLAN.json'),input_manifest_sha256=sha(ROOT/'host/S1_INPUTS.json'),
        executable=dict(path=str(executable),sha256=sha(executable)),
        dependencies=[dict(path=str(f),sha256=sha(f)) for f in (ROOT/'build/S1').glob('*.dll')],
        sources={str(f.relative_to(ROOT)):sha(f) for f in sources},driver_files=driver,
        expected_backend_device_index=0,expected_description_contains='B570',
        environment={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))},
        limits=dict(operator_host_attempts=161,capability_only_attempts=1,planned_graph_attempts=160,model_processes=0,model_requests=0,owned_seconds=3600,per_attempt_seconds=180,RSS_bytes=8*1024**3,output_bytes=2*1024**3),
        monitoring=dict(operator_GPU_memory='actual backend-reported checkpoints: BACKEND_READY, BEFORE_GRAPH, AFTER_GRAPH, CLOSE; not periodic/continuous residency',min_backend_free_bytes=512*1024**2,
                        supervisor_nominal_period_ms=100,supervisor_max_actual_gap_ms=1000,supervisor_scope='owned process RSS, global available RAM, output/disk, wall; no periodic GPU claim',min_host_available_bytes=8*1024**3,min_disk_free_bytes=4*1024**3),
        command_template=[str(executable),'{attempt}/REQUEST.wire','{attempt}/raw.jsonl'],
        wire_schema='core.encode of study,F0_sha256,kind,cells(census) OR cell,mode,input,output_dir(graph). Actual bytes/SHA saved before each Popen.',
        census='all executable nodes from all16 inputs x5 modes, full ggml_backend_dev_supports_op; no graph_compute. Runtime modules must pass parent stdin gate first.',
        choice='QH_C if complete census admits all16; otherwise QH_D if all16; otherwise STOP. MQ/PQ mandatory. REPEAT4 rejection retained; unsupported nonprimary skipped.',
        placement='direct ggml_backend_graph_compute on actual Vulkan handle; every executable node actual buffer device must match; no scheduler/CPU backend available',
        numerical='all stage/final F32 vectors, full input before/after identity; repeat/q1 checks; valid finite PQ/QH difference retained; nonfinite/invalid/q1 mismatch stops',
        extra_probes=0,warmups=0,retries=0,automatic_S2=False,old_remaining_slots_reused=False,
        executable_launches_during_preparation=0,modules_before=before,modules_after=modules())
    save(ROOT/'host/S1_F0.json',f0)
    save(ROOT/'host/S1_PREPARATION_RECEIPT.json',dict(F0_sha256=sha(ROOT/'host/S1_F0.json'),inputs=16,operator_attempts_started=0,device_queries=0,GPU_operators=0,model_requests=0,modules=modules()))
    print(dict(F0_sha256=sha(ROOT/'host/S1_F0.json'),inputs=16,operator_attempts_started=0))

if __name__=='__main__':main()
