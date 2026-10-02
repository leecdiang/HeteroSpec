// Vocab-only input contract. No context, decode, sampler or model forward exists.
#include "llama.h"
#include "json.hpp"
#include <windows.h>
#include <iostream>
#include <string>
#include <vector>
int main(int argc,char **argv){
    if(argc!=3)return 2;SetDllDirectoryA(argv[1]);auto dll=LoadLibraryA((std::string(argv[1])+"/llama.dll").c_str());if(!dll)return 3;
#define GET(N) auto f_##N=(decltype(&N))GetProcAddress(dll,#N);if(!f_##N)return 4;
    GET(llama_model_default_params) GET(llama_model_load_from_file) GET(llama_model_get_vocab) GET(llama_tokenize) GET(llama_model_free)
    auto p=f_llama_model_default_params();p.vocab_only=true;p.n_gpu_layers=0;auto m=f_llama_model_load_from_file(argv[2],p);if(!m)return 5;auto v=f_llama_model_get_vocab(m);
    std::string line;while(std::getline(std::cin,line)){
        auto q=nlohmann::json::parse(line);auto text=q.at("formatted_prompt").get<std::string>();std::vector<int> ids(text.size()+64);
        int n=f_llama_tokenize(v,text.c_str(),text.size(),ids.data(),ids.size(),true,true);if(n<=0)return 6;ids.resize(n);
        std::cout<<nlohmann::json({{"task_id",q.at("task_id")},{"prompt_ids",ids},{"vocab_only",true},{"forward_calls",0}}).dump()<<std::endl;
    }f_llama_model_free(m);return 0;
}
