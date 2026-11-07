#pragma once
#include "llama.h"
#include "../src/hsc_counter.h"
#include "../src/hs_scope.h"
#include "capture95.h"
#include "ggml.h"
#include "sampling.h"
#include "nlohmann/json.hpp"
#include <windows.h>
#include <psapi.h>
#include <fstream>
#include <map>
#include <cstring>
#include <stdexcept>
namespace hs {
using j=nlohmann::ordered_json;
inline std::map<llama_context*,std::string> roles;
inline j graphs=j::array();
inline std::string phase="prefill";
inline unsigned long sequence=0;
inline bool enabled(){return hsc::is_heavy() && std::getenv("HS_NATIVE_CAPTURE")!=nullptr;}
inline void emit(j x){
    if(!enabled())return;
    x["sequence"]=sequence++;
    std::ofstream f(std::getenv("HS_NATIVE_CAPTURE"),std::ios::binary|std::ios::app);
    f<<x.dump()<<"\n";f.flush();if(!f)throw std::runtime_error("trace write failed");
}
inline j position(llama_context*c){auto*m=llama_get_memory(c);return {{"sequence",0},{"min",llama_memory_seq_pos_min(m,0)},{"max",llama_memory_seq_pos_max(m,0)}};}
inline bool callback(ggml_tensor*t,bool ask,void*data){
    if(q95capture::callback(t,ask))return true;
    if(ask&&enabled()&&(std::strcmp(t->name,"hs_attention_q-0")==0||std::strcmp(t->name,"result_output")==0||std::strcmp(t->name,"attn_norm-0")==0||std::strcmp(t->name,"hs_attn_single_query-0")==0||std::strcmp(t->name,"hs_attn_query_batch-0")==0||std::strcmp(t->name,"jsa_llama_query_batch-0")==0))
        graphs.push_back({{"role",static_cast<const char*>(data)},{"name",t->name},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}}});
    return false;
}
inline j modules(){HMODULE m[1024];DWORD count=0;j a=j::array();
    if(EnumProcessModules(GetCurrentProcess(),m,sizeof(m),&count))for(unsigned i=0;i<count/sizeof(HMODULE);i++){
        char p[32768];if(GetModuleFileNameA(m[i],p,sizeof(p)))a.push_back(p);
    }return a;
}
inline int decode(llama_context*c,llama_batch b,const char*role){
    hs_scope::guard scope(role,phase=="prefill");
    hsc::decode_begin(c,role,phase=="prefill",b.n_tokens);
    if(!enabled()){int rc=llama_decode(c,b);hsc::decode_end();return rc;} // no added sync in baseline/counts/lite
    roles[c]=role;graphs=j::array();j ids=j::array(),pos=j::array(),seq=j::array(),mask=j::array();
    int start=position(c)["max"].get<int>()+1;
    for(int i=0;i<b.n_tokens;i++){ids.push_back(b.token[i]);pos.push_back(b.pos?b.pos[i]:start+i);j s=j::array();
        if(b.seq_id){for(int k=0;k<b.n_seq_id[i];k++)s.push_back(b.seq_id[i][k]);}else s.push_back(0);
        seq.push_back(s);mask.push_back(b.logits?bool(b.logits[i]):i==b.n_tokens-1);}
    auto before=position(c);int rc=llama_decode(c,b);hsc::decode_end();llama_synchronize(c);
    emit({{"event","decode"},{"scope_mask",hs_scope::mask()},{"scope_active",hs_scope::active},{"role",role},{"phase",phase},{"tokens",ids},{"positions",pos},{"sequence_ids",seq},{"logits_mask",mask},
      {"caller_batch",b.n_tokens},{"ub_capacity",llama_n_ubatch(c)},{"before",before},{"after",position(c)},{"graphs",graphs},{"returncode",rc}});
    return rc;
}
inline void sample(llama_context*c,int idx,int id){
    if(!enabled())return;const float*l=llama_get_logits_ith(c,idx);if(!l)throw std::runtime_error("sample missing logits");
    int nv=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(c))),a=0,b=1;if(l[b]>l[a])std::swap(a,b);
    for(int i=2;i<nv;i++){if(l[i]>l[a]){b=a;a=i;}else if(l[i]>l[b])b=i;}
    emit({{"event","sample"},{"role",roles[c]},{"phase",phase},{"logits_index",idx},{"selected_id",id},{"top1",a},{"top2",b},
      {"top1_score",l[a]},{"top2_score",l[b]},{"selected_score",l[id]},{"positions",position(c)}});
}
inline std::vector<uint8_t> state(llama_context*c){llama_synchronize(c);std::vector<uint8_t>b(llama_state_get_size(c));
    if(llama_state_get_data(c,b.data(),b.size())!=b.size())throw std::runtime_error("short serialized state");return b;}
template<class T>inline void bytes(const char*suffix,const std::vector<T>&b){
    std::string p=std::getenv("HS_NATIVE_CAPTURE");std::ofstream f(p+suffix,std::ios::binary);
    f.write(reinterpret_cast<const char*>(b.data()),b.size()*sizeof(T));f.flush();if(!f)throw std::runtime_error("state witness write failed");}
inline llama_context*move(llama_context*src,llama_model*model,llama_context_params cp,common_sampler_ptr&smpl,int pending,int idx){
    const char*ub=std::getenv("HS_TARGET_CONTINUATION_UB");if(!ub)return src;
    int dest=std::atoi(ub);if(dest!=1&&dest!=2)throw std::runtime_error("invalid continuation UB");
    auto before=state(src);auto pos=position(src);auto*logits=llama_get_logits_ith(src,idx);
    if(!logits)throw std::runtime_error("missing pending source logits");
    int nv=llama_vocab_n_tokens(llama_model_get_vocab(model));bytes(".pending_logits.f32",std::vector<float>(logits,logits+nv));
    auto chain=common_sampler_print(smpl.get()),history=common_sampler_prev_str(smpl.get(),src,4096);auto seed=common_sampler_get_seed(smpl.get());
    common_sampler_ptr clone(common_sampler_clone(smpl.get()));cp.n_ubatch=dest;
    auto*dst=llama_init_from_model(model,cp);if(!dst)throw std::runtime_error("continuation context allocation failed");roles[dst]="target";
    auto consumed=llama_state_set_data(dst,before.data(),before.size());auto restored=state(dst),after=state(src);
    bytes(".source_before.kv",before);bytes(".destination.kv",restored);bytes(".source_after.kv",after);
    j x={{"event","transfer"},{"source_ub",llama_n_ubatch(src)},{"destination_ub",llama_n_ubatch(dst)},{"state_bytes",before.size()},{"consumed_bytes",consumed},
      {"before",pos},{"after",position(dst)},{"source_after",position(src)},{"source_unchanged",before==after},{"state_equal",before==restored},{"pending_id",pending},{"pending_logits_index",idx},
      {"sampler_chain",chain},{"clone_chain",common_sampler_print(clone.get())},{"history",history},{"clone_history",common_sampler_prev_str(clone.get(),dst,4096)},
      {"seed",seed},{"clone_seed",common_sampler_get_seed(clone.get())},{"sampler_bytes","opaque; pinned clone, seed/history and behavioral sham controls"},
      {"pending_boundary","sample and accept exactly once in source; carry pending ID; no destination resample"}};
    emit(x);
    if(before!=after||before!=restored||consumed!=before.size()||pos!=position(dst)||chain!=common_sampler_print(clone.get())||
       history!=common_sampler_prev_str(clone.get(),dst,4096)||seed!=common_sampler_get_seed(clone.get()))throw std::runtime_error("state transfer qualification failed");
    // Retain the source sampler separately until context teardown.
    static std::vector<common_sampler_ptr> retained;retained.push_back(std::move(smpl));smpl=std::move(clone);return dst;
}
}
