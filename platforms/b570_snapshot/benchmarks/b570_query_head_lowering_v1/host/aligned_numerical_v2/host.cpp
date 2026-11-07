#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include <filesystem>
#include "fixture.hpp"
#include "ggml-backend.h"
#include "ggml-alloc.h"
namespace fs=std::filesystem;
static json inventory(){HMODULE m[2048];DWORD n=0;need(EnumProcessModules(GetCurrentProcess(),m,sizeof(m),&n)!=0&&n<=sizeof(m),"modules");json a=json::array();
 for(unsigned i=0;i<n/sizeof(HMODULE);++i){char p[32768];need(GetModuleFileNameExA(GetCurrentProcess(),m[i],p,sizeof(p))!=0,"module path");a.push_back(p);}return a;}
#ifdef PANEL_CPU_AUDIT
int main(int argc,char**argv){try{
 need(argc==3,"CPU metadata: list.json output.jsonl");std::ifstream f(argv[1]);json paths;f>>paths;need(paths.size()==161,"all serialized slots");
 need(!fs::exists(argv[2]),"new CPU evidence");std::ofstream out(argv[2]);
 out<<json({{"event","CPU_START"},{"modules",inventory()},{"graph_computes",0},{"device_queries",0}}).dump()<<std::endl;
 for(auto&path:paths){std::ifstream w(path.get<std::string>());json r;w>>r;validate_request(r);
  auto emit=[&](const json&cell,const std::string&name){auto g=graph(cell,name);auto bytes=r.at("kind")=="graph"?input_bytes(g,r):std::vector<std::pair<ggml_tensor*,std::vector<char>>>{};
   json payload=json::array();for(auto&e:bytes)payload.push_back({{"tensor",g.id(e.first)},{"bytes",e.second.size()}});
   for(auto*t:g.all)need(t->data==nullptr&&t->buffer==nullptr,"metadata allocation only");
   out<<json({{"event","CPU_DESCRIPTOR"},{"slot_id",r.at("slot_id")},{"request",r},{"cell",cell},{"mode",name},{"graph",descriptor(g)},{"payload_sizes",payload}}).dump()<<std::endl;ggml_free(g.c);};
  if(r.at("kind")=="census")for(auto&cell:r.at("cells"))for(auto name:{"MQ","PQ","QH_C","QH_D","REPEAT4"})emit(cell,name);
  else emit(r.at("cell"),r.at("mode"));
 }
 out<<json({{"event","CPU_CLOSE"},{"modules",inventory()},{"graph_computes",0},{"device_queries",0}}).dump()<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}}
#else
static json capabilities(const Graph&g,ggml_backend_dev_t dev){json a=json::array();for(auto*t:g.nodes){auto z=meta(t);z["id"]=g.id(t);z["executable"]=executable(t);z["supports_op"]=ggml_backend_dev_supports_op(dev,t);a.push_back(z);}return a;}
static void write_bytes(const fs::path&p,const std::vector<char>&b){std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());need(bool(f),"byte output");}
static void raw_get(ggml_tensor*t,const fs::path&p){need(t->type==GGML_TYPE_F32&&ggml_is_contiguous(t),"contiguous full F32 stage");std::vector<char>b(ggml_nbytes(t));ggml_backend_tensor_get(t,b.data(),0,b.size());write_bytes(p,b);}
int main(int argc,char**argv){try{
 need(argc==3,"panel host requires exact approved wire/raw paths");std::ifstream f(argv[1]);json r;f>>r;validate_request(r);
 need(!fs::exists(argv[2]),"immutable raw");std::ofstream out(argv[2]);
 out<<json({{"event","HOST_START"},{"origin","NATIVE_VULKAN"},{"pid",GetCurrentProcessId()},{"request",r},{"modules_before",inventory()}}).dump()<<std::endl;
 char exe[MAX_PATH];GetModuleFileNameA(nullptr,exe,MAX_PATH);auto dir=fs::path(exe).parent_path();
 auto lib=LoadLibraryExA((dir/"ggml-vulkan.dll").string().c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(lib,"explicit frozen Vulkan load");
 auto init=(ggml_backend_t(*)(size_t))GetProcAddress(lib,"ggml_backend_vk_init");need(init,"init symbol");auto backend=init(0);need(backend,"backend0");auto dev=ggml_backend_get_device(backend);
 std::string description=ggml_backend_dev_description(dev);need(description.find("B570")!=std::string::npos,"wrong device");
 auto alignment=ggml_backend_buft_get_alignment(ggml_backend_get_default_buffer_type(backend));need(alignment==r.at("required_alignment_bytes").get<size_t>(),"frozen alignment condition changed");
 out<<json({{"event","DEVICE"},{"backend_name",ggml_backend_name(backend)},{"description",description},{"actual_alignment",alignment},{"modules",inventory()}}).dump()<<std::endl;
 auto memory=(void(*)(int,size_t*,size_t*))GetProcAddress(lib,"ggml_backend_vk_get_device_memory");need(memory,"memory symbol");
 auto checkpoint=[&](const char*p){size_t free=0,total=0;memory(0,&free,&total);out<<json({{"event","MEMORY_CHECKPOINT"},{"point",p},{"free",free},{"total",total},{"continuous",false}}).dump()<<std::endl;need(total>0&&free>=512ull*1024*1024,"memory headroom");};
 checkpoint("BACKEND_READY");out<<json({{"event","AWAIT_RUNTIME_GATE"},{"modules",inventory()}}).dump()<<std::endl;
 std::string gate;std::getline(std::cin,gate);need(gate=="GO","parent runtime gate");
 if(r.at("kind")=="census"){
  for(auto&cell:r.at("cells"))for(auto name:{"MQ","PQ","QH_C","QH_D","REPEAT4"}){auto g=graph(cell,name);
   out<<json({{"event","CAPABILITY"},{"cell",cell},{"mode",name},{"graph",descriptor(g)},{"nodes",capabilities(g,dev)},{"graph_compute",false}}).dump()<<std::endl;ggml_free(g.c);}
 }else{
  auto g=graph(r.at("cell"),r.at("mode"));auto desc=descriptor(g);auto caps=capabilities(g,dev);
  out<<json({{"event","PRECOMPUTE"},{"graph",desc},{"nodes",caps}}).dump()<<std::endl;
  for(auto&n:caps)if(n["executable"].get<bool>())need(n["supports_op"].get<bool>(),"unsupported node; stop");
  auto buffer=ggml_backend_alloc_ctx_tensors(g.c,backend);need(buffer,"direct allocation");json physical=json::array();
  for(auto*t:g.all){auto z=meta(t);z["id"]=g.id(t);z["view_root"]=g.id(t->view_src);
   z["offset"]=(uintptr_t)t->data-(uintptr_t)ggml_backend_buffer_get_base(t->buffer);z["buffer_bytes"]=ggml_backend_buffer_get_size(t->buffer);
   z["buffer_name"]=ggml_backend_buffer_name(t->buffer);z["device_matches"]=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer))==dev;physical.push_back(z);}
  out<<json({{"event","PHYSICAL_LAYOUT"},{"alignment",alignment},{"tensors",physical}}).dump()<<std::endl;
  auto bytes=input_bytes(g,r);fs::path dest=r.at("output_dir").get<std::string>();fs::create_directories(dest);
  for(size_t i=0;i<bytes.size();++i){auto&e=bytes[i];ggml_backend_tensor_set(e.first,e.second.data(),0,e.second.size());std::vector<char>b(e.second.size());ggml_backend_tensor_get(e.first,b.data(),0,b.size());need(b==e.second,"before input bytes");write_bytes(dest/("input-"+std::to_string(i)+".before.bin"),b);}
  json bindings=json::array();
  for(auto*t:g.nodes)if(executable(t)){
   json operands=json::array();std::vector<ggml_tensor*>v={t};for(auto*s:t->src)if(s)v.push_back(s);
   for(auto*s:v){need(s->buffer,"binding buffer");auto owner=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(s->buffer));need(owner==dev,"bound device mismatch");
    size_t o=(uintptr_t)s->data-(uintptr_t)ggml_backend_buffer_get_base(s->buffer);size_t delta=o%alignment;
    bool compensated=t->op==GGML_OP_CONT||t->op==GGML_OP_REPEAT||t->op==GGML_OP_CONCAT;
    if(!compensated)need(delta==0,"bound descriptor start must align");
    else {size_t limit=t->op==GGML_OP_CONCAT&&(s==t||s==t->src[1])?255:65535;
     need(delta%ggml_type_size(s->type)==0&&delta/ggml_type_size(s->type)<=limit,"compensated offset encoding");}
    operands.push_back({{"tensor",g.id(s)},{"offset",o},{"delta",delta},{"compensated_path",compensated},{"device_matches",true}});}
   bindings.push_back({{"node",g.id(t)},{"op",ggml_op_name(t->op)},{"operands",operands}});
  }
  out<<json({{"event","BINDINGS"},{"nodes",bindings},{"scope","Actual executable nodes and bound operands; disconnected old views do not impose descriptor alignment"}}).dump()<<std::endl;
  checkpoint("BEFORE_GRAPH");out<<json({{"event","GRAPH_START"}}).dump()<<std::endl;
  auto status=ggml_backend_graph_compute(backend,g.g);ggml_backend_synchronize(backend);
  out<<json({{"event","GRAPH_RETURN"},{"status",int(status)}}).dump()<<std::endl;need(status==GGML_STATUS_SUCCESS,"graph failed");
  for(size_t i=0;i<bytes.size();++i){auto&e=bytes[i];std::vector<char>b(e.second.size());ggml_backend_tensor_get(e.first,b.data(),0,b.size());need(b==e.second,"after input bytes");write_bytes(dest/("input-"+std::to_string(i)+".after.bin"),b);}
  for(size_t i=0;i<g.b.scores.size();++i){raw_get(g.b.scores[i],dest/("qk-"+std::to_string(i)+".f32"));raw_get(g.b.probs[i],dest/("sm-"+std::to_string(i)+".f32"));raw_get(g.b.values[i],dest/("av-"+std::to_string(i)+".f32"));}
  raw_get(g.b.out,dest/"final.f32");out<<json({{"event","GRAPH_OUTPUT"},{"input_bytes_unchanged",true},{"graph",desc}}).dump()<<std::endl;
  checkpoint("AFTER_GRAPH");ggml_backend_buffer_free(buffer);ggml_free(g.c);
 }
 checkpoint("CLOSE");out<<json({{"event","CLOSE"},{"modules",inventory()}}).dump()<<std::endl;ggml_backend_free(backend);FreeLibrary(lib);return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}}
#endif
