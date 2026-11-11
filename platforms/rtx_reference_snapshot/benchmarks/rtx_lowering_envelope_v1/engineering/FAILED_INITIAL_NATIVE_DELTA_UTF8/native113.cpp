#include "hs113_graph.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <windows.h>
#include <psapi.h>
using J=nlohmann::ordered_json;namespace fs=std::filesystem;
static J read(const fs::path&p){std::ifstream f(p);hs113::require(bool(f),"missing JSON");J j;f>>j;return j;}
static void write(const fs::path&p,const J&j){hs113::require(!fs::exists(p),"immutable output exists");fs::create_directories(p.parent_path());std::ofstream f(p);f<<j.dump(2)<<"\n";hs113::require(bool(f),"write failed");}
static std::vector<unsigned char> bytes(const fs::path&p){std::ifstream f(p,std::ios::binary);hs113::require(bool(f),"missing tensor bytes");return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
static int64_t integer(const J&j,int64_t low,int64_t high){hs113::require(j.is_number_integer()&&!j.is_boolean(),"strict integer required");auto n=j.get<int64_t>();hs113::require(n>=low&&n<=high,"integer outside domain");return n;}
static size_t span(const J&m){
    hs113::require(m.at("ne").size()==4&&m.at("nb").size()==4,"four dimensions required");
    const int type=(int)integer(m.at("type"),0,1);const size_t word=type==0?4:2;size_t total=word;std::vector<std::pair<size_t,size_t>>dims;
    for(int i=0;i<4;i++){auto ne=integer(m["ne"][i],1,1024*128),nb=integer(m["nb"][i],word,1024LL*1024*64);hs113::require(nb%word==0,"unaligned stride");total+=(ne-1)*nb;if(ne>1)dims.push_back({nb,(size_t)ne});}
    std::sort(dims.begin(),dims.end());size_t owner=word;for(auto x:dims){hs113::require(x.first>=owner,"overlapping owner view");owner+=(x.second-1)*x.first;}
    hs113::require(total<=64*1024*1024,"bounded input span");return total;
}
static ggml_tensor* input(ggml_context*ctx,const J&m){span(m);int64_t ne[4];for(int i=0;i<4;i++)ne[i]=m["ne"][i].get<int64_t>();auto*t=ggml_new_tensor(ctx,(ggml_type)m["type"].get<int>(),4,ne);for(int i=0;i<4;i++)t->nb[i]=m["nb"][i].get<size_t>();ggml_set_input(t);return t;}
static bool metadata(ggml_op op){return op==GGML_OP_NONE||op==GGML_OP_VIEW||op==GGML_OP_RESHAPE||op==GGML_OP_PERMUTE||op==GGML_OP_TRANSPOSE;}
static J descriptor(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"type",int(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"bytes",ggml_nbytes(t)},{"op_params",std::vector<unsigned char>((unsigned char*)t->op_params,(unsigned char*)t->op_params+GGML_MAX_OP_PARAMS)},{"metadata_only",metadata(t->op)}};}
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
        return {{"common_q1_original_arithmetic_chain",result.common},{"nodes",nodes},{"full_support",nullptr},{"actual_placement",nullptr},{"output",descriptor(result.ordinary)}};
    }
};
int main(int argc,char**argv){try{
    hs113::require(argc==4,"usage native113 --cpu-registry|--cpu-negatives|--gpu-census plan output");std::string mode=argv[1];J plan=read(argv[2]);
    if(mode=="--cpu-negatives"){
        J bad=plan["descriptors"][0]["metadata"]["Q"];int rejected=0;
        for(int kind=0;kind<5;kind++){auto x=bad;if(kind==0)x["ne"][0]=true;if(kind==1)x["nb"][1]=1;if(kind==2)x["ne"][0]=0;if(kind==3)x["nb"][2]=4;if(kind==4)x["type"]=3;try{span(x);}catch(...){rejected++;}}
        hs113::require(rejected==5,"malformed descriptor accepted");write(argv[3],{{"CPU_negative_cases",rejected},{"status","PASS"},{"modules",modules()},{"GPU_calls",0}});return 0;
    }
    bool gpu=mode=="--gpu-census";hs113::require(gpu||mode=="--cpu-registry","unknown mode");ggml_backend_t backend=nullptr;
    if(gpu){hs113::require(plan.contains("approved_stage_F0")&&plan["approved_stage_F0"].is_string(),"missing separately approved S1 F0 binding");
        auto path=fs::path(plan.at("runtime_directory").get<std::string>())/"ggml-cuda.dll";hs113::require(ggml_backend_load(path.string().c_str()),"pinned CUDA plugin load failed");backend=ggml_backend_init_by_name("CUDA0",nullptr);hs113::require(backend,"CUDA0 unavailable");}
    J records=J::array();int graphs=0;for(const auto&d:plan.at("descriptors"))for(const std::string name:{"MQ","PQ","QB","QH_C","QH_D"})for(bool stages:{false,true}){
        Graph graph(d.at("metadata"),name,stages);auto r=graph.registry(backend);r["descriptor_id"]=d.at("id");r["layout"]=name;r["stage_outputs"]=stages;records.push_back(r);graphs++;
    }
    write(argv[3],{{"mode",mode},{"graphs",graphs},{"records",records},{"modules",modules()},{"GPU_initializations",gpu?1:0},{"graph_computes",0},{"support_status",gpu?"ACTUAL_NODE_QUERIES_RECORDED":"NOT_QUERIED_S0"}});
    if(backend)ggml_backend_free(backend);return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
