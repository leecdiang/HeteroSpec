#pragma once
// Binding to the admitted llama dense-cache profile. No token content is read
// by the planner, and no KV bytes cross the device boundary here.
#include "phase_plan.hpp"
#include "llama-kv-cache.h"
inline std::string phase_lowering="LOCAL";
inline int phase_draft_width=1;
inline int phase_target_reserve=4;
inline std::string phase_proposal_mode="live";


struct PhaseContext {
    bool poisoned=false;
    json executions=json::array();
    std::vector<std::vector<float>> outputs;
    double planning_s=0,output_copy_s=0,first_call_plan_s=0,resident_initial_plan_s=0;
    bool compiled_once=false;
    void clear(){need(!poisoned,"poisoned phase context");executions=json::array();outputs.clear();planning_s=output_copy_s=first_call_plan_s=0;}
    template<class Native>
    void decode(Native& owner,const std::vector<int>& ids,int position,bool all,const char* phase){
        need(!poisoned && !ids.empty(),"invalid phase call");
        auto began=Clock::now();
        auto* cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(owner.c));
        need(cache,"unsupported non-dense cache");
        const auto extents=cache->phase_append_requirements(uint32_t(position),uint32_t(ids.size()));
        need(extents.size()==ids.size(),"unsupported cache/append requirements");
        need(cache->type_k()==GGML_TYPE_F16 && cache->type_v()==GGML_TYPE_F16,"unsupported cache arithmetic");
        need(!all||ids.size()<=size_t(phase_target_reserve),"requested outputs exceed actual M2 output reserve");
        const uint64_t arithmetic=1+uint64_t(cache->type_k())+(uint64_t(cache->type_v())<<8);
        std::vector<refplan::Row> rows;rows.reserve(ids.size());
        for(size_t i=0;i<ids.size();++i)rows.push_back({position+int64_t(i),extents[i],arithmetic,all||i+1==ids.size()});
        // SIMPLE's caller groups are maximal for the bound extent and width.
        // LOCAL retains wide projection groups, splitting only attention locally.
        std::vector<refplan::Group> groups;
        if(phase_lowering=="SIMPLE")groups=refplan::plan(rows,32);
        else {need(phase_lowering=="LOCAL","unknown lowering");for(size_t i=0;i<rows.size();i+=32)groups.push_back({i,std::min<size_t>(32,rows.size()-i),0,1});}
        const double compilation=since(began);planning_s+=compilation;
        if(executions.empty())first_call_plan_s=compilation;
        if(!compiled_once){resident_initial_plan_s=compilation;compiled_once=true;}
        outputs.assign(ids.size(),{});
        const size_t vocabulary=llama_vocab_n_tokens(llama_model_get_vocab(owner.model));
        try{
            for(const auto& group:groups){
                auto b=llama_batch_init(int(group.count),0,1);b.n_tokens=int(group.count);
                std::vector<size_t> wanted;
                for(size_t j=0;j<group.count;++j){const size_t i=group.begin+j;b.token[j]=ids[i];b.pos[j]=int(rows[i].position);b.n_seq_id[j]=1;b.seq_id[j][0]=0;b.logits[j]=rows[i].requested_output;if(b.logits[j])wanted.push_back(i);}
                owner.obs.phase=phase;owner.obs.base=position+int(group.begin);owner.obs.caller=int(group.count);
                hs_scope::requested_layout=0;hs_scope::active=true;phase_observe=owner.capture;
                hsc::decode_begin(owner.c,"target",std::string(phase)=="PREFILL",b.n_tokens);
                auto t=Clock::now();int rc=llama_decode(owner.c,b);llama_batch_free(b);need(rc==0,"phase native decode failed");llama_synchronize(owner.c);owner.phases[phase]+=since(t);hsc::decode_end();owner.calls++;
                t=Clock::now();
                for(size_t i:wanted){auto* p=llama_get_logits_ith(owner.c,int(i-group.begin));need(p,"requested row missing");outputs[i].assign(p,p+vocabulary);}
                output_copy_s+=since(t);
                const auto& cells=cache->get_cells(0);
                need(cells.used_max_p1()==uint32_t(position+group.begin+group.count),"unexpected physical append mapping");
                executions.push_back({{"phase",phase},{"position",position+group.begin},{"width",group.count},{"expected_extents",std::vector<uint32_t>(extents.begin()+group.begin,extents.begin()+group.begin+group.count)},{"actual_attention_extent",cache->phase_current_extent()},{"requested_rows",wanted},{"active_cells",cells.get_used()}});
                need(!owner.obs.bad,"phase graph placement failed");
            }
        }catch(...){poisoned=true;throw;}
    }
    float* logits(int row){
        if(row<0){for(size_t i=outputs.size();i>0;--i)if(!outputs[i-1].empty())return outputs[i-1].data();}
        need(row>=0 && size_t(row)<outputs.size() && !outputs[row].empty(),"unrequested phase output");return outputs[row].data();
    }
};
