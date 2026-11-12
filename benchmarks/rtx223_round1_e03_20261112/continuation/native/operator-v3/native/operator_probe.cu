#include "bound_mmvq_prefix.cuh"
#include "bound_quantizer.cuh"
#include "two_group_q8.cuh"
#include "launch_accounting.hpp"
#include <nlohmann/json.hpp>
#include <windows.h>
#include <psapi.h>
#include <bcrypt.h>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

using json = nlohmann::json;
#ifndef HS_NATIVE_EXECUTION_ENABLED
#define HS_NATIVE_EXECUTION_ENABLED 0
#endif
static void need(bool okay, const std::string & message) {
    if (!okay) throw std::runtime_error(message);
}
static void check(cudaError_t value) {
    if (value != cudaSuccess) throw std::runtime_error(cudaGetErrorString(value));
}
static std::vector<char> load(const std::string & path, size_t expected) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    need(bool(input), "missing input: " + path);
    need(size_t(input.tellg()) == expected, "input length mismatch: " + path);
    std::vector<char> data(expected); input.seekg(0); input.read(data.data(), expected);
    need(size_t(input.gcount()) == expected, "truncated input: " + path);
    return data;
}
static std::string sha256(const std::vector<char> & data) {
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    DWORD object_size=0,bytes=0;unsigned char digest[32];
    need(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA256 provider");
    need(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,(PUCHAR)&object_size,sizeof(object_size),&bytes,0)>=0,"SHA256 object size");
    std::vector<unsigned char> object(object_size);
    need(BCryptCreateHash(algorithm,&hash,object.data(),object_size,nullptr,0,0)>=0,"SHA256 create");
    need(data.size()<=ULONG_MAX,"SHA256 input too large");
    need(BCryptHashData(hash,(PUCHAR)data.data(),(ULONG)data.size(),0)>=0,"SHA256 update");
    need(BCryptFinishHash(hash,digest,sizeof(digest),0)>=0,"SHA256 finish");
    BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(algorithm,0);
    std::ostringstream text;text<<std::hex<<std::setfill('0');
    for(auto value:digest)text<<std::setw(2)<<(unsigned)value;
    return text.str();
}
static std::vector<std::string> attempted_capture_paths;
static void save(const std::string & path, const void * data, size_t bytes) {
    if(path.size()>=4 && path.substr(path.size()-4)==".bin")attempted_capture_paths.push_back(path);
    need(GetFileAttributesA(path.c_str()) == INVALID_FILE_ATTRIBUTES, "output already exists: " + path);
    std::ofstream out(path, std::ios::binary); out.write((const char *)data, bytes);
    need(bool(out), "output write failed: " + path);
}
static std::string uuid_text(const cudaUUID_t & uuid) {
    std::ostringstream text; text << "GPU-" << std::hex << std::setfill('0');
    for (int i=0;i<16;++i) {
        if (i==4 || i==6 || i==8 || i==10) text << '-';
        text << std::setw(2) << (unsigned)(unsigned char)uuid.bytes[i];
    }
    return text.str();
}
static void launch_arm(int arm, const block_q8_0 * w, const block_q8_1 * a,
        float * y, int k, int m, int pk, cudaStream_t stream, hs_operator_accounting::LaunchCounts & counts) {
    dim3 block(32,4,1);
    if (arm==2) {
        counts.before();
        hs_two_group_q8<<<dim3(m/2,1,1),block,0,stream>>>(w,a,y,k,m,pk);
        check(cudaGetLastError());counts.submission_succeeded();
    } else {
        const int stride = pk / 32;
        auto launch = [&](const block_q8_1 * ap, float * yp, int groups) {
            counts.before();
            mul_mat_vec_q<GGML_TYPE_Q8_0,4,false><<<dim3(m/2,groups,1),block,0,stream>>>(
                w,ap,nullptr,ggml_cuda_mm_fusion_args_device{},yp,k,
                make_uint3(1,groups==2 ? 1 : 0,groups),k/32,stride,m,
                make_uint3(1,groups==2 ? 1 : 0,groups),m*k/32,
                4*stride,4*m,make_uint3(1,0,1),m*k/32,8*stride,8*m,0);
            check(cudaGetLastError());counts.submission_succeeded();
        };
        if (arm==0) { launch(a,y,1); launch(a+4*stride,y+4*m,1); }
        else launch(a,y,2);
    }
    check(cudaGetLastError());
}
static json resources(int arm) {
    cudaFuncAttributes a{}; int blocks=0;
    if (arm==2) {
        check(cudaFuncGetAttributes(&a,hs_two_group_q8));
        check(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&blocks,hs_two_group_q8,128,0));
    } else {
        check(cudaFuncGetAttributes(&a,mul_mat_vec_q<GGML_TYPE_Q8_0,4,false>));
        check(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&blocks,mul_mat_vec_q<GGML_TYPE_Q8_0,4,false>,128,0));
    }
    return {{"registers_per_thread",a.numRegs},{"static_shared_bytes",a.sharedSizeBytes},
        {"local_bytes_per_thread",a.localSizeBytes},{"resident_blocks_per_sm_limit",blocks},
        {"active_warps_per_sm_limit",blocks*4},{"achieved_occupancy","unknown"},
        {"dram_bytes","unknown"},{"l2_traffic","unknown"},{"spill_load_store_bytes","build log"}};
}
int main(int argc,char ** argv) {
    json result={{"status","FAILED"},{"model_requests",0},{"target_rows",0},{"draft_rows",0},
        {"kernel_launches",0},{"capture_bytes",0}};
    std::string out;
    hs_operator_accounting::LaunchCounts counts;
    int quantizers=0,projections=0;
    try {
        need(argc==2,"usage: operator_probe.exe job.json");
        std::ifstream config(argv[1]); json job; config>>job;
        const volatile bool execution_enabled=HS_NATIVE_EXECUTION_ENABLED!=0;
        need(execution_enabled,"PREPARATION_ONLY: CUDA execution disabled in this binary; integrate resource gate and rebuild in a fresh epoch");
        need(job.at("gpu_admitted")==true,"GPU not admitted");
        need(job.at("schema")=="heterospec-rtx221-operator-v1","wrong schema");
        need(job.at("weight_type")=="Q8_0" && job.at("input_type")=="F32","dtype");
        need(job.at("q")==8 && job.at("g")==2 && job.at("ids")==false && job.at("fusion")==false,"subdomain");
        int k=job.at("k"),m=job.at("m"),pk=job.at("padded_k");
        need(k>0 && k%512==0 && pk==k && m>0 && m%2==0,"geometry or padding");
        need(job.at("input_stride_bytes")==4*k && job.at("output_stride_bytes")==4*m,"stride");
        need(job.at("warmups")==3 && job.at("timing_blocks")==6,"unfrozen work count");
        out=job.at("output_dir").get<std::string>();
        need(GetFileAttributesA((out+"/result.json").c_str())==INVALID_FILE_ATTRIBUTES,"output exists");
        auto w=load(job.at("weight_path"),size_t(k/32)*m*sizeof(block_q8_0));
        auto x=load(job.at("input_path"),size_t(k)*8*sizeof(float));
        auto expected=load(job.at("backend_output_path"),size_t(m)*8*sizeof(float));
        need(sha256(w)==job.at("weight_sha256"),"weight SHA256 mismatch");
        need(sha256(x)==job.at("input_sha256"),"input SHA256 mismatch");
        need(sha256(expected)==job.at("backend_output_sha256"),"backend output SHA256 mismatch");
        int device=job.at("logical_device"); check(cudaSetDevice(device));
        cudaDeviceProp prop{}; check(cudaGetDeviceProperties(&prop,device));
        need(uuid_text(prop.uuid)==job.at("device_uuid"),"device UUID mismatch");
        need(prop.major==12 && prop.minor==0 && prop.warpSize==32,"unsupported GPU");
        result["device"]={{"uuid",uuid_text(prop.uuid)},{"name",prop.name},{"sm_count",prop.multiProcessorCount},
            {"max_threads_per_sm",prop.maxThreadsPerMultiProcessor},{"graph_policy","disabled"}};
        HMODULE modules[512]; DWORD count=0; json dlls=json::array();
        need(EnumProcessModules(GetCurrentProcess(),modules,sizeof(modules),&count)!=0,"module inventory failed");
        for (size_t i=0;i<count/sizeof(HMODULE) && i<512;++i) {
            char path[MAX_PATH]; if(GetModuleFileNameA(modules[i],path,MAX_PATH)) dlls.push_back(path);
        }
        result["loaded_modules"]=dlls;
        block_q8_0 *dw=nullptr; float *dx=nullptr,*dy=nullptr; block_q8_1 *da=nullptr;
        const size_t abytes=size_t(pk/32)*8*sizeof(block_q8_1),ybytes=size_t(m)*8*sizeof(float);
        check(cudaMalloc(&dw,w.size()));check(cudaMalloc(&dx,x.size()));check(cudaMalloc(&da,abytes));check(cudaMalloc(&dy,ybytes));
        check(cudaMemcpy(dw,w.data(),w.size(),cudaMemcpyHostToDevice));
        check(cudaMemcpy(dx,x.data(),x.size(),cudaMemcpyHostToDevice));
        cudaStream_t stream; check(cudaStreamCreateWithFlags(&stream,cudaStreamNonBlocking));

        auto quantize=[&]() {
            counts.before();
            ++quantizers;result["quantizer_launch_attempts"]=quantizers;
            quantize_q8_1<<<dim3(pk/256,8,1),256,0,stream>>>(dx,da,k,k,8*k,8*k,pk,8,make_uint3(1,0,1));
            check(cudaGetLastError());counts.submission_succeeded();
        };
        auto project=[&](int arm) {
            const auto before=counts.attempted;
            try {launch_arm(arm,dw,da,dy,k,m,pk,stream,counts);}
            catch(...) {projections+=int(counts.attempted-before);throw;}
            projections+=int(counts.attempted-before);
        };
        json qualification=json::array(); std::vector<char> first_a,first_y;
        for (int arm=0;arm<3;++arm) {
            result["resources"][std::to_string(arm)]=resources(arm);
            for (int repeat=0;repeat<2;++repeat) {
                quantize();project(arm);check(cudaStreamSynchronize(stream));
                std::vector<char> ah(abytes),yh(ybytes);
                check(cudaMemcpy(ah.data(),da,abytes,cudaMemcpyDeviceToHost));
                check(cudaMemcpy(yh.data(),dy,ybytes,cudaMemcpyDeviceToHost));
                save(out+"/arm"+std::to_string(arm)+"-r"+std::to_string(repeat)+"-activation.bin",ah.data(),abytes);
                save(out+"/arm"+std::to_string(arm)+"-r"+std::to_string(repeat)+"-output.bin",yh.data(),ybytes);
                if(arm==0 && repeat==0) {first_a=ah;first_y=yh;}
                const bool exact_a=ah==first_a,exact_y=yh==expected;
                qualification.push_back({{"arm",arm},{"repeat",repeat},{"activation_exact",exact_a},
                    {"backend_output_exact",exact_y},{"cross_arm_exact",yh==first_y}});
                result["qualification"]=qualification;
                need(exact_a && exact_y && yh==first_y,"bitwise qualification failed; no timing");
            }
        }
        for (int arm=0;arm<3;++arm) for(int repeat=0;repeat<3;++repeat) {quantize();project(arm);}
        check(cudaStreamSynchronize(stream));
        cudaEvent_t begin,end;check(cudaEventCreate(&begin));check(cudaEventCreate(&end));
        result["paired_timings"]=json::array();
        const int orders[6][3]={{0,1,2},{1,2,0},{2,0,1},{2,1,0},{1,0,2},{0,2,1}};
        for (int mode=0;mode<2;++mode) for(int block=0;block<6;++block) for(int position=0;position<3;++position) {
            int arm=orders[block][position];
            if(mode==0) {quantize();check(cudaStreamSynchronize(stream));}
            auto t=std::chrono::steady_clock::now();
            check(cudaEventRecord(begin,stream));
            if(mode==1) quantize();project(arm);
            check(cudaEventRecord(end,stream));check(cudaEventSynchronize(end));
            auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();
            float ms=0;check(cudaEventElapsedTime(&ms,begin,end));
            result["paired_timings"].push_back({{"mode",mode==0?"kernel-only":"complete-operator"},
                {"block",block},{"position",position},{"arm",arm},{"event_ms",ms},{"host_complete_s",elapsed}});
        }
        result["quantizer_launches"]=quantizers;result["projection_launches"]=projections;
        result["kernel_launches"]=quantizers+projections;
        result["capture_bytes"]=6*(abytes+ybytes);result["warmup_operator_calls"]=9;
        result["status"]="PASS_OPERATOR_ONLY";
        check(cudaEventDestroy(begin));check(cudaEventDestroy(end));check(cudaStreamDestroy(stream));
        check(cudaFree(dw));check(cudaFree(dx));check(cudaFree(da));check(cudaFree(dy));
    } catch(const std::exception & error) {result["error"]=error.what();}
    result["kernel_launch_attempts"]=counts.attempted;
    result["kernel_launch_submissions"]=counts.submitted;
    result["kernel_launches"]=counts.attempted; // failures remain charged
    result["quantizer_launch_attempts"]=quantizers;
    result["projection_launch_attempts"]=projections;
    result["completed_kernel_activity_count"]="unknown";
    result["counter_scope"]="explicit standalone quantizer/MMVQ sites only; not model backend";
    std::uint64_t capture_bytes=0;bool capture_bytes_known=true;
    for(const auto & path:attempted_capture_paths){
        WIN32_FILE_ATTRIBUTE_DATA info{};
        if(GetFileAttributesExA(path.c_str(),GetFileExInfoStandard,&info))
            capture_bytes+=(std::uint64_t(info.nFileSizeHigh)<<32)|info.nFileSizeLow;
        else if(GetLastError()!=ERROR_FILE_NOT_FOUND)capture_bytes_known=false;
    }
    result["capture_bytes"]=capture_bytes_known?json(capture_bytes):json(nullptr);
    result["capture_binary_bytes_lower_bound"]=capture_bytes;
    result["capture_bytes_scope"]="all attempted raw binary output paths, including partial failed writes; result metadata accounted separately by supervisor";
    if(!out.empty()) {
        auto content=result.dump(2);save(out+"/result.json",content.data(),content.size());
    }
    std::cout<<result.dump(2)<<std::endl;
    return result.at("status")=="PASS_OPERATOR_ONLY"?0:2;
}
