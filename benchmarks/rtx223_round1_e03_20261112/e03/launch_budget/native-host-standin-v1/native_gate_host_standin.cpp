#include "hs_launch_budget.hpp"
#include <iostream>
int main() {
    const int code=hs_launch_budget_configure_v1(4096,0,4096,"CPU-only native-gate stand-in");
    hs_launch_budget_snapshot_v1_t state{};
    hs_launch_budget_snapshot_v1(&state);
    const bool ok=code==-6 && state.admitted_attempts==0 && state.configured==0;
    std::cout << "{\"pass\":" << (ok?"true":"false") << ",\"native_configure_result\":" << code
              << ",\"numeric_DLL_loaded\":false,\"CUDA_calls\":0,\"GPU_launches\":0,\"metadata\":"
              << hs_launch_budget_metadata_v1() << "}\n";
    return ok?0:1;
}
