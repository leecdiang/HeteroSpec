#pragma once
// Independent CPU set-valued oracle for the frozen PTX primitive semantics.
// No CUDA headers, GPU functions, or GPU-generated oracle tables.
#include <cmath>
#include <cfloat>
#include <cstdint>
#include <cstring>
#include <algorithm>
namespace e11_oracle {
inline uint32_t bits(float x){uint32_t b;std::memcpy(&b,&x,4);return b;}
inline float value(uint32_t b){float x;std::memcpy(&x,&b,4);return x;}
inline float rn_div(float a,float b){volatile float out=a/b;return out;}
inline int quant(float x,float inverse){
    // mul.ftz.f32 defaults to RN; roundf is ties away from zero.
    volatile float product=x*inverse;
    float v=std::fabs(product)<FLT_MIN?std::copysign(0.0f,product):product;
    return int(std::copysign(std::floor(std::fabs(double(v))+0.5),double(v)));
}
struct BlockResult {int shared_inverse_witnesses=0;bool pass=false;};
inline BlockResult block(const float *x,const int *q,float scale){
    BlockResult result;float maximum=0;
    if(!std::isfinite(scale)||scale<=0||scale>1)return result;
    for(int k=0;k<32;++k){
        if(!std::isfinite(x[k])||(x[k]!=0&&std::fabs(x[k])<FLT_MIN)||q[k]<-127||q[k]>127)return result;
        maximum=std::max(maximum,std::fabs(x[k]));
    }
    if(maximum==0||maximum<std::ldexp(1.0f,-126)||maximum>std::ldexp(1.0f,126))return result;
    float nearest=rn_div(127.0f,maximum);
    if(!std::isfinite(nearest)||nearest<FLT_MIN)return result;
    for(int delta=-2;delta<=2;++delta){
        float inverse=value(bits(nearest)+delta);
        float reciprocal=rn_div(1.0f,inverse);
        if(!std::isfinite(reciprocal)||reciprocal<FLT_MIN)continue;
        uint32_t a=bits(scale),b=bits(reciprocal);
        if((a>b?a-b:b-a)>1)continue;
        bool all=true;
        for(int k=0;k<32;++k)all=all&&quant(x[k],inverse)==q[k];
        result.shared_inverse_witnesses+=all;
    }
    result.pass=result.shared_inverse_witnesses>0;return result;
}
inline bool output(float actual,double independent_sum,double absolute_blocks){
    const double u=std::ldexp(1.0,-24),gamma=64*u/(1-64*u);
    return std::isfinite(actual)&&std::isfinite(independent_sum)&&std::isfinite(absolute_blocks)&&absolute_blocks>=0&&
        std::fabs(double(actual)-independent_sum)<=gamma*absolute_blocks+128*double(FLT_MIN);
}
}
