// Resident native IDs; no common-init, hidden warmup, text trimming or retries.
#include "llama.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include "native_memory_budget.h"
#define NOMINMAX
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
#include <sstream>
#include <set>
#include <cstring>
#include <iomanip>
#include <cmath>
#include <bcrypt.h>
extern "C" __declspec(dllimport) void llama_b570_pilot_bind_phase_ubatch(llama_context *,uint32_t);
extern "C" __declspec(dllimport) const char * llama_b570_memory_weight_map(const llama_model *);
extern "C" __declspec(dllimport) void llama_b570_work_enable(llama_context *,bool);
extern "C" __declspec(dllimport) uint64_t llama_b570_work_graphs(const llama_context *);
extern "C" __declspec(dllimport) uint64_t llama_b570_work_rows(const llama_context *);
extern "C" __declspec(dllimport) uint64_t llama_b570_work_width(const llama_context *,uint32_t);
using json=nlohmann::ordered_json;
std::string observation_mode;
std::string counter_hash;
bool counted(){return observation_mode!="baseline";}
bool heavy(){return observation_mode=="heavy";}
bool timed(){return observation_mode=="lite"||heavy();}
json hist_empty(){return json::object();}
void hist_add(json & h,int key,int value=1){std::string k=std::to_string(key);h[k]=h.value(k,0)+value;}
struct Work {
 json w,f,spans;std::chrono::steady_clock::time_point request_start;
 Work(int prompt):request_start(std::chrono::steady_clock::now()) {
  w=json::object();
  for(auto n:{"prompt_ids_count","output_ids_count","proposal_generated","proposal_verified","accepted_committed","first_mismatch_rejected","unexamined_after_mismatch","terminal_discarded","unverified_before_verify","initial_target_committed","bonus_committed","correction_committed","fallback_committed","verify_cycles","verification_seed_rows","draft_continuation_calls","draft_continuation_rows","draft_proposal_calls","draft_proposal_rows","draft_catchup_calls","draft_catchup_rows","rollback_calls","target_prefill_calls","draft_prefill_calls","target_verification_rows","target_ordinary_rows","target_micrographs","target_micrograph_rows","draft_micrographs","draft_micrograph_rows","sampling_calls","phase_binding_calls","kv_trim_calls","inherited_explicit_sync_calls"})w[n]=0;
  w["prompt_ids_count"]=prompt;w["counter_semantics_sha256"]=counter_hash;
  for(auto n:{"accepted_prefix_hist","cycle_progress_hist","verification_caller_width_hist","target_physical_width_hist","target_prefill_physical_width_hist","target_continuation_physical_width_hist","draft_physical_width_hist","attempted_positions","accepted_positions"})w[n]=hist_empty();
  f=json::object();for(auto n:{"target_prefill_ids","draft_prefill_ids","draft_continuation_rows","reconcile_output_ids","rollback_calls","request_channel","target_continuation_calls_w1","target_continuation_calls_w2"})f[n]=0;f["request_channel"]=1;
  spans=json::array();
 }
 void inc(const std::string & n,int value=1){if(counted())w[n]=w[n].get<int64_t>()+value;}
 void span(const std::string & label,std::chrono::steady_clock::time_point begin,const std::string & scope) {
  if(timed())spans.push_back({{"phase",label},{"begin_ms",std::chrono::duration<double,std::milli>(begin-request_start).count()},{"end_ms",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-request_start).count()},{"completion_scope",scope},{"gpu_event_ms",nullptr}});
 }
};
Work * work=nullptr;
std::vector<int> schedule100; bool op100=false; int layer100=0; json tensors100=json::array(); uint64_t opbytes100=0; std::string opdir100;
int partition98=512;std::string payload_dir98;json payloads98=json::object();
bool diagnostic96=false,sham96=false;int boundary96=0,sham_count96=0;
std::vector<int> prefix96;std::set<int>cuts96;json boundaries96=json::array();
std::string sha96(const void*data,size_t size){
 BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;ULONG got=0,len=0;
 if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)!=0)throw std::runtime_error("SHA provider");
 if(BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,(PUCHAR)&len,sizeof(len),&got,0)!=0)throw std::runtime_error("SHA object");
 std::vector<UCHAR>obj(len),out(32);
 if(BCryptCreateHash(a,&h,obj.data(),len,nullptr,0,0)!=0||BCryptHashData(h,(PUCHAR)data,ULONG(size),0)!=0||BCryptFinishHash(h,out.data(),32,0)!=0)throw std::runtime_error("SHA compute");
 BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);std::ostringstream os;
 for(auto b:out)os<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);return os.str();
}

using clock_type=std::chrono::steady_clock;
std::string utc(){SYSTEMTIME s;GetSystemTime(&s);char b[64];sprintf_s(b,"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",s.wYear,s.wMonth,s.wDay,s.wHour,s.wMinute,s.wSecond,s.wMilliseconds);return b;}
void emit(const json &x){std::cout<<x.dump()<<"\n"<<std::flush;}
struct Memory {
 VkInstance instance{};VkPhysicalDevice device{};VkPhysicalDeviceProperties props{};
 std::string luid;bool luid_valid=false;
 int64_t threshold;std::string profile;std::atomic<bool> active{false},violation{false};
 std::thread timer;std::mutex lock;std::vector<json> samples;clock_type::time_point previous;double max_gap_ms=0;std::string failure_file;
 Memory(std::string p,int64_t t):threshold(t),profile(p){
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.apiVersion=VK_API_VERSION_1_1;
  VkInstanceCreateInfo ci{};ci.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;ci.pApplicationInfo=&app;
  if(vkCreateInstance(&ci,nullptr,&instance)!=VK_SUCCESS)throw std::runtime_error("Vulkan instance");
  uint32_t n=0;vkEnumeratePhysicalDevices(instance,&n,nullptr);std::vector<VkPhysicalDevice> ds(n);vkEnumeratePhysicalDevices(instance,&n,ds.data());
  for(auto d:ds){VkPhysicalDeviceProperties p;vkGetPhysicalDeviceProperties(d,&p);if(p.vendorID==0x8086&&p.deviceID==0xE20C&&p.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU){if(device)throw std::runtime_error("Ambiguous B570");device=d;props=p;}}
  if(!device)throw std::runtime_error("B570 PCI unavailable");
  VkPhysicalDeviceIDProperties ids{};ids.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES;
  VkPhysicalDeviceProperties2 p2{};p2.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;p2.pNext=&ids;vkGetPhysicalDeviceProperties2(device,&p2);luid_valid=ids.deviceLUIDValid;
  uint32_t low=0,high=0;memcpy(&low,ids.deviceLUID,4);memcpy(&high,ids.deviceLUID+4,4);std::ostringstream ls;ls<<std::hex<<std::setw(8)<<std::setfill('0')<<high<<"-"<<std::setw(8)<<low;luid=ls.str();
 }
 json sample(std::string point){
  std::lock_guard<std::mutex> guard(lock);json heaps=json::array();int count=0;int64_t free=std::numeric_limits<int64_t>::max();
  for(auto h:b570_opt::owned_process_memory(device)){
   heaps.push_back({{"index",h.index},{"physical_size_bytes",h.physical_size_bytes},{"budget_bytes",h.budget_bytes},{"usage_bytes",h.usage_bytes},{"device_local",h.device_local}});
   if(h.device_local){if(h.index!=0||h.physical_size_bytes!=10563354624ULL)throw std::runtime_error("Dedicated heap mapping changed");++count;free=std::min(free,int64_t(h.budget_bytes)-int64_t(h.usage_bytes));}
  }
  if(count!=1)throw std::runtime_error("Dedicated heap ambiguous");
  auto now=clock_type::now();if(!samples.empty())max_gap_ms=std::max(max_gap_ms,std::chrono::duration<double,std::milli>(now-previous).count());previous=now;
  json r={{"event","MEMORY"},{"point",point},{"profile",profile},{"pid",GetCurrentProcessId()},{"timestamp_utc",utc()},{"device_name",props.deviceName},{"adapter_luid",luid},{"adapter_luid_valid",luid_valid},{"vendor_id",props.vendorID},{"device_id",props.deviceID},{"device_type",props.deviceType},{"scope","OWNED_MODEL_PROCESS"},{"heaps",heaps},{"device_local_headroom_bytes",free},{"threshold_bytes",threshold},{"headroom_gate",free>=threshold}};
  if(active){samples.push_back(r);if(free<threshold)violation=true;}return r;
 }
 void require(std::string point){auto r=sample(point);emit(r);if(r["device_local_headroom_bytes"].get<int64_t>()<threshold)throw std::runtime_error("MEMORY_BLOCKED:"+point);}
 void start(){samples.clear();violation=false;max_gap_ms=0;active=true;sample("REQUEST_BEGIN");if(heavy())timer=std::thread([&]{try{while(active){sample("HEAVY_PERIODIC");std::this_thread::sleep_for(std::chrono::milliseconds(5));}}catch(...){violation=true;}});}
 json stop(){if(active){sample("ENGINEERING_END");active=false;if(timer.joinable())timer.join();}return {{"samples",samples},{"max_observed_gap_ms",max_gap_ms},{"requested_period_ms",heavy()?json(5):json(nullptr)},{"sampled_not_continuous_residency",true},{"violation",bool(violation)}};}
 ~Memory(){bool failed=active;auto last=stop();if(failed&&!failure_file.empty()){std::ofstream f(failure_file);f<<last.dump()<<"\n";}if(instance)vkDestroyInstance(instance,nullptr);}
};
struct Context {
 llama_model *model=nullptr;llama_context *ctx=nullptr;llama_sampler *sampler=nullptr;int ub,capacity;std::string role;Memory *memory;int decodes=0,reset_min=0,reset_max=0;bool capture=false,compute_violation=false,continuation_seen=false;json trace=json::array();int opcaller100=-1,opoffset100=0,opstart100=0,opwidth100=0;std::vector<int>last_input96;int last_pos96=-1;std::string last_phase96;std::set<int> observed_ops;

 static json capture100(ggml_tensor*t,const std::string&kind){
  auto*base=t;while(base->view_src)base=base->view_src;
  auto bt=base->buffer?ggml_backend_buffer_get_type(base->buffer):nullptr;auto dev=bt?ggml_backend_buft_get_device(bt):nullptr;
  json ne=json::array(),nb=json::array();for(int i=0;i<4;++i){ne.push_back(t->ne[i]);nb.push_back(t->nb[i]);}
  json j={{"kind",kind},{"name",t->name},{"op",ggml_op_name(t->op)},{"dtype",ggml_type_name(t->type)},{"type",int(t->type)},{"ne",ne},{"nb",nb},{"buffer_identity",uint64_t(reinterpret_cast<uintptr_t>(base->buffer))},{"tensor_identity",uint64_t(reinterpret_cast<uintptr_t>(t))},{"buffer_type",bt?ggml_backend_buft_name(bt):"UNKNOWN"},{"device",dev?ggml_backend_dev_name(dev):"UNKNOWN"},{"view_offset",t->view_offs},{"op_params_sha256",sha96(t->op_params,sizeof(t->op_params))}};
  j["op_params"]=json::array();for(auto p:t->op_params)j["op_params"].push_back(p);
  bool weight=std::string(t->name).find(".weight")!=std::string::npos;
  bool permitted=!weight||std::string(t->name)=="blk.0.attn_q.weight"||std::string(t->name)=="blk.0.attn_k.weight"||std::string(t->name)=="blk.0.attn_v.weight"||ggml_nbytes(t)<=65536;
  if(!permitted||ggml_nbytes(t)>33554432){j["payload"]=nullptr;j["scope"]="SOURCE_GGUF_PIN_NOT_RAW_CAPTURE";return j;}
  size_t n=ggml_nbytes(t);std::vector<uint8_t>b(n);ggml_backend_tensor_get(t,b.data(),0,n);auto h=sha96(b.data(),n);auto p=std::filesystem::path(opdir100)/(h+".tensor");
  if(!std::filesystem::exists(p)){if(opbytes100+n>536870912)throw std::runtime_error("SYNCHRONOUS_P1C_PAYLOAD_CAP");opbytes100+=n;std::ofstream f(p,std::ios::binary);f.write((char*)b.data(),n);f.close();if(!f)throw std::runtime_error("P1C_PAYLOAD_WRITE");}
  j["payload"]={{"path","operator_payloads/"+h+".tensor"},{"bytes",n},{"sha256",h}};return j;
 }
 static bool observe100(ggml_tensor*t,bool ask,void*data){
  auto*self=static_cast<Context*>(data);std::string name=t->name,suffix="-"+std::to_string(layer100);
  bool embedding=t->op==GGML_OP_GET_ROWS&&t->src[0]&&std::string(t->src[0]->name)=="token_embd.weight";
  bool selected=op100&&self->last_phase96=="PREFILL"&&(embedding||name=="inp_embd"||(name.size()>=suffix.size()&&name.compare(name.size()-suffix.size(),suffix.size(),suffix)==0));
  if(ask)return selected;
  if(!selected)return true;
  if(embedding){if(self->opcaller100!=self->decodes){self->opcaller100=self->decodes;self->opoffset100=0;}self->opstart100=self->last_pos96+self->opoffset100;self->opwidth100=int(t->ne[1]);self->opoffset100+=self->opwidth100;}
  json operands=json::array();for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])operands.push_back(capture100(t->src[i],"src"+std::to_string(i)));
  auto r=capture100(t,"output");r["operands"]=operands;r["micrograph_pos"]=self->opstart100;r["micrograph_width"]=self->opwidth100;r["caller_decode_ordinal"]=self->decodes;r["caller_pos"]=self->last_pos96;r["caller_ids"]=self->last_input96;r["native_context_ub"]=llama_n_ubatch(self->ctx);r["logical_mapping_rule"]="ne1=n_tokens for2D,ne2=n_tokens for Q/K/3D; verify against source and per-micrograph input IDs; raw offset not position";r["actual_shader_pipeline"]=nullptr;r["dispatch_dimensions"]=nullptr;
  tensors100.push_back(r);if(tensors100.dump().size()>4194304)throw std::runtime_error("SYNCHRONOUS_METADATA_CAP");return true;
 }
 void clean_receiver100(){
  llama_synchronize(ctx);llama_free(ctx);llama_sampler_free(sampler);
  auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=512;p.n_ubatch=ub;p.n_seq_max=1;p.n_outputs_max=capacity;p.n_outputs_max_per_seq=capacity;p.n_threads=10;p.n_threads_batch=10;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;p.offload_kqv=true;p.cb_eval=observe100;p.cb_eval_user_data=this;
  ctx=llama_init_from_model(model,p);sampler=llama_sampler_init_greedy();if(!ctx||!sampler)throw std::runtime_error("Fresh receiver allocation");reset();
 }

 static bool observe_compute(ggml_tensor *tensor,bool ask,void *data){auto *self=static_cast<Context*>(data);int op=int(tensor->op);bool needed=tensor->op==GGML_OP_GET_ROWS||tensor->op==GGML_OP_MUL_MAT||tensor->op==GGML_OP_MUL_MAT_ID||tensor->op==GGML_OP_RMS_NORM||tensor->op==GGML_OP_SOFT_MAX;
  if(ask)return needed&&self->observed_ops.count(op)==0;
  self->observed_ops.insert(op);auto *base=tensor;while(base->view_src)base=base->view_src;auto type=base->buffer?ggml_backend_buffer_get_type(base->buffer):nullptr;auto dev=type?ggml_backend_buft_get_device(type):nullptr;bool gpu=dev&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU&&std::string(ggml_backend_dev_name(dev))=="Vulkan0";
  json witness={{"event","COMPUTE_BUFFER_OBSERVATION"},{"role",self->role},{"pid",GetCurrentProcessId()},{"op",ggml_op_name(tensor->op)},{"tensor_name",tensor->name},{"buffer_type",type?ggml_backend_buft_name(type):"UNKNOWN"},{"backend_device",dev?ggml_backend_dev_name(dev):"UNKNOWN"},{"GPU_buffer",gpu},{"scope","first_occurrence_per_op_at_prefill_and_continuation_not_physical_residency"}};emit(witness);if(!gpu)self->compute_violation=true;return true;
 }
 Context(std::string path,std::string role,int ub,int capacity,Memory *memory):role(role),ub(ub),capacity(capacity),memory(memory){
  auto *gpu=ggml_backend_dev_by_name("Vulkan0");if(!gpu||std::string(ggml_backend_dev_description(gpu)).find("B570")==std::string::npos)throw std::runtime_error("Vulkan0 mismatch");
  ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;
  // n_gpu_layers alone leaves token embeddings on CPU in the inherited loader.
  llama_model_tensor_buft_override overrides[]={{".*",ggml_backend_dev_buffer_type(gpu)},{nullptr,nullptr}};mp.tensor_buft_overrides=overrides;
  model=llama_model_load_from_file(path.c_str(),mp);if(!model)throw std::runtime_error("Model allocation failure");
  std::istringstream map(llama_b570_memory_weight_map(model));std::string row;json weights=json::array();bool all_gpu=true;
  while(std::getline(map,row)){std::istringstream fields(row);std::string name,buffer,device,gpu_flag,bytes;std::getline(fields,name,'\t');std::getline(fields,buffer,'\t');std::getline(fields,device,'\t');std::getline(fields,gpu_flag,'\t');std::getline(fields,bytes,'\t');bool match=device=="Vulkan0"&&gpu_flag=="1";all_gpu=all_gpu&&match;weights.push_back({{"name",name},{"buffer_type",buffer},{"backend_device",device},{"gpu_backend_buffer",gpu_flag=="1"},{"tensor_bytes",std::stoull(bytes)}});}
  emit({{"event","WEIGHT_MAP"},{"role",role},{"pid",GetCurrentProcessId()},{"tensors",weights},{"all_weights_Vulkan0",all_gpu},{"physical_residency","UNKNOWN_NOT_PROVEN_BY_BUFFER_DEVICE"}});
  if(weights.empty()||!all_gpu)throw std::runtime_error("RESIDENCY_VIOLATION_CPU_MODEL_WEIGHT");memory->require(role+"_WEIGHTS");
  auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=512;cp.n_ubatch=ub;cp.n_seq_max=1;cp.n_outputs_max=capacity;cp.n_outputs_max_per_seq=capacity;cp.n_threads=10;cp.n_threads_batch=10;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.offload_kqv=true;cp.cb_eval=observe100;cp.cb_eval_user_data=this;
  ctx=llama_init_from_model(model,cp);if(!ctx)throw std::runtime_error("Context allocation failure");sampler=llama_sampler_init_greedy();
  emit({{"event","CONTEXT"},{"role",role},{"n_ctx",llama_n_ctx(ctx)},{"ub",llama_n_ubatch(ctx)},{"outputs_max",capacity},{"outputs_per_seq",capacity},{"layers",llama_model_n_layer(model)+1},{"numeric_path","Vulkan0_F16_KV_FAoff"},{"sampler","native_greedy_seed123_no_stochastic_state"},{"load_forward_calls",0}});memory->require(role+"_CONTEXT");
 }
 void reset(){llama_synchronize(ctx);llama_memory_clear(llama_get_memory(ctx),true);llama_sampler_reset(sampler);llama_b570_pilot_bind_phase_ubatch(ctx,ub);decodes=0;llama_b570_work_enable(ctx,counted());if(work)work->inc("inherited_explicit_sync_calls");compute_violation=false;continuation_seen=false;observed_ops.clear();trace=json::array();reset_min=llama_memory_seq_pos_min(llama_get_memory(ctx),0);reset_max=llama_memory_seq_pos_max(llama_get_memory(ctx),0);if(reset_min!=-1||reset_max!=-1)throw std::runtime_error("KV reset");}
 void decode(const std::vector<int>&ids,int pos,bool all,std::string phase,bool last_output=true){
  if(ids.empty()||ids.size()>512)throw std::runtime_error("Decode size");last_input96=ids;last_pos96=pos;last_phase96=phase;auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
  for(int i=0;i<b.n_tokens;++i){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||(last_output&&i==b.n_tokens-1);}
  if(phase!="PREFILL"&&!continuation_seen){observed_ops.clear();continuation_seen=true;}
  auto phase_begin=timed()?clock_type::now():clock_type::time_point{};
  uint64_t g0=llama_b570_work_graphs(ctx),r0=llama_b570_work_rows(ctx);std::vector<uint64_t> widths(513);if(counted())for(int w=1;w<=512;++w)widths[w]=llama_b570_work_width(ctx,w);
  if(heavy())memory->sample("BEFORE_"+role+"_"+phase);
  int rc=llama_decode(ctx,b);++decodes;llama_batch_free(b);if(rc)throw std::runtime_error("Actual native decode failure:"+std::to_string(rc));
  if(heavy()){llama_synchronize(ctx);memory->sample("AFTER_"+role+"_"+phase);}
  if(compute_violation)throw std::runtime_error("RESIDENCY_VIOLATION_CPU_MODEL_COMPUTE");
  if(work&&counted()){
   std::string lower=role=="TARGET"?"target":"draft";work->inc(lower+"_micrographs",int(llama_b570_work_graphs(ctx)-g0));work->inc(lower+"_micrograph_rows",int(llama_b570_work_rows(ctx)-r0));
   if(phase=="PREFILL"){work->inc(lower+"_prefill_calls");work->f[lower+"_prefill_ids"]=work->f[lower+"_prefill_ids"].get<int>()+int(ids.size());}
   else if(role=="DRAFT"){work->inc("draft_continuation_calls");work->inc("draft_continuation_rows",int(ids.size()));std::string kind=phase=="PROPOSE"?"draft_proposal":"draft_catchup";work->inc(kind+"_calls");work->inc(kind+"_rows",int(ids.size()));work->f["draft_continuation_rows"]=work->f["draft_continuation_rows"].get<int>()+int(ids.size());}
   else {work->f["target_continuation_calls_w"+std::to_string(ids.size())]=work->f["target_continuation_calls_w"+std::to_string(ids.size())].get<int>()+1;work->inc(phase=="VERIFY"?"target_verification_rows":"target_ordinary_rows",int(ids.size()));}
   for(int w=1;w<=512;++w){auto delta=llama_b570_work_width(ctx,w)-widths[w];if(delta){hist_add(work->w[lower+"_physical_width_hist"],w,int(delta));if(role=="TARGET")hist_add(work->w[phase=="PREFILL"?"target_prefill_physical_width_hist":"target_continuation_physical_width_hist"],w,int(delta));}}
  }
  if(work&&timed())work->span(role+"_"+phase,phase_begin,heavy()?"COMPLETED_WITH_HEAVY_SYNC_NOT_FOR_CALIBRATION":"ASYNC_DECODE_ENQUEUE_ONLY_NOT_COMPLETED_COMPONENT_WALL");

  if(memory->violation)throw std::runtime_error("MEMORY_BLOCKED:ENGINEERING_PEAK");
  if(capture){
 json wh=json::object();for(int w=1;w<=512;++w){auto d=llama_b570_work_width(ctx,w)-widths[w];if(d)wh[std::to_string(w)]=d;}
 trace.push_back({{"role",role},{"phase",phase},{"pos",pos},{"input_ids",ids},{"ub",llama_n_ubatch(ctx)},{"all_outputs",all},{"last_output_requested",last_output},{"logits_requested_positions",last_output?json::array({pos+int(ids.size())-1}):json::array()},{"kv_min",llama_memory_seq_pos_min(llama_get_memory(ctx),0)},{"kv_max",llama_memory_seq_pos_max(llama_get_memory(ctx),0)},{"successful_micrographs",llama_b570_work_graphs(ctx)-g0},{"occupied_rows",llama_b570_work_rows(ctx)-r0},{"physical_width_hist",wh},{"GPU_completed_stage_wall",nullptr}});
}
 }
 void prefill(const std::vector<int>&ids){
 size_t pos=0;for(int n:schedule100){if(n<=0||n>512||pos+n>ids.size())throw std::runtime_error("Frozen schedule invalid");size_t end=pos+n;decode(std::vector<int>(ids.begin()+pos,ids.begin()+end),int(pos),false,"PREFILL",end==ids.size());pos=end;}
 if(pos!=ids.size())throw std::runtime_error("Incomplete prompt schedule");
}
 void boundary_snapshot96(int index,int sampled){
 if(!diagnostic96||!capture||role!="TARGET"||cuts96.count(boundary96)==0)return;
 const float *l=llama_get_logits_ith(ctx,index);if(!l)throw std::runtime_error("Boundary logits");
 int count=llama_vocab_n_tokens(llama_model_get_vocab(model)),a=-1,b=-1;
 for(int i=0;i<count;++i){if(a<0||l[i]>l[a]){b=a;a=i;}else if(b<0||l[i]>l[b])b=i;}
 if(a!=sampled||b<0||!std::isfinite(l[a])||!std::isfinite(l[b]))throw std::runtime_error("Boundary top1 identity");
 std::string lh=sha96(l,sizeof(float)*count);float l1=l[a],l2=l[b];
 auto put=[&](const void*data,size_t bytes,const std::string&h,const std::string&suffix){
 auto p=std::filesystem::path(payload_dir98)/(h+suffix);
 if(!std::filesystem::exists(p)){std::ofstream f(p,std::ios::binary);f.write((const char*)data,bytes);f.close();if(!f)throw std::runtime_error("Raw state persistence");}
 if(std::filesystem::file_size(p)!=bytes)throw std::runtime_error("Raw state size");
 return json{{"path","payloads/"+h+suffix},{"sha256",h},{"bytes",bytes}};
 };
 auto lv=put(l,sizeof(float)*count,lh,".logits.f32");

 auto full=[&](){std::vector<uint8_t>v(llama_state_get_size(ctx));v.resize(llama_state_get_data(ctx,v.data(),v.size()));if(v.empty())throw std::runtime_error("Full state empty");return v;};
 auto kv=[&](){std::vector<uint8_t>v(llama_state_seq_get_size(ctx,0));v.resize(llama_state_seq_get_data(ctx,v.data(),v.size(),0));if(v.empty())throw std::runtime_error("KV state empty");return v;};
 auto f=full(),k=kv();auto fh=sha96(f.data(),f.size()),kh=sha96(k.data(),k.size());json sham=nullptr;
 json kvp=nullptr;if(boundary96==0)kvp=put(k.data(),k.size(),kh,".seqkv.bin");
 payloads98[std::to_string(boundary96)]={{"logits",lv},{"sequence_KV",kvp}};

 if(sham96){auto u=llama_n_ubatch(ctx);llama_b570_pilot_bind_phase_ubatch(ctx,u);++sham_count96;auto ff=full(),kk=kv();if(f!=ff||k!=kk)throw std::runtime_error("Own binding sham state changed");
 sham={{"status","PASS_SAME_CONTEXT_BINDING_NOOP_NOT_RESTORE"},{"ub_before",u},{"ub_after",llama_n_ubatch(ctx)},{"full_context_bytes_equal",f==ff},{"sequence_KV_bytes_equal",k==kk},{"future_tokens_forced",false},{"state_clone_or_restore_performed",false}};}
 boundaries96.push_back({{"output_index_zero_based",boundary96},{"naturally_committed_prefix_ids",prefix96},{"sampled_top1_id",sampled},{"top2_id",b},{"top1_logit",l1},{"top2_logit",l2},{"top2_margin",double(l1)-double(l2)},{"full_logits_sha256",lh},{"logits_scope","TOP2_VALUES_FULL_FP32_VECTOR_HASH_NOT_RAW_VECTOR"},{"last_consumed_input_ids",last_input96},{"last_consumed_position",last_pos96},{"last_phase",last_phase96},{"native_sample_output_row",index},{"actual_current_ub",llama_n_ubatch(ctx)},{"output_capacity",capacity},{"kv_min",llama_memory_seq_pos_min(llama_get_memory(ctx),0)},{"kv_max",llama_memory_seq_pos_max(llama_get_memory(ctx),0)},{"full_context_serialized_bytes",f.size()},{"full_context_sha256",fh},{"sequence_KV_serialized_bytes",k.size()},{"sequence_KV_sha256",kh},{"sampler","same-owned-native-greedy-no-stochastic-state"},{"pending_scope","last decoded IDs consumed; natural committed prefix separate; verify KV may retain uncommitted proposal"},{"same_owned_target_context",true},{"diagnostic_sync_readbacks",true},{"own_path_binding_sham",sham}});
 }
 int sample(int index){auto begin=timed()?clock_type::now():clock_type::time_point{};if(work)work->inc("sampling_calls");int id=llama_sampler_sample(sampler,ctx,index);if(work)work->span(role+"_SAMPLE",begin,"NATIVE_SAMPLER_WITH_EXISTING_LOGITS_WAIT");if(id<0||id>=llama_vocab_n_tokens(llama_model_get_vocab(model)))throw std::runtime_error("Sampler invalid ID");boundary_snapshot96(index,id);return id;}
 void trim(int pos){if(work)work->inc("kv_trim_calls");if(!llama_memory_seq_rm(llama_get_memory(ctx),0,pos,-1))throw std::runtime_error("KV rollback failure");if(llama_memory_seq_pos_max(llama_get_memory(ctx),0)!=pos-1)throw std::runtime_error("KV rollback positions");}
 ~Context(){if(sampler)llama_sampler_free(sampler);if(ctx)llama_free(ctx);if(model)llama_model_free(model);}
};
void vocab_guard(Context &t,Context &d){auto *a=llama_model_get_vocab(t.model),*b=llama_model_get_vocab(d.model);
 if(llama_vocab_n_tokens(a)!=llama_vocab_n_tokens(b)||llama_vocab_type(a)!=llama_vocab_type(b)||llama_vocab_bos(a)!=llama_vocab_bos(b)||llama_vocab_eos(a)!=llama_vocab_eos(b)||llama_vocab_get_add_bos(a)!=llama_vocab_get_add_bos(b)||llama_vocab_get_add_eos(a)!=llama_vocab_get_add_eos(b))throw std::runtime_error("Compatibility vocab metadata");
 for(int i=0;i<llama_vocab_n_tokens(a);++i)if(strcmp(llama_vocab_get_text(a,i),llama_vocab_get_text(b,i))||llama_vocab_get_attr(a,i)!=llama_vocab_get_attr(b,i)||llama_vocab_get_score(a,i)!=llama_vocab_get_score(b,i)||llama_vocab_is_eog(a,i)!=llama_vocab_is_eog(b,i))throw std::runtime_error("Compatibility full vocab row");
 emit({{"event","VOCAB_GUARD"},{"full_rows",llama_vocab_n_tokens(a)},{"status","PASS"},{"runtime_eog_equal",true},{"load_forward_calls",0}});
}
int main(int argc,char **argv){
 try{
  if(argc!=10)throw std::runtime_error("Arguments: profile target draft|NONE ub mode k trace_dir probe|resident observation_mode");
  std::string profile=argv[1],target=argv[2],draft=argv[3],mode=argv[5],dir=argv[7],action=argv[8];int ub=std::stoi(argv[4]),k=std::stoi(argv[6]);observation_mode=argv[9];if(observation_mode!="baseline"&&observation_mode!="counts"&&observation_mode!="lite"&&observation_mode!="heavy")throw std::runtime_error("Unknown observation mode");{std::ifstream f(std::filesystem::path(argv[0]).parent_path()/"COUNTER_HASH.txt");std::getline(f,counter_hash);if(counter_hash.size()!=64)throw std::runtime_error("Counter semantics binding missing");}
  int64_t threshold=536870912;if(profile!="STANDARD_Q6")throw std::runtime_error("PR90 only STANDARD_Q6");
  std::string tf=std::filesystem::path(target).filename().string(),df=std::filesystem::path(draft).filename().string();
  if(tf!=(profile=="STANDARD_Q6"?"Meta-Llama-3.1-8B-Instruct-Q6_K.gguf":"Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"))throw std::runtime_error("Profile target quantization mismatch");
  if(draft!="NONE"&&df!="Llama-3.2-1B-Instruct-Q4_K_M.gguf"&&(profile!="STANDARD_Q6"||df!="Llama-3.2-1B-Instruct-Q8_0.gguf"))throw std::runtime_error("Profile draft quantization mismatch");
  if(ub!=128&&ub!=512)throw std::runtime_error("Unknown ordinary UB");
  if(mode!="ordinary"&&mode!="native_greedy"&&mode!="vulkan_batched_repair"&&mode!="N_unrepaired")throw std::runtime_error("Unknown mode");
  if(k!=1||action!="probe"&&action!="resident")throw std::runtime_error("Unknown k/action");
  if(profile=="TIGHT_Q8"&&mode!="ordinary"&&ub!=32)throw std::runtime_error("Tight candidate prefill must be32");
  if(draft!="NONE"&&df!="Llama-3.2-1B-Instruct-Q4_K_M.gguf")throw std::runtime_error("PR90 only Q4 draft");if(draft!="NONE"&&ub!=512)throw std::runtime_error("PR96 speculative UB512 fixed");if(mode=="ordinary"&&draft!="NONE")throw std::runtime_error("Ordinary draft forbidden");
  std::filesystem::create_directories(dir);Memory memory(profile,threshold);memory.require("BEFORE_LOAD");ggml_backend_load_all();llama_backend_init();
  // All speculative and matched modes reserve four outputs, including smaller k.
  Context tgt(target,"TARGET",ub,mode=="ordinary"?1:4,&memory);std::unique_ptr<Context>dft;if(draft!="NONE"){dft=std::make_unique<Context>(draft,"DRAFT",1,1,&memory);vocab_guard(tgt,*dft);}
  if(mode=="vulkan_batched_repair"){llama_b570_pilot_bind_phase_ubatch(tgt.ctx,1);memory.require("REPAIR_WORKSPACE");llama_b570_pilot_bind_phase_ubatch(tgt.ctx,ub);}
  memory.require("LOADED");emit({{"event","READY"},{"profile",profile},{"mode",mode},{"pid",GetCurrentProcessId()},{"forward_calls",0},{"residency_status","RESIDENCY_UNKNOWN"},{"paging_observation","UNAVAILABLE_UNINSTRUMENTED_WDDM"}});
  if(action=="probe"){std::string finish;if(!std::getline(std::cin,finish)||finish!="PROBE_FINISH")throw std::runtime_error("Explicit zero-forward probe close required");emit({{"event","PROBE_COMPLETE"},{"forward_calls",0},{"target_graphs",llama_b570_work_graphs(tgt.ctx)},{"draft_graphs",dft?llama_b570_work_graphs(dft->ctx):0}});return 0;}
  bool checked=false;std::string line;while(std::getline(std::cin,line)){
   auto req=json::parse(line);if(req.value("op","")=="CHECK"){memory.require("PRE_REQUEST");checked=true;emit({{"event","CHECK_OK"},{"pid",GetCurrentProcessId()}});continue;}
   if(!checked)throw std::runtime_error("Explicit outside-timer memory admission required");checked=false;std::string rid=req.at("request_id");
   observation_mode=req.value("observation_mode",observation_mode);if(observation_mode!="baseline"&&observation_mode!="counts"&&observation_mode!="lite"&&observation_mode!="heavy")throw std::runtime_error("Unknown request observation mode");
   auto start=clock_type::now();auto inp=req.at("prompt_ids").get<std::vector<int>>();int cap=req.at("cap");bool capture=req.at("capture");if(capture&&!heavy())throw std::runtime_error("Full capture only heavy engineering");Work current(int(inp.size()));work=&current;
 partition98=req.value("prefill_partition",512);payload_dir98=req.value("payload_dir","");
 if((partition98!=128&&partition98!=512)||draft!="NONE"||mode!="ordinary")throw std::runtime_error("Diagnostic target-only partition contract");
 if(capture&&payload_dir98.empty())throw std::runtime_error("Missing diagnostic payload directory");
 payloads98=json::object();

 schedule100=req.at("prefill_schedule").get<std::vector<int>>();op100=req.value("operator_capture",false);layer100=req.value("operator_layer",0);opdir100=req.value("operator_dir","");tensors100=json::array();opbytes100=req.value("operator_bytes_existing",uint64_t(0));
 if(op100&&(!capture||opdir100.empty()||layer100!=0))throw std::runtime_error("Operator capture contract");
 diagnostic96=req.value("phase96_diagnostic",false);sham96=req.value("own_bind_sham",false);cuts96.clear();boundaries96=json::array();prefix96.clear();boundary96=0;sham_count96=0;
 if(diagnostic96&&!heavy())throw std::runtime_error("Boundary capture needs heavy");
 if(sham96&&!diagnostic96)throw std::runtime_error("Sham needs capture");
 if(req.contains("boundary_cuts"))for(int c:req["boundary_cuts"].get<std::vector<int>>()){if(c<0||c>127)throw std::runtime_error("Cut out of range");cuts96.insert(c);}
   if(inp.empty()||inp.size()>768||cap<1||cap>128||inp.size()+cap+k+1>1024)throw std::runtime_error("Request bounds");
   auto *v=llama_model_get_vocab(tgt.model);for(int id:inp)if(id<0||id>=llama_vocab_n_tokens(v))throw std::runtime_error("Prompt ID invalid");
   tgt.capture=capture;tgt.reset();if(dft){dft->capture=capture;dft->reset();}memory.failure_file=dir+"/"+rid+".failed-memory.json";memory.start();json restored100=nullptr;std::vector<float>initial100;
 if(req.contains("restore100")){
  if(ub!=512||!schedule100.empty()||op100)throw std::runtime_error("Receiver geometry contract");tgt.clean_receiver100();
  auto rd=[&](std::string key){auto path=req["restore100"][key]["path"].get<std::string>();std::ifstream f(path,std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(f)),{});if(b.size()!=req["restore100"][key]["bytes"].get<size_t>()||sha96(b.data(),b.size())!=req["restore100"][key]["sha256"].get<std::string>())throw std::runtime_error("Invalid donor payload pin");return b;};
  auto kv=rd("KV"),l=rd("logits");if(l.size()!=size_t(llama_vocab_n_tokens(v))*4)throw std::runtime_error("Invalid logits shape");initial100.resize(l.size()/4);memcpy(initial100.data(),l.data(),l.size());for(float x:initial100)if(!std::isfinite(x))throw std::runtime_error("Invalid FP32 logits");
  auto size=llama_state_seq_set_data(tgt.ctx,kv.data(),kv.size(),0);llama_synchronize(tgt.ctx);if(size!=kv.size())throw std::runtime_error("Incomplete sequence import");
  std::vector<uint8_t>check(llama_state_seq_get_size(tgt.ctx,0));check.resize(llama_state_seq_get_data(tgt.ctx,check.data(),check.size(),0));
  if(check!=kv||llama_memory_seq_pos_min(llama_get_memory(tgt.ctx),0)!=0||llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0)!=int(inp.size())-1)throw std::runtime_error("KV import differs");
  restored100={{"contract","BOUNDARY0_CLEAN_RECEIVER_NATIVE_GREEDY_EQUIVALENT_NOT_GENERAL_OPAQUE_CLONE"},{"KV_source",req["restore100"]["KV"]},{"logits_source",req["restore100"]["logits"]},{"post_restore_KV_sha256",sha96(check.data(),check.size())},{"post_restore_logits_sha256",sha96(initial100.data(),l.size())},{"KV_min",0},{"KV_max",int(inp.size())-1},{"extra_forward_calls",0},{"clean_context_and_scheduler",true},{"output_slot_reconstruction","initial FP32 consumed through same native apply/accept; next native decode recreates row0; no private dynamic-logit pointer injection"},{"committed_prefix",json::array()},{"pending_before_sample",nullptr},{"receiver_ub",512},{"capacity",1}};
 }else{tgt.prefill(inp);}memory.require("TARGET_PREFILL");if(dft){dft->prefill(inp);memory.require("DRAFT_PREFILL");}
   if(mode=="vulkan_batched_repair"){work->inc("phase_binding_calls");auto bind_begin=timed()?clock_type::now():clock_type::time_point{};auto pos=llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0);std::vector<uint8_t>before,after;if(capture){before.resize(llama_state_get_size(tgt.ctx));before.resize(llama_state_get_data(tgt.ctx,before.data(),before.size()));}llama_b570_pilot_bind_phase_ubatch(tgt.ctx,1);if(llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0)!=pos)throw std::runtime_error("Phase KV position changed");if(capture){after.resize(llama_state_get_size(tgt.ctx));after.resize(llama_state_get_data(tgt.ctx,after.data(),after.size()));if(before!=after)throw std::runtime_error("Phase KV bytes changed");tgt.trace.push_back({{"phase","BINDING"},{"before_bytes",before.size()},{"after_bytes",after.size()},{"actual_full_state_bytes_equal",before==after},{"from_ub",ub},{"to_ub",1}});}work->span("PHASE_BINDING",bind_begin,"INHERITED_COMPLETION_SYNC_AND_POSSIBLE_RESERVATION_NOT_EXCLUSIVE_WALL");memory.require("AFTER_PHASE_BINDING");}
   std::vector<int> out;std::vector<bool> flags;json verifies=json::array();int proposed=0,accepted=0,rollbacks=0;int next=-1;
 if(!initial100.empty()){
  std::vector<llama_token_data>cur;for(int i=0;i<int(initial100.size());++i)cur.push_back({i,initial100[i],0.0f});
  llama_token_data_array a={cur.data(),cur.size(),-1,false};llama_sampler_apply(tgt.sampler,&a);if(a.selected<0||a.selected>=int64_t(cur.size()))throw std::runtime_error("Native equivalent sample failed");next=cur[a.selected].id;llama_sampler_accept(tgt.sampler,next);work->inc("sampling_calls");restored100["natural_first_id"]=next;restored100["sampler_provenance"]="same llama_sampler_init_greedy/apply/accept, source-equivalent full ordered token_data vector";restored100["first_token_consumed_count"]=1;
 }else next=tgt.sample(-1);int base=int(inp.size());
   auto commit=[&](int id){if(out.size()>=size_t(cap)||(!flags.empty()&&flags.back()))throw std::runtime_error("Native suffix prevented");out.push_back(id);flags.push_back(llama_vocab_is_eog(v,id));return flags.back()||out.size()==size_t(cap);};
   work->inc("initial_target_committed");bool done=commit(next);
   while(!done){
    if(!dft){tgt.decode({next},base,false,"ORDINARY");++base;boundary96=int(out.size());prefix96=out;next=tgt.sample(-1);work->inc("fallback_committed");done=commit(next);continue;}
    dft->trim(base);dft->decode({next},base,false,"DRAFT_SYNC");std::vector<int> proposal;
    int count=std::min(k,cap-int(out.size()));for(int i=0;i<count;++i){int p=dft->sample(-1);proposal.push_back(p);++proposed;work->inc("proposal_generated");dft->decode({p},base+1+i,false,"PROPOSE");if(llama_vocab_is_eog(llama_model_get_vocab(dft->model),p))break;}
    std::vector<int> batch={next};batch.insert(batch.end(),proposal.begin(),proposal.end());tgt.decode(batch,base,true,"VERIFY");work->inc("proposal_verified",int(proposal.size()));work->inc("verification_seed_rows");work->inc("verify_cycles");if(counted())hist_add(work->w["verification_caller_width_hist"],int(batch.size()));int progress_before=int(out.size());
    int n=0;std::vector<int> decisions;for(size_t j=0;j<=proposal.size()&&!done;++j){boundary96=int(out.size());prefix96=out;int decision=tgt.sample(int(j));decisions.push_back(decision);if(j<proposal.size()&&counted())hist_add(work->w["attempted_positions"],int(j));
     done=commit(decision);if(j<proposal.size()&&decision==proposal[j]){++accepted;++n;work->inc("accepted_committed");if(counted())hist_add(work->w["accepted_positions"],int(j));if(done){work->inc("terminal_discarded",int(proposal.size())-int(j)-1);break;}}
     else {if(j<proposal.size()){work->inc("first_mismatch_rejected");work->inc("unexamined_after_mismatch",int(proposal.size())-int(j)-1);work->inc("correction_committed");}else work->inc("bonus_committed");next=decision;break;}}
    int keep=base+1+n;tgt.trim(keep);dft->trim(keep);base=keep;++rollbacks;work->inc("rollback_calls");if(counted()){hist_add(work->w["accepted_prefix_hist"],n);hist_add(work->w["cycle_progress_hist"],int(out.size())-progress_before);work->f["rollback_calls"]=work->f["rollback_calls"].get<int>()+1;}
    if(capture)verifies.push_back({{"batch_ids",batch},{"decisions",decisions},{"accepted",n},{"keep_pos",keep},{"repair_scope",mode=="vulkan_batched_repair"?"all_target_continuation_rows_physical_UB1":"none"},{"target_ub",llama_n_ubatch(tgt.ctx)}});
   }
   llama_synchronize(tgt.ctx);work->inc("inherited_explicit_sync_calls");if(dft){llama_synchronize(dft->ctx);work->inc("inherited_explicit_sync_calls");}memory.require("REQUEST_COMPLETE");auto mem=memory.stop();if(counted()){work->w["output_ids_count"]=out.size();work->f["reconcile_output_ids"]=out.size();}
   auto end=clock_type::now();std::string stop=flags.back()?"EOG":"CAP";
   json result={{"event","RESULT"},{"request_id",rid},{"pid",GetCurrentProcessId()},{"profile",profile},{"mode",mode},{"ids",out},{"eog",flags},{"length",out.size()},{"terminal_id",out.back()},{"stop_reason",stop},{"cap",cap},{"prompt_ids",inp},{"reset_target_min",tgt.reset_min},{"reset_target_max",tgt.reset_max},{"reset_draft_min",dft?json(dft->reset_min):json(nullptr)},{"reset_draft_max",dft?json(dft->reset_max):json(nullptr)},{"target_decode_calls",tgt.decodes},{"draft_decode_calls",dft?dft->decodes:0},{"proposed",proposed},{"accepted",accepted},{"rollback_operations",rollbacks},{"target_continuation_ub",llama_n_ubatch(tgt.ctx)},{"native_request_ms",std::chrono::duration<double,std::milli>(end-start).count()},{"residency_status","RESIDENCY_UNKNOWN"},{"memory_violation",bool(memory.violation)}};
   result["observation_mode"]=observation_mode;result["actual_condition"]={{"prefill_ub",ub},{"continuation_ub",llama_n_ubatch(tgt.ctx)},{"output_capacity",mode=="ordinary"?1:4},{"maximum_k",dft?1:0},{"logical_batch",512},{"n_ctx",1024},{"threads",10},{"kv","F16"},{"flash_attention",false}};
   result["workload"]=counted()?work->w:json(nullptr);result["feature_units"]=counted()?work->f:json(nullptr);
   result["observation"]={{"phase_timers",timed()},{"heavy_capture",capture},{"etw",false},{"added_sync",heavy()}};
   result["elapsed_hooks"]=timed()?work->spans:json(nullptr);result["component_completed_wall"]=nullptr;result["GPU_completion_event_ms"]=nullptr;
   result["phase96"]={{"diagnostic_capture",diagnostic96},{"requested_boundary_indices",cuts96},{"boundaries",boundaries96},{"own_bind_sham",sham96},{"own_bind_sham_calls",sham_count96},{"fork_status","FORK_NOT_IMPLEMENTABLE_CURRENT_ACTOR_NO_VALIDATED_FULL_CLONE"},{"evidence_scope","EXPOSED_DIAGNOSTIC_OUTPUT_WORK_NOT_PAID_FORMAL_COST"},{"GPU_completed_stage_wall",nullptr}};
 result["restore100"]=restored100;result["operator100"]={{"enabled",op100},{"layer",layer100},{"tensors",tensors100},{"new_unique_payload_total_bytes",opbytes100},{"shader_pipeline","UNKNOWN_NO_PUBLIC_BACKEND_DISPATCH_HOOK"}};
 result["partition100"]={{"caller_lengths",schedule100},{"final_only_logits",true}};
 result["partition98"]={{"external_submission_limit",partition98},{"context_ub_fixed",ub},{"prefill_logits_policy","ONLY_COMPLETE_PROMPT_FINAL_POSITION"},{"full_payloads",payloads98},{"cost_scope","DIAGNOSTIC_ONLY"}};
 result["component_timing_status"]=timed()?"ASYNC_ENQUEUE_SPANS_NOT_COMPLETED_WALL_PARTITION":"DISABLED_COUNTS_CHANNEL";
   emit(result); // Complete IDs travel before any disk persistence; controller hashes afterward.
   if(capture){std::ofstream f(dir+"/"+rid+".trace.json");f<<json({{"target",tgt.trace},{"draft",dft?dft->trace:json::array()},{"verify",verifies},{"memory",mem}}).dump()<<"\n";if(!f)throw std::runtime_error("Trace persistence");}
   else {std::ofstream f(dir+"/"+rid+".memory.json");f<<mem.dump()<<"\n";if(!f)throw std::runtime_error("Memory persistence");}
   if(memory.violation)throw std::runtime_error("MEMORY_BLOCKED:ENGINEERING_PEAK");work=nullptr;emit({{"event","PERSISTED"},{"request_id",rid}});
  }
 }catch(const std::exception&e){emit({{"event","ERROR"},{"reason",e.what()},{"pid",GetCurrentProcessId()},{"utc",utc()}});return 21;}
 return 0;
}
