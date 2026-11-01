#pragma once
// Included after Context/Pair. Reference-prefill and transfer are paid native
// request work; no saved reference token answer is injected into generation.
struct RepairBoundary { std::vector<uint8_t> state;std::vector<float> logits;json bounds; };
static std::string repair_bytes_hash(const void* p,size_t n){Sha256 s;s.update((const char*)p,n);return s.finish();}
static RepairBoundary repair_snapshot(Context& x){
    llama_synchronize(x.c);
    const auto n=llama_state_seq_get_size(x.c,0);need(n>0,"empty state snapshot");
    RepairBoundary b;b.state.resize(n);
    need(llama_state_seq_get_data(x.c,b.state.data(),n,0)==n,"state export length");
    auto* z=llama_get_logits_ith(x.c,-1);need(z,"boundary logits unavailable");
    const auto nv=llama_vocab_n_tokens(llama_model_get_vocab(x.model));b.logits.assign(z,z+nv);b.bounds=x.bounds();
    for(auto v:b.logits)need(std::isfinite(v),"nonfinite boundary logits");
    return b;
}
static json repair_boundary_identity(const RepairBoundary&b){
    return {{"state_bytes",b.state.size()},{"state_sha256",repair_bytes_hash(b.state.data(),b.state.size())},
        {"logits_sha256",repair_bytes_hash(b.logits.data(),b.logits.size()*sizeof(float))},{"bounds",b.bounds},
        {"scope","serialized sequence KV/positions plus copied full initial logits; opaque state inequality is not a KV-value causal claim"}};
}
static void repair_save_boundary(const RepairBoundary&b,const fs::path&dir){
    fs::create_directories(dir);
    std::ofstream s(dir/"boundary.state",std::ios::binary);s.write((const char*)b.state.data(),b.state.size());need(bool(s),"boundary state write");
    std::ofstream z(dir/"boundary.f32",std::ios::binary);z.write((const char*)b.logits.data(),b.logits.size()*sizeof(float));need(bool(z),"boundary logits write");
    dump(dir/"BOUNDARY.json",repair_boundary_identity(b));
}
static json repair_import(Context&x,const RepairBoundary&b,const std::vector<int>&prompt){
    llama_synchronize(x.c);llama_memory_clear(llama_get_memory(x.c),false);
    const auto got=llama_state_seq_set_data(x.c,b.state.data(),b.state.size(),0);need(got==b.state.size(),"state restore length");
    llama_synchronize(x.c);need(x.bounds()==b.bounds,"restored sequence positions differ");
    const auto n=llama_state_seq_get_size(x.c,0);std::vector<uint8_t> readback(n);
    need(llama_state_seq_get_data(x.c,readback.data(),n,0)==n,"state readback length");
    need(readback==b.state,"serialized state readback differs; inspect format before claiming effective KV correspondence");
    x.token_history=prompt;
    return {{"bytes",got},{"readback_sha256",repair_bytes_hash(readback.data(),readback.size())},{"byte_equal",true},
            {"initial_logits_source","copied producer vector, not restored through KV API"}};
}
static int repair_initial(const std::vector<float>&v,Context&target){
    need(!v.empty(),"empty initial vector");int best=0;
    for(size_t i=0;i<v.size();i++){need(std::isfinite(v[i]),"bad initial logit");if(v[i]>v[best])best=int(i);}
    if(target.capture){std::ofstream f(target.path/"initial.f32",std::ios::binary);f.write((const char*)v.data(),v.size()*sizeof(float));need(bool(f),"initial vector write");}
    return best;
}
static void repair_checkpoint(Context& x,const std::vector<int>&generated,int pending,bool done,const fs::path&dir){
    if(!x.capture)return;
    const auto wanted=repair_options.value("checkpoint_output_lengths",std::vector<int>{});
    if(std::find(wanted.begin(),wanted.end(),int(generated.size()))==wanted.end())return;
    llama_synchronize(x.c);
    const auto n=llama_state_seq_get_size(x.c,0);need(n<=size_t(512)*1024*1024,"checkpoint state too large");
    std::vector<uint8_t> b(n);need(llama_state_seq_get_data(x.c,b.data(),n,0)==n,"checkpoint export");
    fs::create_directories(dir/"checkpoints");const auto stem=std::to_string(generated.size());
    std::ofstream f(dir/"checkpoints"/(stem+".state"),std::ios::binary);f.write((const char*)b.data(),b.size());need(bool(f),"checkpoint write");
    dump(dir/"checkpoints"/(stem+".json"),{{"consumed_ids",x.token_history},{"consumed_sha256",hash_text(json(x.token_history).dump())},
        {"generated_ids",generated},{"pending",done?json(nullptr):json(pending)},{"done",done},{"bounds",x.bounds()},
        {"bytes",b.size()},{"sha256",repair_bytes_hash(b.data(),b.size())},
        {"scope","after actual reconciliation; compare only equal consumed IDs, pending ownership and positions; no serialized last-logit claim"}});
}
