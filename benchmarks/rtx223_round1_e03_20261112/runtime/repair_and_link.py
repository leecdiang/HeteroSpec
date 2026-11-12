"""Fresh repair epoch: rebuild changed TUs/provider, reuse bound successful objects."""
from pathlib import Path
import argparse
import hashlib,json,os,shutil,subprocess,time
import build_runtime as base

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--out',default='build-v3');args=parser.parse_args()
OUT=HERE/args.out
if OUT.parent!=HERE:raise RuntimeError('isolated repair output required')
OUT.mkdir(exist_ok=False)
(OUT/'objects').mkdir();(OUT/'logs').mkdir();(OUT/'bin').mkdir();(OUT/'temp').mkdir()
OLD=HERE/'build-v1';STAGE=HERE/'stage-v4'
source=HERE/'source/ggml/src/ggml-cuda'
if not (OLD/'COMPILE_RECEIPTS.json').exists():raise RuntimeError('wait for first compile batch to finish')
original=json.loads((OLD/'COMPILE_RECEIPTS.json').read_bytes())
commands=json.loads((OLD/'COMMANDS.json').read_bytes())
env=os.environ.copy()
env['PATH']=';'.join(str(p) for p in [base.VC/'bin/Hostx64/x64',base.SDK/f'bin/{base.SDKVER}/x64',base.CUDA/'bin'])+';'+env.get('PATH','')
env['INCLUDE']=';'.join(str(p) for p in [base.VC/'include',*[base.SDK/f'Include/{base.SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]])
env['LIB']=';'.join(str(p) for p in [base.VC/'lib/x64',base.SDK/f'Lib/{base.SDKVER}/ucrt/x64',base.SDK/f'Lib/{base.SDKVER}/um/x64',base.CUDA/'lib/x64'])
env['CUDA_PATH']=str(base.CUDA);env['TEMP']=env['TMP']=str(OUT/'temp')
rebuild={'mmvq.cu','ggml-cuda.cu','hs_e03_runtime.cpp','hs_launch_budget.cu'}
receipts=[];start=time.monotonic()
for old,command in zip(original,commands):
    name=Path(old['source']).name
    if name not in rebuild:
        if old['returncode']!=0:raise RuntimeError('unexpected other failed TU: '+name)
        if base.sha(old['object'])!=old['object_sha256']:raise RuntimeError('successful old object changed')
        receipts.append({'kind':'REUSED_EXACT_SUCCESSFUL_OBJECT','source':old['source'],'object':old['object'],'object_sha256':old['object_sha256'],'first_epoch_receipt':str(OLD/'COMPILE_RECEIPTS.json')})
        continue
    src=(HERE.parent/'e03/launch_budget/hs_launch_budget.cpp') if name=='hs_launch_budget.cu' else (STAGE/name if (STAGE/name).exists() else source/name)
    obj=OUT/'objects'/(name+'.obj')
    argv=list(command['argv'])
    argv=[str(src) if x==old['source'] else x for x in argv]
    if command['kind']=='CUDA':
        argv[argv.index('-o')+1]=str(obj)
        argv.insert(1,'-I'+str(STAGE))
        argv.insert(2,'-I'+str(source))
        if name=='mmvq.cu':argv.append('--ptxas-options=-v')
    else:
        argv=[('/Fo:'+str(obj)) if x.startswith('/Fo:') else x for x in argv]
        argv.insert(1,'/I'+str(STAGE))
    log=OUT/'logs'/(name+'.log');t=time.monotonic()
    with log.open('xb') as f:r=subprocess.run(argv,cwd=OUT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
    item={'kind':'FRESH_REPAIR_COMPILE','source':str(src),'source_sha256':base.sha(src),'object':str(obj),'argv':argv,'returncode':r.returncode,'seconds':time.monotonic()-t,'log_sha256':base.sha(log)}
    if obj.exists():item['object_sha256']=base.sha(obj)
    receipts.append(item)
    (OUT/'COMPILE_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf8')
    print(json.dumps({'repair':name,'code':r.returncode}),flush=True)
    if r.returncode:raise RuntimeError('repair compile failed: '+name)
libs=[base.OLD_BUILD/'ggml/src/ggml-base.lib',*[base.CUDA/f'lib/x64/{name}' for name in ['cudart.lib','cublas.lib','cuda.lib','cublasLt.lib','cudadevrt.lib','cudart_static.lib']]]
link=[str(base.VC/'bin/Hostx64/x64/link.exe'),'/DLL','/MACHINE:X64','/INCREMENTAL:NO','/OUT:'+str(OUT/'bin/ggml-cuda.dll'),'/IMPLIB:'+str(OUT/'ggml-cuda.lib'),
    *[item['object'] for item in receipts],*[str(p) for p in libs],'kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib']
response=OUT/'LINK.rsp';response.write_text('\n'.join(subprocess.list2cmdline([arg]) for arg in link[1:]),encoding='utf8')
t=time.monotonic()
with (OUT/'link.log').open('xb') as f:r=subprocess.run([link[0],'@'+str(response)],cwd=OUT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
(OUT/'LINK.json').write_text(json.dumps({'argv':link,'actual_argv':[link[0],'@'+str(response)],'response_sha256':base.sha(response),'returncode':r.returncode,'seconds':time.monotonic()-t,'libraries':{str(p):base.sha(p) for p in libs}},indent=2),encoding='utf8')
summary={'schema':'heterospec.e03.actual-cuda-dll-repair.v1','status':'NUMERICAL_DLL_LINKED_NOT_LOADED_NOT_QUALIFIED' if r.returncode==0 else 'LINK_FAILED',
    'first_epoch_preserved':str(OLD),'reused_objects':sum(x['kind'].startswith('REUSED') for x in receipts),'fresh_objects':sum(x['kind'].startswith('FRESH') for x in receipts),
    'numerical_DLL_linked':r.returncode==0,'new_DLL_loaded':False,'CUDA_contexts':0,'kernel_launches':0,'model_requests':0,'seconds':time.monotonic()-start,
    'typed_recovery_scope':'C++ errors inside graph callback caught by numerical DLL, returned as GGML_STATUS_FAILED; other API failures not generally recoverable',
    'native_budget_arming':'BLOCKED_NOT_QUALIFIED'}
if (OUT/'bin/ggml-cuda.dll').exists():summary['DLL_sha256']=base.sha(OUT/'bin/ggml-cuda.dll')
(OUT/'BUILD.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary));raise SystemExit(r.returncode)
