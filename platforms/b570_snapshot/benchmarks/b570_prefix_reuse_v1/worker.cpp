#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include "llama.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <memory>
#include <chrono>
#include <algorithm>
#include <map>
#include <iomanip>
#include <sstream>
#include <cmath>
namespace fs=std::filesystem;
using json=nlohmann::json;
using clock_t_tp=std::chrono::steady_clock;
using stamp=clock_t_tp::time_point;
static double sec(stamp t){return std::chrono::duration<double>(clock_t_tp::now()-t).count();}
static void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
static json read(fs::path p){std::ifstream f(p);need(bool(f),"open json");json j;f>>j;return j;}
static void save(fs::path p,const json&j){std::ofstream f(p);f<<j.dump(1)<<'\n';need(bool(f),"write json");}
static std::vector<uint8_t> bytes(fs::path p){std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"read bytes");std::vector<uint8_t> v(size_t(f.tellg()));f.seekg(0);f.read((char*)v.data(),v.size());need(bool(f),"short read");return v;}
static void put(fs::path p,const void*v,size_t n){fs::create_directories(p.parent_path());std::ofstream f(p,std::ios::binary);f.write((const char*)v,n);need(bool(f),"write bytes");}
static std::string hash(const void *v,size_t n){
 BCRYPT_ALG_HANDLE a=nullptr;need(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"sha provider");
 unsigned char digest[32];need(n<UINT32_MAX&&BCryptHash(a,nullptr,0,(PUCHAR)v,ULONG(n),digest,32)==0,"sha");BCryptCloseAlgorithmProvider(a,0);
 std::ostringstream s;for(auto x:digest)s<<std::hex<<std::setw(2)<<std::setfill('0')<<int(x);return s.str();
}
static json job;static fs::path root;static ggml_backend_dev_t device;
static size_t free_gpu_min=SIZE_MAX,free_ram_min=SIZE_MAX;
static void capacity(){
 size_t f=0,total=0;ggml_backend_dev_memory(device,&f,&total);MEMORYSTATUSEX m{};m.dwLength=sizeof(m);need(GlobalMemoryStatusEx(&m),"RAM");
 if(job.value("capacity_trace",false) || f>total || f<128ULL*1024*1024)std::cerr<<"TP_CAPACITY raw_free="<<f<<" total="<<total<<" ram="<<m.ullAvailPhys<<std::endl;
 free_gpu_min=std::min(free_gpu_min,f);free_ram_min=std::min(free_ram_min,size_t(m.ullAvailPhys));
 need(f<=total && f>=128ULL*1024*1024,"128 MiB device reserve");need(m.ullAvailPhys>=2ULL*1024*1024*1024,"2 GiB host reserve");
}
#ifdef CAND
extern "C" LLAMA_API void hs_b570_set_layout(int);
extern "C" LLAMA_API void hs_b570_set_reference_q8(bool);
extern "C" LLAMA_API void hs_b570_set_prefix_extent(bool);
extern "C" LLAMA_API int hs_parallel_groups(llama_context*,uint32_t,uint32_t*,uint32_t*);
extern "C" LLAMA_API int hs_prefix_allocator_census(llama_context*,uint32_t,uint32_t*,uint32_t*);
extern "C" LLAMA_API const char* hs_b570_tensor_backend(llama_context*,ggml_tensor*);
#endif
struct scope {
 scope(const std::string&arm){
#ifdef CAND
  const int mode=arm=="FAST"?0:arm=="PQ"||arm=="S1"?1:2;
  hs_b570_set_layout(mode);hs_b570_set_reference_q8(mode!=0);
  hs_b570_set_prefix_extent(arm=="PQ"||arm=="QB");
#endif
 }
 ~scope(){
#ifdef CAND
  hs_b570_set_prefix_extent(false);hs_b570_set_reference_q8(false);hs_b570_set_layout(0);
#endif
 }
};
struct ctx {
 llama_context*c=nullptr;int nv=0,capacity_n,ub;bool trace;json nodes=json::array();int pos=0,width=0,calls=0;
 static bool callback(ggml_tensor*t,bool ask,void*u){
  auto &x=*static_cast<ctx*>(u);
  const std::string name=t->name;
  const bool dump=job.value("capture",false) && name.size()>2 && name.substr(name.size()-2)=="-0" &&
      (name.rfind("hs_",0)==0 || name.rfind("kq",0)==0 || name.rfind("Qcur",0)==0 || name.rfind("ffn_out",0)==0);
  if(!ask){
   if(dump){
    std::vector<uint8_t> data(ggml_nbytes(t));ggml_backend_tensor_get(t,data.data(),0,data.size());
    const auto file="capture-"+std::to_string(x.nodes.size())+"-"+name+".bin";
    put(root/file,data.data(),data.size());x.nodes.push_back({{"capture",file},{"name",name},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"type",ggml_type_name(t->type)}});
   }
   return true;
  }
  if(t->op!=GGML_OP_MUL_MAT && t->op!=GGML_OP_CONCAT && t->op!=GGML_OP_CONT && t->op!=GGML_OP_SOFT_MAX)return dump;
  json z={{"name",name},{"op",ggml_op_name(t->op)},{"base",x.pos},{"width",x.width},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}}};
  for(int i=0;i<2;i++)if(auto*s=t->src[i])z["sources"].push_back({{"name",s->name},{"type",ggml_type_name(s->type)},{"ne",{s->ne[0],s->ne[1],s->ne[2],s->ne[3]}},{"nb",{s->nb[0],s->nb[1],s->nb[2],s->nb[3]}}});
#ifdef CAND
  if(x.c){auto*b=hs_b570_tensor_backend(x.c,t);z["backend"]=b?b:"unknown";}
#endif
  x.nodes.push_back(std::move(z));return dump;
 }
 ctx(llama_model*m,int C,int U,bool observe=false):nv(llama_vocab_n_tokens(llama_model_get_vocab(m))),capacity_n(C),ub(U),trace(observe){
  auto p=llama_context_default_params();p.n_ctx=C;p.n_batch=512;p.n_ubatch=U;p.n_outputs_max=U;p.n_outputs_max_per_seq=U;
  p.n_threads=p.n_threads_batch=8;p.type_k=p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
  if(observe){p.cb_eval=callback;p.cb_eval_user_data=this;}
  c=llama_init_from_model(m,p);need(c,"context allocation");
 }
 ~ctx(){if(c)llama_free(c);}
 void decode(const int *ids,int n,int base,bool all,bool last,const std::string&arm){
  pos=base;width=n;scope active(arm);
  auto b=llama_batch_init(n,0,1);b.n_tokens=n;
  for(int i=0;i<n;i++){b.token[i]=ids[i];b.pos[i]=base+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||(last&&i==n-1);}
  int rc=llama_decode(c,b);llama_batch_free(b);need(rc==0,"llama_decode");calls++;
 }
 void restore(const std::vector<uint8_t>&v,bool verify){
  need(llama_state_seq_set_data(c,v.data(),v.size(),0)==v.size(),"restore");llama_synchronize(c);
  if(verify){auto same=state();need(same==v,"restored KV differs");}
 }
 std::vector<uint8_t> state(){llama_synchronize(c);std::vector<uint8_t>v(llama_state_seq_get_size(c,0));need(llama_state_seq_get_data(c,v.data(),v.size(),0)==v.size(),"state export");return v;}
};
static std::vector<int> partition(ctx&x,const std::string&arm,int n,int base){
 if(arm=="S1")return std::vector<int>(n,1);
 if((arm!="WB" && arm!="WB-cut")||n==1)return {n};
#ifdef CAND
 uint32_t chunks[32],head=0;int count=hs_parallel_groups(x.c,n,chunks,&head);
 need(count>0 && count<=n && head==uint32_t(base),"unsupported physical WB append");
 return std::vector<int>(chunks,chunks+count);
#else
 throw std::runtime_error("WB requested on original reference");
#endif
}
struct output {
 bool heavy;json ids=json::array(),vectors=json::array();
 void collect(ctx&x,int row){
  float*v=llama_get_logits_ith(x.c,row);need(v,"logits");int id=int(std::max_element(v,v+x.nv)-v);ids.push_back(id);
  if(heavy){size_t n=size_t(x.nv)*4;std::string h=hash(v,n);fs::path p=fs::path(job.at("cas").get<std::string>())/h.substr(0,2)/h;if(!fs::exists(p))put(p,v,n);vectors.push_back(h);}
 }
};
static void chunk(ctx&x,const std::string&arm,const int*ids,int n,int base,bool all,bool last,output&out,json*calls){
 int at=0;
 for(int w:partition(x,arm,n,base)){
  bool emit=last&&at+w==n;
  int reused=llama_perf_context(x.c).n_reused;
  x.decode(ids+at,w,base+at,all,emit,arm);
  if(all){for(int j=0;j<w;j++)out.collect(x,j);}
  else if(emit)out.collect(x,-1);
  if(calls)calls->push_back({{"head",base+at},{"width",w},{"reuse_delta",llama_perf_context(x.c).n_reused-reused}});
  at+=w;
 }
 need(at==n,"partition coverage");
}
static json grid(llama_model*m,const json&s){
 auto ids=s.at("ids").get<std::vector<int>>();const int base=s.at("base"),C=job.at("context");std::string arm=s.at("arm");
 auto state=bytes(s.at("state").get<std::string>());ctx x(m,C,s.at("ub"),s.value("trace",false));
 x.restore(state,s.at("heavy"));need(llama_memory_seq_pos_max(llama_get_memory(x.c),0)==base-1,"prior head");capacity();
 output out{s.at("heavy").get<bool>()};json calls=json::array();
 if(x.trace)std::cerr<<"TP_BEGIN "<<arm<<" head="<<base<<" width="<<ids.size()<<std::endl;
 auto start=clock_t_tp::now();
 const int step=s.value("step",int(ids.size()));need(step>0&&step<=32,"positive query step");
 for(int offset=0;offset<int(ids.size());offset+=step){
  int count=std::min(step,int(ids.size())-offset);
  chunk(x,arm,ids.data()+offset,count,base+offset,true,true,out,s.value("trace",false)?&calls:nullptr);
 }
 llama_synchronize(x.c);
 const double elapsed=sec(start);
 if(x.trace)std::cerr<<"TP_END"<<std::endl;
 capacity();
 return {{"slot",s},{"seconds",elapsed},{"greedy",out.ids},{"vectors",out.vectors},{"graph_calls",x.calls},{"trace_calls",calls},{"nodes",x.nodes}};
}
static json seed(llama_model*m,const json&s){
 auto start=clock_t_tp::now();
 const int C=job.at("context");ctx x(m,C,1);auto seq=s.at("ids").get<std::vector<int>>();
 int at=0;json states=json::array();capacity();
 for(int head:s.at("heads").get<std::vector<int>>()){
  while(at<head){x.decode(&seq.at(at),1,at,false,false,"S1");at++;}
  auto v=x.state();auto p=root/("state-"+std::to_string(head)+".bin");put(p,v.data(),v.size());states.push_back({{"head",head},{"bytes",v.size()},{"sha256",hash(v.data(),v.size())}});capacity();
 }
 return {{"states",states},{"prefix_calls",at},{"prefix_construction_seconds",sec(start)}};
}
static json natural(llama_model*m,const json&s){
 const int C=job.at("context"),ub=s.at("ub"),cap=s.at("cap");auto ids=s.at("ids").get<std::vector<int>>();std::string arm=s.at("arm");
 output out{s.at("heavy").get<bool>()};json calls=json::array();double prefill=0,decode=0;int graphs=0;const bool diag=s.value("phases",false);
 auto start=clock_t_tp::now();
 {
  ctx x(m,C,ub,s.value("trace",false));capacity();
  auto p=clock_t_tp::now();
  for(int at=0;at<int(ids.size());){int n=std::min(ub,int(ids.size())-at);chunk(x,arm,&ids[at],n,at,false,at+n==int(ids.size()),out,diag?&calls:nullptr);at+=n;}
  if(diag)prefill=sec(p);
  auto g=clock_t_tp::now();int base=int(ids.size());auto*v=llama_model_get_vocab(m);
  while(int(out.ids.size())<cap){int id=out.ids.back();if(llama_vocab_is_eog(v,id))break;chunk(x,arm,&id,1,base++,false,true,out,nullptr);}
  llama_synchronize(x.c);if(diag)decode=sec(g);graphs=x.calls;
 }
 auto elapsed=sec(start);capacity();return {{"slot",s},{"seconds",elapsed},{"greedy",out.ids},{"vectors",out.vectors},{"graph_calls",graphs},{"prefill_seconds",prefill},{"decode_seconds",decode},{"prefill_calls",calls}};
}
// Cache entries contain owned immutable serialized sequence state. No pending
// output exists: the producer requests no logits and service has a nonempty append.
struct cache_entry { std::vector<uint8_t> data; int head; std::string digest; };
static std::map<std::string,cache_entry> cache;
static json service(llama_model*m,const json&s){
 const int C=job.at("context"),cap=s.value("cap",128); const auto ids=s.at("ids").get<std::vector<int>>();
 const bool heavy=s.at("heavy"),diag=s.value("phases",false),all=s.value("all_append_logits",false);
 output out{heavy};json calls=json::array(),endpoint;std::string arm=s.at("arm");int graphs=0,head=-1;
 double lookup=0,import_time=0,append_time=0;size_t imported=0;
 auto start=clock_t_tp::now();
 {
  const auto &entry=cache.at(s.at("cache_key").get<std::string>());head=entry.head;imported=entry.data.size();
  need(head>=0 && head<int(ids.size()) && ids.size()+cap<=size_t(C),"service capacity/pending ownership");
  if(arm=="AUTO"){
   const auto &policy=job.at("policy");need(policy.at("deployment_id")==job.at("deployment_id"),"policy deployment");
   // The prospectively selected calibration panel contains only zero-density
   // roots. selector.fit therefore freezes a constant table. Avoid pretending
   // that per-input offline features were computed for free during service.
   arm=policy.at("global_fixed_arm");
   for(const auto &bin:policy.at("bins"))need(bin.at("arm")==arm,"nonconstant selector requires qualified native feature extraction");
  }
  need(arm=="S1"||arm=="QB"||arm=="WB-cut"||arm=="WB-rechunk","service policy");
  if(diag)lookup=sec(start);
  ctx x(m,C,arm=="S1"?1:32,s.value("trace",false));capacity();
  auto im=clock_t_tp::now();if(head)x.restore(entry.data,heavy);
  need(llama_memory_seq_pos_max(llama_get_memory(x.c),0)==head-1,"restored logical position");
#ifdef CAND
  uint32_t runs[32],physical=UINT32_MAX;
  need(hs_parallel_groups(x.c,1,runs,&physical)==1 && physical==uint32_t(head),"restored physical head");
#endif
  if(diag)import_time=sec(im);
  auto ap=clock_t_tp::now();
  for(int at=head;at<int(ids.size());){
   int n=std::min(arm=="S1"?1:32,int(ids.size())-at);
#ifdef CAND
   if(arm=="WB-rechunk"){
    uint32_t widths[32],physical_head=UINT32_MAX;
    int nr=hs_parallel_groups(x.c,n,widths,&physical_head);
    need(nr>0 && nr<=n && physical_head==uint32_t(at),"rechunk physical append");
    n=int(widths[0]);need(n>0,"empty native run");
   }
#else
   need(arm=="S1","original oracle route");
#endif
   chunk(x,arm,&ids[at],n,at,all,at+n==int(ids.size()),out,diag?&calls:nullptr);at+=n;
  }
  llama_synchronize(x.c);if(diag)append_time=sec(ap);
  // Extra append rows are a separate probe, never ordinary service qualification.
  int base=int(ids.size()),generated=1;auto*v=llama_model_get_vocab(m);
  while(generated<cap){int id=out.ids.back();if(llama_vocab_is_eog(v,id))break;chunk(x,arm,&id,1,base++,false,true,out,nullptr);++generated;}
  llama_synchronize(x.c);graphs=x.calls;
  endpoint={{"committed_tokens",out.ids},{"last_position",llama_memory_seq_pos_max(llama_get_memory(x.c),0)},
            {"generated",generated},{"stop",llama_vocab_is_eog(v,out.ids.back().get<int>())?"EOG":"cap"},
            {"pending_token",out.ids.back()},{"pending_decoded",false}};
  if(heavy||s.value("audit_state",false)){auto final=x.state();auto h=hash(final.data(),final.size());endpoint["state_sha256"]=h;
   auto state_path=fs::path(job.at("cas").get<std::string>()).parent_path()/"states"/h.substr(0,2)/h;
   if(!fs::exists(state_path))put(state_path,final.data(),final.size());
   auto owned=final;x.restore(owned,true);need(x.state()==final,"own path roundtrip");
   need(hash(entry.data.data(),entry.data.size())==entry.digest,"retained prefix mutated");
  }
 }
 double elapsed=sec(start);capacity();
 return {{"slot",s},{"seconds",elapsed},{"selected_arm",arm},{"physical_head",head},{"import_bytes",imported},
         {"greedy",out.ids},{"vectors",out.vectors},{"endpoint",endpoint},{"graph_calls",graphs},
         {"lookup_seconds",lookup},{"import_seconds",import_time},{"append_seconds",append_time},{"append_calls",calls}};
}

static json tokenize(llama_model*m){
 const char *tmpl=llama_model_chat_template(m,nullptr);need(tmpl,"model chat template");
 put(root/"template.jinja",tmpl,strlen(tmpl));auto *v=llama_model_get_vocab(m);
 std::ifstream in(job.at("input_jsonl").get<std::string>());std::ofstream file(root/"tokens.jsonl");need(bool(in)&&bool(file),"tokenizer IO");
 std::string line;size_t count=0;
 while(std::getline(in,line)){
  json r=json::parse(line);auto messages=r.at("messages");std::vector<std::string>roles,texts;
  for(auto&z:messages){roles.push_back(z.at("role"));texts.push_back(z.at("content"));}
  std::vector<llama_chat_message>chat;for(size_t i=0;i<roles.size();++i)chat.push_back({roles[i].c_str(),texts[i].c_str()});
  for(bool full:{false,true}){
   size_t nm=chat.size()-(full?0:1);int n=llama_chat_apply_template(tmpl,chat.data(),nm,full,nullptr,0);need(n>0,"native template unsupported");
   std::string rendered(n,'\0');need(llama_chat_apply_template(tmpl,chat.data(),nm,full,rendered.data(),n)==n,"render bytes");
   int nt=llama_tokenize(v,rendered.data(),n,nullptr,0,true,true);need(nt<0,"tokenizer sizing");std::vector<int>tokens(-nt);
   need(llama_tokenize(v,rendered.data(),n,tokens.data(),int(tokens.size()),true,true)==int(tokens.size()),"tokenize whole transcript");
   r[full?"request_ids":"cached_ids"]=tokens;r[full?"request_render_sha256":"cached_render_sha256"]=hash(rendered.data(),rendered.size());
  }
  r.erase("messages");file<<r.dump()<<'\n';++count;
 }
 need(bool(file),"tokenizer output");return {{"rows",count},{"vocabulary",llama_vocab_n_tokens(v)},{"template_sha256",hash(tmpl,strlen(tmpl))},{"add_special",true},{"parse_special",true},{"renderer","llama_chat_apply_template/native builtin selected by GGUF template; no external Jinja"}};
}
int main(int argc,char**argv){
 llama_model*t=nullptr,*d=nullptr;json result={{"records",json::array()},{"status","STARTED"}};
 auto clean=[&]{if(d)llama_model_free(d);if(t)llama_model_free(t);t=d=nullptr;llama_backend_free();};
 try{
  need(argc==3,"worker JOB OUT");job=read(argv[1]);root=argv[2];need(!fs::exists(root),"fresh native unit");fs::create_directories(root);save(root/"result.json",result);
  llama_backend_init();
  if(job.value("tokenize_only",false)){auto p=llama_model_default_params();p.vocab_only=true;t=llama_model_load_from_file(job.at("target").get<std::string>().c_str(),p);need(t,"vocab model");result["tokenization"]=tokenize(t);clean();result["status"]="COMPLETE";save(root/"result.json",result);return 0;}
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*q=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(q)).find("B570")!=std::string::npos)device=q;}
  need(device,"B570 device");ggml_backend_dev_t devices[]={device,nullptr};auto params=llama_model_default_params();params.devices=devices;params.n_gpu_layers=999;params.split_mode=LLAMA_SPLIT_MODE_NONE;
  auto l=clock_t_tp::now();t=llama_model_load_from_file(job.at("target").get<std::string>().c_str(),params);need(t,"load target");
  if(!job.value("target_only",false)){d=llama_model_load_from_file(job.at("draft").get<std::string>().c_str(),params);need(d,"load draft");}
  result["resident_models"]=d?2:1;result["load_seconds"]=sec(l);capacity();
  auto cache_start=clock_t_tp::now();
  for(auto&e:job.value("cache",json::array())){auto data=bytes(e.at("path").get<std::string>());auto h=hash(data.data(),data.size());need(h==e.at("sha256"),"prefix object hash");cache.emplace(e.at("key").get<std::string>(),cache_entry{std::move(data),e.at("head"),h});}
  cache.emplace("empty",cache_entry{{},0,hash(nullptr,0)});result["cache_preload_seconds"]=sec(cache_start);
  for(auto&s:job.at("slots")){
   capacity();json r;std::string kind=s.at("kind");
   if(kind=="admit"){ctx a(t,job.at("context"),s.at("ub"));
    std::unique_ptr<ctx> draft_ctx;
    if(s.value("draft_context",true)){need(d,"draft model required");draft_ctx=std::make_unique<ctx>(d,job.at("context"),1);}
    capacity();r={{"zero_forwards",true},{"both_models_all_gpu",bool(d)},{"draft_context",bool(draft_ctx)}};
#ifdef CAND
    if(s.value("allocator_census",false)){
     json heads=json::array();for(uint32_t h=0;h<uint32_t(job.at("context").get<int>());++h){uint32_t physical=UINT32_MAX,pad=0;need(hs_prefix_allocator_census(a.c,h,&physical,&pad)==0,"native allocator census");need(physical==h,"dense allocator layout");heads.push_back({{"logical",h},{"physical",physical},{"padding",pad}});}r["allocator_heads"]=heads;r["metadata_only_no_KV_compute"]=true;
    }
#endif
   }
   else if(kind=="seed")r=seed(t,s);
   else if(kind=="grid")r=grid(t,s);
   else if(kind=="natural")r=natural(t,s);
   else if(kind=="service")r=service(t,s);
   else throw std::runtime_error("unknown slot");
   result["records"].push_back(std::move(r));save(root/"result.json",result);
  }
  clean();result["status"]="COMPLETE";result["min_free_device"]=free_gpu_min;result["min_free_ram"]=free_ram_min;save(root/"result.json",result);return 0;
 }catch(const std::exception&e){clean();result["status"]="FAILED";result["error"]=e.what();result["min_free_device"]=free_gpu_min;result["min_free_ram"]=free_ram_min;if(fs::is_directory(root))save(root/"result.json",result);return 2;}
}
