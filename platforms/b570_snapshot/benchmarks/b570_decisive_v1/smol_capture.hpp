#pragma once
#include <filesystem>
#include <fstream>
#include <vector>
#include <stdexcept>
#ifdef SMOL_BULK_OBSERVER
#include "smol_bulk.hpp"
#endif
// Only observers read already requested logits and active sequence state.
// No extra output flags, model decode, sampler mutation or state import.
static pj hs_smol_capture_owned(llama_context*ctx,const std::string&base,int index,int row,const std::vector<float>&vector){
 namespace fs=std::filesystem;
 fs::path dir=base+".states";fs::create_directories(dir);
 if(fs::space(dir).available<20ULL*1024*1024*1024)throw std::runtime_error("state disk reserve");
 auto save=[&](const std::string&name,const void*data,size_t n){
  auto path=dir/name;if(fs::exists(path))throw std::runtime_error("state overwrite");
  std::ofstream f(path,std::ios::binary);f.write((const char*)data,n);if(!f)throw std::runtime_error("state write");return path.generic_string();
 };
 int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));if(vector.size()!=size_t(nv))throw std::runtime_error("owned frontier extent");
 llama_synchronize(ctx);
#ifdef SMOL_BULK_OBSERVER
 auto state=smol_bulk_state(ctx);size_t n=state.size();
#else
 size_t n=llama_state_seq_get_size(ctx,0);if(!n)throw std::runtime_error("empty sequence state");
 std::vector<uint8_t> state(n);if(llama_state_seq_get_data(ctx,state.data(),n,0)!=n)throw std::runtime_error("short sequence state");
#endif
 return {{"index",index},{"row",row},{"frontier",save(std::to_string(index)+".f32",vector.data(),vector.size()*4)},
         {"sequence",save(std::to_string(index)+".bin",state.data(),state.size())},{"sequence_bytes",n},
         {"position_min",llama_memory_seq_pos_min(llama_get_memory(ctx),0)},{"position_max",llama_memory_seq_pos_max(llama_get_memory(ctx),0)}};
}
static pj hs_smol_capture(llama_context*ctx,const std::string&base,int index,int row){
 llama_synchronize(ctx);auto*p=llama_get_logits_ith(ctx,row);if(!p)throw std::runtime_error("capture requested row absent");
 int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));std::vector<float> owned(p,p+nv);
 return hs_smol_capture_owned(ctx,base,index,row,owned);
}
