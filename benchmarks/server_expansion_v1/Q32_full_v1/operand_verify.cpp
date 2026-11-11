// Standalone ORIGINAL per-type CUDA scalar-MMVQ recipe on captured32B operands.
// Full model/transactions are checked separately. No toy weights or activations.
#include "llama.h"
#include "llama-model.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "linux_platform.hpp"
#include <nlohmann/json.hpp>
extern "C" {
#include "hash/sha256/sha256.h"
}
#include <fstream>
#include <filesystem>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <cstring>
#include <cmath>
using json=nlohmann::json;namespace fs=std::filesystem;
static void need(bool x,const char*s){if(!x)throw std::runtime_error(s);}
static json read(const fs::path&p){std::ifstream f(p);json x;f>>x;need(bool(f),"read JSON");return x;}
static std::vector<uint8_t> bytes(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"read bytes");auto n=f.tellg();f.seekg(0);std::vector<uint8_t>b(n);f.read(reinterpret_cast<char*>(b.data()),n);need(bool(f),"complete bytes");return b;}
static std::string hash(const std::vector<uint8_t>&b){sha256_t s;sha256_init(&s);sha256_update(&s,b.data(),b.size());unsigned char h[32];sha256_final(&s,h);std::string out;for(auto x:h){out+="0123456789abcdef"[x>>4];out+="0123456789abcdef"[x&15];}return out;}
static void save(const fs::path&p,const json&x){need(!fs::exists(p),"fresh output");std::ofstream f(p);f<<x.dump(2)<<'\n';f.flush();need(bool(f),"JSON write");}
static std::vector<uint8_t> compute(ggml_backend_t backend,ggml_tensor*w,const std::vector<uint8_t>&input,int64_t columns,bool grouped){
    ggml_init_params p={ggml_tensor_overhead()*256+ggml_graph_overhead(),nullptr,true};auto*ctx=ggml_init(p);need(ctx,"ggml context");
    auto*x=grouped?ggml_new_tensor_3d(ctx,GGML_TYPE_F32,w->ne[0],1,columns):ggml_new_tensor_2d(ctx,GGML_TYPE_F32,w->ne[0],1);
    auto*y=ggml_mul_mat(ctx,w,x);auto*g=ggml_new_graph(ctx);ggml_build_forward_expand(g,y);
    auto buf=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buf,"operand GPU allocation");
    std::vector<uint8_t>out(size_t(w->ne[1]*columns)*sizeof(float));const size_t incol=size_t(w->ne[0])*sizeof(float),outcol=size_t(w->ne[1])*sizeof(float);
    for(int64_t i=0;i<(grouped?1:columns);++i){
        ggml_backend_tensor_set(x,input.data()+(grouped?0:i*incol),0,grouped?input.size():incol);
        need(ggml_backend_graph_compute(backend,g)==GGML_STATUS_SUCCESS,"original CUDA scalar recipe compute");ggml_backend_synchronize(backend);
        ggml_backend_tensor_get(y,out.data()+(grouped?0:i*outcol),0,grouped?out.size():outcol);
    }
    ggml_backend_buffer_free(buf);ggml_free(ctx);return out;
}
int main(int argc,char**argv){fs::path out;llama_model*m=nullptr;ggml_backend_t backend=nullptr;try{
    need(argc==3,"JOB OUT");auto job=read(argv[1]);out=argv[2];need(!fs::exists(out),"fresh native output");fs::create_directories(out);
    ggml_backend_load_all_from_path(linux_transfer::executable().parent_path().string().c_str());llama_backend_init();ggml_backend_dev_t gpu=nullptr;
    for(size_t i=0;i<ggml_backend_dev_count();++i){auto*d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"single assigned GPU");gpu=d;}}
    need(gpu,"GPU");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;m=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);need(m&&m->hparams.n_layer()==64,"actual32B model");backend=ggml_backend_dev_init(gpu,nullptr);need(backend,"CUDA backend");
    json result={{"modules_before",linux_transfer::modules()},{"operands",json::array()},{"token_rows",0},{"trajectories",0}};
    for(const auto& probe:job.at("append_probes")){
        const fs::path dir=probe.at("operand_dir").get<std::string>();const std::string name=probe.at("weight");auto meta=read(dir/(name+".json"));ggml_tensor*w=nullptr;
        for(auto&t:m->tensors_by_name)if(t.first==name)w=t.second;need(w,"exact model weight");need(meta.at("weight_type")==ggml_type_name(w->type),"actual block type");
        auto input=bytes(dir/meta.at("activation_tensor").at("file").get<std::string>());auto expected=bytes(dir/meta.at("output_tensor").at("file").get<std::string>());
        need(hash(input)==meta["activation_tensor"]["sha256"]&&hash(expected)==meta["output_tensor"]["sha256"],"captured actual operand commitment");
        std::vector<uint8_t>wb(ggml_nbytes(w));ggml_backend_tensor_get(w,wb.data(),0,wb.size());need(hash(wb)==meta["weight_tensor"]["sha256"],"Actual GGUF weight bytes differ");
        const int64_t columns=meta["activation_tensor"]["ne"][2];need(columns>1&&columns<=32&&input.size()==size_t(w->ne[0]*columns)*sizeof(float),"actual dense independent column groups");need(probe["ids"].size()==size_t(2*columns),"both recipe work reservation");
        for(const auto*b:{&input,&expected}){need(b->size()%4==0,"F32 operand bytes");for(size_t i=0;i<b->size();i+=4){float value;std::memcpy(&value,b->data()+i,4);need(std::isfinite(value),"finite real operand");}}
        auto scalar=compute(backend,w,input,columns,false);auto grouped=compute(backend,w,input,columns,true);const bool pass=scalar==grouped&&scalar==expected;
        json r={{"weight",name},{"type",ggml_type_name(w->type)},{"columns",columns},{"input_sha256",hash(input)},{"weight_sha256",hash(wb)},{"captured_output_sha256",hash(expected)},{"scalar_output_sha256",hash(scalar)},{"grouped_output_sha256",hash(grouped)},{"passed",pass},{"physical_projection_rows",2*columns}};
        save(out/(name+"-CHECKED.json"),r);need(pass,"Exact real32B operand recipe mismatch");result["operands"].push_back(r);result["token_rows"]=result["token_rows"].get<int>()+2*columns;result["trajectories"]=result["trajectories"].get<int>()+1;
    }
    ggml_backend_free(backend);backend=nullptr;llama_model_free(m);m=nullptr;llama_backend_free();result["modules_after"]=linux_transfer::modules();result["status"]="COMPLETE";save(out/"result.json",result);return 0;
}catch(const std::exception&e){if(!out.empty()&&fs::exists(out))save(out/"failure.json",{{"error",e.what()}});std::cerr<<e.what()<<'\n';return 2;}}
