"""Rebuild all numerical CUDA TUs and link an isolated DLL, without loading it."""
from pathlib import Path
import argparse,concurrent.futures,ctypes,hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source'
OLD_BUILD=Path('D:/rtx184-operator/cuda-v2')
CUDA=Path('D:/rtx184-tools/cuda')
MSVC=Path('D:/rtx184-tools/msvc')
VC=MSVC/'VC/Tools/MSVC/14.44.35207';SDK=MSVC/'Windows Kits/10';SDKVER='10.0.26100.0'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def split_windows(command):
    dll=ctypes.WinDLL('shell32',use_last_error=True)
    fn=dll.CommandLineToArgvW;fn.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];fn.restype=ctypes.POINTER(ctypes.c_wchar_p)
    count=ctypes.c_int();argv=fn(command,ctypes.byref(count))
    if not argv:raise ctypes.WinError(ctypes.get_last_error())
    result=[argv[i] for i in range(count.value)]
    free=ctypes.WinDLL('kernel32').LocalFree;free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p;free(argv)
    return result

def main():
    global SOURCE
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='build-v1');parser.add_argument('--jobs',type=int,default=2);parser.add_argument('--source',default='source')
    args=parser.parse_args();out=HERE/args.out
    SOURCE=HERE/args.source
    if SOURCE.parent!=HERE:raise RuntimeError('isolated source directory required')
    if out.parent!=HERE or args.jobs not in (1,2):raise RuntimeError('isolated output and at most two compiler workers required')
    out.mkdir(exist_ok=False);(out/'objects').mkdir();(out/'logs').mkdir();(out/'bin').mkdir();(out/'snapshots').mkdir()
    # The budget provider must be present and part of this numerical build.
    header=SOURCE/'ggml/src/ggml-cuda/hs_launch_budget.hpp'
    provider=SOURCE/'ggml/src/ggml-cuda/hs_launch_budget.cu'
    if not header.exists() or not provider.exists():raise RuntimeError('budget source integration not complete')
    env=os.environ.copy();env['PATH']=';'.join(str(p) for p in [VC/'bin/Hostx64/x64',SDK/f'bin/{SDKVER}/x64',CUDA/'bin'])+';'+env.get('PATH','')
    env['INCLUDE']=';'.join(str(p) for p in [VC/'include',*[SDK/f'Include/{SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]])
    env['LIB']=';'.join(str(p) for p in [VC/'lib/x64',SDK/f'Lib/{SDKVER}/ucrt/x64',SDK/f'Lib/{SDKVER}/um/x64',CUDA/'lib/x64'])
    env['CUDA_PATH']=str(CUDA)
    old_prefixes=['F:/rtx184/loop/native-arms/backend_loop4','F:\\rtx184\\loop\\native-arms\\backend_loop4']
    commands=[]
    old_commands=json.loads((OLD_BUILD/'compile_commands.json').read_bytes())
    for item in old_commands:
        if not item['file'].endswith('.cu'):continue
        old_file=Path(item['file']);relative=old_file.relative_to(Path(old_prefixes[0]))
        source=SOURCE/relative;target=out/'objects'/relative.with_suffix('.cu.obj')
        target.parent.mkdir(parents=True,exist_ok=True)
        argv=split_windows(item['command'])
        mapped=[];skip=False
        for token in argv:
            if token=='-DGGML_CUDA_USE_GRAPHS' or token.startswith('-Xcompiler=-Fd'):continue
            for prefix in old_prefixes:token=token.replace(prefix,str(SOURCE))
            mapped.append(token)
        mapped[mapped.index('-o')+1]=str(target)
        mapped += ['-DNOMINMAX','-DGGML_CUDA_NO_VMM']
        commands.append({'source':str(source),'object':str(target),'argv':mapped,'kind':'CUDA'})
    for name in ('hs_e03_runtime.cpp','hs_launch_budget.cu'):
        source=SOURCE/'ggml/src/ggml-cuda'/name;target=out/'objects'/Path(name).with_suffix('.obj')
        argv=[str(VC/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc','/TP','/DNOMINMAX','/DGGML_BACKEND_BUILD','/DGGML_BACKEND_SHARED','/I'+str(source.parent),'/c',str(source),'/Fo:'+str(target)]
        commands.append({'source':str(source),'object':str(target),'argv':argv,'kind':'HOST_PROVIDER'})
    numerical_files=[p for p in sorted((SOURCE/'ggml/src/ggml-cuda').rglob('*')) if p.is_file() and p.suffix in ('.cu','.cuh','.hpp','.cpp')]
    identities={str(p.relative_to(SOURCE)):sha(p) for p in numerical_files}
    (out/'SOURCE_IDENTITIES.json').write_text(json.dumps(identities,indent=2),encoding='utf8')
    (out/'COMMANDS.json').write_text(json.dumps(commands,indent=2),encoding='utf8')
    start=time.monotonic();receipts=[]
    def compile_one(index,job):
        log=out/'logs'/f'{index:03d}-{Path(job["source"]).name}.log'
        temp=out/'temp'/str(index);temp.mkdir(parents=True,exist_ok=True)
        local_env=env.copy();local_env['TEMP']=local_env['TMP']=str(temp)
        t=time.monotonic();error=None
        try:
            with log.open('xb') as f:r=subprocess.run(job['argv'],cwd=out,env=local_env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
            code=r.returncode
        except Exception as exc:code=None;error=repr(exc)
        result={**job,'returncode':code,'error':error,'seconds':time.monotonic()-t,'log':str(log),'log_sha256':sha(log)}
        if Path(job['object']).exists():result['object_sha256']=sha(job['object'])
        return index,result
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending=[pool.submit(compile_one,i,job) for i,job in enumerate(commands)]
        for future in concurrent.futures.as_completed(pending):
            index,result=future.result();receipts.append((index,result))
            with (out/'PROGRESS.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'index':index,'source':result['source'],'code':result['returncode'],'seconds':result['seconds']})+'\n')
            print(json.dumps({'compiled':len(receipts),'total':len(commands),'source':Path(result['source']).name,'code':result['returncode']}),flush=True)
    receipts=[r for _,r in sorted(receipts)]
    (out/'COMPILE_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf8')
    failed=[r for r in receipts if r['returncode']!=0]
    summary={'schema':'heterospec.e03.actual-cuda-dll-build.v1','old_build_reference':str(OLD_BUILD),'new_source':str(SOURCE),
        'compiler_workers':args.jobs,'translation_units':len(commands),'compile_failures':len(failed),'numerical_DLL_linked':False,
        'new_DLL_loaded':False,'model_requests':0,'CUDA_contexts':0,'kernel_launches':0,'wall_seconds':time.monotonic()-start}
    if failed:
        summary['status']='COMPILE_FAILED_NO_LINK';summary['failed_sources']=[r['source'] for r in failed]
        (out/'BUILD.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary));return 2
    pinned_import=OLD_BUILD/'ggml/src/ggml-base.lib'
    libs=[pinned_import,*[CUDA/f'lib/x64/{name}' for name in ['cudart.lib','cublas.lib','cuda.lib','cublasLt.lib','cudadevrt.lib','cudart_static.lib']]]
    link=[str(VC/'bin/Hostx64/x64/link.exe'),'/DLL','/MACHINE:X64','/INCREMENTAL:NO','/OUT:'+str(out/'bin/ggml-cuda.dll'),'/IMPLIB:'+str(out/'ggml-cuda.lib'),
        *[r['object'] for r in receipts],*[str(p) for p in libs],'kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib']
    response=out/'LINK.rsp'
    response.write_text('\n'.join(subprocess.list2cmdline([argument]) for argument in link[1:]),encoding='utf8')
    t=time.monotonic()
    with (out/'link.log').open('xb') as f:r=subprocess.run([link[0],'@'+str(response)],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
    (out/'LINK.json').write_text(json.dumps({'argv':link,'actual_argv':[link[0],'@'+str(response)],'response_sha256':sha(response),'code':r.returncode,'seconds':time.monotonic()-t,'libraries':{str(p):sha(p) for p in libs}},indent=2),encoding='utf8')
    summary['link_returncode']=r.returncode;summary['numerical_DLL_linked']=r.returncode==0;summary['wall_seconds']=time.monotonic()-start
    summary['status']='NUMERICAL_DLL_LINKED_NOT_LOADED_NOT_QUALIFIED' if r.returncode==0 else 'LINK_FAILED'
    if (out/'bin/ggml-cuda.dll').exists():summary['DLL_sha256']=sha(out/'bin/ggml-cuda.dll')
    summary['source_unchanged_during_build']=all(sha(SOURCE/p)==h for p,h in identities.items())
    (out/'BUILD.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary));return 0 if r.returncode==0 else 2

if __name__=='__main__':raise SystemExit(main())
