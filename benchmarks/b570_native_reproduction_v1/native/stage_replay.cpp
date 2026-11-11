#define NOMINMAX
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "query_head.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
using json=nlohmann::json;namespace fs=std::filesystem;
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
json readj(fs::path p){std::ifstream f(p);json j;f>>j;return j;}
std::vector<char> readb(fs::path p){std::ifstream f(p,std::ios::binary);need(bool(f),"missing raw file");return {(std::istreambuf_iterator<char>(f)),{}};}
void writej(fs::path p,const json&j){std::ofstream f(p);f<<j.dump(2)<<"\n";need(bool(f),"write JSON");}
int main(int argc,char**argv){
    ggml_backend_t backend=nullptr;ggml_context *ctx=nullptr;ggml_backend_buffer_t buf=nullptr;fs::path out;
    json result={{"status","STARTED"},{"rows",json::array()},{"performance_claim",false}};
    auto cleanup=[&](){if(buf){ggml_backend_buffer_free(buf);buf=nullptr;}if(ctx){ggml_free(ctx);ctx=nullptr;}};
    try{
        need(argc==3,"stage_replay FIXTURE OUTPUT");fs::path fixture=argv[1];out=argv[2];need(!fs::exists(out),"fresh output");fs::create_directories(out);
        ggml_backend_load_all();ggml_backend_dev_t dev=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();++i){auto*d=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d)).find("B570")!=std::string::npos){need(!dev,"ambiguous device");dev=d;}}
        need(dev,"B570 missing");backend=ggml_backend_dev_init(dev,nullptr);need(backend,"backend init");
        result["device"]=ggml_backend_dev_description(dev);
        for(int q:{1,2})for(std::string arm:{"PQ","QB"}){
            ctx=ggml_init({8*1024*1024,nullptr,true});need(ctx,"context");
            std::vector<std::pair<ggml_tensor*,std::vector<char>>> uploads;
            auto input=[&](std::string key){
                json j=readj(fixture/(key+".json"));auto bytes=readb(fixture/(key+".bin"));
                auto type=j["type"]=="f32"?GGML_TYPE_F32:GGML_TYPE_F16;
                need(bytes.size()==j["span_bytes"].get<size_t>(),"span mismatch");
                auto*storage=ggml_new_tensor_1d(ctx,type,(bytes.size()+ggml_type_size(type)-1)/ggml_type_size(type));
                auto*t=ggml_view_4d(ctx,storage,j["ne"][0],j["ne"][1],j["ne"][2],j["ne"][3],j["nb"][1],j["nb"][2],j["nb"][3],0);
                need(t->nb[0]==j["nb"][0].get<size_t>(),"element stride");uploads.push_back({storage,std::move(bytes)});return t;
            };
            auto*rawq=input("Q");auto*k=input("K");auto*v=input("V");auto*rawmask=input("mask");
            need(rawq->ne[0]==128&&rawq->ne[2]==32&&rawq->ne[3]==2&&k->ne[1]==512,"fixture domain");
            auto*Q=ggml_view_4d(ctx,rawq,128,q,32,1,rawq->nb[3],rawq->nb[2],rawq->nb[3]*2,0);
            auto*mask=ggml_view_4d(ctx,rawmask,512,q,1,1,rawmask->nb[3],rawmask->nb[3]*2,rawmask->nb[3]*2,0);
            auto built=hs_qh::build(ctx,arm=="PQ"?hs_qh::Mode::PQ:hs_qh::Mode::QB4,Q,k,v,mask,readj(fixture/"capture.json")["scale"]);
            if(built.common_original){
                auto*s=ggml_mul_mat(ctx,k,Q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);
                auto*p=ggml_soft_max_ext(ctx,s,mask,readj(fixture/"capture.json")["scale"],0);auto*a=ggml_mul_mat(ctx,v,p);
                built.scores={s};built.probs={p};built.values={a};built.out=ggml_cont_2d(ctx,ggml_permute(ctx,a,0,2,1,3),4096,q);
            }
            auto*g=ggml_new_graph(ctx);ggml_build_forward_expand(g,built.out);
            for(int i=0;i<ggml_graph_n_nodes(g);++i)need(ggml_backend_dev_supports_op(dev,ggml_graph_node(g,i)),"unsupported operation");
            buf=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buf,"allocation");
            for(auto&u:uploads)ggml_backend_tensor_set(u.first,u.second.data(),0,u.second.size());
            need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"compute");ggml_backend_synchronize(backend);
            json row={{"q",q},{"arm",arm},{"stages",json::object()},{"q1_control",q==1?"first query slice of real q2 fixture":"not applicable"}};
            auto compare=[&](const std::string&name,const std::vector<ggml_tensor*>&tensors){
                std::vector<char>actual;
                for(auto*t:tensors){need(ggml_is_contiguous(t),"output contiguous");size_t off=actual.size();actual.resize(off+ggml_nbytes(t));ggml_backend_tensor_get(t,actual.data()+off,0,ggml_nbytes(t));}
                auto expected=readb(fixture/(name+".bin"));need(actual.size()*2==expected.size()*size_t(q),"reference extent");
                bool equal=memcmp(actual.data(),expected.data(),actual.size())==0;
                std::ofstream f(out/("q"+std::to_string(q)+"-"+arm+"-"+name+".bin"),std::ios::binary);f.write(actual.data(),actual.size());
                row["stages"][name]={{"bytes",actual.size()},{"bitwise_equal",equal}};need(equal,"real captured stage mismatch");
            };
            compare("qk",built.scores);compare("softmax",built.probs);compare("av",built.values);compare("final",{built.out});
            result["rows"].push_back(row);writej(out/"result.json",result);cleanup();
        }
        ggml_backend_free(backend);backend=nullptr;result["status"]="STAGE_REPLAY_PASS";result["normal_cleanup_returned"]=true;writej(out/"result.json",result);return 0;
    }catch(const std::exception&e){cleanup();if(backend)ggml_backend_free(backend);result["status"]="FAILED";result["error"]=e.what();if(!out.empty())writej(out/"result.json",result);std::cerr<<e.what()<<"\n";return 2;}
}
