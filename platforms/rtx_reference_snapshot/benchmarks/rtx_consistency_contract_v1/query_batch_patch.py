"""Keep scalar-query reduction columns while parallelizing over batch axes."""
from pathlib import Path

PATCH='''    if (std::getenv("HS_ATTENTION_QUERY_BATCH") && q->ne[1] > 1) {
        GGML_ASSERT(arch == LLM_ARCH_QWEN3 && !cparams.flash_attn);
        GGML_ASSERT(q->ne[1] <= 4 && q->ne[3] == 1 && k->ne[3] == 1);
        GGML_ASSERT(kq_b == nullptr && sinks == nullptr && v_mla == nullptr);
        GGML_ASSERT(kq_mask && kq_mask->ne[2] == 1 && kq_mask->ne[3] == 1);
        const int64_t queries = q->ne[1];
        q = ggml_view_4d(ctx0, q, q->ne[0], 1, q->ne[2], queries, q->nb[1], q->nb[2], q->nb[1], 0);
        kq_mask = ggml_view_4d(ctx0, kq_mask, kq_mask->ne[0], 1, 1, queries,
                kq_mask->nb[1], kq_mask->nb[1], kq_mask->nb[1], 0);
        cb(q, "hs_attn_query_batch", il);
    }

'''

def apply(src):
    p=src/'src/llama-graph.cpp';s=p.read_text(encoding='utf-8')
    if 'HS_ATTENTION_QUERY_BATCH' not in s:
        start=s.index('ggml_tensor * llm_graph_context::build_attn_mha(')
        needle='    v = ggml_permute(ctx0, v, 0, 2, 1, 3);\n\n'
        pos=s.index(needle,start)+len(needle);s=s[:pos]+PATCH+s[pos:]
        p.write_text(s,encoding='utf-8',newline='\n')
    p=src/'common/hs_observer.h';s=p.read_text(encoding='utf-8')
    a='std::strcmp(t->name,"hs_attn_single_query-0")==0))'
    b='std::strcmp(t->name,"hs_attn_single_query-0")==0||std::strcmp(t->name,"hs_attn_query_batch-0")==0))'
    if b not in s:
        assert s.count(a)==1;s=s.replace(a,b);p.write_text(s,encoding='utf-8',newline='\n')
if __name__=='__main__':apply(Path(__file__).resolve().parent/'generated/source')
