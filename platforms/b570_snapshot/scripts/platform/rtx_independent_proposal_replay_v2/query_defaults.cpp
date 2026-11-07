// Scalar C API defaults only. No model load or inference.
#include "llama.h"
#include "json.hpp"
#include <windows.h>
#include <iostream>
int main(int argc,char **argv){
    if(argc!=2)return 2;SetDllDirectoryA(argv[1]);auto dll=LoadLibraryA((std::string(argv[1])+"/llama.dll").c_str());if(!dll)return 3;
    auto fc=(decltype(&llama_context_default_params))GetProcAddress(dll,"llama_context_default_params");auto fm=(decltype(&llama_model_default_params))GetProcAddress(dll,"llama_model_default_params");if(!fc||!fm)return 4;
    auto c=fc();auto m=fm();nlohmann::ordered_json context,model;
#define C(N) context[#N]=c.N;
    C(n_ctx) C(n_batch) C(n_ubatch) C(n_seq_max) C(n_rs_seq) C(n_outputs_max) C(n_outputs_max_per_seq) C(n_threads) C(n_threads_batch)
    C(ctx_type) C(rope_scaling_type) C(pooling_type) C(attention_type) C(flash_attn_type)
    C(rope_freq_base) C(rope_freq_scale) C(yarn_ext_factor) C(yarn_attn_factor) C(yarn_beta_fast) C(yarn_beta_slow) C(yarn_orig_ctx) C(defrag_thold)
    C(type_k) C(type_v) C(embeddings) C(offload_kqv) C(no_perf) C(op_offload) C(swa_full) C(kv_unified) C(n_samplers)
    context["cb_eval_is_null"]=c.cb_eval==nullptr;context["abort_callback_is_null"]=c.abort_callback==nullptr;context["ctx_other_is_null"]=c.ctx_other==nullptr;context["samplers_is_null"]=c.samplers==nullptr;
#define M(N) model[#N]=m.N;
    M(n_gpu_layers) M(split_mode) M(load_mode) M(lazy_mode) M(main_gpu) M(vocab_only) M(check_tensors) M(use_extra_bufts) M(no_host) M(no_alloc) M(load_mtp)
    model["devices_is_null"]=m.devices==nullptr;model["tensor_split_is_null"]=m.tensor_split==nullptr;model["tensor_overrides_is_null"]=m.tensor_buft_overrides==nullptr;model["kv_overrides_is_null"]=m.kv_overrides==nullptr;
    std::cout<<nlohmann::ordered_json({{"context_defaults",context},{"model_defaults",model},{"forward_calls",0}}).dump()<<std::endl;return 0;
}
