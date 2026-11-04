"""Make known experimental graph applicability failures catchable when bound.
Generic ggml assertions and unbound legacy behavior remain unchanged.
Run on a staged tree, never on the frozen input source.
"""
from pathlib import Path

def harden(text):
    sections=[
        ('    if (hs_query_batch && hs_scope::layout95()==1 && q->ne[2] > 1) {','    const bool v_trans =',4),
        ('    if (hs_query_batch && hs_scope::layout95()==0 && q->ne[1] > 1 && arch == LLM_ARCH_LLAMA) {','    ggml_tensor * cur;',10),
        ('    if (grouped) {','    cb(cur, "kqv_out", il);',2),
    ]
    for begin,end,count in sections:
        if text.count(begin)!=1:raise ValueError('native applicability anchor mismatch')
        a=text.index(begin);b=text.index(end,a);part=text[a:b]
        if part.count('GGML_ASSERT(')!=count:raise ValueError('native applicability assertion count changed')
        text=text[:a]+part.replace('GGML_ASSERT(','HS_CONTRACT_REQUIRE(')+text[b:]
    prefix='''#define HS_CONTRACT_REQUIRE(expr) do { \\
    if (hs_reference_batching::hs_get_packing_binding() && !(expr)) \\
        throw std::runtime_error("unsupported native graph: " #expr); \\
    GGML_ASSERT(expr); \\
} while (0)
'''
    return prefix+text
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('graph',type=Path);a=p.parse_args()
    a.graph.write_text(harden(a.graph.read_text()))
