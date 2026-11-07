"""Source-bound, append-only native execution on the authorized B570 host."""
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, sys, time
HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('HS_PREFIX_ROOT','I:/HeteroSpec/b570-prefix-reuse-20261104'))
OLD=Path('I:/HeteroSpec/b570-parallel-20261103')
ORACLE=Path('C:/hs/b570-native-reproduction-20261026')
LOCK=Path('C:/hs/b570-llama-exclusive.lock')
MODEL=Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-8B-Q8_0.gguf')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def command(argv,log):
 with Path(log).open('x',encoding='utf-8') as f:subprocess.run(list(map(str,argv)),stdout=f,stderr=subprocess.STDOUT,check=True)
def setup():
 ROOT.mkdir(exist_ok=True)
 binding=read(OLD/'SOURCE_BINDING-candidate-D.json')
 for rel,h in binding['compiled_source'].items():assert sha(OLD/'source-00'/rel)==h,rel
 for group in ('runtime_files','reference_runtime_files'):
  for f in binding[group]['files']:assert sha(f['path'])==f['sha256'],f['path']
 assert sha(MODEL)=='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
 write(ROOT/'INHERITED_AUTHENTICATION.json',dict(utc=utc(),design_head='bba256cf04bbd2038029fd59447df9722b24c197',scientific_ancestor='8ca17478c292275b3515a91b51d0e791a8fae256',binding=binding,model=dict(path=str(MODEL),bytes=MODEL.stat().st_size,sha256=sha(MODEL)),old_R_hashes={p.name:sha(p) for p in OLD.glob('R-*.json')},old_k1_sha256=sha(OLD/'K1_REGRESSION.json')))
 shutil.copytree(OLD/'source-00',ROOT/'source-00')
 kit=Path('C:/hs/b570-llama-results/scripts/experiments/b570_llama_companion_v1')
 for name in ('companion_scope.cpp','companion_scope.hpp'):shutil.copyfile(kit/name,HERE/name)
 write(ROOT/'RESOURCE_RESERVATION.json',dict(utc=utc(),initial_request_tranche=2048,planned=1936,development=192,calibration=240,main_qualification=320,main_timed_and_warm=1024,aligned_control=160,engineering_reserve=112,zero_forward_max=6,standalone_graph_max=64,worker_timeout_seconds=7200,disk_reserve_bytes=20*1024**3,ram_reserve_bytes=2*1024**3,device_reserve_bytes=128*1024**2,free_disk_bytes=shutil.disk_usage(ROOT).free,lifecycle='model resident per session; immutable host sequence snapshots; fresh context per service; context creation/import/destruction included',cleanup='Windows Job kill-on-close, assigned suspended, process limit1; native exclusive lock',common_test_gate='Both genuine platform source/policy freezes required. No independent fork authorized by this runner.'))
def build(role):
 dest=ROOT/role;dest.mkdir()
 cand=role.startswith('candidate');src=ROOT/'source-00' if cand else ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2';libs=OLD/'build-00' if cand else ORACLE/'build'
 command(['cmake','-S',HERE,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+src.as_posix(),'-DHISTORICAL_LIBS='+libs.as_posix(),'-DCANDIDATE='+('ON' if cand else 'OFF')],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 bind(role)
def bind(role):
 dest=ROOT/role;cand=role.startswith('candidate');libs=OLD/'build-00' if cand else ORACLE/'build';out=dest/'build/Release'
 for dll in (libs/'bin/Release').glob('*.dll'):
  if cand and dll.name=='llama.dll':continue
  shutil.copyfile(dll,out/dll.name)
 if cand:shutil.copyfile(dest/'build/runtime/src/Release/llama.dll',out/'llama.dll')
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in [out/'frontier.exe',*sorted(out.glob('*.dll'))]]))
 write(dest/'SOURCE.json',dict(files={p.name:sha(p) for p in HERE.iterdir() if p.suffix in ('.py','.cpp','.hpp','.txt')},arithmetic=read(ROOT/'INHERITED_AUTHENTICATION.json')['binding']['compiled_source'],epoch=role))
def reworker(role):
 dest=ROOT/role;dest.mkdir();cand=role.startswith('candidate');src=ROOT/'source-00' if cand else ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2';libs=OLD/'build-00' if cand else ORACLE/'build'
 llama_lib=(ROOT/'candidate-00/build/runtime/src/Release/llama.lib') if cand else libs/'runtime/src/Release/llama.lib'
 cm='cmake_minimum_required(VERSION 3.20)\nproject(prefix_worker LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\n'
 cm+=f'add_executable(frontier "{(HERE/"worker.cpp").as_posix()}")\n'
 cm+=f'target_include_directories(frontier PRIVATE "{src.as_posix()}/include" "{src.as_posix()}/ggml/include" "{src.as_posix()}/vendor")\n'
 cm+='target_compile_definitions(frontier PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED'+(' CAND' if cand else '')+')\n'
 cm+='target_compile_options(frontier PRIVATE /fp:precise /O2 /W4 /utf-8)\n'
 cm+=f'target_link_libraries(frontier PRIVATE "{llama_lib.as_posix()}" "{libs.as_posix()}/runtime/ggml/src/Release/ggml.lib" "{libs.as_posix()}/runtime/ggml/src/Release/ggml-base.lib" bcrypt)\n'
 (dest/'CMakeLists.txt').write_text(cm,encoding='utf-8');shutil.copyfile(HERE/'worker.cpp',dest/'worker.cpp')
 command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 out=dest/'build/Release';baseline=ROOT/('candidate-00' if cand else 'reference-00')/'build/Release'
 for dll in baseline.glob('*.dll'):shutil.copyfile(dll,out/dll.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in [out/'frontier.exe',*sorted(out.glob('*.dll'))]]))
 write(dest/'SOURCE.json',dict(worker_sha256=sha(dest/'worker.cpp'),candidate_library_source=sha(ROOT/'candidate-00/SOURCE.json') if cand else None,epoch=role))
def run(name,role,slots,stage,cache=None,**extra):
 unit=ROOT/'units'/name
 task=dict(target=str(MODEL),target_only=True,context=4096,cas=str(ROOT/'vectors'),slots=slots,**extra)
 if cache is not None:task['cache']=cache
 if unit.exists():
  assert read(unit/'JOB.json')==task,'Resume source/job drift'
  return read(unit/'native/result.json') if (unit/'native/result.json').exists() else read(unit/'RECEIPT.json')
 used=sum(read(p)['requests'] for p in (ROOT/'units').glob('*/BUDGET.json')) if (ROOT/'units').exists() else 0
 count=sum(s['kind'] not in ('admit',) for s in slots)
 assert used+count<=2048
 caps=dict(development=192,calibration=240,engineering_reserve=112,main_qualification=320,main_cost_and_warmup=1024,aligned_control=160)
 if stage in caps:assert sum(read(p)['requests'] for p in (ROOT/'units').glob('*/BUDGET.json') if read(p)['stage']==stage)+count<=caps[stage],stage+' reservation exceeded'
 if (ROOT/'MODEL_STAT_BINDING.json').exists():
  pin=read(ROOT/'MODEL_STAT_BINDING.json');st=MODEL.stat();assert st.st_size==pin['bytes'] and st.st_mtime_ns==pin['mtime_ns'],'Pinned model changed after byte authentication'
 if any(s['kind']=='admit' for s in slots):
  assert sum(read(p).get('admissions',0) for p in (ROOT/'units').glob('*/BUDGET.json'))+len(slots)<=6
 assert shutil.disk_usage(ROOT).free>20*1024**3
 unit.mkdir(parents=True);write(unit/'JOB.json',task)
 write(unit/'BUDGET.json',dict(stage=stage,requests=count,admissions=sum(s['kind']=='admit' for s in slots),utc=utc()))
 manifest=ROOT/role/'FILES.json';files=read(manifest)['files'];cmd=[sys.executable,'-B',str(HERE/'supervisor.py'),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit','7200','--minimum-free-bytes',str(20*1024**3),files[0]['path'],str(unit/'JOB.json'),str(unit/'native')]
 write(unit/'COMMAND.json',cmd);write(LOCK,dict(pid=os.getpid(),unit=str(unit),utc=utc()))
 start=time.monotonic()
 try:
  with (unit/'host.log').open('x') as f:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=7380).returncode
  sup=read(unit/'SUPERVISOR.json');native=read(unit/'native/result.json') if (unit/'native/result.json').exists() else {'status':'NO_NATIVE_FOOTER'}
  loaded={Path(x['path']).name.lower():x['sha256'] for x in sup.get('loaded_module_hashes',[])}
  cleanup=sup.get('job_accounting',{}).get('active_processes')==0
  ok=code==0 and sup['status']=='complete' and cleanup and all(loaded.get(Path(f['path']).name.lower())==f['sha256'] for f in files if f['path'].endswith('.dll'))
  write(unit/'RECEIPT.json',dict(success=ok,status=native['status'],owned_seconds=time.monotonic()-start,process_seconds=sup['charged_seconds'],cleanup=cleanup,manifest_sha256=sha(manifest)))
  print(name,native['status'],native.get('error',''),flush=True);return native
 finally:
  if (unit/'SUPERVISOR.json').exists() and read(unit/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0:LOCK.unlink(missing_ok=True)
if __name__=='__main__':
 if sys.argv[1]=='setup':setup()
 elif sys.argv[1]=='build':build(sys.argv[2])
 elif sys.argv[1]=='reworker':reworker(sys.argv[2])
 elif sys.argv[1]=='admit':
  role=sys.argv[2];print(run('admit-'+role,role,[dict(kind='admit',ub=32 if role.startswith('candidate') else 1,draft_context=False,allocator_census=role.startswith('candidate'))],'zero-forward',capacity_trace=True))
