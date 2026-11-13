#pragma once
// Exact host-file checks, no native/model/GPU dependency or hash shortcut.
#include "../budget_writer/posix.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cmath>
#include <sstream>
#include <vector>
namespace hs::n1chain {
inline FD captured_file(const std::string&root,const std::string&relative){
 const auto slash=relative.find('/');require(slash!=std::string::npos&&relative.find('/',slash+1)==std::string::npos,"two-component immutable capture path required");
 const auto d=relative.substr(0,slash),name=relative.substr(slash+1);filename(d);filename(name);auto r=absolute_dir(root);
 FD dir(::openat(r.n,d.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW));checked(dir.n,"open capture directory");FD f(::openat(dir.n,name.c_str(),O_RDONLY|O_NOFOLLOW));checked(f.n,"open captured numeric bytes");struct stat s{};checked(::fstat(f.n,&s),"stat captured bytes");require(S_ISREG(s.st_mode),"regular numeric file required");return f;
}
inline uint64_t raw_file_size(int f){struct stat s{};checked(::fstat(f,&s),"stat raw capture");require(s.st_size>=0,"negative raw byte size");return uint64_t(s.st_size);}
struct PrefixResult {uint64_t bytes_compared=0;bool pass=true;uint64_t layer=0,kv_head=0,position=0,dimension=0;std::string reason;};
inline PrefixResult compare_retained_prefix(const std::string&root,const std::string&before,const std::string&after,size_t old_head,size_t keep){
 require(keep<=old_head&&old_head<=4096,"retained prefix shape");auto a=captured_file(root,before),b=captured_file(root,after);const size_t row=128*2;
 require(raw_file_size(a.n)==36*8*old_head*row&&raw_file_size(b.n)==36*8*keep*row,"complete all-layer active KV byte lengths");
 std::array<unsigned char,1024*1024>x{},y{};PrefixResult result;
 for(size_t layer=0;layer<36;layer++)for(size_t h=0;h<8;h++)for(size_t off=0;off<keep*row;off+=x.size()){
  const size_t n=std::min(x.size(),keep*row-off);const auto ao=(layer*8+h)*old_head*row+off,bo=(layer*8+h)*keep*row+off;
  require(::pread(a.n,x.data(),n,off_t(ao))==ssize_t(n)&&::pread(b.n,y.data(),n,off_t(bo))==ssize_t(n),"retained prefix short read");
  for(size_t i=0;i<n;i+=2){const auto av=uint16_t(x[i])|(uint16_t(x[i+1])<<8),bv=uint16_t(y[i])|(uint16_t(y[i+1])<<8);
   if(av!=bv||(av&0x7c00)==0x7c00||(bv&0x7c00)==0x7c00){result.bytes_compared+=i+2;result.pass=false;result.layer=layer;result.kv_head=h;result.position=(off+i)/row;result.dimension=((off+i)%row)/2;result.reason="STRICT_RETAINED_ACTIVE_F16_FIRST_DIFFERENCE_OR_NONFINITE";return result;}}
  result.bytes_compared+=n;
 }return result;
}
inline void require_owned_stable(const std::vector<float>&before,const std::vector<float>&after){
 require(before.size()==151936&&after.size()==before.size(),"complete owned vocabulary row");
 for(size_t i=0;i<before.size();++i)require(std::isfinite(before[i])&&std::isfinite(after[i]),"nonfinite owned vocabulary row");
 require(std::memcmp(before.data(),after.data(),before.size()*sizeof(float))==0,"owned output changed across actual decode");
}
}
