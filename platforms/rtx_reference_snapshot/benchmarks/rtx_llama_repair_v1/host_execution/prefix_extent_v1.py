"""Group causal attention by scalar-equivalent physical KV prefix extent."""
import hashlib


def apply(source, code):
    changed = {}
    def edit(name, old, new):
        p = source/name
        text = p.read_text()
        assert text.count(old)==1, (name, old[:100], text.count(old))
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        p.write_text(text.replace(old,new),encoding='utf-8',newline='\n')
        changed.setdefault(name, {'before':before})['after']=hashlib.sha256(p.read_bytes()).hexdigest()
    edit('src/llama-kv-cache.h',
         '    uint32_t get_n_kv(const slot_info & sinfo) const;',
         '    uint32_t get_n_kv(const slot_info & sinfo) const;\n    std::vector<uint32_t> get_prefix_n_kv(const slot_info & sinfo) const;')
    edit('src/llama-kv-cache.h',
         '    uint32_t get_n_kv() const;',
         '    uint32_t get_n_kv() const;\n    std::vector<uint32_t> get_prefix_n_kv() const;')
    anchor='ggml_tensor * llama_kv_cache::get_k(ggml_context * ctx, int32_t il, uint32_t n_kv, const slot_info & sinfo) const {'
    implementation=r'''
std::vector<uint32_t> llama_kv_cache::get_prefix_n_kv(const slot_info & sinfo) const {
    if (n_swa || sinfo.empty() || sinfo.n_stream()!=1 || !sinfo.is_contiguous()) return {};
    const auto & cells=v_cells[sinfo.strm[0]];
    const auto head=sinfo.head();
    if (cells.get_used()!=cells.used_max_p1() || cells.used_max_p1()!=head+sinfo.size()) return {};
    const uint32_t padding=std::max(n_pad,256u);
    std::vector<uint32_t> result;
    for (uint32_t row=0;row<sinfo.size();++row) {
        result.push_back(std::min(cells.size(),std::max(padding,GGML_PAD(head+row+1,padding))));
    }
    return result;
}

'''
    edit('src/llama-kv-cache.cpp',anchor,implementation+anchor)
    anchor='ggml_type llama_kv_cache_context::type_k() const {'
    edit('src/llama-kv-cache.cpp',anchor,
         'std::vector<uint32_t> llama_kv_cache_context::get_prefix_n_kv() const {\n'
         '    return sinfos.empty() ? std::vector<uint32_t>{} : kv->get_prefix_n_kv(sinfos[i_cur]);\n}\n\n'+anchor)
    anchor='    ~llm_graph_input_attn_kv() = default;'
    edit('src/llama-graph.h',anchor,anchor+'\n    std::vector<uint32_t> prefix_n_kv;')
    anchor='    auto inp = std::make_unique<llm_graph_input_attn_kv>(hparams, cparams, mctx_cur);'
    edit('src/llama-graph.cpp',anchor,anchor+'\n    inp->prefix_n_kv=mctx_cur->get_prefix_n_kv();')
    anchor='''bool llm_graph_input_attn_kv::can_reuse(const llm_graph_params & params) {
    const auto * mctx = static_cast<const llama_kv_cache_context *>(params.mctx);'''
    edit('src/llama-graph.cpp',anchor,anchor+'\n    if (prefix_n_kv!=mctx->get_prefix_n_kv()) return false;')
    anchor='''    ggml_tensor * cur = build_attn_mha(q, k, v, kq_b, kq_mask, sinks, v_mla, 0, kq_scale, il);
    cb(cur, "kqv_out", il);'''
    # This anchor occurs in other attention variants; scope it to the KV overload.
    p=source/'src/llama-graph.cpp';text=p.read_text()
    start=text.index('ggml_tensor * llm_graph_context::build_attn(\n        llm_graph_input_attn_kv * inp,')
    end=text.index('\nstatic std::unique_ptr<llm_graph_input_attn_k>',start)
    section=text[start:end];assert section.count(anchor)==1
    replacement=r'''
    const auto & prefix=inp->prefix_n_kv;
    bool ordered=ubatch.pos && ubatch.n_seqs_unq==1;
    for (uint32_t row=1;ordered && row<ubatch.n_tokens;++row) ordered=ubatch.pos[row]==ubatch.pos[0]+int(row);
    const bool grouped=hs_query_batch && cparams.causal_attn && !cparams.flash_attn && ordered &&
        q->ne[2]>1 && prefix.size()==size_t(q->ne[2]) && prefix.front()!=prefix.back() &&
        k->ne[3]==1 && v->ne[3]==1 && kq_b==nullptr && sinks==nullptr && v_mla==nullptr;
    ggml_tensor * cur=nullptr;
    if (grouped) {
        const bool transposed=v->nb[1]>v->nb[2];
        for (size_t begin=0;begin<prefix.size();) {
            size_t end=begin+1;while(end<prefix.size() && prefix[end]==prefix[begin])++end;
            const int64_t width=end-begin,extent=prefix[begin];
            GGML_ASSERT(extent>0 && extent<=k->ne[2] && extent<=kq_mask->ne[0]);
            auto * qg=ggml_view_3d(ctx0,q,q->ne[0],q->ne[1],width,q->nb[1],q->nb[2],begin*q->nb[2]);
            auto * kg=ggml_view_4d(ctx0,k,k->ne[0],k->ne[1],extent,1,k->nb[1],k->nb[2],k->nb[3],0);
            auto * vg=ggml_view_4d(ctx0,v,transposed?extent:v->ne[0],v->ne[1],transposed?v->ne[2]:extent,1,v->nb[1],v->nb[2],v->nb[3],0);
            auto * mg=ggml_view_2d(ctx0,kq_mask,extent,width,kq_mask->nb[1],begin*kq_mask->nb[1]);
            auto * group=build_attn_mha(qg,kg,vg,nullptr,mg,nullptr,nullptr,0,kq_scale,il);
            cb(group,"hs_prefix_attention",il);
            cur=cur?ggml_concat(ctx0,cur,group,1):group;
            begin=end;
        }
        ggml_build_forward_expand(gf,cur);
    } else {
        cur=build_attn_mha(q,k,v,kq_b,kq_mask,sinks,v_mla,0,kq_scale,il);
    }
    cb(cur, "kqv_out", il);'''
    section=section.replace(anchor,replacement)
    before=hashlib.sha256(p.read_bytes()).hexdigest()
    p.write_text(text[:start]+section+text[end:],encoding='utf-8',newline='\n')
    changed.setdefault('src/llama-graph.cpp',{'before':before})['after']=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'mechanism':'Equal causal-prefix extents preserve the scalar reduction tree at physical KV padding boundaries.',
            'changed_files':changed,'numerical_policy_changed':True,'qwen_norm_offload_fix':False,
            'guards':'Dense contiguous single-stream append, ordered single-sequence causal non-flash attention; maximal adjacent equal-extent groups; unchanged generic path otherwise.',
            'reference_policy':'Unscoped single-row R is unchanged. No task ID, answer token, output index, layer or margin condition.',
            'graph_reuse':'Cache the physical per-row prefix extent vector with the graph input and reject reuse if it changes.'}
