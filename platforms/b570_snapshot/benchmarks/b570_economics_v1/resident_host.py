"""Private original-core phase binding; unchanged R stays in its own runtime."""
from native_host import *
from stage_costs import once
from stage_resident_core import stage as core_overlay
SOURCE=Path('C:/hs/b570-direct-id-v1-src')
LIBS=Path('C:/hs/b570-direct-id-v1-build')

PHASE=r'''
#pragma once
#include "phase_binding.hpp"
extern "C" __declspec(dllimport) int b570_economics_bind_phase(llama_context*,uint32_t) noexcept;
static pj econ_phase(llama_context*ctx,prefill_observer&o,uint32_t wanted,int pending){
 const auto old=llama_n_ubatch(ctx);auto *mem=llama_get_memory(ctx);
 const auto lo=llama_memory_seq_pos_min(mem,0),hi=llama_memory_seq_pos_max(mem,0);
 // Offline-only byte witness; the clean path never exports/imports a state.
 std::vector<uint8_t> before,after;
 if(o.evidence.heavy)before=prefill_observer::state(ctx);
 b570_econ::bind_phase(wanted,[&]{return b570_econ::Snapshot{ctx,llama_get_memory(ctx),llama_memory_seq_pos_min(mem,0),llama_memory_seq_pos_max(mem,0),llama_n_ubatch(ctx)};},[&](uint32_t ub){
  if(b570_economics_bind_phase(ctx,ub))throw std::runtime_error("private phase failed; context poisoned");
 });
 if(o.evidence.heavy){after=prefill_observer::state(ctx);if(before!=after)throw std::runtime_error("phase KV bytes changed");}
 smol_capacity();
 return {{"same_context",true},{"same_KV_owner",true},{"source_ub",old},{"destination_ub",wanted},{"position_min",lo},{"position_max",hi},{"pending_id",pending},{"state_transfer",false},{"offline_witness_bytes",before.size()},{"offline_KV_equal",o.evidence.heavy?pj(true):pj(nullptr)}};
}
'''

def core(attempt='core01'):
 bind();d=ROOT/attempt
 if (d/'FILES.json').exists():return d
 d.mkdir();src=d/'source';shutil.copytree(SOURCE/'src',src/'src')
 # Bind the complete implementation; authenticate the ABI against PR187's kit.
 portable=OSMOL/'portable'
 pins=read(portable/'INPUTS.json')
 for x in pins['files']:
  p=Path(x['path'])
  if str(p).replace('\\','/').startswith('source/'):
   q=portable/p;assert sha(q)==x['sha256']
   rel=p.relative_to('source');local=SOURCE/rel
   if local.exists():assert sha(local)==x['sha256'],str(rel)
 write(d/'INPUT_SOURCE.json',dict(files={str(p.relative_to(SOURCE/'src')).replace('\\','/'):sha(p) for p in (SOURCE/'src').rglob('*') if p.is_file()},original_source=str(SOURCE),original_numerical_dll=read(ROOT/'HOST_BINDINGS.json')['original_files']))
 cp=d/'CORE_PINS.json';write(cp,dict(files={'src/'+n:sha(SOURCE/'src'/n) for n in ('llama-context.h','llama-context.cpp')}))
 overlay=d/'overlay';core_overlay(SOURCE,cp,overlay,(1,2,128))
 for p in (overlay/'src').iterdir():shutil.copyfile(p,src/'src'/p.name)
 # Observe one actual occupied graph_compute per successfully processed ubatch.
 # No per-layer embedding callbacks are counted as separate forwards.
 p=src/'src/llama-kv-cache.h';s=p.read_text();s=once(s,'    uint32_t get_n_kv() const;','    uint32_t get_n_kv() const;\n    uint32_t economics_head() const {return sinfos.at(i_cur).head();}')
 p.write_text(s)
 p=src/'src/llama-context.cpp';s=p.read_text();s='#include "llama-kv-cache.h"\n'+s
 s=once(s,'    if (!graph_reuse_disable && res->can_reuse(gparams)) {','    const bool economics_reused=!graph_reuse_disable && res->can_reuse(gparams);\n    if (economics_reused) {')
 key='    ret = GGML_STATUS_SUCCESS;\n\n    return res;'
 s=once(s,key,r'''
    if(std::getenv("HS_ECON_MICROTRACE")) {
        static uint64_t serial=0;
        auto *dense=dynamic_cast<llama_kv_cache_context*>(mctx);
        std::fprintf(stderr,"ECON_MICRO %llu ctx=%p kv=%p rows=%u outputs=%d ub=%u pos0=%d poslast=%d extent=%u head=%u reused=%d nodes=%d\n",
          (unsigned long long)++serial,(void*)this,(void*)memory.get(),ubatch.n_tokens,n_outputs,cparams.n_ubatch,
          ubatch.pos[0],ubatch.pos[ubatch.n_tokens-1],dense?dense->get_n_kv():0,dense?dense->economics_head():0,int(economics_reused),ggml_graph_n_nodes(res->get_gf()));
    }
'''+key)
 p.write_text(s)
 cm=f'''cmake_minimum_required(VERSION 3.20)
project(b570_economics_private_core LANGUAGES CXX)
file(GLOB CORE "source/src/*.cpp" "source/src/models/*.cpp")
add_library(llama SHARED ${{CORE}})
target_compile_features(llama PRIVATE cxx_std_17)
target_compile_options(llama PRIVATE /utf-8 /bigobj)
target_compile_definitions(llama PRIVATE LLAMA_BUILD LLAMA_SHARED _CRT_SECURE_NO_WARNINGS GGML_USE_CPU GGML_USE_VULKAN GGML_SHARED GGML_BACKEND_SHARED)
target_include_directories(llama PRIVATE source/src "{SOURCE.as_posix()}/include" "{SOURCE.as_posix()}/ggml/include" "{LIBS.as_posix()}/src")
target_link_libraries(llama PRIVATE "{LIBS.as_posix()}/ggml/src/Release/ggml.lib" "{LIBS.as_posix()}/ggml/src/Release/ggml-base.lib")
'''
 (d/'CMakeLists.txt').write_text(cm)
 write(d/'OUTPUT_SOURCE.json',dict(files={str(p.relative_to(src)).replace('\\','/'):sha(p) for p in src.rglob('*') if p.is_file()},arithmetic_changed=False,widths=[1,2,128],physical_trace='actual successful process_ubatch graph_compute; unique monotonic serial'))
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--parallel','4'],d/'compile.log')
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in (d/'build/Release').glob('*.dll')]))
 return d

def frontend(arm,mode=0,core_attempt='core01',attempt='resident04'):
 c=core(core_attempt);bind_arm(arm);d=ROOT/attempt/f'{arm}-mode{mode}'
 if (d/'FILES.json').exists():return d
 stage(OLD_CAMPAIGN/arm,ROOT/'bindings'/(arm+'.json'),d,mode,'target' if arm=='M' else 'native')
 for n in ('phase_binding.hpp',):shutil.copyfile(HERE/'native'/n,d/n)
 (d/'economics_phase.hpp').write_text(PHASE)
 p=d/('target.cpp' if arm=='M' else 'native.cpp');s=p.read_text();s=once(s,'#include "observer.h"','#include "observer.h"\n#include "economics_phase.hpp"')
 if arm=='M':
  s=once(s,'    common_sampler_reset(init->sampler(0));sampler=init->sampler(0);','    const auto reset_phase=econ_phase(ctx,observer,128,-1);\n    common_sampler_reset(init->sampler(0));sampler=init->sampler(0);')
  old='    if(transfer){pending_scores=observer.top(ctx,-1);pending=common_sampler_sample(sampler,ctx,-1);\n      ctx=observer.move(ctx,model,continuation_cp,sampler,pending,input.size());}'
  new='''    pending_scores=observer.top(ctx,-1);pending=common_sampler_sample(sampler,ctx,-1);
    if(observer.evidence.final_only){auto*p=llama_get_logits_ith(ctx,-1);observer.evidence.initial_vector.assign(p,p+llama_vocab_n_tokens(vocab));}
    const auto continuation_phase=econ_phase(ctx,observer,128,pending);'''
  s=once(s,old,new)
  anchor='    pj metrics={{"request_id",req.at("request_id")}';s=once(s,anchor,'    pj metrics={{"reset_phase",reset_phase},{"continuation_phase",continuation_phase},{"request_id",req.at("request_id")}')
 else:
  anchor='    llama_memory_clear(llama_get_memory(ctx_dft),true);\n    llama_synchronize(ctx_tgt);llama_synchronize(ctx_dft);'
  s=once(s,anchor,anchor+'\n    const auto reset_phase=econ_phase(ctx_tgt,observer,128,-1);')
  old='''    if(std::getenv("HS_NO_TRANSFER")==nullptr){
      pending_scores=observer.top(ctx_tgt,-1);pending=common_sampler_sample(smpl,ctx_tgt,-1);
      auto * original_sampler=smpl;
      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());common_sampler_free(original_sampler);mem_tgt=llama_get_memory(ctx_tgt);}'''
  new='''    pending_scores=observer.top(ctx_tgt,-1);pending=common_sampler_sample(smpl,ctx_tgt,-1);
    const auto continuation_phase=econ_phase(ctx_tgt,observer,1,pending);'''
  s=once(s,old,new)
  anchor='    pj result={{"request_id",req.at("request_id")}';s=once(s,anchor,'    pj result={{"reset_phase",reset_phase},{"continuation_phase",continuation_phase},{"request_id",req.at("request_id")}')
 p.write_text(s)
 # Explicit cap1 protocol path shares the actual natural stopping loop. The
 # ordinary exposed/pilot workload always defaults to the original cap128.
 s=p.read_text();key='observer.reset(req);';cap='params.n_predict=economic_cap;' if arm=='M' else 'params.n_predict=economic_cap-1;'
 s=once(s,key,key+'\n    const int economic_cap=req.value("cap",128);if(economic_cap!=1&&economic_cap!=128)throw std::runtime_error("cap profile");'+cap)
 p.write_text(s)
 p=d/'CMakeLists.txt';s=p.read_text();s=once(s,'"${PINNED_BUILD}/src/Release/llama.lib"','"'+(c/'build/Release/llama.lib').as_posix()+'"');p.write_text(s)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 active='target' if arm=='M' else 'native'
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-'+active,'--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for x in read(ROOT/'bindings/original-FILES.json')['files']:
  p=Path(x['path'])
  if p.suffix.lower()=='.dll' and p.name.lower()!='llama.dll':shutil.copyfile(p,bins/p.name)
 shutil.copyfile(c/'build/Release/llama.dll',bins/'llama.dll')
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.exe','.dll')]))
 write(d/'SOURCE.json',dict(files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt')},core=str(c),original_R_changed=False,online_KV_transfer=False,target_output_reserve_increased=False))
 return d

if __name__=='__main__':
 if sys.argv[1]=='core':print(core(),flush=True)
 else:
  for arm in ('M','H1','C4U4'):
   for mode in (0,1):print(frontend(arm,mode),flush=True)
