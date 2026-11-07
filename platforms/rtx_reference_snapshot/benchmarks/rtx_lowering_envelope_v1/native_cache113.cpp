#include "src/llama-cparams.h"
#include "src/llama-graph.h"
#include "src/hs_scope.h"
#include <iostream>
#include <stdexcept>
#include <windows.h>
static void check(bool ok){if(!ok)throw std::runtime_error("actual graph identity/role guard failed");}
int main(){try{
    SetEnvironmentVariableA("HS_SCOPE_MASK","3");
    llm_graph_params a{},b{};a.hs_query_batch=b.hs_query_batch=true;a.hs113_layout=3;b.hs113_layout=4;
    check(!a.allow_reuse(b));b.hs113_layout=3;b.hs_query_batch=false;check(!a.allow_reuse(b));
    b.hs_query_batch=true;a.ubatch.n_tokens=1;b.ubatch.n_tokens=2;check(!a.allow_reuse(b));
    for(bool prefill:{false,true}){hs_scope::guard t("target",prefill);check(hs_scope::active);{hs_scope::guard d("draft",prefill);check(!hs_scope::active);}check(hs_scope::active);}
    check(!hs_scope::active);bool rejected=false;try{hs_scope::guard bad("invalid-role",true);}catch(...){rejected=true;}check(rejected);
    std::cout<<"{\"status\":\"PASS\",\"actual_allow_reuse_negative_cases\":3,\"native_role_phase_checks\":6,\"GPU_calls\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
