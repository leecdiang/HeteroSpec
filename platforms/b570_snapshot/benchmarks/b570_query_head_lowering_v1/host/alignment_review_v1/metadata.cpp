// Metadata and host byte addresses only: no backend load, device, or compute call.
#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include <fstream>
#include "fixture.hpp"
static json inventory() {
    HMODULE handles[2048]; DWORD count=0;
    fixture_need(EnumProcessModules(GetCurrentProcess(),handles,sizeof(handles),&count)!=0,"modules");
    json rows=json::array();
    for(unsigned i=0;i<count/sizeof(HMODULE);++i){char name[32768];
        fixture_need(GetModuleFileNameExA(GetCurrentProcess(),handles[i],name,sizeof(name))!=0,"module path");
        rows.push_back(name);
    }return rows;
}
static json meta(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},
    {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
    {"view_offset",t->view_offs},{"op_parameters",{t->op_params[0],t->op_params[1]}},{"bytes",ggml_nbytes(t)}};}
int main(int argc,char**argv){try{
    fixture_need(argc==3,"metadata cells.json output.jsonl");std::ifstream f(argv[1]);json cells;f>>cells;
    fixture_need(cells.size()==16,"fixed cells");std::ofstream out(argv[2]);
    out<<json({{"event","MODULES"},{"modules",inventory()},{"graph_computes",0},{"device_queries",0}}).dump()<<std::endl;
    for(auto&cell:cells)for(auto name:{"MQ","PQ","QB4","QH_C","QH_D","REPEAT4"})for(int policy=0;policy<3;++policy){
        auto g=graph(cell,name,policy==0?32:0,policy==2);
        std::vector<ggml_tensor*> all;
        for(auto*t=ggml_get_first_tensor(g.c);t;t=ggml_get_next_tensor(g.c,t))all.push_back(t);
        auto id=[&](ggml_tensor*t)->int{return t?int(std::find(all.begin(),all.end(),t)-all.begin()):-1;};
        json tensors=json::array(),walked=json::array(),order=json::array();
        for(auto*t:all){auto m=meta(t);m["ctx_id"]=id(t);m["view_root"]=id(t->view_src);m["src"]=json::array();
            for(auto*s:t->src)if(s)m["src"].push_back(id(s));
            fixture_need(t->data==nullptr&&t->buffer==nullptr,"metadata only");
            if(t->view_src)fixture_need(!t->view_src->view_src&&t->view_offs+ggml_nbytes(t)<=ggml_nbytes(t->view_src),"flattened view bounds");
            tensors.push_back(m);
        }
        for(size_t i=0;i<g.nodes.size();++i){auto m=meta(g.nodes[i]);m["id"]=i;m["ctx_id"]=id(g.nodes[i]);walked.push_back(m);}
        for(int i=0;i<ggml_graph_n_nodes(g.g);++i)order.push_back(id(ggml_graph_node(g.g,i)));
        json bindings=json::array();for(auto&b:g.slabs)bindings.push_back({{"ctx_id",id(b.first)},{"source_offset",b.second},{"bytes",ggml_nbytes(b.first)}});
        out<<json({{"event","GRAPH_METADATA"},{"cell",cell},{"mode",name},{"policy",policy},
            {"Q",id(g.q)},{"K",id(g.k)},{"V",id(g.v)},{"mask",id(g.m)},
            {"tensors",tensors},{"walk",walked},{"execution_order",order},{"mask_slabs",bindings}}).dump()<<std::endl;
        ggml_free(g.c);
    }
    out<<json({{"event","CLOSE"},{"modules",inventory()},{"graphs_built_without_compute",288}}).dump()<<std::endl;
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 50;}}
