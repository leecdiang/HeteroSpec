"""Apply native mapping to a freshly staged PR164 Vulkan source."""
from pathlib import Path
import argparse

def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError("unexpected source anchor: " + old[:80])
    return text.replace(old, new, 1)

def apply(root):
    vk = root / 'ggml/src/ggml-vulkan/ggml-vulkan.cpp'
    graph = root / 'src/llama-graph.cpp'
    s = vk.read_text(encoding="utf-8")
    start = s.index('    const bool reference_q8 = ')
    end = s.index('    vk_pipeline to_fp16_vk_0', start)
    s = '#include "../../../src/hs_reference_batching.hpp"\n' + s[:start] + r'''
    using namespace hs_reference_batching;
    const bool eligible = ctx->device->integer_dot_product && src1->type == GGML_TYPE_F32 &&
        ggml_is_contiguous(src1) && !y_non_contig;
    const bool scalar_quant = eligible && ne10 % 4 == 0 &&
        ggml_vk_should_use_mmvq(ctx->device, ne01, 1, ne10, src0->type);
    const bool batch_quant = eligible && (ne11 * ne10) % 4 == 0 &&
        ggml_vk_should_use_mmvq(ctx->device, ne01, ne11, ne10, src0->type);
    const bool selected = dst->op_params[0] == GGML_PREC_F32;
    const auto requirement = projection_requirement(src0->type == GGML_TYPE_Q8_0,
        src1->type == GGML_TYPE_F32,
        scalar_quant ? ActivationPath::q8_1 : ActivationPath::f32,
        batch_quant ? ActivationPath::q8_1 : ActivationPath::f32,
        f16_f32_kernel && !x_non_contig && !y_non_contig);
    bool quantize_y = batch_quant && !(selected && requirement == ProjectionAction::retain_f32_batch);

''' + s[end:]
    point = s.index('    GGML_ASSERT(dmmv != nullptr);', start)
    point = s.index('\n', point)
    s = s[:point] + r'''
    if (selected && std::getenv("HS_TRANSFER_TRACE") && ne11 > 1) {
        std::fprintf(stderr, "HS_PROJECTION op=%s wtype=%d xtype=%d k=%llu m=%llu rows=%llu nb0=%zu nb1=%zu scalar_quant=%d batch_quant=%d retain_f32=%d selected_quant=%d pipeline=%s\n",
            src0->name, int(src0->type), int(src1->type), (unsigned long long)ne10,
            (unsigned long long)ne01, (unsigned long long)ne11, src1->nb[0], src1->nb[1],
            int(scalar_quant), int(batch_quant), int(requirement == ProjectionAction::retain_f32_batch),
            int(quantize_y), dmmv->name.c_str());
    }
''' + s[point:]
    g = graph.read_text(encoding="utf-8")
    g = replace(g,"hs_b570::reference_q8, false, 1","hs_b570::reference_q8, false, 2")
    g = replace(g,'    const bool grouped=hs_b570::prefix_extent',r'''
    // Capture the scalar attention contract from the actual graph operands.
    // Layout/strides are fixed within one graph; physical extent is row-specific.
    const auto descriptor=[](std::initializer_list<uint64_t> fields) {
        uint64_t id=1469598103934665603ULL;
        for (auto value : fields) { id ^= value; id *= 1099511628211ULL; }
        return id;
    };
    const uint64_t arithmetic=descriptor({uint64_t(q->type), uint64_t(k->type), uint64_t(v->type),
        uint64_t(q->ne[0]), uint64_t(q->ne[1]), uint64_t(k->ne[1])});
    const uint64_t dispatch=descriptor({uint64_t(hs_b570::mode), q->nb[1], q->nb[2],
        k->nb[1], k->nb[2], v->nb[1], v->nb[2]});
    const auto groups=hs_reference_batching::partition_adjacent(prefix,arithmetic,dispatch);
    const bool grouped=hs_b570::prefix_extent''')
    g = replace(g,'prefix.front()!=prefix.back()','groups.size()>1')
    g = replace(g,'        const auto groups=hs_reference_batching::partition_adjacent(prefix);','')
    g = replace(g,'    if (grouped) {',r'''
    if (il==0 && hs_b570::mode && q->ne[2]>1 && std::getenv("HS_TRANSFER_TRACE")) {
        std::fprintf(stderr,"HS_ATTENTION pos=%d rows=%lld heads=%lld kvheads=%lld dim=%lld layout=%d arith=%llu dispatch=%llu grouped=%d extents=",
            ubatch.pos ? ubatch.pos[0] : -1,(long long)q->ne[2],(long long)q->ne[1],
            (long long)k->ne[1],(long long)q->ne[0],hs_b570::mode,
            (unsigned long long)arithmetic,(unsigned long long)dispatch,int(grouped));
        for(auto extent:prefix) std::fprintf(stderr,"%u,",extent);
        std::fprintf(stderr,"\n");
    }
    if (grouped) {''')
    g = replace(g,'    if (reference_policy!=hs_reference_policy_identity()) return false;',r'''    if (reference_policy!=hs_reference_policy_identity()) {
        if(std::getenv("HS_TRANSFER_TRACE")) std::fprintf(stderr,"HS_REUSE rejected=policy\n");
        return false;
    }''')
    g = replace(g,'std::vector<uint32_t>{})) return false;',r'''std::vector<uint32_t>{})) {
        if(std::getenv("HS_TRANSFER_TRACE")) std::fprintf(stderr,"HS_REUSE rejected=extent\n");
        return false;
    }''')
    vk.write_text(s,encoding="utf-8",newline="\n")
    graph.write_text(g,encoding="utf-8",newline="\n")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    apply(p.parse_args().source)

