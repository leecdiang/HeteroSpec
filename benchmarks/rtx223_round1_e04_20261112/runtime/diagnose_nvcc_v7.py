from pathlib import Path
import hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v7';OUT.mkdir(exist_ok=False)
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());fixture=OUT/'fixture.cu';fixture.write_text('__global__ void hs_freeze_fixture() {}\n',encoding='ascii')
original=HERE/'toolchain-v1/vc/bin/Hostx64/x64';cc=OUT/'msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64'
shutil.copytree(original,cc)
nvcc=str(HERE/'toolchain-v1/cuda/bin/nvcc.exe');env['TEMP']=env['TMP']=str(OUT)
argv=[nvcc,'-c',str(fixture),'-o',str(OUT/'fixture.obj'),'-ccbin',str(cc),'--generate-code=arch=compute_120a,code=[sm_120a]','--keep','--keep-dir',str(OUT),'-v']
(OUT/'COMMAND.json').write_text(json.dumps({'argv':argv,'env':env,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'scope':'CPU-only same copied MSVC bin bytes, preserved VC/Tools/MSVC/version layout'},indent=2),encoding='utf8')
with (OUT/'compile.log').open('wb') as f:r=subprocess.run(argv,env=env,cwd=OUT,stdout=f,stderr=subprocess.STDOUT,timeout=180)
result={'returncode':r.returncode,'ccbin':str(cc),'cl_bytes_sha256':hashlib.sha256((cc/'cl.exe').read_bytes()).hexdigest(),'GPU_launches':0,'DLL_loads':0};(OUT/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
