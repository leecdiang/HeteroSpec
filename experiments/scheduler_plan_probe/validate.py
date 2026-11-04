from pathlib import Path
import argparse,subprocess,json,hashlib,os
from stage import stage
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--sanitize-native',action='store_true');a=p.parse_args();a.work.mkdir(exist_ok=False,parents=True)
source=a.work/'source';build=a.work/'build';receipt=stage(a.source.resolve(),source);records=[]
def run(cmd,name):
 r=subprocess.run(list(map(str,cmd)),text=True,capture_output=True);(a.work/name).write_text(r.stdout+r.stderr);records.append({'command':list(map(str,cmd)),'status':r.returncode,'log':name})
 if r.returncode:raise RuntimeError(str(cmd))
try:
 native_flags=['-DCMAKE_C_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer','-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer'] if a.sanitize_native else []
 run(['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DGGML_CUDA=OFF','-DGGML_NATIVE=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_TOOLS=OFF','-DLLAMA_BUILD_SERVER=OFF','-DLLAMA_CURL=OFF','-DGGML_CCACHE=OFF',*native_flags],'configure.log')
 run(['cmake','--build',build,'--target','ggml','-j2'],'build.log')
 for sanitizer in (['address,undefined'] if a.sanitize_native else ['none','undefined']):
  exe=a.work/('test-'+sanitizer);flags=[] if sanitizer=='none' else ['-fsanitize='+sanitizer,'-fno-sanitize-recover=all']
  run(['g++','-std=c++17','-O2','-rdynamic',*flags,'-I'+str(HERE),'-I'+str(source/'ggml/include'),'-I'+str(source/'ggml/src'),HERE/'test_native.cpp','-L'+str(build/'bin'),'-Wl,-rpath,'+str(build/'bin'),'-lggml','-lggml-cpu','-lggml-base','-ldl','-o',exe],'compile-'+sanitizer+'.log')
  run([exe],'test-'+sanitizer+'.log')
 status='NATIVE_CPU_DRY_PREFLIGHT_PASS'
finally:
 files=[HERE/n for n in ['hs_plan_probe.h','hs_plan_probe.inc','stage.py','test_native.cpp','validate.py']]
 r={'status':locals().get('status','FAILED'),'stage':receipt,'whole_native_sanitizers':a.sanitize_native,'records':records,'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'library_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (build/'bin').glob('*.so.*') if not f.is_symlink()},'production_fast_path':'NOT_IMPLEMENTED','gpu_execution':'NOT_RUN','reader_lease':'NOT_IMPLEMENTED','zero_tail':'NOT_CHECKED','all_backend_internal_prepare':'NOT_IMPLEMENTED'}
 (a.work/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
