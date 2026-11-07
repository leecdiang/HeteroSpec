"""Opt-in Qwen3/FA-off graph experiment; unchanged external CUDA backend."""
from pathlib import Path

PATCH='''    if (std::getenv("HS_ATTENTION_SINGLE_QUERY") && q->ne[2] > 1) {
        GGML_ASSERT(arch == LLM_ARCH_QWEN3 && !cparams.flash_attn);
        GGML_ASSERT(q->ne[2] == 2 && k->ne[3] == 1);
        GGML_ASSERT(kq_b == nullptr && sinks == nullptr && v_mla == nullptr);
        GGML_ASSERT(kq_mask && kq_mask->ne[2] == 1 && kq_mask->ne[3] == 1);
        ggml_tensor * joined = nullptr;
        for (int64_t i = 0; i < q->ne[2]; ++i) {
            auto * qi = ggml_view_3d(ctx0, q, q->ne[0], q->ne[1], 1, q->nb[1], q->nb[2], i*q->nb[2]);
            auto * mi = ggml_view_2d(ctx0, kq_mask, kq_mask->ne[0], 1, kq_mask->nb[1], i*kq_mask->nb[1]);
            auto * ci = build_attn_mha(qi, k, v, nullptr, mi, nullptr, nullptr, n_kv_max, kq_scale, il);
            cb(ci, "hs_attn_single_query", il);
            joined = joined ? ggml_concat(ctx0, joined, ci, 1) : ci;
        }
        ggml_build_forward_expand(gf, joined);
        return joined;
    }

'''

def apply(src,max_queries=2):
    assert max_queries in [2,4]
    p=src/'src/llama-graph.cpp';s=p.read_text(encoding='utf-8')
    marker='HS_ATTENTION_SINGLE_QUERY'
    if marker not in s:
        start=s.index('ggml_tensor * llm_graph_context::build_attn_mha(')
        pos=s.index('    const bool v_trans = v->nb[1] > v->nb[2];',start)
        s=s[:pos]+PATCH+s[pos:]
    old='GGML_ASSERT(q->ne[2] == 2 && k->ne[3] == 1);'
    wide='GGML_ASSERT(q->ne[2] <= 4 && k->ne[3] == 1);'
    assert s.count(old)+s.count(wide)==1
    s=s.replace(wide if max_queries==2 else old,old if max_queries==2 else wide)
    p.write_text(s,encoding='utf-8',newline='\n')
    p=src/'common/hs_observer.h';s=p.read_text(encoding='utf-8')
    a='std::strcmp(t->name,"attn_norm-0")==0))'
    b='std::strcmp(t->name,"attn_norm-0")==0||std::strcmp(t->name,"hs_attn_single_query-0")==0))'
    if 'std::strcmp(t->name,"hs_attn_single_query-0")' not in s:
        assert s.count(a)==1;s=s.replace(a,b);p.write_text(s,encoding='utf-8',newline='\n')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--max-queries',type=int,choices=[2,4],default=2)
    apply(Path(__file__).resolve().parent/'generated/source',p.parse_args().max_queries)
