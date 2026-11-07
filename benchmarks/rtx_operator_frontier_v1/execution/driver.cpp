#define main frozen_probe_main
#include "probe.cpp"
#undef main
#include "ggml-alloc.h"
#include <iomanip>
#include <fstream>
#include "profiler.inc"
static double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static json desc(ggml_tensor*t){return {{"name",t->name},{"type",int(t->type)},{"bytes",ggml_nbytes(t)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};}
static void dump_tensor(ggml_tensor*t,const fs::path&p){
    std::vector<char>b(ggml_nbytes(t));ggml_backend_tensor_get(t,b.data(),0,b.size());
    std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());check(bool(f),"tensor write");
}
struct Hooks{
    llama_context* ctx=nullptr;
    fs::path dir;
    std::string mode;
    bool on=false;int scalar_row=0;
    json records=json::array();
    static bool call(ggml_tensor*t,bool ask,void*ptr){
        auto&o=*static_cast<Hooks*>(ptr);if(!o.on)return false;
        auto*be=ggml_backend_sched_get_tensor_backend(o.ctx->get_sched(),t);
        if(o.mode=="capture"){
            bool chosen=t->op==GGML_OP_MUL_MAT && t->src[0]->type==GGML_TYPE_Q8_0;
            if(chosen){
                std::string name=t->src[0]->name;
                chosen=name.find("blk.0.")==0 || name=="output.weight" || name=="token_embd.weight";
                bool scalar=t->src[1]->ne[1]==1; if(scalar && name!="blk.0.attn_q.weight")chosen=false;
                if(chosen){
                    auto p=o.dir/name;
                    if(scalar){if(ask && o.scalar_row==0){fs::create_directories(p);dump_tensor(t->src[0],p/"weight.bin");}p/=std::to_string(o.scalar_row);}
                    if(ask){
                        fs::create_directories(p);
                        if(!scalar)dump_tensor(t->src[0],p/"weight.bin");dump_tensor(t->src[1],p/"input.bin");
                        o.records.push_back({{"weight",desc(t->src[0])},{"input",desc(t->src[1])},{"output",desc(t)},{"backend",ggml_backend_name(be)}});
                    }else {dump_tensor(t,p/"output.bin");if(scalar)++o.scalar_row;}
                }
            }
            return true; // fence every preceding op before its consumer's ask callback
        }
        if(ask){
            std::string name=t->name;
            if(t->op==GGML_OP_CONCAT||t->op==GGML_OP_CPY||t->op==GGML_OP_CONT||
               (t->op==GGML_OP_MUL_MAT && (name.find("blk.0.")!=std::string::npos || name=="kq-0" || name=="kqv-0" || name.ends_with("-0")))){
                o.records.push_back({{"op",ggml_op_name(t->op)},{"tensor",desc(t)},{"backend",ggml_backend_name(be)}});
            }
        }
        return false;
    }
};
static void write_bytes(const fs::path&p,const void*b,size_t n){std::ofstream f(p,std::ios::binary);f.write((const char*)b,n);check(bool(f),"write");}
static std::vector<char> bytes(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);check(bool(f),"read open");std::vector<char>b(size_t(f.tellg()));f.seekg(0);f.read(b.data(),b.size());check(bool(f),"read bytes");return b;}
static void run_cell(llama_model*m,const json&j,const fs::path&root){
    std::string mode=j.at("mode"),arm=j.at("arm");
    int pos=j.at("pos"),width=j.at("width");
    fs::path dir=root/j.at("id").get<std::string>();check(fs::create_directories(dir),"attempt exists");
    Hooks hooks;hooks.mode=mode;hooks.dir=dir;
    auto p=llama_context_default_params();p.n_ctx=1536;p.n_batch=1024;p.n_ubatch=arm=="S1"?1:width;
    p.n_outputs_max=p.n_ubatch;p.n_outputs_max_per_seq=p.n_ubatch;p.n_threads=24;p.n_threads_batch=24;p.type_k=p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
    if(mode=="capture"||mode=="qual"){p.cb_eval=Hooks::call;p.cb_eval_user_data=&hooks;}
    hs_scope::active=false;hs_scope::requested_layout=0;
    auto start=Clock::now();std::unique_ptr<llama_context,decltype(&llama_free)> ctx(llama_init_from_model(m,p),llama_free);
    check(bool(ctx),"context init");hooks.ctx=ctx.get();json r={{"unit",j},{"init_s",elapsed(start)}};
    std::vector<int>ids(pos+width+1);for(int i=0;i<int(ids.size());i++)ids[i]=113+(i*173)%2309;
    fs::path state=j.at("state").get<std::string>();
    start=Clock::now();
    if(mode=="prefix"){
        for(int i=0;i<pos;i++)decode(ctx.get(),ids.data()+i,1,i,false);
        r["scalar_prefix_s"]=elapsed(start);
        size_t n=llama_state_seq_get_size(ctx.get(),0);std::vector<char>b(n);
        check(llama_state_seq_get_data(ctx.get(),(uint8_t*)b.data(),n,0)==n,"prefix export");write_bytes(state,b.data(),n);
        save(dir/"receipt.json",r);return;
    }
    if(pos){
        auto b=bytes(state);
        check(llama_state_seq_set_data(ctx.get(),(uint8_t*)b.data(),b.size(),0)==b.size(),"restore");
        check(llama_memory_seq_pos_max(llama_get_memory(ctx.get()),0)==pos-1,"restore position");
    }
    r["restore_s"]=elapsed(start);
#ifndef TPDS_ORACLE
    auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx.get()));check(kv && kv->get_cells(0).used_max_p1()==uint32_t(pos) && kv->get_cells(0).get_used()==uint32_t(pos),"physical prefix");
    r["padding"]=kv->scalar_padding();check(kv->scalar_padding()==256,"regenerate matrix for new padding");
#endif
    hooks.on=mode=="qual"||mode=="capture";hs_scope::active=arm=="QB-local"||arm=="WB-cut";
    hsc::begin(hooks.on?"heavy":"baseline",width);
    if(mode=="profile")profile::begin();start=Clock::now();auto chunks=cuts(ctx.get(),arm,pos,width);
    int offset=0;double output_io=0;
    for(auto n:chunks){
        decode(ctx.get(),ids.data()+pos+offset,int(n),pos+offset,true);
        if(mode!="cost" && mode!="profile"){
            auto io=Clock::now();int vocab=llama_vocab_n_tokens(llama_model_get_vocab(m));
            for(size_t i=0;i<n;i++)write_bytes(dir/(std::to_string(offset+i)+".f32"),llama_get_logits_ith(ctx.get(),int(i)),size_t(vocab)*4);
            output_io+=elapsed(io);
        }
        offset+=int(n);
    }
    r["append_s"]=elapsed(start);if(mode=="profile")profile::end(dir/"gpu.json");r["observer_output_io_s"]=output_io;r["calls"]=chunks;r["nodes"]=hooks.records;
    if(mode!="cost" && mode!="profile"){
        r["physical"]=hsc::w.physical_calls;r["reuse"]=hsc::w.graphs_reused;hooks.on=false;
        decode(ctx.get(),ids.data()+pos+width,1,pos+width,true);
        write_bytes(dir/"continuation.f32",llama_get_logits_ith(ctx.get(),0),4*llama_vocab_n_tokens(llama_model_get_vocab(m)));
    }
    save(dir/"receipt.json",r);hs_scope::active=false;
}
#include "replay.inc"
int main(int argc,char**argv){
    try{
        check(argc==4,"driver MODEL manifest root");fs::path root=argv[3];auto j=read(argv[2]);
        profile::init();auto bin=fs::absolute(argv[0]).parent_path();ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto dev=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(dev)).find("5070")!=std::string::npos)gpu=dev;}
        check(gpu,"native RTX");if(j.contains("replay")){replay(gpu,j,root);return 0;}
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto t=Clock::now();std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],mp),llama_model_free);check(bool(model),"load");
        save(root/"load.json",{{"model",argv[1]},{"seconds",elapsed(t)}});for(auto&cell:j.at("units"))run_cell(model.get(),cell,root);
        model.reset();llama_backend_free();return 0;
    }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
