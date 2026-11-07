#include "../native/draft_prefill.hpp"
#include <numeric>
#include <iostream>
void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
struct OriginalInterface {
    std::vector<int> consumed,positions,widths;
    std::vector<bool> flags;
    void decode(const std::vector<int>&ids,int pos,bool all,const char*,bool last){
        need(!all,"changed output rows");positions.push_back(pos);
        widths.push_back(int(ids.size()));flags.push_back(last);
        consumed.insert(consumed.end(),ids.begin(),ids.end());
    }
    // Verbatim historical method, independently pinned in the adjacent manifest.
#include "fixtures/original_prefill.inc"
};
int main(){
    for(int n=1;n<=4096;n++)for(int caller:{1,4}){
        std::vector<int> ids(n);std::iota(ids.begin(),ids.end(),100);
        OriginalInterface c;c.prefill(ids,tpds_decisive::draft_schedule(n,caller));
        need(c.consumed==ids,"lost or duplicated prompt tokens");
        need(std::count(c.flags.begin(),c.flags.end(),true)==1&&c.flags.back(),"final output policy changed");
        int pos=0;for(std::size_t j=0;j<c.widths.size();j++){
            need(c.positions[j]==pos,"noncontiguous prompt");pos+=c.widths[j];
            need(c.widths[j]<=caller,"caller limit");
        }
        if(caller==4&&n%4==3){
            need(c.widths.size()>=2&&c.widths[c.widths.size()-2]==2&&c.widths.back()==1,"three-token tail");
        }
    }
    OriginalInterface old;bool rejected=false;
    try{old.prefill({1,2,3},{3});}catch(const std::runtime_error&){rejected=true;}
    need(rejected,"regression fixture must reproduce old rejection of width3");
    std::cout<<"8192 actual historical prefill-interface cases passed; width3 rejection reproduced\n";
}
