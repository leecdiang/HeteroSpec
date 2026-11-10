// Independent per-column oracle. Link exclusively to pristine R numerical archives.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "loaded_modules.hpp"
#include <cuda_runtime.h>
#include <nlohmann/json.hpp>
extern "C" {
#include "hash/sha256/sha256.h"
size_t hs_gold_quantized_bytes(int64_t);
void hs_gold_quantize(const float*,void*,int64_t,int);
}
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <set>
#include <chrono>
using json=nlohmann::json;namespace fs=std::filesystem;
static void need(bool x,const char* s){if(!x)throw std::runtime_error(s);}
static uint64_t now_ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
static std::vector<uint8_t> bytes(const fs::path& p){
    std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f),"Gold input file");
    auto n=f.tellg();need(n>0,"Gold input length");std::vector<uint8_t> v(static_cast<size_t>(n));
    f.seekg(0);f.read(reinterpret_cast<char*>(v.data()),v.size());need(bool(f),"Complete gold input");return v;
}
static std::string digest(const std::vector<uint8_t>& v){
    unsigned char h[32];sha256_hash(h,v.data(),v.size());std::string out;
    for(auto c:h){out+="0123456789abcdef"[c>>4];out+="0123456789abcdef"[c&15];}return out;
}
static json read(const char* p){std::ifstream f(p);json j;f>>j;need(bool(f),"Gold JSON");return j;}
static void write(const fs::path& p,const std::vector<uint8_t>& v){
    need(!fs::exists(p),"Preserve gold bytes");std::ofstream f(p,std::ios::binary);
    f.write(reinterpret_cast<const char*>(v.data()),v.size());need(bool(f),"Gold output");
}
static void finite(const std::vector<uint8_t>& v){
    need(v.size()%4==0,"F32 length");for(size_t at=0;at<v.size();at+=4){float f;std::memcpy(&f,v.data()+at,4);need(std::isfinite(f),"Nonfinite gold F32");}
}
int main(int argc,char** argv){try{
    need(argc==3,"--echo JOB or JOB OUT");bool echo=std::string(argv[1])=="--echo";
    json job=read(echo?argv[2]:argv[1]);need(job.at("role")=="pristine_scalar_gold"&&job.at("q")==1,"Only pristine q1 gold");
    if(echo){std::cout<<json{{"q",1},{"cuda_initialized",false},{"scope","CPU_PARSE_ONLY_NOT_GPU_QUALIFICATION"}}.dump()<<'\n';return 0;}
    const char* grant_file=std::getenv("HS_STRONG_GPU_ADMISSION_FILE");need(grant_file&&*grant_file,"GPU disabled without gold host reservation");
    auto grant=read(grant_file);const char* visible=std::getenv("CUDA_VISIBLE_DEVICES");
    need(visible&&grant.at("schema")=="hs.strong.native-reservation.v1"&&grant.at("phase")=="S1"&&
         grant.at("GPU_authorized")==true&&grant.at("complete_F0_readback")==true&&
         grant.at("budget_reserved")==true&&grant.at("private_gpu_uuid")==visible&&
         grant.at("job_sha256")==digest(bytes(argv[1])),"Independent gold admission");
    const auto& d=job.at("operand");int64_t k=d.at("K"),m=d.at("M");std::string type=d.at("type");
    need(k>0&&k%256==0&&m>0&&(type=="Q4_K"||type=="Q6_K"),"Gold descriptor");
    auto weight=bytes(d.at("weight_file").get<std::string>());need(digest(weight)==d.at("weight_sha256"),"Gold weight identity");
    fs::path out=argv[2];need(!fs::exists(out),"Fresh independent gold output");fs::create_directories(out);
    ggml_backend_load_all();ggml_backend_dev_t gpu=nullptr;
    for(size_t i=0;i<ggml_backend_dev_count();++i){auto dev=ggml_backend_dev_get(i);if(ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"Single gold GPU");gpu=dev;}}
    need(gpu,"Assigned gold GPU");auto backend=ggml_backend_dev_init(gpu,nullptr);need(backend,"Gold backend");
    ggml_init_params p{ggml_tensor_overhead()*128+ggml_graph_overhead_custom(128,false),nullptr,true};auto ctx=ggml_init(p);
    auto w=ggml_new_tensor_2d(ctx,type=="Q4_K"?GGML_TYPE_Q4_K:GGML_TYPE_Q6_K,k,m);
    auto x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,k,1);auto y=ggml_mul_mat(ctx,w,x);
    auto graph=ggml_new_graph_custom(ctx,128,false);ggml_build_forward_expand(graph,y);
    auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);need(buffer&&ggml_nbytes(w)==weight.size(),"Gold allocation/weight size");
    ggml_backend_tensor_set(w,weight.data(),0,weight.size());
    float* quant_input=nullptr;void* quant_output=nullptr;size_t quant_bytes=hs_gold_quantized_bytes(k);
    need(cudaMalloc(&quant_input,k*4)==cudaSuccess&&cudaMalloc(&quant_output,quant_bytes)==cudaSuccess,"Gold quant audit storage");
    json records=json::array();std::set<std::string> ids;std::vector<std::vector<uint8_t>> owned;std::vector<std::string> hashes;
    for(const auto& op:job.at("operations")){
        std::string id=op.at("operation_id");need(!id.empty()&&id!="."&&id!=".."&&id.find_first_of("/\\")==std::string::npos&&ids.insert(id).second,"Gold operation identity");
        const auto start=now_ns();std::cout<<"HS_GOLD_OP_BEGIN "<<json{{"operation_id",id},{"monotonic_ns",start}}.dump()<<std::endl;
        auto input=bytes(op.at("activation_file").get<std::string>());need(input.size()==size_t(k*4)&&digest(input)==op.at("activation_sha256"),"Gold column identity");finite(input);
        ggml_backend_tensor_set(x,input.data(),0,input.size());need(ggml_backend_graph_compute(backend,graph)==GGML_STATUS_SUCCESS,"Original scalar graph");
        std::vector<uint8_t> value(size_t(m*4));ggml_backend_tensor_get(y,value.data(),0,value.size());ggml_backend_synchronize(backend);finite(value);
        need(cudaMemcpy(quant_input,input.data(),input.size(),cudaMemcpyHostToDevice)==cudaSuccess,"Gold audit input");
        hs_gold_quantize(quant_input,quant_output,k,w->type);std::vector<uint8_t> quant(quant_bytes);
        need(cudaMemcpy(quant.data(),quant_output,quant.size(),cudaMemcpyDeviceToHost)==cudaSuccess&&cudaDeviceSynchronize()==cudaSuccess,"Original quant audit output");
        for(size_t i=0;i<owned.size();++i)need(digest(owned[i])==hashes[i],"Gold caller ownership overwritten");
        owned.push_back(value);hashes.push_back(digest(value));write(out/(id+".f32"),value);write(out/(id+".q8_1"),quant);
        records.push_back({{"operation_id",id},{"q",1},{"output_sha256",hashes.back()},{"output_bytes",value.size()},
                          {"quantized_sha256",digest(quant)},{"quantized_bytes",quant.size()},
                          {"start_ns",start},{"end_ns",now_ns()},
                          {"clock_scope","qualification_column_including_audit_and_serialization_not_performance_endpoint"},
                          {"audit_extra_quantizer_invocations",1},{"all_outputs_owned",true}});
        std::cout<<"HS_GOLD_OP_COMPLETE "<<records.back().dump()<<std::endl;
    }
    const auto modules=hs_loaded_modules();
    cudaFree(quant_output);cudaFree(quant_input);ggml_backend_buffer_free(buffer);ggml_free(ctx);ggml_backend_free(backend);
    std::ofstream receipt(out/"result.json");receipt<<json{{"status","COMPLETE"},{"operations",records},
         {"native_module_maps",modules},{"scope","independent_pristine_scalar_operands_not_full_model_qualification"}}.dump(2)<<'\n';need(bool(receipt),"Gold receipt");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
