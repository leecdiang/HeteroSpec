#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include <bcrypt.h>
#include "llama.h"
#include "ggml-backend.h"
#include "hs_scope.h"
#include "hsc_counter.h"
#include "arm_spec.h"
#include <regex>
using rtx_scope_transfer::arm_spec;
using rtx_scope_transfer::pool_key;
using rtx_scope_transfer::ArmSpec;
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
static int dense_target_layers=24;
static int dense_threads=24;
static void need(bool v,const char*m){if(!v)throw std::runtime_error(m);}
static double since(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void dump(const fs::path&p,const json&j){auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp);f<<j.dump(2)<<'\n';f.flush();need(bool(f),"write JSON");}for(int attempt=0;attempt<100;attempt++){if(MoveFileExW(tmp.c_str(),p.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))return;DWORD error=GetLastError();if(error!=ERROR_SHARING_VIOLATION&&error!=ERROR_ACCESS_DENIED)throw std::runtime_error("atomic replace error "+std::to_string(error));Sleep(20);}throw std::runtime_error("atomic replace sharing timeout");}
static json load(const fs::path&p){std::ifstream f(p);json j;f>>j;need(bool(f),"read JSON");return j;}
static std::string utc_now(){
    SYSTEMTIME t;GetSystemTime(&t);char value[40];
    snprintf(value,sizeof(value),"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds);
    return value;
}
struct Sha256 {
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    Sha256(){need(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA256 provider");need(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)==0,"SHA256 create");}
    ~Sha256(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
    void update(const char* data,size_t size){need(size<=ULONG_MAX && BCryptHashData(hash,(PUCHAR)data,ULONG(size),0)==0,"SHA256 update");}
    std::string finish(){unsigned char bytes[32];need(BCryptFinishHash(hash,bytes,32,0)==0,"SHA256 finish");const char* hex="0123456789abcdef";std::string out;for(auto b:bytes){out+=hex[b>>4];out+=hex[b&15];}return out;}
};
static std::string hash_text(const std::string& text){Sha256 h;h.update(text.data(),text.size());return h.finish();}
static std::string hash_file(const fs::path& path){std::ifstream f(path,std::ios::binary);need(bool(f),"hash file open");Sha256 h;std::vector<char> block(1024*1024);while(f){f.read(block.data(),block.size());h.update(block.data(),size_t(f.gcount()));}need(f.eof(),"hash file read");return h.finish();}
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
        if(o.phase!="VERIFY" && o.phase!="PREFILL" && o.phase!="ORDINARY")return false;
        std::string name=t->name;
        if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0)return false;
        auto j=meta(t);j["phase"]=o.phase;j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
        for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(meta(t->src[i]));
        j["caller_rows"]=o.caller;j["first_position"]=o.base;
        j["visible_keys_by_causal_row"]=json::array();for(int i=0;i<o.caller;i++)j["visible_keys_by_causal_row"].push_back(o.base+i+1);
        j["visible_keys_basis"]="registered causal positions; tensor extents and mask strides observed separately";
        auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
        // A hybrid target is permitted only with observed CPU/5070 placement.
        if(!d || (ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_CPU &&
           std::string(ggml_backend_dev_description(d)).find("5070")==std::string::npos))o.bad=true;
        std::smatch layer;std::regex layer_suffix("-([0-9]+)$");
        if(std::regex_search(name,layer,layer_suffix))j["layer"]=std::stoi(layer[1]);
        else j["layer"]=nullptr;
        j["device_type"]=d?int(ggml_backend_dev_type(d)):-1;
        auto key=j.dump();o.signatures[key]=std::move(j);return false;
    }
};
struct Context {
    llama_context*c=nullptr;llama_model*model;bool target,capture,scoped;const int selector,ub;Observer obs;
    fs::path path;int calls=0;std::map<std::string,double> phases;json physical_by_phase=json::object();
    Context(llama_model*m,int ub,bool istarget,bool scope,bool cap,const fs::path&dir,int layout):model(m),target(istarget),capture(cap),scoped(scope),selector(layout),ub(ub),path(dir){
        hs_scope::requested_layout=selector;
        hs_scope::active=scoped;
        auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=1024;p.n_ubatch=ub;
        p.n_threads=dense_threads;p.n_threads_batch=dense_threads;p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;
        p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
        p.cb_eval=Observer::callback;p.cb_eval_user_data=&obs;if(cap)fs::create_directories(dir);
        c=llama_init_from_model(m,p);need(c,"context initialization");
    }
    ~Context(){if(c)llama_free(c);}
    void reset(bool cap,const fs::path&dir){capture=cap;path=dir;calls=0;phases.clear();physical_by_phase=json::object();obs=Observer{};if(cap)fs::create_directories(dir);hs_scope::requested_layout=selector;hs_scope::active=scoped;llama_memory_clear(llama_get_memory(c),false);need(llama_memory_seq_pos_max(llama_get_memory(c),0)<0,"KV not empty after reset");}

    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase){
        obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());hs_scope::requested_layout=selector;hs_scope::active=scoped;
        auto widths_before=hsc::w.target_physical;
        auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
        for(int i=0;i<b.n_tokens;i++){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||i==b.n_tokens-1;}
        hsc::decode_begin(c,target?"target":"draft",std::string(phase)=="PREFILL",b.n_tokens);
        auto t=Clock::now();int rc=llama_decode(c,b);llama_batch_free(b);
        need(rc==0,"decode failed");llama_synchronize(c);phases[phase]+=since(t);hsc::decode_end();calls++;
        if(capture && target){for(size_t i=0;i<hsc::w.target_physical.size();i++){
            auto delta=hsc::w.target_physical[i]-widths_before[i];
            if(delta){auto key=std::to_string(i);auto & histogram=physical_by_phase[phase];
                if(histogram.is_null())histogram=json::object();
                histogram[key]=histogram.value(key,int64_t(0))+delta;}}}
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
static void provision(Pair& pair,llama_model*t,llama_model*d,const ArmSpec& spec,const fs::path& dir){
    need(!pair.target && !pair.draft,"pool already provisioned");
    pair.target=std::make_unique<Context>(t,spec.target_ub,true,spec.scoped,false,dir/"target",spec.selector);
    if(spec.scoped)pair.draft=std::make_unique<Context>(d,1,false,false,false,dir/"draft",spec.selector);
}
static json request(llama_model*t,llama_model*d,const json&input,const ArmSpec&spec,const std::string&life,bool capture,const std::string&producer,const fs::path&dir,Pair&resident){
    const auto& arm=spec.name;int k=spec.k;
    hs_scope::requested_layout=spec.selector;
    auto start=Clock::now();hsc::begin(capture?"heavy":"baseline",int(input["prompt_ids"].size()));
    json r={{"arm",arm},{"k",k},{"lifecycle",life},{"cycles",json::array()},{"capture",capture},
        {"draft_enabled",spec.draft},{"observed_scope",spec.scope},{"context_scope_fixed",true},
        {"producer",producer},{"draft_producer","NATIVE"}};
    Pair fresh;Context*target=nullptr,*draft=nullptr;
    if(life=="resident"){
        need(bool(resident.target),"pool must be provisioned before requests");
        target=resident.target.get();
        need(target->selector==spec.selector && target->scoped==spec.scoped && target->ub==spec.target_ub,"context scope/config changed");
        target->reset(capture,dir/"target");
        if(spec.draft){need(bool(resident.draft),"draft pool missing");draft=resident.draft.get();draft->reset(capture,dir/"draft");}
    }else{
        fresh.target=std::make_unique<Context>(t,spec.target_ub,true,spec.scoped,capture,dir/"target",spec.selector);target=fresh.target.get();
        if(spec.draft){fresh.draft=std::make_unique<Context>(d,1,false,false,capture,dir/"draft",spec.selector);draft=fresh.draft.get();}
    }
    double setup=since(start);
    auto request_start=Clock::now();auto prompt=input["prompt_ids"].get<std::vector<int>>();
    if(producer=="P1"){for(size_t i=0;i<prompt.size();i++)target->decode({prompt[i]},int(i),false,"PREFILL");}
    else target->decode(prompt,0,false,"PREFILL");
    if(draft)draft->decode(prompt,0,false,"PREFILL");
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
    r["graphs_reused"]=capture?json(hsc::w.graphs_reused):json(nullptr);
    r["physical_widths"]=json::array();for(size_t i=0;i<hsc::w.target_physical.size();i++)if(hsc::w.target_physical[i])r["physical_widths"].push_back(i);
    r["target_physical_by_phase"]=target->physical_by_phase;
    r["setup_seconds"]=setup;
    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;
    r["teardown_seconds"]=since(teardown);
    r["endpoint"]={{"ids",r["ids"]},{"eog",r["eog"]},{"length",r["length"]},{"terminal_id",r["terminal_id"]},{"stop_reason",r["stop_reason"]}};
    r["prompt_tokens"]=prompt.size();r["prompt_ids"]=prompt;
    r["service_seconds"]=since(start);r["context_teardown_completed"]=life=="fresh";hsc::w.active=false;
    if(capture){
        auto state_record=[&](Context* x,const char* role){
            if(!x)return;
            const auto n=llama_state_seq_get_size(x->c,0);std::vector<uint8_t> bytes(n);
            need(llama_state_seq_get_data(x->c,bytes.data(),n,0)==n,"state serialization size");
            auto file=dir/(std::string(role)+"_final.state");std::ofstream out(file,std::ios::binary);
            out.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());need(bool(out),"state write");out.close();
            r[std::string(role)+"_state"]={{"bytes",n},{"sha256",hash_file(file)}};
        };
        state_record(target,"target");state_record(draft,"draft");
    }
    return r;
}
int main(int argc,char**argv){
    fs::path root;llama_model*t=nullptr,*d=nullptr;bool initialized=false,owns_root=false;auto process_start=Clock::now();
    std::map<std::string,Pair> residents;
    json result={{"status","STARTED"},{"requests",json::array()},{"pid",GetCurrentProcessId()},{"process_start_utc",utc_now()}};
    auto cleanup=[&](){residents.clear();if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
    try{
        bool admission_only=argc==10 && std::string(argv[9])=="--admit-pools";
        need(argc==9 || admission_only,"worker OUT TARGET DRAFT PANEL SLOTS FAMILY BINDING PLAN [--admit-pools]");root=argv[1];need(!fs::exists(root),"fresh output required");need(fs::create_directories(root),"fresh output creation");owns_root=true;
        std::string family=argv[6];
        need(rtx_scope_transfer::source_variant(family)==HS_SOURCE_VARIANT,"wrong source cohort for family");
        auto panel=load(argv[4]),slots=load(argv[5]),binding=load(argv[7]),plan=load(argv[8]);
        need((binding.at("status")=="FROZEN_BEFORE_FIRST_NATIVE_REQUEST" || (admission_only && binding.at("status")=="PREPARED_RESOURCE_ADMISSION_ONLY")) && binding.at("is_synthetic")==false,"unfrozen execution");
        need(family=="Qwen","dense14b uses original Qwen source cohort");
        dense_target_layers=binding.at("dense14b").at("target_gpu_layers").get<int>();
        dense_threads=binding.at("dense14b").at("threads").get<int>();
        need(dense_target_layers>0&&dense_target_layers<40,"hybrid target layer range");
        need(dense_threads>0&&dense_threads<=128,"thread count");
        auto identity=binding.at("families").at(family);
        need(identity.at("source_variant")==HS_SOURCE_VARIANT,"binding source cohort");
        need(slots.is_array() && !slots.empty(),"empty slots");
        result["family"]=family;result["source_variant"]=HS_SOURCE_VARIANT;
        bool resident_life=family!="Llama";
        for(const auto& slot:slots){
            auto id=slot.at("slot_id").get<std::string>();
            need(!id.empty() && id.find("..") == std::string::npos && id.find(':') == std::string::npos && id.find('\\') == std::string::npos && id.front()!='/',"unsafe slot path");
            auto spec=arm_spec(slot.at("arm"));
            need(slot.at("schema")==1 && slot.at("study_id")=="rtx_dense14b_transfer_v1" && slot.at("family")==family,"slot identity");
            need(slot.at("scope")==spec.scope && slot.at("layout_selector")==spec.selector && slot.at("scoped_target")==spec.scoped,"arm scope");
            need(slot.at("target_ub")==spec.target_ub && slot.at("target_outputs")==spec.target_ub && slot.at("k")==spec.k && slot.at("draft_enabled")==spec.draft,"arm geometry/draft");
            need(slot.at("lifecycle")== (resident_life?"resident":"fresh"),"lifecycle");
            need(slot.at("observer")=="off" || slot.at("observer")=="heavy","observer");
            auto producer=slot.at("producer").get<std::string>();
            need(producer=="NATIVE" || (family=="Llama" && (producer=="P1" || producer=="P4_NATIVE")),"producer");
            auto input=panel.at("inputs").at(slot.at("source_index").get<int>());
            need(input.at("id")==slot.at("input_id") && input.at("prompt_ids_sha256")==slot.at("prompt_ids_sha256"),"native input identity");
            need(hash_text(input.at("prompt_ids").dump())==input.at("prompt_ids_sha256"),"native prompt bytes");
            need(input.at("cap")==128 && input.at("prompt_ids").size()>0 && input.at("prompt_ids").size()+132<=1024,"input capacity");
        }
        dump(root/"result.json",result);
        wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);auto bindir=fs::path(exe).parent_path();
        need(hash_file(exe)==identity.at("executable_sha256"),"executable hash differs");
        for(auto it=identity.at("numerical_modules").begin();it!=identity.at("numerical_modules").end();++it){
            need(fs::path(it.key()).filename()==it.key(),"unsafe module name");
            need(hash_file(bindir/it.key())==it.value(),"numerical module hash differs");
        }
        need(hash_file(argv[2])==identity.at("models").at("target").at("sha256") && hash_file(argv[3])==identity.at("models").at("draft").at("sha256"),"model hash differs");
        ggml_backend_load_all_from_path(bindir.string().c_str());llama_backend_init();initialized=true;
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("5070")!=std::string::npos){need(!gpu,"ambiguous GPU");gpu=x;}}
        need(gpu,"RTX5070 unavailable");result["gpu"]=ggml_backend_dev_description(gpu);
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=dense_target_layers;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto load_start=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");mp.n_gpu_layers=999;d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");need(llama_model_n_layer(t)==40&&llama_model_n_embd(t)==5120,"not 14B target geometry");
        result["placement"]={{"target_gpu_layers",dense_target_layers},{"draft_gpu_layers",999},{"threads",dense_threads}};result["model_load_seconds"]=since(load_start);
        auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocabulary size");
        for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocabulary mismatch");
        result["vocabulary_eog"]=json::array();for(int i=0;i<llama_vocab_n_tokens(tv);i++)if(llama_vocab_is_eog(tv,i))result["vocabulary_eog"].push_back(i);
        HMODULE mods[1024];DWORD bytes=0;result["modules"]=json::array();
        need(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes) && bytes<=sizeof(mods),"module inventory failed");
        for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char p[32768];need(GetModuleFileNameExA(GetCurrentProcess(),mods[i],p,sizeof(p))>0,"module path missing");
            std::string name=fs::path(p).filename().string();
            json module={{"path",p},{"name",name}};
            if(identity.at("numerical_modules").contains(name)){auto h=hash_file(p);need(h==identity.at("numerical_modules").at(name),"loaded numerical module differs");module["sha256"]=h;}
            result["modules"].push_back(module);
        }
        auto pool_start=Clock::now();
        if(resident_life)for(const char* name:{"R","C_PQ","C_QB"}){
            auto spec=arm_spec(name);auto key=pool_key(family,spec);
            provision(residents[key],t,d,spec,root/"pool");
        }
        result["resident_provisioning_seconds"]=since(pool_start);
        size_t memory_free=0,memory_total=0;ggml_backend_dev_memory(gpu,&memory_free,&memory_total);
        result["memory_after_provisioning"]={{"free_bytes",memory_free},{"total_bytes",memory_total}};
        MEMORYSTATUSEX ms{};ms.dwLength=sizeof(ms);need(GlobalMemoryStatusEx(&ms),"RAM probe failed");
        result["memory_after_provisioning"]["ram_available_bytes"]=ms.ullAvailPhys;
        need(ms.ullAvailPhys>=binding.at("dense14b").at("min_ram_free_bytes").get<unsigned long long>(),"insufficient RAM headroom");
        dump(root/"PROVISIONED.json",result);
        if(admission_only){
            need(resident_life && residents.size()==3,"admission requires three registered dense14b pools");
            need(memory_free>=binding.at("dense14b").at("min_vram_free_bytes").get<size_t>(),"insufficient frozen VRAM headroom");
            cleanup();result["status"]="RESOURCE_ADMITTED";result["new_native_requests"]=0;
            result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);
            result["process_end_utc"]=utc_now();dump(root/"result.json",result);return 0;
        }
        std::cout<<json({{"event","POOLS_READY"}}).dump()<<std::endl;
        std::string permission;
        need(bool(std::getline(std::cin,permission)) && permission=="RUN","host admission not granted");
        for(auto&slot:slots){
            auto spec=arm_spec(slot.at("arm"));
            std::string id=slot.at("slot_id"),life=slot.at("lifecycle");
            // The frozen IDs use slash-separated paths. No caller-controlled traversal.
            need(id.find("..") == std::string::npos && id.find(':') == std::string::npos && id.find('\\') == std::string::npos && id.front()!='/',"unsafe slot path");
            dump(root/"ACTIVE_SLOT.json",slot);auto input=panel.at("inputs").at(slot.at("source_index").get<int>());
            fs::create_directories((root/id).parent_path());
            auto request_start_utc=utc_now();
            auto r=request(t,d,input,spec,life,slot.at("observer")=="heavy",slot.at("producer"),root/id,residents[pool_key(family,spec)]);
            r["request_start_utc"]=request_start_utc;r["request_end_utc"]=utc_now();
            r["vocabulary_eog"]=result["vocabulary_eog"];r["identity"]=identity;r["context"]=plan.at("context");r["context"]["target_ub"]=spec.target_ub;r["context"]["target_outputs"]=spec.target_ub;
            r["service_timer_definition"]=plan.at("service_timer_definition");
            r["slot"]=slot;r["input_id"]=input.at("id");r["folder"]=id;
            r["prompt_ids_sha256"]=input.at("prompt_ids_sha256");
            r["family"]=family;r["source_variant"]=HS_SOURCE_VARIANT;
            dump(root/(id+".json"),r);
            result["requests"].push_back({{"slot_id",id},{"record",id+".json"}});dump(root/"result.json",result);
            std::cout<<json({{"event","REQUEST_COMPLETED"},{"slot_id",id},{"service_seconds",r["service_seconds"]}}).dump()<<std::endl;
            need(bool(std::getline(std::cin,permission)) && permission=="CONTINUE","host stopped after retained request");
        }
        cleanup();result["status"]="COMPLETE";result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);result["process_end_utc"]=utc_now();dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){result["status"]="FAILED";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);result["process_end_utc"]=utc_now();if(owns_root)dump(root/"result.json",result);std::cerr<<e.what()<<std::endl;return 2;}
}
