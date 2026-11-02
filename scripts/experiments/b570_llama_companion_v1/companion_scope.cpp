#include "companion_scope.hpp"
#include "llama-context.h"
#include <stdexcept>
namespace hs_b570 { thread_local int mode = 0; }
extern "C" void hs_b570_set_layout(int mode) {
    if (mode < 0 || mode > 2) throw std::invalid_argument("layout policy");
    hs_b570::mode = mode;
}
extern "C" const char * hs_b570_tensor_backend(llama_context *ctx, ggml_tensor *tensor) {
    auto *backend = ctx ? ggml_backend_sched_get_tensor_backend(ctx->get_sched(), tensor) : nullptr;
    return backend ? ggml_backend_name(backend) : nullptr;
}
