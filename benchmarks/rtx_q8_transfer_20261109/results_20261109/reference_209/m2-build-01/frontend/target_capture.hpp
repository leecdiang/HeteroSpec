#pragma once
// Diagnostic only. Read already requested logits; do not alter output masks,
// reserve sizes, model state, arithmetic, graph scheduling or lifecycle.
#include "llama.h"
#include <filesystem>
#include <fstream>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <cstdint>
#include <limits>
namespace tpds_decisive {
inline void capture_write_new(const std::filesystem::path& p,const void* data,std::size_t n) {
    if(n==0 || std::filesystem::exists(p))throw std::runtime_error("capture path/length");
    std::ofstream f(p,std::ios::binary|std::ios::out);
    f.write(static_cast<const char*>(data),std::streamsize(n));f.flush();
    if(!f)throw std::runtime_error("capture write failed");
}
inline void capture_existing(llama_context* ctx,llama_model* model,
                             const std::filesystem::path& dir,int frontier_row,const float* supplied=nullptr) {
    static_assert(sizeof(float)==4 && std::numeric_limits<float>::is_iec559,"binary32 required");
    const std::uint16_t one=1;
    if(*reinterpret_cast<const unsigned char*>(&one)!=1)throw std::runtime_error("little endian required");
    if(!ctx||!model||std::filesystem::exists(dir))throw std::runtime_error("capture scope/path");
    llama_synchronize(ctx);
    const int n=llama_vocab_n_tokens(llama_model_get_vocab(model));
    const float* p=supplied?supplied:llama_get_logits_ith(ctx,frontier_row);
    if(!p || n<=0)throw std::runtime_error("requested frontier unavailable; do not change reserve to hide it");
    std::vector<float> logits(p,p+n);
    for(float x:logits)if(!std::isfinite(x))throw std::runtime_error("nonfinite frontier");
    const auto bytes=llama_state_seq_get_size(ctx,0);
    if(bytes==0)throw std::runtime_error("empty native state");
    std::vector<std::uint8_t> state(bytes);
    if(llama_state_seq_get_data(ctx,state.data(),state.size(),0)!=bytes)
        throw std::runtime_error("native sequence export incomplete");
    std::filesystem::create_directories(dir);
    capture_write_new(dir/"frontier.f32",logits.data(),logits.size()*sizeof(float));
    capture_write_new(dir/"sequence.bin",state.data(),state.size());
    std::ofstream meta(dir/"capture.txt");
    meta<<"frontier_row="<<frontier_row<<"\nvocab="<<n<<"\nsequence_bytes="<<bytes
        <<"\nposition_min="<<llama_memory_seq_pos_min(llama_get_memory(ctx),0)
        <<"\nposition_max="<<llama_memory_seq_pos_max(llama_get_memory(ctx),0)
        <<"\npayload_kind=raw_native_sequence\nactive_kv_extraction_required=true\n";
    meta.flush();if(!meta)throw std::runtime_error("capture metadata write");
}
}
