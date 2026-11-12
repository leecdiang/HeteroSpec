#include "work_counts.h"
#include <cuda_runtime.h>
#include <atomic>
#include <vector>
#include <stdexcept>
static std::atomic<int> selected_arm{0};
extern "C" int hs_strong_selected_arm() { return selected_arm.load(); }
extern "C" bool hs_strong_select_arm_once(int arm) {
    if (arm<1 || arm>3) return false;
    int expected=0;
    return selected_arm.compare_exchange_strong(expected,arm);
}
static thread_local hs_work_counts counts{};
static thread_local bool active = false;
struct QuantPayload { uint64_t rows;std::vector<unsigned char> bytes; };
static thread_local bool capture_quant=false;
static thread_local std::vector<QuantPayload> quant_payloads;
extern "C" void hs_quant_capture_reset(bool enabled) { capture_quant=enabled;quant_payloads.clear(); }
extern "C" uint64_t hs_quant_capture_count() { return quant_payloads.size(); }
extern "C" const unsigned char* hs_quant_capture_data(uint64_t i,uint64_t* rows,uint64_t* bytes) {
    const auto& v=quant_payloads.at(i);*rows=v.rows;*bytes=v.bytes.size();return v.bytes.data();
}
extern "C" void hs_work_quant_payload(const void* data,uint64_t rows,uint64_t bytes,void* stream) {
    if (!capture_quant) return;
    QuantPayload p{rows,std::vector<unsigned char>(bytes)};
    if (cudaMemcpyAsync(p.bytes.data(),data,bytes,cudaMemcpyDeviceToHost,static_cast<cudaStream_t>(stream))!=cudaSuccess ||
        cudaStreamSynchronize(static_cast<cudaStream_t>(stream))!=cudaSuccess)
        throw std::runtime_error("Quantized activation audit copy failed");
    quant_payloads.push_back(std::move(p));
}
extern "C" void hs_work_reset() { counts = {}; active = true; }
extern "C" hs_work_counts hs_work_finish() { active = false; return counts; }
extern "C" void hs_work_quant(uint64_t r, uint64_t b) { if (active) { ++counts.quant_calls; counts.quant_rows += r; counts.quant_bytes += b; } }
extern "C" void hs_work_dot(uint64_t c) { if (active) { ++counts.scalar_dot_dispatches; counts.scalar_dot_columns += c; } }
extern "C" void hs_work_backend() { if (active) { ++counts.backend_loop_entries; } }
extern "C" cudaError_t __real_cudaLaunchKernel(const void *, dim3, dim3, void **, size_t, cudaStream_t);
extern "C" cudaError_t __wrap_cudaLaunchKernel(const void * f, dim3 g, dim3 b, void ** a, size_t n, cudaStream_t s) {
    if (active) ++counts.kernel_calls;
    return __real_cudaLaunchKernel(f,g,b,a,n,s);
}
extern "C" cudaError_t __real_cudaLaunchKernelExC(const cudaLaunchConfig_t *, const void *, void **);
extern "C" cudaError_t __wrap_cudaLaunchKernelExC(const cudaLaunchConfig_t * c, const void * f, void ** a) {
    if (active) ++counts.kernel_calls;
    return __real_cudaLaunchKernelExC(c,f,a);
}
extern "C" cudaError_t __real_cudaMemcpyAsync(void *,const void *,size_t,cudaMemcpyKind,cudaStream_t);
extern "C" cudaError_t __wrap_cudaMemcpyAsync(void * d,const void * s,size_t n,cudaMemcpyKind k,cudaStream_t t) {
    if (active) { ++counts.copy_calls; counts.copy_bytes += n; }
    return __real_cudaMemcpyAsync(d,s,n,k,t);
}
extern "C" cudaError_t __real_cudaMemcpy(void *,const void *,size_t,cudaMemcpyKind);
extern "C" cudaError_t __wrap_cudaMemcpy(void * d,const void * s,size_t n,cudaMemcpyKind k) {
    if (active) { ++counts.copy_calls; counts.copy_bytes += n; }
    return __real_cudaMemcpy(d,s,n,k);
}
extern "C" cudaError_t __real_cudaMemcpy2DAsync(void *,size_t,const void *,size_t,size_t,size_t,cudaMemcpyKind,cudaStream_t);
extern "C" cudaError_t __wrap_cudaMemcpy2DAsync(void * d,size_t dp,const void * s,size_t sp,size_t w,size_t h,cudaMemcpyKind k,cudaStream_t t) {
    if (active) { ++counts.copy_calls; counts.copy_bytes += w*h; }
    return __real_cudaMemcpy2DAsync(d,dp,s,sp,w,h,k,t);
}
extern "C" cudaError_t __real_cudaMalloc(void **,size_t);
extern "C" cudaError_t __wrap_cudaMalloc(void ** p,size_t n) {
    if (active) { ++counts.alloc_calls; counts.alloc_bytes += n; }
    return __real_cudaMalloc(p,n);
}
extern "C" cudaError_t __real_cudaMallocAsync(void **,size_t,cudaStream_t);
extern "C" cudaError_t __wrap_cudaMallocAsync(void ** p,size_t n,cudaStream_t t) {
    if (active) { ++counts.alloc_calls; counts.alloc_bytes += n; }
    return __real_cudaMallocAsync(p,n,t);
}
extern "C" cudaError_t __real_cudaStreamSynchronize(cudaStream_t);
extern "C" cudaError_t __wrap_cudaStreamSynchronize(cudaStream_t t) {
    if (active) ++counts.sync_calls;
    return __real_cudaStreamSynchronize(t);
}
extern "C" cudaError_t __real_cudaDeviceSynchronize();
extern "C" cudaError_t __wrap_cudaDeviceSynchronize() {
    if (active) ++counts.sync_calls;
    return __real_cudaDeviceSynchronize();
}
