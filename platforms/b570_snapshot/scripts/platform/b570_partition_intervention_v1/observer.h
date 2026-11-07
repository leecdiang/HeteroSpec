#pragma once
#include "nlohmann/json.hpp"
#include "ggml.h"
#include <fstream>
#include <stdexcept>
#include <cstring>
using hs_json = nlohmann::ordered_json;

struct hs_observer {
    std::string path, mode;
    bool forked = false, secondary_first_block = false;
    hs_json tapes = hs_json::array(), secondary_tapes = hs_json::array();
    hs_json decisions = hs_json::array(), secondary_decisions = hs_json::array();
    hs_json checkpoint, primary_scores, alt_scores;
    hs_json active_graphs = hs_json::array(), block_graphs, primary_graphs, alt_graphs;
    std::vector<int> primary_ids, alt_ids;
    std::vector<bool> primary_eog, alt_eog;
    std::string failure;
    hs_observer() {
        const char * p = std::getenv("HS_PARTITION_OUTPUT");
        const char * m = std::getenv("HS_PARTITION_MODE");
        if (!p || !m) throw std::runtime_error("Missing study output/mode");
        path = p; mode = m;
        if (mode != "baseline" && mode != "control" && mode != "intervention") throw std::runtime_error("Invalid mode");
    }
    static bool graph_callback(ggml_tensor * tensor, bool ask, void * data) {
        auto * o = static_cast<hs_observer *>(data);
        if (ask && std::strcmp(tensor->name, "result_output") == 0)
            o->active_graphs.push_back({{"tensor",tensor->name},{"vocab",tensor->ne[0]},{"output_tokens",tensor->ne[1]}});
        return false; // observe graph query without tensor copying or splitting
    }
    static std::vector<uint8_t> state(llama_context * ctx) {
        llama_synchronize(ctx);
        std::vector<uint8_t> b(llama_state_get_size(ctx));
        const size_t n = llama_state_get_data(ctx,b.data(),b.size());
        if (n != b.size()) throw std::runtime_error("Short state serialization");
        return b;
    }
    void bytes(const std::string & suffix, const std::vector<uint8_t> & b) {
        std::ofstream out(path + suffix, std::ios::binary);
        out.write(reinterpret_cast<const char *>(b.data()), b.size());
        if (!out) throw std::runtime_error("Checkpoint write failed");
    }
    void fail(const std::string & why) {
        failure = why;
        finish({}, 90);
    }
    bool restore(llama_context * src, llama_context * dst, common_sampler * sampler,
                 common_sampler * clone, int output_index, int position,
                 const std::vector<llama_token> & prompt, const std::vector<int> & committed) {
        const auto a = state(src);
        bytes(".before.kv",a);
        const size_t consumed = llama_state_set_data(dst,a.data(),a.size());
        const auto b = state(dst);
        bytes(".restored.kv",b);
        const auto after = state(src);
        bytes(".source_after.kv",after);
        checkpoint = {{"output_index",output_index},{"position",position},{"prompt_ids",prompt},
            {"committed_ids",committed},{"source_ubatch",llama_n_ubatch(src)},
            {"alternate_ubatch",llama_n_ubatch(dst)},{"n_batch",llama_n_batch(dst)},
            {"state_bytes",a.size()},{"consumed_bytes",consumed},
            {"serialized_kv_equal",a == b},{"source_unchanged",a == after},
            {"source_min_position",llama_memory_seq_pos_min(llama_get_memory(src),0)},
            {"source_max_position",llama_memory_seq_pos_max(llama_get_memory(src),0)},
            {"alternate_min_position",llama_memory_seq_pos_min(llama_get_memory(dst),0)},
            {"alternate_max_position",llama_memory_seq_pos_max(llama_get_memory(dst),0)},
            {"sampler_chain",common_sampler_print(sampler)},
            {"clone_chain",common_sampler_print(clone)},
            {"sampler_seed",common_sampler_get_seed(sampler)},
            {"clone_seed",common_sampler_get_seed(clone)},
            {"sampler_history",common_sampler_prev_str(sampler,src,1024)},
            {"clone_history",common_sampler_prev_str(clone,dst,1024)},
            {"sampler_state_method","pinned common_sampler_clone copies params, grammar, reasoning budget, chain and accepted-token ring; same-partition R0 checks decisions"}};
        if (a != b || a != after || consumed != a.size() || checkpoint["sampler_chain"] != checkpoint["clone_chain"] ||
            checkpoint["sampler_history"] != checkpoint["clone_history"] || checkpoint["sampler_seed"] != checkpoint["clone_seed"]) {
            fail("same-state restoration qualification failed"); return false;
        }
        return true;
    }
    static hs_json top(llama_context * ctx, int idx, int proposal) {
        const float * l = llama_get_logits_ith(ctx,idx);
        const int nv = llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(ctx)));
        int a=-1,b=-1;
        for (int i=0;i<nv;++i) {
            if (a<0 || l[i]>l[a]) {b=a;a=i;}
            else if (b<0 || l[i]>l[b]) b=i;
        }
        hs_json r={{"raw_top1_id",a},{"raw_top2_id",b},{"top1_score",l[a]},
            {"top2_score",l[b]},{"margin",l[a]-l[b]},{"proposal_id",proposal}};
        r["proposal_score"] = proposal >= 0 ? hs_json(l[proposal]) : hs_json(nullptr);
        return r;
    }
    hs_json scores(llama_context * ctx, const llama_batch & batch, const std::vector<llama_token> & tape) {
        hs_json r=hs_json::array();
        for (int i=0;i<batch.n_tokens;++i) {
            r.push_back(top(ctx,i,i+1<(int)tape.size()?tape[i+1]:-1));
        }
        return r;
    }
    void tape(const llama_batch & batch, const std::vector<llama_token> & ids,
              const std::vector<int> & committed, int position, bool secondary) {
        hs_json row={{"output_index",committed.size()},{"position",position},
            {"committed_prefix",committed},{"batch_ids",std::vector<llama_token>(batch.token,batch.token+batch.n_tokens)},
            {"batch_positions",std::vector<llama_pos>(batch.pos,batch.pos+batch.n_tokens)},
            {"proposal_tape",std::vector<llama_token>(ids.begin()+1,ids.end())},
            {"fixed_before_target_decode",true}};
        (secondary?secondary_tapes:tapes).push_back(row);
        if (secondary) secondary_first_block=false;
    }
    void commit(llama_context * ctx, common_sampler *, int id, bool accepted,
                int batch_idx, int output_idx, int proposal, bool eog, bool secondary) {
        hs_json r=top(ctx,batch_idx,proposal);
        r["output_index"]=output_idx;r["batch_index"]=batch_idx;
        r["committed_id"]=id;r["accepted_proposal"]=accepted;r["eog"]=eog;
        r["n_batch"]=llama_n_batch(ctx);r["n_ubatch"]=llama_n_ubatch(ctx);
        r["fork_first_block"]=secondary && secondary_first_block;
        (secondary?secondary_decisions:decisions).push_back(r);
    }
    void finish(const std::vector<llama_token> & prompt, int rc) {
        hs_json r={{"schema","heterospec.b570.live_partition.v1"},{"mode",mode},
            {"exit_code",rc},{"failure",failure},{"forked",forked},{"prompt_ids",prompt},
            {"checkpoint",checkpoint},{"proposal_events",tapes},{"alternate_proposal_events",secondary_tapes},
            {"decisions",decisions},{"alternate_decisions",secondary_decisions},
            {"primary_scores",primary_scores},{"alternate_scores",alt_scores},
            {"primary_physical_graphs",primary_graphs},{"alternate_physical_graphs",alt_graphs},
            {"primary_ids",primary_ids},{"primary_eog",primary_eog},{"alternate_ids",alt_ids},{"alternate_eog",alt_eog}};
        std::ofstream out(path,std::ios::binary); out<<r.dump(2)<<"\n";
        if (!out) throw std::runtime_error("Capture write failed");
    }
};
