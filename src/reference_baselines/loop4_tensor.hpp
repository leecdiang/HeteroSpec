#pragma once
#include "loop4_plan.hpp"
#include "ggml.h"
#include <cstring>
namespace hs_loop4 {
static_assert(GGML_MAX_OP_PARAMS>=64,"loop4 marker needs the private final int32 slot");
inline bool marked(const ggml_tensor * t){return t && t->op==GGML_OP_MUL_MAT && t->op_params[HS_LOOP4_MARKER_SLOT]==marker;}
inline void mark(ggml_tensor * t){
    if(!t || t->op!=GGML_OP_MUL_MAT || t->op_params[HS_LOOP4_MARKER_SLOT]!=0)throw std::invalid_argument("occupied loop4 metadata slot");
    t->op_params[HS_LOOP4_MARKER_SLOT]=marker;
}
inline void require(const ggml_tensor * w,const ggml_tensor * x,const ggml_tensor * out){
    if(!w || !x || !out || !marked(out) || w->type!=GGML_TYPE_Q8_0 || x->type!=GGML_TYPE_F32 || out->type!=GGML_TYPE_F32 ||
       !ggml_is_contiguous(w) || !ggml_is_contiguous(x) || !ggml_is_contiguous(out) ||
       w->ne[2]!=1 || w->ne[3]!=1 || x->ne[2]!=1 || x->ne[3]!=1 || out->ne[2]!=1 || out->ne[3]!=1 ||
       x->ne[1]<5 || x->ne[1]>32 || w->ne[0]!=x->ne[0] || w->ne[1]!=out->ne[0] || x->ne[1]!=out->ne[1] ||
       w->ne[0]<=0 || w->ne[1]<=0 || w->ne[0]>std::numeric_limits<int>::max()-512 ||
       w->ne[1]>std::numeric_limits<int>::max()/32 || out->op_params[1]!=0)
        throw std::invalid_argument("unsupported marked backend loop4 matmul");
    const auto row_blocks=w->ne[0]/ggml_blck_size(w->type);
    // Frozen NVIDIA MMVQ uses int row/block offsets. Reserve 32 padded
    // rows (maximum warps for a 1024-thread block on the admitted warp32 path).
    if(row_blocks<=0 || w->ne[1]+32>std::numeric_limits<int>::max()/row_blocks)
        throw std::overflow_error("loop4 weight block offset overflow");
}
} // namespace hs_loop4
