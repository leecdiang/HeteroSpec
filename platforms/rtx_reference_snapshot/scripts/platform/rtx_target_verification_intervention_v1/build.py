"""Build new frontends from the pinned source and retained CUDA backend."""
import io, shutil, subprocess, tarfile
from prepare import *

def replace(s,a,b,n=1):
    assert s.count(a)==n,(a,s.count(a),n)
    return s.replace(a,b)

def main():
    src=OUT/'pinned-source';build=OUT/'native-build';binary=OUT/'worker-bin';binary.mkdir(parents=True,exist_ok=True)
    if not src.exists():
        src.mkdir();archive=subprocess.check_output(['git','archive',UPSTREAM],cwd=PIN)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tf:tf.extractall(src,filter='data')
        save(DOC/'UPSTREAM_SOURCE.json',{'commit':UPSTREAM,'archive_sha256':hashlib.sha256(archive).hexdigest(),'files':{str(p.relative_to(src)).replace('\\','/'):sha(p) for p in src.rglob('*') if p.is_file()}})
    zig=ASSET/'.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    cmds=read(DOC/'BUILD_ATTEMPTS.json') if (DOC/'BUILD_ATTEMPTS.json').exists() else []
    original=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
    for name,source,defines in [('P-old',original/'worker.cpp',['-DPROPOSER_ONLY']),('R-old',original/'worker.cpp',[]),('tokenizer',original/'tokenizer.cpp',[])]:
        cmd=[str(zig),'c++','-std=c++17','-O2','-target','x86_64-windows-gnu','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor/nlohmann'),str(source),*defines,'-lpsapi','-o',str(binary/(name+'.exe'))]
        with (OUT/('build-'+name+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
        cmds.append({'command':cmd,'exit_code':r.returncode});save(DOC/'BUILD_ATTEMPTS.json',cmds)
        if r.returncode:raise RuntimeError('worker compile failed '+name)
    s=(src/'tools/server/server-context.cpp').read_text(encoding='utf-8')
    s='#include "hs_observer.h"\n'+s
    s=replace(s,'    common_init_result_ptr llama_init;','    common_init_result_ptr llama_init;\n    llama_context_ptr hs_continuation;')
    s=replace(s,'        llama_init.reset();','        hs_continuation.reset();\n        llama_init.reset();')
    s=replace(s,'        llama_init = common_init_from_params(params_base);','        if(hs::enabled()){params_base.cb_eval=hs::callback;params_base.cb_eval_user_data=(void*)"target";}\n        llama_init = common_init_from_params(params_base);')
    s=replace(s,'                common_params params_dft = common_base_params_to_speculative(params_base);','                common_params params_dft = common_base_params_to_speculative(params_base);\n                if(hs::enabled())params_dft.cb_eval_user_data=(void*)"draft";')
    s=replace(s,'            ret = llama_decode(ctx_tgt, batch_view);','            ret = hs::decode(ctx_tgt, batch_view, "target");')
    needle='            common_sampler_accept(slot.smpl.get(), id, true);'
    s=replace(s,needle,needle+'''
            if(slot.stats.n_gen==0){
                hs::emit({{"event","first_pending"},{"pending_id",id},{"logits_index",tok_idx},{"modules",hs::modules()}});
                auto cp=common_context_params_to_llama(params_base);
                auto*destination=hs::move(ctx_tgt,model_tgt,cp,slot.smpl,id,tok_idx);
                if(destination!=ctx_tgt){hs_continuation.reset(destination);ctx_tgt=destination;slot.ctx_tgt=destination;slot.mem.init(ctx_tgt,ctx_dft);}
                hs::phase="continuation";
            }
''')
    (src/'tools/server/server-context.cpp').write_text(s,encoding='utf-8',newline='\n')
    p=src/'common/speculative.cpp';s=p.read_text(encoding='utf-8');s='#include "hs_observer.h"\n'+s
    s=s.replace('llama_decode(ctx_dft, batch_dft)','hs::decode(ctx_dft, batch_dft, "draft")').replace('llama_decode(ctx_dft, batch)','hs::decode(ctx_dft, batch, "draft")')
    p.write_text(s,encoding='utf-8',newline='\n')
    p=src/'common/sampling.cpp';s=p.read_text(encoding='utf-8');start=s.index('llama_token common_sampler_sample(');end=s.index('\nstd::vector<llama_token> common_sampler_sample_and_accept_n(',start)
    block=s[start:end].replace('return id;','hs::sample(ctx,idx,id);return id;');s=s[:start]+block+s[end:]
    needle='    return result;\n}\n\nstd::vector<llama_token> common_sampler_sample_and_accept_n'
    s=replace(s,needle,'    hs::emit({{"event","verify_decision"},{"proposal_ids",draft},{"logits_indices",idxs},{"sampled_ids",result}});\n'+needle)
    p.write_text('#include "hs_observer.h"\n'+s,encoding='utf-8',newline='\n')
    shutil.copyfile(HERE/'native_observer.h',src/'common/hs_observer.h')
    p=src/'ggml/src/CMakeLists.txt';s=p.read_text(encoding='utf-8').replace('message(FATAL_ERROR "GGML_BACKEND_DL requires BUILD_SHARED_LIBS")','message(WARNING "Private frontend loads retained external CUDA backend")');p.write_text(s,encoding='utf-8',newline='\n')
    p=src/'tools/cli/cli.cpp';s=p.read_text(encoding='utf-8');s=replace(s,'    cli_context ctx_cli(params);','''    llama_backend_init();
    HMODULE hs_base = LoadLibraryW(L"ggml-base.dll");
    if(!hs_base)return 4;
    auto hs_clock=(void(*)())GetProcAddress(hs_base,"ggml_time_init");
    if(!hs_clock)return 5;hs_clock();
    cli_context ctx_cli(params);''');p.write_text(s,encoding='utf-8',newline='\n')
    cmake=ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    cmd=[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ASSET/'.venv-analysis/Scripts/ninja.exe'),'-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++','-DCMAKE_AR='+str(ASSET/'scripts/debug/cuda_divergence/zig-ar.cmd'),'-DCMAKE_RANLIB='+str(ASSET/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    for name,command in [('configure',cmd),('native',[str(cmake),'--build',str(build),'--target','llama-cli','-j','4'])]:
        with (OUT/('build-'+name+'.log')).open('wb') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
        cmds.append({'command':command,'exit_code':r.returncode});save(DOC/'BUILD_ATTEMPTS.json',cmds)
        if r.returncode:raise RuntimeError('native build failed '+name)
    for p in RUNTIME.glob('*.dll'):
        if p.name in ('ggml.dll','ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublasLt64_12.dll','cudart64_12.dll','libomp.dll') or p.name.startswith('ggml-cpu-'):shutil.copyfile(p,build/'bin'/p.name)
    save(DOC/'BUILD_IDENTITY.json',{'commands':cmds,'compiler_sha256':sha(zig),'compiler_version':subprocess.check_output([str(zig),'version'],text=True).strip(),'upstream':UPSTREAM,'core_recompiled':True,'numerical_backend':'unchanged released CUDA backend; core/frontend require fresh qualification','source_files':{str(p.relative_to(src)).replace('\\','/'):sha(p) for p in src.rglob('*') if p.is_file()},'binaries':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for d in [binary,build/'bin'] for p in d.glob('*') if p.suffix in ['.exe','.dll']},'status':'BUILT_NOT_QUALIFIED'})
    print('built new native and original workers',flush=True)

if __name__=='__main__':main()
