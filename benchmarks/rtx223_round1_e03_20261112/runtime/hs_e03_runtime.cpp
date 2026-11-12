#include "hs_e03_runtime.hpp"
#include <atomic>
#include <stdexcept>

static std::atomic<int> selected{-1};
static std::atomic<std::uint64_t> routes[3]{};
extern "C" __declspec(dllexport) const char * hs_e03_runtime_metadata() {
    return "{\"schema\":\"heterospec.e03.cuda-runtime.v1\",\"abi\":1,\"arm_api\":{\"A\":0,\"B\":1,\"C\":2},"
           "\"C_domain\":\"Q8_0/F32,packed[K,4,2],q8,g2,K%512=0,evenM,noIDs,noFusion\","
           "\"C_kernel\":\"sameCTA_two_independent_case4_accumulators_weight_fragment_reuse\","
           "\"A_core_required\":\"loop4\",\"B_C_core_required\":\"packed\","
           "\"outside_C_domain\":\"existing_packed_route_not_newly_qualified\","
           "\"graph_policy\":\"disabled_all_arms\",\"numerical_qualification\":\"NOT_RUN\","
           "\"metadata_function_calls_CUDA\":false,\"full_physical_launch_budget\":\"NOT_QUALIFIED\"}";
}
extern "C" __declspec(dllexport) int hs_e03_select_arm(int arm) {
    if(arm<0||arm>2)return 2;
    int expected=-1;
    if(selected.compare_exchange_strong(expected,arm))return 0;
    return expected==arm?0:3;
}
extern "C" __declspec(dllexport) int hs_e03_selected_arm() {return selected.load();}
extern "C" __declspec(dllexport) std::uint64_t hs_e03_pair4_dispatches(){return routes[2].load();}
extern "C" __declspec(dllexport) std::uint64_t hs_e03_packed_dispatches(){return routes[1].load();}
extern "C" __declspec(dllexport) std::uint64_t hs_e03_loop4_dispatches(){return routes[0].load();}
void hs_e03_note_dispatch(int route) {
    if(selected.load()<0||route<0||route>2)throw std::runtime_error("e03 runtime arm not configured");
    ++routes[route];
}
