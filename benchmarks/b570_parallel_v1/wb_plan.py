"""Export the planner for a whole-target caller without touching KV or graph state."""
from paths import *
def apply(src):
    h=src/'src/llama-kv-cache.h'
    h.write_text(once(h.read_text(encoding='utf-8'),'    uint32_t get_size()     const;', '    uint32_t get_size()     const;\n    int hs_next_groups(uint32_t rows,uint32_t *groups,uint32_t *head) const;'),encoding='utf-8',newline='\n')
    cpp=src/'src/llama-kv-cache.cpp'
    s=cpp.read_text(encoding='utf-8')+r'''
int llama_kv_cache::hs_next_groups(uint32_t rows,uint32_t *groups,uint32_t *head) const {
    if (!rows || rows>32 || n_swa || get_n_stream()!=1) return -1;
    const auto &cells=v_cells[0];
    const uint32_t end=cells.used_max_p1();
    if(cells.get_used()!=end || v_heads[0]>end || uint64_t(end)+rows>cells.size()) return -1;
    *head=end;
    const uint32_t pad=std::max(n_pad,256u);
    // Exact allocator rule on a dense append. Fast path avoids allocating a row list.
    if((end/pad)==((end+rows-1)/pad)){ groups[0]=rows;return 1; }
    const hs_reference_batching::DenseAppendState predicted{end,rows,end+rows,end+rows,cells.size(),pad,1,true,false};
    const auto ext=hs_reference_batching::scalar_prefix_requirements(predicted);
    const auto plan=hs_reference_batching::partition_adjacent(ext.extents);
    for(size_t i=0;i<plan.size();++i) groups[i]=uint32_t(plan[i].end-plan[i].begin);
    return int(plan.size());
}
extern "C" LLAMA_API int hs_parallel_groups(llama_context *ctx,uint32_t rows,uint32_t *groups,uint32_t *head){
    auto *cache=dynamic_cast<llama_kv_cache *>(llama_get_memory(ctx));
    return cache?cache->hs_next_groups(rows,groups,head):-1;
}
'''
    cpp.write_text(s,encoding='utf-8',newline='\n')
if __name__=='__main__':apply(ROOT/'source-00')

