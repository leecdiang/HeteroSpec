#include <set>
#define main pinned_fixture_unused_main
#include "pinned_fixture.cpp"
#undef main
#include <chrono>
#include <sys/resource.h>
#include <unistd.h>
using Clock=std::chrono::steady_clock;
static double sec(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static J read_json(const std::string&p){std::ifstream f(p);need(bool(f),"input open");J j;f>>j;return j;}
static int integer(const J& j,const char* key,int lo,int hi){const auto&v=j.at(key);need(v.is_number_integer()&&!v.is_boolean(),"integer field type");auto x=v.get<int64_t>();need(x>=lo&&x<=hi,"integer field range");return int(x);}
static void keys(const J&j,std::initializer_list<const char*> names){need(j.is_object(),"object required");std::set<std::string> allowed;for(auto n:names)allowed.insert(n);for(auto it=j.begin();it!=j.end();++it)need(allowed.count(it.key()),"unknown configuration field");}
static void token_list(const J&v,size_t lo,size_t hi){need(v.is_array()&&v.size()>=lo&&v.size()<=hi,"token list extent");for(const auto&x:v)need(x.is_number_integer()&&!x.is_boolean()&&x.get<int64_t>()>=0&&x.get<int64_t>()<128,"token ID type/range");}
static void validate(const J&cfg,const std::string&mode){
 need(mode=="candidate"||mode=="reference"||mode=="free","unknown mode");token_list(cfg.at("prompt_ids"),7,7);
 if(mode=="reference"){
  keys(cfg,{"prompt_ids","jobs"});need(cfg.at("jobs").is_array()&&!cfg.at("jobs").empty()&&cfg.at("jobs").size()<=128,"job inventory");std::set<std::string> js,qs;
  for(const auto&job:cfg.at("jobs")){keys(job,{"job_id","tokens","queries"});need(job.at("job_id").is_string(),"job id type");auto id=job.at("job_id").get<std::string>();need(!id.empty()&&js.insert(id).second,"duplicate/empty job");token_list(job.at("tokens"),7,32);need(job.at("queries").is_array()&&!job.at("queries").empty(),"queries required");
   for(const auto&q:job.at("queries")){keys(q,{"query_id","length","state_required"});need(q.at("query_id").is_string(),"query id type");auto qid=q.at("query_id").get<std::string>();need(!qid.empty()&&qs.insert(qid).second,"duplicate/empty query");integer(q,"length",7,job.at("tokens").size());need(q.at("state_required").is_boolean(),"state flag type");}
  }
 }else{keys(cfg,mode=="free"?std::initializer_list<const char*>{"prompt_ids","cap","stop_after_output_index"}:std::initializer_list<const char*>{"prompt_ids","cap","stop_after_output_index","draft_ubatch","forced_reject_index"});int cap=integer(cfg,"cap",1,9);integer(cfg,"stop_after_output_index",0,cap);if(mode=="candidate"){int u=integer(cfg,"draft_ubatch",1,4);need(u!=3,"draft ubatch must be 1,2,4");integer(cfg,"forced_reject_index",-1,3);}}
}
struct Capture {
 std::filesystem::path dir;int serial=0,calls=0,tokens=0;size_t written=0;double decode_seconds=0,state_seconds=0,write_seconds=0;J execution=J::array();
 explicit Capture(const std::string&p):dir(p){need(!std::filesystem::exists(dir),"fresh output directory required");std::filesystem::create_directory(dir);}
 template<class T> J save(const std::vector<T>&v,const char*kind){auto t=Clock::now();std::string path=std::to_string(serial++)+"-"+kind+".bin";std::ofstream f(dir/path,std::ios::binary);f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));f.flush();need(bool(f),"payload write");written+=v.size()*sizeof(T);write_seconds+=sec(t);return {{"path",path},{"bytes",v.size()*sizeof(T)}};}
 void decode(Ctx&c,const std::vector<int>&ids,int pos,bool all,const std::string&role){auto t=Clock::now();c.decode(ids,pos,all);decode_seconds+=sec(t);++calls;tokens+=ids.size();std::vector<bool>mask(ids.size(),all);mask.back()=true;execution.push_back({{"role",role},{"tokens",ids},{"base",pos},{"caller_width",ids.size()},{"physical_ubatch_capacity",llama_n_ubatch(c.c)},{"actual_n_ctx",llama_n_ctx(c.c)},{"actual_n_ctx_seq",llama_n_ctx_seq(c.c)},{"actual_n_batch",llama_n_batch(c.c)},{"logits_mask",mask}});}
 J snapshot(Ctx&c,const std::vector<int>&prefix,const std::vector<float>&frontier,const std::vector<int>&unconsumed,bool done){auto t=Clock::now();llama_synchronize(c.c);auto state=c.state();state_seconds+=sec(t);return {{"tokens",prefix},{"next_position",prefix.size()},{"sequence_id",0},{"kv_min",llama_memory_seq_pos_min(llama_get_memory(c.c),0)},{"kv_max",llama_memory_seq_pos_max(llama_get_memory(c.c),0)},{"serialized_sequence",save(state,"sequence")},{"frontier_logits",save(frontier,"frontier")},{"unmaterialized_output",unconsumed},{"pending_for_next_loop",done?J(nullptr):J(unconsumed.at(0))},{"done",done}};}
 J metrics(){struct rusage ru{};getrusage(RUSAGE_SELF,&ru);return {{"native_decode_calls",calls},{"decoded_tokens",tokens},{"decode_wall_seconds",decode_seconds},{"state_export_wall_seconds",state_seconds},{"payload_write_wall_seconds",write_seconds},{"raw_payload_bytes_written",written},{"peak_rss_kib_linux",ru.ru_maxrss}};}
};
static std::vector<float> forced(Ctx&unused,llama_model*m,const std::vector<int>&prefix,int prompt_length,Capture&cap){(void)unused;Ctx fresh(m,1,4);cap.decode(fresh,std::vector<int>(prefix.begin(),prefix.begin()+prompt_length),0,false,"proposal_control_prefill");for(size_t i=prompt_length;i<prefix.size();++i)cap.decode(fresh,{prefix[i]},i,false,"proposal_control_scalar");return fresh.logits();}
static J candidate(llama_model*m,const J&cfg,Capture&cap){
 auto prompt=cfg.at("prompt_ids").get<std::vector<int>>();int limit=cfg.at("cap"),reject=cfg.at("forced_reject_index"),dub=cfg.at("draft_ubatch"),stop=cfg.value("stop_after_output_index",0);
 need(limit>0&&limit<=9&&prompt.size()==7&&dub>=1&&dub<=4&&reject>=-1&&reject<=3,"bounded candidate fixture");
 Ctx target(m,1,4),draft(m,dub,1);cap.decode(target,prompt,0,false,"candidate_target_prefill");cap.decode(draft,prompt,0,false,"candidate_draft_prefill");
 auto initial=target.logits();int pending=argmax(initial),base=prompt.size();std::vector<int>ids{pending},history=prompt;bool done=limit==1||stop==1||false;
 J result={{"rows",J::object()},{"commits",J::object()},{"cycles",J::array()}};result["rows"]["initial"]={{"logits",cap.save(initial,"logits")},{"tokens",prompt},{"call_tokens",prompt},{"base",0},{"row",prompt.size()-1},{"all",false}};
 result["commits"]["initial"]=cap.snapshot(target,history,initial,{pending},done);
 for(int cycle=0;!done;++cycle){need(cycle<limit,"cycle bound");int seed=pending;draft.trim(base);cap.decode(draft,{seed},base,false,"draft_sync");std::vector<int>props,work=history;work.push_back(seed);
  for(int j=0;j<3;++j){int proposal=draft.sample();if(reject>=0){proposal=argmax(forced(target,m,work,prompt.size(),cap));if(j==reject)proposal=(proposal+1)%draft.nv;}props.push_back(proposal);cap.decode(draft,{proposal},base+1+j,false,"draft_propose");work.push_back(proposal);}
  auto verify=props;verify.insert(verify.begin(),seed);cap.decode(target,verify,base,true,"candidate_target_verify");std::vector<int>decisions;std::vector<std::vector<float>>vectors;
  for(int row=0;row<4;++row){vectors.push_back(target.logits(row));decisions.push_back(argmax(vectors.back()));auto prefix=history;prefix.insert(prefix.end(),verify.begin(),verify.begin()+row+1);result["rows"]["cycle-"+std::to_string(cycle)+"-row-"+std::to_string(row)]={{"logits",cap.save(vectors.back(),"logits")},{"tokens",prefix},{"call_tokens",verify},{"base",base},{"row",row},{"all",true}};}
  int accepted=0;std::string last;auto emit=[&](int t){ids.push_back(t);done=int(ids.size())==limit||int(ids.size())==stop||false;};
  for(int j=0;j<3&&!done;++j){if(decisions[j]==props[j]){++accepted;emit(props[j]);last="accepted";}else{pending=decisions[j];emit(pending);last="correction";break;}}
  if(accepted==3&&!done){pending=decisions[3];emit(pending);last="bonus";}
  int keep=base+1+accepted;target.trim(keep);draft.trim(keep);history.insert(history.end(),verify.begin(),verify.begin()+1+accepted);
  std::vector<int>left;if(last!="accepted")left.push_back(ids.back());
  auto expected=prompt;expected.insert(expected.end(),ids.begin(),ids.end()-(left.empty()?0:1));need(expected==history,"independent output frontier mismatch");
  result["commits"]["cycle-"+std::to_string(cycle)]=cap.snapshot(target,history,vectors[accepted],left,done);
  result["cycles"].push_back({{"base",base},{"seed",seed},{"proposals",props},{"decisions",decisions},{"accepted",accepted},{"keep",keep},{"last",last},{"pending",done?J(nullptr):J(pending)}});base=keep;
 }
 result["case"]={{"ids",ids},{"cycles",result["cycles"]},{"cap",limit},{"target_ubatch",1},{"forced_reject_index",reject},{"stop_after_output_index",stop},{"stop_is_synthetic_eog_predicate",true}};return result;
}
static J reference(llama_model*m,const J&cfg,Capture&cap,bool autonomous){
 auto prompt=cfg.at("prompt_ids").get<std::vector<int>>();J result={{"jobs",J::object()}};
 if(!autonomous)for(const auto&job:cfg.at("jobs")){Ctx ctx(m,1,4);need(llama_memory_seq_pos_max(llama_get_memory(ctx.c),0)==-1,"reference not empty");auto tokens=job.at("tokens").get<std::vector<int>>();need(tokens.size()>=prompt.size()&&std::equal(prompt.begin(),prompt.end(),tokens.begin()),"reference prompt differs");J observations=J::object();size_t call_start=cap.execution.size();
  cap.decode(ctx,prompt,0,false,"reference_prefill");
  for(size_t n=prompt.size();; ++n){
   if(n>prompt.size())cap.decode(ctx,{tokens[n-1]},n-1,false,"reference_scalar");
   for(const auto&q:job.at("queries")){if(q.at("length")==n){J ob={{"tokens",std::vector<int>(tokens.begin(),tokens.begin()+n)},{"logits",cap.save(ctx.logits(),"reference-logits")}};if(q.at("state_required").get<bool>()){auto st=Clock::now();auto raw=ctx.state();cap.state_seconds+=sec(st);ob["serialized_sequence"]=cap.save(raw,"reference-sequence");}observations[q.at("query_id").get<std::string>()]=ob;}}
   if(n==tokens.size())break;
  }
  result["jobs"][job.at("job_id").get<std::string>()]={{"observations",observations},{"tokens",tokens},{"execution_start",call_start},{"execution_end",cap.execution.size()}};
 }
 if(!autonomous)return result;
 // Autonomous run uses no candidate output tape; its only inputs are prompt
 // and stop contract. Fresh context uses the same fixed whole-prompt producer.
 Ctx free(m,1,4);need(llama_memory_seq_pos_max(llama_get_memory(free.c),0)==-1,"free context not empty");auto prefix=prompt;cap.decode(free,prompt,0,false,"free_prefill");J vectors=J::array(),prefixes=J::array();std::vector<int>out;int limit=cfg.at("cap"),stop=cfg.value("stop_after_output_index",0);
 for(int i=0;i<limit;++i){auto v=free.logits();int token=argmax(v);out.push_back(token);vectors.push_back(cap.save(v,"free-logits"));prefixes.push_back(prefix);if(int(out.size())==limit||int(out.size())==stop||false)break;cap.decode(free,{token},prefix.size(),false,"free_scalar");prefix.push_back(token);}
 std::vector<bool>eog;for(int t:out)eog.push_back(false);
 result["free"]={{"eog_flags",eog},{"output",out},{"logits",vectors},{"prefixes",prefixes},{"decoded_tokens",prefix}};return result;
}
int main(int argc,char**argv){auto start=Clock::now();try{need(argc==5,"bridge MODE MODEL CONFIG OUTPUT");std::string mode=argv[1];auto cfg=read_json(argv[3]);validate(cfg,mode);Capture cap(argv[4]);llama_backend_init();auto mp=llama_model_default_params();mp.n_gpu_layers=0;std::unique_ptr<llama_model,decltype(&llama_model_free)>m(llama_model_load_from_file(argv[2],mp),llama_model_free);need(bool(m),"load model");need(llama_vocab_type(llama_model_get_vocab(m.get()))==LLAMA_VOCAB_TYPE_NONE&&llama_vocab_n_tokens(llama_model_get_vocab(m.get()))==128,"only pinned synthetic token-ID namespace supported");J r;if(mode=="candidate")r=candidate(m.get(),cfg,cap);else{need(mode=="reference"||mode=="free","unknown mode");r=reference(m.get(),cfg,cap,mode=="free");}r["execution"]=cap.execution;r["metrics"]=cap.metrics();r["metrics"]["native_total_wall_seconds"]=sec(start);r["vocab"]=llama_vocab_n_tokens(llama_model_get_vocab(m.get()));r["eog_ids"]=J::array();r["tokenizer"]={{"kind","SYNTHETIC_ID_NAMESPACE_NO_TOKENIZER"},{"vocab_type","NONE"},{"vocab_size",128},{"natural_eog_supported",false}};r["pid"]=getpid();r["loaded_mapping_paths"]=J::array();std::ifstream maps("/proc/self/maps");std::string line;while(std::getline(maps,line)){auto at=line.find('/');if(at!=std::string::npos)r["loaded_mapping_paths"].push_back(line.substr(at));}r["status"]="COMPLETED";std::ofstream f(cap.dir/"capture.json");f<<r.dump(2)<<'\n';need(bool(f),"result write");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
