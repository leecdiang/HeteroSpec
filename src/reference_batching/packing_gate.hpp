#pragma once
#include "execution_contract.hpp"

namespace hs_reference_batching {
// Binding is local to the calling host thread. The host owns registry and state
// lifetimes and must prohibit reentrant mutation of the same context. GPU work
// is not thread-safe merely because this pointer is thread_local.
struct PackingBinding {
    const PackingRegistry * registry=nullptr;
    // Obtain ACTUAL dispatch and residency for this tensor pair. A cached answer
    // keyed only by dtype/shape is not a valid extractor.
    std::function<PackingRequest(const void *,const void *)> describe;
    std::function<void(const PackingDecision &)> observe;
    // Separate qualification for retaining the OLD <=4-column tiled path.
    // This is not the original scalar callback and must not inherit its label.
    std::function<bool(const PackingRequest &)> qualified_tiled;
};
#if defined(_WIN32)
# if defined(HS_CONTRACT_BUILD)
#  define HS_GATE_API __declspec(dllexport)
# else
#  define HS_GATE_API __declspec(dllimport)
# endif
#else
# define HS_GATE_API __attribute__((visibility("default")))
#endif
// One TLS owner in the native module, not a header-local TLS copy per DLL.
extern "C" HS_GATE_API const PackingBinding * hs_get_packing_binding();
extern "C" HS_GATE_API const PackingBinding * hs_exchange_packing_binding(const PackingBinding *);

class PackingScope {
    const PackingBinding * previous_;
public:
    explicit PackingScope(const PackingBinding & binding):previous_(nullptr) {
        if (!binding.registry || !binding.describe) throw std::invalid_argument("incomplete packing binding");
        previous_=hs_exchange_packing_binding(&binding);
    }
    ~PackingScope() { hs_exchange_packing_binding(previous_); }
    PackingScope(const PackingScope &)=delete;
    PackingScope & operator=(const PackingScope &)=delete;
};
inline bool packing_allowed(const void * weight,const void * activation) {
    const auto * b=hs_get_packing_binding();
    if (!b) throw std::runtime_error("missing reference packing binding");
    const auto request=b->describe(weight,activation);
    const auto decision=packing_admission(request,*b->registry);
    if (b->observe) b->observe(decision);
    if (decision.action==Admission::reject)
        throw std::runtime_error(std::string("reference contract rejects graph: ")+reason_name(decision.reason));
    if (decision.action==Admission::optimized) return true;
    if (decision.action==Admission::scalar && b->qualified_tiled && b->qualified_tiled(request)) return false;
    throw std::runtime_error("old tiled lowering is not separately qualified; restore and run original scalar");
}
// The original extractor is called after slot allocation in existing adapters.
// Rejecting here does NOT authorize scalar continuation in the same context.
inline std::vector<uint32_t> checked_prefix(const DenseAppendState & state) {
    auto p=scalar_prefix_requirements(state);
    if (hs_get_packing_binding() &&
        (p.status==PrefixStatus::unsupported_state || p.status==PrefixStatus::inconsistent_state))
        throw std::runtime_error("reference prefix rejected: abort graph and restore full checkpoint before retry");
    return p.extents;
}
} // namespace hs_reference_batching
