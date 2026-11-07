// Uses actual frozen actor headers. No actor/model/backend is initialized.
#include "src/llama-cparams.h"
#include "src/llama-graph.h"
#include "src/hs_scope.h"
#include <iostream>
#include <stdexcept>
#include <windows.h>
static void require(bool b){if(!b)throw std::runtime_error("actual actor contract rejected");}
int main(int argc,char**argv){try{
    require(argc==2);_putenv((std::string("HS_SCOPE_MASK=")+argv[1]).c_str());
    require(hs_scope::mask()==3); // This test is specifically the RTX target mask3 contract.
    for(bool prefill:{false,true}){
        hs_scope::guard target("target",prefill);require(hs_scope::active);
        {hs_scope::guard draft("draft",prefill);require(!hs_scope::active);}
        require(hs_scope::active);
    }
    require(!hs_scope::active);bool bad=false;
    try{hs_scope::guard invalid("invalid",true);}catch(...){bad=true;}require(bad);
    llm_graph_params a{},b{};a.hs_query_batch=b.hs_query_batch=true;
    for(int x:{0,1,3,4})for(int y:{0,1,3,4})if(x!=y){a.hs113_layout=x;b.hs113_layout=y;require(!a.allow_reuse(b));}
    a.hs113_layout=b.hs113_layout=3;b.hs_query_batch=false;require(!a.allow_reuse(b));
    std::cout<<"{\"status\":\"PASS\",\"cache_layout_rejections\":12,\"inactive_cache_rejection\":true,\"target_phase_mask\":3,\"GPU_calls\":0}\n";
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
