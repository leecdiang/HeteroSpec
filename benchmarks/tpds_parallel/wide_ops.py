"""Scoped lowering for quantized projections and graph storage, applied after PR166."""
from pathlib import Path

def apply(src: Path):
    graph=src/"src/llama-graph.cpp"
    text=graph.read_text(encoding="utf8")
    key="    ggml_tensor * res = ggml_mul_mat(ctx0, w, cur);"
    assert text.count(key)==1
    text=text.replace(key, """    ggml_tensor * res = nullptr;
    if (hs_query_batch && w->type == GGML_TYPE_Q8_0 && cur->type == GGML_TYPE_F32 &&
        cur->ne[1] > 4 && cur->ne[1] <= 32 && cur->ne[2] == 1 && cur->ne[3] == 1) {
        // A wide MM dispatch is a different numerical operation on this backend.
        // Preserve four-column parallel matmuls across the physical KV cut.
        for (int64_t i = 0; i < cur->ne[1]; i += 4) {
            const int64_t rows = std::min<int64_t>(4, cur->ne[1] - i);
            auto * x = ggml_view_2d(ctx0, cur, cur->ne[0], rows, cur->nb[1], i*cur->nb[1]);
            auto * block = ggml_mul_mat(ctx0, w, x);
            ggml_format_name(block, "tpds_projection_%s_%lld", w->name, (long long)i);
            res = res ? ggml_concat(ctx0, res, block, 1) : block;
        }
    } else {
        res = ggml_mul_mat(ctx0, w, cur);
    }""")
    graph.write_text(text,encoding="utf8")
    ctx=src/"src/llama-context.cpp"
    text=ctx.read_text(encoding="utf8")
    key="    res += n_sampling_nodes;"
    assert text.count(key)==1
    ctx.write_text(text.replace(key,"""    // Each PQ row adds views, softmax and output nodes in every layer.
    // Size the arena before the scheduler reserves its synthetic graph.
    if (cparams.n_ubatch > 4 && cparams.n_ubatch <= 32) {
        res += 32 * cparams.n_ubatch * model.hparams.n_layer();
    }
"""+key),encoding="utf8")

