// Exact original GGUF tokenizer. No context, decode or model forward is created.
#define NOMINMAX
#include <windows.h>
#include "llama.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>
using json=nlohmann::json;
void need(bool x,const char* message){if(!x)throw std::runtime_error(message);}
int main(int argc,char** argv){
    try{
        SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
        need(argc==4,"model input-jsonl output-jsonl");
        need(!std::filesystem::exists(argv[3]),"fresh tokenizer output required");
        auto params=llama_model_default_params();params.vocab_only=true;params.n_gpu_layers=0;
        auto* model=llama_model_load_from_file(argv[1],params);need(model,"vocabulary load");
        auto* vocab=llama_model_get_vocab(model);need(llama_vocab_n_tokens(vocab)==128256,"original Llama vocabulary");
        auto* chat=llama_model_chat_template(model,nullptr);need(chat,"original template missing");
        std::vector<int> eog;for(int id=0;id<128256;++id)if(llama_vocab_is_eog(vocab,id))eog.push_back(id);
        std::ifstream input(argv[2]);std::ofstream output(argv[3]);need(bool(input)&&bool(output),"tokenizer files");
        std::string line;size_t count=0;
        while(std::getline(input,line)){
            auto item=json::parse(line);auto text=item.at("formatted_prompt").get<std::string>();
            need(text.size()<1024*1024,"prompt byte reservation");
            int n=llama_tokenize(vocab,text.data(),int(text.size()),nullptr,0,false,true);need(n<0,"token count");
            std::vector<int> ids(-n);n=llama_tokenize(vocab,text.data(),int(text.size()),ids.data(),int(ids.size()),false,true);
            need(n==int(ids.size()),"tokenization size");
            output<<json({{"id",item.at("id")},{"prompt_ids",ids}}).dump()<<'\n';need(bool(output),"tokenizer output write");++count;
        }
        json metadata={{"template",chat},{"vocabulary_tokens",128256},{"eog",eog},{"add_special",false},
                       {"parse_special",true},{"vocab_only",true},{"forward_calls",0},{"items",count}};
        {std::ofstream f(std::string(argv[3])+".MODEL.json");f<<metadata.dump(2)<<'\n';need(bool(f),"metadata write");}
        llama_model_free(model);std::cout<<"VOCAB_ONLY_COMPLETE "<<count<<'\n';return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
