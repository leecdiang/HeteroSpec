#pragma once
#include <vector>
#include <stdexcept>
#include <algorithm>
// The caller owns the actual historical context, residency, reset sequence,
// reserve, cap admission and numerical runtime. No contexts are made here.
namespace tpds_decisive {
template<class Decode,class Observe>
void replay_path(const std::vector<int>& prompt,const std::vector<int>& suffix,
                 const std::vector<int>& producer_callers, const std::vector<bool>& producer_logits,
                 Decode decode,Observe observe) {
    if(prompt.empty() || producer_callers.empty() || producer_logits.size()!=producer_callers.size() || !producer_logits.back())throw std::invalid_argument("missing historical producer");
    std::size_t pos=0,call=0;
    for(int n:producer_callers){
        if(n<=0 || pos+std::size_t(n)>prompt.size())throw std::invalid_argument("producer geometry");
        const bool final=producer_logits[call++];
        decode(std::vector<int>(prompt.begin()+pos,prompt.begin()+pos+n),int(pos),false,"PREFILL",final);
        pos+=std::size_t(n);
    }
    if(pos!=prompt.size())throw std::invalid_argument("producer incomplete");
    observe(-1,int(pos)); // existing final prompt row only
    for(int id:suffix){
        decode(std::vector<int>{id},int(pos),false,"FORCED_CONTINUATION",true);
        ++pos;observe(-1,int(pos));
    }
}
}
