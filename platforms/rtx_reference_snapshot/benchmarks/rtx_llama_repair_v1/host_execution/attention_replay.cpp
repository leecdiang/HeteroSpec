#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
#include <stdexcept>
#include <chrono>
using json=nlohmann::json;
namespace fs=std::filesystem;
void need(bool x,const char* message){if(!x)throw std::runtime_error(message);}
std::vector<char> read_bytes(const fs::path& p){
    std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"operand open");
    auto n=f.tellg();need(n>0&&n<=64*1024*1024,"operand reservation");
    std::vector<char> b(static_cast<size_t>(n));f.seekg(0);f.read(b.data(),b.size());need(bool(f),"operand read");return b;
}
json modules(){
    HMODULE handles[1024];DWORD bytes=0;
    need(EnumProcessModules(GetCurrentProcess(),handles,sizeof(handles),&bytes),"module inventory");
    need(bytes<=sizeof(handles),"module inventory truncated");json result=json::array();
    for(size_t i=0;i<bytes/sizeof(HMODULE);++i){char path[32768];need(GetModuleFileNameExA(GetCurrentProcess(),handles[i],path,sizeof(path)),"module path");result.push_back(std::string(path));}
    return result;
}
int main(int argc,char** argv){
    try{
        SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
        need(argc==4,"manifest output DLL directory");json spec;{std::ifstream f(argv[1]);f>>spec;}
        fs::path out=argv[2];need(!fs::exists(out),"fresh output required");fs::create_directories(out);
        need(spec["cases"].size()>0&&spec["cases"].size()<=256,"case reservation");
        ggml_backend_load_all_from_path(argv[3]);auto backend=ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_GPU,nullptr);need(backend,"CUDA backend required");
        std::cout<<json({{"event","READY"}}).dump()<<std::endl;
        std::string permission;std::getline(std::cin,permission);need(permission=="RUN","owned execution handshake");
        json result={{"status","RUNNING"},{"model_requests",0},{"results",json::array()}};
        for(const auto& item:spec["cases"])for(int repetition=0;repetition<2;++repetition){
            need(item["backend"]==ggml_backend_name(backend),"captured scheduler backend differs");
            auto start=std::chrono::steady_clock::now();auto* ctx=ggml_init({4*1024*1024,nullptr,true});need(ctx,"graph context");
            std::vector<ggml_tensor*> inputs;std::vector<std::vector<char>> payloads;
            need(item["inputs"].size()==2,"two real operator inputs required");
            for(const auto& input:item["inputs"]){
                std::string kind=input["type"];need(kind=="f16"||kind=="f32","input type");
                auto ne=input["ne"].get<std::vector<int64_t>>();auto nb=input["nb"].get<std::vector<size_t>>();
                need(ne.size()==4&&nb.size()==4,"input descriptor");
                int64_t elements=1;for(auto dim:ne){need(dim>0&&dim<=16*1024*1024,"input dimension");elements*=dim;need(elements<=16*1024*1024,"input elements");}
                auto* t=ggml_new_tensor_4d(ctx,kind=="f16"?GGML_TYPE_F16:GGML_TYPE_F32,ne[0],ne[1],ne[2],ne[3]);
                for(int axis=0;axis<4;++axis)t->nb[axis]=nb[axis];ggml_set_input(t);
                auto bytes=read_bytes(input["file"].get<std::string>());need(bytes.size()==ggml_nbytes(t),"input span/stride mismatch");
                inputs.push_back(t);payloads.push_back(std::move(bytes));
            }
            std::string op=item["op"];ggml_tensor* output=nullptr;
            if(op=="MUL_MAT")output=ggml_mul_mat(ctx,inputs[0],inputs[1]);
            else if(op=="SOFT_MAX")output=ggml_soft_max_ext(ctx,inputs[0],inputs[1],1.0f,0.0f);
            else throw std::runtime_error("unreviewed replay operator");
            auto params=item["op_params_i32"].get<std::vector<int32_t>>();need(params.size()*4==GGML_MAX_OP_PARAMS,"complete operator parameters");
            std::memcpy(output->op_params,params.data(),GGML_MAX_OP_PARAMS);
            auto* graph=ggml_new_graph_custom(ctx,128,false);ggml_build_forward_expand(graph,output);
            auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer,"operator allocation");
            for(size_t i=0;i<inputs.size();++i)ggml_backend_tensor_set(inputs[i],payloads[i].data(),0,payloads[i].size());
            need(ggml_backend_graph_compute(backend,graph)==GGML_STATUS_SUCCESS,"native operator compute");ggml_backend_synchronize(backend);
            std::vector<char> bytes(ggml_nbytes(output));ggml_backend_tensor_get(output,bytes.data(),0,bytes.size());
            auto name=item["name"].get<std::string>()+"_"+std::to_string(repetition)+".bin";need(fs::path(name).filename()==name,"output name");
            {std::ofstream f(out/name,std::ios::binary);f.write(bytes.data(),bytes.size());need(bool(f),"output write");}
            result["results"].push_back({{"case",item["name"]},{"repetition",repetition},{"backend",ggml_backend_name(backend)},{"file",name},{"bytes",bytes.size()},
                {"ne",{output->ne[0],output->ne[1],output->ne[2],output->ne[3]}},{"nb",{output->nb[0],output->nb[1],output->nb[2],output->nb[3]}},
                {"seconds",std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()}});
            ggml_backend_buffer_free(buffer);ggml_free(ctx);
        }
        result["modules"]=modules();ggml_backend_free(backend);result["normal_cleanup_returned"]=true;
        result["operator_replays"]=result["results"].size();result["status"]="COMPLETE";
        {std::ofstream f(out/"RESULT.json");f<<result.dump(2)<<'\n';need(bool(f),"result write");}
        std::cout<<json({{"event","COMPLETE"},{"operator_replays",result["operator_replays"]}}).dump()<<std::endl;return 0;
    }catch(const std::exception& e){std::cerr<<"ATTENTION_REPLAY_FAILURE "<<e.what()<<'\n';return 2;}
}
