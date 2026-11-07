from host import *
def main():
    s=(HERE/'worker.cpp').read_text()
    code='''
    if(mode=="allocator_census"){
        auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx.get()));check(kv,"dense KV");json result=json::array();
        for(auto&r:j.at("rows")){
            auto ids=r.at("tokens").get<std::vector<int>>();int head=r.at("head");kv->clear(false);llama_seq_id seq=0;
            auto meta=[&](int pos,int n,bool apply){llama_batch_allocr alloc(1);auto b=alloc.ubatch_reserve(n,1);b.seq_id_unq[0]=0;for(int i=0;i<n;i++){b.token[i]=ids[pos+i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i]=&seq;b.output[i]=0;}auto slot=kv->find_slot(b,false);check(!slot.empty(),"allocator slot");auto h=slot.head();if(apply)kv->apply_ubatch(slot,b);return h;};
            if(head)check(meta(0,head,true)==0,"dense prefix origin");int physical=meta(head,std::min(32,int(ids.size())-head),false);
            check(physical==head&&kv->get_cells(0).get_used()==uint32_t(head)&&kv->get_cells(0).used_max_p1()==uint32_t(head),"allocator head");
            result.push_back({{"id",r.at("id")},{"physical_head",physical},{"padding",kv->scalar_padding()},{"metadata_only",true},{"kv_bytes_computed",false}});
        }save(out/"allocator.json",result);return 0;
    }
'''
    s=s.replace('    if(mode=="requests")',code+'    if(mode=="requests")')
    (HERE/'census_worker.cpp').write_text(s);build('census01',source='census_worker.cpp')
    import gzip
    with gzip.open(ROOT/'oasst.messages.jsonl.gz','rt',encoding='utf8') as f:parents={json.loads(x).get('parent_id') for x in f}
    rows=[json.loads(x) for x in (ROOT/'tokenize01/tokens.jsonl').read_text(encoding='utf8').splitlines()]
    sys.path.insert(0,str(HERE.parents[1]/'tpds_prefix_reuse_v1'));import study
    run('allocator-census01','census01',dict(mode='allocator_census',capacity=4096,rows=[dict(id=r['id'],tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids'])) for r in rows if r['id'] not in parents]),admissions=1)
if __name__=='__main__':main()
