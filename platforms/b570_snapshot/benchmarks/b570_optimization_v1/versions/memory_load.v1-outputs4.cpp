// New zero-forward feasibility probe. The inherited numerical DLLs are unchanged.
#include "llama.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include "native_memory_budget.h"
#include <windows.h>
#include <chrono>
#include <iostream>
#include <vector>
#include <string>
#include <iomanip>
using json=nlohmann::ordered_json;
std::string utc(){SYSTEMTIME s;GetSystemTime(&s);char b[64];sprintf_s(b,"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",s.wYear,s.wMonth,s.wDay,s.wHour,s.wMinute,s.wSecond,s.wMilliseconds);return b;}
int main(int argc,char **argv){
 if(argc!=4)return 1;
 try{
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.apiVersion=VK_API_VERSION_1_1;
  VkInstanceCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;ci.pApplicationInfo=&app;VkInstance instance;
  if(vkCreateInstance(&ci,nullptr,&instance)!=VK_SUCCESS)throw std::runtime_error("vkCreateInstance failed");
  uint32_t n=0;vkEnumeratePhysicalDevices(instance,&n,nullptr);std::vector<VkPhysicalDevice> ds(n);vkEnumeratePhysicalDevices(instance,&n,ds.data());VkPhysicalDevice dev=VK_NULL_HANDLE;VkPhysicalDeviceProperties props{};
  for(auto d:ds){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(d,&p);if(p.vendorID==0x8086&&std::string(p.deviceName).find("B570")!=std::string::npos){if(dev)throw std::runtime_error("Ambiguous B570 device");dev=d;props=p;}}
  if(!dev)throw std::runtime_error("Actual B570 device unavailable");
  auto memory=[&](std::string point){json heaps=json::array();uint64_t free=0;for(auto h:b570_opt::owned_process_memory(dev)){heaps.push_back({{"index",h.index},{"physical_size_bytes",h.physical_size_bytes},{"budget_bytes",h.budget_bytes},{"usage_bytes",h.usage_bytes},{"device_local",h.device_local}});if(h.device_local){if(h.usage_bytes>h.budget_bytes)throw std::runtime_error("Device budget overrun");free+=h.budget_bytes-h.usage_bytes;}}json r={{"event","MEMORY"},{"point",point},{"pid",GetCurrentProcessId()},{"timestamp_utc",utc()},{"device_name",props.deviceName},{"device_type",props.deviceType},{"vendor_id",props.vendorID},{"device_id",props.deviceID},{"scope","OWNED_MODEL_PROCESS"},{"heaps",heaps},{"device_local_headroom_bytes",free},{"headroom_gate",free>=536870912},{"model_forward_calls",0},{"decode_calls",0}};std::cout<<r.dump()<<"\n"<<std::flush;return free;};
  memory("BEFORE_LOAD");ggml_backend_load_all();llama_backend_init();
  auto *gpu=ggml_backend_dev_by_name("Vulkan0");if(!gpu||std::string(ggml_backend_dev_description(gpu)).find("B570")==std::string::npos)throw std::runtime_error("Vulkan0 is not B570");
  ggml_backend_dev_t devices[]={gpu,nullptr};std::vector<llama_model*> models;std::vector<llama_context*> contexts;
  for(int role=0;role<2;++role){
   if(std::string(argv[role+1])=="NONE")continue;
   auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;
   auto *model=llama_model_load_from_file(argv[role+1],mp);if(!model)throw std::runtime_error("Full GPU model loading failed");models.push_back(model);memory(role?"DRAFT_WEIGHTS":"TARGET_WEIGHTS");
   auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=512;cp.n_ubatch=role?1:std::stoi(argv[3]);cp.n_seq_max=1;cp.n_threads=10;cp.n_threads_batch=10;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.offload_kqv=true;cp.no_perf=false;cp.n_outputs_max=role?1:4;cp.n_outputs_max_per_seq=role?1:4;
   auto *ctx=llama_init_from_model(model,cp);if(!ctx)throw std::runtime_error("Full GPU context creation failed");contexts.push_back(ctx);
   std::cout<<json({{"event","CONTEXT"},{"role",role?"draft":"target"},{"layers",llama_model_n_layer(model)+1},{"n_ctx",llama_n_ctx(ctx)},{"n_ubatch",llama_n_ubatch(ctx)},{"hidden_warmup_disabled_by_direct_API",true},{"decode_calls",0}}).dump()<<"\n"<<std::flush;
   memory(role?"DRAFT_CONTEXT":"TARGET_CONTEXT");
  }
  auto free=memory("LOADED");for(auto c:contexts)llama_free(c);for(auto m:models)llama_model_free(m);memory("UNLOADED");vkDestroyInstance(instance,nullptr);
  std::cout<<json({{"event","FINAL"},{"status",free>=536870912?"LOADED_HEADROOM_PASS_ZERO_FORWARD":"BLOCKED_INSUFFICIENT_LOADED_HEADROOM"},{"model_forward_calls",0},{"decode_calls",0}}).dump()<<"\n"<<std::flush;
  return free>=536870912?0:20;
 }catch(const std::exception &e){std::cout<<json({{"event","ERROR"},{"reason",e.what()},{"pid",GetCurrentProcessId()},{"utc",utc()},{"decode_calls",0}}).dump()<<"\n"<<std::flush;return 21;}
}
