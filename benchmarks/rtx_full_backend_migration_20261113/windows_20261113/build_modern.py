from pathlib import Path
import json,os,subprocess,time,hashlib
p=Path(__file__).resolve().parent;e=p.parent/'rtx223-e11-u-contract'
env=json.loads((e/'build-003/COMMANDS.json').read_bytes())['environment'];env['TEMP']=env['TMP']=str(p)
cl=Path(env['PATH'].split(';')[0])/'cl.exe';nvcc=Path(json.loads((e/'build-003/COMMANDS.json').read_bytes())['commands'][0][1][0]);cmake=e/'tools/cmake-3.31.8-windows-x86_64/bin/cmake.exe';ninja=e/'tools/ninja/ninja.exe'
src=e/'u';out=p/'build-M';out.mkdir(exist_ok=False)
args=[str(cmake),'-S',str(p),'-B',str(out),'-G','Ninja','-DLLAMA_SOURCE_DIR='+str(src),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_C_COMPILER='+str(cl),'-DCMAKE_CXX_COMPILER='+str(cl),'-DCMAKE_CUDA_HOST_COMPILER='+str(cl),'-DCMAKE_CUDA_COMPILER='+str(nvcc),'-DCUDAToolkit_ROOT='+str(nvcc.parent.parent),'-DCMAKE_CUDA_ARCHITECTURES=120a-real','-DCMAKE_CUDA_COMPILER_FORCED=TRUE','-DGGML_CUDA=ON','-DGGML_NATIVE=OFF','-DLLAMA_CURL=OFF','-DLLAMA_OPENSSL=OFF','-DGGML_CCACHE=OFF','-DCMAKE_RUNTIME_OUTPUT_DIRECTORY='+str(out/'bin')]
commands=[('configure',[a.replace('\\','/') for a in args]),('build',[str(cmake),'--build',str(out),'--target','rtx244_worker','-j','2'])]
results=[]
for name,cmd in commands:
 start=time.monotonic()
 with (out/(name+'.stdout.log')).open('xb') as a,(out/(name+'.stderr.log')).open('xb') as b:cp=subprocess.run(cmd,cwd=p,env=env,stdout=a,stderr=b,timeout=2400,creationflags=0x08000000)
 results.append(dict(stage=name,argv=cmd,returncode=cp.returncode,seconds=time.monotonic()-start));print(json.dumps(results[-1]),flush=True)
 if cp.returncode:break
(out/'BUILD.json').write_text(json.dumps(dict(stages=results,source_commit='0fb8f157702702f33f4e018de8701b2569a1bc28',no_GPU_initialization=True,CMake_ABI_device_probe_suppressed=True),indent=2),encoding='utf8')
