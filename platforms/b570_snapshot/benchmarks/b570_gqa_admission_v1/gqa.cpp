#define NOMINMAX
#include <windows.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "query_head.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <memory>
#include <chrono>
#include <cmath>
#include <cstring>
using json=nlohmann::json; namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
void need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
void js(const fs::path&p,const json&j){std::ofstream f(p);f<<j.dump(2)<<"\n";need(bool(f),"json write");}
template<class T>void save(const fs::path&p,const std::vector<T>&v){std::ofstream f(p,std::ios::binary);f.write((const char*)v.data(),v.size()*sizeof(T));need(bool(f),"raw write");}
json meta(ggml_tensor*t){return {{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"type",ggml_type_name(t->type)}};}
struct Graph {
 int n,q;std::string arm;fs::path dir;
 ggml_context*c=nullptr;ggml_backend_buffer_t buf=nullptr;
 ggml_tensor *qb,*kb,*vb,*m,*Q,*K,*V,*out;ggml_cgraph*g;
 std::vector<ggml_tensor*>scores,probs,values;
 std::vector<float>qdata,mask,final;
 std::vector<ggml_fp16_t>kdata,vdata;
 std::vector<double>sr,pr,ar;
 ~Graph(){if(buf)ggml_backend_buffer_free(buf);if(c)ggml_free(c);}
};
std::unique_ptr<Graph> build(int n,int q,std::string arm,fs::path dir){
 auto x=std::make_unique<Graph>();x->n=n;x->q=q;x->arm=arm;x->dir=dir;
 x->c=ggml_init({8*1024*1024,nullptr,true});need(x->c,"context");auto*c=x->c;
 x->qb=ggml_new_tensor_4d(c,GGML_TYPE_F32,128,32,q,1);
 x->Q=ggml_permute(c,x->qb,0,2,1,3);
 x->kb=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,8,1024,1);
 x->K=ggml_view_4d(c,x->kb,128,n,8,1,2048,256,2097152,0);
 x->vb=ggml_new_tensor_4d(c,GGML_TYPE_F16,1024,128,8,1);
 x->V=ggml_view_4d(c,x->vb,n,128,8,1,2048,262144,2097152,0);
 x->m=ggml_new_tensor_4d(c,GGML_TYPE_F32,n,32,1,1);
 auto b=hs_qh::build(c,arm=="PQ"?hs_qh::Mode::PQ:hs_qh::Mode::QB4,x->Q,x->K,x->V,x->m,1/std::sqrt(128.f));
 if(b.common_original){
  auto*s=ggml_mul_mat(c,x->K,x->Q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);
  auto*p=ggml_soft_max_ext(c,s,x->m,1/std::sqrt(128.f),0);auto*a=ggml_mul_mat(c,x->V,p);
  x->scores={s};x->probs={p};x->values={a};x->out=ggml_cont_2d(c,ggml_permute(c,a,0,2,1,3),128*32,q);
 }else{x->scores=b.scores;x->probs=b.probs;x->values=b.values;x->out=b.out;}
 need(!b.copied_kv,"no KV repeats");
 for(auto*t:x->scores)need(t->src[0]==x->K,"same K");
 for(auto*t:x->values)need(t->src[0]==x->V,"same V");
 x->g=ggml_new_graph(c);ggml_build_forward_expand(x->g,x->out);return x;
}
void reference(Graph&x){
 const int D=128,H=32,HK=8,N=x.n,Q=x.q,C=1024;
 x.qdata.resize(D*H*Q);x.kdata.resize(D*HK*C);x.vdata.resize(C*D*HK);x.mask.assign(N*32,0);
 for(int j=0;j<Q;j++)for(int h=0;h<H;h++)for(int d=0;d<D;d++)
  x.qdata[(j*H+h)*D+d]=float((j*23+h*19+d*7+3)%29-14)/32;
 for(int t=0;t<C;t++)for(int h=0;h<HK;h++)for(int d=0;d<D;d++){
  x.kdata[(t*HK+h)*D+d]=ggml_fp32_to_fp16(float((h*11+t*13+d*3+5)%31-15)/64);
  x.vdata[(h*D+d)*C+t]=ggml_fp32_to_fp16(float((h*7+t*17+d*11+2)%37-18)/64);
 }
 // Derived causal states: 124 visible keys for observed extent256, 260 for extent512.
 int visible=(N==256?124:260);
 for(int j=0;j<Q;j++)for(int t=visible-Q+j+1;t<N;t++)x.mask[j*N+t]=-INFINITY;
 x.sr.resize(N*H*Q);x.pr.resize(N*H*Q);x.ar.resize(D*H*Q);
 float scale=1/std::sqrt(128.f);
 for(int j=0;j<Q;j++)for(int h=0;h<H;h++){
  size_t row=(j*H+h)*N;double mx=-INFINITY;
  for(int t=0;t<N;t++){double s=0;for(int d=0;d<D;d++)s+=double(x.qdata[(j*H+h)*D+d])*ggml_fp16_to_fp32(x.kdata[(t*HK+h/4)*D+d]);
   x.sr[row+t]=s;mx=std::max(mx,s*scale+x.mask[j*N+t]);}
  double denom=0;for(int t=0;t<N;t++){x.pr[row+t]=std::exp(x.sr[row+t]*scale+x.mask[j*N+t]-mx);denom+=x.pr[row+t];}
  for(int t=0;t<N;t++)x.pr[row+t]/=denom;
  for(int d=0;d<D;d++){double s=0;for(int t=0;t<N;t++)s+=double(ggml_fp16_to_fp32(x.vdata[(h/4*D+d)*C+t]))*x.pr[row+t];x.ar[(j*H+h)*D+d]=s;}
 }
 save(x.dir/"q.f32",x.qdata);save(x.dir/"k_storage.f16",x.kdata);save(x.dir/"v_storage.f16",x.vdata);save(x.dir/"mask.f32",x.mask);
 save(x.dir/"ref_qk.f64",x.sr);save(x.dir/"ref_softmax.f64",x.pr);save(x.dir/"ref_final.f64",x.ar);
}
void inputs(Graph&x,bool upload,const char*tag){
 struct I{ggml_tensor*t;void*p;size_t bytes;const char*n;};
 for(auto i:std::vector<I>{{x.qb,x.qdata.data(),x.qdata.size()*4,"q"},{x.kb,x.kdata.data(),x.kdata.size()*2,"k"},{x.vb,x.vdata.data(),x.vdata.size()*2,"v"},{x.m,x.mask.data(),x.mask.size()*4,"mask"}}){
  if(upload)ggml_backend_tensor_set(i.t,i.p,0,i.bytes);
  std::vector<char>b(i.bytes);ggml_backend_tensor_get(i.t,b.data(),0,b.size());save(x.dir/(std::string(i.n)+"-"+tag+".bin"),b);
  need(!memcmp(i.p,b.data(),i.bytes),"input storage differs");
 }
}
std::vector<float> stage(Graph&x,const std::vector<ggml_tensor*>&ts,const char*name){
 std::vector<float>out;
 for(auto*t:ts){need(t->type==GGML_TYPE_F32&&ggml_is_contiguous(t),"stage contiguous");size_t offset=out.size();out.resize(offset+ggml_nelements(t));ggml_backend_tensor_get(t,out.data()+offset,0,ggml_nbytes(t));}
 save(x.dir/(std::string(name)+".f32"),out);return out;
}
json check(const std::vector<float>&a,const std::vector<double>&b){
 need(a.size()==b.size(),"size");bool pass=true;double maxerr=0;
 for(size_t i=0;i<a.size();i++){double e=std::abs(a[i]-b[i]);maxerr=std::max(e,maxerr);pass&=std::isfinite(a[i])&&e<=.0002+.002*std::abs(b[i]);}
 return{{"passed",pass},{"max_abs",maxerr},{"elements",a.size()}};
}
int main(int argc,char**argv){
 fs::path dest;HMODULE vk=nullptr;ggml_backend_t backend=nullptr;
 std::vector<std::unique_ptr<Graph>> graphs;
 json r={{"status","STARTED"},{"rows",json::array()},{"models_loaded",0},{"timing","NOT_PLANNED"},{"computes",0}};
 auto start=Clock::now();auto cleanup=[&](){graphs.clear();if(backend){ggml_backend_free(backend);backend=nullptr;}if(vk){FreeLibrary(vk);vk=nullptr;}};
 try{
  need(argc==3,"gqa OUTPUT DLL");dest=argv[1];need(!fs::exists(dest),"fresh output");fs::create_directories(dest);
  auto flush=[&](){js(dest/"result.json",r);};
  vk=LoadLibraryExW(fs::path(argv[2]).c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(vk,"load");
  auto count=(int(*)())GetProcAddress(vk,"ggml_backend_vk_get_device_count");
  auto desc=(void(*)(int,char*,size_t))GetProcAddress(vk,"ggml_backend_vk_get_device_description");
  auto init=(ggml_backend_t(*)(size_t))GetProcAddress(vk,"ggml_backend_vk_init");need(count&&desc&&init,"API");
  int selected=-1;for(int i=0;i<count();i++){char n[512]={};desc(i,n,512);if(std::string(n).find("B570")!=std::string::npos){need(selected<0,"ambiguous");selected=i;}}
  need(selected>=0,"B570 missing");backend=init(selected);need(backend,"backend");auto dev=ggml_backend_get_device(backend);r["device"]=ggml_backend_dev_description(dev);
  r["admission_controls"]=json::array();
  {
   auto x=build(256,2,"QB",dest/"unused-control");
   for(auto*original:{x->scores[0],x->values[0]})for(int test=0;test<5;test++){
    ggml_tensor op=*original,a=*original->src[0],b=*original->src[1];op.src[0]=&a;op.src[1]=&b;
    if(test==1){b.ne[3]=3;op.ne[3]=3;}
    if(test==2){b.ne[2]=16;op.ne[2]=16;}
    if(test==3){a.nb[3]+=256;}
    if(test==4){a.type=GGML_TYPE_F32;a.nb[0]=4;}
    bool supported=ggml_backend_dev_supports_op(dev,&op),expected=test==0;
    r["admission_controls"].push_back({{"role",original==x->scores[0]?"QK":"AV"},{"case",test},{"expected",expected},{"actual",supported}});
    flush();need(supported==expected,"admission control mismatch");
   }
  }
  for(int n:{256,512})for(int q:{1,2,4})for(std::string arm:{"PQ","QB"}){
   need(std::chrono::duration<double>(Clock::now()-start).count()<18,"internal deadline");
   auto x=build(n,q,arm,dest/(std::to_string(n)+"-q"+std::to_string(q)+"-"+arm));fs::create_directories(x->dir);
   json row={{"n",n},{"q",q},{"arm",arm},{"Q",meta(x->Q)},{"K",meta(x->K)},{"V",meta(x->V)},{"nodes",json::array()},{"support",true},{"numerical","UNSTARTED"}};
   for(int j=0;j<ggml_graph_n_nodes(x->g);j++){
    auto*t=ggml_graph_node(x->g,j);need(t->op!=GGML_OP_REPEAT,"REPEAT forbidden");
    bool supported=ggml_backend_dev_supports_op(dev,t);
    json node={{"op",ggml_op_name(t->op)},{"tensor",meta(t)},{"supported",supported}};
    if(t->op==GGML_OP_MUL_MAT)node["role"]=(t->src[0]==x->K?"QK":"AV");
    row["nodes"].push_back(node);if(!supported)row["support"]=false;
   }
   r["rows"].push_back(row);flush();
   need(row["support"].get<bool>(),"first unsupported graph");
   reference(*x);x->buf=ggml_backend_alloc_ctx_tensors(x->c,backend);need(x->buf,"allocation");
   for(int j=0;j<ggml_graph_n_nodes(x->g);j++){auto*t=ggml_graph_node(x->g,j);need(t->buffer&&ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer))==dev,"placement");}
   inputs(*x,true,"before");
   auto st=ggml_backend_graph_compute(backend,x->g);ggml_backend_synchronize(backend);need(st==GGML_STATUS_SUCCESS,"compute");r["computes"]=r["computes"].get<int>()+1;
   auto s=stage(*x,x->scores,"qk"),p=stage(*x,x->probs,"softmax"),a=stage(*x,x->values,"av");x->final=stage(*x,{x->out},"final");
   inputs(*x,false,"after");
   json checks={{"qk",check(s,x->sr)},{"softmax",check(p,x->pr)},{"av",check(a,x->ar)},{"final",check(x->final,x->ar)}};
   bool all=true;for(auto&c:checks.items())all&=c.value()["passed"].get<bool>();
   if(arm=="QB"){
    auto&prior=*graphs.back();need(prior.arm=="PQ"&&prior.q==q&&prior.n==n,"pair identity");
    for(auto name:{"qk","softmax","av","final"}){
     std::ifstream f(prior.dir/(std::string(name)+".f32"),std::ios::binary),g(x->dir/(std::string(name)+".f32"),std::ios::binary);
     std::vector<char>u((std::istreambuf_iterator<char>(f)),{}),v((std::istreambuf_iterator<char>(g)),{});
     bool equal=!u.empty()&&u==v;checks[std::string(name)+"_PQ_bytes"]={{"passed",equal},{"bytes",u.size()}};all&=equal;
    }
   }
   r["rows"].back()["checks"]=checks;r["rows"].back()["placement"]="ALL_B570";r["rows"].back()["numerical"]=all?"PASS":"FAIL";flush();
   need(all,"first numerical/reference failure");
   graphs.push_back(std::move(x));
  }
  cleanup();r["normal_cleanup_returned"]=true;r["status"]="GQA_PANEL_PASS";js(dest/"result.json",r);return 0;
 }catch(const std::exception&e){
  r["status"]="STOPPED_FIRST_FAILURE";r["error"]=e.what();cleanup();r["normal_cleanup_returned"]=true;
  if(!dest.empty())js(dest/"result.json",r);std::cerr<<e.what()<<"\n";return 2;
 }
}
