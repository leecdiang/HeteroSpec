#include "llama.h"
#include "ggml.h"
#include "ggml-backend.h"
#include "hs_loop4_tensor.hpp"
#include "hs_launch_budget.hpp"
#include "hsc_counter.h"
#include <windows.h>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>

static void need(bool b,const char *s){if(!b)throw std::runtime_error(s);}
static void gate(const char*s){std::cout<<"READY "<<s<<std::endl;std::string v;need(bool(std::getline(std::cin,v))&&v==std::string("GO ")+s,"parent gate refused");}
static void save(const std::string&p,const void*d,size_t n){
 need(n<=32*1024*1024,"capture size");HANDLE h=CreateFileA(p.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
 need(h!=INVALID_HANDLE_VALUE,"fresh output");DWORD w=0;bool ok=WriteFile(h,d,DWORD(n),&w,nullptr)&&w==n&&FlushFileBuffers(h);CloseHandle(h);need(ok,"capture write");
}
struct captured_stop {};
static std::string out;static ggml_tensor*pending=nullptr;static bool done=false;
static bool eval(ggml_tensor*t,bool ask,void*){
 if(ask){
  if(t->op!=GGML_OP_MUL_MAT||!t->src[0]||std::string(t->src[0]->name)!="blk.0.attn_q.weight")return false;
  need(!pending&&!done,"duplicate target");need(t->src[0]->type==GGML_TYPE_Q8_0&&t->src[1]->type==GGML_TYPE_F32,"capture dtype");
  need(t->src[0]->ne[0]==4096&&t->src[0]->ne[1]==4096&&t->src[1]->ne[1]==8&&t->ne[1]==8,"genuine q8 shape");
  need(ggml_is_contiguous(t->src[0])&&ggml_is_contiguous(t->src[1])&&ggml_is_contiguous(t),"capture contiguous");
  for(int i=0;i<3;++i){auto*x=i==0?t->src[0]:i==1?t->src[1]:t;need(x->buffer,"allocated captured tensor");auto*d=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(x->buffer));need(d&&ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU,"captured tensor must reside on GPU");}
  hs_loop4::mark(t);hs_loop4::require(t->src[0],t->src[1],t);pending=t;return true;
 }
 need(t==pending,"unexpected capture callback");
 for(int i=0;i<3;++i){auto*x=i==0?t->src[0]:i==1?t->src[1]:t;std::vector<unsigned char>b(ggml_nbytes(x));ggml_backend_tensor_get(x,b.data(),0,b.size());save(out+"/"+(i==0?"weight.bin":i==1?"activation.f32":"backend-output.f32"),b.data(),b.size());}
 done=true;throw captured_stop{};
}
int main(int argc,char**argv){
 llama_model*m=nullptr;llama_context*c=nullptr;
 try{
  need(argc==4,"capture ROOT_DLL MODEL OUTPUT");out=argv[3];
  gate("LOAD");SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32|LOAD_LIBRARY_SEARCH_USER_DIRS);
  HMODULE dll=LoadLibraryExA(argv[1],nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(dll,"root load");
  auto configure=(int(*)(uint64_t,uint64_t,uint64_t,const char*))GetProcAddress(dll,"hs_launch_budget_configure_v1");
  auto snapshot=(int(*)(hs_launch_budget_snapshot_v1_t*))GetProcAddress(dll,"hs_launch_budget_snapshot_v1");
  auto select=(int(*)(int))GetProcAddress(dll,"hs_e03_select_arm");
  auto init=(ggml_backend_reg_t(*)())GetProcAddress(dll,"ggml_backend_init");need(configure&&snapshot&&select&&init,"control exports");
  need(configure(567,0,32,"RTX223-E08-EXPLICIT-ONLY-CAPTURE")==1,"application-only budget configure");need(select(0)==0,"select backend loop4");
  gate("MODEL");
  auto base=GetModuleHandleA("ggml-base.dll");need(base,"bound base");auto clock_init=(void(*)())GetProcAddress(base,"ggml_time_init");need(clock_init,"shared clock");clock_init();
  std::string cpu=std::string(argv[1]);cpu=cpu.substr(0,cpu.find_last_of("/\\")+1)+"ggml-cpu.dll";
  HMODULE cpu_dll=LoadLibraryExA(cpu.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(cpu_dll,"frozen CPU backend load");
  auto cpu_init=(ggml_backend_reg_t(*)())GetProcAddress(cpu_dll,"ggml_backend_init");need(cpu_init,"CPU backend export");ggml_backend_register(cpu_init());
  ggml_backend_register(init());llama_backend_init();
  ggml_backend_dev_t gpu=nullptr;for(size_t i=0;i<ggml_backend_dev_count();++i){auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"ambiguous GPU");gpu=d;}}need(gpu,"GPU required");
  ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=0;llama_model_tensor_buft_override overrides[]={{"^blk[.]0[.].*",ggml_backend_dev_buffer_type(gpu)},{nullptr,nullptr}};mp.tensor_buft_overrides=overrides;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  m=llama_model_load_from_file(argv[2],mp);need(m,"model load");
  auto cp=llama_context_default_params();cp.n_ctx=32;cp.n_batch=8;cp.n_ubatch=8;cp.n_threads=1;cp.n_threads_batch=1;cp.cb_eval=eval;cp.cb_eval_user_data=nullptr;
  cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;
  c=llama_init_from_model(m,cp);need(c,"context load");
  const std::string text="The quick brown fox jumps over the lazy dog and explains matrix multiplication.";
  std::vector<llama_token>tokens(128);int n=llama_tokenize(llama_model_get_vocab(m),text.c_str(),int(text.size()),tokens.data(),int(tokens.size()),true,true);need(n>=8,"eight real tokens");tokens.resize(8);
  std::string ids;for(auto v:tokens)ids+=std::to_string(v)+"\n";save(out+"/tokens.txt",ids.data(),ids.size());save(out+"/prompt.txt",text.data(),text.size());
  gate("CAPTURE");hsc::begin("heavy",8);hsc::decode_begin(c,"target",false,8);auto b=llama_batch_get_one(tokens.data(),8);int code=-999;bool stopped=false;try{code=llama_decode(c,b);}catch(const captured_stop&){stopped=true;}hsc::decode_end();need(done&&stopped,"target did not stop the complete scheduler");
  std::string receipt="status=CAPTURE_COMPLETE_EXPECTED_STOP\ndecode_return="+std::to_string(code)+"\nstop=typed_exception_in_GNU_scheduler_after_synced_capture\nactual_token_rows=8\nmodel_loads=1\ndecode_calls=1\n";
  gate("CLEANUP");llama_free(c);c=nullptr;llama_model_free(m);m=nullptr;llama_backend_free();
  hs_launch_budget_snapshot_v1_t s{};need(snapshot(&s)==1&&s.terminal_code==0&&s.admitted_attempts<=32,"final counter");receipt+="explicit_app_launches="+std::to_string(s.admitted_attempts)+"\nphysical_launches=UNKNOWN\n";save(out+"/receipt.txt",receipt.data(),receipt.size());std::cout<<"COMPLETE "<<s.admitted_attempts<<std::endl;return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 2;}
}
