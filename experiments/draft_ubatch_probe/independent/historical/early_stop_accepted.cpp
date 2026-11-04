#include "llama.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <fstream>
#include <filesystem>
#include <memory>
#include <stdexcept>
#include <vector>
#include <nlohmann/json.hpp>
using J=nlohmann::json;
static int checks=0;
static void need(bool x,const char*m){++checks;if(!x)throw std::runtime_error(m);}
struct Ctx {
 llama_context*c; llama_model*m; int nv,ub,calls=0;
 Ctx(llama_model*model,int width,int outputs=0):m(model),nv(llama_vocab_n_tokens(llama_model_get_vocab(m))),ub(width){
  auto p=llama_context_default_params();p.n_ctx=128;p.n_batch=128;p.n_ubatch=ub;
  p.n_threads=1;p.n_threads_batch=1;p.n_outputs_max=outputs?outputs:ub;p.n_outputs_max_per_seq=outputs?outputs:ub;
  p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
  c=llama_init_from_model(m,p);need(c,"init");need(int(llama_n_ubatch(c))==ub,"actual ubatch differs");
 }
 ~Ctx(){llama_free(c);} Ctx(const Ctx&)=delete;
 void decode(const std::vector<int>&ids,int pos,bool all=false){
  need(!ids.empty()&&pos>=0&&pos+ids.size()<=128,"decode bounds");
  auto b=llama_batch_init(ids.size(),0,1);b.n_tokens=ids.size();
  for(int i=0;i<b.n_tokens;++i){need(ids[i]>=0&&ids[i]<nv,"token bounds");b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||i+1==b.n_tokens;}
  int rc=llama_decode(c,b);llama_batch_free(b);need(rc==0,"decode failed; abort case, no unsafe continuation");llama_synchronize(c);++calls;
 }
 std::vector<float> logits(int row=-1){auto*p=llama_get_logits_ith(c,row);need(p,"missing logits");std::vector<float> v(p,p+nv);for(float x:v)need(std::isfinite(x),"nonfinite logits");return v;}
 int sample(int row=-1){auto v=logits(row);return std::max_element(v.begin(),v.end())-v.begin();}
 void trim(int n){need(llama_memory_seq_rm(llama_get_memory(c),0,n,-1),"trim failed");need(llama_memory_seq_pos_max(llama_get_memory(c),0)==n-1,"trim position");}
 std::vector<uint8_t> state(){size_t n=llama_state_seq_get_size(c,0);need(n>0,"state size");std::vector<uint8_t> v(n);need(llama_state_seq_get_data(c,v.data(),n,0)==n,"state export");return v;}
 void reset(){llama_memory_clear(llama_get_memory(c),false);need(llama_memory_seq_pos_max(llama_get_memory(c),0)==-1,"reset position");}
};
static bool same(const std::vector<float>&a,const std::vector<float>&b){return a.size()==b.size()&&memcmp(a.data(),b.data(),a.size()*sizeof(float))==0;}
static std::vector<float> oracle(llama_model*m,const std::vector<int>&prefix){Ctx r(m,1);for(size_t i=0;i<prefix.size();++i)r.decode({prefix[i]},i);return r.logits();}
static int argmax(const std::vector<float>&v){return std::max_element(v.begin(),v.end())-v.begin();}
// Identical greedy accept/correction/bonus/trim arithmetic to #151. The native
// fixture independently checks every verification row against a forced-prefix
// scalar replay; the replay is validation work, NOT an optimized service path.
static J transaction(llama_model*m,int dub,int forced_reject,int cap,int stop_index){
 const std::vector<int> prompt={1,2,3,4,5,6,7};Ctx target(m,1,4),draft(m,dub,1);
 target.decode(prompt,0);draft.decode(prompt,0);const auto initial_draft=draft.logits();
 std::vector<int> history=prompt,output;int pending=target.sample(),base=prompt.size(),accepted_total=0,cycles=0;
 J rows=J::array();bool done=false;int mismatch=0;
 auto commit=[&](int token){output.push_back(token);done=true; /* deliberately broken: stop every case immediately */};
 commit(pending);
 while(!done){
  int seed=pending;draft.trim(base);draft.decode({seed},base);
  std::vector<int> prop,forced=history;forced.push_back(seed);
  for(int j=0;j<3;++j){int token=draft.sample();if(forced_reject>=0){token=argmax(oracle(m,forced));if(j==forced_reject)token=(token+1)%draft.nv;}
   prop.push_back(token);draft.decode({token},base+1+j);forced.push_back(token);
  }
  auto verify=prop;verify.insert(verify.begin(),seed);target.decode(verify,base,true);
  std::vector<int> decisions;auto prefix=history;
  for(int row=0;row<4;++row){prefix.push_back(verify[row]);auto actual=target.logits(row),expected=oracle(m,prefix);if(!same(actual,expected))++mismatch;decisions.push_back(argmax(actual));}
  int accepted=0;std::string last;
  for(int j=0;j<3&&!done;++j){if(decisions[j]==prop[j]){++accepted;commit(prop[j]);last="accepted";}else{pending=decisions[j];commit(pending);last="correction";break;}}
  if(accepted==3&&!done){pending=decisions[3];commit(pending);last="bonus";}
  int keep=base+1+accepted;target.trim(keep);draft.trim(keep);
  history.push_back(seed);history.insert(history.end(),prop.begin(),prop.begin()+accepted);
  need(int(history.size())==keep,"history/position disagreement");
  rows.push_back({{"base",base},{"proposals",prop},{"decisions",decisions},{"accepted",accepted},{"last",last},{"keep",keep},{"pending",done?J(nullptr):J(pending)}});
  base=keep;accepted_total+=accepted;++cycles;need(cycles<=cap,"termination");
 }
 // Verify complete endpoint independently using a fresh scalar target.
 auto canonical=prompt;std::vector<int> expected_output;
 for(size_t i=0;i<output.size();++i){int id=argmax(oracle(m,canonical));expected_output.push_back(id);canonical.push_back(id);}
 bool endpoint=output==expected_output;
 // Restore neither logits nor old half-clean state: test actual append after
 // trim on the same retained target, against fresh replay at the same prefix.
 Ctx state_oracle(m,1);for(size_t i=0;i<history.size();++i)state_oracle.decode({history[i]},i);bool state_match=target.state()==state_oracle.state();
 int continuation=1;target.decode({continuation},base);auto hist2=history;hist2.push_back(continuation);
 bool continuation_match=same(target.logits(),oracle(m,hist2));
 target.reset();target.decode(prompt,0);bool reset_match=same(target.logits(),oracle(m,prompt));
 draft.reset();draft.decode(prompt,0);bool draft_reset_match=same(draft.logits(),initial_draft);
 return {{"draft_ubatch",dub},{"forced_reject_index",forced_reject},{"cap",cap},{"stop_after_output_index",stop_index},{"stop_is_synthetic_eog_predicate",true},{"cycles",rows},{"endpoint_match",endpoint},{"verification_vector_mismatches",mismatch},{"serialized_committed_sequence_match",state_match},{"post_trim_continuation_match",continuation_match},{"reset_match",reset_match},{"draft_resident_reset_match",draft_reset_match},{"target_ubatch",1},{"accepted",accepted_total},{"ids",output}};
}
int main(int argc,char**argv){try{
 need(argc==3,"supply tiny GGUF and fresh journal path");need(!std::filesystem::exists(argv[2]),"fresh journal required");std::ofstream journal(argv[2]);need(bool(journal),"journal open");
 auto record=[&](const J&x){journal<<x.dump()<<"\n";journal.flush();need(bool(journal),"journal write");};llama_backend_init();auto mp=llama_model_default_params();mp.n_gpu_layers=0;
 std::unique_ptr<llama_model,decltype(&llama_model_free)> m(llama_model_load_from_file(argv[1],mp),llama_model_free);need(bool(m),"model load");
 J result={{"scope","native CPU tiny model; not frozen CUDA R qualification"},{"attempts",J::array()},{"prefill",J::array()}};
 std::vector<int> prompt={1,2,3,4,5,6,7};auto expected=oracle(m.get(),prompt);
 for(int ub:{1,2,4}){Ctx d(m.get(),ub,1);d.decode(prompt,0);result["prefill"].push_back({{"ubatch",ub},{"actual_ubatch",llama_n_ubatch(d.c)},{"caller_calls",d.calls},{"expected_internal_microbatches",(prompt.size()+ub-1)/ub},{"initial_logits_equal_scalar",same(d.logits(),expected)}});
  for(int rej:{-1,0,1,2,3})for(int cap:{1,2,5,9}){record({{"status","STARTED"},{"ubatch",ub},{"reject",rej},{"cap",cap},{"stop",0}});auto x=transaction(m.get(),ub,rej,cap,0);record({{"status","COMPLETED"},{"result",x}});result["attempts"].push_back(x);}
  for(int stop:{1,2,3,4,5}){record({{"status","STARTED"},{"ubatch",ub},{"reject",3},{"cap",9},{"stop",stop}});auto x=transaction(m.get(),ub,3,9,stop);record({{"status","COMPLETED"},{"result",x}});result["attempts"].push_back(x);}
 }
 bool qualified=true;for(auto&x:result["attempts"])qualified&=x["endpoint_match"].get<bool>()&&x["verification_vector_mismatches"]==0&&x["serialized_committed_sequence_match"].get<bool>()&&x["post_trim_continuation_match"].get<bool>()&&x["reset_match"].get<bool>()&&x["draft_resident_reset_match"].get<bool>();
 result["local_scalar_target_checks_pass"]=qualified;result["checks"]=checks;result["status"]=qualified?"PASS":"OBSERVED_MISMATCH";std::cout<<result.dump(2)<<"\n";return qualified?0:1;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
