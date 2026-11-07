"""Separate Smol deployment: authenticate and exercise original host references."""
from host import *
from pathlib import PureWindowsPath
if sys.flags.optimize:
 raise RuntimeError('Native recovery and its read-only audit require Python assertions enabled')
SMOL=Path('C:/hs/jsa-b570-run-v1')
SROOT=ROOT/'secondary-smol'
def native_path(value):
 parts=PureWindowsPath(str(value)).parts
 assert 'secondary-smol' in parts,'Unexpected native payload root'
 p=SROOT.joinpath(*parts[parts.index('secondary-smol')+1:])
 assert SROOT.resolve() in p.resolve().parents,'Native payload path escape'
 return p
def setup():
 SROOT.mkdir()
 model=read(SMOL/'MODEL_CHOICE.json')['models'];pins=[]
 for role in ('target','draft'):
  f=model[role];p=Path(f['path']);assert sha(p)==f['sha256'];pins.append(dict(role=role,path=str(p),sha256=f['sha256'],bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns))
 bindings=read(SMOL/'BINARY_BINDINGS.json')
 for f,x in bindings.items():
  if f.startswith('bin/original/'):assert sha(SMOL/f)==x['sha256']
 write(SROOT/'AUTHENTICATION.json',dict(models=pins,original_binary_bindings=bindings,old_driver=read(SMOL/'code/runner.py') if False else '32.0.101.9034',current_driver='32.0.101.9150',reference_bridge_required=True,not_a_Qwen_rescue=True))
 front=SROOT/'original-runtime';front.mkdir()
 for p in (SMOL/'bin/original').iterdir():
  if p.suffix.lower() in ('.exe','.dll'):shutil.copyfile(p,front/p.name)
 write(SROOT/'original-FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(front.iterdir())]))
 admission=SROOT/'admission';admission.mkdir()
 for n in ('smol_admission.cpp','resource_budget.hpp'):shutil.copyfile(HERE/n,admission/n)
 cm='cmake_minimum_required(VERSION 3.20)\nproject(smol_admission LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\nfind_package(Vulkan REQUIRED)\nadd_executable(admission smol_admission.cpp)\ntarget_compile_definitions(admission PRIVATE LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED NOMINMAX)\ntarget_include_directories(admission PRIVATE "C:/hs/b570-direct-id-v1-src/include" "C:/hs/b570-direct-id-v1-src/ggml/include")\ntarget_link_libraries(admission PRIVATE "C:/hs/b570-direct-id-v1-build/src/Release/llama.lib" "C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml-base.lib" Vulkan::Vulkan)\n'
 (admission/'CMakeLists.txt').write_text(cm)
 command(['cmake','-S',admission,'-B',admission/'build','-G','Visual Studio 17 2022','-A','x64'],admission/'configure.log')
 command(['cmake','--build',admission/'build','--config','Release','--parallel','4'],admission/'compile.log')
 for p in front.glob('*.dll'):shutil.copyfile(p,admission/'build/Release'/p.name)
 write(admission/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((admission/'build/Release').iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
def supervised(name,manifest,argv,cost,stream_folder=None,**options):
 assert not LOCK.exists();unit=SROOT/'units'/name;unit.mkdir(parents=True)
 for model in read(SROOT/'AUTHENTICATION.json')['models']:
  st=Path(model['path']).stat();assert st.st_size==model['bytes'] and st.st_mtime_ns==model['mtime_ns'],'Authenticated model input changed'
 ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve('smol-'+name,cost);ledger.close()
 write(unit/'RESERVATION.json',dict(**cost,utc=utc()));write(LOCK,dict(pid=os.getpid(),unit=str(unit)))
 args=[sys.executable,'-B',str(HERE/'supervisor.py'),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit','900','--minimum-free-bytes',str(20*1024**3)]
 for key,value in options.items():args += ['--'+key.replace('_','-'),str(value)]
 args+=list(map(str,argv));write(unit/'COMMAND.json',args);start=time.monotonic();code=None;status='FAILED'
 stream=None
 if stream_folder is not None:
  from smol_stream import StateStream
  from smol_state import pack
  stream=StateStream(stream_folder,pack)
 try:
  with (unit/'host.log').open('x') as f:code=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=950).returncode
  r=read(unit/'SUPERVISOR.json');assert r['cleanup_verified'] and r['job_accounting']['active_processes']==0
  status='COMPLETE' if code==0 else 'FAILED';write(unit/'RECEIPT.json',dict(success=code==0,owned_seconds=time.monotonic()-start,cleanup=True))
  return unit,code
 finally:
  ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.finish('smol-'+name,status,code);ledger.close()
  if (unit/'SUPERVISOR.json').exists() and read(unit/'SUPERVISOR.json').get('cleanup_verified'):LOCK.unlink(missing_ok=True)
  if stream is not None:stream.finish()
def admit():
 a=SROOT/'admission';models=read(SROOT/'AUTHENTICATION.json')['models']
 unit,rc=supervised('admission',a/'FILES.json',[a/'build/Release/admission.exe',*[f['path'] for f in models]],dict(requests=0,token_rows=0,operators=0));assert rc==0
 text=(unit/'SUPERVISOR.stdout.log').read_text();assert text.count('SMOL_ZERO_FORWARD_ADMITTED')==3
 write(SROOT/'ADMISSION.json',dict(status='SMOL_UB1_2_4_ZERO_FORWARD_ADMITTED',scope='Original Smol numerical DLLs, dual models, C1024 F16, prefill plus continuation contexts',forwards=0,supervisor_sha256=sha(unit/'SUPERVISOR.json')))
def finish_setup():
 a=SROOT/'admission';cm=a/'CMakeLists.txt'
 cm.write_text(cm.read_text()+'\ntarget_link_libraries(admission PRIVATE "C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml.lib")\ntarget_compile_options(admission PRIVATE /utf-8)\n')
 command(['cmake','-S',a,'-B',a/'build','-G','Visual Studio 17 2022','-A','x64'],a/'configure-02.log')
 command(['cmake','--build',a/'build','--config','Release','--parallel','4'],a/'compile-02.log')
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,a/'build/Release'/p.name)
 write(a/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((a/'build/Release').iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
def reference(index):
 assert read(SROOT/'ADMISSION.json')['forwards']==0
 inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index];n=len(inp['prompt_ids']);name='old-R-'+str(index)
 desc=SROOT/(name+'-request.json');out=SROOT/(name+'-capture.json')
 desc.write_text(json.dumps(dict(request_id=name,prompt_ids=inp['prompt_ids'],output=str(out)))+'\n')
 env=SROOT/(name+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=str(out),HS_PREFILL_UB='128',HS_NO_TRANSFER='1'))
 model=read(SROOT/'AUTHENTICATION.json')['models'][0]['path'];exe=SROOT/'original-runtime/b570-closeout-target.exe'
 argv=[exe,'--model',model,'--device','Vulkan0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size','128','--flash-attn','off','--n-predict','128','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--threads','10','--threads-batch','10','--log-verbosity','3','--no-warmup','--reasoning','off','--simple-io','--no-conversation']
 unit,rc=supervised(name,SROOT/'original-FILES.json',argv,dict(requests=1,token_rows=n+128,operators=0),stdin_file=desc,environment_file=env);assert rc==0
 compare_reference(index)
def compare_reference(index):
 name='old-R-'+str(index);out=SROOT/(name+'-capture.json');inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index]
 schedule=read(SMOL/'REQUEST_SCHEDULE.json')['B'];spec=next(x for x in schedule if x['arm']=='R' and x['capture'])
 oldunit=spec['requests'][index]['unit']
 actual=read(out);oldpath=SMOL/'raw'/hashlib.sha256(oldunit.encode()).hexdigest()[:24]/'capture.json';old=read(oldpath)
 comparisons=dict(prompt=actual['prompt_ids']==old['prompt_ids'],endpoint=actual['ids']==old['ids'] and actual['eog']==old['eog'],all_available_scores=actual['commits']==old['commits'])
 write(SROOT/(name+'-COMPARISON.json'),dict(input_id=inp['id'],historical_capture_sha256=sha(oldpath),current_capture_sha256=sha(out),comparisons=comparisons,old_full_vectors_available=False,new_run_not_a_historical_backfill=True));print(comparisons)
def legacy(index):
 inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index];name='old-N-k1-'+str(index);out=SROOT/(name+'-capture.json');request=SROOT/(name+'-request.json')
 request.write_text(json.dumps(dict(request_id=name,prompt_ids=inp['prompt_ids'],output=str(out)))+'\n')
 env=SROOT/(name+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=str(out),HS_PREFILL_UB='128'))
 models=read(SROOT/'AUTHENTICATION.json')['models'];exe=SROOT/'original-runtime/b570-closeout-native.exe'
 argv=[exe,'--model',models[0]['path'],'--device','Vulkan0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size','1','--flash-attn','off','--n-predict','127','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--threads','10','--threads-batch','10','--log-verbosity','3','--spec-type','draft-simple','--spec-draft-model',models[1]['path'],'--spec-draft-device','Vulkan0','--spec-draft-ngl','all','--spec-draft-n-max','1','--spec-draft-n-min','0','--spec-draft-threads','10','--spec-draft-threads-batch','10']
 unit,rc=supervised(name,SROOT/'original-FILES.json',argv,dict(requests=1,token_rows=2*len(inp['prompt_ids'])+512,operators=0),stdin_file=request,environment_file=env);assert rc==0
 a=read(out);b=read(SROOT/('old-R-'+str(index)+'-capture.json'));n=len(b['ids'])
 write(SROOT/(name+'-COMPARISON.json'),dict(input_id=inp['id'],canonical_endpoint_equal=a['ids'][:n]==b['ids'] and a['eog'][:n]==b['eog'],raw_output_count=len(a['ids']),reference_output_count=n,raw_suffix=len(a['ids'])-n,sampled_target_scores_equal=[x['scores'] for x in a['commits'][:n]]==[x['scores'] for x in b['commits']],full_vector_and_state_qualification=False))
if __name__=='__main__':
 if sys.argv[1]=='setup':setup()
 elif sys.argv[1]=='finish':finish_setup()
 elif sys.argv[1]=='admit':admit()
 elif sys.argv[1]=='compare':compare_reference(int(sys.argv[2]))
 elif sys.argv[1]=='legacy':legacy(int(sys.argv[2]))
 else:reference(int(sys.argv[2]))
