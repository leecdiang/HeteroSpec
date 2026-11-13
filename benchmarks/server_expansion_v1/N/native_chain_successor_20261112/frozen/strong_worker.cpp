#define NOMINMAX
#include "linux_platform.hpp"
#include "linux_platform.hpp"
extern "C" {
#include "hash/sha256/sha256.h"
}
#include <ctime>
#include <cerrno>
#include <unistd.h>
#include <fcntl.h>
#include "llama.h"
#include "target_capture.hpp"
#include "ggml-backend.h"
#include "hs_scope.h"
#include "hsc_counter.h"
#include "arm_spec.h"
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

static void need(bool v,const char*m){if(!v)throw std::runtime_error(m);}
static double since(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void dump(const fs::path&p,const json&j){
    auto tmp=p;tmp+=".tmp";
    {std::ofstream f(tmp);f<<j.dump(2)<<'\n';f.flush();need(bool(f),"write JSON");}
    int fd=::open(tmp.c_str(),O_RDONLY);need(fd>=0,"open JSON for sync");
    const int synced=::fsync(fd);const int closed=::close(fd);need(synced==0&&closed==0,"sync JSON");
    need(::rename(tmp.c_str(),p.c_str())==0,"atomic JSON replace");
    fd=::open(p.parent_path().c_str(),O_RDONLY|O_DIRECTORY);need(fd>=0,"open output directory");
    const int synced_dir=::fsync(fd);const int closed_dir=::close(fd);need(synced_dir==0&&closed_dir==0,"sync output directory");
}
static json load(const fs::path&p){std::ifstream f(p);json j;f>>j;need(bool(f),"read JSON");return j;}
static std::string utc_now(){
    const auto now=std::chrono::system_clock::now();
    const auto stamp=std::chrono::system_clock::to_time_t(now);
    std::tm t{};need(gmtime_r(&stamp,&t)!=nullptr,"UTC conversion");
    char value[48];const auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count()%1000;
    snprintf(value,sizeof(value),"%04d-%02d-%02dT%02d:%02d:%02d.%03lldZ",t.tm_year+1900,t.tm_mon+1,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec,static_cast<long long>(ms));return value;
}
struct Sha256 {
    sha256_t state;
    Sha256(){sha256_init(&state);}
    void update(const char* data,size_t size){sha256_update(&state,reinterpret_cast<const unsigned char*>(data),size);}
    std::string finish(){unsigned char bytes[32];sha256_final(&state,bytes);const char* hex="0123456789abcdef";std::string out;for(auto b:bytes){out+=hex[b>>4];out+=hex[b&15];}return out;}
};
static std::string hash_text(const std::string& text){Sha256 h;h.update(text.data(),text.size());return h.finish();}
static std::string hash_file(const fs::path& path){std::ifstream f(path,std::ios::binary);need(bool(f),"hash file open");Sha256 h;std::vector<char> block(1024*1024);while(f){f.read(block.data(),block.size());h.update(block.data(),size_t(f.gcount()));}need(f.eof(),"hash file read");return h.finish();}
inline bool phase_observe=false;
inline int phase_threads=2;
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
        auto&o=*static_cast<Observer*>(opaque);if(!phase_observe)return false;
        if(!ask){o.bad=true;return false;}
        if(o.phase!="VERIFY" && o.phase!="PREFILL" && o.phase!="ORDINARY")return false;
        std::string name=t->name;
        if(name.rfind("kq",0)!=0&&name.rfind("hs_",0)!=0&&t->op!=GGML_OP_MUL_MAT)return false;
        auto j=meta(t);j["phase"]=o.phase;j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
        for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(meta(t->src[i]));
        j["caller_rows"]=o.caller;j["first_position"]=o.base;
        j["visible_keys_by_causal_row"]=json::array();for(int i=0;i<o.caller;i++)j["visible_keys_by_causal_row"].push_back(o.base+i+1);
        j["visible_keys_basis"]="registered causal positions; tensor extents and mask strides observed separately";
        auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
        if(!d||ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_GPU)o.bad=true;
        auto key=j.dump();o.signatures[key]=std::move(j);return false;
    }
};
#include "resident_context.hpp"
#define draft_ubatch phase_draft_width
struct Context {
    PhaseContext plan;
    llama_context*c=nullptr;llama_model*model;bool target,capture,scoped;const int selector,ub;Observer obs;
    json caller_trace=json::array();fs::path path;int calls=0;std::map<std::string,double> phases;json physical_by_phase=json::object();
    Context(llama_model*m,int ub,bool istarget,bool scope,bool cap,const fs::path&dir,int layout,int draft_physical=1):model(m),target(istarget),capture(cap),scoped(scope),selector(layout),ub(ub),path(dir){
        hs_scope::requested_layout=selector;
        hs_scope::active=scoped;
        auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=1024;p.n_ubatch=istarget?ub:phase_draft_width;
        p.n_threads=phase_threads;p.n_threads_batch=phase_threads;p.n_outputs_max=istarget?phase_target_reserve:1;p.n_outputs_max_per_seq=istarget?phase_target_reserve:1;
        p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
        p.cb_eval=Observer::callback;p.cb_eval_user_data=&obs;if(cap)fs::create_directories(dir);
        hs_scope::active=false;c=llama_init_from_model(m,p);need(c,"context initialization");hs_scope::active=scoped;
    }
    ~Context(){if(c)llama_free(c);}
    void reset(bool cap,const fs::path&dir){plan.clear();capture=cap;path=dir;calls=0;caller_trace=json::array();phases.clear();physical_by_phase=json::object();obs=Observer{};if(cap)fs::create_directories(dir);hs_scope::requested_layout=selector;hs_scope::active=scoped;llama_memory_clear(llama_get_memory(c),false);need(llama_memory_seq_pos_max(llama_get_memory(c),0)<0,"KV not empty after reset");}

    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase){
        if(target){if(capture)caller_trace.push_back({{"phase",phase},{"position",pos},{"rows",ids.size()},{"all_outputs",all}});plan.decode(*this,ids,pos,all,phase);return;}
        if(capture)caller_trace.push_back({{"phase",phase},{"position",pos},{"rows",ids.size()},{"all_outputs",all}});obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());hs_scope::requested_layout=selector;hs_scope::active=scoped;
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
        auto*p=target?plan.logits(row):llama_get_logits_ith(c,row);need(p,"logits missing");int n=llama_vocab_n_tokens(llama_model_get_vocab(model));
        int best=0;for(int i=0;i<n;i++){need(std::isfinite(p[i]),"nonfinite logit");if(p[i]>p[best])best=i;}
        if(capture){++phase_heavy_captures;std::ofstream f(path/(name+".f32"),std::ios::binary);f.write((char*)p,size_t(n)*sizeof(float));need(bool(f),"full logits write");}
        return best;
    }
    void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"KV trim failed");}

    void snapshot(const std::string & key,int row) {
        if (!capture || !target) return;
        ++phase_heavy_captures;tpds_decisive::capture_existing(c,model,path/"state"/key,row,plan.logits(row));
    }
    json bounds(){auto m=llama_get_memory(c);return {{"min",llama_memory_seq_pos_min(m,0)},{"max",llama_memory_seq_pos_max(m,0)}};}
};
struct Pair {std::unique_ptr<Context> target,draft;};
static void provision(Pair& pair,llama_model*t,llama_model*d,const ArmSpec& spec,const fs::path& dir){
    need(!pair.target && !pair.draft,"pool already provisioned");
    pair.target=std::make_unique<Context>(t,spec.target_ub,true,spec.scoped,false,dir/"target",spec.selector);
    if(spec.scoped && d)pair.draft=std::make_unique<Context>(d,1,false,false,false,dir/"draft",spec.selector,draft_ubatch);
}
static json request(llama_model*t,llama_model*d,const json&input,const ArmSpec&spec,const std::string&life,bool capture,const std::string&producer,const fs::path&dir,Pair&resident){
    const auto& arm=spec.name;int k=spec.k;
    hs_scope::requested_layout=spec.selector;
    auto start=Clock::now();hsc::begin(capture?"heavy":"counts",int(input["prompt_ids"].size()));
    json r={{"arm",arm},{"k",k},{"lifecycle",life},{"cycles",json::array()},{"capture",capture},
        {"draft_enabled",spec.draft},{"observed_scope",spec.scope},{"context_scope_fixed",true},
        {"producer",producer},{"draft_producer","NATIVE"},{"draft_ubatch",draft_ubatch}};
    Pair fresh;Context*target=nullptr,*draft=nullptr;
    if(life=="resident"){
        need(bool(resident.target),"pool must be provisioned before requests");
        target=resident.target.get();
        need(target->selector==spec.selector && target->scoped==spec.scoped && target->ub==spec.target_ub,"context scope/config changed");
        target->reset(capture,dir/"target");
        if(spec.draft){need(bool(resident.draft),"draft pool missing");draft=resident.draft.get();draft->reset(capture,dir/"draft");}
    }else{
        fresh.target=std::make_unique<Context>(t,spec.target_ub,true,spec.scoped,capture,dir/"target",spec.selector);target=fresh.target.get();
        if(spec.draft){fresh.draft=std::make_unique<Context>(d,1,false,false,capture,dir/"draft",spec.selector,draft_ubatch);draft=fresh.draft.get();}
    }
    if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft width differs");
    const bool replay=phase_proposal_mode=="replay";
    need(phase_proposal_mode=="live"||replay,"transaction mode");
    need(input.contains("proposal_tape")==replay,"live/replay tape permission");
    if(replay){need(input.at("proposal_tape").at("prompt_ids")==input.at("prompt_ids"),"owned tape prompt");
        need(hash_text(input.at("proposal_tape").dump())==input.at("proposal_tape_sha256"),"owned tape content SHA");}
    need(input.at("prompt_ids").size()+size_t(input.at("cap").get<int>())+size_t(k+1)<=llama_n_ctx(target->c),"transient position capacity");
    r["proposal_mode"]=phase_proposal_mode;r["target_output_reserve"]=phase_target_reserve;
    if(replay)r["proposal_tape_sha256"]=input.at("proposal_tape_sha256");
    double setup=since(start);
    auto request_start=Clock::now();auto prompt=input["prompt_ids"].get<std::vector<int>>();
    if(producer=="P1"){for(size_t i=0;i<prompt.size();i++)target->decode({prompt[i]},int(i),false,"PREFILL");}
    else target->decode(prompt,0,false,"PREFILL");
    if(draft&&!replay)draft->decode(prompt,0,false,"PREFILL");
    int final_frontier=-1;int pending=target->sample(-1,"initial"),base=int(prompt.size()),cycle=0,cap=input["cap"];
    std::vector<int> ids;std::vector<bool> eog;const auto*v=llama_model_get_vocab(t);
    auto commit=[&](int id){ids.push_back(id);eog.push_back(llama_vocab_is_eog(v,id));return bool(eog.back())||int(ids.size())==cap;};
    if(capture)target->snapshot("initial",-1);
    bool done=commit(pending);
    while(!done){
        if(!draft){target->decode({pending},base++,false,"ORDINARY");pending=target->sample(-1,"ordinary-"+std::to_string(ids.size()));if(capture)target->snapshot("ordinary-"+std::to_string(ids.size()),-1);done=commit(pending);continue;}
        int seed=pending;auto target_before=target->bounds(),draft_before=draft->bounds();
        std::vector<int> proposals;
        if(replay){
            const auto& tape=input.at("proposal_tape");const int index=base-int(prompt.size());
            need(index>=0 && size_t(index)<tape.at("rows").size(),"owned tape base missing");
            const auto& row=tape.at("rows").at(index);
            need(row.at("base")==base&&row.at("seed")==seed&&row.at("proposals").size()>=size_t(k),"owned tape seed/base/width");
            for(int j=0;j<k;++j){int token=row.at("proposals").at(j);need(token>=0&&token<llama_vocab_n_tokens(v),"tape proposal token");proposals.push_back(token);}
        }else{
            draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
            for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);draft->decode({proposal},base+1+j,false,"PROPOSE");}
        }
        std::vector<int> verify={seed};verify.insert(verify.end(),proposals.begin(),proposals.end());
        target->decode(verify,base,true,"VERIFY");
        std::vector<int> decisions;for(int row=0;row<=k;row++)decisions.push_back(target->sample(row,"verify-"+std::to_string(cycle)+"-"+std::to_string(row)));
        int accepted=0;bool rejected=false;std::string last;
        for(int j=0;j<k&&!done;j++){
            if(decisions[j]==proposals[j]){accepted++;done=commit(proposals[j]);last="accepted";}
            else{rejected=true;pending=decisions[j];done=commit(pending);last="correction";break;}
        }
        if(accepted==k&&!done){pending=decisions[k];done=commit(pending);last="bonus";}
        int keep=base+1+accepted;target->trim(keep);if(!replay)draft->trim(keep);
        final_frontier=accepted;if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);
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
    r["target_caller_trace"]=target->caller_trace;r["draft_caller_trace"]=draft?draft->caller_trace:json::array();r["draft_physical_width_hist"]=json::object();for(size_t z=0;z<hsc::w.draft_physical.size();z++)if(hsc::w.draft_physical[z])r["draft_physical_width_hist"][std::to_string(z)]=hsc::w.draft_physical[z];r["phase_executions"]=target->plan.executions;r["target_calls"]=target->calls;r["draft_calls"]=draft?draft->calls:0;
    r["geometry"]=json::array();if(capture)for(auto&kv:target->obs.signatures)r["geometry"].push_back(kv.second);
    r["target_physical_width_hist"]=json::object();for(size_t i=0;i<hsc::w.target_physical.size();i++)if(hsc::w.target_physical[i])r["target_physical_width_hist"][std::to_string(i)]=hsc::w.target_physical[i];
    r["graphs_reused"]=hsc::w.graphs_reused;r["graphs_built"]=hsc::w.graphs_built;r["observer_mode"]=capture?"heavy":"counts";
    r["physical_widths"]=json::array();for(size_t i=0;i<hsc::w.target_physical.size();i++)if(hsc::w.target_physical[i])r["physical_widths"].push_back(i);
    r["target_physical_by_phase"]=target->physical_by_phase;
    r["setup_seconds"]=setup;
    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;
    r["teardown_seconds"]=since(teardown);
    r["endpoint"]={{"ids",r["ids"]},{"eog",r["eog"]},{"length",r["length"]},{"terminal_id",r["terminal_id"]},{"stop_reason",r["stop_reason"]}};
    r["prompt_tokens"]=prompt.size();r["prompt_ids"]=prompt;
    r["service_seconds"]=since(start);r["context_teardown_completed"]=life=="fresh";hsc::w.active=false;

    return r;
}
#ifdef _WIN32
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
        auto identity=binding.at("families").at(family);
        need(identity.at("source_variant")==HS_SOURCE_VARIANT,"binding source cohort");
        need(slots.is_array() && !slots.empty(),"empty slots");
        result["family"]=family;result["source_variant"]=HS_SOURCE_VARIANT;
        bool resident_life=family!="Llama";
        for(const auto& slot:slots){
            auto id=slot.at("slot_id").get<std::string>();
            need(!id.empty() && id.find("..") == std::string::npos && id.find(':') == std::string::npos && id.find('\\') == std::string::npos && id.front()!='/',"unsafe slot path");
            auto spec=arm_spec(slot.at("arm"));
            need(slot.at("draft_ubatch")==draft_ubatch,"draft slot mismatch");
            need(plan.at("context").at("draft_ubatch")==draft_ubatch,"draft plan mismatch");
            need(identity.at("draft_ubatch")==draft_ubatch,"draft binding mismatch");
            need(slot.at("schema")==1 && slot.at("study_id")=="tpds_decisive_rtx_draft_v1" && slot.at("family")==family,"slot identity");
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
        const auto bin=linux_transfer::executable().parent_path();
        ggml_time_init();initialized=true;
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("5070")!=std::string::npos){need(!gpu,"ambiguous GPU");gpu=x;}}
        need(gpu,"RTX5070 unavailable");result["gpu"]=ggml_backend_dev_description(gpu);
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto load_start=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");result["model_load_seconds"]=since(load_start);
        auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocabulary size");
        for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocabulary mismatch");
        HMODULE mods[1024];DWORD bytes=0;result["modules"]=json::array();
        need(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes) && bytes<=sizeof(mods),"module inventory failed");
        for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char p[32768];need(GetModuleFileNameExA(GetCurrentProcess(),mods[i],p,sizeof(p))>0,"module path missing");
            std::string name=fs::path(p).filename().string();
            json module={{"path",p},{"name",name}};
            if(identity.at("numerical_modules").contains(name)){auto h=hash_file(p);need(h==identity.at("numerical_modules").at(name),"loaded numerical module differs");module["sha256"]=h;}
            result["modules"].push_back(module);
        }
        auto pool_start=Clock::now();
        if(resident_life)for(const char* name:{"R","C_GS","C_PQ","C_QB"}){
            auto spec=arm_spec(name);auto key=pool_key(family,spec);
            provision(residents[key],t,d,spec,root/"pool");
        }
        result["resident_provisioning_seconds"]=since(pool_start);
        size_t memory_free=0,memory_total=0;ggml_backend_dev_memory(gpu,&memory_free,&memory_total);
        result["memory_after_provisioning"]={{"free_bytes",memory_free},{"total_bytes",memory_total}};
        dump(root/"PROVISIONED.json",result);
        if(admission_only){
            need(resident_life && residents.size()==4,"admission requires all four factorial pools");
            need(memory_free>=256ULL*1024*1024,"less than 256 MiB free after provisioning");
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
            r["identity"]=identity;r["context"]=plan.at("context");r["context"]["target_ub"]=spec.target_ub;r["context"]["target_outputs"]=spec.target_ub;
            r["service_timer_definition"]=plan.at("service_timer_definition");
            r["slot"]=slot;r["input_id"]=input.at("id");r["folder"]=id;
            r["prompt_ids_sha256"]=input.at("prompt_ids_sha256");
            r["family"]=family;r["source_variant"]=HS_SOURCE_VARIANT;
            dump(root/(id+".json"),r);
            result["requests"].push_back({{"slot_id",id},{"record",id+".json"}});dump(root/"result.json",result);
            std::cout<<json({{"event","REQUEST_COMPLETED"},{"slot_id",id},{"service_seconds",r["service_seconds"]}}).dump()<<std::endl;
            need(bool(std::getline(std::cin,permission)) && permission=="CONTINUE","host stopped after retained request");
        }
        result["modules_before"]=result["modules"];        result["modules"]=json::array();
        need(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes) && bytes<=sizeof(mods),"module inventory failed");
        for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char p[32768];need(GetModuleFileNameExA(GetCurrentProcess(),mods[i],p,sizeof(p))>0,"module path missing");
            std::string name=fs::path(p).filename().string();
            json module={{"path",p},{"name",name}};
            if(identity.at("numerical_modules").contains(name)){auto h=hash_file(p);need(h==identity.at("numerical_modules").at(name),"loaded numerical module differs");module["sha256"]=h;}
            result["modules"].push_back(module);
        }
        cleanup();result["status"]="COMPLETE";result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);result["process_end_utc"]=utc_now();dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){result["status"]="FAILED";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;result["native_lifetime_seconds"]=since(process_start);result["process_end_utc"]=utc_now();if(owns_root)dump(root/"result.json",result);std::cerr<<e.what()<<std::endl;return 2;}
}

#endif
