#pragma once
#include <vector>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <nlohmann/json.hpp>
using json=nlohmann::ordered_json;
inline void require(bool b,const char *s){if(!b)throw std::runtime_error(s);}
// No ggml types or graph helpers in the mathematical implementation.
struct Logical {
 int nq,nk,nh,nv; double scale=double(float(1.0/std::sqrt(128.0)));
 std::vector<double> q,k,v,mask,score,prob,value;
 int qi(int j,int h,int d)const{return (j*nh+h)*128+d;}
 int ki(int h,int p,int d)const{return (h*nk+p)*128+d;}
 int vi(int h,int d,int p)const{return (h*128+d)*nk+p;}
 int si(int j,int h,int p)const{return (j*nh+h)*nk+p;}
 void solve(){
  score.resize(nq*nh*nk);prob.resize(score.size());value.assign(nq*nh*128,0);
  for(int j=0;j<nq;++j)for(int h=0;h<nh;++h){
   const int kh=h/(nh/nv); double mx=-INFINITY;
   for(int p=0;p<nk;++p){double s=0;
    for(int d=0;d<128;++d)s+=q[qi(j,h,d)]*k[ki(kh,p,d)];
    score[si(j,h,p)]=s;mx=std::max(mx,s*scale+mask[j*nk+p]);
   }
   double z=0;
   for(int p=0;p<nk;++p){double e=std::exp(score[si(j,h,p)]*scale+mask[j*nk+p]-mx);prob[si(j,h,p)]=e;z+=e;}
   require(z>0&&std::isfinite(z),"undefined oracle softmax");
   for(int p=0;p<nk;++p)prob[si(j,h,p)]/=z;
   for(int d=0;d<128;++d)for(int p=0;p<nk;++p)value[qi(j,h,d)]+=prob[si(j,h,p)]*v[vi(kh,d,p)];
  }
 }
};
inline double half_value(uint16_t b){
 int sign=(b>>15)?-1:1,exp=(b>>10)&31,mant=b&1023;
 if(exp==0)return sign*std::ldexp(double(mant),-24);
 if(exp==31)return mant?NAN:sign*INFINITY;
 return sign*std::ldexp(double(1024+mant),exp-25);
}
inline uint32_t ordered_float(float f){
 uint32_t b;std::memcpy(&b,&f,4);uint32_t magnitude=b&0x7fffffffu;return (b>>31)?0x80000000u-magnitude:0x80000000u+magnitude;
}
struct Metric {
 uint64_t count=0,exact=0,nonfinite=0,maxulp=0;
 uint64_t bins[5]={};double maxabs=0,maxrel=0,sumsq=0;json witness=nullptr;
 void add(float actual,double expected,json coord){
  ++count;
  if(!std::isfinite(actual)||!std::isfinite(expected)){++nonfinite;return;}
  double e=std::abs(double(actual)-expected);if(e==0)++exact;
  uint32_t a=ordered_float(actual),b=ordered_float(float(expected));
  uint64_t u=a>b?uint64_t(a)-b:uint64_t(b)-a;maxulp=std::max(maxulp,u);
  ++bins[u==0?0:u==1?1:u<=4?2:u<=16?3:4];
  sumsq+=e*e;maxrel=std::max(maxrel,e/std::max(std::abs(expected),1e-300));
  if(e>maxabs){maxabs=e;witness={{"coord",coord},{"actual",actual},{"fp64",expected}};}
 }
 json result()const{return {{"elements",count},{"exact_fp64",exact},{"nonfinite",nonfinite},
  {"max_abs",maxabs},{"max_relative_floor_1e_300",maxrel},{"rms",count?std::sqrt(sumsq/count):0},
  {"max_f32_ulp",maxulp},{"ulp_bins_0_1_2to4_5to16_gt16",bins},{"max_abs_witness",witness}};}
};
