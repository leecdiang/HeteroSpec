#include "execution_contract.hpp"
#include <iostream>
#include <stdexcept>
using namespace hs_reference_batching;
int main() {
 unsigned checks=0;
 auto check=[&](bool b){++checks;if(!b)throw std::runtime_error("failed "+std::to_string(checks));};
 DeploymentIdentity dep{"cuda","device","build","runtime","model","reference"};
 ReductionIdentity red{"q","acc","reduce","round","dispatch"};
 PackingRequest r; r.deployment=dep;r.input={128,256,8,"Q8_0","F32",true,true,true,true};
 r.selected_scalar=red;r.selected_grouped=red;r.state={dep,"recipe","prefix",32,5,true};
 r.prefix={PrefixStatus::supported,std::vector<uint32_t>(8,64)};
 PackingQualification q{dep,r.input,red,red,EvidenceLevel::bit_semantics,"test","",true,true};
 PackingRegistry reg;reg.add(q);
 for(bool opt:{false,true}) for(int failed_at=0;failed_at<2;++failed_at) for(bool throws:{false,true}) {
   auto req=r; if(!opt)req.input.all_gpu=false;
   auto live=req.state; int runs=0,verifies=0;
   auto operation=[&](){++runs;if(failed_at==0){live.clean=true;if(throws)throw 7;return false;}return true;};
   auto verify=[&](){++verifies;live.clean=true;if(throws)throw 7;return false;};
   bool caught=false;ExecutionResult result;
   try {result=execute_operator(req,reg,live,[&](auto &){return operation();},operation,verify);}catch(...){caught=true;}
   check(!live.clean);check(live.generation==req.state.generation+1);check(caught==throws);check(runs==1);check(verifies==failed_at);if(!throws)check(!result.success);
 }
 // Every piece of identity is rechecked after callbacks before CLEAN commit.
 for(int field=0;field<5;++field){
   auto live=r.state;
   auto result=execute_operator(r,reg,live,[&](auto &){live.clean=true;switch(field){case 0:++live.generation;break;case 1:++live.position;break;case 2:live.prefix_identity="bad";break;case 3:live.recipe="bad";break;case 4:live.deployment.model="bad";break;}return true;},[]{return true;},[]{return true;});
   check(!result.success&&!live.clean);
 }
 auto overflow=r;overflow.state.generation=~uint64_t(0);auto live=overflow.state;int calls=0;
 auto result=execute_operator(overflow,reg,live,[&](auto &){++calls;return true;},[&](){++calls;return true;},[&](){++calls;return true;});
 check(!result.success&&calls==0&&live.clean&&live.generation==~uint64_t(0));
 // Optional premises apply to all evidence types, not just structural records.
 for(auto level:{EvidenceLevel::empirical_replay,EvidenceLevel::structural_assumptions,EvidenceLevel::bit_semantics}){
   auto x=q;x.level=level;x.assumptions="actual input must satisfy premise";
   PackingRegistry missing;bool caught=false;try{missing.add(x);}catch(...){caught=true;}check(caught);
   for(int predicate=0;predicate<3;++predicate){
     PackingRegistry registry;int invocations=0;x.validate_assumptions=[&](const auto &){++invocations;if(predicate==2)throw 17;return predicate==1;};registry.add(x);
     auto req=r;req.allow_empirical=true;auto decision=packing_admission(req,registry);check(invocations==1);check((decision.action==Admission::optimized)==(predicate==1));
   }
 }
 // Predicate can add other scope qualifications and force vector reallocation.
 PackingRegistry expanding;auto x=q;x.level=EvidenceLevel::structural_assumptions;x.assumptions="test";
 x.validate_assumptions=[&](const auto &){for(uint64_t k=129;k<300;++k){auto other=q;other.input.k=k;expanding.add(other);}return true;};
 expanding.add(x);auto decision=packing_admission(r,expanding);check(decision.action==Admission::optimized&&decision.evidence_id==q.evidence_id);
 std::cout<<"INDEPENDENT_CPP_CHECKS="<<checks<<" GPU_EXECUTIONS=0\n";
}
