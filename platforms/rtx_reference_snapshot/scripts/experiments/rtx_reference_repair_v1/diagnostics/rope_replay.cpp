#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
#include <stdexcept>
#include <chrono>
using json=nlohmann::json;namespace fs=std::filesystem;
void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
json modules(){HMODULE m[1024];DWORD n=0;need(EnumProcessModules(GetCurrentProcess(),m,sizeof(m),&n),"module inventory");json a=json::array();for(size_t i=0;i<n/sizeof(HMODULE);++i){char p[32768];need(GetModuleFileNameExA(GetCurrentProcess(),m[i],p,sizeof(p)),"module path");a.push_back(std::string(p));}return a;}
std::vector<char> bytes(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"input open");auto n=f.tellg();need(n>0&&n<=1024*1024,"operand bound");std::vector<char>b(static_cast<size_t>(n));f.seekg(0);f.read(b.data(),b.size());need(bool(f),"input read");return b;}
int main(int argc,char**argv){
 try{
  SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
  need(argc==4,"manifest output dll-dir");json spec;{std::ifstream f(argv[1]);f>>spec;}
  fs::path out=argv[2];need(!fs::exists(out),"fresh output required");fs::create_directories(out);
  ggml_backend_load_all_from_path(argv[3]);
  auto cpu=ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_CPU,nullptr);auto gpu=ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_GPU,nullptr);need(cpu&&gpu,"CPU/CUDA backends required");
  auto reg=ggml_backend_dev_backend_reg(ggml_backend_get_device(cpu));using set_threads=void(*)(ggml_backend_t,int);
  auto set=reinterpret_cast<set_threads>(ggml_backend_reg_get_proc_address(reg,"ggml_backend_set_n_threads"));need(set,"thread control missing");set(cpu,24);
  std::cout<<json({{"event","READY"}}).dump()<<std::endl;std::string permission;std::getline(std::cin,permission);need(permission=="RUN","owned execution handshake");
  json result={{"status","RUNNING"},{"model_requests",0},{"operator_replays",0},{"threads",24},{"results",json::array()}};
  for(const auto& item:spec.at("operands")){
   auto shape=item.at("shape").get<std::vector<int64_t>>();auto params=item.at("op_params_i32").get<std::vector<int32_t>>();auto positions=item.at("positions_i32").get<std::vector<int32_t>>();
   need(shape==std::vector<int64_t>({128,8,int64_t(positions.size()),1})&&(positions.size()==1||positions.size()==4),"pinned K RoPE shape");need(params.size()*sizeof(int32_t)==GGML_MAX_OP_PARAMS,"complete op parameters");
   auto input=bytes(item.at("input_file").get<std::string>());need(input.size()==128*8*positions.size()*sizeof(float),"operand size");
   auto value=[&](int i){float v;std::memcpy(&v,&params.at(i),4);return v;};
   for(auto backend:{cpu,gpu})for(int repetition=0;repetition<2;++repetition){
    auto start=std::chrono::steady_clock::now();auto*ctx=ggml_init({4*1024*1024,nullptr,true});need(ctx,"context");
    auto*a=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,shape[0],shape[1],shape[2],shape[3]);auto*p=ggml_new_tensor_1d(ctx,GGML_TYPE_I32,positions.size());
    auto*y=ggml_rope_ext(ctx,a,p,nullptr,params[1],params[2],params[4],value(5),value(6),value(7),value(8),value(9),value(10));
    std::memcpy(y->op_params,params.data(),GGML_MAX_OP_PARAMS);auto*g=ggml_new_graph_custom(ctx,128,false);ggml_build_forward_expand(g,y);
    auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer,"backend allocation");ggml_backend_tensor_set(a,input.data(),0,input.size());ggml_backend_tensor_set(p,positions.data(),0,positions.size()*4);
    need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"native RoPE compute");ggml_backend_synchronize(backend);
    std::vector<char> output(ggml_nbytes(y));ggml_backend_tensor_get(y,output.data(),0,output.size());
    auto name=item.at("name").get<std::string>()+"_"+ggml_backend_name(backend)+"_"+std::to_string(repetition)+".f32";{std::ofstream f(out/name,std::ios::binary);f.write(output.data(),output.size());need(bool(f),"output write");}
    result["results"].push_back({{"operand",item.at("name")},{"backend",ggml_backend_name(backend)},{"repetition",repetition},{"output",name},{"bytes",output.size()},{"seconds",std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()}});
    ggml_backend_buffer_free(buffer);ggml_free(ctx);
   }
  }
  result["modules"]=modules();ggml_backend_free(gpu);ggml_backend_free(cpu);result["operator_replays"]=result["results"].size();result["normal_cleanup_returned"]=true;result["status"]="COMPLETE";
  {std::ofstream f(out/"RESULT.json");f<<result.dump(2)<<'\n';need(bool(f),"result write");}std::cout<<json({{"event","COMPLETE"},{"operator_replays",result["operator_replays"]}}).dump()<<std::endl;
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}
}
