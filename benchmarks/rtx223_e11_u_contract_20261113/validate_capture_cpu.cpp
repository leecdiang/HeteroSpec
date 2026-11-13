// Independent CPU-only full-capture checker. No CUDA headers or library linkage.
#include "u_oracle.hpp"
#include <fstream>
#include <vector>
#include <stdexcept>
#include <cstdio>
#include <cfenv>
static std::vector<unsigned char> load(const char*path,size_t bytes){std::ifstream f(path,std::ios::binary);std::vector<unsigned char>v((std::istreambuf_iterator<char>(f)),{});if(v.size()!=bytes)throw std::runtime_error("input size");return v;}
static float f32(const std::vector<unsigned char>&v,size_t i){float x;memcpy(&x,v.data()+i,4);return x;}
static float half(const std::vector<unsigned char>&v,size_t i){unsigned h=v[i]|(unsigned(v[i+1])<<8),e=(h>>10)&31,m=h&1023;if(e==31)throw std::runtime_error("weight half nonfinite");return (h&32768?-1.0f:1.0f)*float(e?std::ldexp(double(m+1024),int(e)-25):std::ldexp(double(m),-24));}
int main(int argc,char**argv){
 try{
  if(argc!=5||std::fegetround()!=FE_TONEAREST)throw std::runtime_error("args/RN");
  auto w=load(argv[1],17825792),x=load(argv[2],131072),raw=load(argv[3],36864),y=load(argv[4],131072);
  std::vector<int>q(32768),coverage(36864);std::vector<float>d(1024);
  for(int col=0;col<8;++col)for(int i0=0;i0<4096;i0+=4){
   int s=(i0%256)/32,k=i0%32,g=col%8;size_t base=size_t(i0/256)*144*16;
   size_t offset=base+size_t((s/2)*32+4*g+(k%16)/4)*16+(2*(s%2)+k/16)*4;
   for(int j=0;j<4;++j){q[col*4096+i0+j]=int(int8_t(raw[offset+j]));coverage[offset+j]++;}
   if(k==0){size_t at=base+size_t(128+4*(g/2)+s/2)*16+(2*(s%2)+g%2)*4;d[col*128+i0/32]=f32(raw,at);for(int j=0;j<4;++j)coverage[at+j]++;}
  }
  for(int n:coverage)if(n!=1)throw std::runtime_error("raw layout not bijective");
  int failed=0,nonunique=0,min_witness=5;
  for(int col=0;col<8;++col)for(int b=0;b<128;++b){float block_x[32];int block_q[32];for(int k=0;k<32;++k){block_x[k]=f32(x,size_t(col*4096+b*32+k)*4);block_q[k]=q[col*4096+b*32+k];}auto r=e11_oracle::block(block_x,block_q,d[col*128+b]);failed+=!r.pass;nonunique+=r.shared_inverse_witnesses>1;min_witness=std::min(min_witness,r.shared_inverse_witnesses);}
  int output_fail=0;double max_error=0,max_ratio=0;const double u=std::ldexp(1.0,-24),gamma=64*u/(1-64*u);
  for(int col=0;col<8;++col)for(int row=0;row<4096;++row){
   double sum=0,absolute=0;
   for(int b=0;b<128;++b){size_t off=size_t(row*128+b)*34;float dw=half(w,off);if(!std::isfinite(dw)||std::fabs(dw)>1)throw std::runtime_error("weight domain");int dot=0;for(int k=0;k<32;++k)dot+=int(int8_t(w[off+2+k]))*q[col*4096+b*32+k];double term=double(dot)*double(dw)*double(d[col*128+b]);sum+=term;absolute+=std::fabs(term);}
   float value=f32(y,size_t(col*4096+row)*4);output_fail+=!e11_oracle::output(value,sum,absolute);double error=std::fabs(double(value)-sum);max_error=std::max(max_error,error);max_ratio=std::max(max_ratio,error/(gamma*absolute+128*double(FLT_MIN)));
  }
  std::printf("{\"pass\":%s,\"quant_blocks\":1024,\"quant_values\":32768,\"layout_bytes_checked\":36864,\"quant_block_fail\":%d,\"nonunique_witness_blocks\":%d,\"minimum_witnesses\":%d,\"output_values\":32768,\"output_bound_fail\":%d,\"maximum_output_error\":%.17g,\"maximum_error_over_bound\":%.17g,\"CUDA_initializations\":0}\n",!failed&&!output_fail?"true":"false",failed,nonunique,min_witness,output_fail,max_error,max_ratio);
  return failed||output_fail?2:0;
 }catch(const std::exception&e){std::fprintf(stderr,"CPU checker failure: %s\n",e.what());return 3;}
}
