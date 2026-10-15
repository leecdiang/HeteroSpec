#pragma once
#define NOMINMAX
#include <windows.h>
#include <psapi.h>
#include "oracle.hpp"
static json module_inventory(){
 HMODULE hs[2048];DWORD bytes=0;require(EnumProcessModules(GetCurrentProcess(),hs,sizeof(hs),&bytes)!=0,"module enumeration");
 require(bytes<=sizeof(hs),"module inventory overflow");json a=json::array();
 for(unsigned i=0;i<bytes/sizeof(HMODULE);++i){char name[32768];require(GetModuleFileNameExA(GetCurrentProcess(),hs[i],name,sizeof(name))!=0,"module path");
  std::string s=name,low=s;std::transform(low.begin(),low.end(),low.begin(),[](unsigned char c){return char(std::tolower(c));});
  for(auto bad:{"vulkan","cuda","cublas","cudnn","igvk","nvoglv","llama"})require(low.find(bad)==std::string::npos,"forbidden GPU/model module");
  if(low.find("ggml-")!=std::string::npos)require(low.find("ggml-base.dll")!=std::string::npos||low.find("ggml-cpu.dll")!=std::string::npos,"non-CPU ggml module");
  a.push_back(s);
 }return a;
}
