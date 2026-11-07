// Synthetic CPU arithmetic only. Explicitly loads ggml-cpu, never a model or Vulkan backend.
#define NOMINMAX
#include <windows.h>
#include "local_attention.h"
#include <cmath>
#include <iostream>
#include <algorithm>
using Compute=int(*)(ggml_context*,ggml_cgraph*,int);
int main(){
 if(GetModuleHandleW(L"vulkan-1.dll")||GetModuleHandleW(L"ggml-vulkan.dll"))return 30;
 auto lib=LoadLibraryW(L"ggml-cpu.dll");if(!lib)return 31;auto compute=(Compute)GetProcAddress(lib,"ggml_graph_compute_with_ctx");if(!compute)return 32;
 int checks=0;double worst=0;
 for(int heads:{8,32})for(int kvheads:{1,8}){
  ggml_init_params p{64*1024*1024,nullptr,false};auto*c=ggml_init(p);
  auto*raw=ggml_new_tensor_3d(c,GGML_TYPE_F32,128,heads,2);auto*q=ggml_permute(c,raw,0,2,1,3);
  auto*k=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,256,kvheads,1);auto*v=ggml_new_tensor_4d(c,GGML_TYPE_F16,256,128,kvheads,1);auto*m=ggml_new_tensor_4d(c,GGML_TYPE_F32,256,32,1,1);
  for(int64_t i=0;i<ggml_nelements(raw);++i)((float*)raw->data)[i]=float((i*7)%37-18)/37;
  for(int64_t i=0;i<ggml_nelements(k);++i)((ggml_fp16_t*)k->data)[i]=ggml_fp32_to_fp16(float((i*11)%43-21)/43);
  for(int64_t i=0;i<ggml_nelements(v);++i)((ggml_fp16_t*)v->data)[i]=ggml_fp32_to_fp16(float((i*13)%47-23)/47);
  for(int j=0;j<32;++j)for(int i=0;i<256;++i)((float*)m->data)[j*256+i]=i<(119+j)?0.0f:-INFINITY;
  auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);auto*probs=ggml_soft_max_ext(c,s,m,.125f,0.0f);auto*mq=ggml_mul_mat(c,v,probs);mq=ggml_permute(c,mq,0,2,1,3);mq=ggml_cont_2d(c,mq,128*heads,2);
  auto*pq=b570_local_attention(c,1,q,k,v,m,.125f);auto*qb=b570_local_attention(c,2,q,k,v,m,.125f);auto*g=ggml_new_graph(c);ggml_build_forward_expand(g,mq);ggml_build_forward_expand(g,pq);ggml_build_forward_expand(g,qb);
  if(compute(c,g,1)!=0)return 33;
  for(auto*other:{pq,qb})for(int64_t i=0;i<ggml_nelements(mq);++i){double error=std::abs(double(((float*)mq->data)[i])-((float*)other->data)[i]);if(!std::isfinite(error)||error>1e-5)return 34;worst=std::max(worst,error);++checks;}
  ggml_free(c);
 }
 if(GetModuleHandleW(L"vulkan-1.dll")||GetModuleHandleW(L"ggml-vulkan.dll"))return 35;
 std::cout<<"PASS SYNTHETIC_CPU_ONLY elements="<<checks<<" max_abs_error="<<worst<<" model/GPU forwards=0\n";
 FreeLibrary(lib);return 0;
}
