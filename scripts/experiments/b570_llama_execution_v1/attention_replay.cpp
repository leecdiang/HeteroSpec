#define NOMINMAX
#include <windows.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "query_head.h"
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
  need(argc==3,"attention_replay CONFIG OUT");auto config=readj(argv[1]);out=argv[2];need(!fs::exists(out),"fresh output");fs::create_directories(out);
  ggml_backend_load_all();ggml_backend_dev_t dev=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*d=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d)).find("B570")!=std::string::npos){need(!dev,"ambiguous B570");dev=d;}}
  need(dev,"B570 missing");backend=ggml_backend_dev_init(dev,nullptr);need(backend,"backend initialization");
  bool all=true;
  for(const auto&fixture:config.at("fixtures"))for(int q:{1,2,3,4})for(std::string arm:{"PQ","QB"}){
   size_t free=0,total=0;ggml_backend_dev_memory(dev,&free,&total);MEMORYSTATUSEX ram{};ram.dwLength=sizeof(ram);need(GlobalMemoryStatusEx(&ram),"RAM query");
   result["resources"].push_back({{"device_free_bytes",free},{"ram_available_bytes",ram.ullAvailPhys}});need(free>=512ULL*1024*1024&&ram.ullAvailPhys>=2ULL*1024*1024*1024,"reserve");
   ctx=ggml_init({16*1024*1024,nullptr,true});need(ctx,"context allocation");
   std::vector<std::pair<ggml_tensor*,std::vector<char>>>uploads;
   auto input=[&](const std::string&key){
    auto j=readj(fixture.at(key+"_meta").get<std::string>());auto bytes=readb(fixture.at(key+"_payload").get<std::string>());
    need(j["source_output_disjoint"]==true,"source alias failure");need(bytes.size()==j["span_bytes"].get<size_t>(),"source span");
    need(j["type"]=="f32"||j["type"]=="f16","attention input type");auto type=j["type"]=="f32"?GGML_TYPE_F32:GGML_TYPE_F16;
    auto*s=ggml_new_tensor_1d(ctx,type,bytes.size()/ggml_type_size(type));
    auto*t=ggml_view_4d(ctx,s,j["ne"][0],j["ne"][1],j["ne"][2],j["ne"][3],j["nb"][1],j["nb"][2],j["nb"][3],0);
    need(t->nb[0]==j["nb"][0].get<size_t>()&&ggml_nbytes(t)==bytes.size(),"actual operand strides/span");uploads.push_back({s,std::move(bytes)});return t;
   };
   auto*rawq=input("Q");auto*k=input("K");auto*v=input("V");auto*rawmask=input("mask");const int64_t n=k->ne[1];
   need(rawq->ne[0]==128&&rawq->ne[1]==1&&rawq->ne[2]==32&&rawq->ne[3]==4,"actual q4 head/query axes");
   need(n>=256&&n<=1024&&n%256==0&&k->ne[2]==8&&v->ne[0]==n,"registered expanded key/GQA domain");
   need(rawmask->ne[0]==n&&rawmask->ne[3]==4,"actual mask axes");
   auto*Q=ggml_view_4d(ctx,rawq,128,q,32,1,rawq->nb[3],rawq->nb[2],rawq->nb[3]*4,0);
   auto*mask=ggml_view_4d(ctx,rawmask,n,q,1,1,rawmask->nb[3],rawmask->nb[3]*4,rawmask->nb[3]*4,0);
   auto sm=readj(fixture.at("softmax_meta").get<std::string>());auto sp=sm["op_params_i32"].get<std::vector<int32_t>>();float scale,bias;std::memcpy(&scale,&sp[0],4);std::memcpy(&bias,&sp[1],4);need(bias==0,"mask bias");
   auto built=hs_qh::build(ctx,arm=="PQ"?hs_qh::Mode::PQ:hs_qh::Mode::QB4,Q,k,v,mask,scale);
   if(built.common_original){auto*s=ggml_mul_mat(ctx,k,Q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);auto*p=ggml_soft_max_ext(ctx,s,mask,scale,0);auto*a=ggml_mul_mat(ctx,v,p);built.scores={s};built.probs={p};built.values={a};built.out=ggml_cont_2d(ctx,ggml_permute(ctx,a,0,2,1,3),4096,q);}
   auto bind=[&](const char*key,const std::vector<ggml_tensor*>&ts){auto meta=readj(fixture.at(std::string(key)+"_meta").get<std::string>());auto params=meta["op_params_i32"].get<std::vector<int32_t>>();need(params.size()*4==GGML_MAX_OP_PARAMS,"complete native operator parameters");for(auto*t:ts){need(meta["op"]==ggml_op_name(t->op),"same native operation");std::memcpy(t->op_params,params.data(),GGML_MAX_OP_PARAMS);}};
   bind("qk",built.scores);bind("softmax",built.probs);bind("av",built.values);
   auto*g=ggml_new_graph(ctx);ggml_build_forward_expand(g,built.out);int numerical=0;
   for(int i=0;i<ggml_graph_n_nodes(g);i++){auto*t=ggml_graph_node(g,i);need(ggml_backend_dev_supports_op(dev,t),"Vulkan operation unsupported");if(t->op!=GGML_OP_VIEW&&t->op!=GGML_OP_RESHAPE&&t->op!=GGML_OP_PERMUTE&&t->op!=GGML_OP_TRANSPOSE)numerical++;}
   buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer,"backend allocation");for(auto&u:uploads)ggml_backend_tensor_set(u.first,u.second.data(),0,u.second.size());
   need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"compute");ggml_backend_synchronize(backend);
   std::string id=fixture.at("id");id+="-q"+std::to_string(q)+"-"+arm;json row={{"id",id},{"q",q},{"arm",arm},{"physical_keys",n},{"numerical_graph_nodes",numerical},{"stages",json::object()}};
   auto compare=[&](const std::string&key,const std::vector<ggml_tensor*>&ts){
    std::vector<char>a;for(auto*t:ts){need(ggml_is_contiguous(t),"stage output layout");size_t off=a.size();a.resize(off+ggml_nbytes(t));ggml_backend_tensor_get(t,a.data()+off,0,ggml_nbytes(t));}
    auto expected=readb(fixture.at(key+"_payload").get<std::string>());need(a.size()*4==expected.size()*size_t(q),"first-q real query slices");bool equal=std::memcmp(a.data(),expected.data(),a.size())==0;all=all&&equal;
    std::ofstream f(out/(id+"-"+key+".bin"),std::ios::binary);f.write(a.data(),a.size());row["stages"][key]={{"bytes",a.size()},{"bitwise_equal",equal}};
   };
   compare("qk",built.scores);compare("softmax",built.probs);compare("av",built.values);compare("final",{built.out});result["rows"].push_back(row);writej(out/"result.json",result);clear();
  }
  clear();ggml_backend_free(backend);backend=nullptr;result["status"]=all?"REAL_ATTENTION_REPLAY_PASS":"REAL_ATTENTION_REPLAY_FAILURE";result["normal_cleanup_returned"]=true;writej(out/"result.json",result);return all?0:3;
 }catch(const std::exception&e){clear();if(backend)ggml_backend_free(backend);result["status"]="FAILED";result["error"]=e.what();result["normal_cleanup_returned"]=true;if(!out.empty())writej(out/"result.json",result);std::cerr<<e.what()<<'\n';return 2;}
}
