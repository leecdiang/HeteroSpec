#pragma once
// Included after worker JSON/hash helpers. Scheduler assignments and observed
// values are separate from buffer owners. No source operand is captured after
// an in-place consumer; these are selected OUTPUT snapshots only.
#include "llama-context.h"
#include <regex>
#include <set>
#include <limits>
static json repair_options=json::object();
struct Observer {
    llama_context* context=nullptr;
    std::string phase="setup";
    int base=0,caller=0,call=0;
    bool bad=false,enabled=false,values=false;
    fs::path root;
    std::string prefix_hash;
    std::vector<int> call_ids, prefix_ids;
    std::map<std::string,json> signatures;
    std::map<std::string,int> occurrences;
    size_t total_bytes=0;
    json trace=json::array();
    static json meta(ggml_tensor*t){
        json j={{"name",t->name},{"type",ggml_type_name(t->type)},
            {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
            {"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
            {"op",ggml_op_name(t->op)}};
        auto* d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
        j["buffer_owner"]=d?ggml_backend_dev_description(d):"UNALLOCATED";
        return j;
    }
    bool selected(ggml_tensor*t) const {
        if(!enabled)return false;
        const std::string name=t->name;
        auto phases=repair_options.value("phases",std::vector<std::string>{"PREFILL","ORDINARY","VERIFY"});
        if(std::find(phases.begin(),phases.end(),phase)==phases.end())return false;
        const int first=repair_options.value("min_call_position",0),last=repair_options.value("max_call_position",1023);
        if(base>last || base+caller-1<first)return false;
        const std::regex names(repair_options.value("tensor_regex",std::string("^(kq|hs_|Qcur|Kcur|Vcur|attn_|ffn_|result_|norm|inp_embd).*$")));
        if(!std::regex_match(name,names))return false;
        auto layers=repair_options.value("layers",std::vector<int>{});
        if(!layers.empty()){
            std::smatch m;std::regex suffix("-([0-9]+)$");
            if(std::regex_search(name,m,suffix) && std::find(layers.begin(),layers.end(),std::stoi(m[1]))==layers.end())return false;
        }
        return true;
    }
    static bool callback(ggml_tensor*t,bool ask,void*opaque){
        auto&o=*static_cast<Observer*>(opaque);
        try {
            if(ask){
                if(!o.selected(t))return false;
                auto j=meta(t);
                j["sources"]=json::array();for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(meta(t->src[i]));
                // This is the scheduler's assignment for the current graph, not
                // inferred from the tensor's memory or the model layer table.
                auto* b=o.context?ggml_backend_sched_get_tensor_backend(o.context->get_sched(),t):nullptr;
                j["compute_backend"]=b?ggml_backend_name(b):"UNRESOLVED";
                j["placement_basis"]="ggml_backend_sched_get_tensor_backend";
                if(t->op==GGML_OP_MUL_MAT && !b)o.bad=true;
                j["phase"]=o.phase;j["call"]=o.call;j["first_position"]=o.base;j["caller_rows"]=o.caller;
                j["caller_prefix_sha256"]=o.prefix_hash;
                j["call_ids"]=o.call_ids;j["caller_prefix_ids"]=o.prefix_ids;
                j["logical_row_mapping"]="NOT_INFERRED_FROM_SHAPE";
                std::smatch layer;std::string name=t->name;
                if(std::regex_search(name,layer,std::regex("-([0-9]+)$")))j["layer"]=std::stoi(layer[1]);else j["layer"]=nullptr;
                o.signatures[std::to_string(o.call)+"/"+name]=j;
                return o.values; // false batches normally; true requests post-compute observation
            }
            need(o.values,"unexpected post-compute callback");
            const size_t bytes=ggml_nbytes(t);
            const size_t tensor_limit=repair_options.value("max_tensor_bytes",size_t(64)*1024*1024);
            const size_t request_limit=repair_options.value("max_request_trace_bytes",size_t(512)*1024*1024);
            need(bytes>0&&bytes<=tensor_limit&&o.total_bytes<=request_limit&&bytes<=request_limit-o.total_bytes,"trace byte budget exceeded");
            std::vector<char> data(bytes);
            ggml_backend_tensor_get(t,data.data(),0,bytes);
            auto j=o.signatures.at(std::to_string(o.call)+"/"+std::string(t->name));
            const size_t index=o.trace.size();
            fs::create_directories(o.root/"trace");
            const auto rel=std::string("trace/")+std::to_string(index)+".bin";
            std::ofstream f(o.root/rel,std::ios::binary);f.write(data.data(),data.size());need(bool(f),"tensor trace write");f.close();
            Sha256 hash;hash.update(data.data(),data.size());
            j["file"]=rel;j["sha256"]=hash.finish();j["bytes"]=bytes;
            j["occurrence_in_call"]=o.occurrences[std::to_string(o.call)+"/"+std::string(t->name)]++;
            j["observer_effect"]="synchronizing diagnostic; never performance sample";
            o.trace.push_back(j);o.total_bytes+=bytes;
            dump(o.root/"TRACE.json",{{"version",1},{"snapshots",o.trace},{"interpretation","observed outputs only; token-axis alignment needs explicit source binding"}});
            return true; // false here would abort graph execution
        }catch(const std::exception&e){
            o.bad=true;
            try {if(!o.root.empty())dump(o.root/"OBSERVER_FAILURE.json",{{"error",e.what()},{"phase",o.phase},{"call",o.call}});}catch(...){}
            return false;
        }
    }
};
