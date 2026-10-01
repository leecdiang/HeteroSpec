// Independent one-model worker. The original DLL implements math and samplers.
#include "llama.h"
#include "ggml-backend.h"
#include "json.hpp"
#include <windows.h>
#include <psapi.h>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using json=nlohmann::ordered_json;
#define API_LIST(X) \
X(llama_backend_init) X(llama_model_default_params) X(llama_context_default_params) \
X(llama_model_load_from_file) X(llama_init_from_model) X(llama_model_get_vocab) \
X(llama_vocab_n_tokens) X(llama_tokenize) X(llama_vocab_is_eog) X(llama_get_logits_ith) \
X(llama_batch_init) X(llama_batch_free) X(llama_decode) X(llama_get_memory) \
X(llama_memory_seq_rm) X(llama_memory_seq_pos_max) X(llama_free) X(llama_model_free) \
X(llama_sampler_chain_default_params) X(llama_sampler_chain_init) X(llama_sampler_chain_add) \
X(llama_sampler_init_top_k) X(llama_sampler_init_temp) X(llama_sampler_init_dist) \
X(llama_sampler_apply) X(llama_sampler_accept) X(llama_sampler_reset) X(llama_sampler_free) \
X(llama_vocab_get_suppress_tokens) X(llama_sampler_init_logit_bias) X(llama_synchronize)
#define DECL(N) decltype(&N) f_##N;
API_LIST(DECL)
decltype(&ggml_backend_load_all_from_path) f_backend_load;
decltype(&ggml_backend_dev_by_name) f_dev;
static json graphs=json::array();
static bool graph_observe(ggml_tensor * t,bool ask,void*) {
    if(ask && std::string(t->name)=="result_output")graphs.push_back({{"name",t->name},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}}});
    return false; // Observe metadata; request no tensor reads or extra execution.
}
static void require(bool ok,const char * msg){if(!ok)throw std::runtime_error(msg);}
static json modules(){
    HMODULE mods[1024];DWORD count;json a=json::array();
    if(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&count))for(unsigned i=0;i<count/sizeof(HMODULE);i++){
        char p[32768];if(GetModuleFileNameA(mods[i],p,sizeof(p)))a.push_back(p);
    }return a;
}
static std::string hex(const void * p,size_t n){
    const auto * b=(const unsigned char*)p;std::string s;s.reserve(n*2);const char * h="0123456789abcdef";
    for(size_t i=0;i<n;i++){s.push_back(h[b[i]>>4]);s.push_back(h[b[i]&15]);}return s;
}
static void send(const json &j){std::cout<<j.dump()<<std::endl;}
int main(int argc,char **argv){try{
    require(argc==5,"usage: worker runtime-dir model-path ubatch role");
    const std::string role=argv[4];
#ifdef PROPOSER_ONLY
    require(role=="P","P executable refuses target role");
    require(std::string(argv[2]).find("Qwen3-0.6B-Q8_0.gguf")!=std::string::npos,"P model allowlist");
#else
    require(role=="R","R executable refuses proposer role");
    require(std::string(argv[2]).find("Qwen3-8B-Q8_0.gguf")!=std::string::npos,"R model allowlist");
#endif
    SetDllDirectoryA(argv[1]);
    auto base=LoadLibraryA((std::string(argv[1])+"/ggml-base.dll").c_str());
    auto ggml=LoadLibraryA((std::string(argv[1])+"/ggml.dll").c_str());
    auto dll=LoadLibraryA((std::string(argv[1])+"/llama.dll").c_str());require(base&&ggml&&dll,"original DLL load failed");
#define LOAD(N) f_##N=(decltype(f_##N))GetProcAddress(dll,#N);require(f_##N!=nullptr,#N);
    API_LIST(LOAD)
    f_backend_load=(decltype(f_backend_load))GetProcAddress(base,"ggml_backend_load_all_from_path");
    f_dev=(decltype(f_dev))GetProcAddress(base,"ggml_backend_dev_by_name");require(f_backend_load&&f_dev,"backend exports");
    f_llama_backend_init();f_backend_load(argv[1]);
    ggml_backend_dev_t devices[]={f_dev("CUDA0"),nullptr};require(devices[0]!=nullptr,"CUDA0 unavailable");
    auto mp=f_llama_model_default_params();mp.n_gpu_layers=-1;mp.devices=devices;
    auto model=f_llama_model_load_from_file(argv[2],mp);require(model!=nullptr,"model load failed");
    auto cp=f_llama_context_default_params();cp.n_ctx=4096;cp.n_batch=2048;cp.n_ubatch=std::stoi(argv[3]);cp.n_seq_max=1;
    cp.n_threads=24;cp.n_threads_batch=24;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.kv_unified=false;cp.no_perf=false;
    cp.cb_eval=graph_observe;cp.cb_eval_user_data=nullptr;
    auto ctx=f_llama_init_from_model(model,cp);require(ctx!=nullptr,"context initialization failed");
    auto vocab=f_llama_model_get_vocab(model);const int nv=f_llama_vocab_n_tokens(vocab);
    auto sampler=f_llama_sampler_chain_init(f_llama_sampler_chain_default_params());
    int ns=0;const auto * suppress=f_llama_vocab_get_suppress_tokens(vocab,&ns);std::vector<llama_logit_bias> bias;
    for(int i=0;i<ns;i++)bias.push_back({suppress[i],-INFINITY});
    if(ns)f_llama_sampler_chain_add(sampler,f_llama_sampler_init_logit_bias(nv,ns,bias.data()));
#ifdef PROPOSER_ONLY
    f_llama_sampler_chain_add(sampler,f_llama_sampler_init_top_k(10));
    f_llama_sampler_chain_add(sampler,f_llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
#else
    // All omitted CLI default transforms are identities under this frozen greedy configuration.
    f_llama_sampler_chain_add(sampler,f_llama_sampler_init_temp(0));
    f_llama_sampler_chain_add(sampler,f_llama_sampler_init_dist(123));
#endif
    int nextpos=0;std::vector<int> committed;int round=0;
    auto decode=[&](const std::vector<int>&tokens,int pos,const std::vector<int>&mask){
        auto b=f_llama_batch_init((int)tokens.size(),0,1);b.n_tokens=(int)tokens.size();
        for(size_t i=0;i<tokens.size();i++){b.token[i]=tokens[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=mask[i];}
        graphs=json::array();const int rc=f_llama_decode(ctx,b);f_llama_batch_free(b);require(rc==0,"decode failed");f_llama_synchronize(ctx);
        return json{{"tokens",tokens},{"positions_start",pos},{"logits_mask",mask},{"graphs",graphs},{"returncode",rc}};
    };
    auto sample=[&](int idx,int proposal,bool draft){
        float * logits=f_llama_get_logits_ith(ctx,idx);require(logits!=nullptr,"missing logits row");
        std::vector<llama_token_data> data(nv);int top1=0,top2=1;if(logits[1]>logits[0])std::swap(top1,top2);
        for(int i=2;i<nv;i++){if(logits[i]>logits[top1]){top2=top1;top1=i;}else if(logits[i]>logits[top2])top2=i;}
        for(int i=0;i<nv;i++)data[i]={i,logits[i],0};
        llama_token_data_array a={data.data(),data.size(),-1,false};f_llama_sampler_apply(sampler,&a);
        if(draft){std::sort(a.data,a.data+a.size,[](auto &x,auto &y){return x.p>y.p;});a.selected=0;}
        require(a.selected>=0,"sampler selected no token");int token=a.data[a.selected].id;f_llama_sampler_accept(sampler,token);
        // Raw bytes are returned only to the local recorder for SHA256; recorder omits them from archived events.
        json j={{"logits_index",idx},{"logits_bytes_hex",hex(logits,nv*sizeof(float))},{"raw_top1",top1},{"raw_top2",top2},
            {"raw_top1_score",logits[top1]},{"raw_top2_score",logits[top2]},{"proposal_id",proposal},{"proposal_score",proposal<0?json(nullptr):json(logits[proposal])},{"selected_id",token},{"selected_probability",a.data[a.selected].p},{"eog",f_llama_vocab_is_eog(vocab,token)}};
        return j;
    };
    send({{"event","READY"},{"role",role},{"pid",GetCurrentProcessId()},{"model_open",argv[2]},{"modules",modules()},
        {"context",{{"n_ctx",4096},{"n_batch",2048},{"n_ubatch",cp.n_ubatch},{"n_seq_max",1},{"threads",24},{"flash_attention","off"},{"kv_unified",false}}},{"suppress_ids",std::vector<int>(suppress,suppress+ns)}});
    std::string line;
    while(std::getline(std::cin,line)){
        auto q=json::parse(line);auto op=q.at("op").get<std::string>();json out;
        if(op=="init"){
            require(nextpos==0,"duplicate prefill");auto text=q.at("formatted_prompt").get<std::string>();std::vector<int> toks(text.size()+64);
            int n=f_llama_tokenize(vocab,text.c_str(),text.size(),toks.data(),toks.size(),true,true);require(n>0,"tokenization failed");toks.resize(n);
            std::vector<int> mask(n,0);mask.back()=1;
            out={{"event","PREFILL"},{"prompt_ids",toks},{"decode",decode(toks,0,mask)}};nextpos=n;
#ifndef PROPOSER_ONLY
            auto s=sample(n-1,-1,false);int id=s["selected_id"];committed.push_back(id);out["samples"]=json::array({s});out["committed_ids"]=committed;out["terminal"]=s["eog"];
#endif
        }
#ifdef PROPOSER_ONLY
        else if(op=="propose"){
            require(q.at("position").get<int>()==nextpos,"P position differs from retained KV");int pending=q.at("pending");int cap=q.at("max_proposals");require(cap>=0&&cap<=2,"P width");
            json samples=json::array(),decodes=json::array();std::vector<int> ids;f_llama_sampler_reset(sampler);
            if(cap>0){decodes.push_back(decode({pending},nextpos,{1}));for(int i=0;i<cap;i++){
                auto s=sample(0,-1,true);int id=s["selected_id"];ids.push_back(id);samples.push_back(s);
                if(i+1<cap)decodes.push_back(decode({id},nextpos+i+1,{1}));
            }}
            require(f_llama_memory_seq_rm(f_llama_get_memory(ctx),0,nextpos,-1),"P rollback failed");
            out={{"event","PROPOSALS"},{"round",round},{"proposal_ids",ids},{"decodes",decodes},{"samples",samples},{"suffix_delete_start",nextpos}};
        }else if(op=="update"){
            auto tokens=q.at("verified_batch").get<std::vector<int>>();require(q.at("position").get<int>()==nextpos,"P update position");
            std::vector<int> mask(tokens.size(),0);mask.back()=1;
            auto d=decode(tokens,nextpos,mask);int retained=q.at("retain_count");require(retained>=1&&retained<=(int)tokens.size(),"P retained count");
            nextpos+=retained;require(f_llama_memory_seq_rm(f_llama_get_memory(ctx),0,nextpos,-1),"P verification suffix delete failed");
            out={{"event","UPDATE"},{"decode",d},{"next_position",nextpos},{"suffix_delete_start",nextpos}};round++;
        }
#else
        else if(op=="verify"){
            require(q.at("round").get<int>()==round,"R round differs");require(q.at("position").get<int>()==nextpos,"R position differs");require(q.at("pending").get<int>()==committed.back(),"R pending differs from own sampler");
            auto proposals=q.at("proposal_ids").get<std::vector<int>>();require(proposals.size()<=2,"R width");std::vector<int> tokens={committed.back()};tokens.insert(tokens.end(),proposals.begin(),proposals.end());
            auto d=decode(tokens,nextpos,std::vector<int>(tokens.size(),1));json samples=json::array();std::vector<int> ids;
            int accepted=0;
            for(size_t i=0;i<tokens.size();i++){
                const int proposal=i<proposals.size()?proposals[i]:-1;auto s=sample(i,proposal,false);int id=s["selected_id"];samples.push_back(s);ids.push_back(id);
                if(i==proposals.size()||id!=proposal)break;accepted++;
            }
            int retained=(int)ids.size();nextpos+=retained;require(f_llama_memory_seq_rm(f_llama_get_memory(ctx),0,nextpos,-1),"R suffix delete failed");
            auto terminal=false;std::vector<int> visible;
            for(int id:ids){if(committed.size()==128)break;committed.push_back(id);visible.push_back(id);if(f_llama_vocab_is_eog(vocab,id)){terminal=true;break;}}
            terminal=terminal||committed.size()==128;
            out={{"event","VERIFIED"},{"round",round},{"decode",d},{"samples",samples},{"accepted_proposals",accepted},{"sampled_ids",ids},{"committed_ids",visible},{"retain_count",retained},{"next_position",nextpos},{"suffix_delete_start",nextpos},{"terminal",terminal},{"committed_count",committed.size()}};round++;
        }
#endif
        else if(op=="close"){send({{"event","CLOSED"},{"modules",modules()}});break;}
        else throw std::runtime_error("operation outside role allowlist");
        out["kv_position_max"]=f_llama_memory_seq_pos_max(f_llama_get_memory(ctx),0);send(out);
    }
    f_llama_sampler_free(sampler);f_llama_free(ctx);f_llama_model_free(model);return 0;
}catch(const std::exception &e){send({{"event","ERROR"},{"error",e.what()}});return 2;}}
