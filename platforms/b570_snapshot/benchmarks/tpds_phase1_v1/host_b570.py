"""B570 review-v2 execution adapter; reuses the admitted supervisor and ledger."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent
ROOT=Path(os.environ.get('HS_PHASE1_ROOT','I:/HeteroSpec/b570-phase1-20261107-v2'))
ECO=Path('I:/HeteroSpec/b570-economics-20261106')
OLD=Path('E:/HeteroSpec/b570-decisive-recovery-restored-20261105/secondary-smol')
os.environ['HS_ECON_ROOT']=str(ROOT)
sys.path.insert(0,str(HERE.parent/'b570_economics_v1'))
import native_host as nh
nh.LIMITS={'requests':1024,'token_rows':2500000,'operators':0}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,j):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2);f.write('\n')
def command(args,log,env=None):
 t=time.monotonic();ok=False
 try:
  with Path(log).open('x',encoding='utf-8') as f:subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,check=True,env=env)
  ok=True
 finally:write(str(log)+'.cost.json',dict(wall_seconds=time.monotonic()-t,success=ok,model_requests=0))
def init():
 ROOT.mkdir(exist_ok=False)
 models=read(ECO/'HOST_BINDINGS.json')['models']
 for m in models:
  p=Path(m['path']);assert p.stat().st_size==m['bytes'] and sha(p)==m['sha256']
 inventory=Path('E:/HeteroSpec/phase1-host-inventory-20261107.txt')
 write(ROOT/'ADOPTION.json',dict(design_head='eed20261b5820ea4f778fb5a1012cb07e98dfea4',branch='codex/b570-phase1-results-20261107-v2',protocol='review-v2',prior_phase1_freezes_found=[],prior_phase1_ledger_units_found=[],audit_inventory=dict(path=str(inventory),sha256=sha(inventory)),old_studies_untouched=True,active_native_workers=0,exclusive_lock_absent=not nh.LOCK.exists(),date='2026-11-07',scientific_base='acc86d9cb07c2afa983f73e28a1048fb99c63e3a'))
 write(ROOT/'HOST_BINDINGS.json',dict(models=models,new_study_limits=nh.LIMITS,supervisor_sha256=sha(nh.PREVIOUS/'supervisor.py'),reference_C1024='unchanged canonical forced-reference02',reference_C4096='independent deployment reference defined before candidate output',matched_idle_draft=True))
 nh.Ledger(ROOT/'ledger.sqlite',nh.LIMITS).close()
 for name in ('supervisor02.py','SUPERVISOR_ADAPTER.json','SUPERVISOR02_VALIDATION.json'):shutil.copyfile(ECO/name,ROOT/name)
 rows=[json.loads(x) for x in (OLD/'cohort/tokenized.jsonl').read_text().splitlines()[1:]]
 selected=next(r for r in sorted(rows,key=lambda x:x['id']) if len(r['prompt_ids'])>=3104)
 write(ROOT/'TOKEN_TAPE.json',dict(source_id=selected['id'],source_prompt_tokens=len(selected['prompt_ids']),source_sha256=sha(OLD/'cohort/tokenized.jsonl'),selection='first lexicographic existing licensed path with >=3104 tokens; fixed before candidate values; structural only',tokens=selected['prompt_ids'][:3104],padding=False))
 sys.path.insert(0,str(HERE));from design import structural
 write(ROOT/'SCHEDULE.json',structural('b570'))
 write(ROOT/'REFERENCE_DEFINITION.json',dict(C1024=dict(canonical_executable=str(OLD/'forced-reference02/build/Release/b570-closeout-target.exe'),sha256=sha(OLD/'forced-reference02/build/Release/b570-closeout-target.exe'),unchanged=True),C4096=dict(independent=True,capacity=4096,producer_outer=512,producer_ub=128,output_reserve=0,per_sequence=1,residency='matched idle Smol135M',arithmetic_dll_sha256=sha(OLD/'forced-reference02/build/Release/llama.dll')),candidate_outputs_seen=False,token_tape_sha256=sha(ROOT/'TOKEN_TAPE.json'),mask={'q2':'all','q4':'all','q32':'last'},reference_scalar_outputs='independent per-row original reserve, only required candidate outputs compared'))
 print('PHASE1_HOST_BOUND',flush=True)
def stage():
 dest=ROOT/'native01';dest.mkdir();inputs=dest/'inputs';shutil.copytree(ECO/'repro/native-inputs/source',inputs/'source');shutil.copytree(ECO/'repro/native-inputs/libs',inputs/'libs');shutil.copytree(ECO/'repro/native-inputs/generated',inputs/'generated')
 for core,base in [('R','core01'),('LS','parallel-core02')]:
  src=dest/core/'src';shutil.copytree(ECO/base/'source/src',src)
  p=src/'llama-context.cpp';s=p.read_text();assert 'cparams.n_ctx != 1024' in s;s=s.replace('cparams.n_ctx != 1024','(cparams.n_ctx != 1024 && cparams.n_ctx != 4096)')
  if core=='R':s=s.replace('(ub != 1 && ub != 2 && ub != 128)','(ub != 1 && ub != 2 && ub != 4 && ub != 32 && ub != 128)')
  s+='''\nvoid llama_context::b570_phase1_allocation(uint64_t *v) const {
 v[0]=cparams.n_ctx;v[1]=cparams.n_ubatch;v[2]=cparams.n_batch;
 v[3]=cparams.n_outputs_max;v[4]=cparams.n_outputs_max_per_seq;v[5]=n_outputs;
 v[6]=logits.size;v[7]=buf_output?ggml_backend_buffer_get_size(buf_output.get()):0;
 v[8]=0;for(auto &b:backends)v[8]+=ggml_backend_sched_get_buffer_size(sched.get(),b.get());
}
extern "C" __declspec(dllexport) int b570_phase1_allocation(llama_context*c,uint64_t*v) noexcept {
 if(!c||!v)return 1;try{c->b570_phase1_allocation(v);return 0;}catch(...){return 2;}
}
''';p.write_text(s)
  p=src/'llama-context.h';s=p.read_text();anchor='    void b570_economics_bind_phase(uint32_t ub);';assert s.count(anchor)==1;p.write_text(s.replace(anchor,anchor+'\n    void b570_phase1_allocation(uint64_t *v) const;'))
 shutil.copyfile(HERE/'native_b570.cpp',dest/'native_b570.cpp');shutil.copyfile(HERE/'compile_trace.py',dest/'compile_trace.py')
 for name in ('resource_budget.hpp','smol_bulk.hpp'):
  s=(ECO/'parallel04/M-mode0'/name).read_text()
  if name=='smol_bulk.hpp':s=s.replace('256ULL*1024*1024','1024ULL*1024*1024').replace('16ULL*1024*1024','32ULL*1024*1024')
  (dest/name).write_text(s)
 cmake='''cmake_minimum_required(VERSION 3.24)
project(phase1_b570 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_COMPILER_LAUNCHER "${PYTHON};${CMAKE_SOURCE_DIR}/compile_trace.py")
add_compile_options(/utf-8 /bigobj)
add_compile_definitions(NOMINMAX _CRT_SECURE_NO_WARNINGS LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN)
include_directories(inputs/source/include inputs/source/common inputs/source/ggml/include inputs/source/vendor inputs/source/ggml/src inputs/generated)
find_package(Vulkan REQUIRED)
foreach(core R LS)
 file(GLOB units "${core}/src/*.cpp" "${core}/src/models/*.cpp")
 add_library(core_${core} SHARED ${units})
 target_compile_definitions(core_${core} PRIVATE LLAMA_BUILD)
 target_include_directories(core_${core} PRIVATE "${core}/src")
 target_link_libraries(core_${core} PRIVATE "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/Release/ggml.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/Release/ggml-base.lib")
 set_target_properties(core_${core} PROPERTIES OUTPUT_NAME llama RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/${core}" ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib/${core}")
endforeach()
foreach(arm ORIGINAL R LS)
 add_executable(worker_${arm} native_b570.cpp)
 target_include_directories(worker_${arm} PRIVATE inputs/source/src)
 target_link_libraries(worker_${arm} PRIVATE "${CMAKE_SOURCE_DIR}/inputs/libs/common/Release/llama-common.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/common/Release/llama-common-base.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/Release/ggml.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/Release/ggml-base.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/Release/ggml-cpu.lib" "${CMAKE_SOURCE_DIR}/inputs/libs/ggml/src/ggml-vulkan/Release/ggml-vulkan.lib" Vulkan::Vulkan)
 if(arm STREQUAL ORIGINAL)
  target_compile_definitions(worker_${arm} PRIVATE PHASE1_CORE=0)
  target_link_libraries(worker_${arm} PRIVATE "${CMAKE_SOURCE_DIR}/inputs/libs/src/Release/llama.lib")
 elseif(arm STREQUAL R)
  target_compile_definitions(worker_${arm} PRIVATE PHASE1_CORE=1)
  target_link_libraries(worker_${arm} PRIVATE core_R)
 else()
  target_compile_definitions(worker_${arm} PRIVATE PHASE1_CORE=2)
  target_link_libraries(worker_${arm} PRIVATE core_LS)
 endif()
 set_target_properties(worker_${arm} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/${arm}")
endforeach()
''';(dest/'CMakeLists.txt').write_text(cmake)
 write(dest/'SOURCE_BINDING.json',dict(base_source_roots={k:str(ECO/v/'source/src') for k,v in [('R','core01'),('LS','parallel-core02')]},changes=['capacity guard 1024/4096','allocation observation, no data fields or arithmetic changes','new clean append frontend, original producer, q32 last mask','bulk observer bound only; canonical R unchanged'],all_files={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()}))
 print('PHASE1_SOURCE_STAGED',flush=True)
def build(attempt='01',native='native01'):
 d=ROOT/native;b=d/('build'+attempt);deps=d/('deps'+attempt);deps.mkdir()
 vs=Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat')
 script=d/('build'+attempt+'.cmd')
 script.write_text('@echo off\ncall "'+str(vs)+'" -arch=x64 -host_arch=x64\nif errorlevel 1 exit /b 1\nset VSLANG=1033\nset PHASE1_DEPS='+str(deps)+'\nset VULKAN_SDK=C:\\VulkanSDK\\1.4.357.0\ncmake -S "'+str(d)+'" -B "'+str(b)+'" -G Ninja -DCMAKE_BUILD_TYPE=Release -DPYTHON="'+sys.executable+'"\nif errorlevel 1 exit /b 1\ncmake --build "'+str(b)+'" -- -j 4 -d keeprsp\n')
 command(['cmd','/d','/c',script],d/('build'+attempt+'.log'))
 for arm in ('ORIGINAL','R','LS'):
  bin=b/'bin'/arm
  for p in (OLD/'forced-reference02/build/Release').glob('*.dll'):
   if p.name.lower()!='llama.dll' or arm=='ORIGINAL':shutil.copyfile(p,bin/p.name)
  if native=='native02' and arm=='LS':
   backend=ECO/'parallel04/M-mode0/build/Release/ggml-vulkan.dll';assert sha(backend)=='059163952ce66e26722dde75eb9dba30b4dfba59a428b3d9577b9b0d637c186e';shutil.copyfile(backend,bin/backend.name)
  write(bin/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bin.iterdir() if p.suffix.lower() in ('.dll','.exe')]))
 print('PHASE1_BUILD_COMPLETE',b,flush=True)
def coords():
 tape=read(ROOT/'TOKEN_TAPE.json')['tokens'];out=[]
 for cap,boundary in [(1024,768),(4096,3072)]:
  for q in (2,4,32):
   for rel,h in [('inside',boundary-q),('crossing',boundary-1)]:out.append(dict(key=f'C{cap}-q{q}-{rel}',capacity=cap,boundary=boundary,width=q,head=h,relation=rel,prompt_ids=tape[:h],known_suffix=tape[h:h+q]))
 return out
def finalize_build():
 d=ROOT/'native01';b=d/'build02';deps=d/'deps-final';deps.mkdir()
 shutil.copyfile(HERE/'compile_trace.py',d/'compile_trace.py')
 cm=d/'CMakeLists.txt';shutil.copyfile(cm,d/'CMakeLists.development.txt');s=cm.read_text();s=s.replace('add_executable(worker_${arm} native_b570.cpp)','add_executable(worker_${arm} worker_${arm}.cpp)');s+='\nforeach(t core_R core_LS worker_ORIGINAL worker_R worker_LS)\n target_link_options(${t} PRIVATE /VERBOSE:LIB)\nendforeach()\n';cm.write_text(s)
 for arm in ('ORIGINAL','R','LS'):(d/('worker_'+arm+'.cpp')).write_text('#include "native_b570.cpp"\n')
 vs=Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat')
 script=d/'finalize.cmd';script.write_text('@echo off\ncall "'+str(vs)+'" -arch=x64 -host_arch=x64\nif errorlevel 1 exit /b 1\nset VSLANG=1033\nset PHASE1_DEPS='+str(deps)+'\nset VULKAN_SDK=C:\\VulkanSDK\\1.4.357.0\ncmake -S "'+str(d)+'" -B "'+str(b)+'" -G Ninja -DCMAKE_BUILD_TYPE=Release -DPYTHON="'+sys.executable+'"\nif errorlevel 1 exit /b 1\ncmake --build "'+str(b)+'" -- -j 4 -d keeprsp\n')
 command(['cmd','/d','/c',script],d/'finalize.log')
 for arm in ('ORIGINAL','R','LS'):
  bin=b/'bin'/arm;write(bin/'FILES-final.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bin.iterdir() if p.suffix.lower() in ('.dll','.exe')]))
 print('FINAL_BUILD_AND_DEPENDENCIES_READY',flush=True)
def execute(name,arm,cap,method,jobs,build='01',trace=False,native='native01'):
 folder=ROOT/'runs'/name;folder.mkdir(parents=True)
 jobs=[dict(x,request_id=name+'-'+str(i),output=str(folder/(str(i)+'.json')),admission_id=f'phase1-{native}-{arm}-C{cap}') for i,x in enumerate(jobs)]
 inp=folder/'REQUESTS.jsonl'
 with inp.open('x') as f:
  for x in jobs:f.write(json.dumps(x)+'\n')
 env={}
 if method=='S':env['HS_ECON_WHOLE']='1'
 if trace:env['HS_ECON_MICROTRACE']='1';env['HS_TRANSFER_TRACE']='1';env['HS_PARALLEL_DISPATCH']='1'
 write(folder/'ENV.json',env)
 bin=ROOT/native/('build'+build)/'bin'/arm
 m=read(ROOT/'HOST_BINDINGS.json')['models']
 argv=[str(bin/('worker_'+arm+'.exe')),m[0]['path'],m[1]['path'],str(cap),method,'4' if arm=='LS' else '0']
 cost=dict(requests=len(jobs),token_rows=sum(x.get('ordinary_cap',len(x['known_suffix']))+(0 if 'restore' in x else len(x['prompt_ids']))+(len(x['prompt_ids']) if x.get('counter_probe') else 0) for x in jobs),operators=0)
 manifest=bin/('FILES-final.json' if (bin/'FILES-final.json').exists() else 'FILES.json')
 unit,rc=nh.supervised(name,manifest,argv,cost,inp,folder/'ENV.json')
 print('NATIVE_UNIT',name,'exit',rc,flush=True)
 assert rc==0,(name,rc)
 for x in jobs:assert Path(x['output']).is_file()
 return folder
def canonical():
 folder=ROOT/'runs/canonical-C1024';folder.mkdir(parents=True)
 jobs=[]
 for x in coords():
  if x['capacity']!=1024:continue
  for repeat in range(2):
   i=len(jobs);jobs.append(dict(request_id=f'canonical-{i}',prompt_ids=x['prompt_ids'],forced_suffix=x['known_suffix'],state_prefixes=[x['prompt_ids'],x['prompt_ids']+x['known_suffix']],output=str(folder/(str(i)+'.json'))))
 inp=folder/'REQUESTS.jsonl'
 with inp.open('x') as f:
  for x in jobs:f.write(json.dumps(x)+'\n')
 write(folder/'ENV.json',dict(HS_PREFILL_OUTPUT=jobs[0]['output'],HS_PREFILL_UB='128'))
 bin=OLD/'forced-reference02/build/Release'
 manifest=folder/'FILES.json';files=[]
 for x in read(OLD/'forced-reference02/FILES.json')['files']:
  p=bin/Path(x['path'].replace('\\','/')).name;assert sha(p)==x['sha256'];files.append(dict(x,path=str(p)))
 write(manifest,dict(files=files))
 argv=read(OLD/'units/old-R-0/SUPERVISOR.json')['argv'];argv[0]=str(bin/'b570-closeout-target.exe')
 cost=dict(requests=len(jobs),token_rows=sum(len(x['prompt_ids'])+len(x['forced_suffix']) for x in jobs),operators=0)
 unit,rc=nh.supervised('canonical-C1024',manifest,argv,cost,inp,folder/'ENV.json');assert rc==0
 write(ROOT/'CANONICAL_C1024_COMPLETE.json',dict(receipts=[str(folder/(str(i)+'.json')) for i in range(len(jobs))],unchanged_original_executable=True,reference_definition_sha256=sha(ROOT/'REFERENCE_DEFINITION.json')))
 print('CANONICAL_C1024_COMPLETE',flush=True)
def references():
 for cap in (1024,4096):
  jobs=[dict(x,heavy=True) for x in coords() if x['capacity']==cap for _ in range(2)]
  folder=execute(f'reference-C{cap}','ORIGINAL',cap,'R',jobs)
  checks=[]
  for i,x in enumerate(c for c in coords() if c['capacity']==cap):
   a=folder/(str(2*i)+'.json');b=folder/(str(2*i+1)+'.json')
   suffixes=['.initial.bin','.initial.f32','.final.bin']+['.row'+str(j)+'.f32' for j in range(x['width'] if x['width']<=4 else 1)]
   equal=all(sha(str(a)+s)==sha(str(b)+s) for s in suffixes);assert equal,(x['key'],'reference repeat')
   if cap==1024:
    old=read(ROOT/'runs/canonical-C1024'/(str(2*i)+'.json'))['prefixes']
    for k in (0,1):
     source=read(ROOT/'runs/canonical-C1024'/(str(2*i+k)+'.json'))['prefixes']
     assert sha(source[0]['sequence'])==sha(str(a)+'.initial.bin')
     assert sha(source[-1]['sequence'])==sha(str(a)+'.final.bin')
     assert sha(source[0]['frontier'])==sha(str(a)+'.initial.f32')
     for j in range(x['width'] if x['width']<=4 else 1):
      index=j+1 if x['width']<=4 else x['width'];assert sha(source[index]['frontier'])==sha(str(a)+'.row'+str(j)+'.f32')
   checks.append(dict(key=x['key'],original_reference_repeat_equal=True,canonical_C1024_bridge=cap==1024,reference=str(a),native_receipt_sha256=sha(a),initial_state_sha256=sha(str(a)+'.initial.bin'),final_state_sha256=sha(str(a)+'.final.bin')))
  write(ROOT/f'REFERENCES_C{cap}.json',dict(checks=checks,capacity=cap,matched_idle_draft=True,definition_sha256=sha(ROOT/'REFERENCE_DEFINITION.json'),candidate_values_received=False))
  print('REFERENCES_QUALIFIED',cap,flush=True)
def repair():
 import numpy as np
 p=ROOT/'runs/qual-native01-C1024-S/0.json';ref=ROOT/'runs/reference-C1024/0.json'
 a=np.fromfile(str(ref)+'.row0.f32',dtype='<f4');b=np.fromfile(str(p)+'.row0.f32',dtype='<f4');diff=np.flatnonzero(a!=b)
 write(ROOT/'FAILURE-native01.json',dict(stage='development qualification, no formal freeze',coordinate='C1024-q2-inside',first_differing_vocabulary_id=int(diff[0]),reference=float(a[diff[0]]),candidate=float(b[diff[0]]),different_values=int(len(diff)),max_abs_difference=float(np.abs(a-b).max()),original_runtime_backend=sha(ROOT/'native01/build02/bin/LS/ggml-vulkan.dll'),required_PR191_backend=sha(ECO/'parallel04/M-mode0/build/Release/ggml-vulkan.dll'),cause='adapter copied canonical R backend into candidate instead of admitted F32/p021 backend',all_failed_records_and_reservations_retained=True,repair_version='native02',formal_samples=0))
 d=ROOT/'native02';d.mkdir()
 for name in ('inputs','R','LS'):shutil.copytree(ROOT/'native01'/name,d/name)
 for p in (ROOT/'native01').iterdir():
  if p.is_file() and (p.suffix in ('.cpp','.hpp') or p.name=='CMakeLists.txt'):shutil.copyfile(p,d/p.name)
 for name in ('native_b570.cpp','compile_trace.py'):shutil.copyfile(HERE/name,d/name)
 write(d/'REPAIR.json',dict(parent_version='native01',failed_qualification=str(ROOT/'FAILURE-native01.json'),changes=['restore path retains legal phase capacity and graph reuse; producer still binds UB128','candidate LS uses exact PR191 Vulkan F32/p021 backend; original R/backend unchanged'],files={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}))
 print('INDEPENDENT_REPAIR_STAGED',flush=True)
def finish_native():
 d=ROOT/'native02';b=d/'build01';deps=d/'deps02';deps.mkdir()
 shutil.copytree(b/'bin',d/'runtime-before-ordinary')
 shutil.copyfile(d/'native_b570.cpp',d/'native_b570-before-ordinary.cpp');shutil.copyfile(HERE/'native_b570.cpp',d/'native_b570.cpp')
 for core in ('R','LS'):os.utime(d/core/'src/llama-context.cpp',None)
 for arm in ('ORIGINAL','R','LS'):
  p=d/('worker_'+arm+'.cpp');p.write_text(p.read_text()+'\n')
 script=d/'finish.cmd';s=(d/'build01.cmd').read_text();s=s.replace(str(d/'deps01'),str(deps)).replace('set VSLANG=1033','set VSLANG=1033\nset VERBOSE=1').replace('-j 4 -d keeprsp','-v -j 4 -d keeprsp');script.write_text(s)
 command(['cmd','/d','/c',script],d/'finish.log')
 for arm in ('ORIGINAL','R','LS'):
  bin=b/'bin'/arm;write(bin/'FILES-final.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bin.iterdir() if p.suffix.lower() in ('.dll','.exe')]))
 print('FINAL_NATIVE02_READY',flush=True)
def qualify(build='01',native='native02'):
 checks=[]
 for cap in (1024,4096):
  refs={x['key']:x for x in read(ROOT/f'REFERENCES_C{cap}.json')['checks']}
  for method,arm in [('R','R'),('S','LS'),('L','LS')]:
   jobs=[]
   for x in coords():
    if x['capacity']!=cap:continue
    ref=refs[x['key']]['reference'];jobs.extend([dict(x,heavy=True),dict(x,heavy=True,restore=ref+'.initial.bin')])
   name=f'qual-{native}-C{cap}-{method}'
   folder=execute(name,arm,cap,method,jobs,build=build,trace=True,native=native)
   native_trace=(ROOT/'units'/name/'SUPERVISOR.stderr.log').read_text(errors='replace').splitlines();segments={};current=None;append=False
   for line in native_trace:
    if line.startswith('PHASE1_REQUEST '):current=line.split()[1];segments[current]=[]
    elif line=='PHASE1_APPEND_BEGIN':append=True
    elif line=='PHASE1_APPEND_END':append=False
    elif line.startswith('ECON_MICRO ') and append:
     f=line.split();segments[current].append(dict(serial=int(f[1]),**dict(z.split('=',1) for z in f[2:])))
   results=[]
   for i,x in enumerate(c for c in coords() if c['capacity']==cap):
    ref=refs[x['key']]['reference']
    for kind,k in [('producer',2*i),('restored',2*i+1)]:
     p=folder/(str(k)+'.json');r=read(p);suffixes=['.initial.bin','.final.bin']+['.row'+str(j)+'.f32' for j in range(x['width'] if x['width']<=4 else 1)]
     if kind=='producer':suffixes.append('.initial.f32')
     equality={s:sha(str(p)+s)==sha(ref+s) for s in suffixes}
     assert all(equality.values()),(name,x['key'],kind,equality)
     assert r['append_observer_calls']==dict(state_exports=0,state_imports=0,reference_replays=0,heavy_captures=0)
     assert r['observed_copied_rows']==(x['width'] if x['width']<=4 else 1)
     micro=segments[r['request_id']];assert micro and sum(int(t['rows']) for t in micro)==x['width']
     assert int(micro[0]['head'])==x['head'],(x['key'],kind,micro)
     assert r['final_position_min']==0 and r['final_position_max']==x['head']+x['width']-1
     results.append(dict(coordinate=x['key'],method=method,kind=kind,full_vector_and_serialized_active_KV_equal=True,required_rows=r['observed_copied_rows'],equality=equality,micrographs=micro,actual_widths=[int(t['rows']) for t in micro],actual_head=int(micro[0]['head']),reference=ref,receipt=str(p),capacity_allocation=r['admission_after_request']))
   write(folder/'QUALIFICATION.json',dict(status='QUALIFIED',checks=results,scope='Exact required full vocabulary rows, complete serialized active KV, frontier, actual physical head/graphs; q32 last row only'))
   checks.extend(results);print('PHASE1_QUALIFIED',cap,method,flush=True)
 write(ROOT/'QUALIFICATION.json',dict(status='QUALIFIED',checks=checks,protocol='review-v2',source_version=native,reference_definition_sha256=sha(ROOT/'REFERENCE_DEFINITION.json'),all_arms_retained=True))
def controls():
 assert read(ROOT/'QUALIFICATION.json')['status']=='QUALIFIED'
 exposed=read(OLD/'campaign02/runs/test-8-oldR/0.json');assert exposed['eog'][-1] is True
 results=[];observed={}
 for cap in (1024,4096):
  base=next(x for x in coords() if x['capacity']==cap)
  eog=dict(base,prompt_ids=exposed['prompt_ids'],ordinary_cap=128)
  jobs=[dict(base,ordinary_cap=1),eog,dict(base,ordinary_cap=1)]
  for method,arm in [('R','ORIGINAL'),('S','LS'),('L','LS')]:
   name=f'ordinary-native02-C{cap}-{method}';folder=execute(name,arm,cap,method,jobs,native='native02',trace=True)
   rows=[read(folder/(str(i)+'.json')) for i in range(3)]
   assert rows[0]['ids']==rows[2]['ids'] and rows[0]['materialized_output_tokens']==rows[2]['materialized_output_tokens']==0
   assert rows[1]['terminal_kind']=='EOG' and rows[1]['ids']==exposed['ids'] and rows[1]['eog']==exposed['eog']
   for i,r in enumerate(rows):
    assert r['generation_ub']==128 and r['materialized_output_tokens']==len(r['ids'])-1 and r['pending_id']==r['ids'][-1]
    if method=='R':observed[(cap,i)]=(r,folder/(str(i)+'.json'))
    else:
     ref,refpath=observed[(cap,i)];assert r['ids']==ref['ids'] and r['eog']==ref['eog'];p=folder/(str(i)+'.json')
     assert sha(str(p)+'.ordinary-final.bin')==sha(str(refpath)+'.ordinary-final.bin')
     for j in range(len(r['ids'])):assert sha(str(p)+f'.ordinary-row{j}.f32')==sha(str(refpath)+f'.ordinary-row{j}.f32')
   results.append(dict(capacity=cap,method=method,request_count=3,reset_repeat_pass=True,EOG_pass=True,cap1_pending_pass=True,complete_conditional_vectors_active_KV_equal=True,receipts=[str(folder/(str(i)+'.json')) for i in range(3)]))
 write(ROOT/'ORDINARY_CONTROLS.json',dict(results=results,no_natural_profit_panel=True,M_source_alias='producer UB128 and singleton continuation UB128; source differences only existing continuation policy, equality and occupied trace verified'))
def clean_checks():
 results=[]
 for cap in (1024,4096):
  x=next(c for c in coords() if c['capacity']==cap);ref=read(ROOT/f'REFERENCES_C{cap}.json')['checks'][0]['reference']
  for method,arm in [('R','R'),('S','LS'),('L','LS')]:
   jobs=[dict(x,restore=ref+'.initial.bin'),dict(x,restore=ref+'.initial.bin')]
   if cap==1024:jobs.append(dict(x,restore=ref+'.initial.bin',counter_probe=True))
   name=f'clean-native02-C{cap}-{method}';folder=execute(name,arm,cap,method,jobs,native='native02')
   for i in (0,1):
    r=read(folder/(str(i)+'.json'));assert r['append_observer_calls']==dict(state_exports=0,state_imports=0,reference_replays=0,heavy_captures=0) and r['capture_heavy'] is False and r['prefill_ms']==0
   if cap==1024:
    dirty=read(folder/'2.json');assert dirty['append_observer_calls']==dict(state_exports=1,state_imports=1,reference_replays=1,heavy_captures=1) and dirty['phase1_clean'] is False
   results.append(dict(capacity=cap,method=method,clean_requests=2,dirty_control=cap==1024,scope_counter_real_calls_pass=True,module_report=str(ROOT/'units'/name/'SUPERVISOR.json')))
 write(ROOT/'CLEAN_OBSERVER_QUALIFIED.json',dict(status='QUALIFIED',results=results,call_chain='own begin/decode/end/finish; no external callback, disk/vector/KV capture/replay absent inside clean append',four_counters_exercised_by_real_dirty_control=True))
def clean_build_check():
 checks=[]
 for cap in (1024,4096):
  x=next(c for c in coords() if c['capacity']==cap and c['width']==4 and c['relation']=='crossing');ref=next(z for z in read(ROOT/f'REFERENCES_C{cap}.json')['checks'] if z['key']==x['key'])['reference']
  for method,arm in [('R','R'),('S','LS'),('L','LS')]:
   folder=execute(f'clean-rebuild-C{cap}-{method}',arm,cap,method,[dict(x,heavy=True)],build='clean',native='native02',trace=True);p=folder/'0.json'
   for suffix in ['.initial.bin','.initial.f32','.final.bin']+[f'.row{j}.f32' for j in range(4)]:assert sha(str(p)+suffix)==sha(ref+suffix)
   checks.append(dict(capacity=cap,method=method,receipt=str(p),complete_outputs_active_KV_equal=True,independent_clean_directory=True))
 write(ROOT/'CLEAN_BUILD_QUALIFIED.json',dict(status='FRESH_DIRECTORY_COMPILE_AND_NATIVE_BRIDGE_PASS',checks=checks,model_weights_reused=True,downloaded_models=False,dependency_policy='Pinned original common/ggml import/static ABI libraries are explicit dependencies, not claimed rebuilt shader algorithms',source_root=str(ROOT/'native02'),build_root=str(ROOT/'native02/buildclean')))
def formal():
 sys.path.insert(0,str(HERE));import build_freeze
 from receipts import normalize_receipt
 from analyze import analyze_structural
 config=read(ROOT/'BUILD_INPUTS.json');frozen=read(ROOT/'BUILD_FREEZE.json');build_freeze.verify(config,frozen)
 freeze=read(ROOT/'FORMAL_FREEZE.json');assert freeze['qualification_sha256']==sha(ROOT/'QUALIFICATION.json') and freeze['clean_observer_sha256']==sha(ROOT/'CLEAN_OBSERVER_QUALIFIED.json') and freeze['schedule_sha256']==sha(ROOT/'SCHEDULE.json')
 inputs=read(ROOT/'INPUT_FREEZE.json')
 for x in inputs['files']:assert sha(x['path'])==x['sha256']
 plan=read(ROOT/'SCHEDULE.json');records=[];details=[];lookup={c['key']:c for c in coords()}
 observed_before=read(ROOT/'CLEAN_MODULE_SETS.json')
 for start in range(0,len(plan),2):
  pair=plan[start:start+2];assert pair[0]['kind']=='warmup' and pair[1]['kind']=='measurement'
  s=pair[0];key=s['root'].removeprefix('Smol-');x=lookup[key];method={'REFERENCE_CONTINUATION':'R','SIMPLE':'S','LOCAL':'L'}[s['arm']];arm='R' if method=='R' else 'LS';cap=s['capacity']
  ref=next(z for z in read(ROOT/f'REFERENCES_C{cap}.json')['checks'] if z['key']==key)
  jobs=[dict(x,restore=ref['reference']+'.initial.bin',slot_id=z['slot_id']) for z in pair]
  name=f'formal-v2-{start//2:03d}';folder=execute(name,arm,cap,method,jobs,native='native02')
  sup=read(ROOT/'units'/name/'SUPERVISOR.json');actual={os.path.normcase(str(Path(z['path']).resolve())):z['sha256'] for z in sup['loaded_module_hashes']}
  expected=observed_before[f'{cap}-{method}'];assert actual==expected,dict(unit=name,extra=sorted(actual.keys()-expected.keys()),missing=sorted(expected.keys()-actual.keys()))
  for i,z in enumerate(pair):
   p=folder/(str(i)+'.json');r=read(p);rec=normalize_receipt(p,z['slot_id'],ref['initial_state_sha256'],True,window='append_after_valid_state',coordinate=z);records.append(rec);details.append(dict(slot=z,receipt=str(p),preparation_ms=r['preparation_ms'],reset_ms=r['reset_ms'],state_import_and_read_ms=r['state_import_and_read_ms'],prefill_ms=r['prefill_ms'],service_ms=r['service_ms'],append_ms=r['append_ms'],observer=r['append_observer_calls']))
  write(ROOT/'performed'/(name+'.json'),dict(records=records[-2:],cost_details=details[-2:],module_set_equal=True,freeze_sha256=sha(ROOT/'FORMAL_FREEZE.json')))
 write(ROOT/'FORMAL_RECORDS.json',records);write(ROOT/'FORMAL_COST_DETAILS.json',details);write(ROOT/'STRUCTURAL_ANALYSIS.json',analyze_structural(plan,records));build_freeze.verify(config,frozen)
 print('ALL_216_SLOTS_COMPLETE',flush=True)
if __name__=='__main__':
 started=time.monotonic();success=False
 try:
  {'init':init,'stage':stage,'build':build,'repair':repair,'finish-native':finish_native,'finalize-build':finalize_build,'canonical':canonical,'references':references,'qualify':qualify,'controls':controls,'clean-checks':clean_checks,'clean-build-check':clean_build_check,'formal':formal}[sys.argv[1]](*sys.argv[2:]);success=True
 finally:
  if ROOT.exists():write(ROOT/'driver-costs'/(sys.argv[1]+'-'+str(time.time_ns())+'.json'),dict(action=sys.argv[1:],wall_seconds=time.monotonic()-started,success=success,scope='inclusive driver including nested native/build/offline work; do not add to nested costs'))
