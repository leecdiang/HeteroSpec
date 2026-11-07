#define NOMINMAX
#include <windows.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "query_head.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using json=nlohmann::json; namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
template<class T> static void save(const fs::path&p,const std::vector<T>&v){
 std::ofstream f(p,std::ios::binary);need(bool(f),"open raw");f.write((const char*)v.data(),v.size()*sizeof(T));need(bool(f),"write raw");
}
static void save_json(const fs::path&p,const json&j){std::ofstream f(p);f<<j.dump(2)<<'\n';need(bool(f),"write json");}
static double ms(Clock::time_point a,Clock::time_point b){return std::chrono::duration<double,std::milli>(b-a).count();}
static json compare(const std::vector<float>&actual,const std::vector<double>&expected){
 need(actual.size()==expected.size(),"reference size");double max_abs=0,max_rel=0;size_t worst=0;bool pass=true;
 for(size_t i=0;i<actual.size();i++){double err=std::abs(double(actual[i])-expected[i]);double rel=err/std::max(1e-12,std::abs(expected[i]));
  if(err>max_abs){max_abs=err;worst=i;}max_rel=std::max(max_rel,rel);
  pass=pass&&std::isfinite(actual[i])&&std::isfinite(expected[i])&&err<=0.0002+0.002*std::abs(expected[i]);
 }
 return {{"passed",pass},{"elements",actual.size()},{"max_abs_error",max_abs},{"max_relative_error",max_rel},{"worst_index",worst}};
}

#include <memory>
struct Graph {
 int n,q,input;std::string mode;ggml_context*c=nullptr;ggml_backend_buffer_t buffer=nullptr;
 ggml_tensor *qstorage,*tq,*tk,*tv,*tm,*out,*scores,*probs,*values;ggml_cgraph*g;
 std::vector<float> qv,kf,vf,mask,final,common_q,staging,readback;
 std::vector<ggml_fp16_t> k,v;
 std::vector<double> sr,pr,ar;
 fs::path path;
 ~Graph(){if(buffer)ggml_backend_buffer_free(buffer);if(c)ggml_free(c);}
};
static json meta(const ggml_tensor*t){
 return {{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};
}
static uint32_t mix32(uint32_t x){x^=x>>16;x*=0x7feb352du;x^=x>>15;x*=0x846ca68bu;return x^(x>>16);}
static void reference(Graph&x){
 const int N=x.n,Q=x.q,H=8,D=128;const float scale=1.0f/std::sqrt(128.0f);
 x.qv.resize(D*Q*H);x.kf.resize(D*N*H);x.vf.resize(N*D*H);x.k.resize(x.kf.size());x.v.resize(x.vf.size());x.mask.assign(N*32,0.0f);
 for(int h=0;h<H;h++)for(int j=0;j<Q;j++)for(int d=0;d<D;d++)
  x.qv[(h*Q+j)*D+d]=x.input==0 ? float(((h*19+j*23+d*7+3)%29)-14)/32.0f :
   float(int(mix32(uint32_t((h*Q+j)*D+d)^uint32_t(0x12ab34cdu+x.input))%65)-32)/(x.input==1?64.0f:16.0f);
 for(int h=0;h<H;h++)for(int t=0;t<N;t++)for(int d=0;d<D;d++){
  size_t ki=(h*N+t)*D+d,vi=(h*D+d)*N+t;
  x.kf[ki]=float(((h*11+t*13+d*3+5)%31)-15)/64.0f;
  x.vf[vi]=float(((h*7+t*17+d*11+2)%37)-18)/64.0f;
  if(x.input!=0){x.kf[ki]=float(int(mix32(uint32_t(ki)^uint32_t(0x73e8bba1u+x.input))%65)-32)/(x.input==1?128.0f:32.0f);
   x.vf[vi]=float(int(mix32(uint32_t(vi)^uint32_t(0x9d1327f5u+x.input))%65)-32)/(x.input==1?64.0f:32.0f);}
  x.k[ki]=ggml_fp32_to_fp16(x.kf[ki]);x.v[vi]=ggml_fp32_to_fp16(x.vf[vi]);
 }
 for(int j=0;j<Q;j++)for(int t=N-Q+j+1;t<N;t++)x.mask[j*N+t]=-INFINITY;
 x.sr.resize(N*Q*H);x.pr.resize(N*Q*H);x.ar.resize(D*Q*H);
 for(int j=0;j<Q;j++)for(int h=0;h<H;h++){
  double largest=-INFINITY;size_t row=(j*H+h)*N;
  for(int t=0;t<N;t++){double sum=0;for(int d=0;d<D;d++)sum+=double(x.qv[(h*Q+j)*D+d])*x.kf[(h*N+t)*D+d];
   x.sr[row+t]=sum;largest=std::max(largest,sum*double(scale)+double(x.mask[j*N+t]));}
  double denom=0;for(int t=0;t<N;t++){x.pr[row+t]=std::exp(x.sr[row+t]*double(scale)+double(x.mask[j*N+t])-largest);denom+=x.pr[row+t];}
  for(int t=0;t<N;t++)x.pr[row+t]/=denom;
  for(int d=0;d<D;d++){double sum=0;for(int t=0;t<N;t++)sum+=double(x.vf[(h*D+d)*N+t])*x.pr[row+t];x.ar[(j*H+h)*D+d]=sum;}
 }
 // Oracle above uses logical compact Q. Every transaction starts from identical
 // preexisting permuted host bytes [q,H,d]; QB preserves that representation.
 x.common_q.resize(x.qv.size());x.staging.resize(x.qv.size());x.readback.resize(x.qv.size());
 for(int j=0;j<Q;j++)for(int h=0;h<H;h++)for(int d=0;d<D;d++)
  x.common_q[(j*H+h)*D+d]=x.qv[(h*Q+j)*D+d];
 save(x.path/"common_q_permuted.f32",x.common_q);
 if(x.mode!="QH_C")x.qv=x.common_q;
 save(x.path/"q.f32",x.qv);save(x.path/"k.f16",x.k);save(x.path/"v.f16",x.v);save(x.path/"mask.f32",x.mask);
 save(x.path/"reference_qk.f64",x.sr);save(x.path/"reference_softmax.f64",x.pr);save(x.path/"reference_final.f64",x.ar);
}
static void inputs(Graph&x,bool upload,const std::string&tag){
 struct Input{ggml_tensor*t;const void*data;size_t bytes;const char*name;};
 std::vector<Input> in={{x.qstorage,x.qv.data(),x.qv.size()*4,"q"},{x.tk,x.k.data(),x.k.size()*2,"k"},
 {x.tv,x.v.data(),x.v.size()*2,"v"},{x.tm,x.mask.data(),x.mask.size()*4,"mask"}};
 for(auto&i:in){if(upload)ggml_backend_tensor_set(i.t,i.data,0,i.bytes);std::vector<char>r(i.bytes);
  ggml_backend_tensor_get(i.t,r.data(),0,r.size());save(x.path/(std::string(i.name)+"."+tag+".bin"),r);
  need(std::memcmp(r.data(),i.data,i.bytes)==0,"input bytes differ");}
}
static std::vector<float> raw(Graph&x,ggml_tensor*t,const char*name){
 need(t->type==GGML_TYPE_F32&&ggml_is_contiguous(t),"contiguous F32 stage");std::vector<float>r(ggml_nelements(t));
 ggml_backend_tensor_get(t,r.data(),0,r.size()*4);save(x.path/(std::string(name)+".f32"),r);return r;
}
static std::vector<float> logical(const Graph&x,const std::vector<float>&r,int width){
 need(r.size()==size_t(width*x.q*8),"stage size");if(x.mode!="QH_C"||x.q==1)return r;
 std::vector<float>out(r.size());for(int j=0;j<x.q;j++)for(int h=0;h<8;h++)for(int k=0;k<width;k++)
  out[(j*8+h)*width+k]=r[(h*x.q+j)*width+k];return out;
}
int main(int argc,char**argv){
 fs::path dest;HMODULE vk=nullptr;ggml_backend_t backend=nullptr;std::vector<std::unique_ptr<Graph>>graphs;
 json r={{"experiment","B570_COMMON_Q_COMPLETE_TRANSACTION"},{"status","STARTED"},{"phase","SUPPORT"},
 {"models_loaded",0},{"actors_started",0},{"rtl_started",0},{"rows",json::array()},{"graph_computations_returned",0},
 {"numerical_status","UNSTARTED"},{"timing_status","UNSTARTED"}};
 for(int n:{1023,1024,1025})for(int q:{1,2,4})for(int input:{0,1,2})for(auto mode:{"QB_A","QB_B","QH_C"})
  r["rows"].push_back({{"key",n},{"q",q},{"input",input},{"mode",mode},{"support","UNSTARTED"},{"numerical","UNSTARTED"},{"timing","UNSTARTED"}});
 auto whole=Clock::now();
 auto cleanup=[&](){graphs.clear();if(backend){ggml_backend_free(backend);backend=nullptr;}if(vk){FreeLibrary(vk);vk=nullptr;}};
 auto flush=[&](){save_json(dest/"result.json",r);};
 auto deadline=[&](){need(ms(whole,Clock::now())<50000,"50-second session internal cutoff");};
 try{
  need(argc==3,"usage: balanced OUTPUT_DIRECTORY SESSION_INDEX");int session=std::stoi(argv[2]);need(session>=0&&session<3,"session index");r["session"]=session;dest=argv[1];need(!fs::exists(dest),"fresh result directory required");fs::create_directories(dest);flush();
  std::cout<<json({{"event","START"},{"pid",GetCurrentProcessId()}}).dump()<<std::endl;
  wchar_t exe[32768];need(GetModuleFileNameW(nullptr,exe,32768)>0,"exe path");
  auto dll=fs::path(exe).parent_path()/"ggml-vulkan.dll";vk=LoadLibraryExW(dll.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(vk,"load candidate Vulkan");
  auto count=(int(*)())GetProcAddress(vk,"ggml_backend_vk_get_device_count");
  auto describe=(void(*)(int,char*,size_t))GetProcAddress(vk,"ggml_backend_vk_get_device_description");
  auto init=(ggml_backend_t(*)(size_t))GetProcAddress(vk,"ggml_backend_vk_init");need(count&&describe&&init,"Vulkan APIs");
  int selected=-1;r["devices"]=json::array();
  for(int i=0;i<count();i++){char name[512]={};describe(i,name,sizeof(name));r["devices"].push_back({{"index",i},{"name",name}});
   if(std::string(name).find("B570")!=std::string::npos){need(selected==-1,"ambiguous B570");selected=i;}}
  need(selected>=0,"B570 unavailable");backend=init(selected);need(backend,"init B570");auto dev=ggml_backend_get_device(backend);
  r["device"]=ggml_backend_dev_description(dev);need(std::string(ggml_backend_dev_description(dev)).find("B570")!=std::string::npos,"device mismatch");flush();
  for(size_t i=0;i<r["rows"].size();i++){
   deadline();auto&row=r["rows"][i];r["active_row"]=i;row["support"]="STARTED";flush();
   auto owner=std::make_unique<Graph>();auto&x=*owner;x.n=row["key"];x.q=row["q"];x.input=row["input"];x.mode=row["mode"];
   x.path=dest/(std::to_string(x.n)+"-q"+std::to_string(x.q)+"-i"+std::to_string(x.input)+"-"+x.mode);fs::create_directories(x.path);
   x.c=ggml_init({4*1024*1024,nullptr,true});need(x.c,"metadata context");auto*c=x.c;
   if(x.mode=="QH_C"||x.q==1){
    x.qstorage=ggml_new_tensor_4d(c,GGML_TYPE_F32,128,x.q,8,1);x.tq=x.qstorage;
   }else{
    x.qstorage=ggml_new_tensor_4d(c,GGML_TYPE_F32,128,8,x.q,1);
    x.tq=ggml_permute(c,x.qstorage,0,2,1,3);
   }
   x.tk=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,x.n,8,1);
   x.tv=ggml_new_tensor_4d(c,GGML_TYPE_F16,x.n,128,8,1);x.tm=ggml_new_tensor_4d(c,GGML_TYPE_F32,x.n,32,1,1);
   auto b=hs_qh::build(c,x.mode=="QH_C"?hs_qh::Mode::QH_C:hs_qh::Mode::QB4,x.tq,x.tk,x.tv,x.tm,1.0f/std::sqrt(128.0f));
   if(b.common_original){x.scores=ggml_mul_mat(c,x.tk,x.tq);ggml_mul_mat_set_prec(x.scores,GGML_PREC_F32);
    x.probs=ggml_soft_max_ext(c,x.scores,x.tm,1.0f/std::sqrt(128.0f),0);x.values=ggml_mul_mat(c,x.tv,x.probs);
    x.out=ggml_cont_2d(c,ggml_permute(c,x.values,0,2,1,3),128*8,x.q);
   }else{need(b.scores.size()==1&&b.probs.size()==1&&b.values.size()==1,"single attention chain");
    x.scores=b.scores[0];x.probs=b.probs[0];x.values=b.values[0];x.out=b.out;}
   need(x.scores->src[0]==x.tk&&x.values->src[0]==x.tv&&!b.copied_kv,"same K/V objects, no repeat substitution");
   row["common_original"]=b.common_original;row["packed_q"]=b.packed_q;row["copied_kv"]=b.copied_kv;row["same_kv_objects"]=true;
   x.g=ggml_new_graph(c);ggml_build_forward_expand(x.g,x.out);row["nodes"]=json::array();
   for(int j=0;j<ggml_graph_n_nodes(x.g);j++){
    auto*t=ggml_graph_node(x.g,j);bool okay=ggml_backend_dev_supports_op(dev,t);json src=json::array();
    for(int k=0;k<GGML_MAX_SRC;k++)if(t->src[k])src.push_back({{"index",k},{"tensor",meta(t->src[k])}});
    row["nodes"].push_back({{"index",j},{"op",ggml_op_name(t->op)},{"output",meta(t)},{"sources",src},{"supported",okay}});
    need(t->op!=GGML_OP_REPEAT,"no REPEAT nodes");
    if(!okay){row["support"]="UNSUPPORTED";flush();throw std::runtime_error("first unsupported node; stop");}
   }
   if(i%3==1){need(row["nodes"]==r["rows"][i-1]["nodes"],"QB_A/B graph metadata equality");row["qb_ab_graph_metadata_equal"]=true;}
   row["support"]="SUPPORTED";graphs.push_back(std::move(owner));flush();
   std::cout<<json({{"event","SUPPORT_PASS"},{"row",i},{"key",x.n},{"q",x.q},{"mode",x.mode}}).dump()<<std::endl;
  }
  r["status"]="ALL_SUPPORT_PASSED";r["phase"]="NUMERICAL";r["numerical_status"]="STARTED";flush();
  auto compute=[&](Graph&x){deadline();auto st=ggml_backend_graph_compute(backend,x.g);ggml_backend_synchronize(backend);
   need(st==GGML_STATUS_SUCCESS,"Vulkan graph compute status");r["graph_computations_returned"]=r["graph_computations_returned"].get<int>()+1;};
  for(size_t i=0;i<graphs.size();i++){
   deadline();auto&x=*graphs[i];auto&row=r["rows"][i];r["active_row"]=i;row["numerical"]="STARTED";flush();
   auto start=Clock::now();reference(x);row["cpu_reference_ms"]=ms(start,Clock::now());
   x.buffer=ggml_backend_alloc_ctx_tensors(x.c,backend);need(x.buffer,"allocate Vulkan tensors");
   row["buffer_bytes"]=ggml_backend_buffer_get_size(x.buffer);
   for(int j=0;j<ggml_graph_n_nodes(x.g);j++){
    auto*t=ggml_graph_node(x.g,j);need(t->buffer,"node buffer exists");
    need(ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer))==dev,"all node buffers on B570");}
   start=Clock::now();inputs(x,true,"before");row["upload_and_initial_readback_ms"]=ms(start,Clock::now());
   start=Clock::now();compute(x);row["first_graph_wall_ms"]=ms(start,Clock::now());
   start=Clock::now();auto s=logical(x,raw(x,x.scores,"gpu_qk"),x.n),p=logical(x,raw(x,x.probs,"gpu_softmax"),x.n);
   auto a=logical(x,raw(x,x.values,"gpu_av"),128);x.final=raw(x,x.out,"gpu_final");inputs(x,false,"after-numerical");
   row["correctness_readback_ms"]=ms(start,Clock::now());
   json checks={{"qk",compare(s,x.sr)},{"softmax",compare(p,x.pr)},{"av",compare(a,x.ar)},{"final",compare(x.final,x.ar)}};
   if(i%3!=0){auto&other=graphs[i-i%3]->final;checks["vs_qb_a"]=compare(x.final,std::vector<double>(other.begin(),other.end()));
    need(x.final.size()==other.size(),"arm final size");row["final_bytes_equal_qb_a"]=std::memcmp(x.final.data(),other.data(),other.size()*4)==0;
    need(row["final_bytes_equal_qb_a"].get<bool>(),"first final byte mismatch");}
   row["checks"]=checks;save_json(x.path/"correctness.json",checks);flush();
   for(auto&check:checks.items())if(!check.value()["passed"].get<bool>()){row["numerical"]="FAILED";flush();throw std::runtime_error("first numerical failure; stop before timing");}
   row["numerical"]="PASS";flush();std::cout<<json({{"event","NUMERICAL_PASS"},{"row",i},{"key",x.n},{"q",x.q},{"mode",x.mode},{"checks",checks}}).dump()<<std::endl;
  }
  r["numerical_status"]="ALL_PASS";r["phase"]="TRANSACTION_QUALIFICATION";flush();
  auto transaction=[&](Graph&x){
   deadline();
   auto start=Clock::now();
   if(x.mode!="QH_C"||x.q==1){
    std::memcpy(x.staging.data(),x.common_q.data(),x.common_q.size()*4);
   }else{
    for(int h=0;h<8;h++)for(int j=0;j<x.q;j++)
     std::memcpy(x.staging.data()+(h*x.q+j)*128,x.common_q.data()+(j*8+h)*128,128*4);
   }
   ggml_backend_tensor_set(x.qstorage,x.staging.data(),0,x.staging.size()*4);
   ggml_backend_synchronize(backend);
   auto status=ggml_backend_graph_compute(backend,x.g);
   ggml_backend_synchronize(backend);
   ggml_backend_tensor_get(x.out,x.readback.data(),0,x.readback.size()*4);
   ggml_backend_synchronize(backend);
   auto end=Clock::now();
   r["graph_computations_returned"]=r["graph_computations_returned"].get<int>()+1;
   need(status==GGML_STATUS_SUCCESS,"transaction compute failed");
   need(std::memcmp(x.staging.data(),x.qv.data(),x.qv.size()*4)==0,"transaction Q representation mismatch");
   need(std::memcmp(x.readback.data(),x.final.data(),x.final.size()*4)==0,"transaction final byte mismatch");
   return ms(start,end);
  };
  // Validate the actual continuous path for every slot before any measured block.
  for(size_t i=0;i<graphs.size();i++){
   auto&x=*graphs[i];transaction(x);
   save(x.path/"transaction_qualified_final.f32",x.readback);
   if(i%3!=0)need(x.common_q==graphs[i-i%3]->common_q,"common host Q mismatch across arms");
   r["rows"][i]["transaction_qualification"]="PASS";
  }
  r["transaction_qualification"]="ALL_PASS";r["phase"]="TIMING";r["timing_status"]="STARTED";flush();
  for(auto&x:graphs)for(int warm=0;warm<5;warm++)transaction(*x);
  std::ofstream timing_log(dest/"timing.jsonl");need(bool(timing_log),"timing log");
  const int permutations[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
  for(int block=0;block<6;block++){
   for(int visit=0;visit<27;visit++){
    const int rotated=(visit+session*9+block*5)%27;
    const int cell=(block+session)%2 ? 26-rotated : rotated;
    const size_t base=size_t(cell)*3;auto&first=*graphs[base];
    r["active_block"]=block;r["active_cell"]=cell;
    for(int arm=0;arm<3;arm++)transaction(*graphs[base+(arm+block+session)%3]);
    json samples=json::array();std::vector<double>values[3];
    for(int perm_visit=0;perm_visit<6;perm_visit++){
     int permutation=(perm_visit+cell+block+session)%6;json order=json::array();
     for(int pos=0;pos<3;pos++){
      int arm=permutations[permutation][pos];auto&x=*graphs[base+arm];json times=json::array();
      for(int call=0;call<5;call++){double elapsed=transaction(x);times.push_back(elapsed);values[arm].push_back(elapsed);}
      order.push_back({{"arm",x.mode},{"position",pos},{"samples_ms",times}});
     }
     samples.push_back({{"permutation",permutation},{"visits",order}});
    }
    json means=json::object();for(int arm=0;arm<3;arm++){double sum=0;for(double v:values[arm])sum+=v;means[graphs[base+arm]->mode]=sum/values[arm].size();}
    json record={{"session",session},{"block",block},{"cell",cell},{"visit",visit},{"key",first.n},{"q",first.q},{"input",first.input},
     {"arm_means_ms",means},{"permutations",samples},{"elapsed_session_ms",ms(whole,Clock::now())}};
    timing_log<<record.dump()<<'\n';timing_log.flush();need(bool(timing_log),"timing record write");
    for(size_t index=base;index<base+3;index++){
     auto&x=*graphs[index];auto final=raw(x,x.out,("gpu_final_block"+std::to_string(block)).c_str());
     need(std::memcmp(final.data(),x.final.data(),x.final.size()*4)==0,"first post-block final byte mismatch");
    }
   }
   flush();std::cout<<json({{"event","TIMING_BLOCK_COMPLETE"},{"session",session},{"block",block}}).dump()<<std::endl;
  }
  for(size_t i=0;i<graphs.size();i++){auto&x=*graphs[i];inputs(x,false,"after-timing");r["rows"][i]["timing"]="PASS";r["rows"][i]["input_bytes_unchanged"]=true;}
  r["timing_status"]="ALL_PASS";r["status"]="EXPLORATORY_ALL_PASS";r["phase"]="COMPLETE";
  r["timing_scope"]="Continuous host steady-clock: common permuted host Q -> copy or transpose -> Q upload/sync -> graph compute/sync -> full final readback/sync. Preallocated targets, resident K/V/mask. Excludes natural Q production, KV updates, setup, reference and validation comparisons. No GPU timestamps or claimed replay.";
  cleanup();r["normal_cleanup_returned"]=true;r["total_host_elapsed_ms"]=ms(whole,Clock::now());flush();return 0;
 }catch(const std::exception&e){
  r["status"]="STOPPED_FIRST_FAILURE";r["error"]=e.what();r["elapsed_before_cleanup_ms"]=ms(whole,Clock::now());
  std::cerr<<e.what()<<std::endl;if(!dest.empty()&&fs::exists(dest))flush();
  cleanup();r["normal_cleanup_returned"]=true;r["total_host_elapsed_ms"]=ms(whole,Clock::now());if(!dest.empty()&&fs::exists(dest))flush();return 2;
 }
}
