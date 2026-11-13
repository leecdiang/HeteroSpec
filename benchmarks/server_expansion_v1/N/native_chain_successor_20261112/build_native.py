"""Compile/link only. NEVER launches a native linked executable or loads a model.

The immutable original numerical archives are verified and linked directly.
Common parser-only objects may come from the separately bound #226 CPU build;
its libllama/ggml numerical archives are deliberately never linked here.
"""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--host-root',type=Path,required=True)
p.add_argument('--out',type=Path,required=True);p.add_argument('--bindings',type=Path,required=True)
p.add_argument('--producer-build',type=Path,required=True);a=p.parse_args()
if a.out.exists(): raise SystemExit('Fresh build directory required; preserve every failure epoch')
root=a.host_root.resolve();here=Path(__file__).resolve().parent;binding=json.loads(a.bindings.read_text())
def sha(q):
 h=hashlib.sha256()
 with q.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
frozen={
 'repository-01/benchmarks/linux_transfer_v1/native/reference.cpp':'111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723',
 'run-01/stage-03/sources/reference/include/llama.h':'3d1b18eda626c1b9ecf5bda0798e65b974a8f70f30d56726610633a980cb4160',
 'run-01/stage-03/sources/reference/common/chat.cpp':'abab0d03a111bd198693a518c7cdd07a33326a6a6685cc182a88d4fdae5f61dc',
 'pr210-stage-b-build-02/frontend/worker.cpp':'429ca63224bffdc62fff65cc0c4b4199ea0ae9677fa3b087d1bbbe1d01b12938',
 'pr210-stage-b-build-02/frontend/resident_context.hpp':'02b361035da2baa586e7c2192ca05a87036ef4336a478f954ee1a006fa6b8647'}
for path,want in frozen.items():
 if sha(root/path)!=want: raise SystemExit('Complete original source identity conflict: '+path)
def expand(s):
 prefix='${HS_ROOT}/'
 if not s.startswith(prefix): raise SystemExit('Explicit bound host-relative path required')
 return root/s[len(prefix):]
selected=[]
for role in ('R','loop4'):
 item=next(x for x in binding if x['build_root']=='run-01/build-'+role+'-01')
 for archive in item['archives']:
  q=expand(archive['path'])
  if q.stat().st_size!=archive['bytes'] or sha(q)!=archive['sha256']:raise SystemExit('Original numerical archive conflict: '+str(q))
 selected.append(item)
a.out.mkdir(parents=True)
original=(root/'repository-01/benchmarks/linux_transfer_v1/native/reference.cpp').read_bytes()
sentinel=b'int main(int argc,char**argv){try{'
if original.count(sentinel)!=1:raise SystemExit('Frozen original main delimiter changed')
prefix=original.split(sentinel)[0]
(a.out/'frozen_reference_primitives.inc').write_bytes(prefix)
commands=[];env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';start=time.monotonic()
def run(argv,log,timeout=600):
 commands.append(argv)
 with (a.out/log).open('w') as f:
  r=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 if r.returncode:raise SystemExit('Compile/link failed; preserve '+str(a.out/log))
producer=a.producer_build.resolve()
front=[producer/'build/common/libllama-common.a',producer/'build/common/libllama-common-base.a',producer/'build/vendor/cpp-httplib/libcpp-httplib.a']
frontobjs=[producer/'server-task-03.o',producer/'server-common-04.o',producer/'server-chat-06.o']
for f in front+frontobjs:
 if not f.is_file():raise SystemExit('Missing source-bound parser-only object: '+str(f))
frontend_identity=[{'name':str(x.relative_to(producer)),'sha256':sha(x),'bytes':x.stat().st_size} for x in front+frontobjs]
frontend_frozen={'build/common/libllama-common.a':'b04bb9125e580960afaab7140b1aea868010f4c434aed6591f07e3200a35b247','build/common/libllama-common-base.a':'0d32a74dbd666dc604c0f52a7aaede6826585d7286f7654babce0c3397cbe07f','build/vendor/cpp-httplib/libcpp-httplib.a':'d5f2e179c047c8ad3aaf517f355232ec5281e8d126094554734e008de1671d5e','server-task-03.o':'fd40bd3171993b7ceb5907a9bfabb3fc7c185be688ae8d05043a380c44e2a0bb','server-common-04.o':'13c3e162fa6c23154e671a4ac545e3bbad7050c9f64f63b78b180571dec2f155','server-chat-06.o':'a918caadb4103bb1f2162b62a52f4f36d61567b674c423141cd1a140db81d7ce'}
for f in frontend_identity:
 if f['sha256']!=frontend_frozen[f['name']]:raise SystemExit('Parser-only object identity conflict: '+f['name'])

compiler='/usr/bin/g++';cfg=[]
for role,item in zip(('R','loop4'),selected):
 src=root/('run-01/stage-03/sources/reference' if role=='R' else 'run-01/stage-04/sources/loop4')
 out=a.out/role;out.mkdir()
 inc=[src/x for x in ('include','src','ggml/include','ggml/src','common','vendor','vendor/nlohmann','tools/server','tools/mtmd')]
 inc += [root/'repository-01/benchmarks/linux_transfer_v1/native',root/'pr210-stage-b-build-02/frontend',here/'native',a.out]
 flags=['-std=c++17','-O0','-g','-fno-lto','-fno-inline','-Wall','-Wextra']+['-I'+str(q) for q in inc]
 if role=='loop4':flags+=['-DHS_STRONG_LOOP4=1','-DHS_FROZEN_RESIDENT_CONTEXT="'+str(root/'pr210-stage-b-build-02/frontend/resident_context.hpp')+'"']
 objects=[]
 for name in ('runtime','active_kv','producer_facade','worker'):
  obj=out/(name+'.o');run([compiler]+flags+['-c',str(here/'native'/(''+name+'.cpp')),'-o',str(obj)],role+'-'+name+'-compile.log');objects.append(obj)
 original_archives=[expand(x['path']) for x in item['archives']]
 # Keep original GPU numerical code and original reference ABI. Do not use the
 # CPU producer build's libllama.a or libggml*.a as a numerical substitute.
 cuda=Path('/usr/local/cuda-12.5/targets/x86_64-linux/lib')
 system=['-lgomp','-lpthread','-lm',str(cuda/'libcudart.so'),str(cuda/'libcublas.so'),str(cuda/'libcublasLt.so'),str(cuda/'libculibos.a'),str(cuda/'stubs/libcuda.so'),'-ldl','-lrt','/usr/local/lib/libnccl.so']
 exe=out/'n1a-native-not-admitted'
 run([compiler,'-O0','-fno-lto','-Wl,--gc-sections','-Wl,-Map='+str(out/'link.map'),'-Wl,-rpath,'+str(cuda)+':/usr/local/lib']+[str(x) for x in objects+frontobjs]+['-Wl,--start-group']+[str(x) for x in front+original_archives]+['-Wl,--end-group']+system+['-o',str(exe)],role+'-link.log')
 # File/symbol readers only: never ldd, --help, selftest, dlopen or native run.
 run(['readelf','-d',str(exe)],role+'-readelf-dynamic.log')
 run(['nm','-C','--defined-only',str(exe)],role+'-symbols.log')
 symbols=(a.out/(role+'-symbols.log')).read_text()
 for required in ('llama_decode','llama_init_from_model','ggml_backend_tensor_get','capture_active_kv','prepare_native_worker','NativeProducer::advance'):
  if required not in symbols:raise SystemExit('Actual ABI symbol missing: '+required)
 cfg.append({'role':role,'executable_sha256':sha(exe),'bytes':exe.stat().st_size,'executed':False,'numerical_build':item['build_root'],'original_numerical_archives':item['archives'],'objects':[{'file':str(x.relative_to(a.out)),'bytes':x.stat().st_size,'sha256':sha(x)} for x in objects]})
receipt={'status':'COMPILED_LINKED_SYMBOL_INSPECTED_NOT_EXECUTED','elapsed_s':time.monotonic()-start,'whole_source_gate':frozen,'reference_helper_prefix_sha256':sha(a.out/'frozen_reference_primitives.inc'),'reference_main_excluded':True,'original_reference_whole_file_used_for_derivation':True,'parser_only_frontend_objects':frontend_identity,'commands':commands,'artifacts':cfg,'native_executables_started':0,'backend_initializations':0,'model_creations':0,'model_contexts':0,'GPU_contexts':0,'placement_actions':0,'forwards':0}
(a.out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k in ('status','elapsed_s','native_executables_started','backend_initializations','model_creations','GPU_contexts','forwards')}))
