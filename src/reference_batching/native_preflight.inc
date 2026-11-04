// Compiled inside llama's graph translation unit, not in the host executable.
#include "llama-context.h"
extern "C" HS_GATE_API bool hs_native_decode_supported(llama_context * ctx,llama_batch batch) noexcept {
    if(!ctx || hs_scope::active || hs_reference_batching::hs_get_packing_binding())return false;
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
