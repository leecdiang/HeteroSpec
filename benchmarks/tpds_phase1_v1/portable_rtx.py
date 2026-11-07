"""Fresh-directory native build from source + pinned numerical dependencies.

No model weights, historical KV archive, global installation or GPU run needed
to build. A new executable still needs its own native original-R qualification.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,j):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(j,f,indent=2)
def build(source,out,runtime,zig,cmake,ninja,sdk):
    source=source.resolve();out=out.resolve();runtime=runtime.resolve();sdk=sdk.resolve()
    assert not out.exists() and not out.is_relative_to(source) and not source.is_relative_to(out)
    out.mkdir(parents=True);assert shutil.disk_usage(out).free>=24*1024**3
    env=os.environ.copy();env.update(ZIG_GLOBAL_CACHE_DIR=str(out/'compiler-cache'),TEMP=str(out/'temp'),TMP=str(out/'temp'));(out/'temp').mkdir()
    def command(path,label,args,cwd=None):
        start=time.monotonic()
        with (path/(label+'.log')).open('xb') as f:r=subprocess.run(list(map(str,args)),cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
        save(path/(label+'.json'),dict(argv=list(map(str,args)),working_directory=str(cwd or Path.cwd()),seconds=time.monotonic()-start,code=r.returncode));r.check_returncode()
    snapshot=out/'source';shutil.copytree(source,snapshot,ignore=shutil.ignore_patterns('.git','__pycache__','*.gguf','*.key','*.pem','*.exe','*.dll','*.bin'))
    save(out/'SOURCE_MANIFEST.json',dict(source_files={p.relative_to(snapshot).as_posix():sha(p) for p in snapshot.rglob('*') if p.is_file()},excluded_uncompiled_binary_fixtures=True,models_included=False))
    for recipe in ('loop4','packed'):
        src=snapshot/'cores'/recipe;core=out/('core-'+recipe);core.mkdir();run=out/('runtime-'+recipe);run.mkdir();(run/'bin').mkdir();f=snapshot/'frontend'
        (core/'ar.cmd').write_text('@"'+str(zig)+'" ar %*\n',encoding='utf8');(core/'ranlib.cmd').write_text('@"'+str(zig)+'" ranlib %*\n',encoding='utf8')
        options=['-S',str(src),'-B',str(core),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++','-DCMAKE_AR='+str(core/'ar.cmd'),'-DCMAKE_RANLIB='+str(core/'ranlib.cmd'),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        command(core,'configure',[cmake,*options]);command(core,'core',[cmake,'--build',str(core),'--target','llama','vendor-hash','-j','4','--','-d','keeprsp','-d','keepdepfile'])
        flags=['-DPHASE_CANDIDATE=1','-std=c++17','-O3','-DNDEBUG','-DGGML_BACKEND_DL','-D_CRT_SECURE_NO_WARNINGS','-DHS_SOURCE_VARIANT="original"','-fms-extensions']
        includes=[src/'src',core/'src',src/'include',src/'ggml/include',src/'common',src/'vendor',f]+[sdk/x/'include' for x in ('cuda_nvcc','cuda_runtime','cuda_cupti')]
        command(run,'worker',[zig,'c++',*flags,*['-I'+str(p) for p in includes],'-MD','-MF',str(run/'worker.d'),'-c',str(f/'entry.cpp'),'-o',str(run/'worker.obj')])
        command(run,'link',[zig,'c++','-v','-O3',run/'worker.obj',core/'src/libllama.a',core/'ggml/src/ggml.a',core/'ggml/src/ggml-base.a',core/'vendor/hash/libvendor-hash.a','-lpsapi','-lws2_32','-lbcrypt','-o',run/'bin/worker.exe'])
        for p in runtime.glob('*.dll'):
            q=run/'bin'/p.name
            if p.stat().st_dev==q.parent.stat().st_dev:os.link(p,q)
            else:shutil.copy2(p,q)
        save(run/'BUILD.json',dict(exe=sha(run/'bin/worker.exe'),core=sha(core/'src/libllama.a'),modules={p.name:sha(p) for p in (run/'bin').glob('*.dll')},source_manifest_sha256=sha(out/'SOURCE_MANIFEST.json'),qualified=False,fresh_directory_build=True))
        print('Fresh native build complete',recipe,flush=True)
    save(out/'COMPLETE.json',dict(status='BOTH_NATIVE_CORES_AND_WORKERS_BUILT',model_forward_requests=0,toolchain={str(p):sha(p) for p in (zig,cmake,ninja)},numerical_runtime_source=str(runtime),native_qualification_required=True))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('sources','out','runtime','zig','cmake','ninja','cuda-headers'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();build(a.sources,a.out,a.runtime,a.zig,a.cmake,a.ninja,a.cuda_headers)
