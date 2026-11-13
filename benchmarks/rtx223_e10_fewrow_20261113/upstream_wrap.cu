#include "bound_few_prefix.cuh"
#include "bound_few_quantizer.cuh"
#include <cuda_runtime.h>
extern "C" void e10_reserve(unsigned,const char*);
extern "C" int e10_u_shared(){return mmq_few_nbytes_shared(GGML_TYPE_Q8_0,1,1);}
extern "C" cudaError_t e10_u_prepare(){return cudaFuncSetAttribute(mul_mat_q_few<GGML_TYPE_Q8_0,1,1>,cudaFuncAttributeMaxDynamicSharedMemorySize,e10_u_shared());}
extern "C" cudaError_t e10_u_resources(cudaFuncAttributes *a,int *blocks){
 cudaError_t r=cudaFuncGetAttributes(a,mul_mat_q_few<GGML_TYPE_Q8_0,1,1>);if(r!=cudaSuccess)return r;
 return cudaOccupancyMaxActiveBlocksPerMultiprocessor(blocks,mul_mat_q_few<GGML_TYPE_Q8_0,1,1>,128,e10_u_shared());
}
extern "C" void e10_u_quantize(const float*x,void*q,cudaStream_t stream){
 e10_reserve(1,"U_quantizer");
 quantize_mmq_few_q8_1<MMQ_Q8_1_DS_LAYOUT_D4><<<dim3(8,8,1),128,0,stream>>>(x,q,4096,4096,32768,32768,8,1);
}
extern "C" void e10_u_project(const void*w,const void*q,float*y,cudaStream_t stream){
 e10_reserve(1,"U_projection");
 mul_mat_q_few<GGML_TYPE_Q8_0,1,1><<<dim3(256,1,1),dim3(32,4,1),69632,stream>>>(
  static_cast<const char*>(w),static_cast<const int4*>(q),y,16,4096,8,4352,4096,1,17825792,32768,1,17825792,32768,true);
}
