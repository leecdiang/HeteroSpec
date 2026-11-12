#pragma once
// A separate native draft-only producer. It records proposals at EVERY frozen
// greedy prefix so k3 and k7 can consume the same owned position-indexed tape.
// The target reference is not executed or changed here; its original receipt is bound.
static void m2_tapes(const json& job,json& result,const fs::path& root,Pair& pool,llama_model*d){
    need(phase_proposal_mode=="producer"&&pool.draft,"explicit native tape producer");
    need(!job.contains("inputs")&&!job.contains("cases"),"producer cannot run SD requests");
    const auto*v=llama_model_get_vocab(d);json outputs=json::array();
    for(const auto& entry:job.at("proposal_tape_requests")){
        std::string name=entry.at("name");need(name.find('/')==std::string::npos&&name.find("..") ==std::string::npos,"safe tape name");
        const auto prompt=entry.at("prompt_ids").get<std::vector<int>>();const auto greedy=entry.at("greedy_ids").get<std::vector<int>>();
        need(!prompt.empty()&&greedy.size()>1&&greedy.size()<=128&&prompt.size()+greedy.size()+8<=1024,"bounded native tape producer");
        auto& c=*pool.draft;c.reset(false,root/"producer"/name);hsc::begin("counts",int(prompt.size()));
        c.decode(prompt,0,false,"PREFILL");json rows=json::array();
        for(size_t i=0;i+1<greedy.size();++i){
            const int base=int(prompt.size()+i),seed=greedy[i];need(seed>=0&&seed<llama_vocab_n_tokens(v)&&!llama_vocab_is_eog(v,seed),"frozen autonomous greedy seed");
            c.trim(base);c.decode({seed},base,false,"DRAFT_SYNC");json proposals=json::array(),vectors=json::array();
            for(int j=0;j<7;++j){
                auto*p=llama_get_logits_ith(c.c,-1);need(p,"owned proposal vector");Sha256 hash;
                const int n=llama_vocab_n_tokens(v);for(int z=0;z<n;++z)need(std::isfinite(p[z]),"finite owned proposal operands");
                hash.update(reinterpret_cast<const char*>(p),size_t(n)*sizeof(float));
                int token=c.sample(-1,"");proposals.push_back(token);vectors.push_back(hash.finish());c.decode({token},base+1+j,false,"PROPOSE");
            }
            rows.push_back({{"base",base},{"seed",seed},{"proposals",proposals},{"proposal_vector_sha256",vectors}});c.trim(base+1);
        }
        json tape={{"schema","heterospec.m2.owned-position-proposal-tape.v1"},{"root",entry.at("root")},
            {"target_sha256",job.at("target_sha256")},{"draft_sha256",job.at("draft_sha256")},
            {"autonomous_R_receipt_sha256",entry.at("autonomous_R_receipt_sha256")},
            {"prompt_ids",prompt},{"greedy_ids",greedy},{"max_k",7},{"rows",rows}};
        fs::create_directories(root/"tapes");dump(root/"tapes"/(name+".json"),tape);
        int actual=0;json widths=json::object();for(size_t i=0;i<hsc::w.draft_physical.size();++i)if(hsc::w.draft_physical[i]){widths[std::to_string(i)]=hsc::w.draft_physical[i];actual+=int(i*hsc::w.draft_physical[i]);}
        need(actual==int(prompt.size())+8*int(rows.size()),"actual producer draft physical row accounting");
        result["token_rows"]=result["token_rows"].get<int>()+actual;result["trajectories"]=result["trajectories"].get<int>()+1;
        outputs.push_back({{"root",entry.at("root")},{"path","tapes/"+name+".json"},{"canonical_tape_sha256",hash_text(tape.dump())},
            {"draft_calls",c.calls},{"draft_physical_width_hist",widths},{"target_calls",0},{"target_rows",0},{"draft_rows",actual}});
    }
    result["proposal_tapes"]=outputs;result["proposal_mode"]="producer";hsc::w.active=false;
}
