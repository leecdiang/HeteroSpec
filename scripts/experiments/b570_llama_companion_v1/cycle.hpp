#pragma once
#include <vector>
#include <stdexcept>
namespace hs_cycle {
struct Result { std::vector<int> emitted; int accepted=0; bool stopped=false; bool bonus=false; };
template<class Eog>
Result select(const std::vector<int>& proposals, const std::vector<int>& decisions,
              int remaining, Eog eog) {
    if(proposals.empty() || decisions.size()!=proposals.size()+1 || remaining<=0)
        throw std::invalid_argument("verification cycle geometry");
    Result r;
    auto emit=[&](int t){r.emitted.push_back(t); r.stopped=eog(t)||int(r.emitted.size())==remaining;};
    for(size_t j=0;j<proposals.size();++j){
        const bool accepted=proposals[j]==decisions[j];
        if(accepted) ++r.accepted;
        emit(decisions[j]);
        if(r.stopped || !accepted) return r;
    }
    r.bonus=true; emit(decisions.back()); return r;
}
}
