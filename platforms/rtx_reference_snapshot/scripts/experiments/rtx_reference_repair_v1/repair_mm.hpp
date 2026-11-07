#pragma once
// Candidate implementation primitive, NOT a proof of bitwise correspondence.
// Enabled only at build time, by operator class after localization. It never
// looks at task IDs, generated tokens, model output, or logits margins.
#include "ggml.h"
#include "hs_scope.h"
#include <cstring>
#ifndef HSR_MM_ROLES
#define HSR_MM_ROLES 0
#endif
namespace hs_repair_mm {
inline int weight_role(const char*n){
    if(std::strstr(n,"attn_q.weight")||std::strstr(n,"attn_k.weight")||std::strstr(n,"attn_v.weight")||std::strstr(n,"attn_qkv.weight"))return 1;
    if(std::strstr(n,"attn_output.weight"))return 2;
    if(std::strstr(n,"ffn_up.weight")||std::strstr(n,"ffn_gate.weight")||std::strstr(n,"ffn_down.weight"))return 4;
    return 0;
}
inline ggml_tensor* mul_mat(ggml_context*ctx,ggml_tensor*a,ggml_tensor*b){
    const int role=weight_role(ggml_get_name(a));
    if(!hs_scope::active || !(HSR_MM_ROLES&role) || b->ne[1]<=1)return ggml_mul_mat(ctx,a,b);
    GGML_ASSERT(a->type==GGML_TYPE_Q8_0 && b->type==GGML_TYPE_F32);
    GGML_ASSERT(a->ne[2]==1&&a->ne[3]==1&&b->ne[2]==1&&b->ne[3]==1);
    GGML_ASSERT(a->ne[0]==b->ne[0] && b->ne[1]<=4);
    // Keep one-column native matmul primitives; independent query graphs may be
    // scheduled separately. Backend selection still needs same-operand validation.
    ggml_tensor* result=nullptr;
    for(int64_t j=0;j<b->ne[1];++j){
        auto*row=ggml_view_2d(ctx,b,b->ne[0],1,b->nb[1],size_t(j)*b->nb[1]);
        auto*out=ggml_mul_mat(ctx,a,row);
        ggml_format_name(out,"hsr_mm_%s_row_%lld",ggml_get_name(a),(long long)j);
        result=result?ggml_concat(ctx,result,out,1):out;
    }
    return result;
}
}
