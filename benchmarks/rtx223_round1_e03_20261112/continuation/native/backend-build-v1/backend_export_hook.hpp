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
inline std::filesystem::path dispatch_root;
inline unsigned dispatch_index=0,expected_dispatches=0;
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
    static std::string completed_location;
    if(completed_location==location)return;
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
    dispatch_root=root;dispatch_index=0;expected_dispatches=hs_loop4::marked(output)?2:1;
    completed_location=location;
}
inline void dispatch(int type,int columns,bool small_k,bool halve_iters,bool fusion,bool ids,
                     dim3 grid,dim3 block,int shared,uint32_t row_x,uint32_t col_y,uint32_t col_out,
                     uint32_t channel_x,uint32_t channel_y,uint32_t channel_out) {
    if(dispatch_root.empty())return;
    need(type==int(GGML_TYPE_Q8_0)&&columns==4&&!fusion&&!ids,"captured q8 did not select original unfused case4");
    std::string text="schema=heterospec.actual-mmvq-dispatch.v1\nstatus=BEFORE_KERNEL_SUBMISSION_NOT_COMPLETION\n";
    text+="type=Q8_0\narithmetic_columns="+std::to_string(columns)+"\n";
    text+="small_k="+std::to_string(small_k)+"\nhalve_iters="+std::to_string(halve_iters)+"\n";
    text+="grid="+std::to_string(grid.x)+","+std::to_string(grid.y)+","+std::to_string(grid.z)+"\n";
    text+="block="+std::to_string(block.x)+","+std::to_string(block.y)+","+std::to_string(block.z)+"\n";
    text+="dynamic_shared_bytes="+std::to_string(shared)+"\n";
    text+="strides_row_x_col_y_col_out="+std::to_string(row_x)+","+std::to_string(col_y)+","+std::to_string(col_out)+"\n";
    text+="strides_channel_x_y_out="+std::to_string(channel_x)+","+std::to_string(channel_y)+","+std::to_string(channel_out)+"\n";
    text+="full_backend_kernel_budget_attested=false\nclean_guard_attested=false\n";
    write_new(dispatch_root/("dispatch-"+std::to_string(dispatch_index)+".txt"),text.data(),text.size());
    if(++dispatch_index==expected_dispatches)dispatch_root.clear();
}
}
