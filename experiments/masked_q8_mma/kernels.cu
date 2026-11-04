// Experimental prequantized operator only. Not a runtime dispatch replacement.
#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <stdint.h>
#include <stddef.h>

// Serialized layouts, byte loads never assume int32 alignment of Q8_0 payload.
struct Q80 { uint16_t d; int8_t q[32]; };
struct Q81 { uint16_t d, sum; int8_t q[32]; };
static_assert(sizeof(Q80)==34 && sizeof(Q81)==36, "frozen serialization");
// W payload is only 2-byte aligned; Y payload and 36-byte block stride are 4-byte aligned.
__device__ __forceinline__ uint32_t word_w(const int8_t *p) {
    uint16_t lo,hi;
    asm volatile("ld.global.u16 %0, [%1];" : "=h"(lo) : "l"(p));
    asm volatile("ld.global.u16 %0, [%1];" : "=h"(hi) : "l"(p+2));
    return uint32_t(lo)|(uint32_t(hi)<<16);
}
__device__ __forceinline__ uint32_t word_y(const int8_t *p) {
    uint32_t v;asm volatile("ld.global.u32 %0, [%1];" : "=r"(v) : "l"(p));return v;
}
__device__ __forceinline__ float scale(uint16_t a, uint16_t b) {
    return __fmul_rn(__half2float(__ushort_as_half(a)),__half2float(__ushort_as_half(b)));
}
template<bool Fused> __device__ __forceinline__ float update(float a,float s,int d) {
    return Fused ? __fmaf_rn(s,__int2float_rn(d),a) : __fadd_rn(a,__fmul_rn(s,__int2float_rn(d)));
}
__device__ __forceinline__ void mma(int (&d)[4], uint32_t a0,uint32_t a1,uint32_t b) {
#if __CUDA_ARCH__ >= 800
    asm volatile("mma.sync.aligned.m16n8k16.row.col.s32.s8.s8.s32 "
        "{%0,%1,%2,%3}, {%4,%5}, {%6}, {%7,%8,%9,%10};"
        : "=r"(d[0]),"=r"(d[1]),"=r"(d[2]),"=r"(d[3])
        : "r"(a0),"r"(a1),"r"(b),"r"(0),"r"(0),"r"(0),"r"(0));
#else
    asm volatile("trap;");
#endif
}

// Both implementations share identical physical accumulator ownership and FP DAG.
template<bool UseMMA,bool Fused>
__global__ void mapped8(const Q80 *w,const Q81 *y,float *out,int B,int M) {
    const int p=threadIdx.x, warp=threadIdx.y,g=p/4,t=p%4;
    const int row0=blockIdx.x*8,col0=blockIdx.y*8;
    float a[8][2][4]={};
    __shared__ float cross[3][64][32];
    for(int base=32*0;base<B;base+=32) {
#pragma unroll
        for(int u=0;u<8;++u) {
            const int k=base+8*warp+u;
            // Warp-uniform; absent K updates are skipped, not zero-padded FP ops.
            if(k<B) {
#pragma unroll
                for(int h=0;h<2;++h) {
                    int d[4];
                    if constexpr(UseMMA) {
                        const Q80 &wa=w[size_t(row0+g/2)*B+k];
                        const Q80 &wb=w[size_t(row0+(g+8)/2)*B+k];
                        uint32_t a0=(t/2==g%2)?word_w(wa.q+16*h+4*t):0;
                        uint32_t a1=(t/2==(g+8)%2)?word_w(wb.q+16*h+4*t):0;
                        uint32_t b=word_y(y[size_t(col0+g)*B+k].q+16*h+4*t);
                        mma(d,a0,a1,b);
                    } else {
#pragma unroll
                        for(int z=0;z<4;++z) {
                            int r=(g+8*(z/2))/2,j=2*t+z%2,v=2*h+g%2;
                            const int8_t *wp=w[size_t(row0+r)*B+k].q+8*v;
                            const int8_t *yp=y[size_t(col0+j)*B+k].q+8*v;
                            d[z]=__dp4a(int(word_w(wp+4)),int(word_y(yp+4)),__dp4a(int(word_w(wp)),int(word_y(yp)),0));
                        }
                    }
#pragma unroll
                    for(int z=0;z<4;++z) {
                        int r=(g+8*(z/2))/2,j=2*t+z%2;
                        a[u][h][z]=update<Fused>(a[u][h][z],scale(w[size_t(row0+r)*B+k].d,y[size_t(col0+j)*B+k].d),d[z]);
                    }
                }
            }
        }
    }
    if(warp) {
#pragma unroll
        for(int u=0;u<8;++u)
#pragma unroll
            for(int h=0;h<2;++h)
#pragma unroll
                for(int z=0;z<4;++z) cross[warp-1][u*8+h*4+z][p]=a[u][h][z];
    }
    __syncthreads();
    if(warp) return;
#pragma unroll
    for(int u=0;u<8;++u)
#pragma unroll
        for(int h=0;h<2;++h)
#pragma unroll
            for(int z=0;z<4;++z)
#pragma unroll
                for(int widx=0;widx<3;++widx) a[u][h][z]=__fadd_rn(a[u][h][z],cross[widx][u*8+h*4+z][p]);
    // Simultaneous butterfly stages: do not overwrite a partner before reading it.
#pragma unroll
    for(int offset=4;offset>=1;offset/=2) {
        float b[8][2][4];
#pragma unroll
        for(int u=0;u<8;++u)
#pragma unroll
            for(int h=0;h<2;++h)
#pragma unroll
                for(int z=0;z<4;++z) b[u][h][z]=__fadd_rn(a[u][h][z],a[u^offset][h][z]);
#pragma unroll
        for(int u=0;u<8;++u)
#pragma unroll
            for(int h=0;h<2;++h)
#pragma unroll
                for(int z=0;z<4;++z) a[u][h][z]=b[u][h][z];
    }
    // Only u=0,h=0 selected writers are needed after the earlier butterflies.
#pragma unroll
    for(int z=0;z<4;++z) {
        float v=__fadd_rn(a[0][0][z],a[0][1][z]);
        v=__fadd_rn(v,__shfl_xor_sync(0xffffffff,v,4));
        int r=(g+8*(z/2))/2,j=2*t+z%2;
        // Original row-within-two writer lane is r%2, not always lane zero.
        if(g%2==r%2) out[size_t(col0+j)*M+row0+r]=v;
    }
}

// Independent logical-lane W4 control, not imported frozen binary proof.
template<bool Fused,int Rows=2,int Cols=4> __global__ void reference4(const Q80 *w,const Q81 *y,float *out,int B,int M) {
    int lane=threadIdx.x,warp=threadIdx.y,row=blockIdx.x*Rows,col=blockIdx.y*Cols;
    float a[Rows][Cols]={}; __shared__ float s[3][Rows*Cols][32];
    for(int k=8*warp+lane/4;k<B;k+=32) {
#pragma unroll
        // Register-blocked control: load each weight pair once across columns.
        for(int r=0;r<Rows;++r) {
            const Q80 &wb=w[size_t(row+r)*B+k];int v=lane%4;
            int w0=int(word_w(wb.q+8*v)),w1=int(word_w(wb.q+8*v+4));uint16_t wd=wb.d;
#pragma unroll
            for(int j=0;j<Cols;++j) {
                const Q81 &yb=y[size_t(col+j)*B+k];
                int d=__dp4a(w0,int(word_y(yb.q+8*v)),0);
                d=__dp4a(w1,int(word_y(yb.q+8*v+4)),d);
                a[r][j]=update<Fused>(a[r][j],scale(wd,yb.d),d);
            }
        }
    }
    if(warp) {
#pragma unroll
        for(int r=0;r<Rows;++r)
#pragma unroll
            for(int j=0;j<Cols;++j) s[warp-1][r*Cols+j][lane]=a[r][j];
    }
    __syncthreads();if(warp)return;
#pragma unroll
    for(int r=0;r<Rows;++r)
#pragma unroll
        for(int j=0;j<Cols;++j) {
#pragma unroll
            for(int i=0;i<3;++i) a[r][j]=__fadd_rn(a[r][j],s[i][r*Cols+j][lane]);
#pragma unroll
            for(int off=16;off;off/=2) a[r][j]=__fadd_rn(a[r][j],__shfl_xor_sync(0xffffffff,a[r][j],off));
            if(lane==r%2)out[size_t(col+j)*M+row+r]=a[r][j];
        }
}
// Caller owns allocation extents, residency, no-alias, synchronization, finite
// scales and exact input bytes. This low-level research API is NOT admission.
extern "C" cudaError_t hs_experimental_q8(const void *w,const void *y,float *out,int K,int M,int N,int mode,bool fused,cudaStream_t stream) {
    if(!w||!y||!out||K<=0||K%32||M<=0||M%8||N<8||N>32||N%8||mode<0||mode>5) return cudaErrorInvalidValue;
    if(uintptr_t(w)%2||uintptr_t(y)%4||uintptr_t(out)%4) return cudaErrorInvalidValue;
    if((mode==3&&N%32)||(mode==4&&N%16))return cudaErrorInvalidValue;
    int device=0,major=0;cudaError_t err=cudaGetDevice(&device);if(err!=cudaSuccess)return err;
    err=cudaDeviceGetAttribute(&major,cudaDevAttrComputeCapabilityMajor,device);if(err!=cudaSuccess)return err;
    if(major<8)return cudaErrorNotSupported;
    dim3 threads(32,4);
#define RUN(F) if(mode==0) mapped8<true,F><<<dim3(M/8,N/8),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M); else if(mode==1) mapped8<false,F><<<dim3(M/8,N/8),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M); else if(mode==2) reference4<F><<<dim3(M/2,N/4),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M); else if(mode==3) reference4<F,2,32><<<dim3(M/2,N/32),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M); else if(mode==4) reference4<F,4,16><<<dim3(M/4,N/16),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M); else reference4<F,8,8><<<dim3(M/8,N/8),threads,0,stream>>>((const Q80*)w,(const Q81*)y,out,K/32,M)
    if(fused){RUN(true);}else{RUN(false);}
#undef RUN
    return cudaGetLastError();
}
