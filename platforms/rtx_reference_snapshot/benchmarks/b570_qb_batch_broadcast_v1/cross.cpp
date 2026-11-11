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
 int n,q;std::string mode;ggml_context*c=nullptr;ggml_backend_buffer_t buffer=nullptr;
 ggml_tensor *tq,*tk,*tv,*tm,*out,*scores,*probs,*values;ggml_cgraph*g;
 std::vector<float> qv,kf,vf,mask,final;
 std::vector<ggml_fp16_t> k,v;
 std::vector<double> sr,pr,ar;
 fs::path path;
 ~Graph(){if(buffer)ggml_backend_buffer_free(buffer);if(c)ggml_free(c);}
};
static json meta(const ggml_tensor*t){
 return {{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}}};
}
static void reference(Graph&x){
 const int N=x.n,Q=x.q,H=8,D=128;const float scale=1.0f/std::sqrt(128.0f);
 x.qv.resize(D*Q*H);x.kf.resize(D*N*H);x.vf.resize(N*D*H);x.k.resize(x.kf.size());x.v.resize(x.vf.size());x.mask.assign(N*32,0.0f);
 for(int h=0;h<H;h++)for(int j=0;j<Q;j++)for(int d=0;d<D;d++)
  x.qv[(h*Q+j)*D+d]=float(((h*19+j*23+d*7+3)%29)-14)/32.0f;
 for(int h=0;h<H;h++)for(int t=0;t<N;t++)for(int d=0;d<D;d++){
  size_t ki=(h*N+t)*D+d,vi=(h*D+d)*N+t;
  x.kf[ki]=float(((h*11+t*13+d*3+5)%31)-15)/64.0f;
  x.vf[vi]=float(((h*7+t*17+d*11+2)%37)-18)/64.0f;
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
 save(x.path/"q.f32",x.qv);save(x.path/"k.f16",x.k);save(x.path/"v.f16",x.v);save(x.path/"mask.f32",x.mask);
 save(x.path/"reference_qk.f64",x.sr);save(x.path/"reference_softmax.f64",x.pr);save(x.path/"reference_final.f64",x.ar);
}
static void inputs(Graph&x,bool upload,const std::string&tag){
 struct Input{ggml_tensor*t;const void*data;size_t bytes;const char*name;};
 std::vector<Input> in={{x.tq,x.qv.data(),x.qv.size()*4,"q"},{x.tk,x.k.data(),x.k.size()*2,"k"},
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
 need(r.size()==size_t(width*x.q*8),"stage size");if(x.mode=="QB"||x.q==1)return r;
 std::vector<float>out(r.size());for(int j=0;j<x.q;j++)for(int h=0;h<8;h++)for(int k=0;k<width;k++)
  out[(j*8+h)*width+k]=r[(h*x.q+j)*width+k];return out;
}
int main(int argc,char**argv){
 fs::path dest;HMODULE vk=nullptr;ggml_backend_t backend=nullptr;std::vector<std::unique_ptr<Graph>>graphs;
 json r={{"experiment","B570_QB_BATCH_BROADCAST_FIX_CROSS"},{"status","STARTED"},{"phase","SUPPORT"},
 {"models_loaded",0},{"actors_started",0},{"rtl_started",0},{"rows",json::array()},{"graph_computations_returned",0},
 {"numerical_status","UNSTARTED"},{"timing_status","UNSTARTED"}};
 for(int n:{1023,1024,1025})for(int q:{1,2,4})for(auto mode:{"QB","QH_C"})
  r["rows"].push_back({{"key",n},{"q",q},{"mode",mode},{"support","UNSTARTED"},{"numerical","UNSTARTED"},{"timing","UNSTARTED"}});
 auto whole=Clock::now();
 auto cleanup=[&](){graphs.clear();if(backend){ggml_backend_free(backend);backend=nullptr;}if(vk){FreeLibrary(vk);vk=nullptr;}};
 auto flush=[&](){save_json(dest/"result.json",r);};
 auto deadline=[&](){need(ms(whole,Clock::now())<240000,"240-second internal cutoff");};
 try{
  need(argc==2,"usage: cross OUTPUT_DIRECTORY");dest=argv[1];need(!fs::exists(dest),"fresh result directory required");fs::create_directories(dest);flush();
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
   auto owner=std::make_unique<Graph>();auto&x=*owner;x.n=row["key"];x.q=row["q"];x.mode=row["mode"];
   x.path=dest/(std::to_string(x.n)+"-q"+std::to_string(x.q)+"-"+x.mode);fs::create_directories(x.path);
   x.c=ggml_init({4*1024*1024,nullptr,true});need(x.c,"metadata context");auto*c=x.c;
   x.tq=ggml_new_tensor_4d(c,GGML_TYPE_F32,128,x.q,8,1);x.tk=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,x.n,8,1);
   x.tv=ggml_new_tensor_4d(c,GGML_TYPE_F16,x.n,128,8,1);x.tm=ggml_new_tensor_4d(c,GGML_TYPE_F32,x.n,32,1,1);
   auto b=hs_qh::build(c,x.mode=="QB"?hs_qh::Mode::QB4:hs_qh::Mode::QH_C,x.tq,x.tk,x.tv,x.tm,1.0f/std::sqrt(128.0f));
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
   if(i%2==1){std::vector<double>other(graphs[i-1]->final.begin(),graphs[i-1]->final.end());checks["qb_qhc_final"]=compare(x.final,other);}
   row["checks"]=checks;save_json(x.path/"correctness.json",checks);flush();
   for(auto&check:checks.items())if(!check.value()["passed"].get<bool>()){row["numerical"]="FAILED";flush();throw std::runtime_error("first numerical failure; stop before timing");}
   row["numerical"]="PASS";flush();std::cout<<json({{"event","NUMERICAL_PASS"},{"row",i},{"key",x.n},{"q",x.q},{"mode",x.mode},{"checks",checks}}).dump()<<std::endl;
  }
  r["numerical_status"]="ALL_PASS";r["phase"]="TIMING";r["timing_status"]="STARTED";flush();
  for(size_t pair=0;pair<graphs.size()/2;pair++){
   auto left=pair*2,right=left+1;
   for(auto index:{left,right}){r["rows"][index]["timing"]="STARTED";r["rows"][index]["timing_samples_ms"]=json::array();}
   r["active_pair"]=pair;flush();
   for(int warm=0;warm<2;warm++)for(auto index:{left,right})compute(*graphs[index]);
   for(int round=0;round<10;round++){
    size_t order[2]={round%2?right:left,round%2?left:right};
    for(auto index:order){r["active_row"]=index;auto start=Clock::now();compute(*graphs[index]);
     r["rows"][index]["timing_samples_ms"].push_back(ms(start,Clock::now()));}flush();
   }
   for(auto index:{left,right}){
    auto&x=*graphs[index];auto&row=r["rows"][index];inputs(x,false,"after-timing");
    auto final=raw(x,x.out,"gpu_final_after_timing");row["post_timing_final"]=compare(final,x.ar);flush();
    need(row["post_timing_final"]["passed"].get<bool>(),"post timing numerical failure");
    std::vector<double>t=row["timing_samples_ms"].get<std::vector<double>>();std::sort(t.begin(),t.end());
    row["warmups"]=2;row["median_graph_wall_ms"]=(t[4]+t[5])/2;row["min_graph_wall_ms"]=t.front();row["max_graph_wall_ms"]=t.back();
    row["input_bytes_unchanged"]=true;row["timing"]="PASS";flush();
   }
   std::cout<<json({{"event","TIMING_PAIR_PASS"},{"key",graphs[left]->n},{"q",graphs[left]->q},
    {"qb_median_ms",r["rows"][left]["median_graph_wall_ms"]},{"qhc_median_ms",r["rows"][right]["median_graph_wall_ms"]}}).dump()<<std::endl;
  }
  r["timing_status"]="ALL_PASS";r["status"]="EXPLORATORY_ALL_PASS";r["phase"]="COMPLETE";
  r["timing_scope"]="Host steady-clock graph call plus synchronization, resident operands; includes in-graph/backend Q packing; excludes setup, upload, readback, CPU reference. No GPU timestamps/replay.";
  cleanup();r["normal_cleanup_returned"]=true;r["total_host_elapsed_ms"]=ms(whole,Clock::now());flush();return 0;
 }catch(const std::exception&e){
  r["status"]="STOPPED_FIRST_FAILURE";r["error"]=e.what();r["elapsed_before_cleanup_ms"]=ms(whole,Clock::now());
  std::cerr<<e.what()<<std::endl;if(!dest.empty()&&fs::exists(dest))flush();
  cleanup();r["normal_cleanup_returned"]=true;r["total_host_elapsed_ms"]=ms(whole,Clock::now());if(!dest.empty()&&fs::exists(dest))flush();return 2;
 }
}
