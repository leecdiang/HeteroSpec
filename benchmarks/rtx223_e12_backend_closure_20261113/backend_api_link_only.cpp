// Compile/link evidence only. Never load this DLL: its imports are numerical DLLs.
// This contains no backend invocation, graph execution, CUDA call, or executable entry.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cuda.h"

extern "C" __declspec(dllexport) const void * hs_e12_linked_api(unsigned index) {
    switch (index) {
        case 0: return reinterpret_cast<const void *>(&ggml_backend_cuda_init);
        case 1: return reinterpret_cast<const void *>(&ggml_init);
        case 2: return reinterpret_cast<const void *>(&ggml_new_tensor_2d);
        case 3: return reinterpret_cast<const void *>(&ggml_mul_mat);
        case 4: return reinterpret_cast<const void *>(&ggml_new_graph);
        case 5: return reinterpret_cast<const void *>(&ggml_build_forward_expand);
        case 6: return reinterpret_cast<const void *>(&ggml_backend_alloc_ctx_tensors);
        case 7: return reinterpret_cast<const void *>(&ggml_backend_buffer_set_usage);
        case 8: return reinterpret_cast<const void *>(&ggml_backend_tensor_set);
        case 9: return reinterpret_cast<const void *>(&ggml_backend_graph_compute);
        case 10: return reinterpret_cast<const void *>(&ggml_backend_synchronize);
        case 11: return reinterpret_cast<const void *>(&ggml_backend_tensor_get);
        case 12: return reinterpret_cast<const void *>(&ggml_backend_buffer_free);
        case 13: return reinterpret_cast<const void *>(&ggml_backend_free);
        case 14: return reinterpret_cast<const void *>(&ggml_free);
        default: return nullptr;
    }
}
