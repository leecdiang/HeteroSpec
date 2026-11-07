#pragma once
#include "ggml-backend.h"
#include "../src/hsc_counter.h"
#include "llama.h"
#include "nlohmann/json.hpp"
#include <filesystem>
#include <fstream>
#include <cstring>

namespace q95capture {
using json=nlohmann::ordered_json;
inline bool opened[2]={false,false},done[2]={false,false};
inline json snapshots[2];
inline bool enabled(){return hsc::is_heavy() && hsc::w.role==1 && std::getenv("HS_Q95_CAPTURE");}
inline json dump_tensor(ggml_tensor * t,const std::string & name,int phase){
    const auto dir=std::filesystem::path(std::getenv("HS_Q95_CAPTURE"))/(phase==0?"prefill":"continuation");
    std::filesystem::create_directories(dir);
    std::vector<unsigned char> data(ggml_nbytes(t));ggml_backend_tensor_get(t,data.data(),0,data.size());
    const auto path=dir/(name+".bin");if(std::filesystem::exists(path))throw std::runtime_error("duplicate snapshot tensor");
    std::ofstream file(path,std::ios::binary);file.write((const char*)data.data(),data.size());file.flush();if(!file)throw std::runtime_error("snapshot write failed");
    std::vector<unsigned char> params((unsigned char*)t->op_params,(unsigned char*)t->op_params+GGML_MAX_OP_PARAMS);
    return {{"file",name+".bin"},{"type",int(t->type)},{"type_name",ggml_type_name(t->type)},
        {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
        {"bytes",data.size()},{"pointer",(uint64_t)t->data},{"alignment_mod256",(uint64_t)t->data%256},
        {"buffer",t->buffer?ggml_backend_buffer_name(t->buffer):"null"},{"op",ggml_op_name(t->op)},{"op_params_bytes",params}};
}
inline bool callback(ggml_tensor * t,bool ask){
    if(!enabled())return false;
    const int phase=hsc::w.prefill?0:1;
    const bool qk=std::strcmp(t->name,"kq-0")==0;
    const bool soft=std::strcmp(t->name,"kq_soft_max-0")==0;
    const bool av=std::strcmp(t->name,"kqv-0")==0;
    if(done[phase])return false;
    if(qk && !opened[phase]){
        const auto * q=t->src[1];if(q->ne[1]<=1 || q->ne[1]>4 || q->ne[3]!=1)return false;
        if(ask)return true;
        opened[phase]=true;
        auto * ctx=(llama_context*)hsc::w.context;
        auto * memory=llama_get_memory(ctx);
        snapshots[phase]={{"phase",phase==0?"prefill":"continuation"},{"role","target"},{"layer",0},
            {"caller_rows",hsc::w.caller_rows},{"q_occupancy",q->ne[1]},{"context_pointer",(uint64_t)ctx},
            {"cache_sequence",0},{"cache_min_at_operator",llama_memory_seq_pos_min(memory,0)},
            {"cache_max_at_operator",llama_memory_seq_pos_max(memory,0)},
            {"Q",dump_tensor(t->src[1],"Q",phase)},{"K",dump_tensor(t->src[0],"K",phase)},
            {"native_QK",dump_tensor(t,"native_QK",phase)}};
        return true;
    }
    if(!opened[phase])return false;
    if(soft){
        if(ask)return true;
        if(!t->src[1])throw std::runtime_error("snapshot mask absent");
        snapshots[phase]["mask"]=dump_tensor(t->src[1],"mask",phase);
        snapshots[phase]["native_softmax"]=dump_tensor(t,"native_softmax",phase);
        return true;
    }
    if(av){
        if(ask)return true;
        snapshots[phase]["V"]=dump_tensor(t->src[0],"V",phase);
        snapshots[phase]["native_AV"]=dump_tensor(t,"native_AV",phase);
        const auto dir=std::filesystem::path(std::getenv("HS_Q95_CAPTURE"))/(phase==0?"prefill":"continuation");
        std::ofstream file(dir/"snapshot.json",std::ios::binary);file<<snapshots[phase].dump(2)<<"\n";file.flush();if(!file)throw std::runtime_error("snapshot metadata failed");
        done[phase]=true;return true;
    }
    return false;
}
}
