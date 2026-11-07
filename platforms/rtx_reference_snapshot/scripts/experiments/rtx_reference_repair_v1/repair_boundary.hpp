#pragma once
// Included AFTER Context. No historical output is used to choose a live token.
namespace hs_repair {
struct Boundary {
    std::vector<uint8_t> state;
    std::vector<float> logits;
    json bounds;
};
inline Boundary capture_boundary(Context&x){
    llama_synchronize(x.c);Boundary b;b.bounds=x.bounds();
    auto n=llama_state_seq_get_size(x.c,0);need(n>0,"empty producer state");b.state.resize(n);
    need(llama_state_seq_get_data(x.c,b.state.data(),n,0)==n,"producer serialization");
    auto*p=llama_get_logits_ith(x.c,-1);need(p,"producer final logits absent");
    b.logits.assign(p,p+llama_vocab_n_tokens(llama_model_get_vocab(x.model)));
    sample_vector(b.logits);return b;
}
inline json import_boundary(Context&receiver,const Boundary&b,bool verify){
    need(receiver.bounds()["max"].get<int>()<0,"receiver must be empty before import");
    auto n=llama_state_seq_set_data(receiver.c,b.state.data(),b.state.size(),0);
    need(n==b.state.size(),"state import did not consume the complete buffer");
    need(receiver.bounds()==b.bounds,"positions changed at import");
    json r={{"bytes",n},{"positions_equal",true},{"receiver_readback_checked",verify},
       {"includes_initial_logits",true},{"pending_token_consumed",false}};
    if(verify){
        auto m=llama_state_seq_get_size(receiver.c,0);std::vector<uint8_t> after(m);
        need(llama_state_seq_get_data(receiver.c,after.data(),m,0)==m,"receiver state readback");
        r["serialized_bytes_equal"]=after==b.state;
        // Reject an unexplained representation mismatch. A documented semantic KV
        // parser can replace this overly strong check; never waive it to get PASS.
        need(after==b.state,"serialized import differs; audit logical KV before advancing");
    }
    return r;
}
inline int produce_and_import(llama_model*model,Context&receiver,const std::vector<int>&prompt,
                             bool capture,const fs::path&dir,json&receipt){
    const bool reference=opt.prefill=="reference";
    const int selector=opt.prefill=="qb"?0:1;
    auto begin=Clock::now();
    {
        // A real UB1/unscoped producer, not q1 calls inside an arbitrary UB4 graph.
        // The entire producer creation/prefill/export/import/destruction is paid.
        Context donor(model,reference?1:4,true,!reference,capture,dir/"producer",selector);
        donor.decode(prompt,0,false,"PREFILL");
        auto b=capture_boundary(donor);
        receipt=import_boundary(receiver,b,capture);
        receipt["producer_kind"]=opt.prefill;
        receipt["producer_ub"]=reference?1:4;
        receipt["producer_calls"]=donor.calls;
        receipt["producer_seconds"]=donor.phases;
        receipt["producer_geometry"]=json::array();if(capture)for(auto&kv:donor.obs.signatures)receipt["producer_geometry"].push_back(kv.second);
        if(capture){
            write_bytes(dir/"boundary_source.state",b.state.data(),b.state.size());
            write_bytes(dir/"boundary_logits.f32",b.logits.data(),b.logits.size()*sizeof(float));
            // Matches the inherited capture convention. Never read stale receiver logits.
            write_bytes(receiver.path/"initial.f32",b.logits.data(),b.logits.size()*sizeof(float));
            receipt["boundary_state_sha256"]=hash_file(dir/"boundary_source.state");
            receipt["boundary_logits_sha256"]=hash_file(dir/"boundary_logits.f32");
        }
        const int pending=sample_vector(b.logits);
        receipt["pending_token"]=pending;
    }
    receipt["producer_bridge_seconds"]=since(begin);
    return receipt["pending_token"].get<int>();
}
inline void save_native_boundary(Context&x,const fs::path&dir,json&r){
    auto b=capture_boundary(x);
    write_bytes(dir/"boundary_source.state",b.state.data(),b.state.size());
    write_bytes(dir/"boundary_logits.f32",b.logits.data(),b.logits.size()*sizeof(float));
    r={{"producer_kind","native"},{"positions",b.bounds},{"bytes",b.state.size()},
       {"boundary_state_sha256",hash_file(dir/"boundary_source.state")},
       {"boundary_logits_sha256",hash_file(dir/"boundary_logits.f32")},
       {"pending_token",sample_vector(b.logits)}};
}
}
