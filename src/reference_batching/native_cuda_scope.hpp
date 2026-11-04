#pragma once
#include "cuda_audit.h"
#include "ggml-backend.h"
#include <stdexcept>
namespace hs_reference_batching {
// Uses the CUDA backend module's own storage. Missing instrumentation refuses
// an explicitly requested CUDA scope, never silently pretends to install it.
class NativeCudaAuditScope {
    hs_cuda_exchange_audit_fn exchange_=nullptr;
    const hs_cuda_audit_binding * previous_=nullptr;
    hs_cuda_audit_binding enforcement_{HS_CUDA_AUDIT_ABI,2,nullptr,nullptr};
public:
    explicit NativeCudaAuditScope(bool require_cuda=false,const hs_cuda_audit_binding * collect=nullptr) {
        auto registry=ggml_backend_reg_by_name("CUDA");
        if(!registry){if(require_cuda)throw std::runtime_error("CUDA backend unavailable");return;}
        exchange_=reinterpret_cast<hs_cuda_exchange_audit_fn>(ggml_backend_reg_get_proc_address(registry,"hs_cuda_exchange_audit_v1"));
        if(!exchange_)throw std::runtime_error("CUDA dispatch instrumentation unavailable");
        if(collect && (collect->abi!=HS_CUDA_AUDIT_ABI || collect->mode!=1 || !collect->record))
            throw std::invalid_argument("invalid collect-only CUDA audit binding");
        previous_=exchange_(collect ? collect : &enforcement_);
        if(previous_){exchange_(previous_);exchange_=nullptr;throw std::runtime_error("nested CUDA audit unsupported");}
    }
    ~NativeCudaAuditScope(){if(exchange_)exchange_(previous_);}
    NativeCudaAuditScope(const NativeCudaAuditScope &)=delete;
    NativeCudaAuditScope & operator=(const NativeCudaAuditScope &)=delete;
};
} // namespace hs_reference_batching
