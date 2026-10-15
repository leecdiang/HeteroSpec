// Separate CPU metadata program. The frozen numerical host is included under
// its CPU-only branch, with its old entry renamed and never called.
#define PANEL_CPU_AUDIT
#define main unused_frozen_CPU_entry
#include "generated/host.cpp"
#undef main
int main(int argc,char**argv){try{
 need(argc==3,"CPU list and output required");std::ifstream f(argv[1]);json paths;f>>paths;need(paths.size()==69,"all targeted serialized slots");
 need(!fs::exists(argv[2]),"exclusive CPU evidence");std::ofstream out(argv[2]);
 out<<json({{"event","CPU_START"},{"pid",GetCurrentProcessId()},{"modules",inventory()},{"graph_computes",0},{"device_queries",0}}).dump()<<std::endl;
 for(auto&path:paths){std::ifstream w(path.get<std::string>());json r;w>>r;validate_request(r);
  auto emit=[&](const json&cell,const std::string&name){auto g=graph(cell,name);auto bytes=r.at("kind")=="graph"?input_bytes(g,r):std::vector<std::pair<ggml_tensor*,std::vector<char>>>{};
   json payload=json::array();for(auto&e:bytes)payload.push_back({{"tensor",g.id(e.first)},{"bytes",e.second.size()}});
   for(auto*t:g.all)need(t->data==nullptr&&t->buffer==nullptr,"CPU metadata allocation only");
   out<<json({{"event","CPU_DESCRIPTOR"},{"slot_id",r.at("slot_id")},{"request",r},{"cell",cell},{"mode",name},{"graph",descriptor(g)},{"payload_sizes",payload}}).dump()<<std::endl;ggml_free(g.c);};
  if(r.at("kind")=="census")for(auto&cell:r.at("cells"))for(auto name:{"MQ","PQ","QH_C","QH_D","REPEAT4"})emit(cell,name);
  else emit(r.at("cell"),r.at("mode"));
 }
 out<<json({{"event","CPU_CLOSE"},{"modules",inventory()},{"graph_computes",0},{"device_queries",0}}).dump()<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}}
