#pragma once
#include <stdint.h>
#include <stddef.h>
// Fixed-layout observation ABI. No pointer here identifies model/reference
// equivalence; source/build pins and the qualification artifact remain external.
#define HS_CUDA_AUDIT_ABI 1u
struct hs_cuda_tensor_record {
    int32_t type;
    int64_t ne[4];
    uint64_t nb[4];
    uint8_t allocated, same_device_buffer, host_buffer, reserved;
};
struct hs_cuda_dispatch_record {
    uint32_t abi;
    uint32_t phase; // 1 selected route; 2 actual MMVQ specialization launch
    int32_t device, cc, warp;
    const char * route;
    const char * source_digest;
    hs_cuda_tensor_record tensors[3]; // actual post-packing weight/input/output
    int32_t type, columns, small_k, halve_iters, fusion, ids;
    uint32_t grid[3], block[3], shared_bytes;
    uint32_t argument_count;
    uint64_t arguments[24]; // actual MMVQ derived strides/ratios, documented in staging script
};
struct hs_cuda_audit_binding {
    uint32_t abi;
    uint32_t mode; // 1 collect-only; 2 enforce (currently always fail closed)
    void * user;
    void (*record)(void *,const hs_cuda_dispatch_record *);
};
// Discover through ggml backend registry, not a link-time CUDA dependency.
typedef const hs_cuda_audit_binding * (*hs_cuda_exchange_audit_fn)(const hs_cuda_audit_binding *);
