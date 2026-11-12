#include "hs_launch_budget.hpp"
#include <atomic>
#include <mutex>
#include <cstdio>
#include <cstdlib>
#if defined(_WIN32)
#include <windows.h>
#endif

namespace {
enum : int { OK=1, UNARMED=-1, EXHAUSTED=-2, REENTRY=-3, LB_OPAQUE=-4,
             CONFIGURATION=-5, NATIVE_BLOCKED=-6, TERMINAL=-7 };
struct state_type {
    std::mutex configuration_lock;
    std::atomic<int> configured{0};
    std::atomic<int> terminal{0};
    std::atomic<uint64_t> limit{4096}, inherited{0}, reservation{0};
    std::atomic<uint64_t> admitted{0}, rejected{0};
};
state_type state;  // one shared definition, not header/TLS state
thread_local bool in_prelaunch = false;

int reject(int code) {
    state.rejected.fetch_add(1, std::memory_order_relaxed);
    int empty=0;
    state.terminal.compare_exchange_strong(empty, code, std::memory_order_acq_rel);
    return code;
}

[[noreturn]] void failstop(int code, const char * text) {
    std::fputs(text, stderr);
    std::fputc('\n', stderr);
    std::fflush(stderr);
#if defined(_WIN32)
    // No C++ exception crosses the GNU/MSVC DLL ABI. Only this process exits.
    TerminateProcess(GetCurrentProcess(), 0xE0330000u + static_cast<unsigned>(-code));
#endif
    std::abort();
}
}

extern "C" int hs_launch_budget_configure_v1(uint64_t limit, uint64_t inherited,
                                               uint64_t reservation, const char * epoch) {
#if !defined(HS_LB_CPU_TEST_ONLY)
    (void)limit; (void)inherited; (void)reservation; (void)epoch;
    // Source-visible launch coverage is not a proof of all physical kernels:
    // opaque runtime/library work remains unqualified. No numeric DLL is armed.
    return reject(NATIVE_BLOCKED);
#else
    std::lock_guard<std::mutex> lock(state.configuration_lock);
    if (state.configured.load() != 0 || state.terminal.load() != 0) return reject(CONFIGURATION);
    if (!epoch || !epoch[0] || limit == 0 || limit > 4096 || inherited > limit ||
        reservation > limit-inherited) return reject(CONFIGURATION);
    state.limit.store(limit); state.inherited.store(inherited); state.reservation.store(reservation);
    state.configured.store(1, std::memory_order_release);
    return OK;
#endif
}

extern "C" int hs_launch_budget_try_v1(const char * site) {
    if (in_prelaunch) return reject(REENTRY);
    struct scoped_flag {
        scoped_flag() { in_prelaunch=true; }
        ~scoped_flag() { in_prelaunch=false; }
    } guard;
    if (!site || !site[0]) return reject(CONFIGURATION);
    if (!state.configured.load(std::memory_order_acquire)) return reject(UNARMED);
    if (state.terminal.load(std::memory_order_acquire)) return reject(TERMINAL);
    uint64_t current=state.admitted.load(std::memory_order_relaxed);
    while (true) {
        const uint64_t inherited=state.inherited.load(std::memory_order_relaxed);
        const uint64_t limit=state.limit.load(std::memory_order_relaxed);
        const uint64_t reservation=state.reservation.load(std::memory_order_relaxed);
        if (current >= reservation || inherited >= limit || current >= limit-inherited)
            return reject(EXHAUSTED);
        if (state.admitted.compare_exchange_weak(current, current+1,
                                                std::memory_order_acq_rel,
                                                std::memory_order_relaxed)) return OK;
        if (state.terminal.load(std::memory_order_acquire)) return reject(TERMINAL);
    }
}

extern "C" void hs_launch_budget_before_launch_v1(const char * site) {
    const int code=hs_launch_budget_try_v1(site);
    if (code != OK) failstop(code, "HeteroSpec launch budget refused before explicit CUDA launch");
}

extern "C" int hs_launch_budget_deny_opaque_try_v1(const char * route) {
    (void)route;
    return reject(LB_OPAQUE);
}

extern "C" void hs_launch_budget_deny_opaque_v1(const char * route) {
    failstop(hs_launch_budget_deny_opaque_try_v1(route),
             "HeteroSpec narrow launch profile refuses opaque CUDA/library route before call");
}

extern "C" int hs_launch_budget_snapshot_v1(hs_launch_budget_snapshot_v1_t * out) {
    if (!out) return CONFIGURATION;
    *out = {1, state.limit.load(), state.inherited.load(), state.reservation.load(),
            state.admitted.load(), state.rejected.load(), state.terminal.load(), state.configured.load()};
    return OK;
}

extern "C" const char * hs_launch_budget_metadata_v1() {
    return "{\"abi\":1,\"native_arm\":\"BLOCKED\",\"scope\":\"one-bound-DLL-instance-all-TUs\","
           "\"reset_api\":false,\"all_physical_kernels_qualified\":false,"
           "\"CUDA_graphs\":\"DENY\",\"opaque_libraries\":\"DENY\","
           "\"runtime_hidden_work\":\"UNKNOWN_NOT_ADMITTED\"}";
}

#if defined(HS_LB_CPU_TEST_ONLY)
extern "C" int hs_launch_budget_test_reentry_v1() {
    in_prelaunch=true;
    int result=hs_launch_budget_try_v1("CPU-test-recursive-prelaunch");
    in_prelaunch=false;
    return result;
}
#endif
