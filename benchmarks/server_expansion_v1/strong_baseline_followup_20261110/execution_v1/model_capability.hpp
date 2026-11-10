#pragma once
#include "llama-context.h"
// Called after context creation and before the first registered model request.
static void m1_capability(const json& job,Pair& pool,llama_model* target,llama_model* draft,
                         const ArmSpec& spec,const fs::path& root,json& result){
    const std::set<std::string> keys={"family","target_model","target_sha256","n_ctx","threads","lowering",
        "draft_width","draft","residency","profile","inputs","cases","forced","observe_positions","state_positions",
        "capability_request","k","target_output_reserve","proposal_mode","cuda_graphs","arm","n_ubatch",
        "output_reserve","kv","flash_attention","capture_operands","operand_capture_classes","capacity_overflow_probe"};
    for(auto i=job.begin();i!=job.end();++i)need(keys.count(i.key()),"Unknown strong native job field");
    need(target&&!draft&&pool.target&&!pool.draft&&!spec.draft&&spec.k==0,"Actual M target-only residency");
    need(phase_lowering=="SIMPLE","WHOLE must retain the original W/SIMPLE planner");
    auto* ctx=pool.target->c;const auto& p=ctx->get_cparams();
    auto* cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx));need(cache,"Strong dense KV cache");
    need(llama_n_ctx(ctx)==1024&&llama_n_batch(ctx)==1024&&llama_n_ubatch(ctx)==32&&
         p.n_outputs_max==32&&p.n_outputs_max_per_seq==32&&!p.flash_attn&&
         cache->type_k()==GGML_TYPE_F16&&cache->type_v()==GGML_TYPE_F16,"Actual strong runtime parameters");
    int gpu_layers=0;
    for(int layer=0;layer<int(target->hparams.n_layer());++layer){
        auto* dev=target->dev_layer(layer);need(dev&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"Actual GPU layer");++gpu_layers;
    }
    auto* output=target->dev_output();need(output&&ggml_backend_dev_type(output)==GGML_BACKEND_DEVICE_TYPE_GPU,"Actual GPU output");
    need(target->tok_embd&&target->tok_embd->buffer,"Actual embedding buffer");
    const auto embedding_type=ggml_backend_buffer_get_type(target->tok_embd->buffer);
    auto* embedding=ggml_backend_buft_get_device(embedding_type);
    need(embedding,"Actual embedding device");
    const int selected=hs_strong_selected_arm();need(selected>=1&&selected<=3,"Actual selected implementation");
    const auto model_hash=hash_file(job.at("target_model").get<std::string>());
    need(model_hash==job.at("target_sha256"),"Actual model SHA-256");
    need(llama_vocab_n_tokens(llama_model_get_vocab(target))==151936,"Actual complete vocabulary");
    json echo={{"schema","hs.strong.runtime.v1"},{"arm",selected==1?"G":selected==2?"B":"C"},
        {"n_ctx",llama_n_ctx(ctx)},{"n_batch",llama_n_batch(ctx)},{"n_ubatch",llama_n_ubatch(ctx)},
        {"output_reserve",p.n_outputs_max},{"outputs_per_seq",p.n_outputs_max_per_seq},{"flash_attention",p.flash_attn},
        {"kv_K",ggml_type_name(cache->type_k())},{"kv_V",ggml_type_name(cache->type_v())},
        {"vocab",151936},{"layers",target->hparams.n_layer()},{"query_heads",target->hparams.n_head()},
        {"kv_heads",target->hparams.n_head_kv()},{"head_k",target->hparams.n_embd_head_k()},
        {"head_v",target->hparams.n_embd_head_v()},{"GPU_layers",gpu_layers},{"GPU_output",true},
        {"embedding_device_type",ggml_backend_dev_type(embedding)==GGML_BACKEND_DEVICE_TYPE_CPU?"CPU":"GPU"},
        {"target_sha256",model_hash},{"draft",false},{"k",0},{"threads",phase_threads},
        {"lowering","WHOLE"},{"native_planner",phase_lowering},{"cuda_graphs",false},{"greedy",true},{"requested_output_policy","PREFILL:last;VERIFY:all_original_rows"}};
    dump(root/"CAPABILITY.json",echo);
    need(echo==job.at("capability_request"),"Actual strong capability differs from frozen request");
    result["native_capability"]=echo;
    result["embedding_buffer_type"]=ggml_backend_buft_name(embedding_type);
}
