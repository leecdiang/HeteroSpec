#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include <fstream>
#include <iostream>
#include <set>
#include <array>
#include "oracle.hpp"
#include "local_attention.h"
using Compute=int(*)(ggml_context*,ggml_cgraph*,int);
static json module_inventory(){
 HMODULE hs[2048];DWORD bytes=0;require(EnumProcessModules(GetCurrentProcess(),hs,sizeof(hs),&bytes)!=0,"module enumeration");
 require(bytes<=sizeof(hs),"module inventory overflow");json a=json::array();
 for(unsigned i=0;i<bytes/sizeof(HMODULE);++i){char name[32768];require(GetModuleFileNameExA(GetCurrentProcess(),hs[i],name,sizeof(name))!=0,"module path");
  std::string s=name,low=s;std::transform(low.begin(),low.end(),low.begin(),[](unsigned char c){return char(std::tolower(c));});
  for(auto bad:{"vulkan","cuda","cublas","cudnn","igvk","nvoglv","llama"})require(low.find(bad)==std::string::npos,"forbidden GPU/model module");
  if(low.find("ggml-")!=std::string::npos)require(low.find("ggml-base.dll")!=std::string::npos||low.find("ggml-cpu.dll")!=std::string::npos,"non-CPU ggml module");
  a.push_back(s);
 }return a;
}
static size_t offset(ggml_tensor*t,int a,int b=0,int c=0,int d=0){
 return size_t(a)*t->nb[0]+size_t(b)*t->nb[1]+size_t(c)*t->nb[2]+size_t(d)*t->nb[3];
}
static float get(ggml_tensor*t,int a,int b=0,int c=0,int d=0){return *reinterpret_cast<float*>(static_cast<char*>(t->data)+offset(t,a,b,c,d));}
static json meta(ggml_tensor*t){
 json x={{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},
 {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
 {"view_offset",t->view_offs},{"prec_flag",t->op_params[0]}};
 if(t->view_src)x["owner"]="view_src";else x["owner"]="context_allocation";
 return x;
}
static void walk(ggml_tensor*t,std::vector<ggml_tensor*>&xs){
 if(!t||std::find(xs.begin(),xs.end(),t)!=xs.end())return;
 for(auto*s:t->src)walk(s,xs);xs.push_back(t);
}
static ggml_tensor *original(ggml_context*c,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m,int nq,int nh){
 auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);
 auto*p=ggml_soft_max_ext(c,s,m,.125f,0.0f);
 auto*a=ggml_mul_mat(c,v,p);auto*r=ggml_permute(c,a,0,2,1,3);
 return ggml_cont_2d(c,r,128*nh,nq);
}
struct Input {Logical l;int storage,mask,pattern;std::vector<float>q,m;std::vector<uint16_t>k,v;};
template<class T>static void readvec(std::ifstream&f,std::vector<T>&v,size_t n){v.resize(n);f.read((char*)v.data(),n*sizeof(T));require(bool(f),"truncated input");}
static Input read_input(const std::string&path){
 std::ifstream f(path,std::ios::binary);int hdr[7];f.read((char*)hdr,sizeof(hdr));require(bool(f),"header");
 Input a;auto&l=a.l;l.nq=hdr[0];l.nk=hdr[1];l.nh=hdr[2];l.nv=hdr[3];a.storage=hdr[4];a.mask=hdr[5];a.pattern=hdr[6];
 require((l.nq==1||l.nq==2)&&l.nk>=127&&l.nk<=257&&l.nh%l.nv==0,"input geometry");
 readvec(f,a.q,l.nq*l.nh*128);readvec(f,a.k,l.nv*l.nk*128);readvec(f,a.v,l.nv*128*l.nk);readvec(f,a.m,32*l.nk);
 require(f.peek()==EOF,"extra input");
 l.q.assign(a.q.begin(),a.q.end());for(auto x:a.k)l.k.push_back(half_value(x));for(auto x:a.v)l.v.push_back(half_value(x));
 l.mask.assign(a.m.begin(),a.m.begin()+l.nq*l.nk);l.solve();return a;
}
static json execute(Input&a,Compute compute){
 auto&l=a.l;int nq=l.nq,nk=l.nk,nh=l.nh,nv=l.nv;
 ggml_init_params pars{128*1024*1024,nullptr,false};auto*c=ggml_init(pars);require(c!=nullptr,"context");
 size_t baseoff=a.storage?32:0;
 auto*base=ggml_new_tensor_1d(c,GGML_TYPE_F32,128*nh*nq+baseoff/4);
 auto*q=ggml_view_4d(c,base,128,nq,nh,1,a.storage?512*nh:512,a.storage?512:512*nq,512*nh*nq,baseoff);
 auto*k=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,nk,nv,1);
 auto*v=ggml_new_tensor_4d(c,GGML_TYPE_F16,nk,128,nv,1);
 auto*m=ggml_new_tensor_4d(c,GGML_TYPE_F32,nk,32,1,1);
 for(int j=0;j<nq;++j)for(int h=0;h<nh;++h)for(int d=0;d<128;++d)
  *reinterpret_cast<float*>(static_cast<char*>(q->data)+offset(q,d,j,h))=a.q[l.qi(j,h,d)];
 std::memcpy(k->data,a.k.data(),a.k.size()*2);std::memcpy(v->data,a.v.data(),a.v.size()*2);std::memcpy(m->data,a.m.data(),a.m.size()*4);
 json out={{"geometry",{{"q",nq},{"k",nk},{"h",nh},{"hk",nv},{"storage",a.storage},{"mask",a.mask},{"pattern",a.pattern}}},
 {"inputs",{{"q",meta(q)},{"k",meta(k)},{"v",meta(v)},{"mask",meta(m)}}}};
 uint64_t addresses=0;
 for(int layout=0;layout<3;++layout){
  auto*result=(layout==0||nq==1)?original(c,q,k,v,m,nq,nh):b570_local_attention(c,layout,q,k,v,m,.125f);
  if(nq==1)require(b570_local_attention(c,layout,q,k,v,m,.125f)==nullptr,"q1 delegation");
  auto*g=ggml_new_graph(c);ggml_build_forward_expand(g,result);
  std::vector<ggml_tensor*>nodes;walk(result,nodes);json metadata=json::array();
  std::vector<ggml_tensor*>soft;for(auto*t:nodes){metadata.push_back(meta(t));if(t->op==GGML_OP_SOFT_MAX)soft.push_back(t);}
  require(soft.size()==size_t(layout==1&&nq==2?2:1),"real graph softmax count");
  // Logical storage formula is independent of graph qi/mi views.
  for(size_t z=0;z<soft.size();++z){auto*probs=soft[z];auto*scores=probs->src[0];auto*qi=scores->src[1];auto*mi=probs->src[1];
   for(int j=0;j<nq;++j){if(layout==1&&nq==2&&int(z)!=j)continue;
    int col=(layout==0||nq==1)?j:0,batch=(layout==2&&nq==2)?j:0;
    for(int h=0;h<nh;++h){
     for(int d=0;d<128;++d){
      size_t expected=baseoff+4*(a.storage?((j*nh+h)*128+d):((h*nq+j)*128+d));
      size_t actual=size_t(static_cast<char*>(qi->data)-static_cast<char*>(base->data))+offset(qi,d,col,h,batch);
      require(actual==expected&&actual+4<=ggml_nbytes(base),"Q address/bounds");++addresses;
     }
     // Actual mul_mat source0 broadcast divides destination head/batch by repetition.
     int kh=h/(scores->ne[2]/k->ne[2]),kb=batch/(scores->ne[3]/k->ne[3]);
     require(kh==h/(nh/nv)&&kb==0,"GQA/fourth-axis broadcast");
     for(int p=0;p<nk;++p){
      size_t actual=size_t(static_cast<char*>(mi->data)-static_cast<char*>(m->data))+offset(mi,p,col,h%mi->ne[2],batch%mi->ne[3]);
      require(actual==size_t(j*nk+p)*4&&actual+4<=ggml_nbytes(m),"mask address");++addresses;
      for(int d=0;d<128;++d){
       require(offset(k,d,p,kh,kb)==size_t(((h/(nh/nv))*nk+p)*128+d)*2,"K address");
       require(offset(v,p,d,kh,kb)==size_t(((h/(nh/nv))*128+d)*nk+p)*2,"V address");addresses+=2;
      }
     }
    }
   }
  }
  require(compute(c,g,1)==0,"CPU compute failed");
  Metric scores_metric,probs_metric,av_metric,perm_metric,final_metric;
  for(size_t z=0;z<soft.size();++z){auto*p=soft[z];auto*s=p->src[0];ggml_tensor*av=nullptr,*perm=nullptr;
   for(auto*t:nodes){if(t->op==GGML_OP_MUL_MAT&&t->src[1]==p)av=t;}
   require(av!=nullptr,"AV node");for(auto*t:nodes)if(t->op==GGML_OP_PERMUTE&&t->src[0]==av)perm=t;
   require(perm!=nullptr,"permute node");
   require(s->ne[0]==nk&&s->ne[2]==nh&&av->ne[0]==128,"stage shape");
   for(int j=0;j<nq;++j){if(layout==1&&nq==2&&int(z)!=j)continue;
    int col=(layout==0||nq==1)?j:0,batch=(layout==2&&nq==2)?j:0;
    for(int h=0;h<nh;++h){
     for(int key=0;key<nk;++key){json co={j,h,key};double se=l.score[l.si(j,h,key)],pe=l.prob[l.si(j,h,key)];
      scores_metric.add(get(s,key,col,h,batch),se,co);probs_metric.add(get(p,key,col,h,batch),pe,co);
      if(a.pattern==0)require(double(get(s,key,col,h,batch))==se,"structured QK exact");
      if(a.pattern==0&&a.mask==2)require(double(get(p,key,col,h,batch))==pe,"single-key softmax exact");
     }
     for(int d=0;d<128;++d){json co={j,h,d};double expected=l.value[l.qi(j,h,d)];
      av_metric.add(get(av,d,col,h,batch),expected,co);perm_metric.add(get(perm,d,h,col,batch),expected,co);
      require(offset(perm,d,h,col,batch)==offset(av,d,col,h,batch),"permute address");++addresses;
      if(a.pattern==0&&a.mask==2)require(double(get(av,d,col,h,batch))==expected,"single-key AV exact");
     }
    }
   }
  }
  require(result->ne[0]==128*nh&&result->ne[1]==nq&&ggml_is_contiguous(result),"final shape/stride");
  for(int j=0;j<nq;++j)for(int h=0;h<nh;++h)for(int d=0;d<128;++d){double e=l.value[l.qi(j,h,d)];
   final_metric.add(get(result,h*128+d,j),e,{j,h,d});++addresses;
   if(a.pattern==0&&a.mask==2)require(double(get(result,h*128+d,j))==e,"single-key final exact");
  }
  out["layouts"].push_back({{"layout",layout},{"common_original_path",nq==1},{"graph",metadata},
   {"QK",scores_metric.result()},{"softmax",probs_metric.result()},{"AV",av_metric.result()},
   {"permute",perm_metric.result()},{"final",final_metric.result()}});
 }
 out["address_checks"]=addresses;out["structured_strict_checks"]=a.pattern==0;
 ggml_free(c);return out;
}
int main(int argc,char**argv){
 try{
  require(argc==3,"usage: cpu.exe fixtures-list.json output.jsonl");auto initial=module_inventory();
  char exe[MAX_PATH];GetModuleFileNameA(nullptr,exe,MAX_PATH);std::string dir=exe;dir=dir.substr(0,dir.find_last_of("\\/"));
  auto lib=LoadLibraryExA((dir+"/ggml-cpu.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
  require(lib!=nullptr,"explicit CPU load");auto compute=(Compute)GetProcAddress(lib,"ggml_graph_compute_with_ctx");require(compute!=nullptr,"CPU symbol");
  auto loaded=module_inventory();std::ifstream listfile(argv[1]);json list;listfile>>list;
  std::ofstream output(argv[2],std::ios::out|std::ios::app);
  output<<json({{"event","MODULES"},{"entry",initial},{"loaded",loaded}}).dump()<<std::endl;
  for(auto&f:list){
   auto before=module_inventory();auto a=read_input(f["path"]);auto result=execute(a,compute);auto after=module_inventory();
   require(before==loaded&&after==loaded,"module inventory changed");result["id"]=f["id"];result["input_sha256"]=f["sha256"];
   result["modules_before_after_equal_loaded"]=true;result["event"]="FIXTURE";output<<result.dump()<<std::endl;
  }
  output<<json({{"event","CLOSE"},{"modules",module_inventory()},{"gpu_starts",0}}).dump()<<std::endl;
  FreeLibrary(lib);return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}
}
