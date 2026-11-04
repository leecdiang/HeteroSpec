#include <cuda_runtime.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <cstdio>
extern "C" cudaError_t hs_experimental_q8(const void*,const void*,float*,int,int,int,int,bool,cudaStream_t);
struct W{uint16_t d;int8_t q[32];};struct Y{uint16_t d,s;int8_t q[32];};static_assert(sizeof(W)==34&&sizeof(Y)==36,"layout");
#define OK(x) do{auto e=(x);if(e!=cudaSuccess){fprintf(stderr,"FAIL %s\n",cudaGetErrorString(e));return 1;}}while(0)
int main(){
 int devices=0;auto e=cudaGetDeviceCount(&devices);if(e!=cudaSuccess||!devices){printf("NOT_RUN_NO_DEVICE: %s\n",cudaGetErrorString(e));return 77;}
 constexpr int B=33,M=8,N=32;std::vector<W>w(M*B);std::vector<Y>y(N*B);
 const int8_t w0[8]={127,127,101,0,0,0,0,0},y0[8]={127,21,1,0,0,0,0,0};
 const int8_t w1[8]={-127,-101,0,0,0,0,0,0},y1[8]={108,1,0,0,0,0,0,0};
 w[0].d=y[0].d=0x3c00;w[32].d=0x3be9;y[32].d=0x3f4d;
 memcpy(w[0].q,w0,8);memcpy(y[0].q,y0,8);memcpy(w[32].q,w1,8);memcpy(y[32].q,y1,8);
 W*dw;Y*dy;float*out;OK(cudaMalloc(&dw,w.size()*sizeof(W)));OK(cudaMalloc(&dy,y.size()*sizeof(Y)));OK(cudaMalloc(&out,M*N*4));
 OK(cudaMemcpy(dw,w.data(),w.size()*sizeof(W),cudaMemcpyHostToDevice));OK(cudaMemcpy(dy,y.data(),y.size()*sizeof(Y),cudaMemcpyHostToDevice));
 std::vector<uint32_t>ref(M*N),got(M*N);int checks=0;
 for(bool fused:{true,false}){
  OK(hs_experimental_q8(dw,dy,out,B*32,M,N,2,fused,0));OK(cudaDeviceSynchronize());OK(cudaMemcpy(ref.data(),out,M*N*4,cudaMemcpyDeviceToHost));
  uint32_t expected=fused?0xc5bcb40b:0xc5bcb40c;if(ref[0]!=expected){printf("FAIL W4 mode=%d got=%08x expected=%08x\n",fused,ref[0],expected);return 1;}++checks;
  for(int mode:{0,1,3,4,5}){OK(hs_experimental_q8(dw,dy,out,B*32,M,N,mode,fused,0));OK(cudaDeviceSynchronize());OK(cudaMemcpy(got.data(),out,M*N*4,cudaMemcpyDeviceToHost));if(got!=ref){printf("FAIL variant=%d fused=%d\n",mode,fused);return 1;}++checks;}
 }
 OK(cudaFree(dw));OK(cudaFree(dy));OK(cudaFree(out));printf("FINITE_FMA_WITNESS_PASS checks=%d; not frozen-runtime qualification\n",checks);return 0;
}
