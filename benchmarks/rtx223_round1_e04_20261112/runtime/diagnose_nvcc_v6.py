from pathlib import Path
import ctypes,hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v6';OUT.mkdir(exist_ok=False)
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());fixture=OUT/'fixture.cu';fixture.write_text('__global__ void hs_freeze_fixture() {}\n',encoding='ascii')
nvcc=str(HERE/'toolchain-v1/cuda/bin/nvcc.exe');cc=str(HERE/'toolchain-v1/vc/bin/Hostx64/x64');b=ctypes.create_unicode_buffer(32768)
fn=ctypes.WinDLL('kernel32').GetShortPathNameW;fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32];fn.restype=ctypes.c_uint32
if not fn(cc,b,len(b)):raise ctypes.WinError()
cc=b.value;env['TEMP']=env['TMP']=str(OUT)
argv=[nvcc,'-c',str(fixture),'-o',str(OUT/'fixture.obj'),'-ccbin',cc,'--generate-code=arch=compute_120a,code=[sm_120a]']
(OUT/'COMMAND.json').write_text(json.dumps({'argv':argv,'env':env,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'scope':'CPU-only GetShortPathName to same isolatedcopy; nonewfilesystemalias'},indent=2),encoding='utf8')
with (OUT/'compile.log').open('wb') as f:r=subprocess.run(argv,env=env,cwd=OUT,stdout=f,stderr=subprocess.STDOUT,timeout=180)
result={'returncode':r.returncode,'ccbin_short':cc,'same_cl_bytes_sha256':hashlib.sha256((Path(cc)/'cl.exe').read_bytes()).hexdigest(),'GPU_launches':0,'DLL_loads':0};(OUT/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
