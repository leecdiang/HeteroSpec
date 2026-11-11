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
using LLAMA_FJson=nlohmann::json;
#ifndef LLAMA_F_CORE
#error Explicit numerical core binding required
#endif
static std::string llama_f_hash(const std::string&path){
    std::ifstream f(path,std::ios::binary);need(bool(f),"LLAMA_F native hash open");sha256_t s;sha256_init(&s);std::vector<unsigned char>b(4*1024*1024);
    while(f){f.read(reinterpret_cast<char*>(b.data()),b.size());sha256_update(&s,b.data(),size_t(f.gcount()));}need(f.eof(),"LLAMA_F native hash read");
    unsigned char out[32];sha256_final(&s,out);std::string value;const char*h="0123456789abcdef";for(auto x:out){value+=h[x>>4];value+=h[x&15];}return value;
}
static LLAMA_FJson llama_f_tensor(ggml_tensor*t,ggml_backend_dev_t gpu){
    while(!t->buffer&&t->view_src)t=t->view_src;
    need(t->buffer&&!ggml_backend_buffer_is_host(t->buffer),"LLAMA_F actual non-host tensor buffer required");
    const auto buft=ggml_backend_buffer_get_type(t->buffer);const auto dev=ggml_backend_buft_get_device(buft);
    need(dev==gpu&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"LLAMA_F weights and KV must use the selected GPU");
    return {{"name",t->name},{"type",ggml_type_name(t->type)},{"shape",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
        {"logical_bytes",ggml_nbytes(t)},{"buffer_type",ggml_backend_buft_name(buft)},{"host_backed",false}};
}
static LLAMA_FJson llama_f_structure(llama_model*m){
    char arch[256]={};need(llama_model_meta_val_str(m,"general.architecture",arch,sizeof(arch))>0,"LLAMA_F native architecture");
    return {{"architecture",arch},{"layers",m->hparams.n_layer()},{"query_heads",m->hparams.n_head()},{"kv_heads",m->hparams.n_head_kv()},
        {"head_k",m->hparams.n_embd_head_k()},{"head_v",m->hparams.n_embd_head_v()},
        {"K_elements",m->hparams.n_embd_k_gqa()},{"V_elements",m->hparams.n_embd_v_gqa()},
        {"vocab",llama_vocab_n_tokens(llama_model_get_vocab(m))},{"tensor_count",m->tensors_by_name.size()}};
}
static LLAMA_FJson llama_f_context(llama_context*c,llama_model*m,ggml_backend_dev_t gpu,LLAMA_FJson&placement){
    const auto&p=c->get_cparams();auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(c));need(kv,"LLAMA_F dense KV required");
    auto ids=kv->get_layer_ids();need(ids.size()==m->hparams.n_layer(),"LLAMA_F every layer has KV");
    ggml_init_params ip={};ip.mem_size=8*1024*1024;ip.no_alloc=true;auto*views=ggml_init(ip);need(views,"LLAMA_F KV metadata context");
    llama_kv_cache::slot_info slot{};slot.s0=slot.s1=0;slot.strm={0};slot.idxs={{0}};placement["KV"]=LLAMA_FJson::array();
    for(auto il:ids)placement["KV"].push_back({{"layer",il},{"K",llama_f_tensor(kv->get_k_storage(int(il)),gpu)},{"V",llama_f_tensor(kv->get_v(views,int(il),1,slot),gpu)}});
    ggml_free(views);need(llama_memory_seq_pos_max(llama_get_memory(c),0)==-1,"LLAMA_F capability precedes all input forwards");
    return {{"n_ctx",llama_n_ctx(c)},{"n_batch",llama_n_batch(c)},{"n_ubatch",llama_n_ubatch(c)},
        {"outputs_max",p.n_outputs_max},{"outputs_per_seq",p.n_outputs_max_per_seq},{"flash_attention",p.flash_attn},
        {"type_k",ggml_type_name(kv->type_k())},{"type_v",ggml_type_name(kv->type_v())},{"cache_capacity",kv->get_size()},
        {"all_KV_on_selected_GPU",true},{"active_prefix_tokens",0}};
}
static LLAMA_FJson llama_f_model(const LLAMA_FJson&job,const std::string&role,llama_model*m,llama_context*c,ggml_backend_dev_t gpu,LLAMA_FJson&placement){
    const auto h=llama_f_hash(job.at(role+"_model").get<std::string>());need(h==job.at(role+"_sha256"),"LLAMA_F actual native weight hash");
    placement["model_tensors"]=LLAMA_FJson::array();for(const auto&x:m->tensors_by_name)placement["model_tensors"].push_back(llama_f_tensor(x.second,gpu));
    need(!m->tensors_by_name.empty(),"LLAMA_F actual tensor inventory");
    return {{"sha256",h},{"structure",llama_f_structure(m)},{"context",llama_f_context(c,m,gpu,placement)},{"all_model_tensors_on_selected_GPU",true}};
}
static LLAMA_FJson llama_f_capability(const LLAMA_FJson&job,llama_model*t,llama_context*tc,llama_model*d,llama_context*dc,
        ggml_backend_dev_t gpu,const std::string&cut,int k,int width,const fs::path&root){
    const std::set<std::string>keys={"family","target_model","target_sha256","draft_model","draft_sha256","n_ctx","threads","lowering","draft_width","draft","residency","profile","inputs","cases","forced","observe_positions","state_positions","capability_request"};
    for(auto it=job.begin();it!=job.end();++it)need(keys.count(it.key()),"Unknown LLAMA_F native job field");
    need(job.at("n_ctx")==1024&&job.at("threads")==2&&!job.value("profile",false),"Fixed LLAMA_F C1024 two-thread unprofiled deployment");
    LLAMA_FJson placement;LLAMA_FJson echo={{"schema","heterospec.llama_f.native-capability.v1"},{"core",LLAMA_F_CORE},{"family",job.at("family")},
        {"residency",job.at("residency")},{"cut",cut},{"k",k},{"draft_width",width},{"threads",2},{"greedy",true},
        {"target_output_policy","PREFILL:last;VERIFY:all_original_rows"},{"placement_policy","all_model_tensors_and_KV_on_one_GPU_v1"},
        {"target",llama_f_model(job,"target",t,tc,gpu,placement["target"])},{"draft",nullptr}};
    if(d){need(dc,"LLAMA_F draft context exists");echo["draft"]=llama_f_model(job,"draft",d,dc,gpu,placement["draft"]);}
    std::ofstream f(root/"PLACEMENT.json");f<<placement.dump(2)<<'\n';need(bool(f),"LLAMA_F placement receipt");
    std::ofstream g(root/"CAPABILITY.json");g<<echo.dump(2)<<'\n';need(bool(g),"LLAMA_F capability receipt");
    need(echo==job.at("capability_request"),"Native LLAMA_F capability differs from complete requested contract");return echo;
}
