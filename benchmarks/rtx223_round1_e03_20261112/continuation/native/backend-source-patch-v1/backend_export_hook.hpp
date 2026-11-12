#pragma once
// Include in the isolated MMVQ translation unit only. Capture-heavy, never clean.
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <vector>
#include <string>
#include <stdexcept>
#include <cstdlib>

namespace hs_e02_backend_export {
inline void need(bool ok,const char * text) {if(!ok)throw std::runtime_error(text);}
inline void write_new(const std::filesystem::path & path,const void * data,size_t size) {
    need(size<=MAXDWORD,"backend capture write exceeds DWORD");
    HANDLE file=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    need(file!=INVALID_HANDLE_VALUE,"backend capture duplicate/unavailable output");
    DWORD written=0;
    bool okay=WriteFile(file,data,DWORD(size),&written,nullptr)&&written==size&&FlushFileBuffers(file);
    CloseHandle(file);need(okay,"backend capture short write");
}
inline void quantized(const ggml_tensor * weight,const ggml_tensor * input,const ggml_tensor * output,
                      const void * q8,size_t bytes,cudaStream_t stream) {
    const char * location=std::getenv("HS_E02_Q8_QUANT_CAPTURE");
    if(!location)return;
    if(std::string(weight->name)!="blk.0.attn_q.weight" || weight->type!=GGML_TYPE_Q8_0 ||
       input->type!=GGML_TYPE_F32 || weight->ne[0]!=4096 || weight->ne[1]!=4096 ||
       input->ne[1]*input->ne[2]*input->ne[3]!=8)return;
    need(bytes==size_t(8)*4096/32*sizeof(block_q8_1),"backend quantized size outside narrow capture");
    std::vector<unsigned char> raw(bytes);
    need(cudaMemcpyAsync(raw.data(),q8,bytes,cudaMemcpyDeviceToHost,stream)==cudaSuccess,"backend Q8_1 capture copy");
    need(cudaStreamSynchronize(stream)==cudaSuccess,"backend Q8_1 capture synchronization");
    std::filesystem::path root=location;
    need(!std::filesystem::exists(root),"backend quantized capture already exists");
    std::filesystem::create_directories(root);
    write_new(root/"activation_q8_1.bin",raw.data(),raw.size());
    std::string descriptor="schema=heterospec.backend-quantized-q8.v1\nstatus=CAPTURE_ONLY_NOT_QUALIFICATION\n";
    descriptor+="logical_q=8\nweight_type=Q8_0\nactivation_type=F32\nquantized_type=Q8_1\n";
    descriptor+="activation_bytes="+std::to_string(bytes)+"\n";
    descriptor+="input_ne="+std::to_string(input->ne[0])+","+std::to_string(input->ne[1])+","+std::to_string(input->ne[2])+","+std::to_string(input->ne[3])+"\n";
    descriptor+="output_ne="+std::to_string(output->ne[0])+","+std::to_string(output->ne[1])+","+std::to_string(output->ne[2])+","+std::to_string(output->ne[3])+"\n";
    descriptor+="dispatch_route=ENTERED_MMVQ_HOST_FUNCTION_AFTER_ORIGINAL_QUANTIZER\n";
    descriptor+="clean_guard_attested=false\nlaunch_counter_attested=false\n";
    write_new(root/"descriptor.txt",descriptor.data(),descriptor.size());
}
}
