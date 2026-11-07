"""Post-run asset identity, actual offload and execution provenance checks."""
import re
from common import *
cfg=read(LOCAL/'CONFIG.json');assets=read(PUB/'ASSET_CHECK.json');checks={}
for name,h in assets['runtime_S_files'].items():checks['S/runtime/'+name]=sha(Path(cfg['runtime_S'])/name)==h
for role,m in cfg['models'].items():checks['Qwen/'+role]=sha(m['path'])==m['sha256']
for role,m in read(LOCAL/'F_MODEL_CONFIG.json')['models'].items():checks['SmolLM2/'+role]=sha(m['path'])==m['sha256']
native=read(PUB/'NATIVE_BUILD.json')
for name,h in native['all_runtime_dlls'].items():checks['new_runtime/'+name]=sha(LOCAL/'native/build/bin'/name)==h
for name,h in native['binaries'].items():checks['new_binary/'+name]=sha(LOCAL/'native/build/bin'/name)==h
for name,h in read(PUB/'S_F0.json')['code_sha256'].items():checks['immutable_S/'+name]=sha(Path(__file__).parent/name)==h
offload=[]
for p in (LOCAL/'runs').glob('**/server.log'):
    text=p.read_text(encoding='utf-8',errors='replace');counts=[(int(a),int(b)) for a,b in re.findall(r'offloaded (\d+)/(\d+) layers to GPU',text)];command=read(p.parent/'COMMAND.json');expected=2 if command['condition']['spec'] else 1
    actual=len(counts)==expected and all(a==b for a,b in counts)
    graph_count=text.count('CUDA Graph id ')
    offload.append({'run':p.parent.relative_to(LOCAL).as_posix(),'log_sha256':sha(p),'layer_counts':counts,'expected_model_count':expected,'full_GPU_layers_directly_logged':actual if counts else None,'CUDA_graph_execution_messages':graph_count,'requested_GPU_all':command['condition']['name']=='E32' or ('--n-gpu-layers' in command['command'] and command['command'][command['command'].index('--n-gpu-layers')+1]=='all'),'execution_evidence_present':actual or graph_count>0,'diagnostic_capture_callback':bool(command.get('capture')),'selected_memory_lines':[line for line in text.splitlines() if any(t in line for t in ['CUDA0 model buffer','CUDA0 KV buffer','n_ctx =','n_ubatch =','JSA_DVR shared'])][:12]})
first_commit='5b3121bab39a92ba5e4a52e4b30d1211fd78c2e4';bridge_source={}
for name in ['common.py','bridge.py','verify_bridge.py']:
    b=subprocess.check_output(['git','show',first_commit+':scripts/platform/jsa_rtx_validation_v1/'+name],cwd=REPO);bridge_source[name]={'committed_blob_sha256':hashlib.sha256(b).hexdigest(),'local_sha256':sha(Path(__file__).parent/name),'byte_equal':hashlib.sha256(b).hexdigest()==sha(Path(__file__).parent/name)}
postload=read(PUB/'POST_LOAD_OFFLOAD.json')
result={'status':'PASS_WITH_LOG_LIMITATION' if all(checks.values()) and all((r['execution_evidence_present'] or r['diagnostic_capture_callback']) and r['requested_GPU_all'] for r in offload) and postload['status']=='PASS' else 'FAILED','asset_checks':checks,'offload':offload,'post_load_offload':postload,'offload_log_limitation':'Ordinary server verbosity suppresses per-model layer-count/memory lines. Capture-off original logs retain CUDA graph execution; diagnostic capture callbacks do not provide that graph-reuse log evidence and are labeled separately. Full layer counts were checked in post-run zero-forward loads with the same binary/assets/load arguments plus verbose logging. E original logs directly show full layer counts. Post-load evidence is not retrospectively attributed to individual formal invocations.','original_S_bridge_provenance':'Initial engineering bridge launched on design HEAD with uncommitted runner code after an initial sparse-add/identity error. The bytes match first commit5b3121b; it was engineering only. All formal S forwards used independently verified freeze b454b72.','bridge_first_commit_byte_proof':bridge_source,'S_CPU_background':'Exposure audit and native CPU builds overlapped part of S; GPU inference was exclusive and all host admission gates passed. No same-day point estimate is promoted to cross-date robustness.','new_family_and_external_repaired_studies':'No confirmation implementation repair or formal retry','utc':now()}
save(PUB/'POSTCHECKS.json',result);assert result['status']=='PASS_WITH_LOG_LIMITATION';print('POST-RUN ASSETS/GPU EXECUTION PASS WITH LOG LIMITATION',len(offload),flush=True)
