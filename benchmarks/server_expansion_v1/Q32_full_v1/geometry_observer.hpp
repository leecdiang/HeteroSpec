#pragma once
// Exact structural dedup before JSON allocation. Validate device on every
// invocation; retain each distinct complete descriptor and occurrence count.
// Every physical call/position remains in the independent execution journal.
#ifdef Q32_OFFLINE_OPERANDS
#include "operand_observer.hpp"
#else
static bool q32_operand_wanted(ggml_tensor*,const std::string&){return false;}
static void q32_operand_copy(ggml_tensor*){throw std::runtime_error("offline operand capture disabled");}
#endif
struct Observer {
    std::string phase="setup";int base=0,caller=0;bool bad=false;
    std::map<std::string,json> signatures;
    static ggml_backend_dev_t device(ggml_tensor*t){return t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;}
    static json meta(ggml_tensor*t){auto*d=device(t);return {{"name",t->name},{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"device",d?ggml_backend_dev_description(d):"UNALLOCATED"}};}
    template<class T>static void field(std::string&out,const T&x){out.append(reinterpret_cast<const char*>(&x),sizeof(x));}
    static void text(std::string&out,const char*x){const size_t n=std::strlen(x);field(out,n);out.append(x,n);}
    static void tensor_key(std::string&out,ggml_tensor*t){
        text(out,t->name);field(out,t->type);out.append(reinterpret_cast<const char*>(t->ne),sizeof(t->ne));out.append(reinterpret_cast<const char*>(t->nb),sizeof(t->nb));auto*d=device(t);field(out,d);
    }
    static bool callback(ggml_tensor*t,bool ask,void*opaque){
        auto&o=*static_cast<Observer*>(opaque);if(!phase_observe)return false;
        if(!ask){if(q32_operand_wanted(t,o.phase)){q32_operand_copy(t);return false;}o.bad=true;return false;}
        if(o.phase!="VERIFY"&&o.phase!="PREFILL"&&o.phase!="ORDINARY")return false;
        const std::string name=t->name;if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0&&t->op!=GGML_OP_MUL_MAT)return false;
        auto*d=device(t);if(!d||ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_GPU)o.bad=true;
        std::string key;key.reserve(1024);text(key,o.phase.c_str());field(key,o.caller);field(key,t->op);tensor_key(key,t);
        for(int i=0;i<GGML_MAX_SRC;++i){const bool present=t->src[i]!=nullptr;field(key,present);if(present)tensor_key(key,t->src[i]);}
        auto it=o.signatures.find(key);
        if(it!=o.signatures.end()){it->second["observed_occurrences"]=it->second["observed_occurrences"].get<int>()+1;return q32_operand_wanted(t,o.phase);}
        auto j=meta(t);j["phase"]=o.phase;j["op"]=ggml_op_name(t->op);j["sources"]=json::array();for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])j["sources"].push_back(meta(t->src[i]));j["caller_rows"]=o.caller;j["first_position"]=o.base;j["observed_occurrences"]=1;
        j["visible_keys_by_causal_row"]=json::array();for(int i=0;i<o.caller;++i)j["visible_keys_by_causal_row"].push_back(o.base+i+1);j["visible_keys_basis"]="First observed descriptor instance; full positions/widths remain in per-call executions";
        o.signatures.emplace(std::move(key),std::move(j));return q32_operand_wanted(t,o.phase);
    }
};
