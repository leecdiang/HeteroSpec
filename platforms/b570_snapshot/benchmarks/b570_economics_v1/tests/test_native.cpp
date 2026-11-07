#include "../native/phase_binding.hpp"
#include <iostream>
#include <cmath>
using namespace b570_cost;
static unsigned checks=0;
static void need(bool x){++checks;if(!x)throw std::runtime_error("test failure");}
int main(){
 Recorder r;r.enter(Phase::transition,0);r.enter(Phase::export_source,1);
 r.leave(Phase::export_source,3);r.leave(Phase::transition,5);
 need(r.valid&&r.depth==0);need(r.rows[7].inclusive_s==5);need(r.rows[7].exclusive_s==3);
 need(r.rows[8].exclusive_s==2);need(r.rows[7].exclusive_s+r.rows[8].exclusive_s==5);
 r.reset();r.enter(Phase::transition,0);r.leave(Phase::context_create,1);need(!r.valid);
 r=Recorder{};r.enter(Phase::transition,2);r.leave(Phase::transition,1);need(!r.valid);
 for(int i=0;i<100;++i){
  r=Recorder{};r.enter(Phase::transition,0);
  for(int k=0;k<i;++k){r.enter(Phase::state_checks,2*k);r.leave(Phase::state_checks,2*k+1);}
  r.leave(Phase::transition,2*i+1);
  need(r.valid);need(r.rows[14].calls==static_cast<unsigned>(i));
  need(std::abs(r.rows[7].exclusive_s+r.rows[14].exclusive_s-(2*i+1))<1e-10);
 }
 int object=0,owner=1;unsigned width=128;int calls=0;
 auto observe=[&]{return b570_econ::Snapshot{&object,&owner,0,19,width};};
 auto bind=[&](unsigned n){width=n;++calls;};
 b570_econ::bind_phase(1,observe,bind);need(width==1&&calls==1);
 b570_econ::bind_phase(1,observe,bind);need(calls==1);
 bool failed=false;try{b570_econ::bind_phase(2,observe,[&](unsigned){});}catch(...){failed=true;}need(failed);
 failed=false;try{b570_econ::bind_phase(0,observe,bind);}catch(...){failed=true;}need(failed);
 reset();int syncs=0;
 for(int i=0;i<2;++i){begin_decode("target","continuation",2,[&]{++syncs;});end_decode([&]{++syncs;});}
 if constexpr(B570_COST_MODE==0){need(syncs==0);need(recorder.decode_calls==0);}
 else {need(recorder.valid&&recorder.depth==0);need(recorder.decode_calls==2&&recorder.caller_rows==4);need(syncs==(B570_COST_MODE==2?4:0));}
 failed=false;try{classify("draft","invented_phase");}catch(...){failed=true;}need(failed);
 need(classify("draft","continuation")==Phase::draft_continuation_unsplit);
 if constexpr(B570_COST_MODE!=0){
  failed=false;try{measure(Phase::sampler_clone,[]{throw std::runtime_error("fixture");});}catch(...){failed=true;}
  need(failed&&recorder.depth==0&&recorder.valid);
 }
 std::cout<<"STANDALONE_HELPER_PASS "<<checks<<" mode="<<B570_COST_MODE<<"\n";
}
