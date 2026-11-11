"""Actual prospective S1 F0, with S1A-only human approval still required."""
import json,os,platform,shutil,sys,time
from pathlib import Path
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    assert not (ROOT/'execution_ledger').exists(),'no S1 start permitted in S0'
    tests=json.loads((ROOT/'CPU_ACCEPTED/S0_TESTS.json').read_bytes());assert tests['status']=='PASS'
    original=json.loads((ROOT/'PARENT_SOURCE_HASHES.json').read_bytes());delta={};source=ROOT/'native/source'
    for name,h in original.items():
        current=sha(source/name)
        if current!=h:
            delta[name]=dict(parent=h,current=current);p=ROOT/'native_delta'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,p)
    for name in ('hs113_graph.h','native113.cpp','native_cache113.cpp'):
        assert sha(source/name)==sha(ROOT/name);delta[name]=dict(parent=None,current=sha(source/name))
    save(ROOT/'ACTUAL_SOURCE_DELTA.json',dict(files=delta,parent='PR104 authenticated E1 source',parent_inventory_sha256=sha(ROOT/'PARENT_SOURCE_HASHES.json')))
    identity=json.loads((ROOT/'IDENTITY_RECONCILIATION.json').read_bytes());old=json.loads(Path('D:/hs-qb-confirmation-v02/FREEZE.json').read_bytes());routes=json.loads(Path('D:/hs-qb-confirmation-v02/RUNTIME_MANIFEST.json').read_bytes())
    from wire import recipe,command,FAMILIES,ARMS
    models={f:v['models'] for f,v in json.loads(Path('D:/hs104-e1-v1/MODEL_CONTRACT.json').read_bytes())['families'].items()}
    original_R={f:next(x for x in old['files'] if x['path'].endswith('/llama-server.exe') or x['path'].endswith('\\llama-server.exe')) for f in FAMILIES}
    entries=[]
    for family in FAMILIES:
        for arm in ARMS:
            path=original_R[family]['path'] if arm=='R' else str(ROOT/'native/build/bin/llama-server.exe')
            entries.append(dict(family=family,arm=arm,binary=path,sha256=sha(path),condition=recipe(arm,'QH_C'),
                QH_selection='placeholder bound to C-then-D complete census rule; no QH variant selected yet' if 'QH' in arm else None,
                command_for_C_variant_only=command(family,arm,models,'QH_C',original_R),GPU_model_load_qualification='NOT_STARTED_S0'))
    save(ROOT/'RUNTIME_MANIFEST.json',dict(original_PR98_PR104_routes_15=routes['routes'],new_actor_routes_21=entries,
        numerical_DLLs=identity['numerical_DLLs'],effective_draft_free_k=0,C_speculative_k=3,target_mask=3,original_R_unchanged=True))
    profiler=dict(status='PROFILE_UNAVAILABLE_PLACEMENT_ONLY',nsys_PATH=shutil.which('nsys'),ncu_PATH=shutil.which('ncu'),
        standard_Nsight_installation_dirs=[str(p) for p in Path('C:/Program Files/NVIDIA Corporation').glob('*Nsight*')],
        CUDA_toolkit_standard_root_exists=Path('C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA').exists(),CUDA_profiler_invocations=0,
        ABI_qualification='No compatible installed trace adapter admitted; no driver/toolkit installation or upgrade')
    save(ROOT/'PROFILE_AVAILABILITY.json',profiler)
    paths=set()
    for p in ROOT.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or p.name.endswith('.lock'):continue
        if 's0_ledger' in p.parts and 'freeze_actual_S1_F0' in p.name:continue
        if 'build' in p.parts and 'native' in p.parts:
            if p.suffix!='.exe' and p.name not in ('CMakeCache.txt','build.ninja','compile_commands.json'):continue
        if 'registration' in p.parts:continue
        paths.add(p.resolve())
    for x in old['files']:paths.add(Path(x['path']).resolve())
    for name in identity['numerical_DLLs']:paths.add(Path(identity['numerical_runtime_directory'])/name)
    for c in json.loads((ROOT/'FULL_SNAPSHOTS.json').read_bytes())['contexts']:
        for name,h in c['registry'].items():
            p=Path(c['root'])/name;assert sha(p)==h;paths.add(p)
        for arm in ('MQ','PQ','QB'):
            for repeat in (0,1):
                d=Path('D:/hs104-authenticated-final-restore/E1/data')/f'operators/{c["index"]:03d}/{arm}-r{repeat}'
                for p in d.iterdir():
                    if p.is_file():paths.add(p)
    oldbuild=json.loads(Path('D:/hs104-e1-v1/NATIVE_BUILD.json').read_bytes())
    for row in oldbuild['attempts']:
        if row['label']=='configure':
            paths.add(Path(row['command'][0]));paths.add(Path(next(s.split('=',1)[1] for s in row['command'] if s.startswith('-DCMAKE_CXX_COMPILER='))));paths.add(Path(next(s.split('=',1)[1] for s in row['command'] if s.startswith('-DCMAKE_MAKE_PROGRAM='))))
    paths.add(Path(shutil.which('nvidia-smi')))
    pins=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]
    # The actual standalone binary exports no automatic GPU entry. Human
    # approval + authenticated F0 are required by the separate controller.
    save(ROOT/'registration/S1_F0.json',dict(schema=1,phase='S1_PREPARED_NOT_AUTHORIZED',prepared_epoch=time.time(),design='0fba42fe8732527ca99ceb9c9ee67e93b18e9d80',
        PR104='f997262d6b0accb126a1217c9356745cc8bbf708',PR110='dae5aea9f9009a686196dd89981c0ae9699ae612',files=pins,
        runtime_directory=identity['numerical_runtime_directory'],numerical_DLLs=identity['numerical_DLLs'],execution_root='D:/hs113-s1-v1',
        stage_limits=dict(support_host_attempts=1,operator_host_attempts=1009,graph_computes=2808,explicit_warmups=288,owned_seconds=7200,derived_bytes=4*1024**3),
        next_requested_authorization=dict(stage='S1A_SUPPORT_ONLY',operator_hosts=1,graph_computes=0,model_requests=0,native_host_seconds_cap=240,support_raw_bytes_cap=128*1024**2),
        later_numeric_timing_and_model_authorization='NOT_GRANTED; selected census must be sealed/authenticated before any outputs; exact new author approval required',
        admission_policy=dict(**old['host_identity'],nvidia_smi=shutil.which('nvidia-smi'),AC_required=1,headroom_MiB_min=512,idle_util_max=5,temperature_C_max=55,readiness_queries=1,readiness_failure='retain and stop, no automatic GPU retry'),
        profiler=profiler,operator_environment=dict(GGML_CUDA_DISABLE_GRAPHS='1',rationale='registered graph calls only; no implicit CUDA Graph capture; same for all standalone layouts'),
        observation='source-bound completed inclusive host timer; raw ns audited; no exclusive kernel or DRAM claim; inherited R checkpoint semantics remain distinct',
        numerical_selection='QH_C only if every actual registered executable node supported; else QH_D if complete; else stop. Never use numeric/latency outcomes.',
        full_uncropped_snapshots=72,source_shape_superset=96,actual_GGML_registry_graphs=1680,
        CPU_tests=tests,stage_results=dict(actual_CUDA_support='NOT_QUERIED',CUDA_placement='NOT_EXECUTED',numerical='NOT_EXECUTED',full_request='NOT_EXECUTED',cost_gain='NOT_MEASURED'),
        current_python=sys.version,current_platform=platform.platform(),new_GPU_model_operator_device_queries=0))
    print(json.dumps(dict(frozen_files=len(pins),F0_sha256=sha(ROOT/'registration/S1_F0.json'),next_stage='S1A_SUPPORT_ONLY_PENDING_AUTHOR')))
if __name__=='__main__':main()
