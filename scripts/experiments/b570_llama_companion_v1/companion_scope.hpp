#pragma once
#include "llama.h"
#include "ggml-backend.h"
// Implemented inside llama, not an executable-local duplicate of a DLL variable.
extern "C" LLAMA_API void hs_b570_set_layout(int mode);
extern "C" LLAMA_API void hs_b570_set_reference_q8(bool enabled);
extern "C" LLAMA_API const char * hs_b570_tensor_backend(llama_context *, ggml_tensor *);
namespace hs_b570 { extern thread_local int mode; extern thread_local bool reference_q8; }
