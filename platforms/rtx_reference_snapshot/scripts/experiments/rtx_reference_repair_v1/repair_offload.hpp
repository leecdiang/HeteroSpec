#pragma once
#include <cstring>
// Included after the backend API and hs_scope definitions. Preserve the native
// single-token offload predicate for head-wise normalization scaling. The tensor
// and numerical operations are unchanged; only the scheduler's preference query
// sees a one-token shape. R and inactive draft graphs retain the original query.
namespace hs_repair_offload {
template<class Backend, class Tensor>
inline bool offload_op(Backend backend, const Tensor * tensor) {
    const bool head_scale = std::strncmp(tensor->name,"Kcur_normed-",12)==0 ||
                            std::strncmp(tensor->name,"Qcur_normed-",12)==0;
    if (hs_scope::active && tensor->op==GGML_OP_MUL && head_scale &&
        tensor->ne[2]>1 && tensor->ne[2]<=4 && tensor->ne[3]==1) {
        auto single = *tensor;
        single.ne[2] = 1;
        return ggml_backend_offload_op(backend, &single);
    }
    return ggml_backend_offload_op(backend, tensor);
}
}
