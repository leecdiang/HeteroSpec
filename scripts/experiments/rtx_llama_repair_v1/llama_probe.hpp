#pragma once
// Included AFTER Context. No hook is active in qualification or timed requests.
#include "cycle_contract.hpp"
namespace hs_llama_probe {
struct Options {
    std::string mode="off", order="scalar-first";
    int cycle=-1; size_t max_state_bytes=512ULL*1024*1024;
    fs::path root; bool seen=false;
    json receipt; std::vector<std::string> own_hashes;
};
inline Options opt;
inline void configure(const json& slot,const fs::path& root) {
    opt=Options{};opt.root=root;
    auto j=slot.value("llama_diag",json::object());
    opt.mode=j.value("mode",std::string("off"));
    need(opt.mode=="off"||opt.mode=="checkpoint"||opt.mode=="pair","invalid diagnostic mode");
    if(opt.mode=="off") return;
    opt.cycle=j.at("cycle").get<int>(); opt.order=j.value("pair_order",std::string("scalar-first"));
    opt.max_state_bytes=j.value("max_state_bytes",opt.max_state_bytes);
    need(hs_llama_contract::probe_allowed(slot.at("category")=="diagnostic",slot.at("observer")=="heavy",slot.at("draft_enabled").get<bool>(),opt.cycle),"diagnostic leaked into natural qualification/timing");
    need(opt.order=="scalar-first"||opt.order=="batch-first","invalid diagnostic order");
    need(opt.max_state_bytes>0&&opt.max_state_bytes<=2ULL*1024*1024*1024,"state reservation");
}
inline std::vector<uint8_t> state(Context& c) {
    llama_synchronize(c.c);const auto n=llama_state_seq_get_size(c.c,0);
    need(n>0&&n<=opt.max_state_bytes,"diagnostic state exceeds reservation");
    std::vector<uint8_t> b(n);
    need(llama_state_seq_get_data(c.c,b.data(),n,0)==n,"diagnostic state export");return b;
}
inline std::string bytes_hash(const void* p,size_t n) {
    Sha256 h;h.update(reinterpret_cast<const char*>(p),n);return h.finish();
}
struct RestoreGlobals {
    hs_repair::Options saved=hs_repair::opt;
    bool active=hs_scope::active; int layout=hs_scope::requested_layout;
    ~RestoreGlobals(){hs_repair::opt=saved;hs_scope::active=active;hs_scope::requested_layout=layout;}
};
inline json replay(llama_model* model,const std::vector<uint8_t>& before,
                   const json& bounds,const std::vector<int>& tokens,int base,
                   bool scalar,Context& natural,const fs::path& directory) {
    RestoreGlobals restore;
    hs_repair::opt.root=directory;hs_repair::opt.files=0;hs_repair::opt.bytes=0;hs_repair::opt.error.clear();
    fs::create_directories(directory);if(hs_repair::opt.enabled)fs::create_directories(directory/"trace");
    // A fresh q1 unscoped consumer is compared with a fresh same-policy q4
    // consumer of EXACTLY the same source bytes. That source is the natural C
    // path; it is NOT automatically a canonical-R state.
    Context shadow(model,scalar?1:natural.ub,true,scalar?false:natural.scoped,true,directory,scalar?1:natural.selector);
    need(shadow.bounds()["max"].get<int>()<0,"nonempty diagnostic receiver");
    need(llama_state_seq_set_data(shadow.c,before.data(),before.size(),0)==before.size(),"diagnostic import");
    need(shadow.bounds()==bounds&&state(shadow)==before,"diagnostic own-path restore/readback");
    json result={{"scalar",scalar},{"state_import_equal",true},{"rows",json::array()}};
    const int vocabulary=llama_vocab_n_tokens(llama_model_get_vocab(model));
    need(vocabulary==128256,"unexpected Llama vocabulary");
    auto capture=[&](int row,int index) {
        auto* p=llama_get_logits_ith(shadow.c,index);need(p,"diagnostic logits absent");
        std::vector<float> values(p,p+vocabulary);const int token=hs_repair::sample_vector(values);
        auto name="row-"+std::to_string(row)+".f32";
        hs_repair::write_bytes(directory/name,values.data(),values.size()*sizeof(float));
        result["rows"].push_back({{"row",row},{"argmax",token},{"file",name},
          {"sha256",bytes_hash(values.data(),values.size()*sizeof(float))}});
    };
    if(scalar){for(size_t i=0;i<tokens.size();++i){shadow.decode({tokens[i]},base+int(i),true,"VERIFY");capture(int(i),-1);}}
    else {shadow.decode(tokens,base,true,"VERIFY");for(size_t i=0;i<tokens.size();++i)capture(int(i),int(i));}
    auto after=state(shadow);hs_repair::write_bytes(directory/"after.state",after.data(),after.size());
    result["after_state_sha256"]=bytes_hash(after.data(),after.size());result["after_bounds"]=shadow.bounds();
    result["geometry"]=json::array();for(const auto& e:shadow.obs.signatures)result["geometry"].push_back(e.second);
    result["trace_files"]=hs_repair::opt.files;result["trace_bytes"]=hs_repair::opt.bytes;
    dump(directory/"REPLAY.json",result);return result;
}
inline void before(Context& natural,llama_model* model,const std::vector<int>& tokens,
                   int base,int cycle,int emitted) {
    if(opt.mode=="off"||cycle!=opt.cycle)return;
    need(!opt.seen,"diagnostic cycle repeated");opt.seen=true;
    need(tokens.size()>=1&&tokens.size()<=4,"invalid registered verify width");
    const auto bounds=natural.bounds();hs_llama_contract::preverify_bound(bounds["max"].get<int>(),base);
    auto bytes=state(natural);auto dir=opt.root/"checkpoint";fs::create_directories(dir);
    hs_repair::write_bytes(dir/"before.state",bytes.data(),bytes.size());
    opt.receipt={{"cycle",cycle},{"base",base},{"output_begin",emitted},{"pending",tokens.front()},
      {"verify_tokens",tokens},{"source_bounds",bounds},{"source_state_sha256",bytes_hash(bytes.data(),bytes.size())},
      {"source_state_bytes",bytes.size()},{"source_is_canonical_R",false},
      {"row_map",json::array()},{"diagnostic_only",true},{"extra_decode_calls",0}};
    for(size_t i=0;i<tokens.size();++i)opt.receipt["row_map"].push_back({{"row",i},
      {"consumed_position",base+int(i)},{"predicted_output_index",hs_llama_contract::output_index(emitted,int(i),int(tokens.size()))}});
    dump(dir/"CHECKPOINT.json",opt.receipt);
    if(opt.mode=="pair") {
        json scalar,batch;
        auto one=[&](){scalar=replay(model,bytes,bounds,tokens,base,true,natural,dir/"scalar");};
        auto many=[&](){batch=replay(model,bytes,bounds,tokens,base,false,natural,dir/"batch");};
        if(opt.order=="scalar-first"){one();many();}else{many();one();}
        opt.receipt["scalar"]=scalar;opt.receipt["batch"]=batch;
        opt.receipt["extra_decode_calls"]=tokens.size()+1;
        for(auto& row:batch["rows"])opt.own_hashes.push_back(row["sha256"].get<std::string>());
    }
    // Shadow execution must not consume or mutate the original pending state.
    need(state(natural)==bytes&&natural.bounds()==bounds,"diagnostic mutated natural context");
}
inline void after(Context& natural,int cycle,int width) {
    if(opt.mode=="off"||cycle!=opt.cycle)return;
    need(opt.seen,"diagnostic before-hook absent");opt.receipt["natural_rows"]=json::array();
    int vocabulary=llama_vocab_n_tokens(llama_model_get_vocab(natural.model));
    bool own=true;
    for(int row=0;row<width;++row){auto*p=llama_get_logits_ith(natural.c,row);need(p,"natural verification vector missing");
        auto h=bytes_hash(p,size_t(vocabulary)*sizeof(float));
        opt.receipt["natural_rows"].push_back({{"row",row},{"sha256",h}});
        if(opt.mode=="pair")own=own&&h==opt.own_hashes.at(row);
    }
    opt.receipt["same_policy_own_path_vectors_equal"]=opt.mode=="pair"?json(own):json(nullptr);
    dump(opt.root/"checkpoint"/"CHECKPOINT.json",opt.receipt);
    need(own,"q4 own-path replay differs; do not infer causal effects before fixing replay control");
}
inline json finish() {
    if(opt.mode!="off")need(opt.seen,"selected cycle was not executed; keep failed diagnostic");
    return {{"mode",opt.mode},{"seen",opt.seen},{"diagnostic_only",opt.mode!="off"}};
}
}
