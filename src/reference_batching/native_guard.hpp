#pragma once
#include "packing_gate.hpp"
#include "llama.h"
#include "native_cuda_scope.hpp"
namespace hs_reference_batching {
// Implemented inside the staged runtime: avoids host/DLL copies of hs_scope.
extern "C" HS_GATE_API bool hs_exchange_runtime_scope(bool);
extern "C" HS_GATE_API bool hs_native_decode_supported(llama_context *,llama_batch) noexcept;
struct NativeScope {
    bool previous;
    explicit NativeScope(bool enabled):previous(hs_exchange_runtime_scope(enabled)){}
    ~NativeScope(){hs_exchange_runtime_scope(previous);}
    NativeScope(const NativeScope &)=delete;
    NativeScope & operator=(const NativeScope &)=delete;
};
// Install only for the synchronous decode; unwind BEFORE owner reconstructs
// the clean checkpoint. The host must still supply actual dispatch evidence.
inline int guarded_decode(llama_context * context,llama_batch batch,const PackingBinding & binding){
    if(!hs_native_decode_supported(context,batch))throw std::runtime_error("unsupported native reference scope");
    NativeCudaAuditScope cuda_enforcement;
    PackingScope bound(binding);NativeScope scope(true);
    return llama_decode(context,batch);
}
} // namespace hs_reference_batching
