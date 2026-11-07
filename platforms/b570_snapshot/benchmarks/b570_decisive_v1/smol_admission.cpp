#include "llama.h"
#include "ggml-backend.h"
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include <stdexcept>
static void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
#include "resource_budget.hpp"
static void capacity(){
 MEMORYSTATUSEX ram{};ram.dwLength=sizeof(ram);need(GlobalMemoryStatusEx(&ram),"RAM query");
 need(ram.ullAvailPhys>=2ULL*1024*1024*1024,"2GiB RAM reserve");
 need(bounded_vulkan_free()>=128ULL*1024*1024,"128MiB GPU reserve");
}
int main(int argc,char**argv){
 llama_model*t=nullptr,*d=nullptr;llama_context*a=nullptr,*b=nullptr,*c=nullptr;bool init=false;
 auto cleanup=[&](){if(c)llama_free(c);if(b)llama_free(b);if(a)llama_free(a);if(d)llama_model_free(d);if(t)llama_model_free(t);if(init)llama_backend_free();};
 try{
  need(argc==3,"target draft paths");llama_backend_init();init=true;
  ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++)if(std::string(ggml_backend_dev_description(ggml_backend_dev_get(i))).find("B570")!=std::string::npos){need(!gpu,"ambiguous GPU");gpu=ggml_backend_dev_get(i);}
  need(gpu,"B570 missing");ggml_backend_dev_t devices[]={gpu,nullptr};
  auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  t=llama_model_load_from_file(argv[1],mp);need(t,"target model");d=llama_model_load_from_file(argv[2],mp);need(d,"draft model");capacity();
  auto*tv=llama_model_get_vocab(t);auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(std::strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");
  for(int ub:{1,2,4}){
   auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=512;p.n_threads=10;p.n_threads_batch=10;p.n_ubatch=128;p.n_outputs_max=512;p.n_outputs_max_per_seq=512;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
   a=llama_init_from_model(t,p);need(a,"target prefill context");
   p.n_ubatch=ub;p.n_outputs_max=1;p.n_outputs_max_per_seq=1;b=llama_init_from_model(d,p);need(b,"draft context");need(int(llama_n_ubatch(b))==ub,"actual draft width");
   p.n_ubatch=1;p.n_outputs_max=2;p.n_outputs_max_per_seq=2;c=llama_init_from_model(t,p);need(c,"target continuation context");capacity();
   std::printf("SMOL_ZERO_FORWARD_ADMITTED draft_ub=%d vocab=%d\n",ub,llama_vocab_n_tokens(tv));
   llama_free(c);c=nullptr;llama_free(b);b=nullptr;llama_free(a);a=nullptr;
  }
  cleanup();std::puts("SMOL_ADMISSION_COMPLETE forwards=0");return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());cleanup();return 2;}
}
