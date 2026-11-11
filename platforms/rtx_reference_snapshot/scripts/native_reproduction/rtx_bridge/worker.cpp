#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include "llama.h"
#include "ggml-backend.h"
#include "hs_scope.h"
#include "hsc_counter.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <vector>
using json=nlohmann::json; namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void need(bool v,const char*m){if(!v)throw std::runtime_error(m);}
static double since(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void dump(const fs::path&p,const json&j){auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp);f<<j.dump(2)<<'\n';f.flush();need(bool(f),"write JSON");}for(int attempt=0;attempt<100;attempt++){if(MoveFileExW(tmp.c_str(),p.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))return;DWORD error=GetLastError();if(error!=ERROR_SHARING_VIOLATION&&error!=ERROR_ACCESS_DENIED)throw std::runtime_error("atomic replace error "+std::to_string(error));Sleep(20);}throw std::runtime_error("atomic replace sharing timeout");}
static json load(const fs::path&p){std::ifstream f(p);json j;f>>j;need(bool(f),"read JSON");return j;}
struct Observer {
    std::string phase="setup";int base=0,caller=0;bool bad=false;
    std::map<std::string,json> signatures;
    static json meta(ggml_tensor*t){
        json j={{"name",t->name},{"type",ggml_type_name(t->type)},
                {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
                {"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};
        auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
        j["device"]=d?ggml_backend_dev_description(d):"UNALLOCATED";return j;
    }
    static bool callback(ggml_tensor*t,bool ask,void*opaque){
        auto&o=*static_cast<Observer*>(opaque);
        if(!ask){o.bad=true;return false;}
        if(o.phase!="VERIFY")return false;
        std::string name=t->name;
        if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0)return false;
        auto j=meta(t);j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
        for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(meta(t->src[i]));
        j["caller_rows"]=o.caller;j["first_position"]=o.base;
        j["visible_keys_by_causal_row"]=json::array();for(int i=0;i<o.caller;i++)j["visible_keys_by_causal_row"].push_back(o.base+i+1);
        j["visible_keys_basis"]="registered causal positions; tensor extents and mask strides observed separately";
        auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
        if(!d||std::string(ggml_backend_dev_description(d)).find("5070") == std::string::npos)o.bad=true;
        auto key=j.dump();o.signatures[key]=std::move(j);return false;
    }
};
struct Context {
    llama_context*c=nullptr;llama_model*model;bool target,capture,scoped;Observer obs;
    fs::path path;int calls=0;std::map<std::string,double> phases;
    Context(llama_model*m,int ub,bool istarget,bool scope,bool cap,const fs::path&dir):model(m),target(istarget),capture(cap),scoped(scope),path(dir){
        hs_scope::active=scoped;
        auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=1024;p.n_ubatch=ub;
        p.n_threads=24;p.n_threads_batch=24;p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;
        p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
        p.cb_eval=Observer::callback;p.cb_eval_user_data=&obs;if(cap)fs::create_directories(dir);
        c=llama_init_from_model(m,p);need(c,"context initialization");
    }
    ~Context(){if(c)llama_free(c);}
    void reset(bool cap,const fs::path&dir){capture=cap;path=dir;calls=0;phases.clear();obs=Observer{};if(cap)fs::create_directories(dir);hs_scope::active=scoped;llama_memory_clear(llama_get_memory(c),false);need(llama_memory_seq_pos_max(llama_get_memory(c),0)<0,"KV not empty after reset");}

    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase){
        obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());hs_scope::active=scoped;
        auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
        for(int i=0;i<b.n_tokens;i++){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||i==b.n_tokens-1;}
        hsc::decode_begin(c,target?"target":"draft",std::string(phase)=="PREFILL",b.n_tokens);
        auto t=Clock::now();int rc=llama_decode(c,b);llama_batch_free(b);
        need(rc==0,"decode failed");llama_synchronize(c);phases[phase]+=since(t);hsc::decode_end();calls++;
        need(!obs.bad,"observer/placement failed");
    }
    int sample(int row,const std::string&name){
        auto*p=llama_get_logits_ith(c,row);need(p,"logits missing");int n=llama_vocab_n_tokens(llama_model_get_vocab(model));
        int best=0;for(int i=0;i<n;i++){need(std::isfinite(p[i]),"nonfinite logit");if(p[i]>p[best])best=i;}
        if(capture){std::ofstream f(path/(name+".f32"),std::ios::binary);f.write((char*)p,size_t(n)*sizeof(float));need(bool(f),"full logits write");}
        return best;
    }
    void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"KV trim failed");}
    json bounds(){auto m=llama_get_memory(c);return {{"min",llama_memory_seq_pos_min(m,0)},{"max",llama_memory_seq_pos_max(m,0)}};}
};
struct Pair {std::unique_ptr<Context> target,draft;};
static json request(llama_model*t,llama_model*d,const json&input,const std::string&arm,int k,const std::string&life,bool capture,bool counters,const fs::path&dir,Pair&resident){
    hs_scope::requested_layout=arm=="QB"?0:1;
    double provisioning=0;
    if(life=="resident"&&!resident.target){auto p=Clock::now();resident.target=std::make_unique<Context>(t,4,true,true,false,dir/"target");resident.draft=std::make_unique<Context>(d,1,false,false,false,dir/"draft");provisioning=since(p);}
    auto start=Clock::now();hsc::begin(capture?"heavy":counters?"counts":"baseline",int(input["prompt_ids"].size()));
    json r={{"arm",arm},{"k",k},{"lifecycle",life},{"cycles",json::array()},{"capture",capture},{"counters",counters}};
    Pair fresh;Context*target=nullptr,*draft=nullptr;
    if(life=="resident"){target=resident.target.get();draft=resident.draft.get();target->reset(capture,dir/"target");draft->reset(capture,dir/"draft");}
    else{fresh.target=std::make_unique<Context>(t,arm=="R"?1:4,true,arm!="R",capture,dir/"target");target=fresh.target.get();if(arm!="R"){fresh.draft=std::make_unique<Context>(d,1,false,false,capture,dir/"draft");draft=fresh.draft.get();}}
    double setup=since(start);
    auto request_start=Clock::now();auto prompt=input["prompt_ids"].get<std::vector<int>>();
    target->decode(prompt,0,false,"PREFILL");if(draft)draft->decode(prompt,0,false,"PREFILL");
    int pending=target->sample(-1,"initial"),base=int(prompt.size()),cycle=0,cap=input["cap"];
    std::vector<int> ids;std::vector<bool> eog;const auto*v=llama_model_get_vocab(t);
    auto commit=[&](int id){ids.push_back(id);eog.push_back(llama_vocab_is_eog(v,id));return bool(eog.back())||int(ids.size())==cap;};
    bool done=commit(pending);
    while(!done){
        if(!draft){target->decode({pending},base++,false,"ORDINARY");pending=target->sample(-1,"ordinary-"+std::to_string(ids.size()));done=commit(pending);continue;}
        int seed=pending;auto target_before=target->bounds(),draft_before=draft->bounds();
        draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
        std::vector<int> proposals;
        for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);draft->decode({proposal},base+1+j,false,"PROPOSE");}
        std::vector<int> verify={seed};verify.insert(verify.end(),proposals.begin(),proposals.end());
        target->decode(verify,base,true,"VERIFY");
        std::vector<int> decisions;for(int row=0;row<=k;row++)decisions.push_back(target->sample(row,"verify-"+std::to_string(cycle)+"-"+std::to_string(row)));
        int accepted=0;bool rejected=false;std::string last;
        for(int j=0;j<k&&!done;j++){
            if(decisions[j]==proposals[j]){accepted++;done=commit(proposals[j]);last="accepted";}
            else{rejected=true;pending=decisions[j];done=commit(pending);last="correction";break;}
        }
        if(accepted==k&&!done){pending=decisions[k];done=commit(pending);last="bonus";}
        int keep=base+1+accepted;target->trim(keep);draft->trim(keep);
        r["cycles"].push_back({{"cycle",cycle},{"base",base},{"seed",seed},{"proposals",proposals},{"decisions",decisions},
           {"accepted",accepted},{"rejected",rejected},{"commit_kind",last},{"output_length",ids.size()},
           {"pending_after",done?json(nullptr):json(pending)},{"done",done},{"keep",keep},
           {"target_before",target_before},{"draft_before",draft_before},{"target_after",target->bounds()},{"draft_after",draft->bounds()},
           {"caller_rows",k+1}});
        base=keep;cycle++;
    }
    llama_synchronize(target->c);if(draft)llama_synchronize(draft->c);
    r["ids"]=ids;r["eog"]=eog;r["length"]=ids.size();r["terminal_id"]=ids.back();r["stop_reason"]=eog.back()?"EOG":"CAP";
    r["target_final_kv"]=target->bounds();r["draft_final_kv"]=draft?draft->bounds():json(nullptr);
    r["request_seconds"]=since(request_start);r["target_phases"]=target->phases;r["draft_phases"]=draft?json(draft->phases):json::object();
    r["target_calls"]=target->calls;r["draft_calls"]=draft?draft->calls:0;
    r["geometry"]=json::array();if(capture)for(auto&kv:target->obs.signatures)r["geometry"].push_back(kv.second);
    r["target_physical_width_hist"]=json::object();for(size_t i=0;i<hsc::w.target_physical.size();i++)if(hsc::w.target_physical[i])r["target_physical_width_hist"][std::to_string(i)]=hsc::w.target_physical[i];
    r["graphs_reused"]=counters||capture?json(hsc::w.graphs_reused):json(nullptr);
    r["resident_provisioning_seconds"]=provisioning;r["setup_seconds"]=setup;
    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;
    r["teardown_seconds"]=since(teardown);
    r["service_seconds"]=since(start);r["context_teardown_completed"]=life=="fresh";hsc::w.active=false;
    return r;
}
static void endpoint(const json&a,const json&b,bool cycles){
    for(auto key:{"ids","eog","length","terminal_id","stop_reason"})need(a.at(key)==b.at(key),"endpoint mismatch");
    if(cycles){need(a.at("cycles")==b.at("cycles"),"cycle/state mismatch");need(a.at("target_final_kv")==b.at("target_final_kv")&&a.at("draft_final_kv")==b.at("draft_final_kv"),"final KV bounds mismatch");}
}
static void raw_equal(const fs::path&a,const fs::path&b){
    int matches=0,other=0;
    for(auto&e:fs::recursive_directory_iterator(a))if(e.is_regular_file()&&e.path().extension()==".f32"){
        auto p=b/fs::relative(e.path(),a);need(fs::exists(p),"raw counterpart missing");
        std::ifstream fa(e.path(),std::ios::binary),fb(p,std::ios::binary);
        std::vector<char>aa((std::istreambuf_iterator<char>(fa)),{}),bb((std::istreambuf_iterator<char>(fb)),{});
        need(!aa.empty()&&aa==bb,"full logits byte mismatch");matches++;
    }
    for(auto&e:fs::recursive_directory_iterator(b))if(e.is_regular_file()&&e.path().extension()==".f32")other++;
    need(matches>0&&matches==other,"raw inventory mismatch");
}

int main(int argc,char**argv){
    fs::path root;llama_model*t=nullptr,*d=nullptr;bool initialized=false;auto process_start=Clock::now();
    std::map<std::string,Pair> residents;
    json result={{"status","STARTED"},{"requests",json::array()},{"pid",GetCurrentProcessId()}};
    auto cleanup=[&](){residents.clear();if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
    try{
        need(argc==6,"worker OUT TARGET DRAFT PANEL SLOTS");root=argv[1];need(!fs::exists(root),"fresh output required");fs::create_directories(root);
        auto panel=load(argv[4]),slots=load(argv[5]);dump(root/"result.json",result);
        wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);auto bindir=fs::path(exe).parent_path();
        ggml_backend_load_all_from_path(bindir.string().c_str());llama_backend_init();initialized=true;
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("5070")!=std::string::npos){need(!gpu,"ambiguous GPU");gpu=x;}}
        need(gpu,"RTX5070 unavailable");result["gpu"]=ggml_backend_dev_description(gpu);
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto load_start=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");result["model_load_seconds"]=since(load_start);
        auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocabulary size");
        for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocabulary mismatch");
        HMODULE mods[1024];DWORD bytes=0;result["modules"]=json::array();
        if(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes))for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char p[32768];if(GetModuleFileNameExA(GetCurrentProcess(),mods[i],p,sizeof(p)))result["modules"].push_back(p);}
        for(auto&slot:slots){
            std::string id=slot.at("slot_id"),label=slot.at("label"),life=slot.at("lifecycle");int task=slot.at("task"),k=slot.at("k");
            need((k==1||k==3)&&(life=="resident"||life=="fresh"),"invalid cell");
            std::string arm=label=="QB"?"QB":label=="R"?"R":"PQ";need(arm!="R"||life=="fresh","R is fresh reference");
            dump(root/"ACTIVE_SLOT.json",slot);auto input=panel.at("inputs").at(task);
            auto r=request(t,d,input,arm,k,life,slot.at("capture"),slot.at("counters"),root/id,residents[arm]);
            r["slot"]=slot;r["input_id"]=input.at("id");r["folder"]=id;dump(root/(id+".json"),r);
            auto summary=r;summary["geometry_count"]=r["geometry"].size();summary.erase("geometry");
            result["requests"].push_back(summary);dump(root/"result.json",result);
            if(slot.contains("reference")){auto ref=load(slot.at("reference").get<std::string>());endpoint(ref,r,arm!="R");}
            std::cout<<json({{"event","REQUEST_COMPLETED"},{"slot_id",id},{"service_seconds",r["service_seconds"]}}).dump()<<std::endl;
        }
        cleanup();result["status"]="COMPLETE";result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){result["status"]="FAILED";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<std::endl;return 2;}
}
