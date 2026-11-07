"""Bind the logical ordering guard to reuse and expose physical allocator evidence."""
from pathlib import Path
import sys
from map_vulkan import replace

def apply(root):
    kv=root/'src/llama-kv-cache.cpp'
    s=kv.read_text(encoding='utf-8')
    s=replace(s,'    return hs_reference_batching::scalar_prefix_requirements(state).extents;',r'''
    auto requirements=hs_reference_batching::scalar_prefix_requirements(state);
    if (state.rows>1 && std::getenv("HS_TRANSFER_TRACE")) {
        std::fprintf(stderr,"HS_CACHE head=%u rows=%u used=%u occupied_end=%u capacity=%u padding=%u streams=%u dense=%d status=%d\n",
            state.head,state.rows,state.used,state.occupied_end,state.capacity,state.padding,state.streams,
            int(state.contiguous),int(requirements.status));
    }
    return requirements.extents;''')
    kv.write_text(s,encoding='utf-8',newline='\n')
    header=root/'src/llama-graph.h'
    s=replace(header.read_text(encoding='utf-8'),'    hs_reference_batching::PolicyIdentity reference_policy;',
              '    hs_reference_batching::PolicyIdentity reference_policy;\n    bool reference_ordered_append = false;')
    header.write_text(s,encoding='utf-8',newline='\n')
    graph=root/'src/llama-graph.cpp';s=graph.read_text(encoding='utf-8')
    s=replace(s,'hs_b570::reference_q8, false, 2','hs_b570::reference_q8, false, 3')
    s=replace(s,'bool llm_graph_input_attn_kv::can_reuse(',r'''static bool hs_ordered_append(const llama_ubatch & batch) {
    if (!batch.pos || batch.n_seqs_unq != 1) return false;
    for (uint32_t row=1; row<batch.n_tokens; ++row) {
        if (batch.pos[row] != batch.pos[0]+int(row)) return false;
    }
    return true;
}

bool llm_graph_input_attn_kv::can_reuse(''')
    s=replace(s,'    if (reference_policy!=hs_reference_policy_identity()) {','''    if (reference_policy!=hs_reference_policy_identity() ||
        (reference_policy.prefix && reference_ordered_append!=hs_ordered_append(params.ubatch))) {''')
    s=replace(s,'    inp->reference_policy=hs_reference_policy_identity();','    inp->reference_policy=hs_reference_policy_identity();\n    inp->reference_ordered_append=hs_ordered_append(ubatch);')
    s=replace(s,'    bool ordered=ubatch.pos && ubatch.n_seqs_unq==1;\n    for (uint32_t row=1;ordered && row<ubatch.n_tokens;++row) ordered=ubatch.pos[row]==ubatch.pos[0]+int(row);','    const bool ordered=inp->reference_ordered_append;')
    graph.write_text(s,encoding='utf-8',newline='\n')
    vk=root/'ggml/src/ggml-vulkan/ggml-vulkan.cpp';s=vk.read_text(encoding='utf-8')
    s=replace(s,'if (selected && std::getenv("HS_TRANSFER_TRACE") && ne11 > 1)', 'if (src0->type==GGML_TYPE_Q8_0 && std::getenv("HS_TRANSFER_TRACE") && ne11 > 1)')
    s=replace(s,'int(requirement == ProjectionAction::retain_f32_batch)', 'int(selected && requirement == ProjectionAction::retain_f32_batch)')
    vk.write_text(s,encoding='utf-8',newline='\n')
if __name__=='__main__':apply(Path(sys.argv[1]))

