"""Derive an auditable frontend from the read-only pinned speculative example."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/hs/b570-direct-id-v1-src/examples/speculative/speculative.cpp')

def replace(text, old, new):
    assert text.count(old) == 1, (old[:80], text.count(old))
    return text.replace(old, new)

def main():
    src = SOURCE.read_text(encoding='utf-8')
    src = replace(src, '#include "heterospec-direct-id.h"', '#include "heterospec-direct-id.h"\n#include "observer.h"')
    src = replace(src, '    // max number of parallel drafting sequences', '''    if (params.n_parallel != 1 || params.n_ctx != 1024 || params.n_batch != 512 ||
        params.n_ubatch != 1 || params.sampling.temp != 0 || params.sampling.seed != 123 ||
        params.speculative.draft.n_max != 2 || params.n_predict != 127) return 80;
    hs_observer observer;
    params.cb_eval = hs_observer::graph_callback;
    params.cb_eval_user_data = &observer;
    const auto hs_target_params = common_context_params_to_llama(params);
    // max number of parallel drafting sequences''')
    # Save context parameters after upstream applies its output limits.
    src = replace(src, '    // load the target model\n', '    auto hs_target_cp = common_context_params_to_llama(params);\n    // load the target model\n')
    src = replace(src, '    heterospec_direct_ids hs_direct_ids;\n    while (true) {', '''    heterospec_direct_ids hs_direct_ids;
    llama_context * hs_alt = nullptr;
    std::vector<uint8_t> hs_draft_state;
    std::vector<seq_draft> hs_fork_drafts;
    common_sampler * hs_fork_sampler = nullptr;
    int hs_fork_predict = 0, hs_fork_past_tgt = 0, hs_fork_past_dft = 0;
    int hs_fork_drafted = 0, hs_fork_accept = 0;
    heterospec_direct_ids hs_fork_ids;
    bool hs_secondary = false;
    auto hs_generate = [&]() -> int {
    while (true) {''')
    src = replace(src, '                hs_direct_ids.commit(token_id, llama_vocab_is_eog(vocab_tgt, token_id));', '''                observer.commit(ctx_tgt, smpl, token_id, accept,
                    drafts[s_keep].i_batch_tgt[i_dft], n_predict,
                    i_dft < (int) drafts[s_keep].tokens.size() ? drafts[s_keep].tokens[i_dft] : -1,
                    llama_vocab_is_eog(vocab_tgt, token_id), hs_secondary);
                hs_direct_ids.commit(token_id, llama_vocab_is_eog(vocab_tgt, token_id));''')
    src = replace(src, '            llama_decode(ctx_tgt, batch_tgt);\n            ++n_past_tgt;', '''            observer.tape(batch_tgt, drafts[0].tokens, hs_direct_ids.ids, n_past_tgt, hs_secondary);
            if (!hs_secondary && !observer.forked && n_predict >= 64 && observer.mode != "baseline") {
                hs_fork_predict = n_predict;
                hs_fork_past_tgt = n_past_tgt;
                hs_fork_past_dft = n_past_dft;
                hs_fork_drafted = n_drafted;
                hs_fork_accept = n_accept;
                hs_fork_ids = hs_direct_ids;
                hs_fork_sampler = common_sampler_clone(smpl);
                hs_fork_drafts = drafts;
                for (auto & d : hs_fork_drafts) d.smpl = common_sampler_clone(d.smpl);
                hs_draft_state = hs_observer::state(ctx_dft);
                auto alt_cp = hs_target_cp;
                alt_cp.n_ubatch = observer.mode == "control" ? 1 : 128;
                hs_alt = llama_init_from_model(model_tgt, alt_cp);
                if (!hs_alt) { observer.fail("alternate context creation failed"); return 81; }
                if (!observer.restore(ctx_tgt, hs_alt, smpl, hs_fork_sampler, hs_fork_predict, n_past_tgt, inp, hs_direct_ids.ids)) return 82;
                observer.active_graphs.clear();
                if (llama_decode(hs_alt, batch_tgt) != 0) { observer.fail("alternate target decode failed"); return 83; }
                llama_synchronize(hs_alt);
                observer.alt_graphs = observer.active_graphs;
                observer.alt_scores = observer.scores(hs_alt, batch_tgt, drafts[0].tokens);
                observer.forked = true;
            }
            observer.active_graphs.clear();
            if (llama_decode(ctx_tgt, batch_tgt) != 0) { observer.fail("native target decode failed"); return 84; }
            llama_synchronize(ctx_tgt);
            observer.block_graphs = observer.active_graphs;
            if (!hs_secondary && observer.forked && observer.primary_scores.is_null()) {
                observer.primary_scores = observer.scores(ctx_tgt, batch_tgt, drafts[0].tokens);
                observer.primary_graphs = observer.block_graphs;
            }
            ++n_past_tgt;''')
    src = replace(src, '    auto t_dec_end = ggml_time_us();', '''    return 0;
    };
    int hs_rc = hs_generate();
    observer.primary_ids = hs_direct_ids.ids;
    observer.primary_eog = hs_direct_ids.eog;
    if (hs_rc == 0 && observer.forked) {
        if (llama_state_set_data(ctx_dft, hs_draft_state.data(), hs_draft_state.size()) != hs_draft_state.size() ||
            hs_observer::state(ctx_dft) != hs_draft_state) {
            observer.fail("draft continuation checkpoint mismatch"); hs_rc = 85;
        } else {
            for (auto & d : drafts) common_sampler_free(d.smpl);
            common_sampler_free(smpl);
            drafts = std::move(hs_fork_drafts);
            smpl = hs_fork_sampler;
            ctx_tgt = hs_alt;
            mem_tgt = llama_get_memory(ctx_tgt);
            n_predict = hs_fork_predict;
            n_past_tgt = hs_fork_past_tgt + 1;
            n_past_dft = hs_fork_past_dft;
            n_drafted = hs_fork_drafted;
            n_accept = hs_fork_accept;
            has_eos = false;
            hs_direct_ids = hs_fork_ids;
            for (auto & d : drafts) {
                if (d.active) {
                    d.tokens.erase(d.tokens.begin());
                    d.dists.erase(d.dists.begin());
                }
            }
            hs_secondary = true;
            observer.secondary_first_block = true;
            observer.block_graphs = observer.alt_graphs;
            hs_rc = hs_generate();
            observer.alt_ids = hs_direct_ids.ids;
            observer.alt_eog = hs_direct_ids.eog;
        }
    }
    observer.finish(inp, hs_rc);
    if (hs_rc != 0) return hs_rc;
    auto t_dec_end = ggml_time_us();''')
    # Original sidecar remains the primary stream, even after the alternate continuation.
    src = replace(src, '    if (!hs_direct_ids.write())', '    hs_direct_ids.ids = observer.primary_ids;\n    hs_direct_ids.eog = observer.primary_eog;\n    if (!hs_direct_ids.write())')
    (ROOT/'generated_speculative.cpp').write_text(src,encoding='utf-8',newline='\n')

if __name__ == '__main__': main()
