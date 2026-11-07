#include "llama.h"
#include "json.hpp"
#include <windows.h>
#include <iostream>
#include <vector>
using json=nlohmann::ordered_json;
int main(int argc,char**argv){
    if(argc!=3)return 2;SetDllDirectoryA(argv[1]);auto dll=LoadLibraryA((std::string(argv[1])+"/llama.dll").c_str());if(!dll)return 3;
#define GET(N) auto f_##N=(decltype(&N))GetProcAddress(dll,#N);if(!f_##N)return 4;
    GET(llama_model_default_params) GET(llama_model_load_from_file) GET(llama_model_get_vocab) GET(llama_tokenize) GET(llama_model_free) GET(llama_vocab_n_tokens) GET(llama_vocab_is_eog) GET(llama_vocab_type) GET(llama_vocab_get_text) GET(llama_vocab_get_attr) GET(llama_vocab_get_add_bos) GET(llama_vocab_get_add_eos) GET(llama_vocab_bos) GET(llama_vocab_eos) GET(llama_vocab_get_suppress_tokens)
    auto params=f_llama_model_default_params();params.vocab_only=true;params.n_gpu_layers=0;auto model=f_llama_model_load_from_file(argv[2],params);if(!model)return 5;auto vocab=f_llama_model_get_vocab(model);
    json tokens=json::array(),eog=json::array(),suppress=json::array();for(int id=0;id<f_llama_vocab_n_tokens(vocab);++id){tokens.push_back({{"id",id},{"text",f_llama_vocab_get_text(vocab,id)},{"attr",f_llama_vocab_get_attr(vocab,id)}});if(f_llama_vocab_is_eog(vocab,id))eog.push_back(id);}
    int count=0;const auto *s=f_llama_vocab_get_suppress_tokens(vocab,&count);for(int i=0;i<count;++i)suppress.push_back(s[i]);
    std::cout<<json({{"event","vocabulary"},{"tokens",tokens},{"eog",eog},{"type",f_llama_vocab_type(vocab)},{"bos",f_llama_vocab_bos(vocab)},{"eos",f_llama_vocab_eos(vocab)},{"add_bos",f_llama_vocab_get_add_bos(vocab)},{"add_eos",f_llama_vocab_get_add_eos(vocab)},{"suppress",suppress},{"vocab_only",true},{"forward_calls",0},{"context_creations",0}}).dump()<<std::endl;
    std::string line;while(std::getline(std::cin,line)){auto q=json::parse(line);auto text=q.at("formatted_prompt").get<std::string>();std::vector<int> ids(text.size()+64);int n=f_llama_tokenize(vocab,text.c_str(),text.size(),ids.data(),ids.size(),true,true);if(n<=0)return 6;ids.resize(n);std::cout<<json({{"task_id",q.at("task_id")},{"prompt_ids",ids},{"vocab_only",true},{"forward_calls",0}}).dump()<<std::endl;}
    f_llama_model_free(model);return 0;
}
