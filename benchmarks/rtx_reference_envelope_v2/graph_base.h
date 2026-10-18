#pragma once
#include "hs113_graph.h"
#include "core_gate.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <chrono>
#include <cmath>
#include <windows.h>
#include <psapi.h>
using J=nlohmann::ordered_json;namespace fs=std::filesystem;
static J read(const fs::path&p){std::ifstream f(p);hs113::require(bool(f),"missing JSON");J j;f>>j;return j;}
static size_t gpu_file_limit=0,gpu_total_limit=0;
static void write(const fs::path&p,const J&j){hs113::require(!fs::exists(p),"immutable output exists");fs::create_directories(p.parent_path());auto body=j.dump()+"\n";if(gpu_file_limit){size_t used=0;for(const auto&e:fs::directory_iterator(p.parent_path()))if(e.is_regular_file())used+=e.file_size();hs113::require(body.size()<=gpu_file_limit&&used+body.size()<=gpu_total_limit,"native metadata output budget before write");}std::ofstream f(p);f<<body;hs113::require(bool(f),"write failed");}
static std::vector<unsigned char> bytes(const fs::path&p){std::ifstream f(p,std::ios::binary);hs113::require(bool(f),"missing tensor bytes");return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
static int64_t integer(const J&j,int64_t low,int64_t high){hs113::require(j.is_number_integer()&&!j.is_boolean(),"strict integer required");auto n=j.get<int64_t>();hs113::require(n>=low&&n<=high,"integer outside domain");return n;}
static size_t span(const J&m){
    hs113::require(m.at("ne").size()==4&&m.at("nb").size()==4,"four dimensions required");
    const int type=(int)integer(m.at("type"),0,1);const size_t word=type==0?4:2;size_t total=word;std::vector<std::pair<size_t,size_t>>dims;
    for(int i=0;i<4;i++){auto ne=integer(m["ne"][i],1,1024*128),nb=integer(m["nb"][i],word,1024LL*1024*64);hs113::require(nb%word==0,"unaligned stride");total+=(ne-1)*nb;if(ne>1)dims.push_back({nb,(size_t)ne});}
    std::sort(dims.begin(),dims.end());size_t owner=word;for(auto x:dims){hs113::require(x.first>=owner,"overlapping owner view");owner+=(x.second-1)*x.first;}
    hs113::require(total<=64*1024*1024,"bounded input span");if(m.contains("bytes"))hs113::require(integer(m["bytes"],1,64*1024*1024)==(int64_t)total,"view owner span differs");return total;
}
static ggml_tensor* input(ggml_context*ctx,const J&m){span(m);int64_t ne[4];for(int i=0;i<4;i++)ne[i]=m["ne"][i].get<int64_t>();auto*t=ggml_new_tensor(ctx,(ggml_type)m["type"].get<int>(),4,ne);for(int i=0;i<4;i++)t->nb[i]=m["nb"][i].get<size_t>();ggml_set_input(t);return t;}
static bool metadata(ggml_op op){return op==GGML_OP_NONE||op==GGML_OP_VIEW||op==GGML_OP_RESHAPE||op==GGML_OP_PERMUTE||op==GGML_OP_TRANSPOSE;}
static J descriptor(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"name",std::string(t->name)},{"type",int(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"bytes",ggml_nbytes(t)},{"op_params",std::vector<unsigned char>((unsigned char*)t->op_params,(unsigned char*)t->op_params+GGML_MAX_OP_PARAMS)},{"metadata_only",metadata(t->op)}};}
static J modules(){HMODULE list[2048];DWORD needed=0;hs113::require(EnumProcessModules(GetCurrentProcess(),list,sizeof(list),&needed),"module enumeration failed");J j=J::array();for(size_t i=0;i<std::min<size_t>(needed/sizeof(HMODULE),2048);i++){wchar_t path[32768];hs113::require(GetModuleFileNameW(list[i],path,32768)>0,"module path failed");j.push_back(fs::path(path).u8string());}return j;}
struct Graph {
    ggml_context*ctx;ggml_cgraph*g;ggml_tensor*in[4];hs113::Result result;J m;
    Graph(const J&meta,const std::string&name,bool stages):m(meta){
        ctx=ggml_init({ggml_tensor_overhead()*4096+ggml_graph_overhead_custom(4096,false),nullptr,true});hs113::require(ctx,"ggml context failed");
        const char*roles[]={"Q","K","V","mask"};for(int i=0;i<4;i++)in[i]=input(ctx,m.at(roles[i]));
        unsigned char params[3][GGML_MAX_OP_PARAMS];const char*pn[]={"native_QK","native_softmax","native_AV"};
        for(int i=0;i<3;i++){auto p=m.at(pn[i]).at("op_params_bytes").get<std::vector<unsigned char>>();hs113::require(p.size()==GGML_MAX_OP_PARAMS,"exact op params required");std::copy(p.begin(),p.end(),params[i]);}
        result=hs113::build(ctx,in[0],in[1],in[2],in[3],hs113::layout(name),1.0f,params[0],params[1],params[2]);
        g=ggml_new_graph_custom(ctx,4096,false);
        if(stages)for(auto*t:result.stage){ggml_set_output(t);ggml_build_forward_expand(g,t);}
        ggml_set_output(result.ordinary);ggml_build_forward_expand(g,result.ordinary);
    }
    ~Graph(){ggml_free(ctx);}
    J registry(ggml_backend_t backend=nullptr){J nodes=J::array();std::map<ggml_tensor*,int>ids;for(int i=0;i<4;i++)ids[in[i]]=-i-1;
        for(int i=0;i<ggml_graph_n_nodes(g);i++){auto*t=ggml_graph_node(g,i);ids[t]=i;auto d=descriptor(t);d["id"]=i;J src=J::array();for(auto*s:t->src)if(s)src.push_back(ids.count(s)?J(ids[s]):J("EXTERNAL_LEAF"));d["src"]=src;
            d["CUDA_support"]=backend?J(ggml_backend_supports_op(backend,t)):J(nullptr);d["placement"]=backend&&t->buffer?J(ggml_backend_buffer_name(t->buffer)):J(nullptr);nodes.push_back(d);}
        bool full=true;if(backend)for(const auto &n:nodes)if(!n["metadata_only"].get<bool>()&&n["CUDA_support"]!=true)full=false;return {{"common_q1_original_arithmetic_chain",result.common},{"nodes",nodes},{"full_support",backend?J(full):J(nullptr)},{"actual_placement",nullptr},{"output",descriptor(result.ordinary)}};
    }
};
using I=std::array<int64_t,4>;
static I unravel(size_t linear,ggml_tensor*t){I x;for(int i=0;i<4;i++){x[i]=linear%t->ne[i];linear/=t->ne[i];}hs113::require(linear==0,"unravel overflow");return x;}
// Independent storage-only interpreter: never executes MUL_MAT or SOFT_MAX.
static uint32_t storage(ggml_tensor*t,I x,const std::map<ggml_tensor*,std::vector<unsigned char>>&raw){
    size_t off=0;for(int i=0;i<4;i++){hs113::require(x[i]>=0&&x[i]<t->ne[i],"storage coordinate");off+=x[i]*t->nb[i];}
    auto p=raw.find(t);if(p!=raw.end()){hs113::require(off+4<=p->second.size(),"leaf owner bounds");uint32_t v;std::memcpy(&v,p->second.data()+off,4);return v;}
    if(t->view_src){auto it=raw.find(t->view_src);off+=t->view_offs;if(it!=raw.end()){hs113::require(off+4<=it->second.size(),"view owner bounds");uint32_t v;std::memcpy(&v,it->second.data()+off,4);return v;}
        hs113::require(ggml_is_contiguous(t->view_src)&&off%4==0,"generated view owner must be contiguous");return storage(t->view_src,unravel(off/4,t->view_src),raw);}
    if(t->op==GGML_OP_CONT){size_t linear=x[0]+t->ne[0]*(x[1]+t->ne[1]*(x[2]+t->ne[2]*x[3]));return storage(t->src[0],unravel(linear,t->src[0]),raw);}
    if(t->op==GGML_OP_REPEAT){for(int i=0;i<4;i++)x[i]%=t->src[0]->ne[i];return storage(t->src[0],x,raw);}
    if(t->op==GGML_OP_CONCAT){int axis=0;std::memcpy(&axis,t->op_params,sizeof(axis));hs113::require(axis>=0&&axis<4,"CPU concat axis");if(x[axis]<t->src[0]->ne[axis])return storage(t->src[0],x,raw);x[axis]-=t->src[0]->ne[axis];return storage(t->src[1],x,raw);}
    throw std::runtime_error("CPU test attempted arithmetic instead of storage-only path");
}
static J address_tests(const J&plan){size_t checked=0,outputs=0;int cases=0;
    for(const auto&d:plan.at("descriptors")){const auto&m=d.at("metadata");if(d.at("kind")!="ACTUAL_FULL_SNAPSHOT")continue;
        for(std::string name:{"QH_C","QH_D"}){Graph g(m,name,true);auto q=g.in[0];auto mask=g.in[3];int64_t width=q->ne[1],H=q->ne[2],D=q->ne[0];fs::path root=d.at("root").get<std::string>();
            std::map<ggml_tensor*,std::vector<unsigned char>>raw;raw[q]=bytes(root/m["Q"]["file"].get<std::string>());raw[mask]=bytes(root/m["mask"]["file"].get<std::string>());
            ggml_tensor *mm=nullptr,*sm=nullptr,*av=nullptr;for(int i=0;i<ggml_graph_n_nodes(g.g);i++){auto*t=ggml_graph_node(g.g,i);if(t->op==GGML_OP_MUL_MAT&&t->src[0]==g.in[1])mm=t;if(t->op==GGML_OP_SOFT_MAX)sm=t;if(t->op==GGML_OP_MUL_MAT&&t->src[0]==g.in[2])av=t;}
            hs113::require(mm&&sm&&av,"actual arithmetic nodes absent");
            for(int64_t h=0;h<H;h++)for(int64_t j=0;j<width;j++){
                int64_t r=h*width+j;for(int64_t a=0;a<D;a++){I ix=width==1?I{a,j,h,0}:I{a,0,r,0};hs113::require(storage(mm->src[1],ix,raw)==storage(q,I{a,j,h,0},raw),"Q packing address mismatch");checked++;}
                for(int64_t key=0;key<mask->ne[0];key++){I ix=width==1?I{key,j,0,0}:I{key,0,name=="QH_C"?j:r,0};hs113::require(storage(sm->src[1],ix,raw)==storage(mask,I{key,j,0,0},raw),"mask modulo/repeat mismatch");checked++;}
            }
            std::vector<unsigned char>fake(ggml_nbytes(av));for(int64_t h=0;h<H;h++)for(int64_t j=0;j<width;j++)for(int64_t a=0;a<D;a++){
                uint32_t marker=(uint32_t)(1+a+D*(j+width*h));I ix=width==1?I{a,j,h,0}:I{a,0,h*width+j,0};size_t off=0;for(int i=0;i<4;i++)off+=ix[i]*av->nb[i];std::memcpy(fake.data()+off,&marker,4);
            }raw[av]=fake;
            for(int64_t h=0;h<H;h++)for(int64_t j=0;j<width;j++)for(int64_t a=0;a<D;a++){hs113::require(storage(g.result.ordinary,I{a+h*D,j,0,0},raw)==(uint32_t)(1+a+D*(j+width*h)),"ordinary output restoration mismatch");outputs++;}
            hs113::require(g.result.common==(width==1),"q1 common-chain dispatch");cases++;
        }
    }
    return {{"status","PASS"},{"actual_full_snapshot_graph_cases",cases},{"Q_mask_native_word_checks",checked},{"synthetic_AV_restore_word_checks",outputs},{"arithmetic_computes",0},{"CUDA_queries",0},{"scope","actual GGML storage graph CPU interpreter, not numerical or backend qualification"}};
}
