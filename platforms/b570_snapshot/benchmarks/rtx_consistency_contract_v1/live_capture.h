#pragma once
#include "hs_observer.h"
#include <filesystem>

namespace hs_live {
inline bool enabled() { return std::getenv("HS_LIVE_CAPTURE") != nullptr; }
inline void require(bool ok, const char * s) { if (!ok) throw std::runtime_error(s); }
inline void write(const std::string & p, const void * data, size_t n) {
    std::ofstream f(p, std::ios::binary); f.write(static_cast<const char *>(data), n);
    f.flush(); require(bool(f), "live witness write failed");
}
inline std::vector<float> logits(llama_context * c, int nv, int idx) {
    auto * p = llama_get_logits_ith(c, idx); require(p != nullptr, "live logits missing");
    return {p, p + nv};
}
inline hs::j sampler_contract(common_sampler * s, llama_context * c) {
    return {{"chain", common_sampler_print(s)}, {"seed", common_sampler_get_seed(s)},
            {"history", common_sampler_prev_str(s, c, 4096)}};
}
inline bool float_equal(const std::vector<float> & a, const std::vector<float> & b) {
    return a.size() == b.size() && std::memcmp(a.data(), b.data(), a.size() * sizeof(float)) == 0;
}
inline hs::j checkpoint(llama_context * source, llama_model * model, llama_context_params cp,
        common_sampler * smpl, llama_batch input, const llama_tokens & committed,
        const llama_tokens & retained_prefix) {
    hs::j out;
    if (!enabled() || committed.size() != static_cast<size_t>(std::atoi(std::getenv("HS_LIVE_CUT")))) return out;
    const std::string dir = std::getenv("HS_LIVE_CAPTURE");
    std::filesystem::create_directories(dir);
    require(!std::filesystem::exists(dir + "/checkpoint.json"), "duplicate live boundary");
    const auto saved = hs::state(source);
    const auto bounds = hs::position(source);
    const int nv = llama_vocab_n_tokens(llama_model_get_vocab(model));
    const auto pending_logits = logits(source, nv, -1);
    const auto sc = sampler_contract(smpl, source);
    common_sampler_ptr clone(common_sampler_clone(smpl));
    require(sc == sampler_contract(clone.get(), source), "live sampler clone contract differs");
    require(input.n_tokens > 0 && input.token[0] == committed.back(), "live pending contract differs");
    require(bounds["max"].get<int>() == input.pos[0] - 1, "live suffix was not removed");
    hs::j ids = hs::j::array(), pos = hs::j::array(), seq = hs::j::array(), mask = hs::j::array();
    for (int i = 0; i < input.n_tokens; ++i) {
        require(input.n_seq_id[i] == 1 && input.seq_id[i][0] == 0, "live sequence contract differs");
        ids.push_back(input.token[i]); pos.push_back(input.pos[i]);
        seq.push_back({input.seq_id[i][0]}); mask.push_back(bool(input.logits[i]));
    }
    write(dir + "/donor.state", saved.data(), saved.size());
    write(dir + "/unused_previous_logits.f32", pending_logits.data(), pending_logits.size() * sizeof(float));
    out = {{"committed_ids", committed}, {"retained_prefix", retained_prefix}, {"tokens", ids},
           {"positions", pos}, {"sequence_ids", seq}, {"logits_mask", mask}, {"bounds", bounds},
           {"sampler", sc}, {"source_ub", llama_n_ubatch(source)}, {"state_bytes", saved.size()},
           {"previous_logits_consumed_by_call", false}, {"forks", hs::j::array()}};
    if (std::getenv("HS_LIVE_SHAM")) {
        require(llama_state_set_data(source, saved.data(), saved.size()) == saved.size(), "source sham restore failed");
    }
    require(saved == hs::state(source) && bounds == hs::position(source) &&
            float_equal(pending_logits, logits(source, nv, -1)), "live capture changed source");
    out["source_capture_unchanged"] = true;
    if (std::getenv("HS_LIVE_FORK")) {
        const std::string previous_phase = hs::phase;
        hs::phase = "live_fork";
        for (int ub : {2, 1}) {
            auto fp = cp; fp.n_ubatch = ub; fp.cb_eval_user_data = (void *) "live_fork";
            llama_context_ptr ctx(llama_init_from_model(model, fp));
            require(bool(ctx), "live fork context allocation failed");
            hs::roles[ctx.get()] = "live_fork";
            require(llama_state_set_data(ctx.get(), saved.data(), saved.size()) == saved.size(), "live fork restore failed");
            require(saved == hs::state(ctx.get()) && bounds == hs::position(ctx.get()), "live fork roundtrip differs");
            common_sampler_ptr fs(common_sampler_clone(smpl));
            require(sc == sampler_contract(fs.get(), ctx.get()), "live fork sampler contract differs");
            hs::graphs = hs::j::array();
            require(llama_decode(ctx.get(), input) == 0, "live fork decode failed");
            llama_synchronize(ctx.get());
            const auto graphs = hs::graphs;
            std::vector<int> idxs; llama_tokens proposals;
            for (int i = 0; i < input.n_tokens; ++i) {
                idxs.push_back(i); if (i > 0) proposals.push_back(input.token[i]);
                auto row = logits(ctx.get(), nv, i);
                write(dir + "/ub" + std::to_string(ub) + "_row" + std::to_string(i) + ".f32", row.data(), row.size() * sizeof(float));
            }
            const auto accepted = common_sampler_sample_and_accept_n(fs.get(), ctx.get(), idxs, proposals);
            const int nextpos = input.pos[0] + accepted.size();
            require(llama_memory_seq_rm(llama_get_memory(ctx.get()), 0, nextpos, -1), "live fork rollback failed");
            hs::j fork = {{"ub", ub}, {"roundtrip_equal", true}, {"graphs", graphs},
                          {"sampled_ids", accepted}, {"reached_logits_rows", accepted.size()},
                          {"accepted_proposals", accepted.size() - 1}, {"next_position", nextpos}};
            auto cont_state = hs::state(ctx.get());
            auto ccp = cp; ccp.n_ubatch = 1; ccp.cb_eval_user_data = (void *) "live_continuation";
            llama_context_ptr cont(llama_init_from_model(model, ccp));
            require(bool(cont), "live continuation allocation failed");
            hs::roles[cont.get()] = "live_continuation";
            common_sampler_ptr cs(common_sampler_clone(fs.get()));
            require(llama_state_set_data(cont.get(), cont_state.data(), cont_state.size()) == cont_state.size() &&
                    cont_state == hs::state(cont.get()) && hs::position(ctx.get()) == hs::position(cont.get()) &&
                    sampler_contract(fs.get(), ctx.get()) == sampler_contract(cs.get(), cont.get()), "live continuation roundtrip differs");
            fork["continuation_roundtrip_equal"] = true;
            fork["old_logits_restoration"] = "state API omits logits; next decode does not consume old logits";
            ctx.reset();
            llama_tokens auxiliary;
            bool stopped = false;
            for (int id : accepted) if (llama_vocab_is_eog(llama_model_get_vocab(model), id)) stopped = true;
            int pending = accepted.back();
            for (int i = 0; i < 32 && !stopped && committed.size() + accepted.size() + auxiliary.size() < 128; ++i) {
                auto b = llama_batch_init(1, 0, 1); b.n_tokens = 1;
                b.token[0] = pending; b.pos[0] = nextpos + i; b.n_seq_id[0] = 1; b.seq_id[0][0] = 0; b.logits[0] = true;
                const int rc = llama_decode(cont.get(), b); llama_batch_free(b);
                require(rc == 0, "live continuation decode failed"); llama_synchronize(cont.get());
                pending = common_sampler_sample(cs.get(), cont.get(), 0);
                common_sampler_accept(cs.get(), pending, true); auxiliary.push_back(pending);
                stopped = llama_vocab_is_eog(llama_model_get_vocab(model), pending);
            }
            fork["auxiliary_ids"] = auxiliary; fork["auxiliary_eog"] = stopped;
            out["forks"].push_back(fork);
        }
        hs::phase = previous_phase;
        require(saved == hs::state(source) && bounds == hs::position(source) &&
                float_equal(pending_logits, logits(source, nv, -1)) && sc == sampler_contract(smpl, source), "live forks changed source");
        out["source_after_forks_unchanged"] = true;
    }
    const auto serialized = out.dump(2) + "\n";
    write(dir + "/checkpoint.json", serialized.data(), serialized.size());
    hs::emit({{"event", "live_checkpoint"}, {"committed_count", committed.size()}, {"tokens", ids}, {"positions", pos}});
    return out;
}
}
