#pragma once
// CPU-only lifecycle implementation; no llama/CUDA includes or runtime loader.
// The backend ABI is not yet bound to the unavailable frozen Linux source.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>
namespace n1a {
using Tokens=std::vector<int32_t>;
inline void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
enum class Trim {Done, Unsupported, FailedWithoutMutation};
struct Backend {
 virtual ~Backend()=default;
 // Only test backends can be used by this build. Native admission is absent.
 virtual bool is_mock()const=0;
 virtual size_t head()const=0;
 virtual Trim trim(size_t)=0;
 virtual void clear()=0;
 virtual std::vector<float> decode_one(int32_t,size_t)=0;
};
struct Meter {virtual ~Meter()=default; virtual void reserve_row()=0;};
struct State { Tokens materialized,logical,generated;std::optional<int32_t>pending;std::vector<float>frontier;bool frontier_valid=false;};
struct Session {
 Backend& b; Meter& meter; size_t vocab; State s; bool poisoned=false;bool begun=false;bool appended=false;bool terminal=false;Tokens expected;size_t expected_cap=0;
 Session(Backend& backend,Meter& m,size_t v):b(backend),meter(m),vocab(v){need(b.is_mock(),"native backend NOT ADMITTED");need(v>0,"vocab");need(b.head()==0,"fresh backend required");}
 void valid(const Tokens& ids)const {for(auto id:ids)need(id>=0&&size_t(id)<vocab,"token outside vocabulary");}
 void healthy() {need(!poisoned,"poisoned session");
  try{need(b.head()==s.materialized.size(),"observed backend head mismatch");
   Tokens logical=s.materialized;if(s.pending)logical.push_back(*s.pending);
   need(logical==s.logical,"logical/materialized/pending mismatch");
  }catch(...){poisoned=true;invalidate();throw;}
 }
 void invalidate(){s.frontier.clear();s.frontier_valid=false;}
 private:
 void decode(int32_t t){
  healthy();need(t>=0&&size_t(t)<vocab,"token outside vocabulary");need(s.materialized.size()<4096,"C4096 overflow");
  meter.reserve_row(); // reservation failure occurs before backend mutation
  try{auto out=b.decode_one(t,s.materialized.size());need(b.head()==s.materialized.size()+1,"actual native head mismatch");
   need(out.size()==vocab,"complete vocabulary required");for(float x:out)need(std::isfinite(x),"nonfinite output");
   s.materialized.push_back(t);s.logical=s.materialized;s.pending.reset();s.frontier=std::move(out);s.frontier_valid=true;
  }catch(...){poisoned=true;invalidate();throw;}
 }
 public:
 size_t begin(const Tokens& canonical,size_t cap,bool cold=false){
  healthy();need(!begun||terminal,"previous request not terminal");valid(canonical);need(!canonical.empty(),"empty prompt");need(cap>0&&cap<=128,"cap");need(canonical.size()<=4096&&cap-1<=4096-canonical.size(),"capacity rejection before mutation");
  size_t k=0;if(!cold){while(k<s.logical.size()&&k<canonical.size()&&s.logical[k]==canonical[k])++k;k=std::min(k,s.materialized.size());if(k==canonical.size())--k;}
  try{
   if(cold){b.clear();need(b.head()==0,"cold clear failed");}
   else if(k<s.materialized.size()){
    auto before=b.head();auto r=b.trim(k);
    if(r!=Trim::Done){need(b.head()==before,"declared no-mutation trim changed head");b.clear();k=0;}
    need(b.head()==k,"trim/reset head mismatch");
   }
   need(b.head()==k,"reconcile head mismatch");s.materialized.assign(canonical.begin(),canonical.begin()+k);s.logical=s.materialized;s.pending.reset();s.generated.clear();invalidate();begun=true;appended=false;terminal=false;expected=canonical;expected_cap=cap;
  }catch(...){poisoned=true;invalidate();throw;}
  return k; // POST_RECONCILE checkpoint; append is a separate explicit operation.
 }
 void append(const Tokens& canonical){
  healthy();valid(canonical);need(begun&&!appended&&!terminal,"append phase");need(canonical==expected,"canonical changed after reconcile");
  need(canonical.size()>s.materialized.size(),"fresh final output required");need(std::equal(s.materialized.begin(),s.materialized.end(),canonical.begin()),"suffix contract");
  const auto initial=s.materialized.size();
  try{for(size_t i=initial;i<canonical.size();++i)decode(canonical[i]);appended=true;}
  catch(...){if(s.materialized.size()!=initial)poisoned=true;if(poisoned)invalidate();throw;}
 }
 int32_t sample(){healthy();need(appended&&!terminal,"sample phase");need(s.frontier_valid&&s.frontier.size()==vocab,"fresh owned frontier required");auto p=std::max_element(s.frontier.begin(),s.frontier.end());return int32_t(p-s.frontier.begin());}
 Tokens generate(size_t cap,const Tokens& eog){
  healthy();need(begun&&appended&&!terminal,"complete append required before generation");
  need(cap==expected_cap,"cap changed after admission");valid(eog);need(s.generated.empty(),"generation already consumed");
  try{for(size_t i=0;i<cap;++i){int32_t t=sample();s.generated.push_back(t);s.pending=t;s.logical=s.materialized;s.logical.push_back(t);
    if(std::find(eog.begin(),eog.end(),t)!=eog.end()||i+1==cap){terminal=true;return s.generated;}
    decode(t); // final sample remains pending, including EOG. No synthetic EOS.
   }}catch(...){poisoned=true;invalidate();throw;}
  throw std::runtime_error("unreachable");
 }
 void reset(){healthy();try{b.clear();need(b.head()==0,"reset failed");s=State{};begun=false;appended=false;terminal=false;expected.clear();expected_cap=0;}catch(...){poisoned=true;invalidate();throw;}}
};
}
