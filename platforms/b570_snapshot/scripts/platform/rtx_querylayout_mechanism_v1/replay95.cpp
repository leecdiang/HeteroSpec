#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "nlohmann/json.hpp"
#include <fstream>
#include <filesystem>
#include <vector>
#include <cstring>
#include <iostream>
using json=nlohmann::ordered_json;
static std::vector<unsigned char> bytes(const std::filesystem::path & p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("missing input");return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
static void params(ggml_tensor * t,const json & j){auto b=j.at("op_params_bytes").get<std::vector<unsigned char>>();if(b.size()!=GGML_MAX_OP_PARAMS)throw std::runtime_error("invalid op params");std::memcpy(t->op_params,b.data(),b.size());}
static ggml_tensor * input(ggml_context * ctx,const json & j){auto ne=j.at("ne").get<std::vector<int64_t>>();auto nb=j.at("nb").get<std::vector<size_t>>();auto * t=ggml_new_tensor(ctx,(ggml_type)j.at("type").get<int>(),4,ne.data());for(int i=0;i<4;i++)t->nb[i]=nb[i];ggml_set_input(t);return t;}
static ggml_tensor * canonical(ggml_context * ctx,ggml_tensor * t,bool qb){return qb?ggml_cont(ctx,ggml_permute(ctx,t,0,3,2,1)):ggml_cont(ctx,t);}
int main(int argc,char ** argv){try{
    if(argc!=5)throw std::runtime_error("usage replay95 snapshot arm output runtime");
    const std::filesystem::path root=argv[1],out=argv[3];const std::string arm=argv[2];
    if(arm!="MQ"&&arm!="PQ"&&arm!="QB")throw std::runtime_error("invalid arm");
    if(std::filesystem::exists(out))throw std::runtime_error("immutable replay output exists");std::filesystem::create_directories(out);
    std::ifstream file(root/"snapshot.json");json m;file>>m;
    ggml_backend_load_all_from_path(argv[4]);auto backend=ggml_backend_init_by_name("CUDA0",nullptr);if(!backend)throw std::runtime_error("CUDA0 backend unavailable");
    const size_t nodes=1024;auto ctx=ggml_init({ggml_tensor_overhead()*nodes+ggml_graph_overhead_custom(nodes,false),nullptr,true});
    auto * q=input(ctx,m.at("Q")),*k=input(ctx,m.at("K")),*v=input(ctx,m.at("V")),*mask=input(ctx,m.at("mask"));
    if(q->type!=GGML_TYPE_F32 || k->type!=GGML_TYPE_F16 || v->type!=GGML_TYPE_F16 || mask->type!=GGML_TYPE_F32 || q->ne[1]<2 || q->ne[1]>4 || q->ne[3]!=1 || k->ne[3]!=1 || q->ne[2]%k->ne[2] || mask->ne[2]!=1 || mask->ne[3]!=1)throw std::runtime_error("unsupported captured geometry");
    ggml_tensor * sums[3]={nullptr,nullptr,nullptr};
    const int64_t width=q->ne[1];const bool pq=arm=="PQ",qb=arm=="QB";
    for(int64_t i=0;i<(pq?width:1);i++){
        auto * qi=q;auto * mi=mask;
        if(pq){qi=ggml_view_4d(ctx,q,q->ne[0],1,q->ne[2],1,q->nb[1],q->nb[2],q->nb[3],i*q->nb[1]);mi=ggml_view_2d(ctx,mask,mask->ne[0],1,mask->nb[1],i*mask->nb[1]);}
        if(qb){qi=ggml_view_4d(ctx,q,q->ne[0],1,q->ne[2],width,q->nb[1],q->nb[2],q->nb[1],0);mi=ggml_view_4d(ctx,mask,mask->ne[0],1,1,width,mask->nb[1],mask->nb[1],mask->nb[1],0);}
        auto * qk=ggml_mul_mat(ctx,k,qi);params(qk,m.at("native_QK"));
        auto * soft=ggml_soft_max_ext(ctx,qk,mi,1.0f,0.0f);params(soft,m.at("native_softmax"));
        float maxbias;std::memcpy(&maxbias,(const char*)soft->op_params+4,4);if(maxbias!=0)throw std::runtime_error("unsupported alibi bias");
        auto * av=ggml_mul_mat(ctx,v,soft);params(av,m.at("native_AV"));
        ggml_tensor * values[]={canonical(ctx,qk,qb),canonical(ctx,soft,qb),canonical(ctx,av,qb)};
        for(int stage=0;stage<3;stage++)sums[stage]=sums[stage]?ggml_concat(ctx,sums[stage],values[stage],1):values[stage];
    }
    auto * graph=ggml_new_graph_custom(ctx,nodes,false);for(auto * t:sums){ggml_set_output(t);ggml_build_forward_expand(graph,t);}
    auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);if(!buffer)throw std::runtime_error("allocation failed");
    const char * names[]={"Q","K","V","mask"};ggml_tensor * inputs[]={q,k,v,mask};json identities=json::object();
    for(int i=0;i<4;i++){
        auto b=bytes(root/m.at(names[i]).at("file").get<std::string>());if(b.size()!=ggml_nbytes(inputs[i]))throw std::runtime_error("input span differs");
        ggml_backend_tensor_set(inputs[i],b.data(),0,b.size());std::vector<unsigned char> readback(b.size());ggml_backend_tensor_get(inputs[i],readback.data(),0,readback.size());if(b!=readback)throw std::runtime_error("INPUT_NOT_IDENTICAL");
        identities[names[i]]={{"readback_bitwise_equal",true},{"bytes",b.size()},{"pointer",(uint64_t)inputs[i]->data},{"nb",m[names[i]]["nb"]},{"ne",m[names[i]]["ne"]},{"type",int(inputs[i]->type)},{"alignment_mod256",(uint64_t)inputs[i]->data%256}};
    }
    const auto rc=ggml_backend_graph_compute(backend,graph);if(rc!=GGML_STATUS_SUCCESS)throw std::runtime_error("actual CUDA graph failed");ggml_backend_synchronize(backend);
    json stages=json::object();const char * labels[]={"QK","softmax","AV"};
    for(int i=0;i<3;i++){auto * t=sums[i];std::vector<unsigned char> b(ggml_nbytes(t));ggml_backend_tensor_get(t,b.data(),0,b.size());std::ofstream f(out/(std::string(labels[i])+".bin"),std::ios::binary);f.write((const char*)b.data(),b.size());if(!f)throw std::runtime_error("output failed");stages[labels[i]]={{"type",int(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"bytes",b.size()}};}
    json dispatch=json::array();for(int i=0;i<ggml_graph_n_nodes(graph);i++){auto * t=ggml_graph_node(graph,i);dispatch.push_back({{"op",ggml_op_name(t->op)},{"dtype",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"buffer",t->buffer?ggml_backend_buffer_name(t->buffer):"null"},{"kernel_symbol",nullptr},{"grid_block",nullptr}});}
    json result={{"status","COMPLETED"},{"arm",arm},{"backend",ggml_backend_name(backend)},{"fixed_inputs",identities},{"stages",stages},{"actual_runtime_graph_dispatch",dispatch},{"kernel_scheduling","UNKNOWN"},{"launch_tracing","No Nsight/CUPTI trace; backend operation dispatch is not a kernel reduction schedule proof"},{"added_sync",true},{"scope","diagnostic operator replay; no paid request timing"}};
    std::ofstream meta(out/"REPLAY.json");meta<<result.dump(2)<<"\n";meta.flush();if(!meta)throw std::runtime_error("receipt failed");
    ggml_backend_buffer_free(buffer);ggml_free(ctx);ggml_backend_free(backend);return 0;
}catch(const std::exception & e){std::cerr<<e.what()<<"\n";return 2;}}
