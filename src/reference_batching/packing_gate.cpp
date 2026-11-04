#ifndef HS_CONTRACT_BUILD
#define HS_CONTRACT_BUILD
#endif
#include "packing_gate.hpp"
namespace hs_reference_batching {
namespace { thread_local const PackingBinding * binding=nullptr; }
extern "C" HS_GATE_API const PackingBinding * hs_get_packing_binding() { return binding; }
extern "C" HS_GATE_API const PackingBinding * hs_exchange_packing_binding(const PackingBinding * value) {
    const auto * previous=binding;binding=value;return previous;
}
}
