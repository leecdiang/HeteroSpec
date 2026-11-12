// Synthetic host-file tests of actual raw-prefix/ownership checker code only.
// No native backend, model, device, context, CUDA or dynamic-loader dependency.
#include "../native/raw_checks.hpp"
#include <cmath>
#include <fstream>
#include <functional>
#include <iostream>
using namespace hs::n1chain;
namespace {
void rejects(const std::function<void()>&f){bool yes=false;try{f();}catch(const std::exception&){yes=true;}require(yes,"expected failure");}
void write(const std::string&p,const std::vector<unsigned char>&b){std::ofstream f(p,std::ios::binary);require(bool(f),"synthetic output open");f.write(reinterpret_cast<const char*>(b.data()),b.size());require(bool(f),"synthetic output write");}
void bits(std::vector<unsigned char>&v,size_t i,uint16_t value){v.at(i*2)=value&255;v.at(i*2+1)=value>>8;}
}
int main(int argc,char**argv){require(argc==2,"provide fresh synthetic directory");const std::string root=argv[1];checked(::mkdir(root.c_str(),0700),"fresh raw mock directory");for(const auto&name:{"old","good","bad","nanold","nannew"})checked(::mkdir((root+"/"+name).c_str(),0700),"fresh raw case");
 constexpr size_t oldHead=3,keep=1,width=128,groups=36*8;std::vector<unsigned char>a(groups*oldHead*width*2),b(groups*keep*width*2);
 for(size_t g=0;g<groups;g++)for(size_t p=0;p<oldHead;p++)for(size_t d=0;d<width;d++){const uint16_t v=uint16_t(0x3000+g+p*32+d%16);bits(a,(g*oldHead+p)*width+d,v);if(p<keep)bits(b,(g*keep+p)*width+d,v);}
 write(root+"/old/k.bin",a);write(root+"/good/k.bin",b);int n=0;
 const auto correct=compare_retained_prefix(root,"old/k.bin","good/k.bin",oldHead,keep);require(correct.pass&&correct.bytes_compared==groups*keep*width*2,"retained prefix uses old physical stride and all layers");++n;
 auto bad=b;bits(bad,groups*width-1,0x4000);write(root+"/bad/k.bin",bad);const auto mismatch=compare_retained_prefix(root,"old/k.bin","bad/k.bin",oldHead,keep);require(!mismatch.pass&&mismatch.layer==35&&mismatch.kv_head==7&&mismatch.position==0&&mismatch.dimension==127,"last retained scalar coordinate");++n;
 auto na=a,nb=b;bits(na,0,0x7e00);bits(nb,0,0x7e00);write(root+"/nanold/k.bin",na);write(root+"/nannew/k.bin",nb);require(!compare_retained_prefix(root,"nanold/k.bin","nannew/k.bin",oldHead,keep).pass,"identical active NaNs cannot pass strict bytes profile");++n;
 std::vector<float>v(151936,1.f),w=v;require_owned_stable(v,w);w.back()=2.f;rejects([&]{require_owned_stable(v,w);});w=v;v[0]=w[0]=NAN;rejects([&]{require_owned_stable(v,w);});++n;
 rejects([&]{compare_retained_prefix(root,"../old/k.bin","good/k.bin",oldHead,keep);});rejects([&]{compare_retained_prefix(root,"old/k.bin","good/k.bin",oldHead,2);});++n;
 std::cout<<"{\"tests\":"<<n<<",\"failures\":0,\"evidence\":\"INDEPENDENT_HOST_RAW_SYNTHETIC\",\"native_backend_calls\":0,\"models\":0,\"contexts\":0,\"placements\":0,\"forwards\":0}\n";
}
