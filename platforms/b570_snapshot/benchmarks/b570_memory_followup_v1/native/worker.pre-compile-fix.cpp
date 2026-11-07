// Resident native IDs; no common-init, hidden warmup, text trimming or retries.
#include "llama.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include "native_memory_budget.h"
#include <windows.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mutex>
#include <thread>
#include <limits>
extern "C" __declspec(dllimport) void llama_b570_pilot_bind_phase_ubatch(llama_context *,uint32_t);
using json=nlohmann::ordered_json;
using clock_type=std::chrono::steady_clock;
std::string utc(){SYSTEMTIME s;GetSystemTime(&s);char b[64];sprintf_s(b,"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",s.wYear,s.wMonth,s.wDay,s.wHour,s.wMinute,s.wSecond,s.wMilliseconds);return b;}
void emit(const json &x){std::cout<<x.dump()<<"\n"<<std::flush;}
struct Memory {
 VkInstance instance{};VkPhysicalDevice device{};VkPhysicalDeviceProperties props{};
 int64_t threshold;std::string profile;std::atomic<bool> active{false},violation{false};
 std::thread timer;std::mutex lock;std::vector<json> samples;clock_type::time_point previous;double max_gap_ms=0;
 Memory(std::string p,int64_t t):threshold(t),profile(p){
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.apiVersion=VK_API_VERSION_1_1;
  VkInstanceCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;ci.pApplicationInfo=&app;
  if(vkCreateInstance(&ci,nullptr,&instance)!=VK_SUCCESS)throw std::runtime_error("Vulkan instance");
  uint32_t n=0;vkEnumeratePhysicalDevices(instance,&n,nullptr);std::vector<VkPhysicalDevice> ds(n);vkEnumeratePhysicalDevices(instance,&n,ds.data());
  for(auto d:ds){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(d,&p);if(p.vendorID==0x8086&&p.deviceID==0xE20C&&p.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU){if(device)throw std::runtime_error("Ambiguous B570");device=d;props=p;}}
  if(!device)throw std::runtime_error("B570 PCI unavailable");
 }
 json sample(std::string point){
  std::lock_guard<std::mutex> guard(lock);json heaps=json::array();int count=0;int64_t free=std::numeric_limits<int64_t>::max();
  for(auto h:b570_opt::owned_process_memory(device)){
   heaps.push_back({{"index",h.index},{"physical_size_bytes",h.physical_size_bytes},{"budget_bytes",h.budget_bytes},{"usage_bytes",h.usage_bytes},{"device_local",h.device_local}});
   if(h.device_local){if(h.index!=0||h.physical_size_bytes!=10563354624ULL)throw std::runtime_error("Dedicated heap mapping changed");++count;free=std::min(free,int64_t(h.budget_bytes)-int64_t(h.usage_bytes));}
  }
  if(count!=1)throw std::runtime_error("Dedicated heap ambiguous");
  auto now=clock_type::now();if(!samples.empty())max_gap_ms=std::max(max_gap_ms,std::chrono::duration<double,std::milli>(now-previous).count());previous=now;
  json r={{"event","MEMORY"},{"point",point},{"profile",profile},{"pid",GetCurrentProcessId()},{"timestamp_utc",utc()},{"device_name",props.deviceName},{"vendor_id",props.vendorID},{"device_id",props.deviceID},{"device_type",props.deviceType},{"scope","OWNED_MODEL_PROCESS"},{"heaps",heaps},{"device_local_headroom_bytes",free},{"threshold_bytes",threshold},{"headroom_gate",free>=threshold}};
  if(active){samples.push_back(r);if(free<threshold)violation=true;}return r;
 }
 void require(std::string point){auto r=sample(point);emit(r);if(r["device_local_headroom_bytes"].get<int64_t>()<threshold)throw std::runtime_error("MEMORY_BLOCKED:"+point);}
 void start(){samples.clear();violation=false;max_gap_ms=0;active=true;sample("ENGINEERING_BEGIN");timer=std::thread([&]{try{while(active){sample("ENGINEERING_PERIODIC");std::this_thread::sleep_for(std::chrono::milliseconds(5));}}catch(...){violation=true;}});}
 json stop(){if(active){sample("ENGINEERING_END");active=false;if(timer.joinable())timer.join();}return {{"samples",samples},{"max_observed_gap_ms",max_gap_ms},{"requested_period_ms",5},{"sampled_not_continuous_residency",true},{"violation",bool(violation)}};}
 ~Memory(){active=false;if(timer.joinable())timer.join();if(instance)vkDestroyInstance(instance,nullptr);}
};
struct Context {
 llama_model *model=nullptr;llama_context *ctx=nullptr;llama_sampler *sampler=nullptr;int ub,capacity;std::string role;Memory *memory;int decodes=0;bool capture=false;json trace=json::array();
 Context(std::string path,std::string role,int ub,int capacity,Memory *memory):role(role),ub(ub),capacity(capacity),memory(memory){
  auto *gpu=ggml_backend_dev_by_name("Vulkan0");if(!gpu||std::string(ggml_backend_dev_description(gpu)).find("B570")==std::string::npos)throw std::runtime_error("Vulkan0 mismatch");
  ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;
  model=llama_model_load_from_file(path.c_str(),mp);if(!model)throw std::runtime_error("Model allocation failure");memory->require(role+"_WEIGHTS");
  auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=512;cp.n_ubatch=ub;cp.n_seq_max=1;cp.n_outputs_max=capacity;cp.n_outputs_max_per_seq=capacity;cp.n_threads=10;cp.n_threads_batch=10;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.offload_kqv=true;
  ctx=llama_init_from_model(model,cp);if(!ctx)throw std::runtime_error("Context allocation failure");sampler=llama_sampler_init_greedy();
  emit({{"event","CONTEXT"},{"role",role},{"n_ctx",llama_n_ctx(ctx)},{"ub",llama_n_ubatch(ctx)},{"outputs_max",capacity},{"outputs_per_seq",capacity},{"layers",llama_model_n_layer(model)+1},{"numeric_path","Vulkan0_F16_KV_FAoff"},{"sampler","native_greedy_seed123_no_stochastic_state"},{"load_forward_calls",0}});memory->require(role+"_CONTEXT");
 }
 void reset(){llama_synchronize(ctx);llama_memory_clear(llama_get_memory(ctx),true);llama_sampler_reset(sampler);llama_b570_pilot_bind_phase_ubatch(ctx,ub);decodes=0;trace=json::array();if(llama_memory_seq_pos_min(llama_get_memory(ctx),0)!=-1||llama_memory_seq_pos_max(llama_get_memory(ctx),0)!=-1)throw std::runtime_error("KV reset");}
 void decode(const std::vector<int>&ids,int pos,bool all,std::string phase){
  if(ids.empty()||ids.size()>512)throw std::runtime_error("Decode size");auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
  for(int i=0;i<b.n_tokens;++i){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||i==b.n_tokens-1;}
  memory->sample("BEFORE_"+role+"_"+phase);int rc=llama_decode(ctx,b);++decodes;llama_batch_free(b);if(rc)throw std::runtime_error("Actual native decode failure:"+std::to_string(rc));llama_synchronize(ctx);memory->sample("AFTER_"+role+"_"+phase);
  if(memory->violation)throw std::runtime_error("MEMORY_BLOCKED:ENGINEERING_PEAK");
  if(capture)trace.push_back({{"role",role},{"phase",phase},{"pos",pos},{"input_ids",ids},{"ub",llama_n_ubatch(ctx)},{"all_outputs",all},{"kv_max",llama_memory_seq_pos_max(llama_get_memory(ctx),0)}});
 }
 void prefill(const std::vector<int>&ids){for(size_t i=0;i<ids.size();i+=512)decode(std::vector<int>(ids.begin()+i,ids.begin()+std::min(ids.size(),i+512)),int(i),false,"PREFILL");}
 int sample(int index){int id=llama_sampler_sample(sampler,ctx,index);if(id<0||id>=llama_vocab_n_tokens(llama_model_get_vocab(model)))throw std::runtime_error("Sampler invalid ID");return id;}
 void trim(int pos){if(!llama_memory_seq_rm(llama_get_memory(ctx),0,pos,-1))throw std::runtime_error("KV rollback failure");if(llama_memory_seq_pos_max(llama_get_memory(ctx),0)!=pos-1)throw std::runtime_error("KV rollback positions");}
 ~Context(){if(sampler)llama_sampler_free(sampler);if(ctx)llama_free(ctx);if(model)llama_model_free(model);}
};
void vocab_guard(Context &t,Context &d){auto *a=llama_model_get_vocab(t.model),*b=llama_model_get_vocab(d.model);
 if(llama_vocab_n_tokens(a)!=llama_vocab_n_tokens(b)||llama_vocab_type(a)!=llama_vocab_type(b)||llama_vocab_bos(a)!=llama_vocab_bos(b)||llama_vocab_eos(a)!=llama_vocab_eos(b)||llama_vocab_get_add_bos(a)!=llama_vocab_get_add_bos(b)||llama_vocab_get_add_eos(a)!=llama_vocab_get_add_eos(b))throw std::runtime_error("Compatibility vocab metadata");
 for(int i=0;i<llama_vocab_n_tokens(a);++i)if(strcmp(llama_vocab_get_text(a,i),llama_vocab_get_text(b,i))||llama_vocab_get_attr(a,i)!=llama_vocab_get_attr(b,i)||llama_vocab_get_score(a,i)!=llama_vocab_get_score(b,i)||llama_vocab_is_eog(a,i)!=llama_vocab_is_eog(b,i))throw std::runtime_error("Compatibility full vocab row");
 emit({{"event","VOCAB_GUARD"},{"full_rows",llama_vocab_n_tokens(a)},{"status","PASS"},{"runtime_eog_equal",true},{"load_forward_calls",0}});
}
int main(int argc,char **argv){
 try{
  if(argc!=9)throw std::runtime_error("Arguments: profile target draft|NONE ub mode k trace_dir probe|resident");
  std::string profile=argv[1],target=argv[2],draft=argv[3],mode=argv[5],dir=argv[7],action=argv[8];int ub=std::stoi(argv[4]),k=std::stoi(argv[6]);
  int64_t threshold;if(profile=="STANDARD_Q6")threshold=536870912;else if(profile=="TIGHT_Q8")threshold=134217728;else throw std::runtime_error("Unknown profile");
  std::string tf=std::filesystem::path(target).filename().string(),df=std::filesystem::path(draft).filename().string();
  if(tf!=(profile=="STANDARD_Q6"?"Meta-Llama-3.1-8B-Instruct-Q6_K.gguf":"Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"))throw std::runtime_error("Profile target quantization mismatch");
  if(draft!="NONE"&&df!="Llama-3.2-1B-Instruct-Q4_K_M.gguf"&&(profile!="STANDARD_Q6"||df!="Llama-3.2-1B-Instruct-Q8_0.gguf"))throw std::runtime_error("Profile draft quantization mismatch");
  if(ub!=32&&ub!=128&&ub!=512)throw std::runtime_error("Unknown ordinary UB");
  if(mode!="ordinary"&&mode!="native_greedy"&&mode!="vulkan_batched_repair"&&mode!="N_unrepaired")throw std::runtime_error("Unknown mode");
  if(k<1||k>3||action!="probe"&&action!="resident")throw std::runtime_error("Unknown k/action");
  if(profile=="TIGHT_Q8"&&mode!="ordinary"&&ub!=32)throw std::runtime_error("Tight candidate prefill must be32");
  if(mode=="ordinary"&&draft!="NONE")throw std::runtime_error("Ordinary draft forbidden");
  std::filesystem::create_directories(dir);Memory memory(profile,threshold);memory.require("BEFORE_LOAD");ggml_backend_load_all();llama_backend_init();
  Context tgt(target,"TARGET",ub,mode=="ordinary"?1:k+1,&memory);std::unique_ptr<Context>dft;if(draft!="NONE"){dft=std::make_unique<Context>(draft,"DRAFT",1,1,&memory);vocab_guard(tgt,*dft);}
  memory.require("LOADED");emit({{"event","READY"},{"profile",profile},{"mode",mode},{"pid",GetCurrentProcessId()},{"forward_calls",0},{"residency_status","RESIDENCY_UNKNOWN"},{"paging_observation","UNAVAILABLE_UNINSTRUMENTED_WDDM"}});
  if(action=="probe"){emit({{"event","PROBE_COMPLETE"},{"forward_calls",0}});return 0;}
  std::string line;while(std::getline(std::cin,line)){
   auto req=json::parse(line);std::string rid=req.at("request_id");memory.require("PRE_REQUEST");
   auto start=clock_type::now();auto inp=req.at("prompt_ids").get<std::vector<int>>();int cap=req.at("cap");bool capture=req.at("capture");
   if(inp.empty()||inp.size()>768||cap<1||cap>128||inp.size()+cap+k+1>1024)throw std::runtime_error("Request bounds");
   auto *v=llama_model_get_vocab(tgt.model);for(int id:inp)if(id<0||id>=llama_vocab_n_tokens(v))throw std::runtime_error("Prompt ID invalid");
   tgt.capture=capture;tgt.reset();if(dft){dft->capture=capture;dft->reset();}memory.start();tgt.prefill(inp);if(dft)dft->prefill(inp);
   if(mode=="vulkan_batched_repair"){auto pos=llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0);llama_b570_pilot_bind_phase_ubatch(tgt.ctx,1);if(llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0)!=pos)throw std::runtime_error("Phase KV position changed");}
   std::vector<int> out;std::vector<bool> flags;json verifies=json::array();int proposed=0,accepted=0,rollbacks=0;int next=tgt.sample(-1);int base=int(inp.size());
   auto commit=[&](int id){if(out.size()>=size_t(cap)||(!flags.empty()&&flags.back()))throw std::runtime_error("Native suffix prevented");out.push_back(id);flags.push_back(llama_vocab_is_eog(v,id));return flags.back()||out.size()==size_t(cap);};
   bool done=commit(next);
   while(!done){
    if(!dft){tgt.decode({next},base,false,"ORDINARY");++base;next=tgt.sample(-1);done=commit(next);continue;}
    dft->trim(base);dft->decode({next},base,false,"DRAFT_SYNC");std::vector<int> proposal;
    int count=std::min(k,cap-int(out.size()));for(int i=0;i<count;++i){int p=dft->sample(-1);proposal.push_back(p);++proposed;dft->decode({p},base+1+i,false,"PROPOSE");if(llama_vocab_is_eog(llama_model_get_vocab(dft->model),p))break;}
    std::vector<int> batch={next};batch.insert(batch.end(),proposal.begin(),proposal.end());tgt.decode(batch,base,true,"VERIFY");
    int n=0;std::vector<int> decisions;for(size_t j=0;j<=proposal.size()&&!done;++j){int decision=tgt.sample(int(j));decisions.push_back(decision);done=commit(decision);if(j<proposal.size()&&decision==proposal[j]){++accepted;++n;if(done)break;}else{next=decision;break;}}
    int keep=base+1+n;tgt.trim(keep);dft->trim(keep);base=keep;++rollbacks;
    if(capture)verifies.push_back({{"batch_ids",batch},{"decisions",decisions},{"accepted",n},{"keep_pos",keep},{"repair_scope",mode=="vulkan_batched_repair"?"all_target_continuation_rows_physical_UB1":"none"},{"target_ub",llama_n_ubatch(tgt.ctx)}});
   }
   llama_synchronize(tgt.ctx);if(dft)llama_synchronize(dft->ctx);auto mem=memory.stop();
   auto end=clock_type::now();std::string stop=flags.back()?"EOG":"CAP";
   json result={{"event","RESULT"},{"request_id",rid},{"pid",GetCurrentProcessId()},{"profile",profile},{"mode",mode},{"ids",out},{"eog",flags},{"length",out.size()},{"terminal_id",out.back()},{"stop_reason",stop},{"cap",cap},{"prompt_ids",inp},{"reset_target_min",-1},{"reset_target_max",-1},{"reset_draft_checked",bool(dft)},{"target_decode_calls",tgt.decodes},{"draft_decode_calls",dft?dft->decodes:0},{"proposed",proposed},{"accepted",accepted},{"rollback_operations",rollbacks},{"target_continuation_ub",llama_n_ubatch(tgt.ctx)},{"native_request_ms",std::chrono::duration<double,std::milli>(end-start).count()},{"residency_status","RESIDENCY_UNKNOWN"},{"memory_violation",bool(memory.violation)}};
   emit(result); // Complete IDs travel before any disk persistence; controller hashes afterward.
   if(capture){std::ofstream f(dir+"/"+rid+".trace.json");f<<json({{"target",tgt.trace},{"draft",dft?dft->trace:json::array()},{"verify",verifies},{"memory",mem}}).dump()<<"\n";if(!f)throw std::runtime_error("Trace persistence");}
   else {std::ofstream f(dir+"/"+rid+".memory.json");f<<mem.dump()<<"\n";if(!f)throw std::runtime_error("Memory persistence");}
   if(memory.violation)throw std::runtime_error("MEMORY_BLOCKED:ENGINEERING_PEAK");emit({{"event","PERSISTED"},{"request_id",rid}});
  }
 }catch(const std::exception&e){emit({{"event","ERROR"},{"reason",e.what()},{"pid",GetCurrentProcessId()},{"utc",utc()}});return 21;}
 return 0;
}
