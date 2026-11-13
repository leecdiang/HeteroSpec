// Independent streaming finite/greedy checker. Standard-library-only ELF.
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <cmath>
#include <cstring>
#include <filesystem>
using J=nlohmann::json;
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
int main(int argc,char**argv){try{need(argc==2,"raw CPU job");std::ifstream in(argv[1]);J j;in>>j;J out=J::array();for(auto&f:j){std::string path=f.at("path"),type=f.at("type");size_t bytes=f.at("bytes");need(std::filesystem::file_size(path)==bytes,"raw size");std::ifstream x(path,std::ios::binary);need(bool(x),"raw open");if(type=="F32"){need(bytes==151936*4,"full vocabulary vector");std::vector<float>v(151936);x.read(reinterpret_cast<char*>(v.data()),bytes);need(size_t(x.gcount())==bytes,"short F32");int best=0;for(size_t i=0;i<v.size();++i){need(std::isfinite(v[i]),"nonfinite F32");if(v[i]>v[best])best=i;}out.push_back({{"file",f.at("name")},{"greedy",best},{"bytes",bytes}});}else{need(type=="F16"&&bytes%2==0,"raw KV type");char b[65536];size_t done=0;while(done<bytes){size_t n=std::min(sizeof b,bytes-done);x.read(b,n);need(size_t(x.gcount())==n,"short KV");for(size_t i=0;i<n;i+=2){uint16_t w;std::memcpy(&w,b+i,2);need((w&0x7c00)!=0x7c00,"nonfinite F16");}done+=n;}out.push_back({{"file",f.at("name")},{"finite",true},{"bytes",bytes}});}}std::cout<<J({{"status","PASS_INDEPENDENT_RAW_FINITE_AND_GREEDY"},{"files",out},{"GPU_contexts",0},{"model_calls",0}}).dump()<<'\n';return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
