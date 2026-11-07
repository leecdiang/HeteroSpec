#pragma once
// Included after the worker's JSON/hash/clock helpers. One host writer only.
#include "llama-context.h"
#include <regex>
#include <cctype>
#include <limits>
namespace hs_repair {
struct Options {
    std::string prefill="native";
    bool probe=false;
    std::vector<int> teacher;
    std::string trace_mode="off", pattern="^(l_out|result_norm|result_output)(-[0-9]+)?$";
    std::vector<std::string> phases={"PREFILL","ORDINARY","VERIFY"};
    int min_position=0, max_position=std::numeric_limits<int>::max();
    size_t max_files=256,max_bytes=256ULL*1024*1024,files=0,bytes=0;
    fs::path root;
    std::string error;
    bool enabled=false;
};
inline Options opt;
inline void configure(const json& slot,const fs::path& dir){
    opt=Options{};opt.root=dir;
    auto j=slot.at("repair");opt.prefill=j.at("prefill").get<std::string>();
    need(opt.prefill=="native"||opt.prefill=="reference"||opt.prefill=="pq"||opt.prefill=="qb","repair prefill policy");
    opt.probe=j.value("probe",false);
    if(j.contains("teacher_tokens"))opt.teacher=j.at("teacher_tokens").get<std::vector<int>>();
    need(opt.probe||opt.teacher.empty(),"teacher forcing is diagnostic only");
    need(opt.teacher.size()<128,"teacher prefix exceeds fixed cap");
    for(int id:opt.teacher)need(id>=0&&id<151936,"bad teacher token");
    auto tr=j.value("trace",json::object());opt.trace_mode=tr.value("mode",std::string("off"));
    need(opt.trace_mode=="off"||opt.trace_mode=="tensors","unknown trace mode");
    opt.pattern=tr.value("name_regex",opt.pattern);
    if(tr.contains("phases"))opt.phases=tr.at("phases").get<std::vector<std::string>>();
    opt.min_position=tr.value("min_call_position",0);
    opt.max_position=tr.value("max_call_position",std::numeric_limits<int>::max());
    opt.max_files=tr.value("max_files",size_t(256));opt.max_bytes=tr.value("max_bytes",size_t(256ULL*1024*1024));
    need(opt.max_files>0&&opt.max_files<=4096&&opt.max_bytes>0&&opt.max_bytes<=2ULL*1024*1024*1024,"trace budget");
    need(opt.min_position>=0&&opt.max_position>=opt.min_position,"trace position range");
    std::regex validate(opt.pattern);
    opt.enabled=opt.trace_mode=="tensors";
    need(!opt.enabled||slot.at("observer")=="heavy","tensor capture not allowed in clean/timing arm");
    if(opt.enabled)fs::create_directories(dir/"trace");
}
inline bool selected(const std::string&name,const std::string&phase,int pos){
    return opt.enabled && pos>=opt.min_position && pos<=opt.max_position &&
      std::find(opt.phases.begin(),opt.phases.end(),phase)!=opt.phases.end() &&
      std::regex_match(name,std::regex(opt.pattern));
}
inline void write_bytes(const fs::path&p,const void*bytes,size_t n){
    fs::create_directories(p.parent_path());std::ofstream f(p,std::ios::binary|std::ios::trunc);
    need(bool(f),"binary file open");f.write(static_cast<const char*>(bytes),std::streamsize(n));need(bool(f),"binary file write");
}
inline json state_snapshot(llama_context*c){
    auto m=llama_get_memory(c);auto n=llama_state_seq_get_size(c,0);
    std::vector<uint8_t>b(n);need(n>0&&llama_state_seq_get_data(c,b.data(),n,0)==n,"state snapshot failed");
    Sha256 h;h.update(reinterpret_cast<const char*>(b.data()),b.size());
    return {{"bytes",n},{"sha256",h.finish()},{"min",llama_memory_seq_pos_min(m,0)},{"max",llama_memory_seq_pos_max(m,0)}};
}
inline int sample_vector(const std::vector<float>&v){
    need(!v.empty(),"empty transferred logits");int best=0;
    for(size_t i=0;i<v.size();++i){need(std::isfinite(v[i]),"nonfinite transferred logit");if(v[i]>v[best])best=int(i);}
    return best;
}
inline std::string safe_name(const std::string&s){
    std::string out;for(unsigned char c:s)out+=(std::isalnum(c)||c=='_'||c=='-')?char(c):'_';return out;
}
}
