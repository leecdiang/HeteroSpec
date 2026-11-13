#pragma once
// Backend-independent state machine. Only its mock implementation is executed
// during CPU preparation; native factories have a separate concrete deny gate.
#include "../budget_writer/hooks.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <functional>
#include <optional>
#include <string>
#include <vector>
namespace hs::n1chain {
using Tokens=std::vector<int32_t>;
inline void require(bool ok,const char* why){if(!ok)throw Blocked(why);}
enum class TrimResult { Done, UnsupportedBeforeCall, FailedBeforeMutation };
struct Core {
 virtual ~Core()=default;
 virtual void start_request(const std::string&){}
 virtual size_t head()const=0;
 virtual size_t vocabulary()const=0;
 virtual bool is_eog(int32_t)const=0;
 virtual int32_t greedy(const std::vector<float>&)const=0;
 // The concrete backend reserves at each ACTUAL llama_decode boundary. Never
 // double-charge in this state machine, or reserve only an optimistic suffix.
 virtual std::vector<float> append(const std::string&,const Tokens&,size_t,bool initial)=0;
 virtual TrimResult trim(const std::string&,size_t)=0;
 virtual void clear(const std::string&)=0;
};
struct State {
 Tokens canonical,materialized,logical,generated;
 std::optional<int32_t> pending;
 std::vector<float> frontier;
 std::vector<std::vector<float>> requested_vectors;
 bool frontier_valid=false,frontier_owned=false;
 size_t retained=0;
 std::string stop_reason,request_id;
};
class Session {
 Core& core_;BudgetHooks& budget_;State s_;
 bool poisoned_=false,active_=false,appended_=false,terminal_=false;
 size_t cap_=0;std::vector<float> previous_owned_,previous_before_;
 public:
 using Checkpoint=std::function<void(const char*,const State&)>;
 Session(Core& core,BudgetHooks& budget):core_(core),budget_(budget){require(core_.head()==0,"new session requires empty actual context");}
 const State& state()const{return s_;}
 bool poisoned()const{return poisoned_;}
 const std::vector<float>& previous_owned()const{return previous_owned_;}
 const std::vector<float>& previous_before()const{return previous_before_;}
 void poison(const std::string& why)noexcept{poisoned_=true;s_.frontier_valid=false;s_.frontier_owned=false;s_.frontier.clear();budget_.poison(why);}
 void healthy(){
  require(!poisoned_,"session poisoned; no recovery/reentry under this run");
  try{require(core_.head()==s_.materialized.size(),"actual head drift");Tokens expected=s_.materialized;if(s_.pending)expected.push_back(*s_.pending);require(expected==s_.logical,"pending/logical ownership mismatch");}
  catch(...){poison("state mismatch");throw;}
 }
 void valid(const Tokens& ids)const{for(auto id:ids)require(id>=0&&size_t(id)<core_.vocabulary(),"token outside bound model vocabulary");}
 void own(std::vector<float> v){require(v.size()==core_.vocabulary(),"full requested vocabulary row required");for(float x:v)require(std::isfinite(x),"nonfinite requested output");s_.frontier=std::move(v);s_.frontier_valid=s_.frontier_owned=true;}
 void begin(const std::string&id,const Tokens& q,size_t cap,bool cold,size_t cold_keep,Checkpoint checkpoint){
  begin_lazy(id,[&]{return q;},cap,cold,cold_keep,std::move(checkpoint));
 }
 void begin_lazy(const std::string&id,const std::function<Tokens()>&build,size_t cap,bool cold,size_t cold_keep,Checkpoint checkpoint){
  try{healthy();require(!active_||terminal_,"begin over active request");
   if(active_){budget_.finish_request(s_.request_id,"COMPLETED");active_=false;}
   budget_.before_request(id); // charge before producer/render and reject paths
   s_.request_id=id;active_=true;appended_=terminal_=false;core_.start_request(id);
   const Tokens q=build();
   valid(q);require(!q.empty()&&cap>0&&cap<=128,"invalid canonical request/cap");
   require(q.size()<=4096&&cap-1<=4096-q.size(),"capacity rejection before native mutation");
   previous_owned_=s_.frontier;previous_before_=previous_owned_; // distinct owners
   size_t keep=0;
   if(cold){require(cold_keep<q.size(),"cold alignment needs nonempty canonical suffix");core_.clear(id);s_=State{};s_.request_id=id;keep=cold_keep;
    if(keep){Tokens prefix(q.begin(),q.begin()+keep);own(core_.append(id,prefix,0,true));s_.materialized=prefix;s_.logical=prefix;}}
   else{while(keep<s_.logical.size()&&keep<q.size()&&s_.logical[keep]==q[keep])++keep;keep=std::min(keep,s_.materialized.size());if(keep==q.size())--keep;
    if(keep<s_.materialized.size()){
     const auto result=core_.trim(id,keep);
     // Only a capability rejection or caller-controlled PRE-MUTATION failure
     // qualifies for common rebuild. A real failed native trim must throw/poison;
     // unchanged head is never evidence that retained K/V bytes are unchanged.
     if(result!=TrimResult::Done){core_.clear(id);keep=0;}
    }
    s_.materialized.assign(q.begin(),q.begin()+keep);s_.logical=s_.materialized;
    s_.frontier.clear();s_.frontier_valid=s_.frontier_owned=false;
   }
   require(core_.head()==keep,"reconciled actual head differs");s_.canonical=q;s_.retained=keep;s_.pending.reset();s_.generated.clear();s_.requested_vectors.clear();s_.stop_reason.clear();cap_=cap;
   checkpoint("POST_RECONCILE",s_);
  }catch(...){poison("request/reconcile/capture failed");throw;}
 }
 void append(Checkpoint checkpoint){
  try{healthy();require(active_&&!appended_&&!terminal_,"append phase");const size_t p=s_.materialized.size();Tokens suffix(s_.canonical.begin()+p,s_.canonical.end());require(!suffix.empty(),"empty suffix must replay final canonical token");
   own(core_.append(s_.request_id,suffix,p,p==0));require(core_.head()==s_.canonical.size(),"partial decode cannot expose frontier");
   s_.materialized=s_.logical=s_.canonical;s_.pending.reset();appended_=true;
   require(previous_owned_.size()==previous_before_.size()&&(previous_owned_.empty()||std::memcmp(previous_owned_.data(),previous_before_.data(),previous_owned_.size()*sizeof(float))==0),"caller-owned previous output changed after native decode");
   checkpoint("POST_APPEND",s_);
  }catch(...){poison("append/ownership/capture failed");throw;}
 }
 void generate(const Tokens&forced,Checkpoint checkpoint){
  try{healthy();require(active_&&appended_&&!terminal_,"complete append required before sampling");valid(forced);
   require(forced.empty()||forced.size()==cap_,"scripted control tape/cap mismatch");for(size_t i=0;i<cap_;++i){
    require(s_.frontier_valid&&s_.frontier_owned,"stale/unowned output cannot sample");
    s_.requested_vectors.push_back(s_.frontier);const int32_t t=forced.empty()?core_.greedy(s_.frontier):forced.at(i);
    require(t>=0&&size_t(t)<core_.vocabulary(),"sampled token outside model vocabulary");
    s_.generated.push_back(t);s_.pending=t;s_.logical=s_.materialized;s_.logical.push_back(t);
    const bool eog=core_.is_eog(t);
    if(eog||i+1==cap_){terminal_=true;s_.stop_reason=eog?"EOG":"CAP";checkpoint("TERMINAL",s_);return;}
    const size_t old_head=s_.materialized.size();own(core_.append(s_.request_id,Tokens{t},old_head,false));require(core_.head()==old_head+1,"generated decode actual head drift");s_.materialized.push_back(t);s_.logical=s_.materialized;s_.pending.reset();
   }}catch(...){poison("generation/capture/terminal journal failed");throw;}
  poison("unreachable generation exit");throw Blocked("unreachable generation exit");
 }
 void reset(const std::string&id,Checkpoint checkpoint){
  try{healthy();require(active_&&terminal_,"reset requires a terminal active request");require(id==s_.request_id,"reset must close its last charged request");core_.clear(id);require(core_.head()==0,"reset actual active state not empty");s_=State{};s_.request_id=id;active_=appended_=terminal_=false;cap_=0;checkpoint("RESET",s_);budget_.finish_request(id,"COMPLETED");}
  catch(...){poison("reset/capture failed");throw;}
 }
};
}
