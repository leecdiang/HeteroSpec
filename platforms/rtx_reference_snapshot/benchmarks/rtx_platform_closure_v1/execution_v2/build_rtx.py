from pathlib import Path
import concurrent.futures, hashlib, json, os, shutil, subprocess, time
BASE=Path(__file__).resolve().parent
REPO=BASE/'HeteroSpec-rtx-closure'
CODE=REPO/'benchmarks/rtx_platform_closure_v1/execution_v2'
BUILD=BASE/'rtx-runtime-v2'
SOURCE=Path('D:/hsc95/native/source')
OLD=Path('D:/hsc95/native/build')
ZIG=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')
def pin(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def main():
    BUILD.mkdir(exist_ok=False);(BUILD/'bin').mkdir();(BUILD/'source').mkdir()
    records=[]
    for name in ('llama-graph.cpp','llama-context.cpp'):
        shutil.copyfile(SOURCE/'src'/name,BUILD/'source'/name)
    header=(SOURCE/'src/hs_scope.h').read_text(encoding='utf-8')
    first=header.index('inline int layout95()');last=header.index('inline int mask()',first)
    header=header[:first]+'inline int requested_layout=0;\ninline int layout95(){return requested_layout;}\n'+header[last:]
    (BUILD/'source/hs_scope.h').write_text(header,encoding='utf-8',newline='\n')
    shutil.copyfile(BUILD/'source/hs_scope.h',CODE/'hs_scope.h')
    includes=[BUILD/'source',SOURCE/'src',OLD/'src',SOURCE/'include',SOURCE/'ggml/include',SOURCE/'common',SOURCE/'vendor']
    def execute(label,args):
        start=time.perf_counter()
        with (BUILD/(label+'.log')).open('wb') as f:r=subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT)
        row=dict(label=label,argv=[str(x) for x in args],exit_code=r.returncode,wall_seconds=time.perf_counter()-start,log=pin(BUILD/(label+'.log')))
        if r.returncode:raise RuntimeError(str(row))
        return row
    def compile_one(name):
        src=CODE/'worker.cpp' if name=='worker.cpp' else BUILD/'source'/name
        return execute(name,[ZIG,'c++','-std=c++17','-DGGML_BACKEND_DL','-D_CRT_SECURE_NO_WARNINGS','-O3','-DNDEBUG',*[f'-I{p}' for p in includes],'-c',src,'-o',BUILD/(name+'.obj')])
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(compile_one,['llama-graph.cpp','llama-context.cpp','worker.cpp']):records.append(result)
    shutil.copyfile(OLD/'src/libllama.a',BUILD/'libllama.a')
    records.append(execute('archive',[ZIG,'ar','r',BUILD/'libllama.a',BUILD/'llama-graph.cpp.obj',BUILD/'llama-context.cpp.obj']))
    records.append(execute('link',[ZIG,'c++','-O3',BUILD/'worker.cpp.obj',BUILD/'libllama.a',OLD/'ggml/src/ggml.a',OLD/'ggml/src/ggml-base.a',OLD/'vendor/hash/libvendor-hash.a','-lpsapi','-lws2_32','-o',BUILD/'bin/rtx-closure.exe']))
    dlls=[]
    for p in (Path('D:/hs-qb-confirmation-v02/native/build/bin')).glob('*.dll'):
        target=BUILD/'bin'/p.name;os.link(p,target);dlls.append(pin(target))
    result=dict(status='BUILT_NO_MODEL_EXECUTION',build_processes=records,executable=pin(BUILD/'bin/rtx-closure.exe'),DLLs=dlls,
        original_llama_archive=pin(OLD/'src/libllama.a'),new_llama_archive=pin(BUILD/'libllama.a'),compiler=pin(ZIG),
        original_source_files=[pin(SOURCE/'src'/n) for n in ('llama-graph.cpp','llama-context.cpp','hs_scope.h')],
        sources=[pin(p) for p in (BUILD/'source').iterdir()]+[pin(CODE/'worker.cpp')],
        change='Only layout selector storage is dynamic per request; graph/context C++ bytes unchanged, original numerical CUDA DLLs unchanged. Same executable/DLLs for every arm.')
    (CODE/'BUILD_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    shutil.copyfile(__file__,CODE/'build_rtx.py')
    print(json.dumps(dict(executable=result['executable'],compiler_wall_seconds=sum(x['wall_seconds'] for x in records))))
if __name__=='__main__':main()
