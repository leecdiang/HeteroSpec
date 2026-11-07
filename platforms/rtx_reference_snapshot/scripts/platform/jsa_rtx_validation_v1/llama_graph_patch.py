"""Port the query-axis recipe to the actual Llama GQA graph, with shape guards."""
from pathlib import Path
def patch(source):
    p=Path(source)/'src/llama-graph.cpp';text=p.read_text(encoding='utf-8')
    anchor='''    if (hs_query_batch && q->ne[1] > 1) {
        GGML_ASSERT(arch == LLM_ARCH_QWEN3 && !cparams.flash_attn);'''
    # Preserve the historical Qwen block. Llama has its own guarded branch.
    new='''    if (hs_query_batch && q->ne[1] > 1 && arch == LLM_ARCH_LLAMA) {
        GGML_ASSERT(!cparams.flash_attn && hparams.n_expert == 0);
        GGML_ASSERT(q->ne[1] <= 4 && q->ne[3] == 1 && k->ne[3] == 1);
        GGML_ASSERT(q->ne[0] == k->ne[0] && q->ne[2] % k->ne[2] == 0);
        GGML_ASSERT(kq_b == nullptr && sinks == nullptr && v_mla == nullptr);
        GGML_ASSERT(kq_mask && kq_mask->ne[2] == 1 && kq_mask->ne[3] == 1);
        GGML_ASSERT(kq_mask->ne[1] >= q->ne[1]);
        const int64_t queries = q->ne[1];
        q = ggml_view_4d(ctx0, q, q->ne[0], 1, q->ne[2], queries,
                q->nb[1], q->nb[2], q->nb[1], 0);
        kq_mask = ggml_view_4d(ctx0, kq_mask, kq_mask->ne[0], 1, 1, queries,
                kq_mask->nb[1], kq_mask->nb[1], kq_mask->nb[1], 0);
        cb(q, "hs_attn_query_batch", il);
        cb(q, "jsa_llama_query_batch", il);
    } else if (hs_query_batch && q->ne[1] > 1) {
        GGML_ASSERT(arch == LLM_ARCH_QWEN3 && !cparams.flash_attn);'''
    assert text.count(anchor)==1;p.write_text(text.replace(anchor,new),encoding='utf-8',newline='\n')
    p=Path(source)/'common/hs_observer.h';text=p.read_text(encoding='utf-8');anchor='std::strcmp(t->name,"hs_attn_query_batch-0")==0'
    assert text.count(anchor)==1;p.write_text(text.replace(anchor,anchor+'||std::strcmp(t->name,"jsa_llama_query_batch-0")==0'),encoding='utf-8',newline='\n')
