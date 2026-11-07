#pragma once
// Declaration stub ONLY for C++ syntax/instrumentation unit checks. Not llama.
#include <cstddef>
#include <cstdint>
struct llama_context{};struct llama_model{};struct llama_vocab{};struct llama_memory{};
inline void llama_synchronize(llama_context*){}
inline const llama_vocab* llama_model_get_vocab(llama_model*){static llama_vocab v;return &v;}
inline int llama_vocab_n_tokens(const llama_vocab*){return 4;}
inline float* llama_get_logits_ith(llama_context*,int){static float v[4]={1,2,3,4};return v;}
inline std::size_t llama_state_seq_get_size(llama_context*,int){return 8;}
inline std::size_t llama_state_seq_get_data(llama_context*,std::uint8_t*p,std::size_t n,int){for(std::size_t i=0;i<n;i++)p[i]=std::uint8_t(i);return n;}
inline llama_memory* llama_get_memory(llama_context*){static llama_memory m;return &m;}
inline int llama_memory_seq_pos_min(llama_memory*,int){return 0;}
inline int llama_memory_seq_pos_max(llama_memory*,int){return 2;}
