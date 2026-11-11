"""Implement only the family committed in CANDIDATE_DECISION; zero model calls."""
from pathlib import Path
import shutil,json,hashlib,difflib
R=Path(__file__).parent;OLD=Path('C:/hs/b570-direct-id-v1-src');CORE=Path('C:/hs/b570-closeout-v1/src');B=Path('C:/hs/b570-direct-id-v1-build')
assert json.loads((R/'CANDIDATE_DECISION.json').read_text())['decision']=='IMPLEMENT_ONE_FIXED_FAMILY'
assert not (R/'candidate-src').exists()
shutil.copytree(OLD/'src',R/'candidate-src');D=R/'candidate-src'
shutil.copyfile(B/'src/llama-version.h',D/'llama-version.h')
p=D/'llama-context.h';s=p.read_text();s=s.replace('    void sched_reserve();','    void sched_reserve();\n    void b570_pilot_bind_phase_ubatch(uint32_t ub);',1);p.write_text(s,encoding='utf8')
p=D/'llama-context.cpp';s=p.read_text();s+='''
// Isolated research phase binding. No model arithmetic or KV reconstruction.
void llama_context::b570_pilot_bind_phase_ubatch(uint32_t ub) {
    if ((ub != 1 && ub != 128) || cparams.n_ctx != 1024 || cparams.n_batch != 512 || cparams.n_seq_max != 1) {
        throw std::runtime_error("Frozen B570 phase-binding contract violated");
    }
    synchronize();
    if (cparams.n_ubatch != ub) {
        cparams.n_ubatch = ub;
        sched_need_reserve = true;
        sched_reserve();
    }
}
extern "C" __declspec(dllexport) void llama_b570_pilot_bind_phase_ubatch(llama_context * ctx, uint32_t ub) {
    ctx->b570_pilot_bind_phase_ubatch(ub);
}
''';p.write_text(s,encoding='utf8')
F=R/'candidate-front';F.mkdir()
shutil.copyfile(CORE/'observer.h',F/'observer.h')
(F/'phase.h').write_text('''#pragma once
#include "llama.h"
#include "observer.h"
extern "C" __declspec(dllimport) void llama_b570_pilot_bind_phase_ubatch(llama_context *, uint32_t);
inline pj pilot_phase(llama_context * ctx, prefill_observer & o, uint32_t ub, int pending) {
    auto p=prefill_observer::positions(ctx);auto old=llama_n_ubatch(ctx);
    std::vector<uint8_t> before,after;
    if(o.instrument)before=prefill_observer::state(ctx);
    llama_b570_pilot_bind_phase_ubatch(ctx,ub);
    if(o.instrument)after=prefill_observer::state(ctx);
    if(p!=prefill_observer::positions(ctx)||llama_n_ubatch(ctx)!=ub||(o.instrument&&before!=after))throw std::runtime_error("Phase binding changed KV");
    o.bytes(".phase_before.kv",before);o.bytes(".phase_after.kv",after);
    return {{"source_ub",old},{"destination_ub",ub},{"positions",p},{"same_context",true},{"pending_id",pending},{"capture_state_bytes",before.size()},{"capture_kv_equal",o.instrument?pj(before==after):pj(nullptr)},{"opaque_sampler_bytes","unavailable; same live sampler, no serialization"},{"state_transfer",false}};
}
''',encoding='utf8')
def replace(s,a,b):
 assert a in s,a;return s.replace(a,b,1)
s=(CORE/'native.cpp').read_text();s=replace(s,'#include "observer.h"','#include "observer.h"\n#include "phase.h"')
s=replace(s,'params.n_outputs_max = output_limits.total;\n    params.n_outputs_max_per_seq = output_limits.per_seq;','params.n_outputs_max = 512;\n    params.n_outputs_max_per_seq = 1;')
s=replace(s,'    ctx_tgt=source_target;','    ctx_tgt=source_target;\n    llama_b570_pilot_bind_phase_ubatch(ctx_tgt,128);')
s=replace(s,'    observer.decode(ctx_tgt,llama_batch_get_one( inp.data(), n_input - 1),"target");\n    observer.decode(ctx_tgt,llama_batch_get_one(&inp.back(),           1),"target");','''    std::vector<llama_token> prefill_all;int prefill_past=0;
    for(size_t i=0;i<inp.size();i+=512){
        int n=std::min(size_t(512),inp.size()-i);
        prefill_all.insert(prefill_all.end(),inp.begin()+i,inp.begin()+i+n);
        observer.role="target";observer.begin(ctx_tgt,llama_batch_get_one(inp.data()+i,n));
        if(!common_prompt_batch_decode(ctx_tgt,prefill_all,n,prefill_past,512,"",false))return 82;
        observer.end(ctx_tgt,0);
    }''')
s=replace(s,'    int pending=-1;pj pending_scores;\n    if(std::getenv("HS_NO_TRANSFER")==nullptr){\n      pending_scores=observer.top(ctx_tgt,0);pending=common_sampler_sample(smpl,ctx_tgt,0);\n      auto * original_sampler=smpl;\n      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());common_sampler_free(original_sampler);mem_tgt=llama_get_memory(ctx_tgt);}', '''    for(auto id:inp)common_sampler_accept(smpl,id,false);
    int pending=-1;pj pending_scores;
    pending_scores=observer.top(ctx_tgt,-1);pending=common_sampler_sample(smpl,ctx_tgt,-1);
    const pj phase_binding=pilot_phase(ctx_tgt,observer,1,pending);''')
s=replace(s,'    pj result={{"request_id",req.at("request_id")}', '    pj result={{"phase_binding",phase_binding},{"candidate_family","CANONICAL_PREFILL_INPLACE_PHASE_BINDING"},{"target_reservation",512},{"request_id",req.at("request_id")}')
(F/'native.cpp').write_text(s,encoding='utf8')
s=(CORE/'target.cpp').read_text();s=replace(s,'#include "observer.h"','#include "observer.h"\n#include "phase.h"')
s=replace(s,'    if(std::getenv("HS_MATCHED_TARGET")){continuation_cp.n_outputs_max=1;continuation_cp.n_outputs_max_per_seq=1;}','    params.n_outputs_max=512;params.n_outputs_max_per_seq=1;')
s=replace(s,'    ctx=source_target;','    ctx=source_target;\n    llama_b570_pilot_bind_phase_ubatch(ctx,128);')
s=replace(s,'    const bool matched=std::getenv("HS_MATCHED_TARGET")!=nullptr;','    const bool matched=false;')
s=replace(s,'    if(transfer){pending_scores=observer.top(ctx,-1);pending=common_sampler_sample(sampler,ctx,-1);\n      ctx=observer.move(ctx,model,continuation_cp,sampler,pending,input.size());}','    pending_scores=observer.top(ctx,-1);pending=common_sampler_sample(sampler,ctx,-1);\n    const pj phase_binding=pilot_phase(ctx,observer,1,pending);')
s=replace(s,'    pj metrics={{"request_id",req.at("request_id")}','    pj metrics={{"phase_binding",phase_binding},{"candidate_family","CANONICAL_PREFILL_INPLACE_PHASE_BINDING"},{"target_reservation",512},{"request_id",req.at("request_id")}')
(F/'target.cpp').write_text(s,encoding='utf8')
cm='''cmake_minimum_required(VERSION 3.20)
project(b570_private_phase_pilot LANGUAGES CXX)
set(PINNED_SOURCE "C:/hs/b570-direct-id-v1-src")
set(PINNED_BUILD "C:/hs/b570-direct-id-v1-build")
file(GLOB CORE "../candidate-src/*.cpp" "../candidate-src/models/*.cpp")
add_library(llama-b570-pilot SHARED ${CORE})
target_compile_features(llama-b570-pilot PRIVATE cxx_std_17)
target_compile_options(llama-b570-pilot PRIVATE /utf-8 /bigobj)
target_compile_definitions(llama-b570-pilot PRIVATE LLAMA_BUILD LLAMA_SHARED _CRT_SECURE_NO_WARNINGS GGML_USE_CPU GGML_USE_VULKAN GGML_SHARED GGML_BACKEND_SHARED)
target_include_directories(llama-b570-pilot PRIVATE ../candidate-src "${PINNED_SOURCE}/include" "${PINNED_SOURCE}/ggml/include")
target_link_libraries(llama-b570-pilot PRIVATE "${PINNED_BUILD}/ggml/src/Release/ggml.lib" "${PINNED_BUILD}/ggml/src/Release/ggml-base.lib")
foreach(kind native target)
add_executable(b570-candidate-${kind} ${kind}.cpp)
target_compile_features(b570-candidate-${kind} PRIVATE cxx_std_17)
target_compile_definitions(b570-candidate-${kind} PRIVATE _CRT_SECURE_NO_WARNINGS LLAMA_SUBPROCESS LLAMA_SHARED GGML_SHARED GGML_BACKEND_SHARED GGML_USE_CPU GGML_USE_VULKAN)
target_include_directories(b570-candidate-${kind} PRIVATE "${PINNED_SOURCE}/common" "${PINNED_SOURCE}/include" "${PINNED_SOURCE}/ggml/include" "${PINNED_SOURCE}/vendor")
target_link_libraries(b570-candidate-${kind} PRIVATE llama-b570-pilot "${PINNED_BUILD}/common/Release/llama-common.lib" "${PINNED_BUILD}/common/Release/llama-common-base.lib" "${PINNED_BUILD}/ggml/src/Release/ggml.lib" "${PINNED_BUILD}/ggml/src/Release/ggml-cpu.lib" "${PINNED_BUILD}/ggml/src/ggml-vulkan/Release/ggml-vulkan.lib" "${PINNED_BUILD}/ggml/src/Release/ggml-base.lib")
endforeach()
'''
(F/'CMakeLists.txt').write_text(cm,encoding='utf8')
changes=[]
for name in ['llama-context.h','llama-context.cpp']:
 a=(OLD/'src'/name).read_text().splitlines(True);b=(D/name).read_text().splitlines(True)
 changes.extend(difflib.unified_diff(a,b,fromfile='pinned/src/'+name,tofile='private/src/'+name))
(R/'C_PRIVATE_LIBRARY.patch').write_text(''.join(changes),encoding='utf8')
manifest={str(p.relative_to(R)).replace('\\','/'):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in D.rglob('*') if p.is_file()}
(R/'C_PRIVATE_SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print('Created private phase library and exactly one candidate family; zero model requests.')
