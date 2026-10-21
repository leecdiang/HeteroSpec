#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "nlohmann/json.hpp"
#include "native_memory_budget.h"
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
#include <iomanip>
#include <sstream>
using json=nlohmann::ordered_json;
std::string sha(const void*d,size_t n){BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;ULONG z=0,l=0;BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0);BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,(PUCHAR)&l,4,&z,0);std::vector<UCHAR>obj(l),v(32);BCryptCreateHash(a,&h,obj.data(),l,nullptr,0,0);BCryptHashData(h,(PUCHAR)d,ULONG(n),0);BCryptFinishHash(h,v.data(),32,0);BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);std::ostringstream o;for(auto b:v)o<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);return o.str();}
std::vector<uint8_t>read(const json&p){std::ifstream f(p.at("path").get<std::string>(),std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(f)),{});if(b.size()!=p.at("bytes").get<size_t>()||sha(b.data(),b.size())!=p.at("sha256").get<std::string>())throw std::runtime_error("Input pin");return b;}
int main(){try{
 std::string line;std::getline(std::cin,line);json q=json::parse(line);auto operands=q.at("operands");auto lens=q.at("schedule").get<std::vector<int>>();int N=q.at("N");std::string op=q.at("op");
 VkInstance instance{};VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.apiVersion=VK_API_VERSION_1_1;VkInstanceCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;ci.pApplicationInfo=&app;if(vkCreateInstance(&ci,nullptr,&instance))throw std::runtime_error("Vk instance");
 uint32_t nn=0;vkEnumeratePhysicalDevices(instance,&nn,nullptr);std::vector<VkPhysicalDevice>ds(nn);vkEnumeratePhysicalDevices(instance,&nn,ds.data());VkPhysicalDevice device{};VkPhysicalDeviceProperties prop{};for(auto d:ds){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(d,&p);if(p.vendorID==0x8086&&p.deviceID==0xE20C){device=d;prop=p;}}if(!device)throw std::runtime_error("B570");
 json mem=json::array();auto guard=[&](std::string point){json heaps=json::array();bool good=false;for(auto h:b570_opt::owned_process_memory(device)){int64_t free=int64_t(h.budget_bytes)-int64_t(h.usage_bytes);heaps.push_back({{"index",h.index},{"device_local",h.device_local},{"physical_size_bytes",h.physical_size_bytes},{"budget_bytes",h.budget_bytes},{"usage_bytes",h.usage_bytes},{"headroom",free}});if(h.device_local){if(h.index!=0||h.physical_size_bytes!=10563354624||free<536870912)throw std::runtime_error("Memory gate");good=true;}}if(!good)throw std::runtime_error("Dedicated heap");mem.push_back({{"pid",GetCurrentProcessId()},{"point",point},{"heaps",heaps}});};guard("BEFORE");
 ggml_backend_load_all();auto dev=ggml_backend_dev_by_name("Vulkan0");if(!dev||std::string(ggml_backend_dev_description(dev)).find("B570")==std::string::npos)throw std::runtime_error("WrongGPU");auto backend=ggml_backend_dev_init(dev,nullptr);if(!backend)throw std::runtime_error("Backend");std::cout<<json({{"event","REPLAY_READY"},{"pid",GetCurrentProcessId()},{"device","Vulkan0"},{"GPU_forward_calls",0}}).dump()<<std::endl;std::string ack;std::getline(std::cin,ack);if(ack!="RUN")throw std::runtime_error("Explicit admitted replay begin required");std::vector<std::vector<uint8_t>>full;for(auto j:operands)full.push_back(read(j["payload"]));
 json traces=json::array();std::vector<uint8_t>result;int offset=0;
 for(int count:lens){
  if(count<=0||offset+count>N)throw std::runtime_error("Schedule");
  ggml_init_params ip={8*1024*1024,nullptr,true};auto ctx=ggml_init(ip);std::vector<ggml_tensor*>ts;std::vector<std::vector<uint8_t>>inputs;
  for(size_t i=0;i<operands.size();++i){
   auto j=operands[i];auto ne=j["ne"].get<std::vector<int64_t>>();auto original=ne;int axis=j["token_axis"];if(axis>=0){if(axis!=1||ne[1]!=N||ne[2]!=1||ne[3]!=1)throw std::runtime_error("Unsupported logical alignment");ne[1]=count;}
   auto t=ggml_new_tensor(ctx,ggml_type(j["type"].get<int>()),4,ne.data());ggml_set_input(t);ts.push_back(t);
   if(axis<0)inputs.push_back(full[i]);else{size_t row=ggml_row_size(t->type,t->ne[0]);inputs.emplace_back(full[i].begin()+offset*row,full[i].begin()+(offset+count)*row);}
   if(inputs.back().size()!=ggml_nbytes(t))throw std::runtime_error("Noncontiguous source input");
  }
  ggml_tensor*out=nullptr;
  if(op=="RMS_NORM"){float eps;int p=q["op_params"][0];memcpy(&eps,&p,4);out=ggml_rms_norm(ctx,ts[0],eps);}
  else if(op=="MUL")out=ggml_mul(ctx,ts[0],ts[1]);
  else if(op=="MUL_MAT")out=ggml_mul_mat(ctx,ts[0],ts[1]);
  else throw std::runtime_error("Unsupported op");
  ggml_set_output(out);auto graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,out);
  auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);if(!buffer)throw std::runtime_error("Alloc");json inputrows=json::array();
  for(size_t i=0;i<ts.size();++i){ggml_backend_tensor_set(ts[i],inputs[i].data(),0,inputs[i].size());std::vector<uint8_t>b(inputs[i].size());ggml_backend_tensor_get(ts[i],b.data(),0,b.size());if(b!=inputs[i])throw std::runtime_error("Input readback not bitwise");inputrows.push_back({{"operand",i},{"bytes",b.size()},{"sha256",sha(b.data(),b.size())},{"source_full_sha256",operands[i]["payload"]["sha256"]},{"token_axis",operands[i]["token_axis"]}});}
  guard("ALLOCATED");if(ggml_backend_graph_compute(backend,graph)!=GGML_STATUS_SUCCESS)throw std::runtime_error("Graph failed");ggml_backend_synchronize(backend);std::vector<uint8_t>b(ggml_nbytes(out));ggml_backend_tensor_get(out,b.data(),0,b.size());result.insert(result.end(),b.begin(),b.end());
  traces.push_back({{"pos",offset},{"width",count},{"op",op},{"inputs",inputrows},{"output_sha256",sha(b.data(),b.size())},{"output_ne",json::array({out->ne[0],out->ne[1],out->ne[2],out->ne[3]})},{"GPU_pipeline",nullptr},{"dispatch_dimensions",nullptr},{"completion","ggml_backend_graph_compute + ggml_backend_synchronize + readback"}});
  ggml_backend_buffer_free(buffer);ggml_free(ctx);offset+=count;
 }
 if(offset!=N)throw std::runtime_error("Incomplete geometry");guard("COMPLETED");auto h=sha(result.data(),result.size());auto path=std::filesystem::path(q["output_dir"].get<std::string>())/(h+".replay");
 if(!std::filesystem::exists(path)){if(q["existing_bytes"].get<uint64_t>()+result.size()>536870912)throw std::runtime_error("Synchronous payloadcap");std::ofstream f(path,std::ios::binary);f.write((char*)result.data(),result.size());f.close();if(!f)throw std::runtime_error("write");}
 json out={{"event","REPLAY_RESULT"},{"pid",GetCurrentProcessId()},{"device_name",prop.deviceName},{"vendor",prop.vendorID},{"device",prop.deviceID},{"geometry",lens},{"native_op",op},{"memory",mem},{"calls",traces},{"full_output",{{"path","operator_payloads/"+h+".replay"},{"bytes",result.size()},{"sha256",h}}},{"cost_scope","GPU_ONLY_DIAGNOSTIC_NOT_PAID"},{"pipeline_status","UNKNOWN_NOT_EXPORTED"}};
 std::cout<<out.dump()<<std::endl;ggml_backend_free(backend);vkDestroyInstance(instance,nullptr);return 0;
}catch(std::exception&e){std::cout<<json({{"event","REPLAY_ERROR"},{"pid",GetCurrentProcessId()},{"reason",e.what()}}).dump()<<std::endl;return 22;}}
