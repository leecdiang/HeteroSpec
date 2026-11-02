// A new B570 execution contract. Original CUDA/Vulkan experiments are immutable.
#include "llama.h"
#include "ggml-backend.h"
#include "companion_scope.hpp"
#include "cycle.hpp"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <regex>
#include <stdexcept>
#include <vector>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif
using json=nlohmann::json;
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
#ifndef HS_COMPANION_ORACLE
#define HS_COMPANION_ORACLE 0
#endif
void need(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
json load(const fs::path&p){std::ifstream f(p);need(bool(f),"read JSON");json x;f>>x;return x;}
void dump(const fs::path&p,const json&x){fs::create_directories(p.parent_path());std::ofstream f(p);f<<x.dump(2)<<'\n';need(bool(f),"write JSON");}
void bytes(const fs::path&p,const void*data,size_t n){fs::create_directories(p.parent_path());std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),std::streamsize(n));need(bool(f),"write payload");}
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
json config;
ggml_backend_dev_t device=nullptr;
Clock::time_point worker_start;
json resource_samples=json::array();
void safety(){
    need(elapsed(worker_start)<config.at("worker_timeout_seconds").get<double>(),"native timeout");
    size_t free=0,total=0;ggml_backend_dev_memory(device,&free,&total);
    json sample={{"worker_seconds",elapsed(worker_start)},{"device_free_bytes",free},{"device_total_bytes",total}};
#ifdef _WIN32
    MEMORYSTATUSEX m{};m.dwLength=sizeof(m);need(GlobalMemoryStatusEx(&m),"RAM query");
    sample["ram_available_bytes"]=m.ullAvailPhys;
#endif
    resource_samples.push_back(sample);
    need(free>=config.at("min_vram_free_bytes").get<size_t>(),"device-memory reserve");
#ifdef _WIN32
    need(m.ullAvailPhys>=config.at("min_ram_free_bytes").get<unsigned long long>(),"RAM reserve");
#endif
}
struct Scope{Scope(int m){hs_b570_set_layout(m);}~Scope(){hs_b570_set_layout(0);}};
struct Observer{
    llama_context*ctx=nullptr;fs::path root;bool heavy=false,trace=false,failed=false;
    std::string phase,error,pattern="^(l_out|result_norm|result_output)(-[0-9]+)?$";
    int base=0,call=0,rows=0;size_t files=0,total=0,max_bytes=1024ULL*1024*1024;
    std::vector<int> input;
    json geometry=json::array();
    static json shape(ggml_tensor*t){return{{"name",t->name},{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},
        {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};}
    static bool callback(ggml_tensor*t,bool ask,void*data){
        auto&o=*static_cast<Observer*>(data);
        try{
            if(!o.heavy)return false;
            const std::string name=t->name;
            bool geom=name.rfind("hs_",0)==0||name.rfind("kq",0)==0;
            bool want=o.trace&&std::regex_match(name,std::regex(o.pattern));
            if(!geom&&!want)return false;
            json j=shape(t);const char*b=hs_b570_tensor_backend(o.ctx,t);
            j["scheduler_backend"]=b?json(b):json(nullptr);
            j["backend_evidence"]="scheduler assignment; not pipeline/shader identity";
            j["phase"]=o.phase;j["call"]=o.call;j["caller_base"]=o.base;j["caller_ids"]=o.input;
            j["evaluation_observed"]=!ask;j["sources"]=json::array();
            for(auto*s:t->src)if(s)j["sources"].push_back(shape(s));
            if(ask){if(geom){need(b,"missing scheduler assignment");o.geometry.push_back(j);}return want;}
            need(want,"unrequested tensor callback");
            size_t n=ggml_nbytes(t);need(n<=o.max_bytes-o.total,"trace storage reservation exhausted");
            std::vector<uint8_t>v(n);ggml_backend_tensor_get(t,v.data(),0,n);
            std::string file=std::to_string(o.files++)+".bin";bytes(o.root/"trace"/file,v.data(),n);o.total+=n;
            j["file"]=file;j["bytes"]=n;
            j["operand_provenance"]="output captured at producer completion; source descriptors are NOT saved pre-consumer operands";
            j["op_params_i32"]=std::vector<int32_t>(t->op_params,t->op_params+GGML_MAX_OP_PARAMS/sizeof(int32_t));
            if(t->op==GGML_OP_ROPE&&t->src[1]&&t->src[1]->type==GGML_TYPE_I32&&t->src[1]->op==GGML_OP_NONE&&ggml_is_contiguous(t->src[1])){
                std::vector<int32_t>pos(ggml_nelements(t->src[1]));ggml_backend_tensor_get(t->src[1],pos.data(),0,pos.size()*4);j["rope_positions"]=pos;
            }
            dump(o.root/"trace"/(std::to_string(o.files-1)+".json"),j);return true;
        }catch(const std::exception&e){o.failed=true;o.error=e.what();return false;}
    }
};
struct Context{
    llama_context*c=nullptr;llama_model*m;Observer obs;int layout,nv;bool capture;fs::path root;
    Context(llama_model*model,int ub,int mode,bool heavy,const fs::path&dir,bool trace=false,std::string pattern=""):
        m(model),layout(mode),nv(llama_vocab_n_tokens(llama_model_get_vocab(model))),capture(heavy),root(dir){
        auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=1024;p.n_ubatch=ub;
        p.n_threads=config.at("threads");p.n_threads_batch=config.at("threads");
        p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;
        p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;p.offload_kqv=true;
        obs.root=dir;obs.heavy=heavy;obs.trace=trace;if(!pattern.empty())obs.pattern=pattern;
        obs.max_bytes=config.value("trace_bytes_per_request",1024ULL*1024*1024);
        if(heavy){p.cb_eval=Observer::callback;p.cb_eval_user_data=&obs;}
        c=llama_init_from_model(model,p);need(c,"context initialization");obs.ctx=c;
    }
    ~Context(){if(c)llama_free(c);}
    Context(const Context&)=delete;
    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase){
        safety();need(!ids.empty()&&ids.size()<=1024,"caller size");obs.phase=phase;obs.base=pos;obs.input=ids;obs.rows=int(ids.size());obs.call++;
        auto batch=llama_batch_init(int(ids.size()),0,1);batch.n_tokens=int(ids.size());
        for(int i=0;i<batch.n_tokens;i++){batch.token[i]=ids[i];batch.pos[i]=pos+i;batch.n_seq_id[i]=1;batch.seq_id[i][0]=0;batch.logits[i]=all||i==batch.n_tokens-1;}
        int rc;{Scope scope(layout);rc=llama_decode(c,batch);llama_synchronize(c);}llama_batch_free(batch);
        need(rc==0,"decode failure");if(obs.failed)throw std::runtime_error(obs.error);
    }
    std::vector<float>vector(int row,const std::string&name){
        float*p=llama_get_logits_ith(c,row);need(p,"logit ownership");std::vector<float>v(p,p+nv);
        for(float f:v)need(std::isfinite(f),"nonfinite logit");if(capture)bytes(root/(name+".f32"),v.data(),v.size()*4);return v;
    }
    int sample(int row,const std::string&name){auto v=vector(row,name);return int(std::max_element(v.begin(),v.end())-v.begin());}
    void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"KV trim");}
    int minimum(){return llama_memory_seq_pos_min(llama_get_memory(c),0);}
    int maximum(){return llama_memory_seq_pos_max(llama_get_memory(c),0);}
    std::vector<uint8_t>state(){llama_synchronize(c);size_t n=llama_state_seq_get_size(c,0);std::vector<uint8_t>v(n);need(n&&llama_state_seq_get_data(c,v.data(),n,0)==n,"sequence snapshot");return v;}
    void restore(const std::vector<uint8_t>&v,int lo,int hi){need(llama_state_seq_set_data(c,v.data(),v.size(),0)==v.size(),"sequence restore");need(minimum()==lo&&maximum()==hi,"restored positions");need(state()==v,"actual restore readback differs");}
};
struct Probe{std::vector<std::vector<float>>q1,q4;json record;};
Probe probe(Context&source,const std::vector<int>&ids,int base,const fs::path&dir,bool trace,std::string pattern){
    Probe p;auto s=source.state();int lo=source.minimum(),hi=source.maximum();bytes(dir/"source.state",s.data(),s.size());
    p.record={{"state_origin","actual candidate pre-verification state, NOT canonical R"},{"verify_ids",ids},{"actual_query_width",ids.size()},{"consumer_capacity",4},{"base",base},{"min",lo},{"max",hi},
        {"diagnostic_only",true},{"opaque_cross_backend_transfer",false}};
    {Context c(source.m,4,source.layout,true,dir/"q4",trace,pattern);c.restore(s,lo,hi);safety();c.decode(ids,base,true,"VERIFY");
        for(size_t j=0;j<ids.size();j++)p.q4.push_back(c.vector(int(j),"row-"+std::to_string(j)));dump(dir/"q4_geometry.json",c.obs.geometry);}
    {Context c(source.m,1,0,true,dir/"q1",trace,pattern);c.restore(s,lo,hi);safety();
        for(size_t j=0;j<ids.size();j++){c.decode({ids[j]},base+int(j),false,"VERIFY");p.q1.push_back(c.vector(-1,"row-"+std::to_string(j)));}dump(dir/"q1_geometry.json",c.obs.geometry);}
    need(source.state()==s,"probe mutated live source");p.record["live_source_unchanged"]=true;
    p.record["source_semantics"]="rows after a rejected draft prefix are conditional replay, not natural-reference outputs";return p;
}
json request(llama_model*t,llama_model*d,const json&s,const fs::path&dir){
    const auto x=s.at("input");auto prompt=x.at("prompt_ids").get<std::vector<int>>();std::string arm=s.at("arm");
    bool heavy=s.at("observer")=="heavy",spec=arm.rfind("C_",0)==0,trace=s.value("trace",false);
    need(arm=="R"||arm=="M_PQ"||arm=="M_QB"||arm=="C_PQ"||arm=="C_QB","unknown arm");
    need(!HS_COMPANION_ORACLE||arm=="R","oracle executes R only");
    int mode=arm=="R"?0:arm.find("QB")!=std::string::npos?2:1;
    int chosen=s.value("probe_cycle",-1);need((!trace&&chosen<0)||s.at("stage")=="diagnostic","probes are diagnostic only");
    need(!trace||heavy,"trace needs heavy observation");need(x.at("cap")==128&&prompt.size()+132<=1024,"request extent");
    std::string pattern=s.value("trace_pattern",std::string("^(l_out|result_norm|result_output)(-[0-9]+)?$"));
    std::vector<int>out;std::vector<bool>eog;json r={{"slot",s},{"cycles",json::array()},{"input_id",x.at("id")},{"prompt_ids",prompt},{"diagnostic",trace||chosen>=0}};
    auto begin=Clock::now();
    {
        Context target(t,mode?4:1,mode,heavy,dir/"target",trace,pattern);
        std::unique_ptr<Context>draft;if(spec)draft=std::make_unique<Context>(d,1,0,heavy,dir/"draft");
        target.decode(prompt,0,false,"PREFILL");if(draft)draft->decode(prompt,0,false,"PREFILL");
        const auto*v=llama_model_get_vocab(t);int pending=target.sample(-1,"initial"),base=int(prompt.size()),cycle=0;
        auto emit=[&](int token){out.push_back(token);eog.push_back(llama_vocab_is_eog(v,token));return eog.back()||out.size()==128;};
        bool done=emit(pending);
        while(!done){
            if(!spec){target.decode({pending},base++,false,"ORDINARY");pending=target.sample(-1,"ordinary-"+std::to_string(out.size()));done=emit(pending);continue;}
            draft->trim(base);draft->decode({pending},base,false,"DRAFT_SYNC");std::vector<int>proposals;
            for(int j=0;j<3;j++){int p=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(p);draft->decode({p},base+1+j,false,"PROPOSE");}
            std::vector<int>verify{pending};verify.insert(verify.end(),proposals.begin(),proposals.end());Probe p;
            if(cycle==chosen)p=probe(target,verify,base,dir/"probe",trace,pattern);
            target.decode(verify,base,true,"VERIFY");std::vector<int>decisions;
            bool own=true;
            for(size_t j=0;j<verify.size();j++){
                auto vec=target.vector(int(j),"verify-"+std::to_string(cycle)+"-"+std::to_string(j));
                decisions.push_back(int(std::max_element(vec.begin(),vec.end())-vec.begin()));
                if(cycle==chosen)own=own&&vec.size()==p.q4[j].size()&&std::memcmp(vec.data(),p.q4[j].data(),vec.size()*4)==0;
            }
            if(cycle==chosen){p.record["own_q4_full_vectors_equal"]=own;dump(dir/"probe"/"CONTROL.json",p.record);need(own,"same-state q4 own-path replay failed");}
            auto selected=hs_cycle::select(proposals,decisions,128-int(out.size()),[&](int z){return llama_vocab_is_eog(v,z);});
            size_t offset=out.size();for(int z:selected.emitted)done=emit(z);
            pending=selected.emitted.back();int keep=base+1+selected.accepted;target.trim(keep);draft->trim(keep);
            r["cycles"].push_back({{"cycle",cycle},{"base",base},{"verify_ids",verify},{"proposals",proposals},{"decisions",decisions},
                {"accepted",selected.accepted},{"bonus",selected.bonus},{"output_begin",offset},{"emitted",selected.emitted},{"keep",keep},
                {"target_kv_max",target.maximum()},{"draft_kv_max",draft->maximum()}});
            base=keep;cycle++;
        }
        r["geometry"]=target.obs.geometry;r["target_kv_max"]=target.maximum();r["draft_kv_max"]=draft?json(draft->maximum()):json(nullptr);
        if(heavy){auto a=target.state();bytes(dir/"target_final.state",a.data(),a.size());if(draft){auto b=draft->state();bytes(dir/"draft_final.state",b.data(),b.size());}}
    } // Context creation, all compute, recovery, synchronization and teardown are inside clean service clock.
    r["service_seconds"]=elapsed(begin);r["performance_eligible"]=!heavy&&!trace&&chosen<0;
    r["ids"]=out;r["eog"]=eog;r["length"]=out.size();r["terminal_id"]=out.back();r["stop_reason"]=eog.back()?"EOG":"CAP";
    r["probe_executed"]=chosen>=0&&std::any_of(r["cycles"].begin(),r["cycles"].end(),[&](const json&c){return c["cycle"]==chosen;});
    need(chosen<0||r["probe_executed"].get<bool>(),"selected probe cycle not reached; preserve actual request");return r;
}
int main(int argc,char**argv){
    llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;json result={{"status","STARTED"},{"records",json::array()}};
    auto clean=[&](){hs_b570_set_layout(0);if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
    try{
        need(argc==4||argc==5,"worker CONFIG OUT SLOTS [--admit]");config=load(argv[1]);root=argv[2];need(!fs::exists(root),"fresh native output required");fs::create_directories(root);
        bool admit=argc==5;need(!admit||std::string(argv[4])=="--admit","unknown option");auto slots=load(argv[3]);worker_start=Clock::now();
        ggml_backend_load_all();llama_backend_init();initialized=true;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto*d0=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d0)).find("B570")!=std::string::npos){need(!device,"ambiguous B570");device=d0;}}
        need(device,"B570 Vulkan device absent");ggml_backend_dev_t devices[]={device,nullptr};
        auto mp=llama_model_default_params();mp.devices=devices;mp.split_mode=LLAMA_SPLIT_MODE_NONE;mp.n_gpu_layers=config.at("target_gpu_layers");
        t=llama_model_load_from_file(config.at("target").get<std::string>().c_str(),mp);need(t,"target load");
        mp.n_gpu_layers=config.at("draft_gpu_layers");d=llama_model_load_from_file(config.at("draft").get<std::string>().c_str(),mp);need(d,"draft load");
        need(llama_model_n_layer(t)==32&&llama_model_n_embd(t)==4096,"exact Llama8B structure");
        auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==128256&&llama_vocab_n_tokens(dv)==128256,"vocab size");
        for(int i=0;i<128256;i++)need(std::strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocabulary/EOG identity");
        // Admission must cover the same post-load, pre-context gate as execution.
        safety();
        if(admit){Context c(t,4,0,false,root/"capacity"),draft(d,1,0,false,root/"capacity_draft");
            if(config.value("reserve_shadow_context",true)){Context shadow(t,4,0,false,root/"shadow");safety();}else safety();
            result["model_requests"]=0;result["status"]="RESOURCE_ADMITTED";
        }else{
            for(const auto&s:slots){auto rel=s.at("id").get<std::string>();need(rel.find("..") == std::string::npos&&!fs::path(rel).is_absolute(),"slot path");
                auto r=request(t,d,s,root/rel);dump(root/(rel+".json"),r);result["records"].push_back(rel+".json");dump(root/"result.json",result);
                std::cout<<json({{"event","REQUEST_COMPLETED"},{"id",rel}}).dump()<<'\n'<<std::flush;}
            result["model_requests"]=result["records"].size();result["status"]="COMPLETE";
        }
        clean();result["normal_cleanup_returned"]=true;result["resource_samples"]=resource_samples;dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){result["status"]="FAILED";result["error"]=e.what();clean();result["normal_cleanup_returned"]=true;result["resource_samples"]=resource_samples;if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<'\n';return 2;}
}
