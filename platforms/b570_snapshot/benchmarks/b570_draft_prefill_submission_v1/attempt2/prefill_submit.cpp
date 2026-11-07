#define NOMINMAX
#include <windows.h>
#include "llama.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <map>
#include <chrono>
#include <cmath>
#include <cstring>
#include <memory>
using json=nlohmann::json;namespace fs=std::filesystem;using Clock=std::chrono::steady_clock;
void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
void dump(fs::path p,const json&j){std::ofstream f(p);f<<j.dump(2)<<"\n";need(bool(f),"write JSON");}
bool bulk_prefill=false;
Clock::time_point whole;double deadline=230;void cutoff(){need(seconds(whole)<deadline,"internal deadline");}
struct Obs{
 int prefill_q_max=0,prefill_q_nodes=0;std::map<std::string,json>prefill_shapes;
 std::string phase="setup";bool bad=false;int requests=0;std::map<std::string,json>seen;
 static json tensor(ggml_tensor*t){return{{"name",t->name},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"type",ggml_type_name(t->type)}};}
 static bool cb(ggml_tensor*t,bool ask,void*u){
  auto&o=*static_cast<Obs*>(u);if(!ask){o.bad=true;return true;}
  if(o.phase=="PREFILL"){
   std::string name=t->name;
   if(name.rfind("Qcur",0)==0||name.rfind("kq-",0)==0){auto j=tensor(t);j["op"]=ggml_op_name(t->op);o.prefill_shapes[j.dump()]=j;}
   if(name.rfind("kq-",0)==0&&t->op==GGML_OP_MUL_MAT){o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[1]));o.prefill_q_nodes++;}
  }
  if(o.phase!="VERIFY")return false;
  std::string name=t->name;if(name.rfind("hs_",0)!=0&&name.rfind("kq",0)!=0)return false;
  auto j=tensor(t);j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
  for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(tensor(t->src[i]));
  auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
  j["device"]=d?ggml_backend_dev_description(d):"UNKNOWN";
  if(!d||std::string(ggml_backend_dev_description(d)).find("B570")==std::string::npos)o.bad=true;
  auto key=j.dump();o.seen[key]=j;o.requests++;return false;
 }
};
struct Context{
 llama_context*c=nullptr;Obs obs;int nv;fs::path dir;bool capture;int calls=0;std::map<std::string,double> decode_seconds;
 Context(llama_model*m,int ub,fs::path path,bool cap):nv(llama_vocab_n_tokens(llama_model_get_vocab(m))),dir(path),capture(cap){
  auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=512;p.n_ubatch=ub;p.n_threads=8;p.n_threads_batch=8;
  p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
  if(cap){p.cb_eval=Obs::cb;p.cb_eval_user_data=&obs;}
  c=llama_init_from_model(m,p);need(c,"context");if(cap)fs::create_directories(dir);
 }
 ~Context(){if(c)llama_free(c);}
 void decode(const std::vector<int>&ids,int pos,bool all,const char*phase,bool last=true){
  cutoff();obs.phase=phase;auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
  for(int i=0;i<b.n_tokens;i++){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||(last&&i==b.n_tokens-1);}
  auto decode_start=Clock::now();int rc=llama_decode(c,b);llama_batch_free(b);need(rc==0,"decode failure");llama_synchronize(c);decode_seconds[phase]+=seconds(decode_start);calls++;
  if(capture&&obs.phase=="VERIFY"){json sig=json::array();for(auto&kv:obs.seen)sig.push_back(kv.second);dump(dir/("decode-"+std::to_string(calls)+".json"),{{"input_ids",ids},{"pos",pos},{"all_outputs",all},{"signatures",sig},{"placement_ok",!obs.bad}});}
  need(!obs.bad,"placement/observer failure");
 }
 void prefill(const std::vector<int>&ids){for(size_t i=0;i<ids.size();i++)decode({ids[i]},int(i),false,"PREFILL",i+1==ids.size());}
 std::vector<float> logits(int row,std::string name){
  float*p=llama_get_logits_ith(c,row);need(p,"logits");std::vector<float>v(p,p+nv);
  for(float f:v)need(std::isfinite(f),"nonfinite logit");
  if(capture){std::ofstream f(dir/(name+".f32"),std::ios::binary);f.write((char*)v.data(),v.size()*4);need(bool(f),"logits save");}
  return v;
 }
 int sample(int row,std::string name){auto v=logits(row,name);return int(std::max_element(v.begin(),v.end())-v.begin());}
 void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"trim");}
};
struct Output{json record;std::vector<int>ids;std::vector<bool>eog;};
Output request(llama_model*t,llama_model*d,const std::vector<int>&prompt,std::string arm,fs::path dir,bool capture,int cap){
 _putenv_s("HS_REQUEST_LAYOUT",arm=="QB"?"QB":"PQ");
 Context target(t,arm=="R"?1:4,dir/"target",capture);
 std::unique_ptr<Context>draft;if(arm!="R")draft=std::make_unique<Context>(d,1,dir/"draft",capture);
 Output o;o.record={{"arm",arm},{"capture",capture},{"cycles",json::array()}};
 const auto*v=llama_model_get_vocab(t);auto start=Clock::now();
 target.prefill(prompt);if(draft){if(bulk_prefill)draft->decode(prompt,0,false,"PREFILL");else draft->prefill(prompt);}
 int next=target.sample(-1,"initial"),base=int(prompt.size()),cycle=0;
 auto commit=[&](int id){o.ids.push_back(id);o.eog.push_back(llama_vocab_is_eog(v,id));return o.eog.back()||o.ids.size()==size_t(cap);};
 bool done=commit(next);
 while(!done){
  cutoff();
  if(!draft){target.decode({next},base++,false,"ORDINARY");next=target.sample(-1,"ordinary-"+std::to_string(o.ids.size()));done=commit(next);continue;}
  int seed=next;draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
  int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle));
  draft->decode({proposal},base+1,false,"PROPOSE");
  target.decode({seed,proposal},base,true,"VERIFY");
  // Preserve every verification row, including the row discarded on rejection.
  std::vector<int>decisions;for(int j=0;j<2;j++)decisions.push_back(target.sample(j,"verify-"+std::to_string(cycle)+"-"+std::to_string(j)));
  int accepted=0;done=commit(decisions[0]);bool match=decisions[0]==proposal;
  if(match){accepted=1;if(!done){next=decisions[1];done=commit(next);}}
  else next=decisions[0];
  int keep=base+1+accepted;target.trim(keep);draft->trim(keep);
  o.record["cycles"].push_back({{"cycle",cycle},{"base",base},{"batch_ids",{seed,proposal}},
   {"seed_id",seed},{"proposal",proposal},{"decisions",decisions},{"accepted",accepted},{"keep",keep},
   {"q_caller",2},{"target_kv_max",llama_memory_seq_pos_max(llama_get_memory(target.c),0)},
   {"draft_kv_max",llama_memory_seq_pos_max(llama_get_memory(draft->c),0)}});
  base=keep;cycle++;
  if(capture){o.record["partial_ids"]=o.ids;o.record["partial_eog"]=o.eog;dump(dir/"progress.json",o.record);}
 }
 llama_synchronize(target.c);if(draft)llama_synchronize(draft->c);
 o.record["request_seconds"]=seconds(start);o.record["ids"]=o.ids;o.record["eog"]=o.eog;o.record["length"]=o.ids.size();
 o.record["terminal_id"]=o.ids.back();o.record["stop_reason"]=o.eog.back()?"EOG":"CAP";o.record["actual_signatures"]=json::array();
 for(auto&kv:target.obs.seen)o.record["actual_signatures"].push_back(kv.second);
 if(capture&&draft){
  need(target.obs.requests>0,"no verification geometry");bool found=false;
  for(auto&kv:target.obs.seen){auto&j=kv.second;std::string name=j["name"];
   if(name.rfind(arm=="QB"?"hs_qb_qk":"hs_pq_qk",0)==0){
    need((j["ne"][0]==256||j["ne"][0]==512)&&j["ne"][1]==1&&j["ne"][2]==32&&j["ne"][3]==(arm=="QB"?2:1),"unexpected actual geometry");
    found=true;}}
  need(found,"requested layout not integrated");
 }
 o.record["target_decode_seconds"]=target.decode_seconds;o.record["draft_decode_seconds"]=draft?json(draft->decode_seconds):json::object();
 if(capture&&draft){json shapes=json::array();for(auto&kv:draft->obs.prefill_shapes)shapes.push_back(kv.second);
 dump(dir/"draft-prefill-shapes.json",{{"q_max",draft->obs.prefill_q_max},{"observations",draft->obs.prefill_q_nodes},{"shapes",shapes}});
 need(draft->obs.prefill_q_max==1&&draft->obs.prefill_q_nodes>0,"draft prefill physical q admission");}
 o.record["draft_prefill_q_observed"]=draft?draft->obs.prefill_q_max:0;
 o.record["draft_prefill_q_node_observations"]=draft?draft->obs.prefill_q_nodes:0;
 o.record["draft_prefill_api_calls"]=draft?(bulk_prefill?1:int(prompt.size())):0;o.record["draft_microbatch_limit"]=1;o.record["target_calls"]=target.calls;o.record["draft_calls"]=draft?draft->calls:0;
 return o;
}
void equivalent(const json&a,const json&b,bool trace){
 for(auto k:{"ids","eog","length","terminal_id","stop_reason"})need(a.at(k)==b.at(k),"reference endpoint mismatch");
 if(trace)need(a.at("cycles")==b.at("cycles"),"reference state mismatch");
}
int main(int argc,char**argv){
 whole=Clock::now();llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;
 json result={{"status","STARTED"},{"requests",json::array()}};
 auto cleanup=[&](){if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
 try{
  need(argc==8,"prefill_submit OUTPUT TARGET DRAFT PANEL MODE INDEX STUDY_ROOT");
  root=argv[1];need(!fs::exists(root),"fresh output");fs::create_directories(root);
  std::ifstream fi(argv[4]);json panel;fi>>panel;std::string mode=argv[5];int index=std::stoi(argv[6]);fs::path study=argv[7];
  need((mode=="qual"||mode=="time")&&index>=0&&index<4,"mode/index");deadline=mode=="qual"?170:290;
  result["mode"]=mode;result["index"]=index;dump(root/"result.json",result);
  llama_backend_init();initialized=true;ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("B570")!=std::string::npos){need(!gpu,"ambiguous");gpu=x;}}
  need(gpu,"B570 absent");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*){return seconds(whole)<deadline;};
  auto ls=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");
  result["model_load_seconds"]=seconds(ls);
  const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);
  need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab");
  auto run=[&](const json&input,std::string label,bool capture,std::string category){
   bulk_prefill=label=="BULK1";std::string arm=label=="R"?"R":"QB";
   auto prompt=input["prompt_ids"].get<std::vector<int>>();need(prompt.size()+int(input["cap"])+2<512,"extent");
   auto st=Clock::now();auto o=request(t,d,prompt,arm,root/(category+"-"+std::to_string(result["requests"].size())),capture,int(input["cap"]));
   o.record["service_seconds"]=seconds(st);o.record["label"]=label;o.record["input_id"]=input["id"];o.record["category"]=category;
   result["requests"].push_back(o.record);dump(root/"result.json",result);return o.record;
  };
  fs::path prior="C:/hs/b570-formal-request-20261020";
  if(mode=="qual"){
   auto x=run(panel["inputs"][index],"BULK1",true,"qual");
   auto old=prior/("qual-"+std::to_string(index));std::ifstream f(old/"result.json");json ref;f>>ref;
   need(ref["status"]=="QUALIFICATION_PASS","prior qualification");
   equivalent(ref["requests"][2],x,true);
   int matched=0;
   for(auto&e:fs::recursive_directory_iterator(old/"qual-2"))if(e.is_regular_file()&&e.path().extension()==".f32"){
    auto rel=fs::relative(e.path(),old/"qual-2");std::ifstream a(e.path(),std::ios::binary),b(root/"qual-0"/rel,std::ios::binary);
    std::vector<char>aa((std::istreambuf_iterator<char>(a)),{}),bb((std::istreambuf_iterator<char>(b)),{});
    need(!aa.empty()&&aa==bb,"historical QB full logits byte mismatch");matched++;
   }
   int actual=0;for(auto&e:fs::recursive_directory_iterator(root/"qual-0"))if(e.is_regular_file()&&e.path().extension()==".f32")actual++;
   need(matched==actual&&actual>0,"raw inventory");
   result["historical_full_logits_matched"]=matched;result["status"]="QUALIFICATION_PASS";
  }else{
   std::vector<std::vector<std::string>>orders={{"BASE_A","BASE_B","BULK1"},{"BASE_B","BULK1","BASE_A"},{"BULK1","BASE_A","BASE_B"}};need(index<3,"timing session");
   std::ifstream f("C:/hs/b570-spec-bridge-20261020200000/results/result.json");json warm;f>>warm;
   for(auto label:orders[index]){auto x=run(panel["warmup"],label,false,"warmup");equivalent(warm["requests"][label=="R"?0:2],x,label!="R");}
   for(int j=0;j<2;j++){
    int task=2*((index+j)%2);std::ifstream f(prior/("qual-"+std::to_string(task))/"result.json");json ref;f>>ref;
    std::ifstream gate(study/("qual-"+std::to_string(task))/"result.json");json g;gate>>g;need(g["status"]=="QUALIFICATION_PASS","candidate not qualified");
    for(auto label:orders[index]){
     auto x=run(panel["inputs"][task],label,false,"steady");equivalent(ref["requests"][label=="R"?0:2],x,label!="R");
    }
   }
   result["status"]="TIMING_PASS";
  }
  cleanup();result["normal_cleanup_returned"]=true;dump(root/"result.json",result);return 0;
 }catch(const std::exception&e){result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<"\n";return 2;}
}
