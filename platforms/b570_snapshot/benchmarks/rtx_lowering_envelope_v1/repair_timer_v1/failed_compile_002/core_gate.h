#pragma once
#include "ggml.h"
#include "nlohmann/json.hpp"
#include <windows.h>
#include <psapi.h>
#include <bcrypt.h>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <vector>
#include <array>
#include <sstream>
#include <iomanip>

namespace repair113 {
using Json=nlohmann::ordered_json;
namespace fs=std::filesystem;
inline void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
inline std::string hash_handle(HANDLE file){
    BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    require(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA256 provider");
    DWORD length=0,received=0;require(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&length,sizeof(length),&received,0)>=0,"SHA256 object");
    std::vector<unsigned char>object(length);std::array<unsigned char,32>digest{};
    require(BCryptCreateHash(alg,&hash,object.data(),length,nullptr,0,0)>=0,"SHA256 hash");
    LARGE_INTEGER zero{};require(SetFilePointerEx(file,zero,nullptr,FILE_BEGIN),"seek core");
    std::array<unsigned char,65536>block{};DWORD n=0;
    do{require(ReadFile(file,block.data(),DWORD(block.size()),&n,nullptr),"read core");if(n)require(BCryptHashData(hash,block.data(),n,0)>=0,"hash core");}while(n);
    require(BCryptFinishHash(hash,digest.data(),DWORD(digest.size()),0)>=0,"finish SHA256");
    BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(alg,0);
    std::ostringstream s;for(auto x:digest)s<<std::hex<<std::setw(2)<<std::setfill('0')<<int(x);return s.str();
}
inline fs::path module_path(HMODULE module){std::vector<wchar_t>b(32768);DWORD n=GetModuleFileNameW(module,b.data(),DWORD(b.size()));require(n>0&&n<b.size(),"module path");return fs::weakly_canonical(fs::path(std::wstring(b.data(),n)));}
inline bool same_path(const fs::path&a,const fs::path&b){return _wcsicmp(fs::weakly_canonical(a).c_str(),fs::weakly_canonical(b).c_str())==0;}
inline Json modules(){HMODULE list[2048];DWORD bytes=0;require(EnumProcessModules(GetCurrentProcess(),list,sizeof(list),&bytes),"enumerate modules");require(bytes<=sizeof(list),"module list bound");Json out=Json::array();for(size_t i=0;i<bytes/sizeof(HMODULE);i++)out.push_back(module_path(list[i]).u8string());return out;}
inline void no_gpu_modules(){for(const auto&p:modules()){std::string n=fs::path(p.get<std::string>()).filename().string();for(char&c:n)c=char(tolower((unsigned char)c));for(const char*bad:{"ggml-cuda","ggml-vulkan","nvcuda","cudart","cublas","cupti","vulkan","nvapi","nvldumdx"})require(n.find(bad)==std::string::npos,"CPU path forbidden GPU module");}}

// A process-lifetime owner: leave the verified module and locked file resident.
// No unload/reload or timer reset between graph calls. All arms use this gate.
class CoreGate {
    HANDLE file=INVALID_HANDLE_VALUE;HMODULE handle=nullptr;fs::path path;
    bool ready=false,poisoned=false;std::once_flag once;
    using Init=decltype(&ggml_time_init);using Clock=decltype(&ggml_time_us);
    Init init=nullptr;Clock us=nullptr,ms=nullptr;
    Json events=Json::array(),functions=Json::object();std::string digest;
public:
    CoreGate(const fs::path&expected,const std::string&expected_sha):path(fs::weakly_canonical(expected)){
        require(path.is_absolute()&&path.filename()==L"ggml-base.dll","explicit core DLL path required");
        file=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);require(file!=INVALID_HANDLE_VALUE,"lock exact core file");
        digest=hash_handle(file);require(digest==expected_sha,"core file SHA256 mismatch");events.push_back("path_and_hash_verified");
        for(const auto&p:modules()){fs::path candidate(p.get<std::string>());if(_wcsicmp(candidate.filename().c_str(),L"ggml-base.dll")==0)require(same_path(candidate,path),"different core DLL already loaded");}
        handle=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);require(handle,"load exact CPU core");
        require(same_path(module_path(handle),path),"loaded core path mismatch");events.push_back("exact_core_loaded");
        init=(Init)resolve("ggml_time_init");us=(Clock)resolve("ggml_time_us");ms=(Clock)resolve("ggml_time_ms");events.push_back("owned_exports_resolved");
    }
    HMODULE module()const{return handle;}
    void verify_owner(FARPROC fn){HMODULE owner=nullptr;require(fn&&GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCWSTR)fn,&owner),"export address owner");require(owner==handle&&same_path(module_path(owner),path),"export belongs to wrong module");}
    FARPROC resolve(const char*name){auto fn=GetProcAddress(handle,name);require(fn,"missing exact core export");verify_owner(fn);functions[name]={{"address",uint64_t((uintptr_t)fn)},{"owner_path",module_path(handle).u8string()},{"RVA",uint64_t((uintptr_t)fn-(uintptr_t)handle)}};return fn;}
    void initialize(){require(!poisoned,"invalid prior init order");bool called=false;std::call_once(once,[&]{init();ready=true;called=true;events.push_back("dll_initializer_returned");});if(!called)events.push_back("duplicate_request_no_export_call");}
    void require_ready(){if(!ready){poisoned=true;events.push_back("rejected_use_before_dll_init");throw std::runtime_error("DLL not initialized: host copy or order is insufficient");}require(!poisoned,"poisoned admission");}
    int64_t microseconds(){require_ready();return us();}
    int64_t milliseconds(){require_ready();return ms();}
    void test_direct_reinitialize(){require_ready();init();events.push_back("test_only_real_export_reinitialized");}
    Json receipt()const{return {{"path",path.u8string()},{"sha256",digest},{"module_handle",uint64_t((uintptr_t)handle)},{"functions",functions},{"events",events},{"ready",ready&&!poisoned},{"pid",GetCurrentProcessId()},{"lifetime","locked exact core and HMODULE retained to process exit; production initialize is call_once, never per compute"}};}
};
inline CoreGate& process_core(const fs::path&p,const std::string&sha){static CoreGate gate(p,sha);auto receipt=gate.receipt();require(same_path(receipt["path"].get<std::string>(),p)&&receipt["sha256"]==sha,"process core identity changed");gate.initialize();return gate;}
}
