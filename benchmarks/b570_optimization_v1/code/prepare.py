"""Hash-bound recovery/inventory and vocabulary-only runtime evidence. No forwards."""
import hashlib,json,subprocess,shutil,time
from pathlib import Path
R=Path('C:/hs/b570-opt-run-v1');REPO=Path('C:/hs/b570-opt-v1');DOC=REPO/'docs/experiments/b570_optimization_20261011';OLD=Path('C:/hs/b570-opt-pr82-restored-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
sources=[];(R/'source-blobs').mkdir(exist_ok=True)
for x in load(DOC/'SOURCE_BINDINGS.json')['sources']:
 b=subprocess.check_output(['git','cat-file','blob',x['commit']+':'+x['path']],cwd=REPO);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 p=R/'source-blobs'/(x['sha256']+'.blob');p.write_bytes(b);sources.append(dict(**x,local_path=str(p)))
save('PLAN_SOURCE_VERIFICATION.json',dict(status='PASS',plan_head='840ef5fef96068e0e40eee434d89d07bbad6a592',source_blobs=sources,forward_calls=0))
bound=load(OLD/'SOURCE_BINDINGS.json');checked=[]
for name,m in bound.items():
 p=OLD/name;assert p.stat().st_size==m['bytes'] and sha(p)==m['sha256'];checked.append(name)
for p in (R/'build/Release').glob('*.dll'):
 original=OLD/'bin/original'/p.name;assert sha(p)==sha(original)
save('INHERITED_SOURCE_MODULE_RECHECK.json',dict(status='PASS',restored_source_files=len(checked),original_numerical_Dlls={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (R/'build/Release').glob('*.dll')},new_numerical_backend=False,upstream_commit='NOT_CERTIFIED_DISTRIBUTION_SOURCE',PR82_restore=load(R/'PR82_RESTORE.json')))
inventory_cmd="[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); @{utc=(Get-Date).ToUniversalTime().ToString('o');os=(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,LastBootUpTime,TotalVisibleMemorySize);cpu=(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors);video=(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,PNPDeviceID,CurrentHorizontalResolution,CurrentVerticalResolution);power=(powercfg /getactivescheme);temperature='UNAVAILABLE';frequency='UNAVAILABLE'} | ConvertTo-Json -Depth 5"
raw=subprocess.check_output(['powershell','-NoProfile','-Command',inventory_cmd]);(R/'HOST_INVENTORY.raw.json').write_bytes(raw);save('HOST_INVENTORY.json',json.loads(raw.decode('utf-8-sig')))
pins=load(DOC/'ASSETS.json')['models'];assets={}
for key,pin in pins.items():
 p=(Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf') if key in ['Qwen_target_Q8_0','Qwen_draft_Q8_0'] else R/'models')/pin['filename']
 if not p.exists():continue
 h=sha(p);assert p.stat().st_size==pin['bytes'] and h==pin['sha256'];assets[key]=dict(**pin,path=str(p),full_file_verified=True)
save('AVAILABLE_ASSET_CHECKS.json',dict(status='ASSET_BYTES_PASS',models=assets,forward_calls=0))
lineage={}
for p in [R/'native/memory_load.cpp',R/'native/CMakeLists.txt',DOC/'PROTOCOL.md',DOC/'POLICY.json',REPO/'scripts/platform/b570_optimization_v1/native_memory_budget.h',Path('C:/hs/b570-direct-id-v1-src/include/llama.h'),Path('C:/hs/b570-direct-id-v1-src/src/llama-context.cpp'),Path('C:/hs/b570-direct-id-v1-src/src/llama.cpp'),Path('C:/hs/b570-direct-id-v1-src/ggml/src/ggml-vulkan/ggml-vulkan.cpp')]:
 lineage[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size)
save('ZERO_FORWARD_SOURCE_REVIEW.json',dict(status='PASS_ZERO_FORWARD_ENTRY_POINTS_ONLY',sources=lineage,review=['Probe uses direct model_load/context-init; no common_init_from_params warmup or llama_decode/encode calls.', 'llama_context constructor reserves graphs; it does not execute token forward. Numerical DLLs are exact restored PR82 originals.', 'Memory query executes in model-owning PID on actual PCI Intel B570 physical device, not an external probe PID.', 'The device-local heap is separate from the non-device-local system heap; both heaps are retained without claiming all shared allocations are spill.', 'Full offload and KV placement must also be parsed from actual load stderr; requested n_gpu_layers alone is not proof.'],numerical_backend_changed=False,model_forward_calls=0))
tokenizer=Path('C:/hs/jsa-b570-run-v1/tokenizer-build/Release/b570-tokenizer.exe');vocabs={};(R/'vocab').mkdir(exist_ok=True)
for key,a in assets.items():
 out=R/'vocab'/(key+'.jsonl');err=out.with_suffix('.stderr.log')
 if not out.exists():
  with out.open('wb') as f,err.open('wb') as e:subprocess.run([str(tokenizer),a['path']],input=b'',stdout=f,stderr=e,check=True)
 v=json.loads(out.read_text(encoding='utf8').splitlines()[0]);assert v['vocab_only'] and v['forward_calls']==0;vocabs[key]=v
 print('Actual vocab-only read',key,v['vocab_tokens'],flush=True)
equal=[]
for family in ['Qwen','Llama']:
 target=vocabs.get(family+'_target_Q8_0')
 for q in ['Q8_0','Q4_K_M']:
  draft=vocabs.get(family+'_draft_'+q)
  if not target or not draft:continue
  fields=['vocab_tokens','vocab_type','table','bos','eos','add_bos','add_eos','runtime_eog_ids'];diff=[k for k in fields if target[k]!=draft[k]]
  equal.append(dict(family=family,draft=q,status='PASS' if not diff else 'BLOCKED_VOCAB',different_fields=diff,full_vocab_tokens=target['vocab_tokens'],actual_eog_ids=target['runtime_eog_ids'],target_template_only=True))
save('ACTUAL_VOCAB_VERIFICATION.json',dict(status='PASS' if all(x['status']=='PASS' for x in equal) else 'BLOCKED',pairs=equal,tokenizer_sha256=sha(tokenizer),forward_calls=0))
save('PREPARATION_DEVIATIONS.json',[dict(kind='CPU_COMPILE_REJECTED',reason='Inherited llama_model_params uses load_mode and has no use_mmap member; removed nonexistent override and kept native default load mode.',preserved_source='versions/memory_load.pre-field-fix.cpp',model_forward_calls=0),dict(kind='BOUNDED_ZERO_FORWARD_PROBE_REVISION',reason='Explicit n_outputs_max=1 models sequential/native target path instead of conservative4-output batched reservation. All prior loads/results retained; load budget never reset.',preserved_source='versions/memory_load.v1-outputs4.cpp',model_forward_calls=0)])
print('PREPARATION PASS',len(sources),'source blobs;',len(checked),'restored source files;',len(assets),'verified assets',flush=True)
