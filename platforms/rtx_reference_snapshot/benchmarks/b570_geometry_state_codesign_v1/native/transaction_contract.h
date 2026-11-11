#pragma once
#include <vector>
#include <stdexcept>
inline bool b570_commit(std::vector<int>&out,std::vector<bool>&flags,int id,int cap,bool eog){
 if(cap!=128||id<0||id>=128256||out.size()!=flags.size()||out.size()>=size_t(cap)||(!flags.empty()&&flags.back()))throw std::runtime_error("Native suffix prevented");
 out.push_back(id);flags.push_back(eog);return eog||out.size()==size_t(cap);
}
inline int b570_keep(int base,int accepted){if(base<0||accepted<0||accepted>1)throw std::runtime_error("k1 rollback bound");return base+1+accepted;}
