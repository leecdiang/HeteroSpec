#pragma once
#include "common.h"
#include "sampling.h"
#include "llama.h"
#include "ggml.h"
#include "nlohmann/json.hpp"
#include <fstream>
#include <cstring>
#include <stdexcept>
using pj = nlohmann::ordered_json;
struct prefill_observer {
    pj trace=pj::array(), graphs=pj::array(), transfer=nullptr, commits=pj::array();
    std::string phase="initialization", role="target", path;
    bool instrument=true;
    int prefill_ub=1;
    int target_calls=0,draft_calls=0,target_tokens=0,draft_tokens=0;
    void reset(const pj &req){path=req.at("output");trace=pj::array();graphs=pj::array();commits=pj::array();transfer=nullptr;phase="initialization";role="target";target_calls=draft_calls=target_tokens=draft_tokens=0;}
    prefill_observer() {
        const char * p=std::getenv("HS_PREFILL_OUTPUT");
        if (!p) throw std::runtime_error("Missing output"); path=p;
        const char * ub=std::getenv("HS_PREFILL_UB"); if (ub) prefill_ub=std::atoi(ub);
        if ((prefill_ub<1 || prefill_ub>8) && prefill_ub!=128) throw std::runtime_error("Bad prefill UB");
        instrument=std::getenv("HS_TRACE_OFF")==nullptr;
    }
    static bool callback(ggml_tensor * t,bool ask,void * data) {
        auto * o=static_cast<prefill_observer *>(data);
        if (ask && o->instrument && (std::strcmp(t->name,"embd")==0 || std::strcmp(t->name,"result_output")==0))
            o->graphs.push_back({{"tensor",t->name},{"ne0",t->ne[0]},{"ne1",t->ne[1]},
              {"observation","scheduler graph tensor; embd ne1 is occupied forward tokens; no kernel identity"}});
        return false;
    }
    static pj positions(llama_context * ctx) {
        auto * m=llama_get_memory(ctx);
        return {{"sequence_id",0},{"min",llama_memory_seq_pos_min(m,0)},{"max",llama_memory_seq_pos_max(m,0)}};
    }
    void begin(llama_context * ctx,llama_batch b) {
        if(role=="target"){++target_calls;target_tokens+=b.n_tokens;}else{++draft_calls;draft_tokens+=b.n_tokens;}
        graphs=pj::array(); if (!instrument) return;
        pj ids=pj::array(),pos=pj::array(),seq=pj::array(),lg=pj::array();
        int start=llama_memory_seq_pos_max(llama_get_memory(ctx),0)+1;
        for (int i=0;i<b.n_tokens;i++) {
            ids.push_back(b.token[i]); pos.push_back(b.pos?b.pos[i]:start+i);
            pj s=pj::array(); if (b.seq_id) {for(int j=0;j<b.n_seq_id[i];j++) s.push_back(b.seq_id[i][j]);} else s.push_back(0);
            seq.push_back(s); lg.push_back(b.logits?bool(b.logits[i]):i==b.n_tokens-1);
        }
        trace.push_back({{"event","decode"},{"role",role},{"phase",phase},{"input_ids",ids},
            {"positions",pos},{"position_source",b.pos?"explicit batch":"runtime implicit sequential"},
            {"sequence_ids",seq},{"logits_requested",lg},{"caller_batch_length",b.n_tokens},
            {"ub_capacity",llama_n_ubatch(ctx)},{"before",positions(ctx)}});
    }
    void end(llama_context * ctx,int code) {
        if (instrument) {trace.back()["graphs"]=graphs;trace.back()["after"]=positions(ctx);trace.back()["exit_code"]=code;}
        if(instrument)llama_synchronize(ctx);
        if (code) throw std::runtime_error("Decode failure");
    }
    int decode(llama_context * ctx,llama_batch b,const char * r) {
        role=r; begin(ctx,b);int c=llama_decode(ctx,b);end(ctx,c);return c;
    }
    static std::vector<uint8_t> state(llama_context * c) {
        llama_synchronize(c);std::vector<uint8_t>b(llama_state_get_size(c));
        if(llama_state_get_data(c,b.data(),b.size())!=b.size())throw std::runtime_error("Short state");return b;
    }
    template<class T> void bytes(std::string suffix,const std::vector<T>&b) {
        if(!instrument)return;
        std::ofstream f(path+suffix,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size()*sizeof(T));
        if(!f)throw std::runtime_error("State write failed");
    }
    static pj top(llama_context * c,int idx) {
        const float * l=llama_get_logits_ith(c,idx); if(!l)throw std::runtime_error("Missing logits");
        if(std::getenv("HS_TRACE_OFF"))return pj::object();
        int n=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(c))),a=-1,b=-1;
        for(int i=0;i<n;i++){if(a<0||l[i]>l[a]){b=a;a=i;}else if(b<0||l[i]>l[b])b=i;}
        return {{"top1",a},{"top2",b},{"top1_score",l[a]},{"top2_score",l[b]}};
    }
    llama_context * move(llama_context * src,llama_model * model,llama_context_params cp,common_sampler * &sampler,int pending,int prompt_length) {
        auto before=state(src);auto p=positions(src);
        int nv=llama_vocab_n_tokens(llama_model_get_vocab(model));
        const float * l=llama_get_logits_ith(src,-1);std::vector<float> logits(l,l+nv);bytes(".pending_logits.f32",logits);
        auto * clone=common_sampler_clone(sampler);
        auto chain=common_sampler_print(sampler);auto history=common_sampler_prev_str(sampler,src,1024);auto seed=common_sampler_get_seed(sampler);
        auto * dst=llama_init_from_model(model,cp);if(!dst)throw std::runtime_error("Continuation context failed");
        size_t consumed=llama_state_set_data(dst,before.data(),before.size());
        auto restored=state(dst),after=state(src);
        bytes(".before.kv",before);bytes(".restored.kv",restored);bytes(".source_after.kv",after);
        transfer={{"before",p},{"after",positions(dst)},{"source_after",positions(src)},
          {"source_ub",llama_n_ubatch(src)},{"destination_ub",llama_n_ubatch(dst)},
          {"state_bytes",before.size()},{"consumed_bytes",consumed},{"kv_equal",before==restored},
          {"source_unchanged",before==after},{"pending_id",pending},{"pending_eog",llama_vocab_is_eog(llama_model_get_vocab(model),pending)},
          {"pending_logits_method","sample once in prefill context; carry pending ID and cloned post-sample sampler; never sample missing restored logits"},
          {"sampler_chain",chain},{"clone_chain",common_sampler_print(clone)},
          {"sampler_history",history},{"clone_history",common_sampler_prev_str(clone,dst,1024)},
          {"seed",seed},{"clone_seed",common_sampler_get_seed(clone)},
          {"opaque_sampler_bytes","unavailable; pinned clone and behavioral sham equivalence"},
          {"sequence_ownership","single sequence 0; serialized ownership and min/max checked"}};
        if(before!=restored||before!=after||consumed!=before.size()||p!=positions(dst)||
            p["min"]!=0||p["max"]!=prompt_length-1||chain!=common_sampler_print(clone)||
            history!=common_sampler_prev_str(clone,dst,1024)||seed!=common_sampler_get_seed(clone))throw std::runtime_error("Transfer gate failed");
        // The target harness source sampler is owned by common_init_result.
        // Keep it alive with its source context; the continuation uses the clone.
        sampler=clone;return dst;
    }
    void commit(llama_context * c,int id,bool eog,bool accepted,int proposal,int idx,const pj & scores) {
        if(instrument) commits.push_back({{"index",commits.size()},{"id",id},{"eog",eog},{"accepted",accepted},
          {"proposal",proposal},{"logits_index",idx},{"relationship",accepted?"accept":proposal>=0?"correct":"sample_or_bonus"},
          {"scores",scores},{"kv",positions(c)}});
    }
    void mutation(const char * operation,llama_memory_t memory,int s,int t,int p0,int p1) {
        if(instrument)trace.push_back({{"event","kv_mutation"},{"operation",operation},{"sequence",s},{"destination_sequence",t},{"p0",p0},{"p1",p1},
          {"role",role},{"phase",phase},{"min_before",llama_memory_seq_pos_min(memory,0)},{"max_before",llama_memory_seq_pos_max(memory,0)}});
    }
    void finish(const std::vector<int>&ids,const std::vector<bool>&eog,const std::vector<llama_token>&prompt) {
        pj j={{"schema","heterospec.b570.prefill.capture.v1"},{"prompt_ids",prompt},{"ids",ids},{"eog",eog},
            {"prefill_ub",prefill_ub},{"work",{{"target_calls",target_calls},{"draft_calls",draft_calls},{"target_caller_tokens",target_tokens},{"draft_caller_tokens",draft_tokens}}},{"trace",trace},{"commits",commits},{"transfer",transfer}};
        std::ofstream f(path,std::ios::binary);f<<j.dump(2)<<"\n";if(!f)throw std::runtime_error("Capture failed");
    }
};
