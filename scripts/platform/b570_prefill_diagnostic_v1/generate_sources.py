"""Mechanical derivation from fixed, read-only frontends; no inference."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
PIN=Path('C:/hs/b570-direct-id-v1-src')
def replace(s,a,b,n=1):
    assert s.count(a)==n,(a,s.count(a),n)
    return s.replace(a,b)
h=(ROOT/'scripts/platform/b570_mechanism_v08/harness.cpp').read_text()
h=replace(h,'using json = nlohmann::ordered_json;','#include "observer.h"\nusing json = nlohmann::ordered_json;')
h=replace(h,'    llama_backend_init();','    prefill_observer observer;\n    if(observer.instrument){params.cb_eval=prefill_observer::callback;params.cb_eval_user_data=&observer;}\n    const auto continuation_cp=common_context_params_to_llama(params);\n    llama_backend_init();')
h=replace(h,'    auto init = common_init_from_params(params);','    params.n_ubatch=observer.prefill_ub;\n    auto init = common_init_from_params(params);')
h=replace(h,'    std::vector<llama_token> all;','    observer.phase="prefill";\n    std::vector<llama_token> all;')
h=replace(h,'        if (!common_prompt_batch_decode(ctx,all,size,n_past,512,"",false)) return 7;',
    '        observer.begin(ctx,llama_batch_get_one(chunk.data(),size));\n        if (!common_prompt_batch_decode(ctx,all,size,n_past,512,"",false)) return 7;\n        observer.end(ctx,0);')
h=replace(h,'    std::vector<llama_token> generated;',
    '    int pending=-1; json pending_scores;\n    const bool transfer=std::getenv("HS_NO_TRANSFER")==nullptr && continuation_cp.n_ubatch==1;\n    if(transfer){pending_scores=observer.top(ctx,-1);pending=common_sampler_sample(sampler,ctx,-1);\n      ctx=observer.move(ctx,model,continuation_cp,sampler,pending,input.size());}\n    observer.phase="continuation";\n    std::vector<llama_token> generated;')
h=replace(h,'        const float * logits = llama_get_logits_ith(ctx,-1);','        const float * logits = pending>=0 && i==0 ? nullptr : llama_get_logits_ith(ctx,-1);')
h=replace(h,'        if (!logits) return 8;','        if (!logits && !(pending>=0 && i==0)) return 8;')
h=replace(h,'        for (int id=0;id<llama_vocab_n_tokens(vocab);++id) {','        if(logits) for (int id=0;id<llama_vocab_n_tokens(vocab);++id) {')
h=replace(h,'        const float first=logits[top1],second=logits[top2];\n        const llama_token id=common_sampler_sample(sampler,ctx,-1);',
    '        if(!logits){top1=pending_scores["top1"];top2=pending_scores["top2"];}\n        const float first=logits?logits[top1]:pending_scores["top1_score"].get<float>(),second=logits?logits[top2]:pending_scores["top2_score"].get<float>();\n        const llama_token id=(pending>=0 && i==0)?pending:common_sampler_sample(sampler,ctx,-1);')
h=replace(h,'        generated.push_back(id);eog.push_back(stop);','        generated.push_back(id);eog.push_back(stop);\n        observer.commit(ctx,id,stop,false,-1,-1,{{"top1",top1},{"top2",top2},{"top1_score",first},{"top2_score",second}});')
h=replace(h,'        if (!common_prompt_batch_decode(ctx,all,1,n_past,512,"",false)) return 9;',
    '        observer.begin(ctx,llama_batch_get_one(&all.back(),1));\n        if (!common_prompt_batch_decode(ctx,all,1,n_past,512,"",false)) return 9;\n        observer.end(ctx,0);')
h=replace(h,'    std::ofstream out(output_path,std::ios::binary);','    observer.finish(generated,eog,input);\n    std::ofstream out(output_path+std::string(".mechanism.json"),std::ios::binary);')
(HERE/'target.cpp').write_text(h,newline='\n')
s=(PIN/'examples/speculative/speculative.cpp').read_text()
s=replace(s,'#include "heterospec-direct-id.h"','#include "heterospec-direct-id.h"\n#include "observer.h"')
s=replace(s,'    // max number of parallel drafting sequences',
    '    if(params.n_parallel!=1||params.n_ctx!=1024||params.n_batch!=512||params.n_ubatch!=1||params.sampling.temp!=0||params.sampling.seed!=123||params.speculative.draft.n_max!=2||params.n_predict!=127) return 80;\n    prefill_observer observer;\n    if(observer.instrument){params.cb_eval=prefill_observer::callback;params.cb_eval_user_data=&observer;}\n    // max number of parallel drafting sequences')
s=replace(s,'    auto llama_init_tgt = common_init_from_params(params);',
    '    const auto continuation_cp=common_context_params_to_llama(params);\n    auto target_prefill_params=params;target_prefill_params.n_ubatch=observer.prefill_ub;\n    auto llama_init_tgt = common_init_from_params(target_prefill_params);')
s=replace(s,'    inp = common_tokenize(ctx_tgt, params.prompt, true, true);',
    '    if(const char * p=std::getenv("HS_MECHANISM_INPUT_IDS")){std::ifstream f(p);pj j;f>>j;inp=j.get<std::vector<llama_token>>();}\n    else inp = common_tokenize(ctx_tgt, params.prompt, true, true);')
s=replace(s,'    // eval the prompt with both models','    observer.phase="prefill";\n    // eval the prompt with both models')
s=replace(s,'    // the 2 models should have the same vocab','    observer.phase="continuation";\n    // the 2 models should have the same vocab')
s=replace(s,'    heterospec_direct_ids hs_direct_ids;',
    '    int pending=-1;pj pending_scores;\n    if(std::getenv("HS_NO_TRANSFER")==nullptr){\n      pending_scores=observer.top(ctx_tgt,0);pending=common_sampler_sample(smpl,ctx_tgt,0);\n      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());mem_tgt=llama_get_memory(ctx_tgt);}\n    heterospec_direct_ids hs_direct_ids;')
s=replace(s,'                    token_id = common_sampler_sample(smpl, ctx_tgt, drafts[s_keep].i_batch_tgt[i_dft]);',
    '                    const int hs_idx=drafts[s_keep].i_batch_tgt[i_dft];\n                    const auto hs_scores=pending>=0?pending_scores:observer.top(ctx_tgt,hs_idx);\n                    token_id = pending>=0?pending:common_sampler_sample(smpl,ctx_tgt,hs_idx);\n                    pending=-1;')
# Record the selected logit row before accept/correct mutates the loop index.
s=replace(s,'                bool accept = false;','                bool accept = false;\n                const int hs_logit_idx=drafts[s_keep].i_batch_tgt[i_dft];\n                const auto hs_score=pending>=0?pending_scores:observer.top(ctx_tgt,hs_logit_idx);\n                const int hs_proposal=drafts[s_keep].active && i_dft<(int)drafts[s_keep].tokens.size()?drafts[s_keep].tokens[i_dft]:-1;')
s=replace(s,'                hs_direct_ids.commit(token_id, llama_vocab_is_eog(vocab_tgt, token_id));',
    '                hs_direct_ids.commit(token_id, llama_vocab_is_eog(vocab_tgt, token_id));\n                observer.commit(ctx_tgt,token_id,llama_vocab_is_eog(vocab_tgt,token_id),accept,hs_proposal,hs_logit_idx,hs_score);')
# Keep the native loop and its legacy raw overshoot unchanged. Endpoint normalization is external.
import re
s=re.sub(r'llama_decode\(ctx_tgt,\s*(.*?)\);',r'observer.decode(ctx_tgt,\1,"target");',s)
s=re.sub(r'llama_decode\(ctx_dft,\s*(.*?)\);',r'observer.decode(ctx_dft,\1,"draft");',s)
for op in ('rm','cp','keep'):
    pattern=r'llama_memory_seq_'+op+r'\s*\((mem_(?:tgt|dft)),\s*(.*?)\);'
    def mut(m,op=op):
        args=[a.strip() for a in m[2].split(',')]
        role='target' if m[1]=='mem_tgt' else 'draft'
        fields=args if op=='cp' else [args[0],'-1',*args[1:]] if op=='rm' else [args[0],'-1','-1','-1']
        return 'observer.role="'+role+'";observer.mutation("'+op+'",'+m[1]+','+','.join(fields)+');'+m[0]
    s=re.sub(pattern,mut,s)
s=replace(s,'    if (!hs_direct_ids.write()) { return 2; }','    observer.finish(hs_direct_ids.ids,hs_direct_ids.eog,inp);\n    if (!hs_direct_ids.write()) { return 2; }')
(HERE/'native.cpp').write_text(s,newline='\n')
cm=(ROOT/'scripts/platform/b570_mechanism_v08/CMakeLists.txt').read_text()
cm=cm.replace('add_executable(heterospec-mechanism harness.cpp)','add_executable(heterospec-mechanism target.cpp)\nadd_executable(heterospec-prefill-native native.cpp)')
cm+='\ntarget_compile_features(heterospec-prefill-native PRIVATE cxx_std_17)\n'
for prop in ('COMPILE_DEFINITIONS','INCLUDE_DIRECTORIES','LINK_LIBRARIES'):
    cm+=f'get_target_property(shared_{prop} heterospec-mechanism {prop})\nset_target_properties(heterospec-prefill-native PROPERTIES {prop} "${{shared_{prop}}}")\n'
(HERE/'CMakeLists.txt').write_text(cm,newline='\n')
