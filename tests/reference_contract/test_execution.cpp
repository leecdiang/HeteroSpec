#include "packing_gate.hpp"
#include <cassert>
#include <iostream>
#include <thread>
using namespace hs_reference_batching;

DeploymentIdentity deployment() { return {"cuda","RTX5070TiLaptop","pinned-source+compiler","runtime+driver","model-sha","scalar-sha"}; }
ReductionIdentity reduction() { return {"q8_1-row","fp32","mmvq-width4-block32x4","rounding-profile","kernel-sha+launch"}; }
PackingRequest request() {
    PackingRequest r;
    r.deployment=deployment();
    r.input={128,256,32,"Q8_0","F32",true,true,true,true};
    r.selected_scalar=reduction(); r.selected_grouped=reduction();
    r.state={deployment(),"scalar-producer","tokens+positions",128,1,true};
    r.prefix={PrefixStatus::supported,std::vector<uint32_t>(32,256)};
    return r;
}
PackingQualification qualification(const PackingRequest&r) {
    return {r.deployment,r.input,r.selected_scalar,r.selected_grouped,
            EvidenceLevel::empirical_replay,"synthetic-test-receipt-not-GPU-evidence","",true,true};
}
int main() {
    unsigned checks=0;
    const auto check=[&](bool b) { ++checks; if(!b) throw std::runtime_error("check failed "+std::to_string(checks)); };
    for(uint64_t q=5;q<=32;++q) {
        auto p=packing_geometry(128,q);check(valid_geometry(p));check(p.k==128);
        std::vector<int> seen(q);
        for(auto x:p.pieces) for(uint64_t i=0;i<x.columns;++i) ++seen.at(x.column_begin+i);
        for(auto x:seen) check(x==1);
        auto bad=p;bad.pieces[0].column_begin=1;check(!valid_geometry(bad));
    }
    for(auto q:{0ULL,4ULL,33ULL,~0ULL}) {
        bool threw=false;try{packing_geometry(128,q);}catch(const std::invalid_argument&){threw=true;}check(threw);
    }
    bool threw=false;try{packing_geometry(~0ULL,32);}catch(const std::invalid_argument&){threw=true;}check(threw);
    auto r=request();PackingRegistry registry;
    check(packing_admission(r,registry).reason==Reason::no_qualification);
    auto invalid=qualification(r);invalid.level=static_cast<EvidenceLevel>(999);
    threw=false;try{registry.add(invalid);}catch(const std::invalid_argument&){threw=true;}check(threw);
    registry.add(qualification(r));
    check(packing_admission(r,registry).reason==Reason::evidence_too_weak);
    r.allow_empirical=true;
    check(packing_admission(r,registry).action==Admission::optimized);
    auto bad=r;bad.selected_grouped.reduction="different-warp-tree";
    check(packing_admission(bad,registry).reason==Reason::reduction_mismatch);
    bad=r;bad.selected_grouped.dispatch="";check(packing_admission(bad,registry).reason==Reason::reduction_unknown);
    bad=r;bad.input.contiguous=false;check(packing_admission(bad,registry).reason==Reason::unsupported_layout);
    bad=r;bad.input.all_gpu=false;check(packing_admission(bad,registry).reason==Reason::unsupported_device);
    bad=r;bad.input.columns=64;check(packing_admission(bad,registry).action!=Admission::optimized);
    bad=r;bad.state.clean=false;check(packing_admission(bad,registry).action==Admission::reject);
    bad=r;bad.state.deployment.reference="another";check(packing_admission(bad,registry).action==Admission::reject);
    bad=r;bad.prefix={PrefixStatus::unsupported_state,{}};check(packing_admission(bad,registry).reason==Reason::unsupported_prefix);
    bad=r;bad.prefix.extents.pop_back();check(packing_admission(bad,registry).action==Admission::reject);
    bad=r;bad.prefix.extents[0]=0;check(packing_admission(bad,registry).action==Admission::reject);
    bad=r;bad.deployment={};check(packing_admission(bad,registry).action==Admission::reject);
    auto empty=r;empty.input.columns=0;empty.prefix={};check(packing_admission(empty,registry).action==Admission::empty);
    int runs=0,scalars=0;
    auto live=r.state;
    auto optimized=[&](const PackingPlan&p){++runs;return valid_geometry(p);};
    auto scalar=[&](){++scalars;return true;};
    auto result=execute_operator(r,registry,live,optimized,scalar,[]{return true;});
    check(result.success&&result.optimized&&live.clean&&runs==1&&scalars==0);
    check(!execute_operator(r,registry,live,optimized,scalar,[]{return true;}).success);check(runs==1);
    live=r.state;result=execute_operator(r,registry,live,optimized,scalar,[]{return false;});
    check(!result.success&&!live.clean);
    live=r.state;threw=false;
    try{execute_operator(r,registry,live,[](auto&)->bool{throw std::runtime_error("late reject");},scalar,[]{return true;});}
    catch(const std::runtime_error&){threw=true;}check(threw&&!live.clean);
    live=r.state;bad=r;bad.allow_empirical=false;
    result=execute_operator(bad,registry,live,optimized,scalar,[]{return true;});check(result.success&&!result.optimized&&scalars==1);
    threw=false;try{packing_allowed(nullptr,nullptr);}catch(const std::runtime_error&){threw=true;}check(threw);
    PackingBinding binding{&registry,[&](const void*,const void*){return r;},{},{}};
    {PackingScope scope(binding);check(packing_allowed(nullptr,nullptr));
        bool rejected=false;std::thread t([&]{try{packing_allowed(nullptr,nullptr);}catch(const std::runtime_error&){rejected=true;}});t.join();check(rejected);
    }threw=false;try{packing_allowed(nullptr,nullptr);}catch(const std::runtime_error&){threw=true;}check(threw);
    auto unqualified=r;unqualified.allow_empirical=false;
    PackingBinding no_tile{&registry,[&](const void*,const void*){return unqualified;},{},{}};
    {PackingScope scope(no_tile);threw=false;try{packing_allowed(nullptr,nullptr);}catch(const std::runtime_error&){threw=true;}check(threw);}
    no_tile.qualified_tiled=[](const PackingRequest&){return true;};
    {PackingScope scope(no_tile);check(!packing_allowed(nullptr,nullptr));
        {PackingScope inner(binding);check(packing_allowed(nullptr,nullptr));}
        check(!packing_allowed(nullptr,nullptr));
    }
    live=r.state;
    result=execute_operator(r,registry,live,[&](const PackingPlan&){live.position++;return true;},scalar,[]{return true;});
    check(!result.success&&!live.clean);
    // Callback errors may not resurrect clean metadata on failed execution.
    live=r.state;
    result=execute_operator(r,registry,live,[&](const PackingPlan&){live.clean=true;return false;},scalar,[]{return true;});
    check(!result.success&&!live.clean);
    live=r.state;threw=false;
    try{execute_operator(r,registry,live,[&](const PackingPlan&)->bool{live.clean=true;throw std::runtime_error("late failure after metadata write");},scalar,[]{return true;});}
    catch(...){threw=true;}check(threw&&!live.clean);
    live=r.state;
    result=execute_operator(r,registry,live,optimized,scalar,[&](){live.clean=true;return false;});
    check(!result.success&&!live.clean);
    // Structural assumptions must be checked for each actual request.
    auto structural=qualification(r);structural.level=EvidenceLevel::structural_assumptions;
    structural.assumptions="test-only data-dependent premise";
    PackingRegistry structural_registry;
    threw=false;try{structural_registry.add(structural);}catch(const std::invalid_argument&){threw=true;}check(threw);
    bool premise=false;int premise_calls=0;
    structural.validate_assumptions=[&](const PackingRequest & actual){++premise_calls;return premise&&actual.input.k==128;};
    structural_registry.add(structural);
    check(packing_admission(r,structural_registry).reason==Reason::assumptions_unmet);
    premise=true;check(packing_admission(r,structural_registry).action==Admission::optimized);
    premise=false;check(packing_admission(r,structural_registry).reason==Reason::assumptions_unmet);check(premise_calls==3);
    PackingRegistry throwing_registry;structural.validate_assumptions=[](const PackingRequest&)->bool{throw std::runtime_error("premise check failed");};
    throwing_registry.add(structural);check(packing_admission(r,throwing_registry).reason==Reason::assumptions_unmet);
    DenseAppendState s{253,4,257,257,1024,256,1,true,false};
    auto ext=checked_prefix(s);check(ext==std::vector<uint32_t>({256,256,256,512}));
    s.contiguous=false;check(checked_prefix(s).empty());
    {PackingScope scope(binding);threw=false;try{checked_prefix(s);}catch(const std::runtime_error&){threw=true;}check(threw);}
    check(use_scalar_head_preference(true,true,32,true,false));
    check(!use_scalar_head_preference(true,true,33,true,false));
    std::cout<<"CPU_PROTOCOL_CHECKS="<<checks<<" GPU_EXECUTIONS=0\n";
}
