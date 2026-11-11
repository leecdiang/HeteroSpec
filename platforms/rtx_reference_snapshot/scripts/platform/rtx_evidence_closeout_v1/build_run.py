"""Observation-only source changes on freshly verified #84 source; isolated static core."""
from run_common import *
import shutil

def patch():
    src=LOCAL/'native/source';changes=[]
    def replace(name,a,b,count=1):
        p=src/name;s=p.read_text(encoding='utf-8');assert s.count(a)==count,(name,a,s.count(a))
        p.write_text(s.replace(a,b,1),encoding='utf-8',newline='\n');changes.append(name)
    here=Path(__file__).parent
    shutil.copyfile(here/'hsc_counter.h',src/'src/hsc_counter.h')
    shutil.copyfile(here/'hsc_export.h',src/'common/hsc_export.h')
    replace('common/hs_observer.h','#include "llama.h"','#include "llama.h"\n#include "../src/hsc_counter.h"')
    replace('common/hs_observer.h','return std::getenv("HS_NATIVE_CAPTURE")!=nullptr;','return hsc::is_heavy() && std::getenv("HS_NATIVE_CAPTURE")!=nullptr;')
    replace('common/hs_observer.h','    if(!enabled())return llama_decode(c,b); // no observer metadata or forced sync',
      '''    hsc::decode_begin(c,role,phase=="prefill",b.n_tokens);
    if(!enabled()){int rc=llama_decode(c,b);hsc::decode_end();return rc;} // no added sync in baseline/counts/lite''')
    replace('common/hs_observer.h','    auto before=position(c);int rc=llama_decode(c,b);llama_synchronize(c);',
      '    auto before=position(c);int rc=llama_decode(c,b);hsc::decode_end();llama_synchronize(c);')
    replace('src/llama-context.cpp','#include "llama-context.h"','#include "llama-context.h"\n#include "hsc_counter.h"')
    replace('src/llama-context.cpp','    const auto status = graph_compute(res->get_gf(), ubatch.n_tokens > 1);',
      '''    // The inherited scheduler callback path synchronizes even when ask=false.
    // Only heavy requests may enter it. Pointer assignment adds no GPU wait.
    ggml_backend_sched_set_eval_callback(sched.get(), hsc::is_heavy() && hsc::w.context==this ? cparams.cb_eval : nullptr, cparams.cb_eval_user_data);
    hsc::physical(this,ubatch.n_tokens);
    const auto status = graph_compute(res->get_gf(), ubatch.n_tokens > 1);''')
    replace('src/llama-context.cpp','        n_reused++;','        hsc::reused(this);\n        n_reused++;')
    replace('src/llama-graph.cpp','#include "llama-graph.h"','#include "llama-graph.h"\n#include "hsc_counter.h"')
    replace('src/llama-graph.cpp','if (std::getenv("HS_NATIVE_CAPTURE"))','if (hsc::is_heavy())')
    replace('common/speculative.cpp','    void draft(common_speculative_draft_params_vec & dparams) override {\n        auto & ctx_dft = params.ctx_dft;',
      '    void draft(common_speculative_draft_params_vec & dparams) override {\n        hsc::proposal_guard proposal_scope;\n        auto & ctx_dft = params.ctx_dft;',count=4)
    replace('common/speculative.cpp','                common_sampler_sample(smpl, ctx_dft, i_batch, true);',
      '                common_sampler_sample(smpl, ctx_dft, i_batch, true);\n                hsc::stamp("draft_sampling_natural_ready",2,1);',count=2)
    replace('tools/server/server-task.h','    bool return_tokens   = false;','    bool return_tokens   = false;\n    std::string hs_closeout_mode = "counts";')
    replace('tools/server/server-task.h','struct server_task_result_cmpl_final : server_task_result {',
      'struct server_task_result_cmpl_final : server_task_result {\n    json hs_closeout;')
    replace('tools/server/server-schema.cpp','    add((new field_bool("return_tokens", params.return_tokens))',
      '''    add((new field_str("hs_closeout_mode"))
        ->set_handler([&](field_eval_context & ctx, const json & data) {
            auto mode=data.at("hs_closeout_mode").get<std::string>();
            if(mode!="baseline" && mode!="counts" && mode!="lite" && mode!="heavy")throw std::runtime_error("invalid observation mode");
            ctx.params.hs_closeout_mode=mode;
        }));
    add((new field_bool("return_tokens", params.return_tokens))''')
    replace('tools/server/server-task.cpp','        {"tokens",              tokens},','        {"tokens",              tokens},\n        {"hs_closeout",         hs_closeout},')
    replace('tools/server/server-context.cpp','#include "live_capture.h"','#include "live_capture.h"\n#include "hsc_export.h"')
    replace('tools/server/server-context.cpp','    bool load_model(common_params & params) {',
      '''    bool load_model(common_params & params) {
        // Native llama INFO maps to verbosity4. Capture load identity only, then
        // restore normal request verbosity before /health becomes ready.
        struct hs_load_log_guard {
            int previous=common_log_get_verbosity_thold();
            hs_load_log_guard(){common_log_set_verbosity_thold(std::max(previous,4));}
            ~hs_load_log_guard(){common_log_flush(common_log_main());common_log_set_verbosity_thold(previous);}
        } hs_load_log_scope;''')
    replace('tools/server/server-context.cpp','        if(hs::enabled()){params_base.cb_eval=hs::callback;params_base.cb_eval_user_data=(void*)"target";}',
      '        params_base.cb_eval=hs::callback;params_base.cb_eval_user_data=(void*)"target"; // native scheduler enables callback only in heavy requests')
    replace('tools/server/server-context.cpp','                if(hs::enabled())params_dft.cb_eval_user_data=(void*)"draft";',
      '                params_dft.cb_eval_user_data=(void*)"draft";')
    replace('tools/server/server-context.cpp','                        hs::phase="prefill";',
      '                        hs::phase="prefill";\n                        hsc::begin(slot.task->params.hs_closeout_mode,slot.task->n_tokens());')
    replace('tools/server/server-context.cpp','            slot.generated_tokens.push_back(result.tok);',
      '            slot.generated_tokens.push_back(result.tok);\n            hsc::commit();')
    replace('tools/server/server-context.cpp','        res->stats           = slot.stats;',
      '        hsc::finish_cycle();\n        res->hs_closeout = json::parse(hsc::snapshot(slot.ctx_tgt).dump());\n        res->stats           = slot.stats;')
    replace('tools/server/server-context.cpp','            slot.stats.n_draft_tokens += draft.size();',
      '            slot.stats.n_draft_tokens += draft.size();\n            hsc::propose(draft.size());')
    replace('tools/server/server-context.cpp','            common_sampler_accept(slot.smpl.get(), id, true);',
      '            hsc::stamp("target_sampling_natural_ready",1,1);\n            hsc::set_origin(slot.stats.n_gen==0?hsc::initial:hsc::fallback);\n            common_sampler_accept(slot.smpl.get(), id, true);')
    replace('tools/server/server-context.cpp','                slot.spec_i_batch.clear();\n\n                GGML_ASSERT(accepted.size() >= 1);',
      '''                const size_t hsc_a=accepted.size()-1;
                const bool hsc_mismatch=hsc_a<slot.spec_draft.size() && slot.spec_draft[hsc_a]!=accepted.back();
                hsc::verification(slot.spec_draft.size(),hsc_a,hsc_mismatch,hsc_a<slot.spec_draft.size()&&!hsc_mismatch,slot.spec_is_replay);
                slot.spec_i_batch.clear();

                GGML_ASSERT(accepted.size() >= 1);''')
    replace('tools/server/server-context.cpp','                        slot.spec_is_replay = true;',
      '                        hsc::w.unsupported_replay=true;\n                        slot.spec_is_replay = true;')
    replace('tools/server/server-context.cpp','            slot.mem.seq_rm(slot.id, slot.prompt.tokens.pos_next(), -1);',
      '            hsc::rollback();\n            slot.mem.seq_rm(slot.id, slot.prompt.tokens.pos_next(), -1);')
    replace('tools/server/server-context.cpp','                result.tok          = ids[i];',
      '                hsc::set_origin(i<n_accepted?hsc::accepted:(n_accepted==n_draft?hsc::bonus:hsc::correction));\n                result.tok          = ids[i];')
    replace('tools/server/server-context.cpp','            SLT_DBG(slot, "accepted %d/%d draft tokens, new n_tokens = %d\\n",',
      '            hsc::finish_cycle();\n            SLT_DBG(slot, "accepted %d/%d draft tokens, new n_tokens = %d\\n",')
    inv={p.relative_to(src).as_posix():sha(p) for p in sorted(src.rglob('*')) if p.is_file()}
    original=read(LOCAL/'native/BASE_SOURCE_HASHES.json')
    changed={n:h for n,h in inv.items() if original.get(n)!=h}
    assert set(changed)==set(changes)|{'src/hsc_counter.h','common/hsc_export.h'}
    save(PUB/'NATIVE_SOURCE_HASHES.json',inv)
    save(PUB/'NATIVE_PATCH.json',dict(base_source_sha256=sha(LOCAL/'native/BASE_SOURCE_HASHES.json'),changed_source_files=changed,numerical_ops_modified=False,added_sync_modes=['heavy'],source_files=len(inv)))

def build():
    asset=Path('D:/HeteroSpec-PC');src=LOCAL/'native/source';build=LOCAL/'native/build'
    zig=asset/'.venv-analysis/Lib/site-packages/ziglang/zig.exe';cmake=asset/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    cmd=[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja',
      '-DCMAKE_MAKE_PROGRAM='+str(asset/'.venv-analysis/Scripts/ninja.exe'),
      '-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++',
      '-DCMAKE_AR='+str(asset/'scripts/debug/cuda_divergence/zig-ar.cmd'),'-DCMAKE_RANLIB='+str(asset/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),
      '-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF','-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF',
      '-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF',
      '-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063','-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    attempt=[]
    for name,c in [('configure',cmd),('server',[str(cmake),'--build',str(build),'--target','llama-server','-j','4'])]:
        log=LOCAL/'native'/('build-'+name+'.log')
        with log.open('xb') as f:r=subprocess.run(c,stdout=f,stderr=subprocess.STDOUT)
        attempt.append(dict(command=c,exit_code=r.returncode,log_sha256=sha(log)))
        assert r.returncode==0,(name,log)
    dll=read(DESIGN/'ASSETS.json')['numerical_DLL_sha256']
    for n,h in dll.items():
        shutil.copyfile(asset/'tools/llama-b10839'/n,build/'bin'/n);assert sha(build/'bin'/n)==h
    save(PUB/'NATIVE_BUILD.json',dict(status='BUILT_NOT_GPU_QUALIFIED',utc=now(),server_sha256=sha(build/'bin/llama-server.exe'),source_inventory_sha256=sha(PUB/'NATIVE_SOURCE_HASHES.json'),compiler_sha256=sha(zig),cmake_sha256=sha(cmake),numerical_DLL_sha256=dll,attempts=attempt))
    status('NATIVE_BUILT',forwards=0)

if __name__=='__main__':
    patch();build()
