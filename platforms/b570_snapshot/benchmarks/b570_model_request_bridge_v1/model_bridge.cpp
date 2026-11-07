#define NOMINMAX
#include <windows.h>
#include "llama.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <cstring>
#include <stdexcept>
using json=nlohmann::json;namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
static double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void dump(const fs::path&p,const json&v){std::ofstream f(p);f<<v.dump(2)<<'\n';need(bool(f),"write JSON");}
struct Observer{
 std::string phase="setup";int step=-1;size_t asks=0,unexpected_completions=0;
 std::map<std::string,json> signatures;
 static json tensor(ggml_tensor*t){
  json j={{"name",t->name},{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},
   {"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};
  if(t->buffer){auto*d=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer));j["device"]=d?ggml_backend_dev_description(d):"UNKNOWN";}
  else j["device"]="UNALLOCATED";
  return j;
 }
 static bool callback(ggml_tensor*t,bool ask,void*opaque){
  auto&o=*static_cast<Observer*>(opaque);
  if(!ask){o.unexpected_completions++;return true;}
  o.asks++;
  // Only admission metadata: never request per-node evaluation, readback or synchronization.
  std::string name=t->name;
  if(name.rfind("kq",0)!=0)return false;
  auto j=tensor(t);j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
  for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(tensor(t->src[i]));
  std::string key=o.phase+":"+j.dump();
  if(!o.signatures.count(key)){j["phase"]=o.phase;j["first_step"]=o.step;j["observed_asks"]=0;o.signatures[key]=j;}
  o.signatures[key]["observed_asks"]=o.signatures[key]["observed_asks"].get<int>()+1;
  return false;
 }
};
int main(int argc,char**argv){
 fs::path dest;llama_model*model=nullptr;llama_context*ctx=nullptr;
 json result={{"study","B570_REAL_REQUEST_GEOMETRY_BRIDGE"},{"status","STARTED"},{"runs",json::array()}};
 auto start=Clock::now();bool initialized=false;
 auto cleanup=[&](){if(ctx){llama_free(ctx);ctx=nullptr;}if(model){llama_model_free(model);model=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
 auto cutoff=[&](){need(elapsed(start)<100,"internal 100-second cutoff");};
 try{
  need(argc==4,"usage: model_bridge OUTPUT MODEL INPUT_JSON");
  dest=argv[1];need(!fs::exists(dest),"fresh output required");fs::create_directories(dest);
  std::ifstream inputfile(argv[3]);json input;inputfile>>input;
  std::vector<llama_token> prompt=input["prompt_ids"].get<std::vector<llama_token>>();
  need(prompt.size()>0&&prompt.size()+16<=1024,"prompt extent");
  result["prompt"]=input;dump(dest/"result.json",result);
  wchar_t exe[32768];need(GetModuleFileNameW(nullptr,exe,32768)>0,"exe path");
  auto dir=fs::path(exe).parent_path();
  // The pinned ggml DLL registers its linked CPU/Vulkan backends; do not use the dynamic-plugin ABI.

  llama_backend_init();initialized=true;
  ggml_backend_dev_t chosen=nullptr;result["devices"]=json::array();
  for(size_t i=0;i<ggml_backend_dev_count();i++){
   auto*d=ggml_backend_dev_get(i);std::string desc=ggml_backend_dev_description(d);
   result["devices"].push_back(desc);
   if(desc.find("B570")!=std::string::npos){need(!chosen,"ambiguous B570");chosen=d;}
  }
  need(chosen,"B570 unavailable");ggml_backend_dev_t devices[]={chosen,nullptr};
  auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*p){return elapsed(*static_cast<Clock::time_point*>(p))<100;};mp.progress_callback_user_data=&start;
  model=llama_model_load_from_file(argv[2],mp);need(model,"model load");
  result["model"]={{"heads",llama_model_n_head(model)},{"kv_heads",llama_model_n_head_kv(model)},{"layers",llama_model_n_layer(model)}};
  need(llama_model_n_head(model)==32&&llama_model_n_head_kv(model)==8,"expected Qwen3-8B GQA");
  const auto*vocab=llama_model_get_vocab(model);const int nv=llama_vocab_n_tokens(vocab);
  for(auto id:prompt)need(id>=0&&id<nv,"input token range");
  std::vector<std::vector<float>>reference;std::vector<llama_token>reference_ids;
  for(int run=0;run<3;run++){
   cutoff();Observer observer;auto cp=llama_context_default_params();
   cp.n_ctx=1024;cp.n_batch=512;cp.n_ubatch=1;cp.n_threads=8;cp.n_threads_batch=8;
   cp.n_outputs_max=1;cp.n_outputs_max_per_seq=1;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
   cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.no_perf=false;
   if(run==1){cp.cb_eval=Observer::callback;cp.cb_eval_user_data=&observer;}
   ctx=llama_init_from_model(model,cp);need(ctx,"context initialization");
   json r={{"run",run},{"arm",run==1?"METADATA_ONLY":"CLEAN"},{"context",1024},{"ubatch",1},{"steps",json::array()}};
   auto request_start=Clock::now();observer.phase="prefill";
   auto batch=llama_batch_get_one(prompt.data(),int(prompt.size()));
   need(llama_decode(ctx,batch)==0,"prefill decode");llama_synchronize(ctx);
   r["prefill_completed_seconds"]=elapsed(request_start);
   for(int step=0;step<16;step++){
    cutoff();auto*logits=llama_get_logits_ith(ctx,-1);need(logits,"full logits");
    std::vector<float>raw(logits,logits+nv);int token=0;
    for(int id=0;id<nv;id++){need(std::isfinite(raw[id]),"nonfinite logits");if(raw[id]>raw[token])token=id;}
    std::ofstream f(dest/("run-"+std::to_string(run)+"-step-"+std::to_string(step)+".f32"),std::ios::binary);
    f.write(reinterpret_cast<const char*>(raw.data()),raw.size()*4);need(bool(f),"save complete logits");f.close();
    if(run==0){reference.push_back(raw);reference_ids.push_back(token);}
    else{need(size_t(step)<reference.size(),"reference step exists");need(token==reference_ids[step],"greedy ID mismatch");
     need(std::memcmp(raw.data(),reference[step].data(),raw.size()*4)==0,"complete logits mismatch");}
    r["steps"].push_back({{"step",step},{"token_id",token},{"eog",llama_vocab_is_eog(vocab,token)},{"reference_bytes_match",run!=0}});
    if(llama_vocab_is_eog(vocab,token)||step==15)break;
    observer.phase="decode";observer.step=step;auto t=Clock::now();
    auto one=llama_batch_get_one(&token,1);need(llama_decode(ctx,one)==0,"generation decode");llama_synchronize(ctx);
    r["steps"].back()["decode_completed_seconds"]=elapsed(t);
   }
   if(run!=0)need(r["steps"].size()==reference.size(),"output length mismatch");
   r["request_diagnostic_seconds"]=elapsed(request_start);r["observer_asks"]=observer.asks;
   r["observer_unexpected_completions"]=observer.unexpected_completions;
   r["signatures"]=json::array();for(const auto&kv:observer.signatures)r["signatures"].push_back(kv.second);
   if(run==1){need(observer.asks>0&&!observer.signatures.empty(),"no real attention metadata");need(observer.unexpected_completions==0,"observer requested evaluation");}
   llama_free(ctx);ctx=nullptr;r["context_cleanup_returned"]=true;r["status"]="PASS";
   result["runs"].push_back(r);dump(dest/"result.json",result);
   std::cout<<json({{"event","RUN_PASS"},{"run",run},{"steps",r["steps"].size()},{"observer_asks",observer.asks}}).dump()<<std::endl;
  }
  cleanup();result["normal_cleanup_returned"]=true;result["status"]="GEOMETRY_AND_OBSERVER_QUALIFIED";
  result["charged_scope_note"]="Parent receipt charges all native wall; request times include raw-logit capture and are diagnostic, not clean performance or attention critical-path shares.";
  result["native_seconds"]=elapsed(start);dump(dest/"result.json",result);return 0;
 }catch(const std::exception&e){
  result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();
  cleanup();result["normal_cleanup_returned"]=true;result["native_seconds"]=elapsed(start);
  if(!dest.empty()&&fs::exists(dest))dump(dest/"result.json",result);
  std::cerr<<e.what()<<std::endl;return 2;
 }
}
