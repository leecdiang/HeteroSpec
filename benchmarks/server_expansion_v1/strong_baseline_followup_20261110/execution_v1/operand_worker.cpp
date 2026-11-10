// Three projection graphs over frozen real bytes. Echo never initializes a backend.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "work_counts.h"
#include "hs_strong_ref1.hpp"
#include "loaded_modules.hpp"
#include <cuda_runtime.h>
#include <nlohmann/json.hpp>
extern "C" {
#include "hash/sha256/sha256.h"
}
#include <chrono>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <set>
using json = nlohmann::json;
namespace fs = std::filesystem;
static bool backend_initialization_entered=false;
static void need(bool x,const char * s) { if (!x) throw std::runtime_error(s); }
static uint64_t now_ns() { return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
static std::string digest(const std::vector<uint8_t> & b) {
    unsigned char h[32]; sha256_hash(h,b.data(),b.size()); std::string s;
    for (auto c:h) { s += "0123456789abcdef"[c>>4]; s += "0123456789abcdef"[c&15]; } return s;
}
static std::vector<uint8_t> bytes(const std::string & p) {
    std::ifstream f(p,std::ios::binary|std::ios::ate); need(bool(f),"Input file");
    auto n=f.tellg(); need(n>=0,"Input length"); std::vector<uint8_t>b(static_cast<size_t>(n));
    f.seekg(0); f.read(reinterpret_cast<char*>(b.data()),n); need(bool(f),"Complete file"); return b;
}
static json config(const json & j) {
    need(j.at("arm")=="G" || j.at("arm")=="B" || j.at("arm")=="C","Unknown backend");
    for (const auto * key : {"n_ctx","n_ubatch","output_reserve"}) need(j.at(key).is_number_integer(),"Integer configuration required");
    need(j.at("n_ctx")==1024 && j.at("n_ubatch")==32 && j.at("output_reserve")==32,"Context/UB/reserve32");
    need(j.at("kv")=="F16" && j.at("flash_attention")==false && j.at("cuda_graphs")==false,"Common policy");
    return {{"arm",j.at("arm")},{"n_ctx",1024},{"n_ubatch",32},{"output_reserve",32},{"kv","F16"},
            {"flash_attention",false},{"cuda_graphs",false},{"cuda_initialized",false},
            {"scope","CPU_PARSE_ONLY_NOT_GPU_QUALIFICATION"}};
}
static json counters(const hs_work_counts & c) {
    return {{"kernel_application_launch_calls",c.kernel_calls},{"quant_calls",c.quant_calls},
      {"quant_rows",c.quant_rows},{"quant_bytes",c.quant_bytes},{"scalar_dot_dispatches",c.scalar_dot_dispatches},
      {"scalar_dot_columns",c.scalar_dot_columns},{"backend_loop_entries",c.backend_loop_entries},
      {"application_copy_calls",c.copy_calls},{"application_copy_bytes",c.copy_bytes},
      {"application_sync_calls",c.sync_calls},{"application_cuda_malloc_calls",c.alloc_calls},
      {"application_cuda_malloc_bytes",c.alloc_bytes},
      {"opaque_library_internal_launches",nullptr},{"driver_VMM_allocation_bytes",nullptr}};
}
int main(int argc,char ** argv) {
    try {
        need(argc==3 || argc==4,"JOB OUT, or --echo JOB");
        const bool echo=std::string(argv[1])=="--echo";
        need(echo ? argc==3 : argc==4,"Exact CLI arguments");
        std::ifstream jf(echo?argv[2]:argv[1]); json j; jf>>j; need(bool(jf),"Job JSON");
        auto cfg=config(j);
        if (echo) { cfg["monotonic_ns"]=now_ns();std::cout<<cfg.dump()<<'\n'; return 0; }
        need(argc==4 && std::string(argv[3])=="--admitted-by-host", "Host admission required");
        const char * grant_path=std::getenv("HS_STRONG_GPU_ADMISSION_FILE");
        need(grant_path && *grant_path,"GPU disabled: no independently verified host admission");
        std::ifstream grant_file(grant_path);json grant;grant_file>>grant;
        need(bool(grant_file) && grant.at("schema")=="hs.strong.native-reservation.v1" &&
             (grant.at("phase")=="S1" || grant.at("phase")=="S2") && grant.at("GPU_authorized")==true &&
             grant.at("complete_F0_readback")==true && grant.at("budget_reserved")==true,
             "Unverified GPU admission");
        if (grant.at("phase")=="S2") need(grant.at("complete_F1_readback")==true &&
             grant.at("numerically_qualified")==true,"S2 requires final qualification/freeze");
        const bool quant_capture=j.at("capture_quantization").get<bool>();
        if(grant.at("phase")=="S2")need(!quant_capture,"No heavy quantized-byte audit in S2 timing");
        const char * visible=std::getenv("CUDA_VISIBLE_DEVICES");
        need(visible && grant.at("private_gpu_uuid")==visible,"Private GPU binding");
        auto job_file=bytes(argv[1]);
        need(grant.at("job_sha256")==digest(job_file),"Reservation job hash");
        need(j.at("operations").is_array()&&j.at("operations").size()>=1&&j.at("operations").size()<=2,"Registered one/two operations");
        std::set<std::string> operation_ids;
        for (const auto & op : j.at("operations")) {
            const auto id=op.at("operation_id").get<std::string>();
            need(!id.empty() && id!="." && id!=".." && id.find_first_of("/\\") == std::string::npos,"Unsafe operation ID");
            need(operation_ids.insert(id).second,"Duplicate native operation");
        }
        fs::path out=argv[2]; need(!fs::exists(out),"Fresh native output"); fs::create_directories(out);
        const auto & d=j.at("operand"); int64_t k=d.at("K"),m=d.at("M"),q=d.at("q");
        const std::set<std::string> descriptor_keys={"K","M","q","type","weight_file","activation_file","weight_sha256","activation_sha256"};
        for(auto i=d.begin();i!=d.end();++i)need(descriptor_keys.count(i.key()),"Unsupported operand descriptor field; no ignored stride/mask");
        for (const auto * key : {"K","M","q"}) need(d.at(key).is_number_integer(),"Integer descriptor required");
        need(k>0 && k%256==0 && m>0 && q>=1 && q<=32,"Descriptor dimensions");
        for(const auto& op:j.at("operations"))need(op.at("requested_output_rows")==q&&op.at("all_outputs_owned")==true,"All original output rows required");
        const std::string typ=d.at("type"),arm=j.at("arm");
        need(typ=="Q4_K" || typ=="Q6_K","Block type");
        auto wb=bytes(d.at("weight_file")),xb=bytes(d.at("activation_file"));
        need(digest(wb)==d.at("weight_sha256") && digest(xb)==d.at("activation_sha256"),"Frozen bytes");
        need(xb.size()==size_t(k*q*4),"All activation columns");
        for(size_t at=0;at<xb.size();at+=4) { float f;std::memcpy(&f,xb.data()+at,4);need(std::isfinite(f),"Nonfinite input"); }
        setenv("GGML_CUDA_DISABLE_GRAPHS","1",1);
        hs_work_reset();
        backend_initialization_entered=true;
        ggml_backend_load_all(); ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();++i) {
            auto * dev=ggml_backend_dev_get(i);
            if(ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU) { need(!gpu,"Single assigned GPU");gpu=dev; }
        }
        need(gpu,"Assigned CUDA device"); auto backend=ggml_backend_dev_init(gpu,nullptr); need(backend,"Backend");
        ggml_init_params params{ggml_tensor_overhead()*4096+ggml_graph_overhead_custom(4096,false),nullptr,true};
        auto * ctx=ggml_init(params); need(ctx,"Graph context");
        auto * w=ggml_new_tensor_2d(ctx,typ=="Q4_K"?GGML_TYPE_Q4_K:GGML_TYPE_Q6_K,k,m);
        auto * x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,k,q); ggml_tensor * y=nullptr;
        if(arm=="G" && q>1) {
            for(int64_t col=0;col<q;++col) {
                auto * v=ggml_view_2d(ctx,x,k,1,x->nb[1],col*x->nb[1]);
                auto * one=ggml_mul_mat(ctx,w,v); y=y?ggml_concat(ctx,y,one,1):one;
            }
        } else if(arm=="C" && q>1) {
            auto * v=ggml_view_3d(ctx,x,k,1,q,x->nb[1],x->nb[1],0);
            y=ggml_reshape_2d(ctx,ggml_mul_mat(ctx,w,v),m,q);
        } else {
            y=ggml_mul_mat(ctx,w,x);
            if(arm=="B" && q>1) {hs_strong_mark(y);ggml_set_name(y,"hs_backend_ref1_projection");}
        }
        auto * graph=ggml_new_graph_custom(ctx,4096,false); ggml_build_forward_expand(graph,y);
        auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend); need(buffer,"Graph buffers");
        need(ggml_nbytes(w)==wb.size(),"Exact blocked weights"); ggml_backend_tensor_set(w,wb.data(),0,wb.size());
        json records=json::array(); std::vector<std::vector<uint8_t>> owned; std::vector<std::string> hashes;
        owned.resize(j.at("operations").size(),std::vector<uint8_t>(size_t(m*q*4)));
        size_t ordinal=0;
        const auto startup_work=hs_work_finish();size_t free_ready=0,total_ready=0;
        need(cudaMemGetInfo(&free_ready,&total_ready)==cudaSuccess,"Ready GPU memory sample");
        for(const auto & op:j.at("operations")) {
            const uint64_t restore_start=now_ns(); ggml_backend_tensor_set(x,xb.data(),0,xb.size());ggml_backend_synchronize(backend);
            hs_quant_capture_reset(quant_capture);
            const uint64_t start=now_ns(); hs_work_reset();
            need(ggml_backend_graph_compute(backend,graph)==GGML_STATUS_SUCCESS,"Projection compute");
            ggml_backend_tensor_get(y,owned[ordinal].data(),0,owned[ordinal].size());const uint64_t ready=now_ns();
            ggml_backend_synchronize(backend); const uint64_t fence=now_ns(),end=now_ns();const auto work=hs_work_finish();
            for(size_t at=0;at<owned[ordinal].size();at+=4) { float f;std::memcpy(&f,owned[ordinal].data()+at,4);need(std::isfinite(f),"Nonfinite output"); }
            for(size_t i=0;i<hashes.size();++i)need(digest(owned[i])==hashes[i],"Caller output overwritten");
            hashes.push_back(digest(owned[ordinal]));
            json r=op;r["start_ns"]=start;r["end_ns"]=end;r["fence_ns"]=fence;r["copy_api_return_ns"]=ready;r["owned_ready_ns"]=fence;
            r["elapsed_s"]=(end-start)/1e9;r["unit"]="s";r["restore_s"]=(start-restore_start)/1e9;
            r["arm"]=arm;r["q"]=q;r["output_rows"]=q;r["all_outputs_owned"]=true;
            r["callback_continues"]=true;r["output_sha256"]=hashes.back();r["work_counters"]=counters(work);
            r["quantized_activations"]=json::array();
            for(uint64_t at=0;at<hs_quant_capture_count();++at){
                uint64_t rows,n;auto* p=hs_quant_capture_data(at,&rows,&n);
                std::vector<uint8_t> value(p,p+n);
                const auto file=op.at("operation_id").get<std::string>()+"-quant-"+std::to_string(at)+".q8_1";
                std::ofstream f(out/file,std::ios::binary);f.write(reinterpret_cast<const char*>(p),n);need(bool(f),"Quantized bytes write");
                r["quantized_activations"].push_back({{"file",file},{"rows",rows},{"bytes",n},{"sha256",digest(value)}});
            }
            std::ofstream raw(out/(op.at("operation_id").get<std::string>()+".f32"),std::ios::binary);
            raw.write(reinterpret_cast<const char*>(owned[ordinal].data()),owned[ordinal].size());need(bool(raw),"Owned full output file");
            records.push_back(r);++ordinal;
        }
        const auto modules=hs_loaded_modules();const int graph_nodes=ggml_graph_n_nodes(graph);size_t free_after=0,total_after=0;
        need(cudaMemGetInfo(&free_after,&total_after)==cudaSuccess,"Post-operation GPU memory sample");
        ggml_backend_buffer_free(buffer);ggml_free(ctx);ggml_backend_free(backend);
        std::ofstream f(out/"result.json");f<<json{{"operations",records},{"status","COMPLETE"},
            {"native_module_maps",modules},
            {"startup_work_counters",counters(startup_work)},{"graph_nodes",graph_nodes},
            {"GPU_memory_samples",{{"ready_free_bytes",free_ready},{"ready_total_bytes",total_ready},
                {"post_operations_free_bytes",free_after},{"post_operations_total_bytes",total_after},
                {"scope","observed current usage; not a guaranteed peak"}}},
            {"counter_scope","application CUDA API calls; opaque libraries and driver VMM not inferred"}}.dump(2)<<'\n';need(bool(f),"Receipt");return 0;
    } catch(const std::exception & e) {
        std::cerr<<"HS_NATIVE_FAILURE "<<json{{"error",e.what()},{"backend_initialization_entered",backend_initialization_entered}}.dump()<<'\n';return 2;
    }
}
