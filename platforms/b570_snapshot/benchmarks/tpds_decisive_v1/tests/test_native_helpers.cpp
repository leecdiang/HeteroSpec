#include "../native/draft_prefill.hpp"
#include "../native/replay_path.hpp"
#include <numeric>
#include <iostream>
int main(){
    std::size_t checks=0;
    for(std::size_t n=1;n<=4096;n++)for(int c:{1,4}){
        auto v=tpds_decisive::draft_schedule(n,c);
        if(std::accumulate(v.begin(),v.end(),0)!=int(n))return 1;
        for(int w:v)if(w<1||w>c)return 2;
        checks++;
    }
    for(int c:{0,2,3,5}){bool rejected=false;try{tpds_decisive::draft_schedule(8,c);}catch(const std::invalid_argument&){rejected=true;}if(!rejected)return 3;checks++;}
    std::vector<std::vector<int>> calls;std::vector<bool> flags;std::vector<int> positions;
    auto decode=[&](std::vector<int>x,int p,bool all,const char*,bool last){if(all)throw std::runtime_error("all outputs changed");calls.push_back(x);flags.push_back(last);positions.push_back(p);};
    int observed=0;auto obs=[&](int row,int){if(row!=-1)throw std::runtime_error("extra row");observed++;};
    tpds_decisive::replay_path(std::vector<int>{1,2,3},std::vector<int>{4,5},std::vector<int>{3},std::vector<bool>{true},decode,obs);
    if(calls.size()!=3||calls[0].size()!=3||observed!=3||positions!=std::vector<int>({0,3,4}))return 4;
    checks++;
    calls.clear();flags.clear();positions.clear();
    tpds_decisive::replay_path(std::vector<int>{1,2,3},std::vector<int>{},std::vector<int>{1,1,1},std::vector<bool>{false,false,true},decode,obs);
    if(flags!=std::vector<bool>({false,false,true}))return 5;
    checks++;
    calls.clear();flags.clear();positions.clear();
    tpds_decisive::replay_path(std::vector<int>{1,2,3},std::vector<int>{},std::vector<int>{1,1,1},std::vector<bool>{true,true,true},decode,obs);
    if(flags!=std::vector<bool>({true,true,true}))return 6;
    checks++;
    std::cout<<checks<<" standalone CPU schedule/replay checks; no llama library or model execution\n";
}
