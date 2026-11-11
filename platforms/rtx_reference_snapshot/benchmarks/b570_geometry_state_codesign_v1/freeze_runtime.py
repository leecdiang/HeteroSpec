"""Bind built native bytes and actual 80-slot wire objects without executing them."""
from pathlib import Path
from protocol import *
from host_request import admit,readback
ROOT=Path(__file__).resolve().parent
def pin(p):return dict(path=str(p),name=p.name,bytes=p.stat().st_size,sha256=file_sha(p))
def main():
 assets=read_json(ROOT/'p0/ASSETS.json');roles={}
 for role,path,exe,kind in [('old',ROOT/'_host/pr97/baseline/pr92_restore/build/Release','b570-evidence-worker.exe','ORIGINAL_PR92'),('new',ROOT/'_host/build/Release','b570-geometry-worker.exe','PR108_GRAPH_PORT')]:
  mods=[pin(path/n) for n in [exe,'llama-b570-memory.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll']]
  roles[role]=dict(role=role,kind=kind,binary=str(path/exe),sha256=mods[0]['sha256'],modules=mods,files=[pin(path/'COUNTER_HASH.txt')])
 for name in ('ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'):
  assert next(x['sha256'] for x in roles['old']['modules'] if x['name']==name)==next(x['sha256'] for x in roles['new']['modules'] if x['name']==name),'Arithmetic backend drift'
 source=[dict(path=str(p.relative_to(ROOT)).replace(chr(92),'/'),bytes=p.stat().st_size,sha256=file_sha(p)) for p in sorted((ROOT/'_host/source').rglob('*')) if p.is_file()]
 runtime=dict(schema=1,roles=roles,models=assets['models'],driver_files=assets['driver_files'],driver_version=assets['driver_version'],import_libraries=assets['import_libraries'],isolated_llama_source_files=source,numerical_backend_DLL_bytes_unchanged=True,original_R_source='_host/pr97/baseline/pr92_restore/native/worker.cpp',PR101_source_git_blob='c45b45b26d998bbbcfe20a115c319041b8e167a8',new_worker_executed=False)
 write_new(ROOT/'p0/RUNTIME.json',runtime)
 plan=read_json(ROOT/'p0/PLAN_P1.json');validate_plan(plan);cases={c['id']:c for c in plan['panel']}
 wires=[readback(admit(s,cases[s['task']],runtime)) for s in plan['slots']]
 write_new(ROOT/'p0/WIRES_P1.json',wires)
 write_new(ROOT/'p0/SERIALIZER_ADMISSION.json',dict(status='PASS_80_ACTUAL_SERIALIZED_REQUESTS_CPU_ONLY',slots=len(wires),wire_sha256=digest(wires),runtime_sha256=digest(runtime),actual_GPU_geometry='NOT_OBSERVED_P0',all_sent_objects_are_the_admitted_immutable_bytes=True,model_process_starts=0))
 print('80 real wire mappings admitted; GPU geometry NOT_OBSERVED; native starts 0')
if __name__=='__main__':main()
