#pragma once
#include <fstream>
#include <sstream>
#include <set>
#include <string>
#include <vector>
#include <stdexcept>
// Read this process only. Executable ELF mappings exclude GGUF and KV mappings.
inline std::vector<std::string> hs_loaded_modules(){
    std::ifstream maps("/proc/self/maps");if(!maps)throw std::runtime_error("Native module maps");
    std::set<std::string> files;std::string line;
    while(std::getline(maps,line)){
        std::istringstream row(line);std::string address,permissions,offset,device,inode,path;
        row>>address>>permissions>>offset>>device>>inode;std::getline(row,path);
        auto at=path.find_first_not_of(" \t");if(at==std::string::npos||permissions.find('x')==std::string::npos)continue;
        path=path.substr(at);if(path.empty()||path[0]!='/')continue;
        if(path.find(" (deleted)")!=std::string::npos)throw std::runtime_error("Deleted loaded ELF");
        std::ifstream f(path,std::ios::binary);char magic[4]{};f.read(magic,4);
        if(!f||std::string(magic,4)!=std::string("\x7f" "ELF",4))throw std::runtime_error("Unverifiable executable file mapping");
        files.insert(path);
    }
    if(files.empty())throw std::runtime_error("Empty native ELF inventory");
    return {files.begin(),files.end()};
}
