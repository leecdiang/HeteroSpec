"""Build/run CPU-only accounting fixture. Source has no CUDA headers/libraries."""
from pathlib import Path
import hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent
MSVC=Path('D:/rtx184-tools/msvc');VC=MSVC/'VC/Tools/MSVC/14.44.35207'
SDK=MSVC/'Windows Kits/10';SDKVER='10.0.26100.0'
out=HERE/'host-accounting-v1';out.mkdir(exist_ok=False)
env=os.environ.copy()
env['PATH']=';'.join(str(p) for p in [VC/'bin/Hostx64/x64',SDK/f'bin/{SDKVER}/x64'])+';'+env.get('PATH','')
env['INCLUDE']=';'.join(str(p) for p in [VC/'include',*[SDK/f'Include/{SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]])
env['LIB']=';'.join(str(p) for p in [VC/'lib/x64',SDK/f'Lib/{SDKVER}/ucrt/x64',SDK/f'Lib/{SDKVER}/um/x64'])
env['TEMP']=env['TMP']=str(out)
args=[str(VC/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','/O2','/I'+str(HERE),str(HERE/'launch_accounting_test.cpp'),'/Fe:'+str(out/'cpu_accounting.exe')]
start=time.monotonic()
compile_result=subprocess.run(args,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
(out/'compile.log').write_bytes(compile_result.stdout)
if compile_result.returncode:raise RuntimeError('CPU accounting build failed')
r=subprocess.run([str(out/'cpu_accounting.exe')],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10)
(out/'run.log').write_bytes(r.stdout)
receipt={'scope':'CPU_NATIVE_ACCOUNTING_ONLY_NO_CUDA_IN_SOURCE_OR_LINK','compile_argv':args,'compile_returncode':compile_result.returncode,
    'run_returncode':r.returncode,'result':json.loads(r.stdout) if r.returncode==0 else None,'seconds':time.monotonic()-start,
    'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'launch_accounting.hpp',HERE/'launch_accounting_test.cpp',Path(__file__)]},
    'model_requests':0,'CUDA_contexts':0,'kernel_launches':0,'native_GPU_qualification':'NOT_RUN'}
(out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt));raise SystemExit(r.returncode)
