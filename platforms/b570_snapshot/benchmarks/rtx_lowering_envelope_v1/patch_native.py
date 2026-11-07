"""Deterministic isolated source delta, no changes to CUDA/quantization/sampler."""
import json,shutil
from pathlib import Path
from s0_budget import ROOT,save
from recover_s0 import sha
SRC=ROOT/'native/source'
def edit(name,old,new):
    p=SRC/name;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(name,s.count(old));p.write_text(s.replace(old,new),encoding='utf-8')
def main():
    for name in ('hs113_graph.h','native113.cpp'):shutil.copy2(ROOT/name,SRC/name)
    edit('src/hs_scope.h','if(std::strcmp(p,"GS")==0)return 2;',
        'if(std::strcmp(p,"GS")==0)return 2;\n        if(std::strcmp(p,"QH_C")==0)return 3;\n        if(std::strcmp(p,"QH_D")==0)return 4;')
    edit('src/llama-graph.cpp','#include "llama-graph.h"','#include "llama-graph.h"\n#include "../hs113_graph.h"')
    needle='    const bool v_trans = v->nb[1] > v->nb[2];'
    branch='''    if (hs_query_batch && hs_scope::layout95()>=3 && q->ne[2]>1) {
        GGML_ASSERT((arch==LLM_ARCH_QWEN3 || arch==LLM_ARCH_LLAMA) && !cparams.flash_attn && hparams.n_expert==0);
        GGML_ASSERT(!kq_b && !sinks && !v_mla && k->ne[3]==1 && hparams.f_max_alibi_bias==0 && !hparams.attn_soft_cap);
        auto *qq=ggml_permute(ctx0,q,0,2,1,3);
        auto *kk=ggml_permute(ctx0,k,0,2,1,3);
        auto *vv=ggml_permute(ctx0,v,0,2,1,3);
        auto lowered=hs113::build(ctx0,qq,kk,vv,kq_mask,hs_scope::layout95()-1,kq_scale);
        cb(lowered.stage[0],"hs113_qh_QK",il);cb(lowered.stage[1],"hs113_qh_softmax",il);
        cb(lowered.stage[2],"hs113_qh_AV",il);cb(lowered.ordinary,"hs113_qh_ordinary",il);
        if(!cparams.offload_kqv)throw std::runtime_error("QH requires declared CUDA KQV offload");
        ggml_build_forward_expand(gf,lowered.ordinary);return lowered.ordinary;
    }

'''+needle
    edit('src/llama-graph.cpp',needle,branch)
    edit('src/llama-graph.h','    bool hs_query_batch = false;','    bool hs_query_batch = false;\n    int hs113_layout = -1;')
    edit('src/llama-graph.h','        if (hs_query_batch != other.hs_query_batch) {','        if (hs113_layout != other.hs113_layout) return false;\n        if (hs_query_batch != other.hs_query_batch) {')
    edit('src/llama-context.cpp','        /*.hs_query_batch =*/ hs_scope::active,','        /*.hs_query_batch =*/ hs_scope::active,\n        /*.hs113_layout =*/ hs_scope::active ? hs_scope::layout95() : -1,')
    edit('tools/server/server.cpp','#include "server-context.h"','#include "server-context.h"\n#include "server-schema.h"\n#include "../../src/hs_scope.h"\n#include <fstream>\n#include <iostream>')
    early='''    if(argc==3 && std::string(argv[1])=="--hs113-cpu-wire") {
        try {
            std::ifstream file(argv[2]);json batch;file>>batch;json out=json::array();
            for(const auto &body:batch) {
                if(!body.at("prompt").is_array() || body.at("prompt").empty())throw std::runtime_error("token-array prompt required");
                for(const auto&id:body.at("prompt"))if(!id.is_number_integer()||id.is_boolean()||id.get<int64_t>()<0)throw std::runtime_error("strict token ID required");
                common_params base;std::vector<llama_logit_bias> biases;
                auto parsed=server_schema::eval_llama_cmpl_schema(nullptr,base,biases,body);
                bool target=false,draft=true;{hs_scope::guard g("target",true);target=hs_scope::active;{hs_scope::guard d("draft",false);draft=hs_scope::active;}if(hs_scope::active!=target)throw std::runtime_error("scope restore failed");}
                out.push_back({{"prompt",body.at("prompt")},{"n_predict",parsed.n_predict},{"cache_prompt",parsed.cache_prompt},{"return_tokens",parsed.return_tokens},
                    {"mode",parsed.hs_closeout_mode},{"temperature",parsed.sampling.temp},{"top_k",parsed.sampling.top_k},{"top_p",parsed.sampling.top_p},{"min_p",parsed.sampling.min_p},
                    {"seed",parsed.sampling.seed},{"native_layout",hs_scope::layout95()},{"scope_mask",hs_scope::mask()},{"target_prefill_active",target},{"draft_continuation_active",draft},
                    {"backend_initialized",false},{"GPU_queries",0},{"parser","actual server_schema::eval_llama_cmpl_schema"}});
            }
            std::cout<<out.dump()<<"\\n";return 0;
        }catch(const std::exception&e){std::cerr<<e.what()<<"\\n";return 2;}
    }
'''
    edit('tools/server/server.cpp','    std::setlocale(LC_NUMERIC, "C");',early+'    std::setlocale(LC_NUMERIC, "C");')
    # Current inherited E1 server already carries corrected multirow capacity;
    # preserve it and record the exact source rather than re-patch spec logic.
    cmake=SRC/'CMakeLists.txt'
    with cmake.open('a') as f:f.write('''
add_executable(lowering113 native113.cpp)
target_compile_features(lowering113 PRIVATE cxx_std_17)
target_include_directories(lowering113 PRIVATE ${CMAKE_SOURCE_DIR})
target_link_libraries(lowering113 PRIVATE ggml ggml-base vendor::nlohmann psapi)
''')
    original=json.loads((ROOT/'PARENT_SOURCE_HASHES.json').read_bytes());changed={}
    for name,h in original.items():
        if sha(SRC/name)!=h:changed[name]=dict(parent=h,current=sha(SRC/name))
    for name in ('hs113_graph.h','native113.cpp'):changed[name]=dict(parent=None,current=sha(SRC/name))
    save(ROOT/'SOURCE_DELTA.json',dict(files=changed,no_CUDA_shader_precision_sampler_or_speculative_transaction_edits=True))
    print(json.dumps(dict(changed=list(changed))))
if __name__=='__main__':main()
