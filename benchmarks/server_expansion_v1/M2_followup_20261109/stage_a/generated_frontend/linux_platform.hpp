#pragma once
// Native Linux module provenance. No Windows DLL emulation and no GPU calls.
#include <array>
#include <cerrno>
#include <filesystem>
#include <link.h>
#include <stdexcept>
#include <string>
#include <vector>
#include <unistd.h>
namespace linux_transfer {
inline std::filesystem::path executable() {
    std::array<char,32768> b{};
    const auto n=::readlink("/proc/self/exe",b.data(),b.size()-1);
    if(n<=0 || size_t(n)>=b.size()-1)throw std::runtime_error("/proc/self/exe");
    return std::string(b.data(),size_t(n));
}
inline std::vector<std::string> modules() {
    std::vector<std::string> out{executable().string()};
    ::dl_iterate_phdr([](dl_phdr_info* p,size_t,void* data)->int {
        auto& v=*static_cast<std::vector<std::string>*>(data);
        if(p->dlpi_name && *p->dlpi_name)v.emplace_back(p->dlpi_name);
        return 0;
    }, &out);
    return out; // vDSO is reported but is not a file; host records that explicitly.
}
}
