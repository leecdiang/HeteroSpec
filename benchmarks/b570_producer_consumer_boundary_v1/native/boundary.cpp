// Reuse the frozen observer descriptors and native utilities verbatim. The old
// entry point is never called; the original source and numerical DLLs stay pinned.
#define main historical_formal_main
#include "../../b570_native_reproduction_v1/native/formal.cpp"
#undef main
#include <bcrypt.h>
#include <iomanip>
#include <sstream>

fs::path payload_root;
uint64_t payload_bytes=0;
Clock::time_point request_start;
std::string utc() {
 SYSTEMTIME s; GetSystemTime(&s); char b[40];
 snprintf(b,sizeof(b),"%04d-%02d-%02dT%02d:%02d:%02d.%03dZ",s.wYear,s.wMonth,s.wDay,s.wHour,s.wMinute,s.wSecond,s.wMilliseconds);
 return b;
}
std::string sha(const void* data,size_t size) {
 BCRYPT_ALG_HANDLE alg=nullptr; BCRYPT_HASH_HANDLE hash=nullptr;
 need(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"sha provider");
 DWORD n=0,got=0; need(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&n,sizeof(n),&got,0)==0,"sha length");
 std::vector<unsigned char> object(n),out(32);
 need(BCryptCreateHash(alg,&hash,object.data(),n,nullptr,0,0)==0,"sha create");
 size_t at=0;while(at<size){ULONG chunk=ULONG(std::min<size_t>(size-at,1<<26));need(BCryptHashData(hash,(PUCHAR)data+at,chunk,0)==0,"sha update");at+=chunk;}
 need(BCryptFinishHash(hash,out.data(),32,0)==0,"sha finish"); BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(alg,0);
 std::ostringstream s;for(auto c:out)s<<std::hex<<std::setfill('0')<<std::setw(2)<<int(c);return s.str();
}
std::string hash_json(const json& j){auto s=j.dump();return sha(s.data(),s.size());}
std::vector<uint8_t> bytes(fs::path p){std::ifstream f(p,std::ios::binary);need(bool(f),"read payload");return std::vector<uint8_t>((std::istreambuf_iterator<char>(f)),{});}
json save_bytes(const void* data,size_t n) {
 need(n>0,"empty payload");auto h=sha(data,n);auto rel=fs::path("cas")/h.substr(0,2)/h;
 auto p=payload_root/rel;fs::create_directories(p.parent_path());
 if(fs::exists(p)){auto old=bytes(p);need(old.size()==n&&memcmp(old.data(),data,n)==0,"CAS collision/corruption");}
 else{need(payload_bytes+n<=8589934592ULL,"raw payload budget exhausted");std::ofstream f(p,std::ios::binary);f.write((const char*)data,n);need(bool(f),"save payload");payload_bytes+=n;}
 return {{"path",rel.generic_string()},{"bytes",n},{"sha256",h}};
}
json save_json(const json& j){auto s=j.dump(2)+"\n";return save_bytes(s.data(),s.size());}
json signature(json b){for(auto k:{"kv","initial_logits"})b[k].erase("path");return b;}
std::vector<uint8_t> checked_bytes(const json& m){
 auto rel=fs::path(m.at("path").get<std::string>());need(!rel.is_absolute(),"absolute payload path");
 for(auto part:rel)need(part!="..","payload escape");
 auto v=bytes(payload_root/rel);need(v.size()==m.at("bytes")&&sha(v.data(),v.size())==m.at("sha256"),"payload identity");return v;
}

struct BoundaryObs {
 Obs legacy;
 std::map<std::string,json> producer,ordinary;
 bool bad=false; int q=0;
 static bool cb(ggml_tensor*t,bool ask,void*u){
  auto&o=*static_cast<BoundaryObs*>(u);
  // Preserve the historical verification descriptor inventory exactly.
  if(o.legacy.phase=="VERIFY")return Obs::cb(t,ask,&o.legacy);
  if(!ask)return false;
  std::string name=t->name;
  if(name.rfind("hs_",0)!=0&&name.rfind("kq",0)!=0)return false;
  auto j=Obs::tensor(t);j["op"]=ggml_op_name(t->op);j["sources"]=json::array();
  for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(Obs::tensor(t->src[i]));
  auto*d=t->buffer?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;
  j["device"]=d?ggml_backend_dev_description(d):"UNKNOWN";
  if(!d||std::string(ggml_backend_dev_description(d)).find("B570")==std::string::npos)o.bad=true;
  j["caller_width"]=o.q;
  auto& seen=o.legacy.phase=="PREFILL"?o.producer:o.ordinary;seen[j.dump()]=j;
  return false; // Metadata only; no tensor readback or extra graph execution.
 }
};
struct NativeContext {
 llama_context*c=nullptr;BoundaryObs obs;bool heavy;int nv,calls=0;std::string role;
 json vectors=json::object(),geometry=json::object(),caller_trace=json::array();
 NativeContext(llama_model*m,int ub,bool capture,std::string label):heavy(capture),nv(llama_vocab_n_tokens(llama_model_get_vocab(m))),role(label){
  auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=512;p.n_ubatch=ub;p.n_threads=8;p.n_threads_batch=8;
  p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
  p.cb_eval=BoundaryObs::cb;p.cb_eval_user_data=&obs;
  c=llama_init_from_model(m,p);need(c,"context");
 }
 ~NativeContext(){if(c)llama_free(c);}
 void decode(const std::vector<int>&ids,int pos,bool all,const char*phase,bool last=true){
  cutoff();need(seconds(request_start)<180,"request soft deadline");obs.legacy.phase=phase;obs.q=int(ids.size());
  auto b=llama_batch_init(int(ids.size()),0,1);b.n_tokens=int(ids.size());
  for(int i=0;i<b.n_tokens;i++){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||(last&&i==b.n_tokens-1);}
  int rc=llama_decode(c,b);llama_batch_free(b);need(rc==0,"decode failure");llama_synchronize(c);calls++;
  caller_trace.push_back({{"ids",ids},{"pos",pos},{"phase",phase},{"all_outputs",all},{"final_output",last}});
  if(heavy&&obs.legacy.phase=="VERIFY"){
   json sig=json::array();for(auto&kv:obs.legacy.seen)sig.push_back(kv.second);
   geometry[role+"/decode-"+std::to_string(calls)+".json"]=save_json({{"input_ids",ids},{"pos",pos},{"all_outputs",all},{"signatures",sig},{"placement_ok",!obs.legacy.bad}});
  }
  need(!obs.bad&&!obs.legacy.bad,"placement/observer failure");
 }
 void prefill(const std::vector<int>&ids,const std::vector<int>&schedule){
  size_t pos=0;for(int n:schedule){need((n==1||n==2||n==4)&&pos+n<=ids.size(),"prefill schedule");
   decode(std::vector<int>(ids.begin()+pos,ids.begin()+pos+n),int(pos),false,"PREFILL",pos+n==ids.size());pos+=n;}
  need(pos==ids.size(),"prefill incomplete");
 }
 std::vector<float> logits(int row){float*p=llama_get_logits_ith(c,row);need(p,"logits");std::vector<float>v(p,p+nv);for(float f:v)need(std::isfinite(f),"nonfinite");return v;}
 int sample(const std::vector<float>&v,const std::string&key){need(v.size()==size_t(nv),"vocab extent");for(float f:v)need(std::isfinite(f),"nonfinite initial");if(heavy)vectors[key]=save_bytes(v.data(),v.size()*4);return int(std::max_element(v.begin(),v.end())-v.begin());}
 int sample(int row,const std::string&key){return sample(logits(row),key);}
 void trim(int keep){need(llama_memory_seq_rm(llama_get_memory(c),0,keep,-1),"trim");}
 json boundary(const std::vector<float>&initial){
  llama_synchronize(c);auto size=llama_state_seq_get_size(c,0);std::vector<uint8_t>v(size);
  need(llama_state_seq_get_data(c,v.data(),v.size(),0)==size,"state export length");
  return{{"kv",save_bytes(v.data(),v.size())},{"initial_logits",save_bytes(initial.data(),initial.size()*4)},
   {"kv_min",llama_memory_seq_pos_min(llama_get_memory(c),0)},{"kv_max",llama_memory_seq_pos_max(llama_get_memory(c),0)},{"sequence_id",0}};
 }
 std::vector<float> restore(const json&donor,json&readback){
  need(llama_memory_seq_pos_max(llama_get_memory(c),0)==-1,"receiver not empty");auto kv=checked_bytes(donor.at("kv")),raw=checked_bytes(donor.at("initial_logits"));
  need(raw.size()==size_t(nv)*4,"initial vector length");std::vector<float>v(nv);memcpy(v.data(),raw.data(),raw.size());
  need(llama_state_seq_set_data(c,kv.data(),kv.size(),0)==kv.size(),"state import length");llama_synchronize(c);
  readback=boundary(v);need(signature(readback)==signature(donor),"actual restored boundary differs");return v;
 }
};

json run_request(llama_model*t,llama_model*d,const json&input,const json&slot,const json&donor){
 auto prompt=input.at("prompt_ids").get<std::vector<int>>();auto lengths=slot.at("caller_lengths").get<std::vector<int>>();
 need(hash_json(input.at("prompt_ids"))==slot.at("prompt_ids_sha256"),"actual prompt digest");
 int cap=slot.at("cap");bool heavy=slot.at("observer")=="heavy",spec=slot.at("k")==1,resume=slot.at("route")=="resumed";
 std::string layout=slot.at("consumer")=="QB"?"QB":"PQ";_putenv_s("HS_REQUEST_LAYOUT",layout.c_str());
 NativeContext target(t,slot.at("target_ub"),heavy,"target");std::unique_ptr<NativeContext>draft;
 if(spec)draft=std::make_unique<NativeContext>(d,1,heavy,"draft");
 json out={{"cycles",json::array()},{"checks",{{"device_placement",true},{"actual_geometry",true}}},{"extra_forward_calls_on_restore",0}};
 std::vector<float>initial;
 if(resume){json readback;initial=target.restore(donor.at("boundary"),readback);out["restored_boundary"]=readback;
  out["imported_boundary_sha256"]=hash_json(signature(donor.at("boundary")));out["checks"]["restore_roundtrip"]=true;
 }else{target.prefill(prompt,lengths);initial=target.logits(-1);
  // Capture off/on both export a real boundary; heavy adds all trajectory vectors.
  if(slot.at("route")!="strict_reference")out["boundary"]=target.boundary(initial);
 }
 if(draft)draft->prefill(prompt,std::vector<int>(prompt.size(),1));
 int next=target.sample(initial,"target_initial"),base=int(prompt.size()),cycle=0;
 std::vector<int>ids;std::vector<bool>eog;const auto*v=llama_model_get_vocab(t);
 auto commit=[&](int id){ids.push_back(id);eog.push_back(llama_vocab_is_eog(v,id));return eog.back()||ids.size()==size_t(cap);};
 bool done=commit(next);
 while(!done){
  if(!draft){target.decode({next},base++,false,"ORDINARY");next=target.sample(-1,"target_ordinary/"+std::to_string(ids.size()));done=commit(next);continue;}
  int seed=next;draft->trim(base);draft->decode({seed},base,false,"DRAFT_SYNC");
  int proposal=draft->sample(-1,"draft_proposal/"+std::to_string(cycle));draft->decode({proposal},base+1,false,"PROPOSE");
  target.decode({seed,proposal},base,true,"VERIFY");std::vector<int>decisions;
  for(int j=0;j<2;j++)decisions.push_back(target.sample(j,"target_verify/"+std::to_string(cycle)+"/"+std::to_string(j)));
  int accepted=0;std::vector<int>committed{decisions[0]};done=commit(decisions[0]);bool match=decisions[0]==proposal;
  if(match){accepted=1;if(!done){next=decisions[1];committed.push_back(next);done=commit(next);}}else next=decisions[0];
  int keep=base+1+accepted;target.trim(keep);draft->trim(keep);
  out["cycles"].push_back({{"cycle",cycle},{"base",base},{"batch_ids",{seed,proposal}},{"seed_id",seed},{"proposal",proposal},{"decisions",decisions},
   {"accepted",accepted},{"keep",keep},{"q_caller",2},{"committed_ids",committed},
   {"target_kv_max",llama_memory_seq_pos_max(llama_get_memory(target.c),0)},{"draft_kv_max",llama_memory_seq_pos_max(llama_get_memory(draft->c),0)}});
  base=keep;cycle++;
 }
 out["endpoint"]={{"ids",ids},{"eog",eog},{"length",ids.size()},{"terminal_id",ids.back()},{"stop_reason",eog.back()?"EOG":"CAP"}};
 out["actual_signatures"]=json::array();for(auto&kv:target.obs.legacy.seen)out["actual_signatures"].push_back(kv.second);
 out["producer_signatures"]=json::array();for(auto&kv:target.obs.producer)out["producer_signatures"].push_back(kv.second);
 if(!resume&&slot.at("producer")=="P4T"){
  int found=0;for(auto&kv:target.obs.producer){auto&j=kv.second;std::string name=j["name"];
   if(name.rfind("hs_pq_qk",0)==0){need((j["caller_width"]==2||j["caller_width"]==4)&&(j["ne"][0]==256||j["ne"][0]==512)&&j["ne"][1]==1&&j["ne"][2]==32&&j["ne"][3]==1,"unexpected producer geometry");found++;}}
  need(found>0,"P4T bridge not observed");
 }
 out["ordinary_signatures"]=json::array();for(auto&kv:target.obs.ordinary)out["ordinary_signatures"].push_back(kv.second);
 out["physical_micrograph_histogram"]=nullptr;out["target_calls"]=target.calls;out["draft_calls"]=draft?draft->calls:0;
 out["target_caller_trace"]=target.caller_trace;out["draft_caller_trace"]=draft?draft->caller_trace:json::array();
 out["vectors"]=target.vectors;if(draft)out["vectors"].update(draft->vectors);out["geometry_files"]=target.geometry;
 // Every observed bridge QK must be within the admitted extent; q1 uses upstream.
 if(spec&&cycle){int count=0;for(auto&kv:target.obs.legacy.seen){auto&j=kv.second;std::string name=j["name"];
  if(name.rfind(layout=="QB"?"hs_qb_qk":"hs_pq_qk",0)==0){need((j["ne"][0]==256||j["ne"][0]==512)&&j["ne"][1]==1&&j["ne"][2]==32&&j["ne"][3]==(layout=="QB"?2:1),"unexpected verify geometry");count++;}}
  need(count>0,"layout bridge not observed");}
 out["request_seconds_diagnostic"]=seconds(request_start);out["status"]="COMPLETE_QUALIFIED";return out;
}

int main(int argc,char**argv){
 whole=Clock::now();deadline=890;llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;json result={{"status","STARTED"},{"requests",json::array()}};
 auto cleanup=[&](){if(d)llama_model_free(d);if(t)llama_model_free(t);d=t=nullptr;if(initialized)llama_backend_free();initialized=false;};
 try{
  need(argc==6,"boundary OUTPUT TARGET DRAFT PANEL SLOTS");root=argv[1];need(!fs::exists(root),"fresh output required");fs::create_directories(root);
  json panel,job;std::ifstream(argv[4])>>panel;std::ifstream(argv[5])>>job;payload_root=job.at("payload_root").get<std::string>();fs::create_directories(payload_root);
  for(auto&e:fs::recursive_directory_iterator(payload_root))if(e.is_regular_file())payload_bytes+=e.file_size();
  need(job.at("slots").size()>0&&job.at("slots").size()<=16,"one input worker");
  dump(root/"result.json",result);llama_backend_init();initialized=true;ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("B570")!=std::string::npos){need(!gpu,"ambiguous B570");gpu=x;}}
  need(gpu,"B570 absent");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*){return seconds(whole)<890;};t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");
  const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  json eogs=json::array();for(int i=0;i<llama_vocab_n_tokens(tv);i++){need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab identity");if(llama_vocab_is_eog(tv,i))eogs.push_back(i);}
  need(eogs==job.at("eog_ids")&&llama_vocab_n_tokens(tv)==job.at("vocabulary_size"),"frozen vocabulary");
  std::map<std::string,json>completed;
  for(auto&slot:job.at("slots")){
   std::string sid=slot.at("slot_id");json row={{"slot_id",sid},{"attempt",0},{"status","STARTED"},{"native_started",true},{"pid",GetCurrentProcessId()},
    {"started_utc",utc()},{"runtime_sha256",job.at("runtime_sha256")},{"prompt_ids_sha256",slot.at("prompt_ids_sha256")},{"performance_eligible",false},{"reason","native request entered"}};
   result["active_request"]=row;dump(root/"result.json",result);request_start=Clock::now();
   try{
    auto input=panel.at(slot.at("input_id").get<std::string>());auto prompt=input.at("prompt_ids").get<std::vector<int>>();
    need(!prompt.empty()&&prompt.size()+int(slot.at("cap"))+2<512,"input extent");for(int id:prompt)need(id>=0&&id<llama_vocab_n_tokens(tv),"input vocabulary");
    json donor;if(!slot.at("donor_slot_id").is_null())donor=completed.at(slot.at("donor_slot_id").get<std::string>());
    row.update(run_request(t,d,input,slot,donor));row.erase("reason");row["finished_utc"]=utc();
    if(!slot.at("compare_slot_id").is_null()){
     const auto&other=completed.at(slot.at("compare_slot_id").get<std::string>());need(row.at("endpoint")==other.at("endpoint")&&row.at("cycles")==other.at("cycles"),"observer/own-path endpoint-cycle sham failed");
     if(!row.at("vectors").empty()&&!other.at("vectors").empty())need(row.at("vectors")==other.at("vectors"),"own-path vector sham failed");
    }
    if(!slot.at("producer_match_slot_id").is_null())need(signature(row.at("boundary"))==signature(completed.at(slot.at("producer_match_slot_id").get<std::string>()).at("boundary")),"natural-spec producer mismatch");
    completed[sid]=row;result["requests"].push_back(row);result.erase("active_request");dump(root/"result.json",result);
   }catch(const std::exception&e){row["status"]="TECHNICAL_FAILURE";row["reason"]=e.what();row["finished_utc"]=utc();result["requests"].push_back(row);result.erase("active_request");throw;}
  }
  cleanup();result["status"]="WORKER_COMPLETE";result["normal_cleanup_returned"]=true;dump(root/"result.json",result);return 0;
 }catch(const std::exception&e){cleanup();result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();result["normal_cleanup_returned"]=true;if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<"\n";return 2;}
}
