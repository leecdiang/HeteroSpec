#include "arm_spec.h"
#include <iostream>
#include <set>
#include <stdexcept>
using namespace rtx_scope_transfer;
static void check(bool ok){if(!ok)throw std::runtime_error("arm contract failure");}
int main(){
    std::set<std::string> keys;
    for(const std::string family:{"Qwen","SmolLM2","Llama"}){
        auto r=arm_spec("R");
        check(!r.scoped && !r.draft && r.target_ub==1 && r.k==0 && r.selector==1);
        keys.insert(pool_key(family,r));
        for(const std::string scope:{"GS","PQ","QB"}){
            auto m=arm_spec("M_"+scope),c=arm_spec("C_"+scope);
            check(m.scoped && c.scoped && !m.draft && c.draft && m.k==0 && c.k==3);
            check(m.target_ub==4 && c.target_ub==4 && m.selector==c.selector);
            check(m.selector==(scope=="GS"?2:scope=="PQ"?1:0));
            check(pool_key(family,m)==pool_key(family,c));
            keys.insert(pool_key(family,m));
        }
    }
    check(keys.size()==12);
    for(const std::string name:{"","GS","PQ","QB","C1","M_X","C_GS/../R"}){
        bool rejected=false;try{arm_spec(name);}catch(const std::invalid_argument&){rejected=true;}check(rejected);
    }
    check(source_variant("Qwen")=="original" && source_variant("SmolLM2")=="metadata4" && source_variant("Llama")=="metadata4");
    bool rejected=false;try{pool_key("unknown",arm_spec("R"));}catch(const std::invalid_argument&){rejected=true;}check(rejected);
    std::cout<<"PASS: seven arms, all family pools, source routing, unknown labels rejected; no model execution\n";
}
