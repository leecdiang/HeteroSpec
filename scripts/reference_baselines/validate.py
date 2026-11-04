"""Reproducible cloud/CPU gates for the source-staged loop4 experiment."""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys
from stage import stage
ROOT=Path(__file__).resolve().parents[2]
def main(candidate,work,output):
 work.mkdir(parents=True,exist_ok=False);output.parent.mkdir(parents=True,exist_ok=True);records=[]
 def run(cmd):
  cmd=list(map(str,cmd));r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  records.append({'command':cmd,'returncode':r.returncode,'stdout_tail':r.stdout[-12000:],'stderr_tail':r.stderr[-12000:],
                  'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
  if r.returncode:
   output.write_text(json.dumps({'status':'FAILED','records':records},indent=2)+'\n');raise RuntimeError('command failed: '+str(cmd))
 receipt=stage(candidate,work/'arms');source=work/'arms/backend_loop4';build=work/'build';lib=build/'bin'
 run(['cmake','-S',source,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DGGML_CUDA=OFF','-DGGML_VULKAN=OFF','-DGGML_NATIVE=OFF','-DLLAMA_BUILD_COMMON=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_TOOLS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_SERVER=OFF','-DGGML_CCACHE=OFF'])
 run(['cmake','--build',build,'--target','llama','-j','2'])
 flags=['g++','-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-I'+str(ROOT/'src/reference_baselines'),'-I'+str(source/'ggml/include')]
 links=['-L'+str(lib),'-Wl,-rpath,'+str(lib),'-lggml','-lggml-base','-lggml-cpu']
 for name in ['test_loop4','test_cpu_reject']:
  executable=work/name
  run(flags+['-fsanitize=undefined','-fno-sanitize-recover=all',ROOT/f'tests/reference_baselines/{name}.cpp']+links+['-o',executable]);run([executable])
 run([sys.executable,'-m','unittest','discover','-s','tests/reference_baselines','-p','test_*.py','-v'])
 for name in ['generated_integration_probe.py','generated_graph_probe.py']:
  run([sys.executable,ROOT/'tests/reference_baselines'/name,'--candidate',candidate,'--library-dir',lib,'--sanitizer','address-undefined','--disable-leak-check'])
 files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['src/reference_baselines','scripts/reference_baselines','tests/reference_baselines'] for p in sorted((ROOT/folder).iterdir()) if p.is_file()}
 result={'status':'CPU_BUILD_AND_BASELINE_PROTOCOL_TESTS_PASS','platform':platform.platform(),'stage':receipt,'records':records,'source_sha256':files,
         'libraries':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [lib/'libllama.so.0.4.0',lib/'libggml-base.so.0.23.0',lib/'libggml-cpu.so.0.23.0']},
         'cuda_compilation':'NOT_RUN','gpu_execution':'NOT_RUN','reference_equivalence':'NOT_ESTABLISHED','performance':'NOT_MEASURED',
         'quantizer_count':'source structure only; GPU trace required'}
 output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.candidate.resolve(),a.work.resolve(),a.output.resolve())
