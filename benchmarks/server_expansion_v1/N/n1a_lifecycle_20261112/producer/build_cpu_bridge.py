"""Rebuild the CPU-only producer component bridge from fixed upstream source.
No model is read or executed by this builder. The manual commands reproduced by
this recipe were executed; this fresh-directory convenience wrapper is preparation.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--upstream-source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--jobs',type=int,default=2);a=p.parse_args()
if a.jobs not in (1,2):raise SystemExit('compile jobs must be1 or2')
if a.out.exists():raise SystemExit('fresh output directory required')
src=a.upstream_source.resolve();here=Path(__file__).resolve().parent
binding=json.loads((here/'SOURCE_BINDING.json').read_text())
for f in binding['bound_source_files']:
 q=src/f['relative_path'];b=q.read_bytes()
 if len(b)!=f['bytes'] or hashlib.sha256(b).hexdigest()!=f['sha256']:raise SystemExit('fixed source mismatch: '+f['relative_path'])
a.out.mkdir(parents=True);env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']='';env['OMP_NUM_THREADS']='2';start=time.monotonic()
flags=binding['build_recipe']['cmake_flags'];commands=[]
def run(cmd,name):
 commands.append(cmd)
 with (a.out/name).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 if r.returncode:raise SystemExit('build failed; preserve '+name)
run(['cmake','-S',str(src),'-B',str(a.out/'build')]+flags,'configure.log')
run(['cmake','--build',str(a.out/'build'),'--target','llama-common','-j'+str(a.jobs)],'build.log')
incs=['-I'+str(src/x) for x in ['common','include','ggml/include','vendor','vendor/nlohmann','tools/server','tools/mtmd']]
compiler=['g++','-std=c++17','-O2','-DNDEBUG','-ffunction-sections','-fdata-sections']
objs=[]
for name in ['server-task','server-common','server-chat']:
 obj=a.out/(name+'.o');objs.append(str(obj));run(compiler+incs+['-c',str(src/('tools/server/'+name+'.cpp')),'-o',str(obj)],name+'-compile.log')
exe=a.out/'producer_bridge';archives=sorted((a.out/'build').rglob('*.a'))
run(compiler+incs+[str(here/'producer_bridge.cpp')]+objs+['-Wl,--gc-sections','-o',str(exe),'-Wl,--start-group']+[str(q) for q in archives]+['-Wl,--end-group','-pthread','-ldl'],'link.log')
tags=subprocess.check_output(['readelf','-d',str(exe)],text=True)
if any(s in tags.lower() for s in ['cuda','cublas','vulkan','sycl']):raise SystemExit('unexpected GPU dependency')
receipt={'status':'CPU_BUILD_PASS_NOT_MODEL_QUALIFICATION','executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'executable_bytes':exe.stat().st_size,'helper_source_sha256':hashlib.sha256((here/'producer_bridge.cpp').read_bytes()).hexdigest(),'elapsed_s':time.monotonic()-start,'jobs':a.jobs,'commands':commands,'dynamic_tags':tags,'native_tool_invocations':0,'model_contexts_created':0,'forward_calls':0,'GPU_contexts_created':0}
(a.out/'BUILD.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['commands','dynamic_tags']}))
