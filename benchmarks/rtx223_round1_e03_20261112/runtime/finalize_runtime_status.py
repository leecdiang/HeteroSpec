from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((HERE/'build-v3/BUILD.json').read_bytes())
bindings=json.loads((HERE/'AS_BUILT_BINDINGS_FINAL.json').read_bytes())
metadata=json.loads((HERE/'RUNTIME_METADATA_EXPECTED.json').read_bytes())
old=json.loads((HERE/'delta-v2/ORIGIN_MANIFEST.json').read_bytes())['files']
delta=json.loads((HERE/'delta-v2/OVERRIDES.json').read_bytes())
expected={**old,**{x['target_relative_path']:x['sha256'] for x in delta['overrides']}}
final=json.loads((HERE/'FINAL_SOURCE_IDENTITIES.json').read_bytes())['source_files_sha256']
if expected!=final:raise RuntimeError('origin+delta does not reconstruct final source manifest')
if any(sha(HERE/'delta-v2'/x['delta_relative_path'])!=x['sha256'] for x in delta['overrides']):raise RuntimeError('delta file identity')
if sha(HERE/'build-v3/bin/ggml-cuda.dll')!=build['DLL_sha256']:raise RuntimeError('numerical DLL changed')
commands=json.loads((HERE/'build-v1/COMMANDS.json').read_bytes())
repairs=json.loads((HERE/'build-v3/COMPILE_RECEIPTS.json').read_bytes())
flags=[x for c in commands for x in c['argv']]+[x for c in repairs if c['kind']=='FRESH_REPAIR_COMPILE' for x in c['argv']]
if any('HS_LB_CPU_TEST_ONLY' in x or 'GGML_CUDA_USE_PDL' in x or x=='-DGGML_CUDA_USE_GRAPHS' for x in flags):raise RuntimeError('forbidden compile policy')
status={'schema':'heterospec.e03.runtime-final-status.v1','decision':'INCONCLUSIVE','scope':'actual numerical CUDA DLL linked; no normal DLL initialization or GPU use',
    'gates':{'C_runtime_source_dispatch':'PASS_SOURCE_ONLY','numerical_DLL_link':'PASS','normal_numerical_DLL_LoadLibrary':'NOT_RUN_BLOCKED',
        'metadata_exports_called_in_numerical_DLL':'NOT_RUN','GPU_runtime_C_selection':'NOT_RUN','native_66_cell_qualification':'NOT_RUN','numerical_bytes':'NOT_RUN','operator_or_service_timing':'NOT_RUN'},
    'DLL':bindings['DLL'],'compile_policy':{'arch':'sm_120a','original_fast_math_flags_retained':True,'graphs':'disabled','NCCL':'disabled','VMM':'disabled','PDL':'disabled in all recorded compile arguments','CPU_TEST_ONLY':False},
    'model_requests':0,'target_rows':0,'draft_rows':0,'CUDA_contexts':0,'kernel_launches':0,'native_GPU_seconds':0,
    'actual_loaded_numerical_modules':None,'metadata_function_source':metadata,
    'resource_metadata':'COMPILER_RESOURCES.json','all_physical_launch_budget':'NOT_QUALIFIED; native configure remains -6',
    'first_batch':{'translation_units':145,'successes':144,'failures':1,'seconds':617.625,'not_globally_source_frozen':'One superseded provider body synced mid-batch; exact time unknown, old preserved'},
    'final_link':{'reused_objects':141,'fresh_objects':4,'seconds':build['seconds'],'exact_provider_implementation_objects':1},
    'artifact_reconstruction':{'old_members':len(old),'overrides':len(delta['overrides']),'delta_bytes':sum((HERE/'delta-v2'/x['delta_relative_path']).stat().st_size for x in delta['overrides']),
        'origin_plus_delta_matches_complete_final_manifest':True,'materializer':'materialize_final_source.py','fresh_builder':'build_runtime.py --source final-source --out new-output --jobs 2'},
    'source_and_as_built_binding':'AS_BUILT_BINDINGS_FINAL.json','failure_history':'PREPARATION_FAILURES.json',
    'engineering_total_wall_seconds':None,'compiler_wall_is_not_service_latency':True,
    'old_numerical_sources_and_DLLs_modified':False,'normal_DLL_initialization_not_conflated_with_PE_mapping':True}
(HERE/'STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf8');print(json.dumps(status))
