#pragma once
#include "query_head.h"
// Native transaction remains k1/q<=2. q3/4 belong only to operator/CPU study.
inline ggml_tensor *b570_local_attention(ggml_context*c,int layout,ggml_tensor*q,
 ggml_tensor*k,ggml_tensor*v,ggml_tensor*m,float scale){
 if(layout==0||q->ne[1]==1)return nullptr;
 hs_qh::require(q->ne[1]==2,"native continuation remains q<=2");
 auto mode=layout==1?hs_qh::Mode::PQ:layout==3?hs_qh::Mode::QH_C:hs_qh::Mode::QH_D;
 hs_qh::require(layout==1||layout==3||layout==4,"unregistered native layout");
 auto built=hs_qh::build(c,mode,q,k,v,m,scale);
 hs_qh::require(built.out&&!built.common_original,"native q2 graph missing");return built.out;
}
