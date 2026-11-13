"""Exact-anchor M2 frontend port; no numerical archive or reference edits."""
from pathlib import Path
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b,1)
def transform(frontend):
    p=frontend/'resident_context.hpp';s=p.read_text()
    s=once(s,'inline int phase_draft_width=1;', 'inline int phase_draft_width=1;\ninline int phase_target_reserve=4;\ninline std::string phase_proposal_mode="live";')
    s=once(s,'ids.size()<=4,"requested outputs exceed unchanged candidate reserve"','ids.size()<=size_t(phase_target_reserve),"requested outputs exceed actual M2 output reserve"')
    p.write_text(s)
    p=frontend/'worker.cpp';s=p.read_text()
    s=once(s,'p.n_outputs_max=istarget?4:1;p.n_outputs_max_per_seq=istarget?4:1;', 'p.n_outputs_max=istarget?phase_target_reserve:1;p.n_outputs_max_per_seq=istarget?phase_target_reserve:1;')
    s=once(s,'if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0)return false;', 'if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0&&t->op!=GGML_OP_MUL_MAT)return false;')
    s=once(s,'double setup=since(start);','''const bool replay=phase_proposal_mode=="replay";
    need(phase_proposal_mode=="live"||replay,"transaction mode");
    need(input.contains("proposal_tape")==replay,"live/replay tape permission");
    if(replay){need(input.at("proposal_tape").at("prompt_ids")==input.at("prompt_ids"),"owned tape prompt");
        need(hash_text(input.at("proposal_tape").dump())==input.at("proposal_tape_sha256"),"owned tape content SHA");}
    need(input.at("prompt_ids").size()+size_t(input.at("cap").get<int>())+size_t(k+1)<=llama_n_ctx(target->c),"transient position capacity");
    r["proposal_mode"]=phase_proposal_mode;r["target_output_reserve"]=phase_target_reserve;
    if(replay)r["proposal_tape_sha256"]=input.at("proposal_tape_sha256");
    double setup=since(start);''')
    s=once(s,'if(draft)draft->decode(prompt,0,false,"PREFILL");','if(draft&&!replay)draft->decode(prompt,0,false,"PREFILL");')
    a='''draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
        std::vector<int> proposals;
        for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);draft->decode({proposal},base+1+j,false,"PROPOSE");}'''
    b='''std::vector<int> proposals;
        if(replay){
            const auto& tape=input.at("proposal_tape");const int index=base-int(prompt.size());
            need(index>=0 && size_t(index)<tape.at("rows").size(),"owned tape base missing");
            const auto& row=tape.at("rows").at(index);
            need(row.at("base")==base&&row.at("seed")==seed&&row.at("proposals").size()>=size_t(k),"owned tape seed/base/width");
            for(int j=0;j<k;++j){int v=row.at("proposals").at(j);need(v>=0&&v<llama_vocab_n_tokens(v),"tape proposal token");proposals.push_back(v);}
        }else{
            draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
            for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);draft->decode({proposal},base+1+j,false,"PROPOSE");}
        }'''
    # Use the vocabulary already declared above; keep token validation structural.
    b=b.replace('int v=row.at("proposals").at(j);need(v>=0&&v<llama_vocab_n_tokens(v),"tape proposal token");proposals.push_back(v);',
                'int token=row.at("proposals").at(j);need(token>=0&&token<llama_vocab_n_tokens(v),"tape proposal token");proposals.push_back(token);')
    s=once(s,a,b)
    s=once(s,'target->trim(keep);draft->trim(keep);','target->trim(keep);if(!replay)draft->trim(keep);')
    p.write_text(s)
    p=frontend/'entry.cpp';s=p.read_text()
    s=once(s,'#include "rtx_append.inc"','#include "rtx_append.inc"\n#include "m2_tapes.hpp"')
    a='need(!fs::exists(root),"fresh native output");fs::create_directories(root);'
    s=once(s,a,a+'''
        phase_target_reserve=job.at("target_output_reserve");
        const int m2_k=job.at("k");phase_proposal_mode=job.at("proposal_mode");
        need(phase_target_reserve==8&&(m2_k==3||m2_k==7)&&job.at("draft")==true&&job.at("draft_width")==4,"M2 explicit k3/7 reserve8 D4 contract");
        need(phase_proposal_mode=="live"||phase_proposal_mode=="replay"||phase_proposal_mode=="producer","M2 proposal mode");''')
    s=once(s,'job.value("draft",false)?3:0','m2_k')
    s=once(s,'if(job.contains("append_probes")){phase1_append(job,result,root,pool);}',
           'if(job.contains("proposal_tape_requests")){m2_tapes(job,result,root,pool,d);}\n        else if(job.contains("append_probes")){phase1_append(job,result,root,pool);}')
    a='result["token_rows"]=result["token_rows"].get<int>()+int(input.at("prompt_ids").size())+(spec.draft?int(input.at("prompt_ids").size())+8*int(r["cycles"].size()):int(r["ids"].size())-1);'
    b='''int actual_rows=0;for(auto it=r.at("target_physical_width_hist").begin();it!=r.at("target_physical_width_hist").end();++it)actual_rows+=std::stoi(it.key())*it.value().get<int>();
                for(auto it=r.at("draft_physical_width_hist").begin();it!=r.at("draft_physical_width_hist").end();++it)actual_rows+=std::stoi(it.key())*it.value().get<int>();
                result["token_rows"]=result["token_rows"].get<int>()+actual_rows;'''
    s=once(s,a,b);p.write_text(s)
