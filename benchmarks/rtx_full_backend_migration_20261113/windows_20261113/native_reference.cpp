// Independent integration reference: own batch construction/control and captures.
// Does not include the adapter source. No cross-version arithmetic equivalence claim.
#define NOMINMAX
#include "llama.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include <stdexcept>
using json=nlohmann::json;namespace fs=std::filesystem;
static void must(bool ok,const char *why){if(!ok)throw std::runtime_error(why);}
static std::vector<llama_token> tokenize(const llama_vocab *v,const std::string&s,bool bos){
 std::vector<llama_token> t(s.size()+256);int n=llama_tokenize(v,s.data(),int(s.size()),t.data(),int(t.size()),bos,true);must(n>0,"tokenize");t.resize(n);return t;
}
int main(int argc,char **argv){
 llama_model*m=nullptr;llama_context*c=nullptr;
 try{
  must(argc==6,"ref MODEL INPUT_JSONL OUTPUT_JSONL CAPTURE_PREFIX TOKENIZE_OUTPUT");
#ifdef HS_LEGACY_R
  auto bin=fs::absolute(argv[0]).parent_path();auto base=LoadLibraryW((bin/L"ggml-base.dll").c_str());must(base,"base");auto init=(void(*)())GetProcAddress(base,"ggml_time_init");must(init,"clock");init();ggml_backend_load_all_from_path(bin.string().c_str());
#endif
  llama_backend_init();ggml_backend_dev_t device=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){must(!device,"ambiguous device");device=d;}}
  must(device,"GPU required");ggml_backend_dev_t devices[]={device,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  m=llama_model_load_from_file(argv[1],mp);must(m,"model");const auto*v=llama_model_get_vocab(m);const int nv=llama_vocab_n_tokens(v);
  std::ofstream receipt(argv[3]);must(bool(receipt),"receipt");receipt<<json({{"event","loaded"},{"vocab",nv},{"device",ggml_backend_dev_description(device)}})<<'\n';receipt.flush();
  if(std::string(argv[5])!="-"){
   std::ifstream raw(argv[2]);std::ofstream tok(argv[5]);must(bool(raw)&&bool(tok),"tokenizer IO");std::string line;
   while(std::getline(raw,line)){auto x=json::parse(line);x["prompt_ids"]=tokenize(v,x.at("prompt_text"),true);auto t=tokenize(v,x.at("continuation_text"),false);if(t.size()<128)continue;t.resize(128);x["continuation_ids"]=t;x["tokenizer_identity"]="GGUF408b9555-native-original-v4";tok<<x<<'\n';}
   tok.flush();must(bool(tok),"tokenizer write");receipt<<"{\"event\":\"tokenizer_done\"}\n";receipt.flush();
  }
  std::string request_file;must(bool(std::getline(std::cin,request_file)),"controller request path");
  auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=32;cp.n_ubatch=32;cp.n_seq_max=1;cp.n_threads=cp.n_threads_batch=2;cp.type_k=cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.attention_type=LLAMA_ATTENTION_TYPE_CAUSAL;
#ifdef HS_LEGACY_R
  cp.n_batch=1024;cp.n_ubatch=1;cp.n_outputs_max=cp.n_outputs_max_per_seq=1;cp.n_threads=cp.n_threads_batch=24;
#endif
  c=llama_init_from_model(m,cp);must(c,"context");
  std::ifstream in(request_file);std::string line;must(bool(in),"request file");
  while(std::getline(in,line)){
   auto r=json::parse(line);auto ids=r.at("prompt_ids").get<std::vector<llama_token>>();auto tail=r.at("continuation_ids").get<std::vector<llama_token>>();must(ids.size()>=1&&ids.size()<=768&&tail.size()==128,"envelope");
   if(r.contains("prompt_text")){must(tokenize(v,r["prompt_text"],true)==ids,"native tokenizer prompt disagreement");auto t=tokenize(v,r["continuation_text"],false);must(t.size()>=128,"native continuation");t.resize(128);must(t==tail,"native tokenizer continuation disagreement");}
   if(r.contains("panel_check"))for(const auto &x:r["panel_check"]){must(tokenize(v,x["prompt_text"],true)==x["prompt_ids"].get<std::vector<llama_token>>(),"panel tokenizer mismatch");auto t=tokenize(v,x["continuation_text"],false);must(t.size()>=128,"panel tail length");t.resize(128);must(t==x["continuation_ids"].get<std::vector<llama_token>>(),"panel tail mismatch");}
   llama_memory_clear(llama_get_memory(c),true);must(llama_memory_seq_pos_max(llama_get_memory(c),0)<0,"native reset");std::vector<float> all;int pos=0,calls=0;
   const auto prompt_size=ids.size();std::vector<llama_token> emitted;bool eog=false;
   auto submit=[&](const llama_token *input,int width){
    llama_batch b=llama_batch_init(width,0,1);b.n_tokens=width;
    for(int j=0;j<width;j++){b.token[j]=input[j];b.pos[j]=pos+j;b.n_seq_id[j]=1;b.seq_id[j][0]=0;b.logits[j]=j==width-1;}
    auto rc=llama_decode(c,b);llama_batch_free(b);must(rc==0,"native decode");llama_synchronize(c);auto l=llama_get_logits_ith(c,-1);must(l,"native logits");
    for(int j=0;j<nv;j++)must(std::isfinite(l[j]),"native finite");all.insert(all.end(),l,l+nv);pos+=width;calls++;
   };
   for(size_t offset=0;offset<prompt_size;offset+=32)submit(ids.data()+offset,int(std::min<size_t>(32,prompt_size-offset)));
   for(int step=0;step<128;step++){
    llama_token token=tail[step];
    if(r.value("kind",std::string("P"))=="G"){
     const auto *logits=llama_get_logits_ith(c,-1);token=llama_token(std::max_element(logits,logits+nv)-logits);
     if(llama_vocab_is_eog(v,token)){eog=true;break;}
    }
    emitted.push_back(token);submit(&token,1);
   }
   auto path=std::string(argv[4])+"-"+std::to_string(r.at("id").get<int>())+".f32";std::ofstream f(path,std::ios::binary);f.write((const char*)all.data(),all.size()*4);f.flush();must(bool(f),"native capture");
   receipt<<json({{"event","request"},{"id",r["id"]},{"rows",pos},{"calls",calls},{"capture_floats",all.size()},{"kv_last_position",llama_memory_seq_pos_max(llama_get_memory(c),0)},{"tokens",emitted},{"eog",eog},{"status","ok"}})<<'\n';receipt.flush();must(bool(receipt),"receipt write");
  }
  must(in.eof(),"native input");llama_free(c);c=nullptr;llama_model_free(m);m=nullptr;llama_backend_free();receipt<<"{\"event\":\"done\"}\n";receipt.flush();must(bool(receipt),"done write");return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';if(c)llama_free(c);if(m)llama_model_free(m);llama_backend_free();return 1;}
}
