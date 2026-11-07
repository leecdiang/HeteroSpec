"""Isolated E1 source integration/build. Never starts a model or CUDA operator."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e

ROOT=Path('D:/hs104-e1-v1')
OLD=Path('D:/hsc95/native/source')
E2=Path('D:/hs-qb-confirmation-v02')
ASSET=Path('D:/HeteroSpec-PC')

def main():
    result=e.read(E2/'exact_restoration_20261015/E2_ANALYSIS.json')
    e.require(result['time_block_gate']=='PASS' and all(r['status']=='QUALIFIED_FINITE_PANEL' for r in result['comparisons']),'complete qualified E2 gate required')
    e.require(not (E2/'EXECUTION.lock').exists(),'E2 still active')
    ROOT.mkdir(exist_ok=False)
    plan=e.read(E2/'PLAN.json');prior=Path(plan['results'])
    inventory=e.read(prior/'NATIVE_SOURCE_HASHES.json')
    actual={p.relative_to(OLD).as_posix():e.sha(p) for p in OLD.rglob('*') if p.is_file()}
    e.require(actual==inventory,'original complete PR98 source inventory differs')
    original_build=e.read(prior/'NATIVE_BUILD.json')
    zig=ASSET/'.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    cmake=ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    e.require(e.sha(zig)==original_build['compiler_sha256'] and e.sha(cmake)==original_build['cmake_sha256'],'inherited compiler/cmake changed')
    e.save(ROOT/'PARENT_SOURCE_HASHES.json',actual)
    source=ROOT/'native/source';shutil.copytree(OLD,source)
    generated=ROOT/'generated';e.patch_e1(OLD/'common/capture95.h',OLD/'replay95.cpp',generated)
    for name,rel in [('capture95.h','common/capture95.h'),('replay95.cpp','replay95.cpp')]:
        shutil.copyfile(generated/name,source/rel)
    after={p.relative_to(source).as_posix():e.sha(p) for p in source.rglob('*') if p.is_file()}
    changed=[p for p in after if after[p]!=actual[p]]
    e.require(set(changed)=={'common/capture95.h','replay95.cpp'},'non-diagnostic source changed')
    e.save(ROOT/'SOURCE_HASHES.json',after)
    build=ROOT/'native/build'
    cmd=[str(cmake),'-S',str(source),'-B',str(build),'-G','Ninja',
         '-DCMAKE_MAKE_PROGRAM='+str(ASSET/'.venv-analysis/Scripts/ninja.exe'),
         '-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc',
         '-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++',
         '-DCMAKE_AR='+str(ASSET/'scripts/debug/cuda_divergence/zig-ar.cmd'),
         '-DCMAKE_RANLIB='+str(ASSET/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),
         '-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON',
         '-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF',
         '-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF',
         '-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF',
         '-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063',
         '-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    attempts=[]
    for label,args in [('configure',cmd),('build',[str(cmake),'--build',str(build),'--target','llama-server','querylayout-replay','-j','4'])]:
        start=time.perf_counter();log=ROOT/(label+'.log')
        with log.open('xb') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
        item=dict(label=label,command=args,exit_code=r.returncode,seconds=time.perf_counter()-start,log_sha256=e.sha(log))
        attempts.append(item);e.save(ROOT/(label+'-ATTEMPT.json'),item)
        e.require(r.returncode==0,'isolated E1 '+label+' failed; raw attempt retained')
    for name,h in original_build['numerical_DLL_sha256'].items():
        src=E2/'native/build/bin'/name;e.require(e.sha(src)==h,'old numerical DLL changed')
        shutil.copyfile(src,build/'bin'/name);e.require(e.sha(build/'bin'/name)==h,'diagnostic DLL copy differs')
    new=dict(status='BUILT_NOT_GPU_QUALIFIED',utc=e.utc(),source_inventory_sha256=e.sha(ROOT/'SOURCE_HASHES.json'),
             server_sha256=e.sha(build/'bin/llama-server.exe'),replay_sha256=e.sha(build/'bin/querylayout-replay.exe'),
             compiler_sha256=e.sha(zig),cmake_sha256=e.sha(cmake),numerical_DLL_sha256=original_build['numerical_DLL_sha256'],
             attempts=attempts,changed_source_paths=changed,new_model_requests=0,new_operator_starts=0)
    e.save(ROOT/'NATIVE_BUILD.json',new)
    print(json.dumps(new,indent=2),flush=True)
if __name__=='__main__':main()
