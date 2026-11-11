#pragma once
// Deployment observation/placement only; numerical archives stay immutable.
#include "llama-model.h"
#include "llama-context.h"
#include "llama-kv-cache.h"
#include "ggml-backend.h"
#include <fstream>
#include <vector>
#include <set>
extern "C" {
#include "hash/sha256/sha256.h"
}
using D14Json=nlohmann::json;
#ifndef D14_CORE
#error Explicit numerical core binding required
#endif
static std::string d14_hash(const std::string&path){
    std::ifstream f(path,std::ios::binary);need(bool(f),"D14 native hash open");sha256_t s;sha256_init(&s);std::vector<unsigned char>b(4*1024*1024);
    while(f){f.read(reinterpret_cast<char*>(b.data()),b.size());sha256_update(&s,b.data(),size_t(f.gcount()));}need(f.eof(),"D14 native hash read");
    unsigned char out[32];sha256_final(&s,out);std::string value;const char*h="0123456789abcdef";for(auto x:out){value+=h[x>>4];value+=h[x&15];}return value;
}
static D14Json d14_tensor(ggml_tensor*t,ggml_backend_dev_t gpu){
    while(!t->buffer&&t->view_src)t=t->view_src;
    need(t->buffer&&!ggml_backend_buffer_is_host(t->buffer),"D14 actual non-host tensor buffer required");
    const auto buft=ggml_backend_buffer_get_type(t->buffer);const auto dev=ggml_backend_buft_get_device(buft);
    need(dev==gpu&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"D14 weights and KV must use the selected GPU");
    return {{"name",t->name},{"type",ggml_type_name(t->type)},{"shape",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
        {"logical_bytes",ggml_nbytes(t)},{"buffer_type",ggml_backend_buft_name(buft)},{"host_backed",false}};
}
static D14Json d14_structure(llama_model*m){
    char arch[256]={};need(llama_model_meta_val_str(m,"general.architecture",arch,sizeof(arch))>0,"D14 native architecture");
    return {{"architecture",arch},{"layers",m->hparams.n_layer()},{"query_heads",m->hparams.n_head()},{"kv_heads",m->hparams.n_head_kv()},
        {"head_k",m->hparams.n_embd_head_k()},{"head_v",m->hparams.n_embd_head_v()},
        {"K_elements",m->hparams.n_embd_k_gqa()},{"V_elements",m->hparams.n_embd_v_gqa()},
        {"vocab",llama_vocab_n_tokens(llama_model_get_vocab(m))},{"tensor_count",m->tensors_by_name.size()}};
}
static D14Json d14_context(llama_context*c,llama_model*m,ggml_backend_dev_t gpu,D14Json&placement){
    const auto&p=c->get_cparams();auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(c));need(kv,"D14 dense KV required");
    auto ids=kv->get_layer_ids();need(ids.size()==m->hparams.n_layer(),"D14 every layer has KV");
    ggml_init_params ip={};ip.mem_size=8*1024*1024;ip.no_alloc=true;auto*views=ggml_init(ip);need(views,"D14 KV metadata context");
    llama_kv_cache::slot_info slot{};slot.s0=slot.s1=0;slot.strm={0};slot.idxs={{0}};placement["KV"]=D14Json::array();
    for(auto il:ids)placement["KV"].push_back({{"layer",il},{"K",d14_tensor(kv->get_k_storage(int(il)),gpu)},{"V",d14_tensor(kv->get_v(views,int(il),1,slot),gpu)}});
    ggml_free(views);need(llama_memory_seq_pos_max(llama_get_memory(c),0)==-1,"D14 capability precedes all input forwards");
    return {{"n_ctx",llama_n_ctx(c)},{"n_batch",llama_n_batch(c)},{"n_ubatch",llama_n_ubatch(c)},
        {"outputs_max",p.n_outputs_max},{"outputs_per_seq",p.n_outputs_max_per_seq},{"flash_attention",p.flash_attn},
        {"type_k",ggml_type_name(kv->type_k())},{"type_v",ggml_type_name(kv->type_v())},{"cache_capacity",kv->get_size()},
        {"all_KV_on_selected_GPU",true},{"active_prefix_tokens",0}};
}
static D14Json d14_model(const D14Json&job,const std::string&role,llama_model*m,llama_context*c,ggml_backend_dev_t gpu,D14Json&placement){
    const auto h=d14_hash(job.at(role+"_model").get<std::string>());need(h==job.at(role+"_sha256"),"D14 actual native weight hash");
    placement["model_tensors"]=D14Json::array();for(const auto&x:m->tensors_by_name)placement["model_tensors"].push_back(d14_tensor(x.second,gpu));
    need(!m->tensors_by_name.empty(),"D14 actual tensor inventory");
    return {{"sha256",h},{"structure",d14_structure(m)},{"context",d14_context(c,m,gpu,placement)},{"all_model_tensors_on_selected_GPU",true}};
}
static D14Json d14_capability(const D14Json&job,llama_model*t,llama_context*tc,llama_model*d,llama_context*dc,
        ggml_backend_dev_t gpu,const std::string&cut,int k,int width,const fs::path&root){
    const std::set<std::string>keys={"family","target_model","target_sha256","draft_model","draft_sha256","n_ctx","threads","lowering","draft_width","draft","residency","profile","inputs","cases","forced","observe_positions","state_positions","capability_request"};
    for(auto it=job.begin();it!=job.end();++it)need(keys.count(it.key()),"Unknown D14 native job field");
    need(job.at("n_ctx")==1024&&job.at("threads")==2&&!job.value("profile",false),"Fixed D14 C1024 two-thread unprofiled deployment");
    D14Json placement;D14Json echo={{"schema","heterospec.d14.native-capability.v1"},{"core",D14_CORE},{"family",job.at("family")},
        {"residency",job.at("residency")},{"cut",cut},{"k",k},{"draft_width",width},{"threads",2},{"greedy",true},
        {"target_output_policy","PREFILL:last;VERIFY:all_original_rows"},{"placement_policy","all_model_tensors_and_KV_on_one_GPU_v1"},
        {"target",d14_model(job,"target",t,tc,gpu,placement["target"])},{"draft",nullptr}};
    if(d){need(dc,"D14 draft context exists");echo["draft"]=d14_model(job,"draft",d,dc,gpu,placement["draft"]);}
    std::ofstream f(root/"PLACEMENT.json");f<<placement.dump(2)<<'\n';need(bool(f),"D14 placement receipt");
    std::ofstream g(root/"CAPABILITY.json");g<<echo.dump(2)<<'\n';need(bool(g),"D14 capability receipt");
    need(echo==job.at("capability_request"),"Native D14 capability differs from complete requested contract");return echo;
}
