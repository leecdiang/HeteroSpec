"""Compile via Zig's Clang driver, avoiding failing Zig C++ cache wrapper.

Only compiles/links; never runs backend/model executables.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time,shutil

ROOT=Path(__file__).resolve().parents[2]
ZIG=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx221-round1-20261112/request/compiler_copy/zig.exe')
OLD=Path('D:/rtx211-q8-20261109')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=2),encoding='utf8')

def build(frontend,out):
    frontend=Path(frontend).resolve();out=Path(out).resolve()
    if not frontend.is_relative_to(ROOT) or not out.is_relative_to(ROOT):
        raise ValueError('frontend and fresh build output must remain inside the independent e02 workspace')
    out.mkdir(parents=True,exist_ok=False)
    snapshots=out/'source_snapshot';shutil.copytree(frontend,snapshots)
    shutil.copy2(Path(__file__),out/'direct_build.executed.py')
    source_identity={p.name:sha(p) for p in frontend.iterdir() if p.is_file()}
    env=os.environ.copy();env.update(ZIG_LIB_DIR=str(ZIG.parent/'lib'),ZIG_GLOBAL_CACHE_DIR=str(out/'global-cache'),ZIG_LOCAL_CACHE_DIR=str(out/'local-cache'),TEMP=str(out/'temp'),TMP=str(out/'temp'))
    (out/'temp').mkdir()
    windows=ZIG.parent/'lib/libc/include/any-windows-any'
    options=['-target','x86_64-windows-gnu','-stdlib=libc++','-nostdinc++', '-march=native']
    for p in [ZIG.parent/'lib/libcxx/include',ZIG.parent/'lib/libcxxabi/include',ZIG.parent/'lib/include',windows,ZIG.parent/'lib/libunwind/include']:
        options += ['-isystem',str(p)]
    definitions=['NDEBUG','__MSVCRT_VERSION__=0xE00','_WIN32_WINNT=0x0a00','_LIBCPP_ABI_VERSION=1','_LIBCPP_ABI_NAMESPACE=__1','_LIBCPP_HAS_THREADS=1','_LIBCPP_HAS_MONOTONIC_CLOCK=1','_LIBCPP_HAS_TERMINAL=1','_LIBCPP_HAS_MUSL_LIBC=0','_LIBCXXABI_DISABLE_VISIBILITY_ANNOTATIONS','_LIBCPP_DISABLE_VISIBILITY_ANNOTATIONS','_LIBCPP_HAS_VENDOR_AVAILABILITY_ANNOTATIONS=0','_LIBCPP_HAS_FILESYSTEM=1','_LIBCPP_HAS_RANDOM_DEVICE=1','_LIBCPP_HAS_LOCALIZATION=1','_LIBCPP_HAS_UNICODE=1','_LIBCPP_HAS_WIDE_CHARACTERS=1','_LIBCPP_HAS_NO_STD_MODULES=1','_LIBCPP_PSTL_BACKEND_SERIAL','_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_NONE']
    options += ['-D'+d for d in definitions]
    commands=[];inputs_before={}
    def run(label,args,cwd=out,timeout=300):
        for arg in args:
            p=Path(arg)
            if p.is_file() and out not in p.parents:
                inputs_before.setdefault(str(p),sha(p))
        begin=time.monotonic();p=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        (out/(label+'.log')).write_bytes(p.stdout)
        record={'label':label,'argv':args,'cwd':str(cwd),'returncode':p.returncode,'seconds':time.monotonic()-begin,'log_sha256':sha(out/(label+'.log'))}
        commands.append(record);put(out/'COMMANDS.json',commands)
        if p.returncode:
            put(out/'FAILED.json',record);raise RuntimeError(label+' failed: '+p.stdout.decode('utf8',errors='replace')[-6000:])
        return record
    (out/'header-smoke.cpp').write_text('#include "'+str(ROOT/'request/timeline.hpp').replace('\\','/')+'"\nint value(){hs_request_timeline::Recorder r;{hs_request_timeline::Span s(&r,"test");}r.finish();return r.spans.size();}\n',encoding='utf8')
    run('header', [str(ZIG),'clang',*options,'-std=c++17','-O3','-c',str(out/'header-smoke.cpp'),'-o',str(out/'header.obj')])
    builds={}
    for core in ('loop4','packed'):
        dest=out/core;(dest/'bin').mkdir(parents=True)
        old=OLD/(core+'-v2');before=json.loads((old/'BUILD.json').read_bytes())
        if sha(Path('D:/rtx192-review-v2/build-v2')/core/'src/libllama.a')!=before['core']:
            raise RuntimeError('qualified numerical archive changed: '+core)
        args=json.loads((old/'worker.json').read_bytes())['argv']
        args=[x.replace(str(old),str(dest)).replace(str(OLD/'frontend-v2'),str(frontend)) for x in args]
        args[0]=str(ZIG);args[1]='clang';args[2:2]=options
        run(core+'-worker',args)
        # Reuse exact previously compiled CRT/libc++ inputs by read-only path;
        # invoking the C++ wrapper would try to rebuild them via its failing cache path.
        linker=(old/'link.log').read_text(encoding='utf8').strip()
        if not linker.startswith('lld-link ') or '\n' in linker:
            raise ValueError('original linker trace is not one unambiguous command')
        args=[str(ZIG),'lld-link',*[x.replace(str(old),str(dest)) for x in linker.split()[1:]]]
        run(core+'-link',args)
        builds[core]={'exe':str(dest/'bin/worker.exe'),'exe_sha256':sha(dest/'bin/worker.exe'),'core_sha256':before['core'],'native_execution':'NOT_RUN'}
    changed=[p for p,h in inputs_before.items() if sha(p)!=h]
    if changed or source_identity!={p.name:sha(p) for p in frontend.iterdir() if p.is_file()}:
        raise RuntimeError('build inputs changed during compile/link: '+repr(changed))
    result={'status':'COMPILED_LINKED_NOT_NATIVE_QUALIFIED','commands':commands,'builds':builds,'source_hashes':source_identity,'linked_input_identities_before_and_after':inputs_before,'build_script_sha256':sha(out/'direct_build.executed.py'),'model_requests':0,'GPU_launches':0}
    put(out/'BUILD.json',result);print(json.dumps({'status':result['status'],'builds':builds,'source_members':len(source_identity),'read_only_inputs':len(inputs_before)},indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--frontend',default=str(ROOT/'request/prepared_frontend'));p.add_argument('--out',required=True);args=p.parse_args();build(args.frontend,args.out)
