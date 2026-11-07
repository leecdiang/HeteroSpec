"""Install CUDA requirements in a freshly staged, already source-bound candidate."""
from pathlib import Path
import argparse
import shutil


def replace(path, before, after):
    source = path.read_text(encoding="utf-8")
    if source.count(before) != 1:
        raise ValueError(f"unexpected source anchor in {path}: {before}")
    path.write_text(source.replace(before, after), encoding="utf-8", newline="\n")


def install(tree):
    backend = tree / "ggml/src/ggml-backend.cpp"
    graph = tree / "src/llama-graph.cpp"
    replace(backend, '#include "repair_offload.hpp"', '#include <unordered_set>\n#include "repair_offload.hpp"')
    replace(backend, 'ggml_backend_sched_backend_id_from_cur(ggml_backend_sched_t sched, struct ggml_tensor * tensor)', 'ggml_backend_sched_backend_id_from_cur(ggml_backend_sched_t sched, struct ggml_tensor * tensor, bool feeds_rope)')
    replace(backend, 'graph->uid = ggml_graph_next_uid();', '''graph->uid = ggml_graph_next_uid();
    std::unordered_set<const ggml_tensor *> rotary_inputs;
    if (hs_scope::active) {
        for (int i = 0; i < graph->n_nodes; ++i) {
            const auto * node = graph->nodes[i];
            if (node->op == GGML_OP_ROPE) rotary_inputs.insert(node->src[0]);
        }
    }''')
    for var in ("leaf", "node", "src"):
        replace(backend, f"ggml_backend_sched_backend_id_from_cur(sched, {var})", f"ggml_backend_sched_backend_id_from_cur(sched, {var}, rotary_inputs.count({var}) != 0)")
    replace(backend, "offload_op(sched->backends[b], tensor)", "offload_op(sched->backends[b], tensor, feeds_rope)")
    offload = tree / "ggml/src/repair_offload.hpp"
    offload.write_text('''#pragma once
#include "../../src/hs_reference_batching.hpp"
#include <cstdio>
#include <cstdlib>
namespace hs_repair_offload {
template<class Backend, class Tensor>
inline bool offload_op(Backend backend, const Tensor * tensor, bool feeds_rope) {
    const bool batch = ggml_backend_offload_op(backend, tensor);
    const auto * norm = tensor->src[0];
    const auto * weight = tensor->src[1];
    const bool head_scale = feeds_rope && tensor->op == GGML_OP_MUL &&
        norm && norm->op == GGML_OP_RMS_NORM && weight &&
        weight->ne[0] == tensor->ne[0] && weight->ne[1] == 1 &&
        weight->ne[2] == 1 && weight->ne[3] == 1 && tensor->ne[3] == 1;
    if (!hs_scope::active || !head_scale || tensor->ne[2] <= 1 || tensor->ne[2] > 4) return batch;
    auto one = *tensor;
    one.ne[2] = 1;
    const bool scalar = ggml_backend_offload_op(backend, &one);
    const bool selected = hs_reference_batching::use_scalar_head_preference(
        hs_scope::active, head_scale, tensor->ne[2], scalar, batch);
    if (std::getenv("HS_RTX164_TRACE")) {
        std::fprintf(stderr,"RTX164_HEAD %s %s heads=%lld rows=%lld scalar=%d batch=%d selected=%d\\n",
            tensor->name, ggml_backend_name(backend), (long long)tensor->ne[1],
            (long long)tensor->ne[2], scalar, batch, selected);
    }
    return selected;
}
}
''', encoding="utf-8")
    replace(graph, "const auto groups=hs_reference_batching::partition_adjacent(prefix);", '''const uint64_t arithmetic = 1 + uint64_t(q->type) + (uint64_t(k->type) << 8) + (uint64_t(v->type) << 16);
        GGML_ASSERT(q->ne[0] <= 65535 && q->ne[1] <= 65535 && k->ne[1] <= 65535);
        const uint64_t dispatch = uint64_t(q->ne[0]) | (uint64_t(q->ne[1]) << 16) |
                                  (uint64_t(k->ne[1]) << 32) | (uint64_t(transposed) << 48);
        const auto groups=hs_reference_batching::partition_adjacent(prefix, arithmetic, dispatch);''')
    replace(graph, "ggml_tensor * cur=nullptr;\n    if (grouped)", '''if (hs_query_batch && std::getenv("HS_RTX164_TRACE") && !prefix.empty()) {
        std::fprintf(stderr,"RTX164_ATTN layer=%d heads=%lld kv_heads=%lld rows=%lld first=%u last=%u split=%d position=%d\\n",
            il,(long long)q->ne[1],(long long)k->ne[1],(long long)q->ne[2],prefix.front(),prefix.back(),grouped,ubatch.pos ? int(ubatch.pos[0]) : -1);
    }
    ggml_tensor * cur=nullptr;
    if (grouped)''')
    replace(graph, "void llm_graph_result::reset() {", """void llm_graph_result::reset() {
    rotary_head_scales.clear();
    head_placement_key.clear();""")
    header = tree / "src/llama-graph.h"
    replace(header, "    void set_outputs(const llm_graph_params & params);", '''    void set_outputs(const llm_graph_params & params);
    std::vector<const ggml_tensor *> rotary_head_scales;
    std::vector<int64_t> head_placement_key;
    std::vector<int64_t> current_head_placement_key(const llm_graph_params & params) const;''')
    replace(graph, "void llm_graph_result::set_outputs(const llm_graph_params & params) {", '''std::vector<int64_t> llm_graph_result::current_head_placement_key(const llm_graph_params & params) const {
    std::vector<int64_t> key;
    for (auto * t : rotary_head_scales) {
        key.insert(key.end(), {t->ne[0], t->ne[1], t->ne[2], t->type, t->src[1]->type});
        const bool host = t->src[1]->buffer && ggml_backend_buffer_is_host(t->src[1]->buffer);
        key.push_back(host);
        if (!host || !hs_scope::active || t->ne[2] <= 1 || t->ne[2] > 4) continue;
        auto one = *t;
        one.ne[2] = 1;
        for (int i = 0; i + 1 < ggml_backend_sched_get_n_backends(params.sched); ++i) {
            auto b = ggml_backend_sched_get_backend(params.sched, i);
            if (!ggml_backend_supports_op(b, t)) { key.push_back(-1); continue; }
            const bool scalar = ggml_backend_offload_op(b, &one);
            const bool batch = ggml_backend_offload_op(b, t);
            const bool selected = hs_reference_batching::use_scalar_head_preference(true, true, t->ne[2], scalar, batch);
            key.push_back((scalar << 2) | (batch << 1) | selected);
        }
    }
    return key;
}

void llm_graph_result::set_outputs(const llm_graph_params & params) {
    rotary_head_scales.clear();
    for (int i = 0; i < ggml_graph_n_nodes(gf); ++i) {
        const auto * rope = ggml_graph_node(gf, i);
        if (rope->op != GGML_OP_ROPE) continue;
        const auto * t = rope->src[0];
        if (t && t->op == GGML_OP_MUL && t->src[0] && t->src[0]->op == GGML_OP_RMS_NORM &&
            t->src[1] && t->src[1]->ne[0] == t->ne[0] && ggml_is_vector(t->src[1]) && t->ne[3] == 1)
            rotary_head_scales.push_back(t);
    }
    head_placement_key = current_head_placement_key(params);
    if (std::getenv("HS_RTX164_TRACE") && !head_placement_key.empty()) {
        std::fprintf(stderr,"RTX164_CACHE_BUILD layout=%d active=%d head_scale_nodes=%zu placement_key=",
            hs_scope::layout95(),hs_scope::active,rotary_head_scales.size());
        for (auto x : head_placement_key) std::fprintf(stderr,"%lld,", (long long)x);
        std::fputc(10, stderr);
    }''')
    replace(graph, "bool llm_graph_result::can_reuse(const llm_graph_params & params) {", '''bool llm_graph_result::can_reuse(const llm_graph_params & params) {
    if (head_placement_key != current_head_placement_key(params)) return false;''')
    shutil.copyfile(Path(__file__).with_name("reference_batching.hpp"), tree / "src/hs_reference_batching.hpp")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path)
    install(parser.parse_args().tree)
