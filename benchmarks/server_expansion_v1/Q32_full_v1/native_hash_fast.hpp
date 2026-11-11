#pragma once
// Same complete SHA-256, using the pre-existing hash-bound system libcrypto.
// No library installation/upgrade, no cached digest, no model-byte omission.
#include <dlfcn.h>
#include <sys/mman.h>
#include <sys/stat.h>
namespace fast_digest {
using sha256_function=unsigned char*(*)(const unsigned char*,size_t,unsigned char*);
static sha256_function implementation(){
    static auto fn=[](){auto*h=::dlopen("/usr/lib/x86_64-linux-gnu/libcrypto.so.3",RTLD_NOW|RTLD_LOCAL);need(h,"Existing pinned libcrypto unavailable");auto p=reinterpret_cast<sha256_function>(::dlsym(h,"SHA256"));need(p,"Pinned OpenSSL SHA256 ABI unavailable");return p;}();return fn;
}
static std::string file(const fs::path&path){
    int fd=::open(path.c_str(),O_RDONLY|O_CLOEXEC);need(fd>=0,"SHA256 file open");struct stat st{};
    if(::fstat(fd,&st)!=0||st.st_size<=0){::close(fd);throw std::runtime_error("SHA256 nonempty regular model/journal file required");}
    const size_t n=size_t(st.st_size);auto*data=::mmap(nullptr,n,PROT_READ,MAP_PRIVATE,fd,0);::close(fd);need(data!=MAP_FAILED,"SHA256 read-only mmap");
    unsigned char bytes[32];auto fn=implementation();auto*p=fn(static_cast<const unsigned char*>(data),n,bytes);const int rc=::munmap(data,n);need(p&&rc==0,"Complete SHA256 or read-only unmap failed");std::string out;for(auto x:bytes){out+="0123456789abcdef"[x>>4];out+="0123456789abcdef"[x&15];}return out;
}
}
