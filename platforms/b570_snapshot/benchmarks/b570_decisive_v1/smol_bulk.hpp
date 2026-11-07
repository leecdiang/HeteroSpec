#pragma once
#include "llama-memory.h"
#include "llama-io.h"
#include "ggml-backend.h"
#include <cstring>
// Invoke the unchanged memory writer through its pinned ABI. Coalesce repeated
// reads from each transposed tensor, then emit only the writer's requested bytes.
// This is an offline observer; it never writes or restores model memory.
struct smol_bulk_writer final:llama_io_write_i {
 std::vector<uint8_t> bytes,cached;ggml_tensor*last=nullptr;
 void write(const void*data,size_t n)override{
  if(n>256ULL*1024*1024||bytes.size()+n>256ULL*1024*1024)throw std::runtime_error("observer state bound");
  auto*p=(const uint8_t*)data;bytes.insert(bytes.end(),p,p+n);
 }
 void write_tensor(ggml_tensor*t,size_t off,size_t n)override{
  if(last!=t){size_t total=ggml_nbytes(t);if(total>16ULL*1024*1024)throw std::runtime_error("observer tensor bound");cached.resize(total);ggml_backend_tensor_get(t,cached.data(),0,total);last=t;}
  if(off>cached.size()||n>cached.size()-off)throw std::runtime_error("observer tensor range");
  write(cached.data()+off,n);
 }
 size_t n_bytes()override{return bytes.size();}
};
static std::vector<uint8_t> smol_bulk_state(llama_context*ctx){
 smol_bulk_writer io;uint32_t magic=0xaf143cd8;int32_t sequence=0;
 io.write(&magic,4);io.write(&sequence,4);llama_get_memory(ctx)->state_write(io,0,0);
 static bool checked=false;
 if(!checked){size_t n=llama_state_seq_get_size(ctx,0);std::vector<uint8_t> original(n);
  if(!n||llama_state_seq_get_data(ctx,original.data(),n,0)!=n||original!=io.bytes)throw std::runtime_error("bulk observer differs from original seq writer");checked=true;
 }
 return io.bytes;
}
