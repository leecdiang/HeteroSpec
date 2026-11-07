#define NOMINMAX
#include <windows.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "gguf.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
#include <cmath>
using json=nlohmann::json;namespace fs=std::filesystem;
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
json readj(const fs::path&p){std::ifstream f(p);need(bool(f),"JSON missing");json j;f>>j;return j;}
std::vector<char> readb(const fs::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"payload missing");return {(std::istreambuf_iterator<char>(f)),{}};}
void writej(const fs::path&p,const json&j){std::ofstream f(p);f<<j.dump(2)<<'\n';need(bool(f),"write JSON");}
void writeb(const fs::path&p,const std::vector<char>&v){std::ofstream f(p,std::ios::binary);f.write(v.data(),v.size());need(bool(f),"write binary");}
int main(int argc,char**argv){
 ggml_backend_t backend=nullptr;ggml_backend_buffer_t buffer=nullptr;ggml_context*ctx=nullptr;gguf_context*gguf=nullptr;fs::path out;
 json result={{"status","STARTED"},{"rows",json::array()},{"resources",json::array()},{"model_requests",0}};
 auto clear=[&](){if(buffer){ggml_backend_buffer_free(buffer);buffer=nullptr;}if(ctx){ggml_free(ctx);ctx=nullptr;}};
 auto cleanup=[&](){clear();if(backend){ggml_backend_free(backend);backend=nullptr;}if(gguf){gguf_free(gguf);gguf=nullptr;}};
 try{
  need(argc==3,"q8_replay CONFIG OUT");auto config=readj(argv[1]);out=argv[2];need(!fs::exists(out),"fresh output");fs::create_directories(out/"weights");
  const bool force_no_mmvq=config.value("force_no_mmvq",false);
  result["declared_disable_mmvq_intervention"]=force_no_mmvq;
  if(force_no_mmvq)need(_putenv_s("GGML_VK_DISABLE_MMVQ","1")==0,"declared MMVQ intervention");
  ggml_backend_load_all();ggml_backend_dev_t dev=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*d=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d)).find("B570")!=std::string::npos){need(!dev,"ambiguous device");dev=d;}}
  need(dev,"B570 absent");backend=ggml_backend_dev_init(dev,nullptr);need(backend,"backend initialization");
  result["device"]=ggml_backend_dev_description(dev);
  std::string model=config.at("target_model");gguf=gguf_init_from_file(model.c_str(),{true,nullptr});need(gguf,"GGUF metadata");
  bool all=true;
  for(const auto&fixture:config.at("fixtures")){
   size_t free=0,total=0;ggml_backend_dev_memory(dev,&free,&total);MEMORYSTATUSEX ram{};ram.dwLength=sizeof(ram);need(GlobalMemoryStatusEx(&ram),"RAM query");
   result["resources"].push_back({{"device_free_bytes",free},{"device_total_bytes",total},{"ram_available_bytes",ram.ullAvailPhys}});
   need(free>=512ULL*1024*1024&&ram.ullAvailPhys>=2ULL*1024*1024*1024,"resource reserve");
   auto im=readj(fixture.at("input_meta").get<std::string>());auto om=readj(fixture.at("output_meta").get<std::string>());
   auto activation=readb(fixture.at("input_payload").get<std::string>());auto expected=readb(fixture.at("output_payload").get<std::string>());
   std::string weight=fixture.at("weight");int64_t ti=gguf_find_tensor(gguf,weight.c_str());need(ti>=0,"weight missing");auto wn=gguf_get_tensor_ne(gguf,ti);
   need(gguf_get_tensor_type(gguf,ti)==GGML_TYPE_Q8_0&&wn[2]==1&&wn[3]==1,"Q8 matrix contract");
   need(im["type"]=="f32"&&im["op"]=="MUL"&&im["name"]=="attn_norm-0","captured pre-projection producer");
   need(om["op"]=="MUL_MAT"&&om["sources"][0]["name"]==weight&&om["sources"][1]["name"]==im["name"],"native operand ownership");
   int q=fixture.at("q");need(q==1||q==4,"registered replay widths");
   need(im["ne"]==json::array({wn[0],q,1,1})&&om["ne"]==json::array({wn[1],q,1,1}),"replay shape");
   size_t offset=gguf_get_data_offset(gguf)+gguf_get_tensor_offset(gguf,ti),size=gguf_get_tensor_size(gguf,ti);
   std::vector<char>w(size);std::ifstream model_file(model,std::ios::binary);model_file.seekg(offset);model_file.read(w.data(),size);need(bool(model_file),"immutable weight bytes");
   fs::path wp=out/"weights"/(weight+".bin");if(!fs::exists(wp))writeb(wp,w);
   ctx=ggml_init({16*1024*1024,nullptr,true});need(ctx,"graph metadata allocation");
   auto*W=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,wn[0],wn[1]);ggml_set_name(W,weight.c_str());
   auto*X=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,wn[0],q);ggml_set_name(X,"captured_attn_norm");
   auto*Y=ggml_mul_mat(ctx,W,X);ggml_set_name(Y,om["name"].get<std::string>().c_str());
   auto params=om["op_params_i32"].get<std::vector<int32_t>>();need(params.size()*4==GGML_MAX_OP_PARAMS,"operator parameter bytes");std::memcpy(Y->op_params,params.data(),GGML_MAX_OP_PARAMS);
   const bool intervene=fixture.value("reference_f32_activation",false);
   if(intervene)ggml_mul_mat_set_prec(Y,GGML_PREC_F32);
   need(activation.size()==ggml_nbytes(X)&&expected.size()==ggml_nbytes(Y),"complete operand/output bytes");
   for(int j=0;j<4;j++){need(W->ne[j]==om["sources"][0]["ne"][j].get<int64_t>()&&W->nb[j]==om["sources"][0]["nb"][j].get<size_t>(),"immutable weight geometry");need(X->nb[j]==im["nb"][j].get<size_t>()&&Y->nb[j]==om["nb"][j].get<size_t>(),"actual tensor strides");}
   need(ggml_backend_dev_supports_op(dev,Y),"native Vulkan operation unsupported");
   auto*g=ggml_new_graph(ctx);ggml_build_forward_expand(g,Y);buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer,"backend allocation");
   ggml_backend_tensor_set(W,w.data(),0,w.size());ggml_backend_tensor_set(X,activation.data(),0,activation.size());
   need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"graph compute");ggml_backend_synchronize(backend);
   std::vector<char>actual(ggml_nbytes(Y));ggml_backend_tensor_get(Y,actual.data(),0,actual.size());
   size_t differences=0;double maxabs=0;for(size_t j=0;j<actual.size();j+=4){float a,b;std::memcpy(&a,actual.data()+j,4);std::memcpy(&b,expected.data()+j,4);need(std::isfinite(a)&&std::isfinite(b),"finite results");differences+=std::memcmp(actual.data()+j,expected.data()+j,4)!=0;maxabs=std::max(maxabs,double(std::abs(a-b)));}
   std::string id=fixture.at("id");writeb(out/(id+".bin"),actual);all=all&&actual==expected;
   result["rows"].push_back({{"id",id},{"q",q},{"weight",weight},{"weight_offset",offset},{"weight_bytes",size},{"native_expected_meta",fixture.at("output_meta")},{"reference_f32_activation",intervene},{"bitwise_expected",actual==expected},{"different_fp32_words",differences},{"max_abs",maxabs}});
   writej(out/"result.json",result);clear();
  }
  result["status"]=all?config.value("expected_status",std::string("OWN_PATH_REPLAY_PASS")):"REPLAY_EXPECTATION_FAILURE";cleanup();result["normal_cleanup_returned"]=true;writej(out/"result.json",result);return all?0:3;
 }catch(const std::exception&e){result["status"]="FAILED";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;if(!out.empty())writej(out/"result.json",result);std::cerr<<e.what()<<'\n';return 2;}
}
