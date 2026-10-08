#pragma once
#include "common.h"
#include "sampling.h"
#include "llama.h"
#include "nlohmann/json.hpp"
#include <map>
#include <fstream>
#include <filesystem>
using psj=nlohmann::ordered_json;
// Instrument actual accept/clone history. No reference, task, or future input.
inline std::map<common_sampler*,psj> pilot_hist;
inline common_sampler * pilot_init(llama_model *m,common_params_sampling &p) {
 auto *s=common_sampler_init(m,p);pilot_hist[s]=psj::array();return s;
}
inline void pilot_accept(common_sampler*s,llama_token id,bool generated){common_sampler_accept(s,id,generated);pilot_hist[s].push_back({id,generated});}
inline common_sampler * pilot_clone(common_sampler*s){auto*c=common_sampler_clone(s);pilot_hist[c]=pilot_hist[s];return c;}
inline void pilot_free(common_sampler*s){pilot_hist.erase(s);common_sampler_free(s);}
inline psj pilot_sampler(common_sampler*s,llama_context*c){
 auto *clone=pilot_clone(s);
 psj x={{"accepted_history",pilot_hist[s]},{"chain",common_sampler_print(s)},{"history_string",common_sampler_prev_str(s,c,1024)},{"seed",common_sampler_get_seed(s)},
 {"clone_chain",common_sampler_print(clone)},{"clone_history",common_sampler_prev_str(clone,c,1024)},{"clone_seed",common_sampler_get_seed(clone)},
 {"opaque_bytes","unavailable in published common sampler API"},
 {"restore_scope","accepted history replay into same effective greedy chain then real clone; RNG cursor not serialized; greedy singleton selection, empty grammar and unlimited reasoning only; full trajectory shams required"}};
 pilot_free(clone);return x;
}
inline common_sampler * pilot_restore_sampler(llama_model*m,llama_context*c,common_params_sampling&p,const psj&x){
 if(p.temp!=0 || !p.grammar.empty() || p.grammar_lazy || p.reasoning_control || p.reasoning_budget_tokens>=0 || p.backend_sampling || p.mirostat!=0 || p.penalty_repeat!=1 || p.penalty_freq!=0 || p.penalty_present!=0 || p.dry_multiplier!=0)throw std::runtime_error("Unsupported effective sampler restore");
 auto*s=pilot_init(m,p);for(auto&a:x.at("accepted_history"))pilot_accept(s,a.at(0).get<int>(),a.at(1).get<bool>());
 auto*clone=pilot_clone(s);pilot_free(s);auto y=pilot_sampler(clone,c);
 if(y.at("chain")!=x.at("chain")||y.at("history_string")!=x.at("history_string")||y.at("seed")!=x.at("seed"))throw std::runtime_error("Sampler restore metadata mismatch");return clone;
}
inline std::vector<uint8_t> pilot_read(const std::string&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Missing payload "+p);return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
template<class T> inline void pilot_write(const std::string&p,const std::vector<T>&v){std::ofstream f(p,std::ios::binary);f.write((const char*)v.data(),v.size()*sizeof(T));if(!f)throw std::runtime_error("Payload write "+p);}
inline void pilot_json(const std::string&p,const psj&j){std::ofstream f(p,std::ios::binary);f<<j.dump(2)<<"\n";if(!f)throw std::runtime_error("Metadata write "+p);}
inline psj pilot_load(const std::string&p){std::ifstream f(p);psj j;f>>j;return j;}
inline psj pilot_batch(llama_batch b){psj rows=psj::array();for(int i=0;i<b.n_tokens;i++){std::vector<int>s(b.seq_id[i],b.seq_id[i]+b.n_seq_id[i]);rows.push_back({{"id",b.token[i]},{"pos",b.pos[i]},{"seq",s},{"logits",bool(b.logits[i])}});}return rows;}
inline void pilot_restore_batch(llama_batch &b,const psj&rows){common_batch_clear(b);for(auto&r:rows)common_batch_add(b,r.at("id").get<int>(),r.at("pos").get<int>(),r.at("seq").get<std::vector<int>>(),r.at("logits").get<bool>());}
