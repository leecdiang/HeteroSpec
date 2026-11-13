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
    auto detokenize=[&](const std::vector<int>&ids){std::vector<char>back(ids.size()*64+128);int n=llama_detokenize(vocab,ids.data(),ids.size(),back.data(),back.size(),false,true);if(n<0){back.resize(-n);n=llama_detokenize(vocab,ids.data(),ids.size(),back.data(),back.size(),false,true);}if(n<0)throw std::runtime_error("native detokenize");return std::string(back.data(),n);};
    auto raw_pieces=[&](const std::vector<int>&ids){std::string result;for(int id:ids){std::vector<char>piece(128);int n=llama_token_to_piece(vocab,id,piece.data(),piece.size(),0,true);if(n<0){piece.resize(-n);n=llama_token_to_piece(vocab,id,piece.data(),piece.size(),0,true);}if(n<0)throw std::runtime_error("native token_to_piece");result.append(piece.data(),n);}return result;};
    std::string line;while(std::getline(std::cin,line)){
        auto q=json::parse(line);std::string text;
        if(q.contains("prompt_ids"))text=raw_pieces(q.at("prompt_ids").get<std::vector<int>>());else text=q.at("formatted_prompt").get<std::string>();
        const bool add_special=q.value("add_special",false);std::vector<int>ids(text.size()+64);
        int n=llama_tokenize(vocab,text.c_str(),text.size(),ids.data(),ids.size(),add_special,true);if(n<=0)return 6;ids.resize(n);
        std::cout<<json({{"task_id",q.at("task_id")},{"prompt_ids",ids},{"native_detokenized_prompt",detokenize(ids)},{"native_raw_piece_prompt",raw_pieces(ids)},
            {"add_special",add_special},{"vocab_only",true},{"forward_calls",0}}).dump()<<std::endl;
    }
    llama_model_free(model);return 0;
}

