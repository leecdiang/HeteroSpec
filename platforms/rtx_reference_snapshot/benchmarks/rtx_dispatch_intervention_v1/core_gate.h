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
inline FARPROC import_target(const char*dll,const char*symbol){
    auto image=(unsigned char*)GetModuleHandleW(nullptr);auto dos=(IMAGE_DOS_HEADER*)image;require(dos->e_magic==IMAGE_DOS_SIGNATURE,"PE DOS");
    auto nt=(IMAGE_NT_HEADERS64*)(image+dos->e_lfanew);require(nt->Signature==IMAGE_NT_SIGNATURE,"PE signature");
    auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];require(dir.VirtualAddress,"host has no import directory");
    for(auto d=(IMAGE_IMPORT_DESCRIPTOR*)(image+dir.VirtualAddress);d->Name;d++){
        if(_stricmp((char*)image+d->Name,dll))continue;require(d->OriginalFirstThunk,"named IAT required");
        auto name=(IMAGE_THUNK_DATA64*)(image+d->OriginalFirstThunk);auto slot=(IMAGE_THUNK_DATA64*)(image+d->FirstThunk);
        for(;name->u1.AddressOfData;name++,slot++){if(IMAGE_SNAP_BY_ORDINAL64(name->u1.Ordinal))continue;auto n=(IMAGE_IMPORT_BY_NAME*)(image+name->u1.AddressOfData);if(!strcmp((const char*)n->Name,symbol))return (FARPROC)slot->u1.Function;}
    }throw std::runtime_error("host lacks required shared import");
}
inline Json verify_plugin_core_imports(const fs::path&plugin,HMODULE core){
    HMODULE loaded=GetModuleHandleW(plugin.c_str());require(loaded&&same_path(module_path(loaded),plugin),"actual plugin path");
    auto image=(unsigned char*)loaded;auto dos=(IMAGE_DOS_HEADER*)image;require(dos->e_magic==IMAGE_DOS_SIGNATURE,"plugin PE");
    auto nt=(IMAGE_NT_HEADERS64*)(image+dos->e_lfanew);auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];Json out=Json::array();
    for(auto d=(IMAGE_IMPORT_DESCRIPTOR*)(image+dir.VirtualAddress);d->Name;d++){
        if(_stricmp((char*)image+d->Name,"ggml-base.dll"))continue;require(d->OriginalFirstThunk,"plugin named IAT");
        auto name=(IMAGE_THUNK_DATA64*)(image+d->OriginalFirstThunk);auto slot=(IMAGE_THUNK_DATA64*)(image+d->FirstThunk);
        for(;name->u1.AddressOfData;name++,slot++){require(!IMAGE_SNAP_BY_ORDINAL64(name->u1.Ordinal),"unnamed plugin core import");auto n=(IMAGE_IMPORT_BY_NAME*)(image+name->u1.AddressOfData);auto fn=(FARPROC)slot->u1.Function;
            require(fn==GetProcAddress(core,(char*)n->Name),"plugin core import target differs");HMODULE owner=nullptr;
            require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCWSTR)fn,&owner)&&owner==core,"plugin core symbol owner");
            out.push_back({{"symbol",(char*)n->Name},{"target",uint64_t((uintptr_t)fn)},{"owner_path",module_path(owner).u8string()}});
        }
    }require(!out.empty(),"plugin lacks core imports");return out;
}
inline void pin_numeric_file(const fs::path&p,const std::string&sha){HANDLE file=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);require(file!=INVALID_HANDLE_VALUE&&hash_handle(file)==sha,"pinned numerical file hash/path");/* Process-lifetime read lock; no unload or replacement. */}
inline Json verify_registry_import(const fs::path&runtime,const std::string&sha){
    auto fn=import_target("ggml.dll","ggml_backend_load");HMODULE owner=nullptr;require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCWSTR)fn,&owner),"registry function owner");
    auto path=runtime/"ggml.dll";require(same_path(module_path(owner),path),"registry DLL path");
    static HANDLE file=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);require(file!=INVALID_HANDLE_VALUE&&hash_handle(file)==sha,"registry DLL hash");
    require(GetProcAddress(owner,"ggml_backend_load")==fn&&GetProcAddress(owner,"ggml_backend_init_by_name")==import_target("ggml.dll","ggml_backend_init_by_name"),"registry IAT is not actual pinned export");
    return {{"path",module_path(owner).u8string()},{"sha256",sha},{"backend_load_IAT_target",uint64_t((uintptr_t)fn)},{"owner",uint64_t((uintptr_t)owner)}};
}

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
    Json verify_shared_import(const char*name){auto fn=import_target("ggml-base.dll",name);require(fn==resolve(name),"shared IAT differs from verified core export");verify_owner(fn);return {{"symbol",name},{"IAT_target",uint64_t((uintptr_t)fn)},{"owner_path",module_path(handle).u8string()},{"module_handle",uint64_t((uintptr_t)handle)}};}
    void initialize(){require(!poisoned,"invalid prior init order");bool called=false;std::call_once(once,[&]{init();ready=true;called=true;events.push_back("dll_initializer_returned");});if(!called)events.push_back("duplicate_request_no_export_call");}
    void require_ready(){if(!ready){poisoned=true;events.push_back("rejected_use_before_dll_init");throw std::runtime_error("DLL not initialized: host copy or order is insufficient");}require(!poisoned,"poisoned admission");}
    int64_t microseconds(){require_ready();return us();}
    int64_t milliseconds(){require_ready();return ms();}
    void test_direct_reinitialize(){require_ready();init();events.push_back("test_only_real_export_reinitialized");}
    Json receipt()const{return {{"path",path.u8string()},{"sha256",digest},{"module_handle",uint64_t((uintptr_t)handle)},{"functions",functions},{"events",events},{"ready",ready&&!poisoned},{"pid",GetCurrentProcessId()},{"lifetime","locked exact core and HMODULE retained to process exit; production initialize is call_once, never per compute"}};}
};
inline CoreGate& process_core(const fs::path&p,const std::string&sha){static CoreGate gate(p,sha);auto receipt=gate.receipt();require(same_path(receipt["path"].get<std::string>(),p)&&receipt["sha256"]==sha,"process core identity changed");gate.initialize();return gate;}
}
