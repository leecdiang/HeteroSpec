// Offline-compiled S1 host. Never invoked during S0, including for --help.
#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include "oracle.hpp"
#include "query_head.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include <filesystem>
#include <fstream>
#include <iostream>
namespace fs=std::filesystem;
static json inventory(){HMODULE m[2048];DWORD n=0;require(EnumProcessModules(GetCurrentProcess(),m,sizeof(m),&n)!=0,"module inventory");require(n<=sizeof(m),"module overflow");json a=json::array();for(unsigned i=0;i<n/sizeof(HMODULE);++i){char p[32768];require(GetModuleFileNameExA(GetCurrentProcess(),m[i],p,sizeof(p))!=0,"module path");a.push_back(p);}return a;}
static json metadata(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},{"view_offset",t->view_offs},{"op_parameters",{t->op_params[0],t->op_params[1]}}};}
static void walk(ggml_tensor*t,std::vector<ggml_tensor*>&v){if(!t||std::find(v.begin(),v.end(),t)!=v.end())return;for(auto*s:t->src)walk(s,v);v.push_back(t);}
static bool executable(ggml_tensor*t){return t->op!=GGML_OP_NONE&&t->op!=GGML_OP_VIEW&&t->op!=GGML_OP_RESHAPE&&t->op!=GGML_OP_PERMUTE&&t->op!=GGML_OP_TRANSPOSE;}
static hs_qh::Built common(ggml_context*c,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m){hs_qh::Built b;b.common_original=true;
 auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);auto*p=ggml_soft_max_ext(c,s,m,float(1/std::sqrt(128.0)),0);auto*a=ggml_mul_mat(c,v,p);
 b.scores={s};b.probs={p};b.values={a};auto*r=ggml_permute(c,a,0,2,1,3);b.out=ggml_cont_2d(c,r,128*q->ne[2],q->ne[1]);return b;}
struct Graph{ggml_context*c;ggml_tensor*base,*q,*k,*v,*m;hs_qh::Built built;ggml_cgraph*g;std::vector<ggml_tensor*>nodes;};
static hs_qh::Mode mode(std::string s){if(s=="MQ")return hs_qh::Mode::MQ;if(s=="PQ")return hs_qh::Mode::PQ;if(s=="QH_C")return hs_qh::Mode::QH_C;if(s=="QH_D")return hs_qh::Mode::QH_D;if(s=="REPEAT4")return hs_qh::Mode::REPEAT4;throw std::runtime_error("unplanned GPU mode");}
static Graph graph(json cell,std::string name){auto shape=cell["geometry"];int q=shape["q"],n=shape["n"],h=shape["h"],hk=shape["hk"];
 require(shape["d"]==128&&shape["dv"]==128&&shape["storage"]=="permuted"&&q>=1&&q<=4&&(n==63||n==257)&&h==8&&(hk==8||hk==2),"S1 frozen shape");
 ggml_init_params init{16*1024*1024,nullptr,true};Graph x{};x.c=ggml_init(init);require(x.c,"metadata context");
 x.base=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,8+128*h*q);x.q=ggml_view_4d(x.c,x.base,128,q,h,1,512*h,512,512*h*q,32);
 x.k=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,128,n,hk,1);x.v=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,n,128,hk,1);x.m=ggml_new_tensor_4d(x.c,GGML_TYPE_F32,n,32,1,1);
 x.built=hs_qh::build(x.c,mode(name),x.q,x.k,x.v,x.m,float(1/std::sqrt(128.0)));if(x.built.common_original)x.built=common(x.c,x.q,x.k,x.v,x.m);
 x.g=ggml_new_graph(x.c);ggml_build_forward_expand(x.g,x.built.out);walk(x.built.out,x.nodes);return x;}
static json capability(Graph&x,ggml_backend_dev_t dev){json a=json::array();for(size_t i=0;i<x.nodes.size();++i){auto*t=x.nodes[i];json n=metadata(t);n["id"]=i;n["executable"]=executable(t);n["supports_op"]=ggml_backend_dev_supports_op(dev,t);a.push_back(n);}return a;}
static void raw_get(ggml_tensor*t,const fs::path&file){require(t->type==GGML_TYPE_F32&&ggml_is_contiguous(t),"stage F32");std::vector<char>b(ggml_nbytes(t));ggml_backend_tensor_get(t,b.data(),0,b.size());std::ofstream f(file,std::ios::binary);f.write(b.data(),b.size());require(bool(f),"output write");}
int main(int argc,char**argv){
 try{require(argc==3,"usage: qh-vulkan request.json raw.jsonl; S1 F0 approval required");std::ifstream f(argv[1]);json request;f>>request;
  require(request["study"]=="b570-query-head-lowering-v1"&&request["F0_sha256"].get<std::string>().size()==64,"bound request");
  require(!fs::exists(argv[2]),"immutable output");std::ofstream out(argv[2]);out<<json({{"event","HOST_START"},{"pid",GetCurrentProcessId()},{"request",request},{"modules_before",inventory()}}).dump()<<std::endl;
  char exe[MAX_PATH];GetModuleFileNameA(nullptr,exe,MAX_PATH);auto dir=fs::path(exe).parent_path();auto lib=LoadLibraryExA((dir/"ggml-vulkan.dll").string().c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
  require(lib,"explicit frozen Vulkan load");auto init=(ggml_backend_t(*)(size_t))GetProcAddress(lib,"ggml_backend_vk_init");require(init,"vk init symbol");auto backend=init(0);require(backend,"Vulkan backend0");auto dev=ggml_backend_get_device(backend);
  std::string description=ggml_backend_dev_description(dev);out<<json({{"event","DEVICE"},{"backend_name",ggml_backend_name(backend)},{"description",description},{"modules",inventory()}}).dump()<<std::endl;
  require(description.find("B570")!=std::string::npos,"device identity mismatch; no alternate-device retry");
  auto memory=(void(*)(int,size_t*,size_t*))GetProcAddress(lib,"ggml_backend_vk_get_device_memory");require(memory,"memory API");
  auto checkpoint=[&](const char*point){size_t free=0,total=0;memory(0,&free,&total);
   out<<json({{"event","MEMORY_CHECKPOINT"},{"point",point},{"backend_reported_free_bytes",free},{"backend_reported_total_bytes",total},{"continuous_residency",false}}).dump()<<std::endl;
   require(total>0&&free>=512ull*1024*1024,"checkpoint memory headroom gate");};
  checkpoint("BACKEND_READY");
  out<<json({{"event","AWAIT_RUNTIME_GATE"},{"modules",inventory()}}).dump()<<std::endl;
  std::string gate;std::getline(std::cin,gate);require(gate=="GO","parent did not admit exact runtime before support/compute");
  if(request["kind"]=="capability_only"){
   require(request["cells"].size()==16,"complete census cells");for(auto&cell:request["cells"])for(auto name:{"MQ","PQ","QH_C","QH_D","REPEAT4"}){
    auto g=graph(cell,name);out<<json({{"event","CAPABILITY"},{"cell",cell},{"mode",name},{"nodes",capability(g,dev)},{"graph_compute",false}}).dump()<<std::endl;ggml_free(g.c);
   }
  }else{
   require(request["kind"]=="graph","request kind");auto cell=request["cell"];auto g=graph(cell,request["mode"]);auto caps=capability(g,dev);
   out<<json({{"event","PRECOMPUTE_CAPABILITY"},{"nodes",caps}}).dump()<<std::endl;
   for(auto&n:caps)if(n["executable"].get<bool>())require(n["supports_op"].get<bool>(),"unsupported executable node; no fallback");
   auto buffer=ggml_backend_alloc_ctx_tensors(g.c,backend);require(buffer,"direct Vulkan tensor allocation");
   std::ifstream in(request["input"].get<std::string>(),std::ios::binary);int hdr[7];in.read((char*)hdr,sizeof(hdr));auto sh=cell["geometry"];int nq=sh["q"],nh=sh["h"],nk=sh["n"],nv=sh["hk"];
   require(hdr[0]==nq&&hdr[1]==nk&&hdr[2]==nh&&hdr[3]==nv&&hdr[4]==1&&hdr[5]==0&&hdr[6]==0,"wire/input descriptor mismatch");
   std::vector<float>logical(128*nh*nq),physical(8+128*nh*nq);in.read((char*)logical.data(),logical.size()*4);
   for(int j=0;j<nq;++j)for(int h=0;h<nh;++h)for(int d=0;d<128;++d)physical[8+(j*nh+h)*128+d]=logical[(j*nh+h)*128+d];
   std::vector<char>kb(128*nk*nv*2),vb(128*nk*nv*2),mb(32*nk*4);in.read(kb.data(),kb.size());in.read(vb.data(),vb.size());in.read(mb.data(),mb.size());require(bool(in)&&in.peek()==EOF,"input size");
   std::vector<std::pair<ggml_tensor*,std::vector<char>>> inputbytes={{g.base,std::vector<char>((char*)physical.data(),(char*)physical.data()+physical.size()*4)},{g.k,kb},{g.v,vb},{g.m,mb}};
   fs::path dest=request["output_dir"].get<std::string>();fs::create_directories(dest);
   auto save_input=[&](size_t i,const char*when,const std::vector<char>&data){std::ofstream f(dest/("input-"+std::to_string(i)+"."+when+".bin"),std::ios::binary);f.write(data.data(),data.size());require(bool(f),"input identity bytes write");};
   for(size_t i=0;i<inputbytes.size();++i){auto&e=inputbytes[i];ggml_backend_tensor_set(e.first,e.second.data(),0,e.second.size());std::vector<char>read(e.second.size());ggml_backend_tensor_get(e.first,read.data(),0,read.size());require(read==e.second,"before-compute input bytes");save_input(i,"before",read);}
   json assignments=json::array();for(size_t i=0;i<g.nodes.size();++i){auto*t=g.nodes[i];if(!executable(t))continue;require(t->buffer,"node allocated buffer");
    auto owner=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer));require(owner==dev,"buffer/device assignment; no CPU fallback");
    assignments.push_back({{"id",i},{"node",metadata(t)},{"direct_execution_backend",ggml_backend_name(backend)},{"buffer_name",ggml_backend_buffer_name(t->buffer)},{"device_matches",true}});
   }
   out<<json({{"event","ASSIGNMENT_BEFORE_COMPUTE"},{"nodes",assignments},{"scope","direct backend graph call plus actual buffer-device ownership, not individual shader timestamps"}}).dump()<<std::endl;
   checkpoint("BEFORE_GRAPH");
   out<<json({{"event","GRAPH_START"}}).dump()<<std::endl;auto status=ggml_backend_graph_compute(backend,g.g);ggml_backend_synchronize(backend);
   out<<json({{"event","GRAPH_RETURN"},{"status",int(status)}}).dump()<<std::endl;require(status==GGML_STATUS_SUCCESS,"Vulkan graph result");
   for(size_t i=0;i<inputbytes.size();++i){auto&e=inputbytes[i];std::vector<char>read(e.second.size());ggml_backend_tensor_get(e.first,read.data(),0,read.size());require(read==e.second,"after-compute input bytes");save_input(i,"after",read);}
   json stages=json::array();
   for(size_t i=0;i<g.built.scores.size();++i){raw_get(g.built.scores[i],dest/("qk-"+std::to_string(i)+".f32"));raw_get(g.built.probs[i],dest/("sm-"+std::to_string(i)+".f32"));raw_get(g.built.values[i],dest/("av-"+std::to_string(i)+".f32"));stages.push_back({{"part",i},{"QK",metadata(g.built.scores[i])},{"softmax",metadata(g.built.probs[i])},{"AV",metadata(g.built.values[i])}});}
   raw_get(g.built.out,dest/"final.f32");out<<json({{"event","GRAPH_OUTPUT"},{"stages",stages},{"final",metadata(g.built.out)},{"input_bytes_unchanged",true}}).dump()<<std::endl;checkpoint("AFTER_GRAPH");
   ggml_backend_buffer_free(buffer);ggml_free(g.c);
  }
  checkpoint("CLOSE");out<<json({{"event","CLOSE"},{"modules",inventory()}}).dump()<<std::endl;ggml_backend_free(backend);FreeLibrary(lib);return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}
}
