// Compiled inside llama's graph translation unit, not in the host executable.
#include "llama-context.h"
#include "ggml-cpu.h"
extern "C" HS_GATE_API bool hs_native_decode_supported(llama_context * ctx,llama_batch batch) noexcept {
    if(!ctx || hs_scope::active || hs_reference_batching::hs_get_packing_binding())return false;
    auto scheduler=ctx->get_sched();if(!scheduler)return false;
    for(int i=0;i<ggml_backend_sched_get_n_backends(scheduler);++i){
        auto backend=ggml_backend_sched_get_backend(scheduler,i);
        if(ggml_backend_is_cpu(backend))continue;
        auto device=ggml_backend_get_device(backend);
        auto cuda=ggml_backend_reg_by_name("CUDA");
        if(!device || !cuda || ggml_backend_dev_backend_reg(device)!=cuda ||
           !ggml_backend_reg_get_proc_address(cuda,"hs_cuda_exchange_audit_v1"))return false;
    }
    const auto & p=ctx->get_cparams();const auto & model=ctx->get_model();const auto & h=model.hparams;
    if(hs_scope::layout95()!=0 && hs_scope::layout95()!=1)return false;
    if(p.flash_attn || p.n_seq_max!=1 || !p.causal_attn || h.n_expert || h.n_swa)return false;
    if(model.arch!=LLM_ARCH_LLAMA && model.arch!=LLM_ARCH_QWEN3)return false;
    auto * memory=ctx->get_memory();
    if(!memory || typeid(*memory)!=typeid(llama_kv_cache))return false;
    if(batch.n_tokens<1 || batch.n_tokens>32 || uint32_t(batch.n_tokens)>p.n_batch || !batch.token || batch.embd ||
       !batch.pos || !batch.n_seq_id || !batch.seq_id || !batch.logits)return false;
    const auto previous=llama_memory_seq_pos_max(memory,0);
    if(previous>std::numeric_limits<llama_pos>::max()-batch.n_tokens)return false;
    for(int32_t i=0;i<batch.n_tokens;++i)
        if(batch.token[i]<0 || uint32_t(batch.token[i])>=model.vocab.n_tokens() || batch.pos[i]!=previous+1+i || batch.n_seq_id[i]!=1 || !batch.seq_id[i] ||
           batch.seq_id[i][0]!=0 || !batch.logits[i])return false;
    return true;
}
