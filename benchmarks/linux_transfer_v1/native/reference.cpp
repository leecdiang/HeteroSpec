// Independent deployment reference. Built only with the pristine upstream core.
// It never loads the candidate core, receives candidate logits, or widens UB1.
#include "llama.h"
#include "ggml-backend.h"
#include "ggml.h"
#include "nlohmann/json.hpp"
#include "linux_platform.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <set>
using J=nlohmann::ordered_json;
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void need(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
static double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void write_json(const fs::path& p,const J& j){need(!fs::exists(p),"output exists");fs::create_directories(p.parent_path());std::ofstream f(p);f<<j.dump(2)<<'\n';need(bool(f),"write JSON");}
static void write_bytes(const fs::path&p,const void*d,size_t n){need(!fs::exists(p),"capture exists");fs::create_directories(p.parent_path());std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(d),n);need(bool(f),"write capture");}
struct ModelDelete{void operator()(llama_model*p)const{if(p)llama_model_free(p);}};
struct ContextDelete{void operator()(llama_context*p)const{if(p)llama_free(p);}};
struct Batch {
    llama_batch b;
    Batch(const std::vector<int>&ids,int pos,bool all):b(llama_batch_init(int(ids.size()),0,1)){
        b.n_tokens=int(ids.size());
        for(size_t i=0;i<ids.size();++i){b.token[i]=ids[i];b.pos[i]=pos+int(i);b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||i+1==ids.size();}
    }
    ~Batch(){llama_batch_free(b);}
    Batch(const Batch&)=delete;Batch&operator=(const Batch&)=delete;
};
static void decode(llama_context*c,const std::vector<int>&ids,int pos,bool all=false){
    need(!ids.empty(),"empty decode");Batch b(ids,pos,all);need(llama_decode(c,b.b)==0,"reference decode failed");llama_synchronize(c);
}
static std::vector<float> logits(llama_context*c,int nv){const float*p=llama_get_logits_ith(c,-1);need(p,"reference logits missing");return {p,p+nv};}
static int greedy(const std::vector<float>&v){
    need(!v.empty(),"empty logits");int best=0;
    for(size_t i=0;i<v.size();++i){need(std::isfinite(v[i]),"nonfinite logits");if(v[i]>v[best])best=int(i);}return best;
}
static void capture(llama_context*c,const fs::path&dir,const std::vector<float>&v,bool state){
    write_bytes(dir/"frontier.f32",v.data(),v.size()*sizeof(float));
    if(state){size_t n=llama_state_seq_get_size(c,0);std::vector<uint8_t>b(n);need(llama_state_seq_get_data(c,b.data(),n,0)==n,"reference state capture");write_bytes(dir/"sequence.bin",b.data(),b.size());}
}
static bool contains(const std::vector<int>&v,int x){return std::find(v.begin(),v.end(),x)!=v.end();}
static void token_check(const std::vector<int>&v,int nv){for(int x:v)need(x>=0&&x<nv,"invalid input token");}
int main(int argc,char**argv){try{
    need(argc==3,"reference JOB.json OUT");std::ifstream jf(argv[1]);need(bool(jf),"job input");J job;jf>>job;
    fs::path out=argv[2];need(!fs::exists(out),"fresh output directory required");fs::create_directories(out);
    const int cap=job.value("n_ctx",1024),threads=job.value("threads",8);
    need(cap==1024 && threads>0,"Phase one reference is C1024; context expansion is a new deployment");
    ggml_time_init();llama_backend_init();ggml_backend_dev_t gpu=nullptr;
    for(size_t i=0;i<ggml_backend_dev_count();++i){auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"exactly one visible GPU required");gpu=d;}}
    need(gpu,"no GPU; CPU test is not a deployment reference");ggml_backend_dev_t devices[]={gpu,nullptr};
    auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
    auto began=Clock::now();std::unique_ptr<llama_model,ModelDelete> model(llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp));need(bool(model),"reference model");
    auto cp=llama_context_default_params();cp.n_ctx=cap;cp.n_batch=cap;cp.n_ubatch=1;cp.n_seq_max=1;cp.n_outputs_max=1;cp.n_outputs_max_per_seq=1;
    cp.n_threads=threads;cp.n_threads_batch=threads;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
    std::unique_ptr<llama_context,ContextDelete> ctx(llama_init_from_model(model.get(),cp));need(bool(ctx),"reference context");
    const auto*vocab=llama_model_get_vocab(model.get());const int nv=llama_vocab_n_tokens(vocab);
    J result={{"schema","linux-transfer.reference.v1"},{"setup_s",seconds(began)},{"reference_kind","independent-pristine-upstream-Linux-UB1"},
        {"n_ctx",llama_n_ctx(ctx.get())},{"n_batch",llama_n_batch(ctx.get())},{"n_ubatch",llama_n_ubatch(ctx.get())},
        {"output_reserve",1},{"threads",threads},{"vocab",nv},{"modules_before",linux_transfer::modules()},{"requests",J::array()},{"cases",J::array()}};
    need(llama_n_ctx(ctx.get())==unsigned(cap)&&llama_n_ubatch(ctx.get())==1,"observed reference allocation");
    if(job.contains("cases")||job.contains("forced")){
        const J cases=job.contains("cases")?job.at("cases"):J::array({job});
        for(size_t k=0;k<cases.size();++k){const auto&c=cases[k];const std::string name=c.value("name",std::to_string(k));need(!name.empty()&&name!=".."&&name.find('/')==std::string::npos&&name.find('\\')==std::string::npos,"safe case name");fs::path dir=out/name;llama_memory_clear(llama_get_memory(ctx.get()),true);llama_synchronize(ctx.get());
            const auto wanted=c.at("observe_positions").get<std::vector<int>>();const auto states=c.at("state_positions").get<std::vector<int>>();int pos=0;
            for(const auto&call:c.at("forced")){auto ids=call.at("ids").get<std::vector<int>>();token_check(ids,nv);need(!ids.empty()&&pos+int(ids.size())<=cap,"forced bounds");
                if(call.value("phase",std::string("VERIFY"))=="PREFILL"){
                    need(pos==0,"reference producer must be the initial whole caller");decode(ctx.get(),ids,0);pos+=int(ids.size());if(contains(wanted,pos))capture(ctx.get(),dir/"captures"/std::to_string(pos),logits(ctx.get(),nv),contains(states,pos));
                }else for(int id:ids){decode(ctx.get(),{id},pos);++pos;if(contains(wanted,pos))capture(ctx.get(),dir/"captures"/std::to_string(pos),logits(ctx.get(),nv),contains(states,pos));}
            }
            result["cases"].push_back({{"name",c.value("name",std::to_string(k))},{"materialized_tokens",pos}});
        }
    }else{
        for(const auto&entry:job.at("inputs")){
            const auto input=entry.at("input");const std::string name=entry.at("name");need(!name.empty()&&name.find('/')==std::string::npos&&name.find('\\')==std::string::npos&&name!="..","safe request name");
            const auto ids=input.at("prompt_ids").get<std::vector<int>>();const int limit=input.at("cap");const bool heavy=entry.value("capture",false);
            token_check(ids,nv);need(!ids.empty()&&limit>0&&limit<=128&&ids.size()+size_t(limit)<=size_t(cap),"reference input capacity");
            auto t=Clock::now();llama_memory_clear(llama_get_memory(ctx.get()),true);llama_synchronize(ctx.get());decode(ctx.get(),ids,0);int pos=int(ids.size());
            J emitted=J::array(),eog=J::array();std::vector<float> v=logits(ctx.get(),nv);
            const auto state_positions=entry.value("state_positions",std::vector<int>{});
            for(int n=0;n<limit;++n){
                const int token=greedy(v);const bool stop=llama_vocab_is_eog(vocab,token);
                if(heavy)capture(ctx.get(),out/name/"captures"/std::to_string(pos),v,n==0||stop||n+1==limit||contains(state_positions,pos));
                emitted.push_back(token);eog.push_back(stop);
                if(stop||n+1==limit)break;decode(ctx.get(),{token},pos);++pos;v=logits(ctx.get(),nv);
            }
            const double elapsed=seconds(t);J rec={{"ids",emitted},{"eog",eog},{"cap",limit},{"pending_id",emitted.back()},{"pending_position",pos},{"materialized_tokens",pos},
                {"terminal_kind",eog.back().get<bool>()?"EOG":"CAP"},{"state_capture_policy","initial/terminal plus explicitly requested logical positions"},{"service_s",elapsed},{"heavy",heavy}};
            write_json(out/name/"receipt.json",rec);result["requests"].push_back({{"name",name},{"record",name+"/receipt.json"}});
            std::cout<<"LINUX_RESULT_READY "<<name<<'\n'<<std::flush;
        }
    }
    result["modules_after"]=linux_transfer::modules();result["status"]="COMPLETE";write_json(out/"result.json",result);
    ctx.reset();model.reset();llama_backend_free();return 0;
}catch(const std::exception&e){std::cerr<<"REFERENCE_FAILURE "<<e.what()<<'\n';return 2;}}
