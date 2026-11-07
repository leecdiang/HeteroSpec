from common95 import *
import shutil
assert read(PUB/'ANCESTRY_RESTORE.json')['status']=='PASS'
src=LOCAL/'native/source';here=Path(__file__).parent
before={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
save(PUB/'PARENT_NATIVE_SOURCE_HASHES.json',before)
def replace(rel,old,new,count=1):
    p=src/rel;s=p.read_text(encoding='utf-8');assert s.count(old)==count,(rel,old,s.count(old));p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
replace('src/hs_scope.h','inline thread_local bool active = false;','''inline thread_local bool active = false;
inline int layout95() {
    static const int layout=[] { const char * p=std::getenv("HS_Q95_LAYOUT");
        if(!p || std::strcmp(p,"QB")==0)return 0;
        if(std::strcmp(p,"PQ")==0)return 1;
        if(std::strcmp(p,"GS")==0)return 2;
        throw std::runtime_error("invalid fixed query layout"); }();
    return layout;
}''')
replace('src/llama-graph.cpp','if (std::getenv("HS_ATTENTION_SINGLE_QUERY") && q->ne[2] > 1)', 'if (hs_query_batch && hs_scope::layout95()==1 && q->ne[2] > 1)')
replace('src/llama-graph.cpp','#include "hsc_counter.h"','#include "hsc_counter.h"\n#include "hs_scope.h"')
replace('src/llama-graph.cpp','GGML_ASSERT(arch == LLM_ARCH_QWEN3 && !cparams.flash_attn);','GGML_ASSERT((arch == LLM_ARCH_QWEN3 || arch == LLM_ARCH_LLAMA) && !cparams.flash_attn && hparams.n_expert == 0);',count=2)
replace('src/llama-graph.cpp','if (hs_query_batch && q->ne[1] > 1 && arch == LLM_ARCH_LLAMA)', 'if (hs_query_batch && hs_scope::layout95()==0 && q->ne[1] > 1 && arch == LLM_ARCH_LLAMA)')
replace('src/llama-graph.cpp','else if (hs_query_batch && q->ne[1] > 1)', 'else if (hs_query_batch && hs_scope::layout95()==0 && q->ne[1] > 1)')
replace('src/llama-context.cpp','mctx = memory->init_batch(*balloc, cparams.n_ubatch, output_all);','mctx = memory->init_batch(*balloc, hs_scope::active && hs_scope::layout95()==2 ? 1 : cparams.n_ubatch, output_all);')
shutil.copyfile(here/'capture95.h',src/'common/capture95.h')
replace('common/hs_observer.h','#include "../src/hs_scope.h"','#include "../src/hs_scope.h"\n#include "capture95.h"')
replace('common/hs_observer.h','inline bool callback(ggml_tensor*t,bool ask,void*data){','inline bool callback(ggml_tensor*t,bool ask,void*data){\n    if(q95capture::callback(t,ask))return true;')
replace('src/llama-graph.h','if (hs_query_batch != other.hs_query_batch) return false;','''if (hs_query_batch != other.hs_query_batch) {
            if(hsc::is_heavy() && std::getenv("HS_Q95_REUSE_TRACE")) {
                FILE * file=std::fopen(std::getenv("HS_Q95_REUSE_TRACE"),"ab");
                if(!file)throw std::runtime_error("reuse trace unavailable");
                std::fprintf(file,"{\\"cached_active\\":%d,\\"new_active\\":%d,\\"rejected\\":true}\\n",int(hs_query_batch),int(other.hs_query_batch));std::fclose(file);
            }
            return false;
        }''')
replace('src/llama-graph.h','#pragma once','#pragma once\n#include "hsc_counter.h"\n#include <cstdio>')
shutil.copyfile(here/'replay95.cpp',src/'replay95.cpp')
with (src/'CMakeLists.txt').open('a',encoding='utf-8',newline='\n') as f:f.write('''
add_executable(querylayout-replay replay95.cpp)
target_compile_features(querylayout-replay PRIVATE cxx_std_17)
target_include_directories(querylayout-replay PRIVATE ${CMAKE_SOURCE_DIR}/common)
target_link_libraries(querylayout-replay PRIVATE ggml ggml-base vendor::nlohmann)
''')
after={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
save(PUB/'NATIVE_SOURCE_HASHES.json',after)
save(PUB/'NATIVE_PATCH.json',dict(changed_files={n:h for n,h in after.items() if before.get(n)!=h},parent_head=PARENT_HEAD,numerical_backend_source_changed=False,declared_changes=['Phase-scoped historical PQ subgraphs for admitted Qwen3/Llama graphs','GS whole-target physical microbatch1, unchanged caller/output reservation and draft','Diagnostic-only native QK/softmax/AV input/output readbacks','Actual graph reuse rejection trace only in heavy diagnostic mode'],no_new_forwards=True))
asset=Path('D:/HeteroSpec-PC');zig=asset/'.venv-analysis/Lib/site-packages/ziglang/zig.exe';cmake=asset/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe';build=LOCAL/'native/build'
cmd=[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(asset/'.venv-analysis/Scripts/ninja.exe'),'-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++','-DCMAKE_AR='+str(asset/'scripts/debug/cuda_divergence/zig-ar.cmd'),'-DCMAKE_RANLIB='+str(asset/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
attempts=[];status('BUILDING_ISOLATED_NATIVE',new_forwards=0)
for name,c in [('configure',cmd),('build',[str(cmake),'--build',str(build),'--target','llama-server','querylayout-replay','-j','4'])]:
    log=LOCAL/'native'/('build-'+name+'.log')
    with log.open('xb') as f:r=subprocess.run(c,stdout=f,stderr=subprocess.STDOUT)
    attempts.append(dict(command=c,returncode=r.returncode,log_sha256=sha(log)));assert r.returncode==0,(name,log)
dlls=read(PUB/'ANCESTRY_RESTORE.json')['numerical_DLL_sha256']
for name,h in dlls.items():
    shutil.copyfile(asset/'tools/llama-b10839'/name,build/'bin'/name);assert sha(build/'bin'/name)==h
save(PUB/'NATIVE_BUILD.json',dict(status='BUILT_NOT_GPU_QUALIFIED',utc=now(),source_inventory_sha256=sha(PUB/'NATIVE_SOURCE_HASHES.json'),server_sha256=sha(build/'bin/llama-server.exe'),replay_sha256=sha(build/'bin/querylayout-replay.exe'),compiler_sha256=sha(zig),cmake_sha256=sha(cmake),numerical_DLL_sha256=dlls,attempts=attempts))
status('ISOLATED_NATIVE_BUILT',new_forwards=0)
