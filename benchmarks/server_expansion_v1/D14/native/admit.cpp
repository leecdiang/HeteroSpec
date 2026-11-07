#include "llama.h"
#include "llama-model.h"
#include "llama-context.h"
#include "llama-kv-cache.h"
#include "ggml-backend.h"
#include "linux_platform.hpp"
#include <nlohmann/json.hpp>
extern "C" {
#include "hash/sha256/sha256.h"
}
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <thread>
#include <vector>
using json=nlohmann::json;namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
static double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static json read(const fs::path&p){std::ifstream f(p);json j;f>>j;need(bool(f),"job JSON");return j;}
static void save(const fs::path&p,const json&j){std::ofstream f(p);f<<j.dump(2)<<'\n';f.flush();need(bool(f),"receipt write");}
struct Hash {
    sha256_t s;Hash(){sha256_init(&s);}
    void add(const char*p,size_t n){sha256_update(&s,reinterpret_cast<const unsigned char*>(p),n);}
    std::string finish(){unsigned char b[32];sha256_final(&s,b);const char*h="0123456789abcdef";std::string r;for(auto x:b){r+=h[x>>4];r+=h[x&15];}return r;}
};
static std::string file_hash(const fs::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"model hash open");Hash h;std::vector<char>b(4*1024*1024);while(f){f.read(b.data(),b.size());h.add(b.data(),size_t(f.gcount()));}need(f.eof(),"model hash read");return h.finish();}
static std::string text_hash(const char*s){Hash h;if(s)h.add(s,std::strlen(s));return h.finish();}
static ggml_tensor* storage(ggml_tensor*t){while(!t->buffer&&t->view_src)t=t->view_src;return t;}
static json tensor(ggml_tensor*t,ggml_backend_dev_t gpu){
    auto*base=storage(t);need(base->buffer,"actual allocated tensor buffer required");
    auto*dev=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(base->buffer));
    need(dev==gpu&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"CPU/other-device tensor placement disallowed");
    return {{"name",t->name},{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
        {"logical_bytes",ggml_nbytes(t)},{"device",ggml_backend_dev_description(dev)},{"buffer_type",ggml_backend_buft_name(ggml_backend_buffer_get_type(base->buffer))}};
}
static json model(llama_model*m,ggml_backend_dev_t gpu){
    json a=json::array();for(const auto&item:m->tensors_by_name){auto row=tensor(item.second,gpu);row["model_name"]=item.first;a.push_back(row);}
    need(!a.empty(),"all model tensors observed");char arch[256]={};need(llama_model_meta_val_str(m,"general.architecture",arch,sizeof(arch))>0,"actual architecture");
    return {{"architecture",arch},{"layers",m->hparams.n_layer()},{"query_heads",m->hparams.n_head()},{"KV_heads",m->hparams.n_head_kv()},
        {"head_k",m->hparams.n_embd_head_k()},{"head_v",m->hparams.n_embd_head_v()},
        {"vocab",llama_vocab_n_tokens(llama_model_get_vocab(m))},{"model_tensors",a},
        {"chat_template_sha256",text_hash(llama_model_chat_template(m,nullptr))},{"all_model_tensors_on_selected_GPU",true}};
}
static json context(llama_context*c,llama_model*m,ggml_backend_dev_t gpu,int ub,int outputs){
    const auto&p=c->get_cparams();auto*cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(c));need(cache,"actual dense KV required");
    need(llama_n_ctx(c)==1024&&llama_n_batch(c)==1024&&int(llama_n_ubatch(c))==ub,"effective context/batch fields");
    need(p.n_outputs_max==uint32_t(outputs)&&p.n_outputs_max_per_seq==uint32_t(outputs)&&!p.flash_attn,"effective output/FA fields");
    need(cache->type_k()==GGML_TYPE_F16&&cache->type_v()==GGML_TYPE_F16&&cache->get_size()==1024,"effective F16 KV allocation");
    auto ids=cache->get_layer_ids();need(ids.size()==m->hparams.n_layer(),"every layer KV allocated");
    ggml_init_params ip={};ip.mem_size=8*1024*1024;ip.no_alloc=true;auto*views=ggml_init(ip);need(views,"metadata views");
    json rows=json::array();llama_kv_cache::slot_info slot{};slot.s0=slot.s1=0;slot.strm={0};slot.idxs={{0}};
    for(auto il:ids){auto*k=cache->get_k_storage(int(il));auto*v=cache->get_v(views,int(il),1,slot);rows.push_back({{"layer",il},{"K_storage",tensor(k,gpu)},{"V_storage",tensor(storage(v),gpu)}});}
    ggml_free(views);need(llama_memory_seq_pos_max(llama_get_memory(c),0)==-1,"zero-forward empty active prefix");
    return {{"n_ctx",llama_n_ctx(c)},{"n_batch",llama_n_batch(c)},{"n_ubatch",llama_n_ubatch(c)},
        {"output_capacity",p.n_outputs_max},{"outputs_per_seq",p.n_outputs_max_per_seq},{"flash_attention",p.flash_attn},
        {"cache_capacity",cache->get_size()},{"active_prefix_tokens",0},{"KV",rows},{"all_K_and_V_buffers_on_selected_GPU",true}};
}
int main(int argc,char**argv){
    fs::path out;llama_model*t=nullptr,*d=nullptr;llama_context*tc=nullptr,*dc=nullptr;const auto began=Clock::now();
    try{
        need(argc==3,"admit JOB OUT");const auto job=read(argv[1]);out=argv[2];need(!fs::exists(out),"fresh native output");fs::create_directories(out);
        const std::set<std::string>allowed={"family","target_model","target_sha256","draft_model","draft_sha256","n_ctx","threads","target_ubatch","draft_ubatch","target_outputs","draft_outputs","zero_forward","inputs","placement"};
        for(auto it=job.begin();it!=job.end();++it)need(allowed.count(it.key()),"unknown admission field");
        need(job.at("zero_forward")==true&&job.at("inputs").empty(),"admission never accepts token inputs");
        need(job.at("n_ctx")==1024&&job.at("threads")==2&&job.at("target_ubatch")==32&&job.at("draft_ubatch")==4&&job.at("target_outputs")==4&&job.at("draft_outputs")==1,"fixed C1024 D4 allocation contract");
        need(job.at("placement")=="all_model_tensors_and_KV_on_one_GPU_v1","explicit strict placement profile");
        auto start=Clock::now();auto th=file_hash(job.at("target_model").get<std::string>()),dh=file_hash(job.at("draft_model").get<std::string>());
        need(th==job.at("target_sha256")&&dh==job.at("draft_sha256"),"actual native model SHA");
        json result={{"schema","server-d14.zero-forward-admission.v1"},{"native_hash_s",seconds(start)},
            {"target_sha256",th},{"draft_sha256",dh},{"modules_before",linux_transfer::modules()},
            {"trajectories",0},{"token_rows",0},{"model_forwards",0},{"numerical_qualification","NOT_RUN"}};
        ggml_time_init();ggml_backend_load_all_from_path(linux_transfer::executable().parent_path().string().c_str());llama_backend_init();
        ggml_backend_dev_t gpu=nullptr;for(size_t i=0;i<ggml_backend_dev_count();++i){auto dev=ggml_backend_dev_get(i);if(ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"one visible GPU only");gpu=dev;}}need(gpu,"GPU required");
        ggml_backend_dev_t devices[]={gpu,nullptr};llama_model_tensor_buft_override override_types[]={{".*",ggml_backend_dev_buffer_type(gpu)},{nullptr,nullptr}};
        auto mp=llama_model_default_params();mp.devices=devices;mp.split_mode=LLAMA_SPLIT_MODE_NONE;mp.n_gpu_layers=999;mp.tensor_buft_overrides=override_types;
        start=Clock::now();t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);need(t&&d,"both pinned models loaded");result["model_pair_load_s"]=seconds(start);
        result["target_model"]=model(t,gpu);result["draft_model"]=model(d,gpu);
        need(t->hparams.n_layer()==40&&t->hparams.n_head()==40&&t->hparams.n_head_kv()==8&&t->hparams.n_embd_head_k()==128,"pinned14B native topology");
        auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"full pair vocab size");
        for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(std::strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"full native vocab/EOG compatibility");
        result["full_native_pair_vocab_and_EOG_equal"]=true;
        auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=1024;cp.n_ubatch=32;cp.n_threads=cp.n_threads_batch=2;cp.n_outputs_max=cp.n_outputs_max_per_seq=4;cp.type_k=cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.offload_kqv=true;
        start=Clock::now();tc=llama_init_from_model(t,cp);need(tc,"target context allocation");cp.n_ubatch=4;cp.n_outputs_max=cp.n_outputs_max_per_seq=1;dc=llama_init_from_model(d,cp);need(dc,"draft context allocation");result["context_pair_allocation_s"]=seconds(start);
        result["target_context"]=context(tc,t,gpu,32,4);result["draft_context"]=context(dc,d,gpu,4,1);result["GPU_device"]=ggml_backend_dev_description(gpu);
        result["status"]="ALLOCATED_ZERO_FORWARD_HOLD";save(out/"allocation.json",result);std::cout<<"ZERO_FORWARD_ALLOCATION_READY"<<std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(5));
        need(llama_memory_seq_pos_max(llama_get_memory(tc),0)==-1&&llama_memory_seq_pos_max(llama_get_memory(dc),0)==-1,"no active tokens after hold");
        result["modules_after"]=linux_transfer::modules();llama_free(dc);dc=nullptr;llama_free(tc);tc=nullptr;llama_model_free(d);d=nullptr;llama_model_free(t);t=nullptr;llama_backend_free();
        result["status"]="ZERO_FORWARD_ADMISSION_PASS";result["whole_main_s"]=seconds(began);save(out/"result.json",result);return 0;
    }catch(const std::exception&e){if(!out.empty()&&fs::exists(out))save(out/"failure.json",{{"error",e.what()},{"model_forwards",0}});std::cerr<<e.what()<<std::endl;if(dc)llama_free(dc);if(tc)llama_free(tc);if(d)llama_model_free(d);if(t)llama_model_free(t);return 2;}
}
