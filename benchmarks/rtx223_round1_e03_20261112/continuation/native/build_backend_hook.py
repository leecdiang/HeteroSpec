"""Compile isolated patched MMVQ TU only. No DLL replacement, load or execution."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent
CORE=Path('D:/rtx192-review-v2/native-v2/cores/packed')
CUDA=Path('D:/rtx184-tools/cuda')
MSVC=Path('D:/rtx184-tools/msvc')
VC=MSVC/'VC/Tools/MSVC/14.44.35207';SDK=MSVC/'Windows Kits/10';SDKVER='10.0.26100.0'
parser=argparse.ArgumentParser();parser.add_argument('--source',default='backend-source-patch-v2');parser.add_argument('--out',default='backend-build-v1');args=parser.parse_args()
src=HERE/args.source;out=HERE/args.out
if src.parent!=HERE or out.parent!=HERE:raise RuntimeError('isolated source/output required')
out.mkdir(exist_ok=False)
env=os.environ.copy()
env['PATH']=';'.join(str(p) for p in [VC/'bin/Hostx64/x64',SDK/f'bin/{SDKVER}/x64',CUDA/'bin'])+';'+env.get('PATH','')
env['INCLUDE']=';'.join(str(p) for p in [VC/'include',*[SDK/f'Include/{SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]])
env['LIB']=';'.join(str(p) for p in [VC/'lib/x64',SDK/f'Lib/{SDKVER}/ucrt/x64',SDK/f'Lib/{SDKVER}/um/x64'])
env['CUDA_PATH']=str(CUDA);env['TEMP']=env['TMP']=str(out)
command=[str(CUDA/'bin/nvcc.exe'),'-std=c++17','-O3','-arch=sm_120','--ptxas-options=-v','-ccbin',str(VC/'bin/Hostx64/x64'),'-Xcompiler=/MT,/O2,/EHsc','-DNOMINMAX','-DGGML_CUDA_NO_VMM',
    '-I'+str(src),'-I'+str(CORE/'ggml/include'),'-I'+str(CORE/'ggml/src'),'-I'+str(CORE/'ggml/src/ggml-cuda'),'-I'+str(CORE/'vendor'),'-c',str(src/'mmvq.cu'),'-o',str(out/'mmvq.obj')]
for name in ('mmvq.cu','backend_export_hook.hpp'):(out/name).write_bytes((src/name).read_bytes())
start=time.monotonic();error=None
try:
    r=subprocess.run(command,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
    (out/'compile.log').write_bytes(r.stdout);code=r.returncode
except Exception as exc:code=None;error=repr(exc)
receipt={'kind':'ISOLATED_MMVQ_TU_COMPILE_ONLY','command':command,'returncode':code,'error':error,'seconds':time.monotonic()-start,
    'old_DLLs_replaced':False,'new_DLL_linked':False,'GPU_contexts':0,'model_requests':0,'kernel_launches':0,'native_qualification':'NOT_RUN',
    'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [src/'mmvq.cu',src/'backend_export_hook.hpp',Path(__file__)]}}
if (out/'mmvq.obj').exists():receipt['object_sha256']=hashlib.sha256((out/'mmvq.obj').read_bytes()).hexdigest()
(out/'BUILD.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt));raise SystemExit(0 if code==0 else 2)
