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
#include <chrono>
#include <cmath>
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
static int gpu_run(const J&job,const fs::path&out){
    hs113::require(job.contains("approved_stage_F0"),"separate S1 approval binding missing");fs::path root=job.at("root").get<std::string>(),runtime=job.at("runtime_directory").get<std::string>();
    hs113::require(!fs::exists(out),"immutable scientific output");fs::create_directories(out);J m=read(root/"snapshot.json");std::string kind=job.at("kind"),layout=job.at("layout");
    hs113::require(kind=="numeric"||kind=="clean"||kind=="trace","bounded host mode");SetDllDirectoryW(runtime.wstring().c_str());
    hs113::require(ggml_backend_load((runtime/"ggml-cuda.dll").string().c_str()),"CUDA plugin unavailable");auto backend=ggml_backend_init_by_name("CUDA0",nullptr);hs113::require(backend,"CUDA0 unavailable");
    auto cudart=GetModuleHandleW(L"cudart64_12.dll");hs113::require(cudart,"actual pinned cudart module absent");auto complete=(int(*)())GetProcAddress(cudart,"cudaDeviceSynchronize");hs113::require(complete,"device-wide completion unavailable");
    Graph g(m,layout,kind=="numeric");auto support=g.registry(backend);for(const auto&n:support["nodes"])if(!n["metadata_only"].get<bool>())hs113::require(n["CUDA_support"]==true,"unsupported executable node; CPU fallback forbidden");
    auto buffer=ggml_backend_alloc_ctx_tensors(g.ctx,backend);hs113::require(buffer,"CUDA allocation failed");
    for(int i=0;i<ggml_graph_n_nodes(g.g);i++){auto*t=ggml_graph_node(g.g,i);if(!metadata(t->op))hs113::require(t->buffer&&!ggml_backend_buffer_is_host(t->buffer)&&ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer))==ggml_backend_get_device(backend),"actual allocation placement mismatch");}
    const char*roles[]={"Q","K","V","mask"};std::vector<std::vector<unsigned char>>initial;
    for(int i=0;i<4;i++){initial.push_back(bytes(root/m[roles[i]]["file"].get<std::string>()));hs113::require(initial.back().size()==ggml_nbytes(g.in[i]),"whole input span mismatch");ggml_backend_tensor_set(g.in[i],initial.back().data(),0,initial.back().size());}
    hs113::require(complete()==0,"setup completion failure");
    for(int i=0;i<4;i++){std::vector<unsigned char>b(initial[i].size());ggml_backend_tensor_get(g.in[i],b.data(),0,b.size());hs113::require(b==initial[i],"full input before-start readback differs");}
    int warmup=kind=="numeric"?0:1,count=kind=="clean"?8:1;J times=J::array(),intervals=J::array();std::vector<unsigned char>expected;int starts=0;
    for(int i=-warmup;i<count;i++){
        write(out/("GRAPH_STARTED_"+std::to_string(starts)+".json"),{{"index",starts},{"warmup",i<0}});starts++;
        auto begin=std::chrono::steady_clock::now();auto rc=ggml_backend_graph_compute(backend,g.g);hs113::require(rc==GGML_STATUS_SUCCESS&&complete()==0,"compute/completion failed");auto end=std::chrono::steady_clock::now();
        std::vector<unsigned char>b(ggml_nbytes(g.result.ordinary));ggml_backend_tensor_get(g.result.ordinary,b.data(),0,b.size());if(expected.empty())expected=b;else hs113::require(b==expected,"within-host output repeatability failed");
        if(i>=0){times.push_back(std::chrono::duration<double,std::milli>(end-begin).count());intervals.push_back({{"begin_ns",std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count()},{"end_ns",std::chrono::duration_cast<std::chrono::nanoseconds>(end.time_since_epoch()).count()}});}
    }
    for(int i=0;i<4;i++){std::vector<unsigned char>b(initial[i].size());ggml_backend_tensor_get(g.in[i],b.data(),0,b.size());hs113::require(b==initial[i],"full input mutation");}
    auto dump=[&](const char*name,ggml_tensor*t){std::vector<unsigned char>b(ggml_nbytes(t));ggml_backend_tensor_get(t,b.data(),0,b.size());std::ofstream f(out/(std::string(name)+".bin"),std::ios::binary);f.write((char*)b.data(),b.size());hs113::require(bool(f),"tensor write failed");};
    if(kind=="numeric"){dump("QK",g.result.stage[0]);dump("softmax",g.result.stage[1]);dump("AV",g.result.stage[2]);}dump("ordinary",g.result.ordinary);
    write(out/"RECORD.json",{{"status","COMPLETED"},{"layout",layout},{"kind",kind},{"graph_computes",starts},{"warmups",warmup},{"completed_host_wall_ms",times},{"raw_completed_intervals",intervals},{"pid",GetCurrentProcessId()},{"synchronization","explicit cudaDeviceSynchronize, all device streams; inclusive host wall, not kernel time"},{"input_reset_and_postcheck",true},{"nodes",g.registry(backend)},{"modules",modules()},{"profile","PROFILE_UNAVAILABLE_PLACEMENT_ONLY"},{"kernel_names",nullptr},{"DRAM_bytes",nullptr}});
    ggml_backend_buffer_free(buffer);ggml_backend_free(backend);return 0;
}
int main(int argc,char**argv){try{
    hs113::require(argc==4,"usage native113 --cpu-registry|--cpu-negatives|--gpu-census plan output");std::string mode=argv[1];J plan=read(argv[2]);
    if(mode=="--cpu-negatives"){
        J bad=plan["descriptors"][0]["metadata"]["Q"];int rejected=0;
        for(int kind=0;kind<5;kind++){auto x=bad;if(kind==0)x["ne"][0]=true;if(kind==1)x["nb"][1]=1;if(kind==2)x["ne"][0]=0;if(kind==3)x["nb"][2]=4;if(kind==4)x["type"]=3;try{span(x);}catch(...){rejected++;}}
        hs113::require(rejected==5,"malformed descriptor accepted");write(argv[3],{{"CPU_negative_cases",rejected},{"status","PASS"},{"modules",modules()},{"GPU_calls",0}});return 0;
    }
    if(mode=="--cpu-addresses"){write(argv[3],address_tests(plan));return 0;}
    if(mode=="--gpu-run")return gpu_run(plan,argv[3]);
    bool gpu=mode=="--gpu-census";hs113::require(gpu||mode=="--cpu-registry","unknown mode");ggml_backend_t backend=nullptr;
    if(gpu){hs113::require(plan.contains("approved_stage_F0")&&plan["approved_stage_F0"].is_string(),"missing separately approved S1 F0 binding");
        auto runtime=fs::path(plan.at("runtime_directory").get<std::string>());SetDllDirectoryW(runtime.wstring().c_str());auto path=runtime/"ggml-cuda.dll";hs113::require(ggml_backend_load(path.string().c_str()),"pinned CUDA plugin load failed");backend=ggml_backend_init_by_name("CUDA0",nullptr);hs113::require(backend,"CUDA0 unavailable");}
    J records=J::array();int graphs=0;for(const auto&d:plan.at("descriptors"))for(const std::string name:{"MQ","PQ","QB","QH_C","QH_D"})for(bool stages:{false,true}){
        Graph graph(d.at("metadata"),name,stages);auto r=graph.registry(backend);r["descriptor_id"]=d.at("id");r["layout"]=name;r["stage_outputs"]=stages;records.push_back(r);graphs++;
    }
    write(argv[3],{{"mode",mode},{"graphs",graphs},{"records",records},{"modules",modules()},{"GPU_initializations",gpu?1:0},{"graph_computes",0},{"support_status",gpu?"ACTUAL_NODE_QUERIES_RECORDED":"NOT_QUERIED_S0"}});
    if(backend)ggml_backend_free(backend);return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
