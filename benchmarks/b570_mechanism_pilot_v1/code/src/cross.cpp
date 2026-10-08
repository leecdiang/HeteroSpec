// Real API-restored target donor x whole current path recipe. No prefill/reference forward.
#include "arg.h"
#include "common.h"
#include "sampling.h"
#include "llama.h"
#include "pilot_state.h"
#include "observer.h"
#include "log.h"
#include <iostream>
#include <clocale>
int main(int argc,char**argv){
 std::setlocale(LC_NUMERIC,"C");common_params params;params.sampling.n_probs=128;common_init();
 if(!common_params_parse(argc,argv,params,LLAMA_EXAMPLE_COMPLETION))return 1;
 if(params.warmup||params.n_ctx!=1024||params.n_batch!=512||params.sampling.temp!=0||params.sampling.seed!=123)return 2;
 llama_backend_init();llama_numa_init(params.numa);prefill_observer observer;
 params.cb_eval=prefill_observer::callback;params.cb_eval_user_data=&observer;
 common_log_set_verbosity_thold(4);auto init=common_init_from_params(params);auto*m=init->model();
 auto cp=common_context_params_to_llama(params);common_log_set_verbosity_thold(3);
 std::cout<<"HS_READY\n"<<std::flush;std::string line;
 while(std::getline(std::cin,line)){
  auto req=pj::parse(line);observer.reset(req);observer.phase="continuation";
  std::string file=req.at("checkpoint");auto j=pilot_load(file);std::string base=file.substr(0,file.size()-5);
  cp.n_ubatch=req.at("recipe").at("ub");cp.n_outputs_max=req.at("recipe").at("outputs_max");cp.n_outputs_max_per_seq=req.at("recipe").at("outputs_max_per_seq");
  auto *ctx=llama_init_from_model(m,cp);if(!ctx)return 3;
  auto bytes=pilot_read(base+".target.kv");auto consumed=llama_state_set_data(ctx,bytes.data(),bytes.size());auto before=prefill_observer::state(ctx);
  if(consumed!=bytes.size()||before!=bytes)throw std::runtime_error("Cross restore roundtrip failed");
  auto *s=pilot_restore_sampler(m,ctx,params.sampling,j.at("target_sampler"));
  llama_batch b=llama_batch_init(512,0,1);pilot_restore_batch(b,req.at("batch"));
  auto pos_before=prefill_observer::positions(ctx);const auto start=ggml_time_us();
  observer.decode(ctx,b,"target");llama_synchronize(ctx);const auto end=ggml_time_us();
  int nv=llama_vocab_n_tokens(llama_model_get_vocab(m));std::vector<float>values;pj scores=pj::array();
  for(int i=0;i<b.n_tokens;i++){auto*l=llama_get_logits_ith(ctx,i);values.insert(values.end(),l,l+nv);scores.push_back(observer.top(ctx,i));}
  auto decision=common_sampler_sample(s,ctx,0);pj decisions=pj::array();
  // Independently sample each observed row under its effective greedy contract.
  // No KV operation, accepted-history mutation, or extra model forward.
  for(int i=0;i<b.n_tokens;i++){auto *clone=pilot_clone(s);decisions.push_back(common_sampler_sample(clone,ctx,i));pilot_free(clone);}
  auto after=prefill_observer::state(ctx);
  pilot_write(observer.path+".logits.f32",values);
  pilot_write(observer.path+".before.kv",before);pilot_write(observer.path+".after.kv",after);
  pj result={{"request_id",req.at("request_id")},{"checkpoint",file},{"batch",pilot_batch(b)},{"recipe",req.at("recipe")},{"consumed_bytes",consumed},{"restore_equal",true},{"source_file_untouched",true},{"position_before",pos_before},{"position_after",prefill_observer::positions(ctx)},{"sampler",pilot_sampler(s,ctx)},{"decision_id",decision},{"row_decision_ids",decisions},{"decision_eog",llama_vocab_is_eog(llama_model_get_vocab(m),decision)},{"rows",scores},{"n_vocab",nv},{"trace",observer.trace},{"forward_ms",(end-start)/1000.0}};
  pilot_json(observer.path,result);llama_batch_free(b);pilot_free(s);llama_free(ctx);
  std::cout<<"HS_RESULT "<<result.dump()<<"\n"<<std::flush;
 }
 return 0;
}
