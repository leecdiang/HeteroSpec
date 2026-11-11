#pragma once
// Instrumentation only. The linked numerical archives remain the qualified
// Linux successor's exact archives. No arithmetic or transaction is replaced.
#include "llama-context.h"
#ifndef M1_PROJECTION
#error Explicit projection/core binding required
#endif
static json m1_structure(llama_model* m) {
    return {{"layers",m->hparams.n_layer()},{"query_heads",m->hparams.n_head()},
        {"kv_heads",m->hparams.n_head_kv()},{"head_k",m->hparams.n_embd_head_k()},
        {"head_v",m->hparams.n_embd_head_v()},{"K_elements",m->hparams.n_embd_k_gqa()},
        {"V_elements",m->hparams.n_embd_v_gqa()}};
}
static json m1_context(Context& x) {
    const auto& p=x.c->get_cparams();
    auto* cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(x.c));
    need(cache,"M1 dense cache required");
    return {{"n_ctx",llama_n_ctx(x.c)},{"n_batch",llama_n_batch(x.c)},
        {"n_ubatch",llama_n_ubatch(x.c)},{"outputs_max",p.n_outputs_max},
        {"outputs_per_seq",p.n_outputs_max_per_seq},{"flash_attention",p.flash_attn},
        {"type_k",ggml_type_name(cache->type_k())},{"type_v",ggml_type_name(cache->type_v())}};
}
static json m1_placement(llama_model* m) {
    json layers=json::array();
    for(int i=0;i<int(m->hparams.n_layer());++i) {
        auto dev=m->dev_layer(i);need(dev && ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"M1 layer must be GPU placed");
        layers.push_back(ggml_backend_dev_description(dev));
    }
    auto out=m->dev_output();need(out && ggml_backend_dev_type(out)==GGML_BACKEND_DEVICE_TYPE_GPU,"M1 output must be GPU placed");
    return {{"layers",layers},{"output",ggml_backend_dev_description(out)}};
}
static void m1_capability(const json& job,Pair& pool,llama_model* t,llama_model* d,const ArmSpec& spec,const fs::path& root,json& result) {
    const std::vector<std::string> keys={"family","target_model","target_sha256","draft_model","draft_sha256","n_ctx","threads","lowering","draft_width","draft","residency","profile","inputs","cases","forced","observe_positions","state_positions","capability_request"};
    for(auto it=job.begin();it!=job.end();++it)need(std::find(keys.begin(),keys.end(),it.key())!=keys.end(),"Unknown M1 native job field");
    need(job.at("n_ctx")==llama_n_ctx(pool.target->c),"Ignored context request");
    need(d && pool.draft && spec.draft && spec.k==3 && phase_draft_width==4,"M1 is fixed k3/D4 only");
    need(!job.value("profile",false),"No event profiling in M1");
    const auto target_hash=hash_file(job.at("target_model").get<std::string>());
    const auto draft_hash=hash_file(job.at("draft_model").get<std::string>());
    need(target_hash==job.at("target_sha256") && draft_hash==job.at("draft_sha256"),"Native model hash mismatch");
    json echo={{"schema","heterospec.m1.native-capability.v1"},{"target_sha256",target_hash},{"draft_sha256",draft_hash},
        {"target_structure",m1_structure(t)},{"draft_structure",m1_structure(d)},
        {"target_context",m1_context(*pool.target)},{"draft_context",m1_context(*pool.draft)},
        {"target_placement",m1_placement(t)},{"draft_placement",m1_placement(d)},
        {"k",spec.k},{"draft_width",phase_draft_width},{"cut",phase_lowering},{"projection",M1_PROJECTION},
        {"threads",phase_threads},{"greedy",true},{"target_output_policy","PREFILL:last;VERIFY:all_original_rows"},
        {"draft_output_policy","last"},{"physical_rows_evidence","per-request executions and native physical width histograms"}};
    dump(root/"CAPABILITY.json",echo);
    need(echo==job.at("capability_request"),"Native capability differs from complete requested contract");
    result["native_capability"]=echo;
}
