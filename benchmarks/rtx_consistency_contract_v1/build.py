"""Create an isolated private frontend; never modify historical source/builds."""
import hashlib, json, os, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSET = Path(os.environ.get('HETEROSPEC_ASSET_ROOT','D:/HeteroSpec-PC'))
ORIGINAL = Path(os.environ.get('HETEROSPEC_RTX_STUDY_ROOT','D:/HeteroSpec-RTX-Target-V1')) / 'work/rtx-target-v1/pinned-source'
SRC = HERE / 'generated/source'
BUILD = HERE / 'generated/build'

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    if not SRC.exists():
        shutil.copytree(ORIGINAL, SRC)
        p = SRC / 'tools/server/server-context.cpp'
        s = p.read_text(encoding='utf-8')
        def replace(a,b):
            nonlocal s
            assert s.count(a) == 1, (a,s.count(a))
            s = s.replace(a,b)
        replace('#include "hs_observer.h"', '#include "live_capture.h"')
        replace('    llama_tokens generated_tokens;', '    llama_tokens generated_tokens;\n    llama_tokens hs_live_committed;')
        replace('        generated_tokens.clear();', '        generated_tokens.clear();\n        hs_live_committed.clear();')
        replace('        slot.generated_text += token_str;', '        if (hs_live::enabled()) slot.hs_live_committed.push_back(result.tok);\n        slot.generated_text += token_str;')
        replace('            ret = hs::decode(ctx_tgt, batch_view, "target");', '''            if (hs_live::enabled()) {
                for (auto & slot : slots) {
                    if (slot.state != SLOT_STATE_GENERATING) continue;
                    llama_tokens prefix;
                    for (int i = 0; i < slot.prompt.n_tokens() - batch_view.n_tokens; ++i) prefix.push_back(slot.prompt.tokens[i]);
                    hs_live::checkpoint(ctx_tgt, model_tgt, common_context_params_to_llama(params_base),
                            slot.smpl.get(), batch_view, slot.hs_live_committed, prefix);
                }
            }
            ret = hs::decode(ctx_tgt, batch_view, "target");''')
        p.write_text(s, encoding='utf-8', newline='\n')
    shutil.copyfile(HERE / 'live_capture.h', SRC / 'common/live_capture.h')
    zig = ASSET / '.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    cmake = ASSET / '.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    cmd = [str(cmake), '-S', str(SRC), '-B', str(BUILD), '-G', 'Ninja',
           '-DCMAKE_MAKE_PROGRAM='+str(ASSET/'.venv-analysis/Scripts/ninja.exe'),
           '-DCMAKE_C_COMPILER='+str(zig), '-DCMAKE_C_COMPILER_ARG1=cc',
           '-DCMAKE_CXX_COMPILER='+str(zig), '-DCMAKE_CXX_COMPILER_ARG1=c++',
           '-DCMAKE_AR='+str(ASSET/'scripts/debug/cuda_divergence/zig-ar.cmd'),
           '-DCMAKE_RANLIB='+str(ASSET/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),
           '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF', '-DGGML_BACKEND_DL=ON',
           '-DGGML_CPU=OFF', '-DGGML_CUDA=OFF', '-DLLAMA_SUBPROCESS=OFF', '-DLLAMA_BUILD_APP=OFF',
           '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_MTMD=OFF',
           '-DLLAMA_OPENSSL=OFF', '-DLLAMA_BUILD_UI=OFF', '-DLLAMA_USE_PREBUILT_UI=OFF',
           '-DLLAMA_BUILD_NUMBER=10839', '-DLLAMA_BUILD_COMMIT=0cae43063',
           '-DCMAKE_EXE_LINKER_FLAGS=-lpsapi', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    attempts=[]
    for name,command in [('configure',cmd), ('compile',[str(cmake),'--build',str(BUILD),'--target','llama-cli','-j','4'])]:
        with (HERE/'generated'/('build-'+name+'.log')).open('wb') as f:
            r=subprocess.run(command, stdout=f, stderr=subprocess.STDOUT)
        attempts.append({'command':command,'exit_code':r.returncode})
        (HERE/'generated/BUILD_ATTEMPTS.json').write_text(json.dumps(attempts,indent=2)+'\n')
        if r.returncode: raise RuntimeError(name+' failed; inspect retained log')
    runtime=ASSET/'tools/llama-b10839'
    for p in runtime.glob('*.dll'):
        if p.name in ('ggml.dll','ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublasLt64_12.dll','cudart64_12.dll','libomp.dll') or p.name.startswith('ggml-cpu-'):
            shutil.copyfile(p,BUILD/'bin'/p.name)
    changed={}
    for p in SRC.rglob('*'):
        if p.is_file():
            rel=p.relative_to(SRC);old=ORIGINAL/rel
            if not old.exists() or sha(old)!=sha(p):changed[str(rel).replace('\\','/')]=sha(p)
    inventory={'compiler_sha256':sha(zig),'changed_source_files':changed,
               'retained_cuda_sha256':sha(BUILD/'bin/ggml-cuda.dll'),
               'original_cuda_equal':sha(BUILD/'bin/ggml-cuda.dll')==sha(runtime/'ggml-cuda.dll'),
               'frontend_sha256':sha(BUILD/'bin/llama-cli.exe'), 'status':'BUILT_NOT_QUALIFIED'}
    (HERE/'generated/BUILD_IDENTITY.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(inventory),flush=True)

if __name__=='__main__': main()
