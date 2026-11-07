#define NOMINMAX
#include <windows.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
using json=nlohmann::json;namespace fs=std::filesystem;
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
json readj(const fs::path&p){std::ifstream f(p);need(bool(f),"metadata missing");json j;f>>j;return j;}
std::vector<char>readb(const fs::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"payload missing");return {(std::istreambuf_iterator<char>(f)),{}};}
void writej(const fs::path&p,const json&j){std::ofstream f(p);f<<j.dump(2)<<'\n';need(bool(f),"write metadata");}
int main(int argc,char**argv){
 ggml_backend_t backend=nullptr;ggml_context*ctx=nullptr;ggml_backend_buffer_t buffer=nullptr;fs::path out;
 json result={{"status","STARTED"},{"rows",json::array()},{"model_requests",0},{"resources",json::array()}};
 auto clear=[&](){if(buffer){ggml_backend_buffer_free(buffer);buffer=nullptr;}if(ctx){ggml_free(ctx);ctx=nullptr;}};
 try{
  need(argc==3,"av_replay CONFIG OUT");auto config=readj(argv[1]);out=argv[2];need(!fs::exists(out),"fresh output");fs::create_directories(out);
  ggml_backend_load_all();ggml_backend_dev_t dev=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*d=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d)).find("B570")!=std::string::npos){need(!dev,"ambiguous B570");dev=d;}}
  need(dev,"B570 missing");backend=ggml_backend_dev_init(dev,nullptr);need(backend,"backend initialization");bool all=true;
  for(const auto&f:config.at("fixtures")){
   size_t free=0,total=0;ggml_backend_dev_memory(dev,&free,&total);MEMORYSTATUSEX ram{};ram.dwLength=sizeof(ram);need(GlobalMemoryStatusEx(&ram),"RAM query");result["resources"].push_back({{"device_free_bytes",free},{"ram_available_bytes",ram.ullAvailPhys}});need(free>=512ULL*1024*1024&&ram.ullAvailPhys>=2ULL*1024*1024*1024,"reserve");
   ctx=ggml_init({8*1024*1024,nullptr,true});need(ctx,"metadata allocation");std::vector<std::pair<ggml_tensor*,std::vector<char>>>uploads;
   auto input=[&](const char*key){std::string k=key;auto j=readj(f.at(k+"_meta").get<std::string>());auto bytes=readb(f.at(k+"_payload").get<std::string>());need(j["type"]=="f16"||j["type"]=="f32","real dtype");auto type=j["type"]=="f16"?GGML_TYPE_F16:GGML_TYPE_F32;need(bytes.size()==j["span_bytes"].get<size_t>(),"real span");auto*s=ggml_new_tensor_1d(ctx,type,bytes.size()/ggml_type_size(type));auto*t=ggml_view_4d(ctx,s,j["ne"][0],j["ne"][1],j["ne"][2],j["ne"][3],j["nb"][1],j["nb"][2],j["nb"][3],0);need(t->nb[0]==j["nb"][0].get<size_t>()&&ggml_nbytes(t)==bytes.size(),"real stride");uploads.push_back({s,std::move(bytes)});return t;};
   auto*V=input("V");auto*P=input("P");need(V->type==GGML_TYPE_F16&&P->type==GGML_TYPE_F32,"AV contract");auto*Y=ggml_mul_mat(ctx,V,P);
   auto om=readj(f.at("output_meta").get<std::string>());auto params=om["op_params_i32"].get<std::vector<int32_t>>();need(params.size()*4==GGML_MAX_OP_PARAMS,"operator parameters");std::memcpy(Y->op_params,params.data(),GGML_MAX_OP_PARAMS);
   for(int i=0;i<4;i++)need(Y->ne[i]==om["ne"][i].get<int64_t>()&&Y->nb[i]==om["nb"][i].get<size_t>(),"complete output geometry");
   auto*g=ggml_new_graph(ctx);ggml_build_forward_expand(g,Y);need(ggml_backend_dev_supports_op(dev,Y),"AV unsupported");buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer,"allocation");for(auto&u:uploads)ggml_backend_tensor_set(u.first,u.second.data(),0,u.second.size());
   need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"compute");ggml_backend_synchronize(backend);std::vector<char>actual(ggml_nbytes(Y));ggml_backend_tensor_get(Y,actual.data(),0,actual.size());auto expected=readb(f.at("output_payload").get<std::string>());need(actual.size()==expected.size(),"full expected vector");bool equal=actual==expected;all=all&&equal;
   std::string id=f.at("id");std::ofstream payload(out/(id+".bin"),std::ios::binary);payload.write(actual.data(),actual.size());payload.close();result["rows"].push_back({{"id",id},{"physical_keys",V->ne[0]},{"query_batch",P->ne[3]},{"bitwise_expected",equal},{"bytes",actual.size()}});writej(out/"result.json",result);clear();
  }
  clear();ggml_backend_free(backend);backend=nullptr;result["status"]=all?config.at("expected_status"):json("AV_REPLAY_FAILURE");result["normal_cleanup_returned"]=true;writej(out/"result.json",result);return all?0:3;
 }catch(const std::exception&e){clear();if(backend)ggml_backend_free(backend);result["status"]="FAILED";result["error"]=e.what();result["normal_cleanup_returned"]=true;if(!out.empty())writej(out/"result.json",result);std::cerr<<e.what()<<'\n';return 2;}
}
