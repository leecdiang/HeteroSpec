#include <cuda_runtime.h>
#include <vector>
#include <random>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <stdexcept>
extern "C" cudaError_t hs_experimental_q8(const void*,const void*,float*,int,int,int,int,bool,cudaStream_t);
struct W{uint16_t d;int8_t q[32];};struct Y{uint16_t d,s;int8_t q[32];};
static_assert(sizeof(W)==34&&sizeof(Y)==36,"layout");
void check(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
int main(){
 // Invalid-call checks return before any CUDA device access or dereference.
 const void *aligned=reinterpret_cast<void*>(uintptr_t(4096));float *output=reinterpret_cast<float*>(uintptr_t(8192));
 int rejected=0;
 auto reject=[&](const void* w,const void* y,float* o,int K,int M,int N,int mode){if(hs_experimental_q8(w,y,o,K,M,N,mode,false,0)!=cudaErrorInvalidValue)throw std::runtime_error("invalid-call guard failed");++rejected;};
 reject(nullptr,aligned,output,32,8,8,0);reject(aligned,aligned,output,31,8,8,0);
 reject(aligned,aligned,output,32,7,8,0);reject(aligned,aligned,output,32,8,9,0);
 reject(aligned,aligned,output,32,8,8,6);reject(aligned,aligned,output,32,8,8,3);
 reject(aligned,aligned,output,32,8,8,4);reject(aligned,reinterpret_cast<void*>(uintptr_t(4098)),output,32,8,8,0);
 printf("HOST_ARGUMENT_REJECTIONS_PASS checks=%d\n",rejected);
 int count=0;auto e=cudaGetDeviceCount(&count);if(e!=cudaSuccess||!count){printf("NOT_RUN: CUDA device unavailable (%s)\n",cudaGetErrorString(e));return 77;}
 cudaDeviceProp prop{};check(cudaGetDeviceProperties(&prop,0));if(prop.major<8){puts("NOT_RUN: SM80 minimum");return 77;}
 try{
 std::mt19937 rng(178);size_t comparisons=0;
 for(int B:{1,7,17,31,32,33,128,384})for(int M:{8,16})for(int N:{8,16,24,32})for(int kind=0;kind<4;++kind){
  std::vector<W>w(M*B);std::vector<Y>y(N*B);
  for(auto &b:w){b.d=kind==1?0x8000:kind==2?0x0001:kind==3?0x7bff:uint16_t((rng()%0x7c00)|((rng()%2)<<15));for(auto &q:b.q)q=kind==2?-128:int8_t(rng()%256);}
  for(auto &b:y){b.d=kind==2?0x0001:kind==3?0x7bff:uint16_t(rng()%0x7c00);b.s=0;for(auto &q:b.q)q=kind==2?-128:int8_t(rng()%256);}
  W*dw;Y*dy;float*o;check(cudaMalloc(&dw,w.size()*sizeof(W)));check(cudaMalloc(&dy,y.size()*sizeof(Y)));check(cudaMalloc(&o,M*N*sizeof(float)));
  check(cudaMemcpy(dw,w.data(),w.size()*sizeof(W),cudaMemcpyHostToDevice));check(cudaMemcpy(dy,y.data(),y.size()*sizeof(Y),cudaMemcpyHostToDevice));
  for(bool fused:{false,true}){
   std::vector<uint32_t>reference(M*N),got(M*N);
   check(hs_experimental_q8(dw,dy,o,B*32,M,N,2,fused,0));check(cudaDeviceSynchronize());check(cudaMemcpy(reference.data(),o,M*N*4,cudaMemcpyDeviceToHost));
   for(int mode:{0,1,3,4,5}){
    if((mode==3&&N%32)||(mode==4&&N%16))continue;
    check(cudaMemset(o,0xa5,M*N*4));check(hs_experimental_q8(dw,dy,o,B*32,M,N,mode,fused,0));check(cudaDeviceSynchronize());check(cudaMemcpy(got.data(),o,M*N*4,cudaMemcpyDeviceToHost));
    for(int i=0;i<M*N;++i){if(reference[i]!=got[i]){printf("FAIL B=%d M=%d N=%d kind=%d fused=%d mode=%d i=%d ref=%08x got=%08x\n",B,M,N,kind,int(fused),mode,i,reference[i],got[i]);return 1;}++comparisons;}
   }
  }
  check(cudaFree(dw));check(cudaFree(dy));check(cudaFree(o));
 }
 printf("FINITE_PREQUANTIZED_OPERATOR_PASS comparisons=%zu device=%s; not frozen-runtime equivalence\n",comparisons,prop.name);return 0;
 }catch(const std::exception &e){fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
