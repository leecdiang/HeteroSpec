"""Build all core/frontend objects from recovered source in a fresh build directory.
CUDA numerical DLLs remain the pinned external distribution, not rebuilt CUDA kernels.
"""
import argparse,json,os,pathlib,shutil,subprocess,time
from rtx_recover import sha,read,save
P=pathlib.Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);a=ap.parse_args();root=a.root.resolve()
    source=root/'original/native/source';build=root/'clean-build';build.mkdir(exist_ok=False)
    envroot=P('D:/HeteroSpec-PC/.venv-analysis');zig=envroot/'Lib/site-packages/ziglang/zig.exe';cmake=envroot/'Lib/site-packages/cmake/data/bin/cmake.exe'
    cmd=[cmake,'-S',source,'-B',build,'-G','Ninja',f'-DCMAKE_MAKE_PROGRAM={envroot}/Scripts/ninja.exe',f'-DCMAKE_C_COMPILER={zig}','-DCMAKE_C_COMPILER_ARG1=cc',f'-DCMAKE_CXX_COMPILER={zig}','-DCMAKE_CXX_COMPILER_ARG1=c++', '-DCMAKE_AR=D:/HeteroSpec-PC/scripts/debug/cuda_divergence/zig-ar.cmd','-DCMAKE_RANLIB=D:/HeteroSpec-PC/scripts/debug/cuda_divergence/zig-ranlib.cmd','-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    records=[]
    for label,argv in [('configure',cmd),('build',[cmake,'--build',build,'--target','llama-server','querylayout-replay','-j','4'])]:
        start=time.perf_counter()
        with (build/(label+'.log')).open('wb') as f:p=subprocess.Popen([str(x) for x in argv],stdout=f,stderr=subprocess.STDOUT);rc=p.wait()
        records.append(dict(label=label,argv=list(map(str,argv)),pid=p.pid,exit_code=rc,seconds=time.perf_counter()-start,log_sha256=sha(build/(label+'.log'))));save(root/'BUILD_PROGRESS.json',records)
        if rc:raise RuntimeError(label+' failed')
        print(label,'PASS',flush=True)
    for p in (root/'original/native/bin').glob('*.dll'):shutil.copyfile(p,build/'bin'/p.name)
    save(root/'CLEAN_BUILD.json',dict(status='BUILT_NOT_NUMERICALLY_QUALIFIED',records=records,compiler_sha256=sha(zig),cmake_sha256=sha(cmake),binaries={p.name:sha(p) for p in (build/'bin').glob('*.exe')},scope='All core/frontend C++ objects rebuilt; original external numerical DLLs retained. Rebuild identity reported separately from historical executable.'))
if __name__=='__main__':main()
