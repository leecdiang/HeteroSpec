#include <cmath>
#include <cstdint>
#include <cstring>
static float flush(float x){uint32_t b;memcpy(&b,&x,4);if((b&0x7f800000)==0)b&=0x80000000;memcpy(&x,&b,4);return x;}
extern "C" uint32_t case_bits(int i,int ftz){
 volatile float x=i==0?std::ldexp(1.0f,-126):1.0f;
 volatile float y=i==0?0.5f:0.0f;
 volatile float z=i==0?0.0f:std::ldexp(1.0f,-149);
 float v=ftz?flush(std::fma(flush(x),flush(y),flush(z))):std::fma(float(x),float(y),float(z));
 uint32_t b;memcpy(&b,&v,4);return b;
}
// Real signed-int8 dot8 leaves, placed at blocks0 and32 of one W4 lane.
extern "C" uint32_t fma_witness(int fused){
 const int8_t w0[8]={127,127,101,0,0,0,0,0},y0[8]={127,21,1,0,0,0,0,0};
 const int8_t w1[8]={-127,-101,0,0,0,0,0,0},y1[8]={108,1,0,0,0,0,0,0};
 int d0=0,d1=0;for(int i=0;i<8;++i){d0+=int(w0[i])*int(y0[i]);d1+=int(w1[i])*int(y1[i]);}
 volatile float s=0.98876953125f*1.8251953125f,a=float(d0),d=float(d1);
 float v=fused?std::fma(float(s),float(d),float(a)):float(float(a)+float(s*d));uint32_t bits;memcpy(&bits,&v,4);return bits;
}
