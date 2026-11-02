#include "companion_scope.hpp"
#include "llama-context.h"
#include <stdexcept>
namespace hs_b570 { thread_local int mode = 0; thread_local bool reference_q8 = false; thread_local bool prefix_extent = false; }
extern "C" void hs_b570_set_reference_q8(bool enabled) { hs_b570::reference_q8 = enabled; }
extern "C" void hs_b570_set_prefix_extent(bool enabled) { hs_b570::prefix_extent = enabled; }
extern "C" void hs_b570_set_layout(int mode) {
    if (mode < 0 || mode > 2) throw std::invalid_argument("layout policy");
    hs_b570::mode = mode;
}
extern "C" const char * hs_b570_tensor_backend(llama_context *ctx, ggml_tensor *tensor) {
    auto *backend = ctx ? ggml_backend_sched_get_tensor_backend(ctx->get_sched(), tensor) : nullptr;
    return backend ? ggml_backend_name(backend) : nullptr;
}
