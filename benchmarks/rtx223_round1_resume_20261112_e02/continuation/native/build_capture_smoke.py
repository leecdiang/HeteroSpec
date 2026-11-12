"""Compile header syntax with host MSVC only; never execute native code."""
from pathlib import Path
import hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent
CORE=Path('D:/rtx192-review-v2/native-v2/cores/packed')
MSVC=Path('D:/rtx184-tools/msvc')
VC=MSVC/'VC/Tools/MSVC/14.44.35207'
SDK=MSVC/'Windows Kits/10'
SDKVER='10.0.26100.0'
out=HERE/'capture-build-v1'
out.mkdir(exist_ok=False)
env=os.environ.copy()
env['PATH']=';'.join(str(p) for p in [VC/'bin/Hostx64/x64',SDK/f'bin/{SDKVER}/x64'])+';'+env.get('PATH','')
env['INCLUDE']=';'.join(str(p) for p in [VC/'include',*[SDK/f'Include/{SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]])
env['TEMP']=env['TMP']=str(out)
args=[str(VC/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/EHsc','/Zs','/DNOMINMAX',
      '/I'+str(CORE/'ggml/include'),'/I'+str(CORE/'vendor'),'/I'+str(HERE),str(HERE/'capture_smoke.cpp')]
t=time.monotonic()
r=subprocess.run(args,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
(out/'compile.log').write_bytes(r.stdout)
receipt={'kind':'HOST_COMPILE_ONLY_NO_EXECUTION','argv':args,'returncode':r.returncode,'wall_seconds':time.monotonic()-t,
         'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'capture_operand.hpp',HERE/'capture_smoke.cpp',Path(__file__)]},
         'model_requests':0,'CUDA_contexts':0,'kernel_launches':0,'native_qualification':'NOT_RUN'}
(out/'BUILD.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt))
raise SystemExit(r.returncode)
