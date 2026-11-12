#pragma once
#include <cstdint>

#if defined(_WIN32)
#define HS_LB_API __declspec(dllexport)
#else
#define HS_LB_API
#endif

// Exactly one implementation object must be linked into the bound CUDA DLL.
// There is deliberately no per-TU state, no reset API and no environment arm.
struct hs_launch_budget_snapshot_v1_t {
    uint64_t abi_version;
    uint64_t family_limit;
    uint64_t inherited_charged;
    uint64_t worker_reservation;
    uint64_t admitted_attempts;
    uint64_t rejected_attempts;
    int32_t terminal_code;
    int32_t configured;
};

extern "C" {
HS_LB_API int hs_launch_budget_configure_v1(uint64_t limit, uint64_t inherited_charged,
                                           uint64_t worker_reservation, const char * epoch_tag);
HS_LB_API int hs_launch_budget_try_v1(const char * source_site);
HS_LB_API void hs_launch_budget_before_launch_v1(const char * source_site);
HS_LB_API void hs_launch_budget_deny_opaque_v1(const char * route);
HS_LB_API int hs_launch_budget_snapshot_v1(hs_launch_budget_snapshot_v1_t * output);
HS_LB_API const char * hs_launch_budget_metadata_v1();
#if defined(HS_LB_CPU_TEST_ONLY)
HS_LB_API int hs_launch_budget_test_reentry_v1();
#endif
}
