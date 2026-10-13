#include "llama.h"
#include "nlohmann/json.hpp"
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
using json=nlohmann::ordered_json;
std::string hex(const char *s){std::string r;for(const unsigned char *p=(const unsigned char *)s;*p;++p){r.push_back("0123456789abcdef"[*p>>4]);r.push_back("0123456789abcdef"[*p&15]);}return r;}
int main(int argc,char **argv){
 if(argc!=2)return 1;auto mp=llama_model_default_params();mp.vocab_only=true;mp.n_gpu_layers=0;
 auto *m=llama_model_load_from_file(argv[1],mp);if(!m)return 2;auto *v=llama_model_get_vocab(m);
 json eog=json::array(),table=json::array();
 for(int i=0;i<llama_vocab_n_tokens(v);++i){bool stop=llama_vocab_is_eog(v,i);if(stop)eog.push_back(i);table.push_back({{"id",i},{"text_hex",hex(llama_vocab_get_text(v,i))},{"attr",llama_vocab_get_attr(v,i)},{"score",llama_vocab_get_score(v,i)},{"eog",stop}});}
 const char *tmpl=llama_model_chat_template(m,nullptr);
 std::cout<<json({{"vocab_tokens",llama_vocab_n_tokens(v)},{"vocab_type",llama_vocab_type(v)},{"runtime_eog_ids",eog},{"table",table},{"bos",llama_vocab_bos(v)},{"eos",llama_vocab_eos(v)},{"add_bos",llama_vocab_get_add_bos(v)},{"add_eos",llama_vocab_get_add_eos(v)},{"chat_template",tmpl?tmpl:""},{"vocab_only",true},{"forward_calls",0}}).dump()<<"\n";
 std::string line;while(std::getline(std::cin,line)){
  auto r=json::parse(line);std::string text=r.at("formatted_prompt");std::vector<llama_token> ids(text.size()+32);
  int n=llama_tokenize(v,text.data(),text.size(),ids.data(),ids.size(),true,true);
  if(n<0){ids.resize(-n);n=llama_tokenize(v,text.data(),text.size(),ids.data(),ids.size(),true,true);}if(n<0)return 3;ids.resize(n);
  std::cout<<json({{"id",r.at("id")},{"prompt_ids",ids},{"forward_calls",0}}).dump()<<"\n";
 }
 llama_model_free(m);return 0;
}
