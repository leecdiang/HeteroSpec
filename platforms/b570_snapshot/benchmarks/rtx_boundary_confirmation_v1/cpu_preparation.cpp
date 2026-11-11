// CPU-only common-producer preparation. No GGML/CUDA dependency or graph call.
#include "nlohmann/json.hpp"
#include <windows.h>
#include <psapi.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstring>
#include <cctype>
#include <cstdint>
#include <stdexcept>
using J=nlohmann::ordered_json;namespace fs=std::filesystem;
static void check(bool x,const char*s){if(!x)throw std::runtime_error(s);}
static int64_t tick(){LARGE_INTEGER t;check(QueryPerformanceCounter(&t),"QPC");return t.QuadPart;}
static std::vector<unsigned char> readbytes(fs::path p){std::ifstream f(p,std::ios::binary);check(bool(f),"source bytes");return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
static void noGPU(){HMODULE m[2048];DWORD n;check(EnumProcessModules(GetCurrentProcess(),m,sizeof(m),&n),"module scan");for(size_t i=0;i<n/sizeof(HMODULE)&&i<2048;i++){char p[32768];check(GetModuleFileNameA(m[i],p,sizeof(p)),"module path");std::string s=p;for(auto&c:s)c=tolower(c);check(s.find("cuda")==std::string::npos&&s.find("cublas")==std::string::npos&&s.find("vulkan")==std::string::npos,"CPU-only modules");}}
int main(int argc,char**argv){try{check(argc==3,"job output");noGPU();std::ifstream input(argv[1]);J job;input>>job;auto c=job.at("context");fs::path root=c.at("root").get<std::string>(),out=argv[2];check(!fs::exists(out),"fresh output");fs::create_directories(out);const char* names[]={"Q","K","V","mask"};std::vector<std::vector<unsigned char>> expected,buffers;int D=c.at("d"),H=c.at("Hq"),q=c.at("q"),S=c.at("keys");auto m=c.at("metadata");for(auto name:names)expected.push_back(readbytes(root/(std::string(name)+".bin")));
    std::vector<unsigned char> canonical(expected[0].size());for(int j=0;j<q;j++)for(int h=0;h<H;h++)for(int a=0;a<D;a++){size_t src=size_t(a)*m["Q"]["nb"][0].get<size_t>()+size_t(j)*m["Q"]["nb"][1].get<size_t>()+size_t(h)*m["Q"]["nb"][2].get<size_t>();size_t dst=size_t((j*H+h)*D+a)*4;memcpy(canonical.data()+dst,expected[0].data()+src,4);}
    LARGE_INTEGER freq;check(QueryPerformanceFrequency(&freq)&&freq.QuadPart>0,"QPC frequency");auto alloc0=tick();for(auto&v:expected)buffers.emplace_back(v.size());auto alloc1=tick();struct Sample{int64_t a,b;};std::vector<Sample> samples(65);std::string storage=c.at("storage"),mask=c.at("mask");
    for(int i=0;i<65;i++){auto a=tick();if(storage=="permuted")memcpy(buffers[0].data(),canonical.data(),canonical.size());else for(int h=0;h<H;h++)for(int j=0;j<q;j++)memcpy(buffers[0].data()+size_t(h*q+j)*D*4,canonical.data()+size_t(j*H+h)*D*4,size_t(D)*4);
        for(int role=1;role<=2;role++)memcpy(buffers[role].data(),expected[role].data(),expected[role].size());
        for(int j=0;j<q;j++)for(int k=0;k<S;k++){bool visible=mask=="causal"?k<S-q+j+1:mask=="irregular"?(k+j)%3!=0:k==(S-q+j)%S;uint32_t bits=visible?0:0xff800000;memcpy(buffers[3].data()+size_t(j*S+k)*4,&bits,4);}auto b=tick();check(b>a,"positive CPU interval");samples[i]={a,b};check(buffers==expected,"actual full preparation bytes");}
    J rows=J::array();for(int i=0;i<65;i++)rows.push_back({{"index",i},{"warmup",i==0},{"begin",samples[i].a},{"end",samples[i].b},{"all_full_bytes_exact",true}});for(int role=0;role<4;role++){std::ofstream f(out/(std::string("prepared_")+names[role]+".bin"),std::ios::binary);f.write((const char*)buffers[role].data(),buffers[role].size());check(bool(f),"CPU prepared write");}
    noGPU();std::ofstream report(out/"CPU_PREPARATION.json");report<<J({{"status","PASS"},{"pid",GetCurrentProcessId()},{"case_id",c["case_id"]},{"QPC_frequency",freq.QuadPart},{"cold_output_allocation_ticks",alloc1-alloc0},{"rows",rows},{"GPU_calls",0},{"CUDA_loads",0},{"meaning","common logical Q and already available complete KV;actual Q packing+KVcopy+mask creation;not decoder operand production"}}).dump()<<"\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
