// Built twice against the complete, matched original reference and loop4 trees.
// NEVER EXECUTE this linked binary in CPU preparation, even with --help: its
// original numerical archives contain GPU library/ELF initializers.
#include "runtime.hpp"
#include "../budget_writer/sha256.hpp"
#include "llama.h"
#include "ggml.h"
#include "ggml-backend.h"
#include "llama-kv-cache.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <fstream>
#include <map>
#include <sstream>
#include <unistd.h>
#include <cstdlib>
namespace {
using hs::n1chain::ProductionGate;using hs::n1chain::BudgetHooks;
struct Dispatch {ProductionGate*gate=nullptr;BudgetHooks*account=nullptr;std::string request;};
thread_local Dispatch dispatch;
// The sole native decode entry, including calls from BOTH original helpers.
int guarded_decode(llama_context*c,llama_batch b){
 hs::n1chain::require(dispatch.gate&&dispatch.account&&!dispatch.request.empty(),"native decode outside budget dispatch");
 dispatch.gate->before_decode(dispatch.request,size_t(b.n_tokens));
 dispatch.account->before_decode(dispatch.request,size_t(b.n_tokens));
 return ::llama_decode(c,b);
}
}
#if defined(HS_STRONG_LOOP4)
// The exact full frozen resident_context.hpp is included, not recreated from
// excerpts. Its planner sees the COMPLETE suffix and retains SIMPLE maximal
// rechunking. Only the actual decode call is intercepted for pre-reservation.
using json=nlohmann::json;using Clock=std::chrono::steady_clock;
static void need(bool x,const char*m){hs::n1chain::require(x,m);}
static double since(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
#include "hs_scope.h"
#include "hsc_counter.h"
inline bool phase_observe=false;
#define llama_decode guarded_decode
#include HS_FROZEN_RESIDENT_CONTEXT
#undef llama_decode
struct StrongOwner {
 llama_context*c=nullptr;llama_model*model=nullptr;bool capture=true;int calls=0;
 struct {std::string phase;int base=0,caller=0;bool bad=false;}obs;
 std::map<std::string,double>phases;
};
#else
// Generated only after verifying the WHOLE original reference.cpp SHA. The
// verbatim helper prefix reuses its Batch/decode/logits/finite greedy arithmetic;
// the old unguarded C1024 main is not compiled into this descendant.
#define llama_decode guarded_decode
#include "frozen_reference_primitives.inc"
#undef llama_decode
#endif
namespace hs::n1chain {
namespace {
std::string file_hash(const std::string&p){std::ifstream f(p,std::ios::binary);require(bool(f),"model hash open");Sha256 h;std::vector<char>b(1024*1024);while(f){f.read(b.data(),b.size());h.update(b.data(),size_t(f.gcount()));}require(f.eof(),"model hash read");return h.finish();}
class BoundCore final:public NativeCore {
 ProductionGate& gate_;BudgetHooks&account_;RuntimeConfig cfg_;
 llama_model*model_=nullptr;llama_context*ctx_=nullptr;const llama_vocab*vocab_=nullptr;
 bool poisoned_=false;std::string context_id_,fault_;nlohmann::json work_=nlohmann::json::array();
#if defined(HS_STRONG_LOOP4)
 StrongOwner owner_;PhaseContext plan_;
#endif
 void ready()const{require(!poisoned_&&ctx_&&model_,"native core invalid/poisoned");}
 void action(const std::string&id,const std::string&kind){gate_.before_mutation(id,kind);account_.before_mutation(id,kind);}
 void fail(const char*why)noexcept{poisoned_=true;gate_.poison(why);account_.poison(why);}
 public:
 BoundCore(ProductionGate&gate,BudgetHooks&account,const RuntimeConfig&cfg):gate_(gate),account_(account),cfg_(cfg){
  // This must precede even backend enumeration/default-parameter access. The
  // concrete gate always throws in this build. Source/static checks, not native
  // execution, verify this ordering during CPU preparation.
  gate_.before_backend_init(cfg.placement_id);account_.before_backend_init(cfg.placement_id);
  gate_.before_placement(cfg.placement_id);account_.before_placement(cfg.placement_id);
  require(cfg.threads==2,"fixed two-thread deployment");
  require(cfg.gpu_uuid.rfind("GPU-",0)==0&&cfg.gpu_uuid.size()==40,"explicit allocated UUID required");
  const char*visible=std::getenv("CUDA_VISIBLE_DEVICES");require(visible&&std::string(visible)==cfg.gpu_uuid,"visible device must equal the one separately approved UUID");
  require(cfg.model_sha256=="408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6","fixed Qwen model identity");
  require(file_hash(cfg.model_path)==cfg.model_sha256,"actual model bytes changed");
  ggml_time_init();llama_backend_init();ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();++i){auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){require(!gpu,"one allocated visible GPU required");gpu=d;}}
  require(gpu,"missing allocated GPU");ggml_backend_dev_t devices[]={gpu,nullptr};
  auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  gate_.before_model_load(cfg.placement_id);account_.before_model_load(cfg.placement_id);
  model_=llama_model_load_from_file(cfg.model_path.c_str(),mp);require(model_,"original-source model load");
  try{auto cp=llama_context_default_params();cp.n_ctx=4096;cp.n_batch=4096;cp.n_seq_max=1;
#if defined(HS_STRONG_LOOP4)
   cp.n_ubatch=32;cp.n_outputs_max=32;cp.n_outputs_max_per_seq=32;
   phase_lowering="SIMPLE";phase_target_reserve=32;hs_scope::active=false;hs_scope::requested_layout=0;
#else
   cp.n_ubatch=1;cp.n_outputs_max=1;cp.n_outputs_max_per_seq=1;
#endif
   cp.n_threads=cfg.threads;cp.n_threads_batch=cfg.threads;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
   gate_.before_context(cfg.placement_id);account_.before_context(cfg.placement_id);
   ctx_=llama_init_from_model(model_,cp);require(ctx_,"C4096 context allocation");
   vocab_=llama_model_get_vocab(model_);require(llama_vocab_n_tokens(vocab_)==151936,"actual model vocabulary");
   require(llama_n_ctx(ctx_)==4096&&llama_n_batch(ctx_)==4096,"actual context/batch echo");
   require(llama_n_ubatch(ctx_)==
#if defined(HS_STRONG_LOOP4)
    32
#else
    1
#endif
    ,"actual microbatch echo");
   require(head()==0,"new actual context not empty");
   context_id_=cfg.run_id+"-pid"+std::to_string(::getpid())+"-owned-context1";
#if defined(HS_STRONG_LOOP4)
   owner_.c=ctx_;owner_.model=model_;
#endif
  }catch(...){if(ctx_)llama_free(ctx_);ctx_=nullptr;llama_model_free(model_);model_=nullptr;fail("native setup failure");throw;}
 }
 ~BoundCore()override{
  // Releasing this object's own allocations after poison is cleanup, never a
  // new request/forward/placement. No object is created in CPU preparation.
  if(ctx_)llama_free(ctx_);if(model_)llama_model_free(model_);
 }
 void start_request(const std::string&id)override{ready();action(id,"REQUEST_LOCAL_TRACE_RESET");work_=nlohmann::json::array();}
 size_t head()const override{require(ctx_,"head on missing context");auto m=llama_get_memory(ctx_);const auto lo=llama_memory_seq_pos_min(m,0),hi=llama_memory_seq_pos_max(m,0);require(hi<0||lo==0,"nonzero native prefix origin");return hi<0?0:size_t(hi)+1;}
 size_t vocabulary()const override{ready();return size_t(llama_vocab_n_tokens(vocab_));}
 bool is_eog(int32_t t)const override{ready();require(t>=0&&size_t(t)<vocabulary(),"EOG token range");return llama_vocab_is_eog(vocab_,t);}
 int32_t greedy(const std::vector<float>&v)const override{ready();require(v.size()==vocabulary(),"full greedy vector");
#if defined(HS_STRONG_LOOP4)
  int32_t best=0;for(size_t i=0;i<v.size();++i){require(std::isfinite(v[i]),"finite original greedy contract");if(v[i]>v[size_t(best)])best=int32_t(i);}return best;
#else
  return ::greedy(v); // verbatim original finite/lowest-ID tie rule
#endif
 }
 std::vector<float> append(const std::string&id,const Tokens&ids,size_t position,bool initial)override{
  ready();require(!ids.empty()&&position==head()&&ids.size()<=4096-position,"native append/capacity");for(auto t:ids)require(t>=0&&size_t(t)<vocabulary(),"bound input token");
  action(id,"APPEND_BEGIN");dispatch={&gate_,&account_,id};
  try{
#if defined(HS_STRONG_LOOP4)
   const size_t before=plan_.executions.size();plan_.decode(owner_,ids,int(position),false,initial?"PREFILL":"ORDINARY");
   for(size_t i=before;i<plan_.executions.size();++i)work_.push_back(plan_.executions.at(i));
   auto*p=plan_.logits(-1);require(p,"owned planned output missing");std::vector<float>out(p,p+vocabulary());
#else
   if(initial){::decode(ctx_,ids,int(position),false);work_.push_back({{"kind","ORIGINAL_WHOLE_PREFILL_UB1"},{"position",position},{"rows",ids.size()},{"physical_microbatch",1}});}
   else{for(size_t i=0;i<ids.size();++i){::decode(ctx_,Tokens{ids[i]},int(position+i),false);work_.push_back({{"kind","ORIGINAL_ONE_TOKEN_APPEND_UB1"},{"position",position+i},{"rows",1}});}}
   auto out=::logits(ctx_,int(vocabulary()));
#endif
   require(head()==position+ids.size(),"actual native append incomplete");for(float x:out)require(std::isfinite(x),"full output contains nonfinite value");dispatch={};return out;
  }catch(...){dispatch={};fail("native append/partial decode failure");throw;}
 }
 TrimResult trim(const std::string&id,size_t keep)override{
  ready();require(keep<=head(),"trim exceeds actual head");action(id,"TRIM_BEGIN");
  if(fault_=="UNSUPPORTED_BEFORE_CALL"){fault_.clear();return TrimResult::UnsupportedBeforeCall;}
  if(fault_=="FAILED_BEFORE_MUTATION"){fault_.clear();return TrimResult::FailedBeforeMutation;}
  try{require(llama_memory_seq_rm(llama_get_memory(ctx_),0,llama_pos(keep),-1),"native trim failed; mutation uncertainty");require(head()==keep,"trim actual head mismatch");return TrimResult::Done;}
  catch(...){fail("native trim uncertain; unchanged head does not prove retained bytes");throw;}
 }
 void clear(const std::string&id)override{ready();action(id,"CLEAR_SEQ0");try{llama_memory_clear(llama_get_memory(ctx_),true);llama_synchronize(ctx_);require(head()==0,"actual reset failed");
#if defined(HS_STRONG_LOOP4)
  plan_.clear();
#endif
 }catch(...){fail("native reset uncertain");throw;}}
 llama_context*existing_context()const override{ready();return ctx_;}
 llama_model*existing_model()const override{ready();return model_;}
 std::string context_id()const override{ready();return context_id_;}
 std::string actual_work_json()const override{return work_.dump();}
 void set_control_fault(const std::string&fault)override{require(fault.empty()||fault=="UNSUPPORTED_BEFORE_CALL"||fault=="FAILED_BEFORE_MUTATION","unknown fault mode");fault_=fault;}
};
}
std::unique_ptr<NativeCore> make_native_core(ProductionGate&gate,BudgetHooks&account,const RuntimeConfig&cfg){
 gate.before_backend_init(cfg.placement_id); // deny before backend object construction
 return std::make_unique<BoundCore>(gate,account,cfg);
}
}
