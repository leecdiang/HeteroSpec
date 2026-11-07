#pragma once
// Host-clock diagnostics, never a claim of device-kernel time.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <utility>
#ifndef B570_COST_MODE
#define B570_COST_MODE 0
#endif
#ifndef B570_ECON_SPEC
#define B570_ECON_SPEC 0
#endif
static_assert(B570_COST_MODE>=0 && B570_COST_MODE<=2, "cost mode");
namespace b570_cost {
enum class Phase : std::size_t {
 target_prefill, target_ordinary, target_verify, draft_prefill,
 draft_sync, draft_proposal, draft_continuation_unsplit,
 transition, export_source, import_state, export_destination,
 export_source_after, context_create, context_destroy, state_checks,
 sampler_clone, phase_bind, barrier_before, count
};
constexpr std::size_t N=static_cast<std::size_t>(Phase::count);
constexpr const char* names[N]={"target_prefill","target_ordinary","target_verify",
 "draft_prefill","draft_sync","draft_proposal","draft_continuation_unsplit",
 "transition","export_source","import_state","export_destination","export_source_after",
 "context_create","context_destroy","state_checks","sampler_clone","phase_bind","barrier_before"};
struct Row { std::uint64_t calls=0; double inclusive_s=0, exclusive_s=0; };
struct Frame { Phase phase; double start, children; };
struct Recorder {
 std::array<Row,N> rows{}; std::array<Frame,32> stack{};
 std::size_t depth=0; bool valid=true; std::uint64_t decode_calls=0, caller_rows=0;
 void reset(){ if(depth)throw std::runtime_error("unfinished diagnostic span"); *this=Recorder{}; }
 void enter(Phase p,double now){ if(depth==stack.size())throw std::runtime_error("span depth"); stack[depth++]={p,now,0}; }
 void leave(Phase p,double now) noexcept {
  if(!depth || stack[depth-1].phase!=p){valid=false;return;}
  auto f=stack[--depth]; const double elapsed=now-f.start;
  if(elapsed<0 || elapsed+1e-12<f.children){valid=false;return;}
  auto&r=rows[static_cast<std::size_t>(p)];++r.calls;
  r.inclusive_s+=elapsed;r.exclusive_s+=elapsed-f.children;
  if(depth)stack[depth-1].children+=elapsed;
 }
};
inline thread_local Recorder recorder;
inline double now(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
class Span {
 Phase phase;
public:
 explicit Span(Phase p):phase(p){if constexpr(B570_COST_MODE!=0)recorder.enter(p,now());}
 Span(const Span&)=delete;Span&operator=(const Span&)=delete;
 ~Span(){if constexpr(B570_COST_MODE!=0)recorder.leave(phase,now());}
};
template<class F> decltype(auto) measure(Phase p,F&& f){Span span(p);return std::forward<F>(f)();}
inline Phase classify(const std::string&role,const std::string&phase){
 if((role!="draft" && role!="target") || (phase!="prefill" && phase!="continuation"))throw std::runtime_error("unknown cost phase");
 if(role=="draft")return phase=="prefill"?Phase::draft_prefill:Phase::draft_continuation_unsplit;
 return phase=="prefill"?Phase::target_prefill:(B570_ECON_SPEC?Phase::target_verify:Phase::target_ordinary);
}
// Split sync/proposal only at actual distinct caller sites. Never fabricate two
// component times by splitting an indivisible native call.
inline thread_local Phase decode_phase=Phase::count;
template<class Sync> void begin_decode(const std::string&role,const std::string&phase,int rows,Sync sync){
 if constexpr(B570_COST_MODE!=0){
  if(decode_phase!=Phase::count||rows<1)throw std::runtime_error("invalid decode span");
  if constexpr(B570_COST_MODE==2)measure(Phase::barrier_before,sync);
  decode_phase=classify(role,phase);recorder.enter(decode_phase,now());
  ++recorder.decode_calls;recorder.caller_rows+=static_cast<std::uint64_t>(rows);
 }
}
template<class Sync> void end_decode(Sync sync){
 if constexpr(B570_COST_MODE!=0){
  if(decode_phase==Phase::count)throw std::runtime_error("decode end without begin");
  if constexpr(B570_COST_MODE==2)sync();
  recorder.leave(decode_phase,now());decode_phase=Phase::count;
 }
}
inline void reset(){if constexpr(B570_COST_MODE!=0){recorder.reset();decode_phase=Phase::count;}}
inline void write(const std::string&path){
 if constexpr(B570_COST_MODE!=0){
  if(!recorder.valid||recorder.depth||decode_phase!=Phase::count)throw std::runtime_error("invalid diagnostic trace");
  std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("cost output");
  f<<std::setprecision(17)<<"{\"schema\":\"b570-cost-v1\",\"mode\":"<<B570_COST_MODE
   <<",\"valid\":true,\"clock\":\"host-steady\",\"device_time\":false,\"decode_calls\":"<<recorder.decode_calls
   <<",\"caller_rows\":"<<recorder.caller_rows<<",\"phases\":{";
  for(std::size_t i=0;i<N;++i){const auto&r=recorder.rows[i];if(i)f<<',';
   f<<'"'<<names[i]<<"\":{\"calls\":"<<r.calls<<",\"inclusive_s\":"<<r.inclusive_s<<",\"exclusive_s\":"<<r.exclusive_s<<'}';}
  f<<"}}\n";if(!f)throw std::runtime_error("cost write");
 }
}
}
