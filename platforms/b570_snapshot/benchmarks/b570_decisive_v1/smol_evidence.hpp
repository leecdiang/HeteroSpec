#pragma once
#include "smol_capture.hpp"
#include <map>
struct SmolEvidence {
 bool heavy=false,final_only=false;int serial=0,last_start=0,last_count=0,prompt_count=0;
 std::vector<int> tokens,batch_positions;std::vector<bool> flags;
 std::map<int,std::vector<float>> last_owned;std::vector<float> initial_vector;
 pj vectors=pj::array(),states=pj::array(),draft_vectors=pj::array();std::string base;
 void reset(const pj&r){heavy=r.value("heavy_state",false);final_only=r.value("audit_final",false);prompt_count=r.at("prompt_ids").size();serial=0;tokens.clear();last_owned.clear();initial_vector.clear();vectors=pj::array();states=pj::array();draft_vectors=pj::array();base=r.at("output");}
 void begin(llama_context*ctx,llama_batch b,const std::string&role){
  if(!(heavy||final_only)||role!="target")return;
  int start=b.pos?b.pos[0]:llama_memory_seq_pos_max(llama_get_memory(ctx),0)+1;
  if(start<0||start>int(tokens.size()))throw std::runtime_error("target transcript gap");
  tokens.resize(start);last_start=start;last_count=b.n_tokens;batch_positions.clear();flags.clear();
  for(int i=0;i<b.n_tokens;i++){
   int pos=b.pos?b.pos[i]:start+i;if(pos!=start+i)throw std::runtime_error("non-dense target batch");
   tokens.push_back(b.token[i]);batch_positions.push_back(pos);flags.push_back(b.logits?bool(b.logits[i]):i==b.n_tokens-1);
  }
 }
 void end(llama_context*ctx,const std::string&role){
  if(heavy&&role=="draft"&&llama_memory_seq_pos_max(llama_get_memory(ctx),0)+1==prompt_count&&draft_vectors.empty()){
   auto*p=llama_get_logits_ith(ctx,-1);if(!p)throw std::runtime_error("draft final prompt row missing");
   int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));
   std::string path=base+".draft-prefill.f32";std::ofstream f(path,std::ios::binary);f.write((const char*)p,nv*4);if(!f)throw std::runtime_error("draft full row write");draft_vectors.push_back({{"path",path},{"tokens",prompt_count}});
  }
  if(!heavy||role!="target")return;
  int outputs=std::count(flags.begin(),flags.end(),true);last_owned.clear();
  for(size_t i=0;i<flags.size();i++)if(flags[i]){
   int row=outputs==1?-1:int(i);auto*p=llama_get_logits_ith(ctx,row);if(!p)throw std::runtime_error("target full row missing");
   int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));std::vector<float> owned(p,p+nv);
   last_owned[batch_positions[i]]=owned;
   // Intermediate 512-token prefill outputs are unused. Preserve their native
   // flags, but qualify the final prompt frontier and every continuation row.
   if(batch_positions[i]+1<prompt_count)continue;
   std::filesystem::path folder=base+".vectors";std::filesystem::create_directories(folder);
   auto path=folder/(std::to_string(vectors.size())+".f32");if(std::filesystem::exists(path))throw std::runtime_error("vector overwrite");
   std::ofstream f(path,std::ios::binary);f.write((const char*)owned.data(),owned.size()*4);if(!f)throw std::runtime_error("full vector write");
   vectors.push_back({{"prefix",std::vector<int>(tokens.begin(),tokens.begin()+batch_positions[i]+1)},{"row",row},{"path",path.generic_string()}});
  }
 }
 void commit(llama_context*ctx){
  if(!(heavy||final_only))return;
  int keep=llama_memory_seq_pos_max(llama_get_memory(ctx),0)+1;
  if(keep<1||keep>int(tokens.size()))throw std::runtime_error("commit transcript extent");tokens.resize(keep);
  int outputs=std::count(flags.begin(),flags.end(),true);int row=outputs==1?-1:keep-last_start-1;
  if(outputs>1&&(row<0||row>=last_count||!flags[row]))throw std::runtime_error("retained row not requested");
  std::vector<float> owned;
  if(heavy)owned=last_owned.at(keep-1);
  else if(!initial_vector.empty()&&keep==prompt_count)owned=initial_vector;
  else{llama_synchronize(ctx);auto*p=llama_get_logits_ith(ctx,row);if(!p)throw std::runtime_error("final requested row missing");int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));owned.assign(p,p+nv);}
  auto s=hs_smol_capture_owned(ctx,base,serial++,row,owned);s["prefix"]=tokens;s["frontier_ownership"]="owned before restore or buffer reuse";states.push_back(s);
 }
};
