#pragma once
#include "ggml.h"
#include <stdexcept>
// Graph representation only. Uses unchanged ggml/Vulkan arithmetic operators.
// Inputs after the upstream permutations: Q[D,Q,H,1], K[D,K,Hkv,1], V[K,Dv,Hkv,1].
inline ggml_tensor * b570_local_attention(ggml_context *ctx, int layout,
 ggml_tensor *q, ggml_tensor *k, ggml_tensor *v, ggml_tensor *mask, float scale) {
 if(layout==0 || q->ne[1]==1) return nullptr; // exact legal upstream q1 path
 const auto nq=q->ne[1], nh=q->ne[2];
 if((layout!=1&&layout!=2)||nq!=2||q->ne[3]!=1||k->ne[3]!=1||v->ne[3]!=1||
    q->ne[0]!=k->ne[0]||k->ne[1]!=v->ne[0]||k->ne[2]!=v->ne[2]||
    nh%k->ne[2]!=0||!mask||mask->ne[0]!=k->ne[1]||mask->ne[1]<nq||
    mask->ne[2]!=1||mask->ne[3]!=1||mask->type!=GGML_TYPE_F32||
    mask->nb[1]!=mask->ne[0]*sizeof(float)) throw std::runtime_error("PR108 local attention contract");
 auto one=[&](ggml_tensor *qi,ggml_tensor *mi) {
  auto scores=ggml_mul_mat(ctx,k,qi);ggml_mul_mat_set_prec(scores,GGML_PREC_F32);
  auto probs=ggml_soft_max_ext(ctx,scores,mi,scale,0.0f);
  auto values=ggml_mul_mat(ctx,v,probs);
  values=ggml_permute(ctx,values,0,2,1,3);
  return ggml_cont_2d(ctx,values,values->ne[0]*values->ne[1],values->ne[2]*values->ne[3]);
 };
 if(layout==2){
  auto qi=ggml_view_4d(ctx,q,q->ne[0],1,nh,nq,q->nb[1],q->nb[2],q->nb[1],0);
  auto mi=ggml_view_4d(ctx,mask,mask->ne[0],1,1,nq,mask->nb[1],mask->nb[1],mask->nb[1],0);
  return one(qi,mi);
 }
 ggml_tensor *out=nullptr;
 for(int64_t j=0;j<nq;++j){
  auto qi=ggml_view_4d(ctx,q,q->ne[0],1,nh,1,q->nb[1],q->nb[2],q->nb[3],j*q->nb[1]);
  auto mi=ggml_view_4d(ctx,mask,mask->ne[0],1,1,1,mask->nb[1],mask->nb[1],mask->nb[1],j*mask->nb[1]);
  auto col=one(qi,mi);out=out?ggml_concat(ctx,out,col,1):col;
 }
 return out;
}
