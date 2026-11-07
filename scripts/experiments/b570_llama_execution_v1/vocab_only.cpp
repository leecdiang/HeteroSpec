#include "llama.h"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <chrono>
using json=nlohmann::json;
int main(int argc,char**argv){
 llama_model*model=nullptr;
 try{
  if(argc!=4)throw std::runtime_error("vocab_only MODEL INPUT_JSONL OUTPUT_JSONL");
  auto begin=std::chrono::steady_clock::now();auto mp=llama_model_default_params();mp.vocab_only=true;mp.n_gpu_layers=0;
  model=llama_model_load_from_file(argv[1],mp);if(!model)throw std::runtime_error("vocabulary model load");
  auto*v=llama_model_get_vocab(model);json eog=json::array();for(int i=0;i<llama_vocab_n_tokens(v);i++)if(llama_vocab_is_eog(v,i))eog.push_back(i);
  const char*templ=llama_model_chat_template(model,nullptr);if(!templ)throw std::runtime_error("chat template missing");
  std::ifstream input(argv[2]);std::ofstream output(argv[3]);if(!input||!output)throw std::runtime_error("tokenization files");
  std::string line;size_t count=0;
  while(std::getline(input,line)){
   auto row=json::parse(line);std::string text=row.at("formatted_prompt");std::vector<llama_token>ids(text.size()+32);
   int n=llama_tokenize(v,text.data(),int(text.size()),ids.data(),int(ids.size()),false,true);
   if(n<0){ids.resize(-n);n=llama_tokenize(v,text.data(),int(text.size()),ids.data(),int(ids.size()),false,true);}
   if(n<0)throw std::runtime_error("tokenization failed");ids.resize(n);output<<json({{"id",row.at("id")},{"prompt_ids",ids}}).dump()<<'\n';count++;
  }
  if(!output)throw std::runtime_error("token output write");output.close();
  json result={{"status","VOCAB_ONLY_COMPLETE"},{"rows",count},{"template",templ},{"vocab_tokens",llama_vocab_n_tokens(v)},{"eog",eog},{"add_special",false},{"parse_special",true},{"forward_calls",0},{"contexts_created",0},{"gpu_layers",0}};
  llama_model_free(model);model=nullptr;result["normal_cleanup_returned"]=true;result["elapsed_seconds"]=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
  std::ofstream receipt(std::string(argv[3])+".MODEL.json");receipt<<result.dump(2)<<'\n';return 0;
 }catch(const std::exception&e){if(model)llama_model_free(model);std::cerr<<e.what()<<'\n';return 2;}
}
