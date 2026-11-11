// Build against the sealed PR166 cohort. No speculation in this diagnostic driver.
#include "llama-context.h"
#include "llama-kv-cache.h"
#include "hs_reference_batching.hpp"
#include "hs_scope.h"
#include "hsc_counter.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <chrono>
#include <iostream>
#include <memory>
#include <cmath>
using json=nlohmann::json;
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void check(bool ok,const char* msg){if(!ok)throw std::runtime_error(msg);}
static json read(const fs::path& p){std::ifstream in(p);return json::parse(in);}
static void save(const fs::path& p,const json& j){std::ofstream out(p);out<<j.dump(2);check(bool(out),"write");}
struct Observe {
    llama_context* ctx=nullptr;
    bool enabled=false;
    json nodes=json::array();
    static bool callback(ggml_tensor* t,bool ask,void* opaque){
        auto& o=*static_cast<Observe*>(opaque);
        if(!ask || !o.enabled || !o.ctx)return false;
        std::string name=t->name;
        // One layer per geometry, including every actual matmul input shape.
        if ((name.size()<2 || name.substr(name.size()-2)!="-0") && name.find("tpds_projection_blk.0.")!=0)return false;
        auto* be=ggml_backend_sched_get_tensor_backend(o.ctx->get_sched(),t);
        json inputs=json::array();
        for(auto* src:t->src)if(src)inputs.push_back({src->name,{src->ne[0],src->ne[1],src->ne[2],src->ne[3]}});
        o.nodes.push_back({{"op",ggml_op_name(t->op)},{"name",name},{"shape",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
            {"backend",be?ggml_backend_name(be):"unknown"},{"inputs",inputs}});
        return false;
    }
};
static void decode(llama_context* ctx,const int* ids,int count,int pos,bool outputs){
    auto batch=llama_batch_init(count,0,1);
    batch.n_tokens=count;
    for(int i=0;i<count;i++){
        batch.token[i]=ids[i];batch.pos[i]=pos+i;batch.n_seq_id[i]=1;
        batch.seq_id[i][0]=0;batch.logits[i]=outputs;
    }
    hsc::decode_begin(ctx,"target",true,count);
    int rc=llama_decode(ctx,batch);llama_batch_free(batch);
    check(rc==0,"decode");llama_synchronize(ctx);hsc::decode_end();
}
static std::vector<size_t> cuts(llama_context* ctx,std::string arm,int pos,size_t n){
    if(arm=="S1")return std::vector<size_t>(n,1);
    if(arm!="WB-cut")return {n};
#ifdef TPDS_ORACLE
    throw std::runtime_error("WB unavailable on sealed scalar core");
#else
    auto* kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx));
    check(kv!=nullptr,"dense KV required");
    const auto& cells=kv->get_cells(0);
    check(cells.get_used()==uint32_t(pos) && cells.used_max_p1()==uint32_t(pos),"non-dense append");
    uint32_t end=uint32_t(pos+n);
    auto req=hs_reference_batching::scalar_prefix_requirements({uint32_t(pos),uint32_t(n),end,end,
        kv->get_size(),kv->scalar_padding(),1,true,false});
    check(req.extents.size()==n,"WB geometry unsupported");
    std::vector<size_t> widths;
    for(const auto& g:hs_reference_batching::partition_adjacent(req.extents))widths.push_back(g.end-g.begin);
    return widths;
#endif
}
static void unit(llama_model* model,const json& j,const fs::path& dir){
    std::string arm=j.at("arm");int base=j.at("base"),width=j.at("width"),capacity=j.at("ctx");
    auto ids=j.at("tokens").get<std::vector<int>>();
    check(width>=1 && width<=32 && int(ids.size())==base+width && base+width<=capacity,"input geometry");
    check(arm=="S1" || arm=="PQ-ext" || arm=="QB-local" || arm=="WB-cut" || arm=="native","arm");
    Observe obs;
    auto p=llama_context_default_params();
    p.n_ctx=capacity;p.n_batch=std::min(capacity,1024);p.n_ubatch=arm=="S1"?1:width;
    p.n_threads=24;p.n_threads_batch=24;p.n_outputs_max=p.n_ubatch;p.n_outputs_max_per_seq=p.n_ubatch;
    p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
    p.cb_eval=Observe::callback;p.cb_eval_user_data=&obs;
    hs_scope::active=false;hs_scope::requested_layout=arm=="PQ-ext"?1:0;
    std::unique_ptr<llama_context,decltype(&llama_free)> ctx(llama_init_from_model(model,p),llama_free);
    check(bool(ctx),"context");obs.ctx=ctx.get();
    hsc::begin("counts",base);
    for(int i=0;i<base;i++)decode(ctx.get(),ids.data()+i,1,i,false);
    hsc::begin(j.value("trace",true)?"heavy":"counts",width);
    hs_scope::active=arm=="PQ-ext" || arm=="QB-local" || arm=="WB-cut";
    obs.enabled=j.value("trace",true);
    auto chunks=cuts(ctx.get(),arm,base,width);
    fs::create_directories(dir);
    json record={{"arm",arm},{"base",base},{"width",width},{"ctx",capacity},{"calls",chunks}};
    int used=0,vocab=llama_vocab_n_tokens(llama_model_get_vocab(model));
    for(auto n:chunks){
        decode(ctx.get(),ids.data()+base+used,int(n),base+used,true);
        for(size_t r=0;r<n;r++){
            auto* row=llama_get_logits_ith(ctx.get(),int(r));
            check(row!=nullptr,"missing row");
            for(int k=0;k<vocab;k++)check(std::isfinite(row[k]),"nonfinite logit");
            std::ofstream out(dir/(std::to_string(used+r)+".f32"),std::ios::binary);
            out.write((const char*)row,vocab*sizeof(float));check(bool(out),"vector write");
        }
        used+=int(n);
    }
    record["nodes"]=obs.nodes;record["graphs_reused"]=hsc::w.graphs_reused;
    for(int i=1;i<=width;i++)if(hsc::w.target_physical[i])record["physical"][std::to_string(i)]=hsc::w.target_physical[i];
    save(dir/"receipt.json",record);hs_scope::active=false;
}
int main(int argc,char** argv){
    try{
        check(argc==4,"probe MODEL MANIFEST OUT");auto manifest=read(argv[2]);
        auto bin=fs::absolute(argv[0]).parent_path();ggml_backend_load_all_from_path(bin.string().c_str());
        llama_backend_init();
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){
            auto dev=ggml_backend_dev_get(i);
            if(std::string(ggml_backend_dev_description(dev)).find("5070")!=std::string::npos)gpu=dev;
        }
        check(gpu!=nullptr,"RTX unavailable");ggml_backend_dev_t devices[]={gpu,nullptr};
        auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=manifest.at("layers");
        mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],mp),llama_model_free);
        check(bool(model),"model load");
        for(const auto& j:manifest.at("units"))unit(model.get(),j,fs::path(argv[3])/j.at("id").get<std::string>());
        model.reset();llama_backend_free();return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
