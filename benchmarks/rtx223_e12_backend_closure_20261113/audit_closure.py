"""Narrow reuse/source audit and read-only host/NVML snapshot; no CUDA runtime."""
from pathlib import Path
import json,hashlib,subprocess,datetime,importlib.util
p=Path(__file__).resolve().parent;e=p.parent/'rtx223-e11-u-contract';s=e/'full-backend-002/src';sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(name,obj):
 with (p/name).open('x',encoding='utf8') as f:json.dump(obj,f,indent=2)
verified=json.loads((e/'DELIVERY_FINAL_VERIFIED.json').read_bytes());assert verified['head']=='c8e5ea070ac393d7513903e0ec261dfce4554a49'
expected={x['path']:x for x in verified['remote_blobs']};reused=[]
for name in ['RESULT.json','ANALYSIS.json','ALL_SAMPLES.csv','ALL_PAIRS.csv','NUMERICAL_CONTRACTS_ZH.md','BACKEND_BOUNDARIES_ZH.md','PERFORMANCE_DECISION.json','QUALIFICATION_NATIVE_RESULT.json','TIMING_NATIVE_RESULT.json','FAMILY_FINAL.jsonl']:
 q=e/'delivery'/name;assert sha(q)==expected[name]['sha256']
 reused.append(dict(expected[name],local=str(q)))
result=json.loads((e/'delivery/RESULT.json').read_bytes());analysis=json.loads((e/'delivery/ANALYSIS.json').read_bytes())
assert result['budget']['explicit_application_permits']==400 and result['budget']['global_reserved']==430
assert analysis['all_samples']==48 and analysis['post_batch_checks']==48
put('REUSE_VERIFIED.json',dict(pass_=True,utc=utc(),parent_head=verified['head'],files=reused,scope='Only reused published results/contracts/raw samples/ledger;no whole-history or GGUF rehash',old_failures_unchanged=True))
paths=['ggml/src/ggml-cuda/ggml-cuda.cu','ggml/src/ggml-cuda/mmq-few.cu','ggml/src/ggml-cuda/quantize.cu','ggml/src/ggml-cuda/common.cuh','ggml/src/ggml-cuda/graph.cuh','ggml/include/ggml-cuda.h','ggml/include/ggml-backend.h','ggml/include/ggml-alloc.h','ggml/include/ggml.h']
frozen=json.loads((e/'full-backend-002/INPUTS.json').read_bytes());sources=[]
needles={'ggml-cuda.cu':['static void ggml_cuda_mul_mat(','const bool use_mmq_few =','ggml_cuda_mul_mat_q_few(ctx','static void ggml_cuda_graph_launch_chunk(','cudaGraphLaunch(graph->instances[idx]','for (cudaGraphExec_t instance','cudaGraphLaunch(instance','static enum ggml_status ggml_backend_cuda_graph_compute(','if (!graph->warmup_complete)','ggml_cuda_kernel_can_use_pdl(','cudaEventCreateWithFlags(&event, cudaEventDisableTiming)','ggml_backend_t ggml_backend_cuda_init('], 'mmq-few.cu':['static bool mmq_few_is_constant(','void ggml_cuda_mul_mat_q_few(','ggml_cuda_pool_alloc<int4> src1_q','quantize_mmq_few_q8_1_cuda(','bool ggml_cuda_should_use_mmq_few(','static int ggml_cuda_mmq_few_min_ncols('], 'quantize.cu':['void quantize_mmq_few_q8_1_cuda(','ggml_cuda_kernel_launch(quantize_mmq_few_q8_1<MMQ_Q8_1_DS_LAYOUT_D4>'], 'common.cuh':['cudaStream_t stream(int device, int stream)','static __inline__ void ggml_cuda_kernel_launch(','cudaLaunchKernelEx(&pdl_cfg.cfg'], 'graph.cuh':['bool is_enabled() const','getenv("GGML_CUDA_DISABLE_GRAPHS")']}
for rel in paths:
 q=s/rel;assert sha(q)==frozen[str(q)]['sha256']
 text=q.read_text(encoding='utf8').splitlines();anchors=[]
 for needle in needles.get(q.name,[]):
  matches=[i+1 for i,line in enumerate(text) if needle in line];assert matches,(rel,needle)
  anchors.append(dict(symbol=needle,lines=matches))
 sources.append(dict(path=rel,local=str(q),sha256=sha(q),bytes=q.stat().st_size,anchors=anchors,unchanged_since_full_build=True))
identity=json.loads((e/'FULL_BACKEND_BUILD_IDENTITY_V3.json').read_bytes());dll=Path(identity['path']);assert sha(dll)==identity['sha256']
put('SOURCE_ARTIFACT_BINDING.json',dict(pass_=True,utc=utc(),fixed_commit='0fb8f157702702f33f4e018de8701b2569a1bc28',full_cuda_DLL=dict(path=str(dll),sha256=sha(dll),bytes=dll.stat().st_size,loaded_this_task=False),sources=sources,link_only=json.loads((p/'link-only/RESULT.json').read_bytes())))
spec=importlib.util.spec_from_file_location('e12management',e/'observation_v3.py');ob=importlib.util.module_from_spec(spec);spec.loader.exec_module(ob)
nvml=json.loads((e/'DEPLOYMENT.json').read_bytes())['modules']['nvml.dll'];assert sha(nvml['path'])==nvml['sha256']
m=ob.Management(nvml['path'])
try:
 m.start();total,free,used,disk,pids=m.sample(p);util=m.utilization()
 gpu=dict(utc=utc(),read_only_NVML=True,nvml_sha256=nvml['sha256'],fixed_UUID=ob.UUID,compute_pids=pids,utilization_percent=util,temperature_c=m.temperature,total_bytes=total,free_bytes=free,used_bytes=used,disk_free_bytes=disk,CUDA_runtime_calls=0,numerical_DLL_loads=0,limits='Snapshot only;graphics/noncompute work or future tasks not excluded;not GPU execution admission')
finally:m.close()
put('GPU_READONLY.json',gpu)
cp=subprocess.run(['rg','--files','--hidden','-g','*.lock','-g','*.lease','-g','*lease.json','-g','!models/**','D:/HeteroSpec-PC'],capture_output=True,creationflags=0x08000000)
assert cp.returncode in (0,1)
host=json.loads((p/'HOST_INITIAL.private.json').read_bytes().decode('utf-8-sig'));threads=json.loads((p/'THREAD_SNAPSHOT.json').read_bytes())
put('HOST_SUMMARY.json',dict(utc=utc(),host_snapshot_start=host['start_utc'],host_snapshot_end=host['end_utc'],process_count=len(host['all_processes']),task_count=len(host['all_tasks']),competing_workers=host['competing_workers'],project_tasks=host['project_tasks'],project_services=host['project_services'],known_lease_paths={x:str(Path(x).exists()) for x in ['D:/HeteroSpec-PC/RTX_EXPERIMENT.lock','D:/HeteroSpec-PC/rtx223-e11-u-contract/runner.lease']},lock_inventory_rg_exit=cp.returncode,lock_inventory_paths=cp.stdout.decode('utf8').splitlines(),local_active_threads=[x for x in threads['entries'] if x.get('hostId')=='local' and x['status']=='active'],other_active_threads=[x for x in threads['entries'] if x.get('hostId')!='local' and x['status']=='active'],limits='Recent50 app inventory and current host snapshot only;no claim all external queues empty;no GPU job admitted'))
put('BUDGET.json',dict(schema='heterospec.e12.independent_closure.v1',authorization_limit=500,per_controlled_GPU_seconds=120,reserved=0,actual_explicit_application_kernel_calls=0,attempts=0,old_e11_limit=500,old_e11_reserved=430,old_e11_actual=400,old_e11_unchanged=True,status='CLOSED_UNSPENT_RUNTIME_GATE_NOT_IMPLEMENTED',physical_launch_hard_cap_proven=False,old4096='NOT_CLOSED',new_GPU_tasks_queued=0))
put('RESULT.json',dict(utc=utc(),status='CLOSED_WITH_LIMITED_MODERN_OPERATOR_REFERENCE',parent_head=verified['head'],gates=dict(pr237_reuse='PASS_NARROW_REVIEW',source_and_existing_DLL='PASS',public_API_compile_link='PASS_NOT_LOADED',shape_predicate='STATIC_ELIGIBLE_NOT_RUNTIME_PROVEN',host_snapshot='NO_CONFLICT_OBSERVED_NOT_RUNTIME_ADMISSION',full_backend_execution_control='BLOCKED_NOT_IMPLEMENTED',full_backend_U_quantization_access='BLOCKED_PRIVATE_TEMPORARY',full_backend_projection_timing='BLOCKED_PRIVATE_STREAM_AND_GRAPH_BOUNDARY',full_backend_qualification='NOT_RUN',full_backend_paired_timing='NOT_RUN',new_candidate='NOT_RUN_OUT_OF_SCOPE',service='NOT_RUN_OUT_OF_SCOPE'),reason='A public API caller links, but the required full path/quantizer oracle/projection boundary and default graph prelaunch controls need a new instrumented backend and re-admission;stop under bounded closure instruction',consumption=dict(model_loads=0,forward=0,numerical_DLL_loads=0,CUDA_initializations=0,GPU_contexts_created=0,explicit_application_kernel_calls=0),old_results='PR235 FAIL and PR237 independent-contract PASS/timings unchanged',termination='No new GPU runner/profile/queue/lease created;no processes terminated;no ACL/security changes',publication='Draft evidence only;no paper edits,submission,arXiv or merge'))
print(json.dumps(dict(reused_files=len(reused),source_files=len(sources),API_link='PASS',compute_pids=pids,host_workers=host['competing_workers'],GPU='NOT_RUN',budget_actual=0)))
