#include "llama.h"
#include <nlohmann/json.hpp>

#include <iostream>
#include <vector>
using json=nlohmann::ordered_json;
int main(int argc,char**argv){
    if(argc!=2)return 2;
    auto params=llama_model_default_params();params.vocab_only=true;params.n_gpu_layers=0;auto model=llama_model_load_from_file(argv[1],params);if(!model)return 5;auto vocab=llama_model_get_vocab(model);
    json tokens=json::array(),eog=json::array(),suppress=json::array();for(int id=0;id<llama_vocab_n_tokens(vocab);++id){tokens.push_back({{"id",id},{"text",llama_vocab_get_text(vocab,id)},{"attr",llama_vocab_get_attr(vocab,id)}});if(llama_vocab_is_eog(vocab,id))eog.push_back(id);}
    int count=0;const auto *s=llama_vocab_get_suppress_tokens(vocab,&count);for(int i=0;i<count;++i)suppress.push_back(s[i]);
    std::cout<<json({{"event","vocabulary"},{"tokens",tokens},{"eog",eog},{"type",llama_vocab_type(vocab)},{"bos",llama_vocab_bos(vocab)},{"eos",llama_vocab_eos(vocab)},{"add_bos",llama_vocab_get_add_bos(vocab)},{"add_eos",llama_vocab_get_add_eos(vocab)},{"suppress",suppress},{"vocab_only",true},{"forward_calls",0},{"context_creations",0}}).dump()<<std::endl;
    std::string line;while(std::getline(std::cin,line)){auto q=json::parse(line);auto text=q.at("formatted_prompt").get<std::string>();std::vector<int> ids(text.size()+64);int n=llama_tokenize(vocab,text.c_str(),text.size(),ids.data(),ids.size(),q.value("add_special",true),true);if(n<=0)return 6;ids.resize(n);std::vector<char> back(text.size()*2+128);int nb=llama_detokenize(vocab,ids.data(),ids.size(),back.data(),back.size(),false,true);if(nb<0){back.resize(-nb);nb=llama_detokenize(vocab,ids.data(),ids.size(),back.data(),back.size(),false,true);}if(nb<0)return 7;std::cout<<json({{"task_id",q.at("task_id")},{"prompt_ids",ids},{"native_detokenized_prompt",std::string(back.data(),nb)},{"add_special",q.value("add_special",true)},{"vocab_only",true},{"forward_calls",0}}).dump()<<std::endl;}
    llama_model_free(model);return 0;
}

