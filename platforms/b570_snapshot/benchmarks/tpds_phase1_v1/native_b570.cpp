// Phase1 host adapter. Arithmetic and resident phase binding remain in the pinned cores.
#include "common.h"
#include "llama.h"
#include "llama-ext.h"
#include "ggml-backend.h"
#include "nlohmann/json.hpp"
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <chrono>
using J=nlohmann::ordered_json;
using Clock=std::chrono::steady_clock;
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
#include "resource_budget.hpp"
#include "smol_bulk.hpp"
#if PHASE1_CORE
extern "C" __declspec(dllimport) int b570_economics_bind_phase(llama_context*,uint32_t) noexcept;
extern "C" __declspec(dllimport) int b570_phase1_allocation(llama_context*,uint64_t*) noexcept;
#endif
#if PHASE1_CORE == 2
extern "C" __declspec(dllimport) void hs_b570_set_layout(int);
extern "C" __declspec(dllimport) void hs_b570_set_reference_q8(bool);
extern "C" __declspec(dllimport) void hs_b570_set_prefix_extent(bool);
#endif
static void policy(bool active){
#if PHASE1_CORE == 2
 hs_b570_set_layout(active?2:0);hs_b570_set_reference_q8(active);hs_b570_set_prefix_extent(active);
#endif
}
static int64_t ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
static double ms(int64_t a,int64_t b){return (b-a)/1e6;}
static void dump(const std::string&p,const J&j){std::ofstream f(p);f<<j.dump(2)<<"\n";need(bool(f),"JSON write");}
static void bytes(const std::string&p,const void*b,size_t n){std::ofstream f(p,std::ios::binary);f.write((const char*)b,n);need(bool(f),"binary write");}
struct Audit {
 bool active=false;uint64_t exports=0,imports=0,replays=0,heavy=0;
 void reset(){exports=imports=replays=heavy=0;}
 J json(){return {{"state_exports",exports},{"state_imports",imports},{"reference_replays",replays},{"heavy_captures",heavy}};}
} audit;
static std::vector<uint8_t> capture(llama_context*c){if(audit.active){++audit.exports;++audit.heavy;}return smol_bulk_state(c);}
static void restore(llama_context*c,const std::vector<uint8_t>&b){if(audit.active)++audit.imports;need(llama_state_seq_set_data(c,b.data(),b.size(),0)==b.size(),"sequence import");}
static J capacity(llama_context*c){
 MEMORYSTATUSEX m{};m.dwLength=sizeof(m);need(GlobalMemoryStatusEx(&m),"RAM query");need(m.ullAvailPhys>=2ULL*1024*1024*1024,"RAM floor");
 auto free=bounded_vulkan_free();need(free>=128ULL*1024*1024,"signed GPU budget floor");
 J b=J::array();for(auto&x:llama_get_memory_breakdown(c))b.push_back({{"buffer_type",ggml_backend_buft_name(x.first)},{"model",x.second.model},{"context",x.second.context},{"compute",x.second.compute}});
 J j={{"actual_n_ctx",llama_n_ctx(c)},{"actual_n_batch",llama_n_batch(c)},{"actual_n_ubatch",llama_n_ubatch(c)},{"memory_breakdown",b},{"positive_signed_budget_bytes",free},{"available_RAM_bytes",m.ullAvailPhys}};
#if PHASE1_CORE
 uint64_t v[9]{};need(!b570_phase1_allocation(c,v),"allocation ABI");j["allocation"]={{"n_ctx",v[0]},{"n_ubatch",v[1]},{"n_batch",v[2]},{"n_outputs_max",v[3]},{"n_outputs_max_per_seq",v[4]},{"n_outputs_used",v[5]},{"logits_elements",v[6]},{"output_buffer_bytes",v[7]},{"scheduler_buffer_bytes",v[8]}};
#endif
 return j;
}
static void bind(llama_context*c,int n){
#if PHASE1_CORE
 need(!b570_economics_bind_phase(c,n),"resident phase binding poisoned context");
#else
 need(n==128,"original producer UB");
#endif
}
// All decode/begin/end/finish paths are owned here. There is no external observer callback.
static void decode(llama_context*c,llama_batch b){need(llama_decode(c,b)==0,"decode");}
static std::vector<float> row(llama_context*c,int i,int nv){auto*p=llama_get_logits_ith(c,i);need(p,"requested logits");return {p,p+nv};}
int main(int argc,char**argv){try{
 need(argc==6,"usage: worker target draft capacity method output-reserve");
 const int cap=std::stoi(argv[3]);need(cap==1024||cap==4096,"capacity");const std::string method=argv[4];need(method=="R"||method=="S"||method=="L","method");
 const int reserve=std::stoi(argv[5]);need(reserve==0||reserve==4,"no reserve32");
 common_init();llama_backend_init();common_params p;p.model.path=argv[1];p.n_ctx=cap;p.n_batch=512;p.n_ubatch=128;p.n_gpu_layers=-2;p.fit_params=false;p.warmup=false;p.n_predict=128;p.sampling.temp=0;p.sampling.seed=123;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;p.cache_type_k=GGML_TYPE_F16;p.cache_type_v=GGML_TYPE_F16;p.cpuparams.n_threads=10;p.cpuparams_batch.n_threads=10;
 if(reserve){p.n_outputs_max=reserve;p.n_outputs_max_per_seq=reserve;}
 auto owner=common_init_from_params(p);auto*c=owner->context();need(c,"target context");auto*model=owner->model();const int nv=llama_vocab_n_tokens(llama_model_get_vocab(model));
 auto d=p;d.model.path=argv[2];d.n_ubatch=1;d.n_outputs_max=1;d.n_outputs_max_per_seq=1;auto idle=common_init_from_params(d);need(idle->context(),"matched idle draft");need(llama_n_ctx(c)==unsigned(cap)&&llama_n_ctx(idle->context())==unsigned(cap),"actual capacity binding");
 auto admission=capacity(c);std::cout<<"HS_READY\n"<<std::flush;
 std::vector<uint8_t> prepared;std::string prepared_path;std::string line;
 while(std::getline(std::cin,line)){
  auto service_begin=ns();J r=J::parse(line);auto out=r.at("output").get<std::string>();std::filesystem::create_directories(std::filesystem::path(out).parent_path());
  if(std::getenv("HS_ECON_MICROTRACE"))std::fprintf(stderr,"PHASE1_REQUEST %s\n",r.at("request_id").get<std::string>().c_str());
  const auto ids=r.at("prompt_ids").get<std::vector<int>>(),suffix=r.at("known_suffix").get<std::vector<int>>();const int q=int(suffix.size()),head=int(ids.size());need((q==2||q==4||q==32)&&head+q<=cap,"query contract");
  for(auto t:ids)need(t>=0&&t<nv,"prompt token");for(auto t:suffix)need(t>=0&&t<nv,"suffix token");
  policy(false);llama_memory_clear(llama_get_memory(c),true);llama_memory_clear(llama_get_memory(idle->context()),true);llama_synchronize(c);llama_synchronize(idle->context());if(!r.contains("restore"))bind(c,128);
  auto reset_end=ns();double import_ms=0,prefill_ms=0;std::vector<float> initial;
  if(r.contains("restore")){
   const std::string path=r.at("restore");auto a=ns();if(path!=prepared_path){std::ifstream f(path,std::ios::binary);need(bool(f),"state file");prepared.assign(std::istreambuf_iterator<char>(f),{});prepared_path=path;}
   restore(c,prepared);llama_synchronize(c);import_ms=ms(a,ns());
  }else{
   if(audit.active)++audit.replays;auto a=ns();std::vector<int> all;int past=0;
   // Unchanged whole-prompt outer512 / physical UB128 producer, including tail.
   for(size_t at=0;at<ids.size();at+=512){int n=int(std::min(size_t(512),ids.size()-at));all.insert(all.end(),ids.begin()+at,ids.begin()+at+n);need(common_prompt_batch_decode(c,all,n,past,512,"",false),"original whole-prompt producer");}
   llama_synchronize(c);prefill_ms=ms(a,ns());initial=row(c,-1,nv);
  }
  need(llama_memory_seq_pos_min(llama_get_memory(c),0)==0&&llama_memory_seq_pos_max(llama_get_memory(c),0)==head-1,"valid prepared prefix");
  if(r.contains("ordinary_cap")){
   const int limit=r.at("ordinary_cap");need((limit==1||limit==128)&&!initial.empty(),"ordinary control");
   policy(method!="R");bind(c,128);J emitted=J::array(),eogs=J::array();std::vector<float> frontier=initial;
   for(int i=0;i<limit;++i){
    int token=0;for(int j=1;j<nv;++j)if(frontier[j]>frontier[token])token=j;
    bool stop=llama_vocab_is_eog(llama_model_get_vocab(model),token);emitted.push_back(token);eogs.push_back(stop);
    bytes(out+".ordinary-row"+std::to_string(i)+".f32",frontier.data(),frontier.size()*4);
    if(stop||i==limit-1)break;auto one=llama_batch_init(1,0,1);common_batch_add(one,token,head+i,{0},true);decode(c,one);llama_batch_free(one);frontier=row(c,0,nv);
   }
   llama_synchronize(c);auto b=capture(c);bytes(out+".ordinary-final.bin",b.data(),b.size());
   int materialized=llama_memory_seq_pos_max(llama_get_memory(c),0)+1-head;
   dump(out,J{{"request_id",r.at("request_id")},{"ordinary_control",true},{"capacity_observed",llama_n_ctx(c)},{"ids",emitted},{"eog",eogs},{"materialized_output_tokens",materialized},{"pending_id",emitted.back()},{"terminal_kind",eogs.back().get<bool>()?"EOG":"CAP"},{"cap",limit},{"service_ms",ms(service_begin,ns())},{"generation_ub",llama_n_ubatch(c)},{"admission_after_request",capacity(c)}});
   std::cout<<"HS_RESULT "<<r.at("request_id")<<"\n"<<std::flush;continue;
  }
  bool heavy=r.value("heavy",false);if(heavy){auto b=capture(c);bytes(out+".initial.bin",b.data(),b.size());if(!initial.empty())bytes(out+".initial.f32",initial.data(),initial.size()*4);}
  auto prepared_end=ns();std::vector<std::vector<float>> owned;owned.reserve(q<=4?q:1);
  auto batch=llama_batch_init(q,0,1);for(int j=0;j<q;++j)common_batch_add(batch,suffix[j],head+j,{0},q<=4||j==q-1);
  // The clock includes native phase binding/reserve, decode, sync and requested copy.
  if(std::getenv("HS_ECON_MICROTRACE"))std::fprintf(stderr,"PHASE1_APPEND_BEGIN\n");
  audit.reset();audit.active=true;const auto begin=ns()/1000;
  policy(method!="R");bind(c,method=="R"?128:q);
  if(r.value("counter_probe",false)){
   auto witness=capture(c);need(!witness.empty(),"counter probe");restore(c,witness);
   // Deliberately dirty diagnostic: exercise every real scope counter.
   ++audit.replays;policy(false);llama_memory_clear(llama_get_memory(c),true);bind(c,128);
   std::vector<int> replay;int past=0;
   for(size_t at=0;at<ids.size();at+=512){int n=int(std::min(size_t(512),ids.size()-at));replay.insert(replay.end(),ids.begin()+at,ids.begin()+at+n);need(common_prompt_batch_decode(c,replay,n,past,512,"",false),"diagnostic replay");}
   llama_synchronize(c);policy(method!="R");bind(c,method=="R"?128:q);
  }
  if(method=="R"){
   for(int j=0;j<q;++j){auto one=llama_batch_init(1,0,1);common_batch_add(one,suffix[j],head+j,{0},true);decode(c,one);llama_batch_free(one);if(q<=4||j==q-1)owned.push_back(row(c,0,nv));}
  }else{decode(c,batch);llama_synchronize(c);for(int j=0;j<q;++j)if(q<=4||j==q-1)owned.push_back(row(c,j,nv));}
  llama_synchronize(c);const auto end=ns()/1000;audit.active=false;llama_batch_free(batch);
  if(std::getenv("HS_ECON_MICROTRACE"))std::fprintf(stderr,"PHASE1_APPEND_END\n");
  // Heavy witnesses and disk output are outside the append clock, independently charged.
  J stats={{"request_id",r.at("request_id")},{"capacity_observed",llama_n_ctx(c)},{"requested_mask",q<=4?"all":"last"},{"observed_copied_rows",owned.size()},{"phase1_clean",!r.value("counter_probe",false)},{"prefill_outside_append",true},{"append_includes_phase_bind_sync_and_requested_copy",true},{"append_observer_calls",audit.json()},{"native_admission_receipt",r.at("admission_id")},{"append_begin_us",begin},{"append_end_us",end},{"append_ms",(end-begin)/1000.0},{"reset_ms",ms(service_begin,reset_end)},{"prefill_ms",prefill_ms},{"state_import_and_read_ms",import_ms},{"preparation_ms",ms(service_begin,prepared_end)},{"head",head},{"width",q},{"method",method},{"target_owner",uintptr_t(c)},{"KV_owner",uintptr_t(llama_get_memory(c))},{"original_producer_ub",128},{"original_producer_outer",512},{"explicit_output_reserve",reserve},{"capture_heavy",heavy}};
  if(heavy){auto b=capture(c);bytes(out+".final.bin",b.data(),b.size());for(size_t j=0;j<owned.size();++j)bytes(out+".row"+std::to_string(j)+".f32",owned[j].data(),owned[j].size()*4);stats["admission_after_request"]=capacity(c);}
  stats["final_position_min"]=llama_memory_seq_pos_min(llama_get_memory(c),0);stats["final_position_max"]=llama_memory_seq_pos_max(llama_get_memory(c),0);stats["service_ms"]=ms(service_begin,ns());dump(out,stats);std::cout<<"HS_RESULT "<<stats.dump()<<"\n"<<std::flush;
 }
 return 0;
}catch(const std::exception&e){std::cerr<<"PHASE1_FAILURE "<<e.what()<<"\n";return 31;}}
