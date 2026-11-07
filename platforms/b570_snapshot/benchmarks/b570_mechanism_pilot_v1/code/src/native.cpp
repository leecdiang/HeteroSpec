#include "arg.h"
#include "common.h"
#include "sampling.h"
#include "speculative.h"
#include "log.h"
#include "llama.h"
#include "heterospec-direct-id.h"
#include "pilot_state.h"
#include "observer.h"

#include <algorithm>
#include <clocale>
#include <cstdio>
#include <cstring>
#include <random>
#include <set>
#include <string>
#include <vector>
#include <iostream>

#define SPEC_VOCAB_MAX_SIZE_DIFFERENCE  128
#define SPEC_VOCAB_CHECK_START_TOKEN_ID 5

struct seq_draft {
    bool active   = false;
    bool drafting = false;
    bool skip     = false;

    int i_batch_dft = 0;
    std::vector<int> i_batch_tgt;

    std::vector<llama_token> tokens;
    std::vector<std::vector<llama_token_data>> dists;

    struct common_sampler * smpl = nullptr;
};

int main(int argc, char ** argv) {
    std::setlocale(LC_NUMERIC, "C");

    common_params params;

    // needed to get candidate probs even for temp <= 0.0
    params.sampling.n_probs = 128;

    common_init();

    if (!common_params_parse(argc, argv, params, LLAMA_EXAMPLE_SPECULATIVE)) {
        return 1;
    }

    if (params.n_predict < -1) {
        LOG_ERR("%s: --n-predict must be >= -1\n", __func__);
        return 1;
    }

    if (params.speculative.draft.mparams.path.empty()) {
        LOG_ERR("%s: --model-draft is required\n", __func__);
        return 1;
    }

    if(params.n_parallel!=1||params.n_ctx!=1024||params.n_batch!=512||params.n_ubatch<1||params.n_ubatch>8||params.sampling.temp!=0||params.sampling.seed!=123||params.speculative.draft.n_max<1||params.speculative.draft.n_max>7||params.n_predict<127||params.n_predict>511) return 80;
    prefill_observer observer;
    if(observer.instrument){params.cb_eval=prefill_observer::callback;params.cb_eval_user_data=&observer;}
    params.warmup=false; // Explicit session warm request; speculative CLI lacks --no-warmup.
    // max number of parallel drafting sequences (i.e. tree branches)
    const int n_seq_dft = params.n_parallel;

    const auto output_limits = common_speculative_get_output_limits(
            params.n_batch, params.n_parallel, params.speculative.draft.n_max);
    params.n_outputs_max = output_limits.total;
    params.n_outputs_max_per_seq = output_limits.per_seq;

    // probability threshold for splitting a draft branch (only for n_seq_dft > 1)
    const float p_draft_split = params.speculative.draft.p_split;

    std::default_random_engine rng(params.sampling.seed == LLAMA_DEFAULT_SEED ? std::random_device()() : params.sampling.seed);
    std::uniform_real_distribution<> u_dist;

    common_log_set_verbosity_thold(4);
    // init llama.cpp
    llama_backend_init();
    llama_numa_init(params.numa);

    llama_model * model_tgt = NULL;
    llama_model * model_dft = NULL;

    llama_context * ctx_tgt = NULL;
    llama_context * ctx_dft = NULL;

    // load the target model
    const auto continuation_cp=common_context_params_to_llama(params);
    auto target_prefill_params=params;target_prefill_params.n_ubatch=observer.prefill_ub;
    auto llama_init_tgt = common_init_from_params(target_prefill_params);

    model_tgt = llama_init_tgt->model();
    ctx_tgt   = llama_init_tgt->context();

    // load the draft model
    params.n_ubatch=1;
    params.devices = params.speculative.draft.devices;
    params.model = params.speculative.draft.mparams;
    params.n_gpu_layers = params.speculative.draft.n_gpu_layers;
    params.n_outputs_max = params.n_parallel;
    params.n_outputs_max_per_seq = 1;
    if (params.speculative.draft.cpuparams.n_threads > 0) {
        params.cpuparams.n_threads = params.speculative.draft.cpuparams.n_threads;
    }

    params.cpuparams_batch.n_threads = params.speculative.draft.cpuparams_batch.n_threads;
    params.tensor_buft_overrides     = params.speculative.draft.tensor_buft_overrides;

    auto llama_init_dft = common_init_from_params(params);

    model_dft = llama_init_dft->model();
    ctx_dft   = llama_init_dft->context();

    const llama_vocab * vocab_tgt = llama_model_get_vocab(model_tgt);
    const llama_vocab * vocab_dft = llama_model_get_vocab(model_dft);

    const bool vocab_type_tgt = llama_vocab_type(vocab_tgt);
    LOG_DBG("vocab_type tgt: %d\n", vocab_type_tgt);

    const bool vocab_type_dft = llama_vocab_type(vocab_dft);
    LOG_DBG("vocab_type dft: %d\n", vocab_type_dft);

    if (vocab_type_tgt != vocab_type_dft) {
        LOG_ERR("%s: draft model vocab type must match target model to use speculation but ", __func__);
        LOG_ERR("vocab_type_dft = %d while vocab_type_tgt = %d\n", vocab_type_dft, vocab_type_tgt);
        return 1;
    }

    if (llama_vocab_get_add_bos(vocab_tgt) != llama_vocab_get_add_bos(vocab_dft) ||
        (llama_vocab_get_add_bos(vocab_tgt) && llama_vocab_bos(vocab_tgt) != llama_vocab_bos(vocab_dft))) {
        LOG_ERR("%s: draft model bos tokens must match target model to use speculation. add: %d - %d, id: %d - %d)\n",
                __func__,
                llama_vocab_get_add_bos(vocab_tgt), llama_vocab_get_add_bos(vocab_dft),
                llama_vocab_bos(vocab_tgt), llama_vocab_bos(vocab_dft));
        return 1;
    }

    if (llama_vocab_get_add_eos(vocab_tgt) != llama_vocab_get_add_eos(vocab_dft) ||
        (llama_vocab_get_add_eos(vocab_tgt) && llama_vocab_eos(vocab_tgt) != llama_vocab_eos(vocab_dft))) {
        LOG_ERR("%s: draft model eos tokens must match target model to use speculation. add: %d - %d, id: %d - %d)\n",
                __func__,
                llama_vocab_get_add_eos(vocab_tgt), llama_vocab_get_add_eos(vocab_dft),
                llama_vocab_eos(vocab_tgt), llama_vocab_eos(vocab_dft));
        return 1;
    }

    {
        const int n_vocab_tgt = llama_vocab_n_tokens(vocab_tgt);
        const int n_vocab_dft = llama_vocab_n_tokens(vocab_dft);
        const int vocab_diff  = n_vocab_tgt > n_vocab_dft
            ? n_vocab_tgt - n_vocab_dft
            : n_vocab_dft - n_vocab_tgt;

        if (vocab_diff > SPEC_VOCAB_MAX_SIZE_DIFFERENCE) {
            LOG_ERR("%s: draft model vocab must closely match target model to use speculation but ", __func__);
            LOG_ERR("target vocab size %d does not match draft vocab size %d - difference %d, max allowed %d\n",
                    n_vocab_tgt, llama_vocab_n_tokens(vocab_dft), vocab_diff, SPEC_VOCAB_MAX_SIZE_DIFFERENCE);
            return 1;
        }

        for (int i = SPEC_VOCAB_CHECK_START_TOKEN_ID; i < std::min(n_vocab_tgt, n_vocab_dft); ++i) {
            const char * token_text_tgt = llama_vocab_get_text(vocab_tgt, i);
            const char * token_text_dft = llama_vocab_get_text(vocab_dft, i);

            if (std::strcmp(token_text_tgt, token_text_dft) != 0) {
                LOG_ERR("%s: draft model vocab must match target model to use speculation but ", __func__);
                LOG_ERR("token %d content differs - target '%s', draft '%s'\n", i,
                        common_token_to_piece(vocab_tgt, i).c_str(),
                        common_token_to_piece(vocab_dft, i).c_str());
                return 1;
            }
        }
    }

    common_log_set_verbosity_thold(3);
    std::cout << "HS_READY\n" << std::flush;
    std::string line;
    auto * source_target=ctx_tgt;
    while(std::getline(std::cin,line)) {
    const auto whole_start=ggml_time_us();
    const auto req=pj::parse(line);
    observer.reset(req);
    ctx_tgt=source_target;
    llama_memory_clear(llama_get_memory(ctx_tgt),true);
    llama_memory_clear(llama_get_memory(ctx_dft),true);
    llama_synchronize(ctx_tgt);llama_synchronize(ctx_dft);
    auto reset_target=prefill_observer::positions(ctx_tgt),reset_draft=prefill_observer::positions(ctx_dft);
    auto * mem_tgt = llama_get_memory(ctx_tgt);
    auto * mem_dft = llama_get_memory(ctx_dft);

    // Tokenize the prompt
    std::vector<llama_token> inp;
    inp=req.at("prompt_ids").get<std::vector<llama_token>>();
    if(inp.empty()||inp.size()+params.n_predict+params.speculative.draft.n_max+4>1024)return 81;

    const int max_context_size     = llama_n_ctx(ctx_tgt);
    const int max_tokens_list_size = max_context_size - 4;

    if ((int) inp.size() > max_tokens_list_size) {
        LOG_ERR("%s: prompt too long (%d tokens, max %d)\n", __func__, (int) inp.size(), max_tokens_list_size);
        return 1;
    }

    LOG("\n\n");

    for (auto id : inp) {
        LOG("%s", common_token_to_piece(ctx_tgt, id).c_str());
    }

    const int n_input = inp.size();

    const auto t_enc_start = ggml_time_us();

    const bool hs_resuming=req.contains("resume");
    observer.phase="prefill";
    // eval the prompt with both models
    if(!hs_resuming) {
    observer.decode(ctx_tgt,llama_batch_get_one( inp.data(), n_input - 1),"target");
    observer.decode(ctx_tgt,llama_batch_get_one(&inp.back(),           1),"target");
    observer.decode(ctx_dft,llama_batch_get_one( inp.data(), n_input),"draft");
    }

    const auto t_enc_end = ggml_time_us();

    observer.phase="continuation";
    // the 2 models should have the same vocab
    //GGML_ASSERT(n_vocab == llama_vocab_n_tokens(model_dft));

    // how many tokens to draft each time
    int n_draft = params.speculative.draft.n_max;

    int n_predict = 0;
    int n_drafted = 0;
    int n_accept  = 0;

    int n_past_tgt = inp.size();
    int n_past_dft = inp.size();

    // used to determine end of generation
    bool has_eos = false;

    const auto t_dec_start = ggml_time_us();
    // target model sampling context (reuse the llama_context's sampling instance)
    struct common_sampler * smpl = pilot_init(model_tgt, params.sampling);

    // draft sequence data
    std::vector<seq_draft> drafts(n_seq_dft);

    for (int s = 0; s < n_seq_dft; ++s) {
        // allocate llama_sampler for each draft sequence
        drafts[s].smpl = pilot_init(model_dft, params.sampling);
    }

    llama_batch batch_dft = llama_batch_init(llama_n_batch(ctx_dft), 0, 1);
    llama_batch batch_tgt = llama_batch_init(llama_n_batch(ctx_tgt), 0, n_seq_dft);



    // sample from the last token of the prompt
    drafts[0].i_batch_tgt.resize(1);
    drafts[0].i_batch_tgt[0] = 0;

    int pending=-1;pj pending_scores;
    if(!hs_resuming && std::getenv("HS_NO_TRANSFER")==nullptr){
      pending_scores=observer.top(ctx_tgt,0);pending=common_sampler_sample(smpl,ctx_tgt,0);
      auto * original_sampler=smpl;
      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());pilot_free(original_sampler);mem_tgt=llama_get_memory(ctx_tgt);}
    heterospec_direct_ids hs_direct_ids;
    bool hs_resume_ready=hs_resuming;
    if(hs_resuming) {
      std::string file=req.at("resume");auto j=pilot_load(file);std::string base=file.substr(0,file.size()-5);
      if(j.at("prompt_ids")!=inp || j.at("pending")!=-1 || j.at("has_eos")!=false)throw std::runtime_error("Resume contract mismatch");
      if(std::getenv("HS_NO_TRANSFER")==nullptr){ctx_tgt=llama_init_from_model(model_tgt,continuation_cp);if(!ctx_tgt)throw std::runtime_error("Resume context");}
      mem_tgt=llama_get_memory(ctx_tgt);
      auto tb=pilot_read(base+".target.kv"),db=pilot_read(base+".draft.kv");
      auto tc=llama_state_set_data(ctx_tgt,tb.data(),tb.size()),dc=llama_state_set_data(ctx_dft,db.data(),db.size());
      auto tr=prefill_observer::state(ctx_tgt),dr=prefill_observer::state(ctx_dft);
      if(tc!=tb.size()||dc!=db.size()||tr!=tb||dr!=db)throw std::runtime_error("Resume KV roundtrip mismatch");
      pilot_free(smpl);pilot_free(drafts[0].smpl);
      smpl=pilot_restore_sampler(model_tgt,ctx_tgt,params.sampling,j.at("target_sampler"));
      drafts[0].smpl=pilot_restore_sampler(model_dft,ctx_dft,params.sampling,j.at("draft_sampler"));
      hs_direct_ids.ids=j.at("ids").get<std::vector<int>>();hs_direct_ids.eog=j.at("eog").get<std::vector<bool>>();
      n_predict=j.at("n_predict");n_drafted=j.at("n_drafted");n_accept=j.at("n_accept");n_past_tgt=j.at("n_past_tgt");n_past_dft=j.at("n_past_dft");
      auto&d=drafts[0];d.active=j.at("active");d.drafting=j.at("drafting");d.skip=j.at("skip");d.i_batch_dft=j.at("i_batch_dft");
      d.i_batch_tgt=j.at("i_batch_tgt").get<std::vector<int>>();d.tokens=j.at("draft_tokens").get<std::vector<int>>();
      d.dists.clear();std::ifstream df(base+".dists",std::ios::binary);
      for(auto&n:j.at("dist_sizes")){std::vector<llama_token_data>v(n.get<size_t>());df.read((char*)v.data(),v.size()*sizeof(llama_token_data));d.dists.push_back(std::move(v));}
      if(!df)throw std::runtime_error("Draft distribution restore failed");
      pilot_restore_batch(batch_tgt,j.at("batch_target"));pilot_restore_batch(batch_dft,j.at("batch_draft"));
      pilot_json(observer.path+".resume.json",{{"source",file},{"target_roundtrip",true},{"draft_roundtrip",true},{"target_position",prefill_observer::positions(ctx_tgt)},{"draft_position",prefill_observer::positions(ctx_dft)},{"target_sampler",pilot_sampler(smpl,ctx_tgt)},{"draft_sampler",pilot_sampler(d.smpl,ctx_dft)},{"effective_greedy_only",true},{"no_prefill_recompute",true}});
    }
    while (true) {
      if(!hs_resume_ready) {
        std::set<int> active_seqs = {};

        // print current draft sequences
        for (int s = 0; s < n_seq_dft; ++s) {
            if (!drafts[s].active) {
                continue;
            }

            active_seqs.insert(s);
            const auto & tokens = drafts[s].tokens;

            LOG_DBG("draft %d: %s\n", s, string_from(ctx_dft, tokens).c_str());
        }

        int i_dft  = 0;
        int s_keep = 0;

        llama_token token_id;
        std::string token_str;

        // loop until we fail to accept a drafted token or we run out of drafted tokens
        while (true) {

            // check if the target token matches any of the drafts
            // for stochastic sampling, attempt to match the token with the drafted tokens
            {
                bool accept = false;
                const int hs_logit_idx=drafts[s_keep].i_batch_tgt[i_dft];
                const auto hs_score=pending>=0?pending_scores:observer.top(ctx_tgt,hs_logit_idx);
                const int hs_proposal=drafts[s_keep].active && i_dft<(int)drafts[s_keep].tokens.size()?drafts[s_keep].tokens[i_dft]:-1;
                if (params.sampling.temp > 0) {
                    // stochastic verification
                    common_sampler_sample(smpl, ctx_tgt, drafts[s_keep].i_batch_tgt[i_dft], true);

                    auto & dist_tgt = *common_sampler_get_candidates(smpl, true);

                    float p_tgt = 0.0f;
                    float p_dft = 0.0f;

                    while (active_seqs.size() > 0) {
                        // randomly select a sequence to verify from active sequences
                        std::uniform_int_distribution<unsigned int> u_int_dist(0, active_seqs.size() - 1);
                        int s = *std::next(active_seqs.begin(), u_int_dist(rng));
                        if (i_dft >= (int) drafts[s].tokens.size()) {
                            drafts[s].active = false;
                            active_seqs.erase(s);
                            continue;
                        }
                        if (accept) {
                            // if we already accepted a token, we can skip the rest
                            if (drafts[s].tokens[i_dft] != drafts[s_keep].tokens[i_dft]) {
                                drafts[s].active = false;
                                active_seqs.erase(s);
                            }
                            continue;
                        }

                        LOG_DBG("verifying sequence #%d at pos #%d from %d active sequence(s)\n", s, i_dft, (int) active_seqs.size());
                        float r = u_dist(rng);
                        llama_token_data_array dist_dft = { drafts[s].dists[i_dft].data() , drafts[s].dists[i_dft].size(), LLAMA_TOKEN_NULL, true };

                        //GGML_ASSERT(dist_tgt.size <= dist_dft.size);

                        // acquire the token probabilities assigned by the draft and target models
                        for (size_t i = 0; i < dist_tgt.size; i++) {
                            if (dist_tgt.data[i].id == drafts[s].tokens[i_dft]) {
                                p_tgt = dist_tgt.data[i].p;
                                break;
                            }
                        }
                        for (size_t i = 0; i < dist_dft.size; i++) {
                            if (dist_dft.data[i].id == drafts[s].tokens[i_dft]) {
                                p_dft = dist_dft.data[i].p;
                                break;
                            }
                        }
                        LOG_DBG("r = %f, p_dft = %f, p_tgt = %f\n", r, p_dft, p_tgt);
                        if (r <= p_tgt / p_dft) {
                            s_keep = s;
                            accept = true;
                            token_id = drafts[s].tokens[i_dft];
                            token_str = common_token_to_piece(ctx_tgt, token_id);
                            pilot_accept(smpl, token_id, true);

                            LOG_DBG("draft token %d of sequence %d (%d, '%s') accepted\n", i_dft, s, token_id, token_str.c_str());
                            break;
                        } else {
                            LOG_DBG("draft token %d of sequence %d (%d, '%s') rejected\n", i_dft, s, drafts[s].tokens[i_dft], common_token_to_piece(ctx_tgt, drafts[s].tokens[i_dft]).c_str());
                            drafts[s].active = false;

                            // calculate residual probability
                            GGML_ASSERT(dist_tgt.sorted);
                            GGML_ASSERT(dist_dft.sorted);

                            // sort dist by id
                            std::sort(dist_tgt.data, dist_tgt.data + dist_tgt.size, [](const llama_token_data &a, const llama_token_data &b) {
                                return a.id < b.id;
                            });
                            std::sort(dist_dft.data, dist_dft.data + dist_dft.size, [](const llama_token_data &a, const llama_token_data &b) {
                                return a.id < b.id;
                            });

                            float sum_probs = 0.0f;

                            for (size_t i = 0; i < dist_tgt.size; i++) {
                                if (i < dist_dft.size) {
                                    dist_tgt.data[i].p = std::max(0.0f, dist_tgt.data[i].p - dist_dft.data[i].p);
                                } else {
                                    dist_tgt.data[i].p = std::max(0.0f, dist_tgt.data[i].p);
                                }

                                sum_probs += dist_tgt.data[i].p;
                            }

                            for (size_t i = 0; i < dist_tgt.size; i++) {
                                dist_tgt.data[i].p /= sum_probs;
                            }

                            // sort dist_tgt by p desc
                            std::sort(dist_tgt.data, dist_tgt.data + dist_tgt.size, [](const llama_token_data &a, const llama_token_data &b) {
                                return a.p > b.p;
                            });
                        }

                        active_seqs.erase(s);
                        for (int i = 0; i < n_seq_dft; i++) {
                            if (i == s) {
                                continue;
                            }
                            if (drafts[i].active && drafts[i].tokens[i_dft] == drafts[s].tokens[i_dft]) {
                                // synchronize active status for sequences with the same drafted token
                                drafts[i].active = drafts[i].active && accept;
                                if (!drafts[i].active) {
                                    active_seqs.erase(s);
                                }
                            }
                        }
                    }

                    if (!accept) {
                        // all drafted tokens were rejected
                        // sample from the target model
                        LOG_DBG("all drafted tokens were rejected, sampling from residual distribution\n");
                        std::vector<float> probs(dist_tgt.size);
                        for (size_t i = 0; i < dist_tgt.size; ++i) {
                            probs[i] = dist_tgt.data[i].p;
                        }

                        std::discrete_distribution<> dist(probs.begin(), probs.end());

                        const int idx = dist(rng);

                        token_id = dist_tgt.data[idx].id;
                        pilot_accept(smpl, token_id, true);
                        token_str = common_token_to_piece(ctx_tgt, token_id);
                    }
                } else {
                    // greedy verification

                    // sample from the target model
                    LOG_DBG("sampling target: s_keep = %3d, i_dft = %3d, i_batch_tgt = %3d\n", s_keep, i_dft, drafts[s_keep].i_batch_tgt[i_dft]);
                    const int hs_idx=drafts[s_keep].i_batch_tgt[i_dft];
                    const auto hs_scores=pending>=0?pending_scores:observer.top(ctx_tgt,hs_idx);
                    token_id = pending>=0?pending:common_sampler_sample(smpl,ctx_tgt,hs_idx);
                    pending=-1;

                    pilot_accept(smpl, token_id, true);

                    token_str = common_token_to_piece(ctx_tgt, token_id);

                    for (int s = 0; s < n_seq_dft; ++s) {
                        if (!drafts[s].active) {
                            continue;
                        }

                        if (i_dft < (int) drafts[s].tokens.size() && token_id == drafts[s].tokens[i_dft]) {
                            LOG_DBG("the sampled target token matches the %dth drafted token of sequence %d (%d, '%s') - accepted\n", i_dft, s, token_id, token_str.c_str());

                            s_keep = s;
                            accept = true;
                        } else {
                            drafts[s].active = false;
                        }
                    }
                }

                hs_direct_ids.commit(token_id, llama_vocab_is_eog(vocab_tgt, token_id));
                observer.commit(ctx_tgt,token_id,llama_vocab_is_eog(vocab_tgt,token_id),accept,hs_proposal,hs_logit_idx,hs_score);
                if (llama_vocab_is_eog(vocab_tgt, token_id)) {
                    has_eos = true;
                }
                ++n_predict;

                if (accept) {
                    ++n_accept;
                    ++n_past_tgt;
                    ++n_past_dft;
                    ++i_dft;
                    if (params.use_color) {
                        // Color token according to its origin sequence
                        LOG("\u001b[%dm%s\u001b[37m", (36 - s_keep % 6), token_str.c_str());
                    } else {
                        LOG("%s", token_str.c_str());
                    }
                    continue;
                } else {
                    LOG("%s", token_str.c_str());
                    break;
                }
            }
        }

        {
            LOG_DBG("the sampled target token (%d, '%s') did not match, or we ran out of drafted tokens\n", token_id, token_str.c_str());

            // TODO: simplify
            {
                LOG_DBG("keeping sequence %d, n_past_tgt = %d, n_past_dft = %d\n", s_keep, n_past_tgt, n_past_dft);

                observer.role="draft";observer.mutation("keep",mem_dft,s_keep,-1,-1,-1);llama_memory_seq_keep(mem_dft, s_keep);
                observer.role="draft";observer.mutation("cp",mem_dft,s_keep,0,-1,-1);llama_memory_seq_cp  (mem_dft, s_keep, 0, -1, -1);
                observer.role="draft";observer.mutation("keep",mem_dft,0,-1,-1,-1);llama_memory_seq_keep(mem_dft, 0);

                observer.role="target";observer.mutation("rm",mem_tgt,s_keep,-1,n_past_tgt,-1);llama_memory_seq_rm  (mem_tgt, s_keep, n_past_tgt, -1);
                observer.role="target";observer.mutation("keep",mem_tgt,s_keep,-1,-1,-1);llama_memory_seq_keep(mem_tgt, s_keep);
                observer.role="target";observer.mutation("cp",mem_tgt,s_keep,0,-1,-1);llama_memory_seq_cp  (mem_tgt, s_keep, 0, -1, -1);
                observer.role="target";observer.mutation("keep",mem_tgt,0,-1,-1,-1);llama_memory_seq_keep(mem_tgt, 0);
            }

            for (int s = 0; s < n_seq_dft; ++s) {
                drafts[s].active = false;
                drafts[s].tokens.clear();
                drafts[s].i_batch_tgt.clear();
                drafts[s].dists.clear();
            }
            // note: will be erased after the speculation phase
            drafts[0].tokens.push_back(token_id);
            drafts[0].dists.push_back(std::vector<llama_token_data>());
            drafts[0].i_batch_tgt.push_back(0);

            common_batch_clear(batch_dft);
            common_batch_add  (batch_dft, token_id, n_past_dft, { 0 }, true);

            observer.role="draft";observer.mutation("rm",mem_dft,0,-1,n_past_dft,-1);llama_memory_seq_rm(mem_dft, 0, n_past_dft, -1);
            // LOG_DBG("dft batch: %s\n", LOG_BATCH_TOSTR_PRETTY(ctx_dft, batch_dft).c_str());
            observer.decode(ctx_dft,batch_dft,"draft");

            ++n_past_dft;
        }

        if ((params.n_predict >= 0 && n_predict > params.n_predict) || has_eos) {
            break;
        }

        if (drafts[0].smpl) {
            pilot_free(drafts[0].smpl);
        }
        drafts[0].smpl = pilot_clone(smpl);

        int n_seq_cur  = 1;
        int n_past_cur = n_past_dft;

        for (int s = 0; s < n_seq_dft; ++s) {
            drafts[s].active   = false;
            drafts[s].drafting = false;
        }
        drafts[0].active      = true;
        drafts[0].drafting    = true;
        drafts[0].i_batch_dft = 0;

        common_batch_clear(batch_tgt);
        common_batch_add  (batch_tgt, drafts[0].tokens[0], n_past_tgt, { 0 }, true);

        // sample n_draft tokens from the draft model using tree-based sampling
        for (int i = 0; i < n_draft; ++i) {
            batch_dft.n_tokens = 0;

            for (int s = 0; s < n_seq_dft; ++s) {
                drafts[s].skip = false;
            }

            for (int s = 0; s < n_seq_dft; ++s) {
                if (!drafts[s].drafting || drafts[s].skip) {
                    continue;
                }

                common_sampler_sample(drafts[s].smpl, ctx_dft, drafts[s].i_batch_dft, true);

                const auto * cur_p = common_sampler_get_candidates(drafts[s].smpl, true);

                for (int k = 0; k < std::min(n_seq_dft + 3, (int) cur_p->size); ++k) {
                    LOG_DBG(" - draft candidate %3d for seq %3d, pos %3d: %6d (%8.3f) '%s'\n",
                            k, s, i, cur_p->data[k].id, cur_p->data[k].p, common_token_to_piece(ctx_dft, cur_p->data[k].id).c_str());
                }

                std::vector<int> sa(1, s);

                // attempt to split the branch if the probability is high enough
                for (int f = 1; f < 8; ++f) {
                    if (n_seq_cur < n_seq_dft && cur_p->data[f].p > p_draft_split) {
                        LOG_DBG("splitting seq %3d into %3d\n", s, n_seq_cur);

                        observer.role="draft";observer.mutation("rm",mem_dft,n_seq_cur,-1,-1,-1);llama_memory_seq_rm(mem_dft,    n_seq_cur, -1, -1);
                        observer.role="draft";observer.mutation("cp",mem_dft,s,n_seq_cur,-1,-1);llama_memory_seq_cp(mem_dft, s, n_seq_cur, -1, -1);

                        // all previous tokens from this branch are now also part of the new branch
                        for (int t = 0; t < batch_tgt.n_tokens; ++t) {
                            for (int p = 0; p < batch_tgt.n_seq_id[t]; ++p) {
                                if (batch_tgt.seq_id[t][p] == s) {
                                    batch_tgt.seq_id[t][batch_tgt.n_seq_id[t]] = n_seq_cur;
                                    batch_tgt.n_seq_id[t]++;
                                    break;
                                }
                            }
                        }

                        // copy the draft state
                        drafts[n_seq_cur].active   = true;
                        drafts[n_seq_cur].drafting = true;
                        drafts[n_seq_cur].skip     = true;

                        drafts[n_seq_cur].tokens      = drafts[s].tokens;
                        drafts[n_seq_cur].dists       = drafts[s].dists;
                        drafts[n_seq_cur].i_batch_dft = drafts[s].i_batch_dft;
                        drafts[n_seq_cur].i_batch_tgt = drafts[s].i_batch_tgt;

                        if (drafts[n_seq_cur].smpl) {
                            pilot_free(drafts[n_seq_cur].smpl);
                        }
                        drafts[n_seq_cur].smpl = pilot_clone(drafts[s].smpl);

                        sa.push_back(n_seq_cur);

                        n_seq_cur++;
                    } else {
                        break;
                    }
                }

                // add drafted token for each sequence
                for (int is = 0; is < (int) sa.size(); ++is) {
                    const llama_token id = cur_p->data[is].id;

                    const int s = sa[is];

                    pilot_accept(drafts[s].smpl, id, true);

                    drafts[s].tokens.push_back(id);
                    // save cur_p.data into drafts[s].dists
                    drafts[s].dists.push_back({cur_p->data, cur_p->data + cur_p->size});

                    // add unique drafted tokens to the target batch
                    drafts[s].i_batch_tgt.push_back(batch_tgt.n_tokens);

                    common_batch_add(batch_tgt, id, n_past_tgt + i + 1, { s }, true);

                    // add the token to the batch for batched decoding with the draft model
                    drafts[s].i_batch_dft = batch_dft.n_tokens;

                    common_batch_add(batch_dft, id, n_past_cur, { s }, true);

                    if (batch_tgt.n_tokens > n_draft) {
                        drafts[s].drafting = false;
                    }
                }
            }

            // no sequence is drafting anymore
            if (batch_dft.n_tokens == 0) {
                break;
            }

            // evaluate the drafted tokens on the draft model
            observer.decode(ctx_dft,batch_dft,"draft");
            ++n_past_cur;
            ++n_drafted;

            if (batch_tgt.n_tokens > n_draft) {
                break;
            }
        }

      } else { hs_resume_ready=false; }
        // evaluate the target model on the drafted tokens
        {
            observer.role="target";observer.mutation("keep",mem_tgt,0,-1,-1,-1);llama_memory_seq_keep(mem_tgt, 0);
            for (int s = 1; s < n_seq_dft; ++s) {
                observer.role="target";observer.mutation("cp",mem_tgt,0,s,-1,-1);llama_memory_seq_cp(mem_tgt, 0, s, -1, -1);
            }

            // LOG_DBG("target batch: %s\n", LOG_BATCH_TOSTR_PRETTY(ctx_tgt, batch_tgt).c_str());
            std::string hs_checkpoint;
            if(!hs_resuming && req.contains("checkpoint_window") && n_predict>=req.at("checkpoint_window").at(0).get<int>() && n_predict<=req.at("checkpoint_window").at(1).get<int>()) {
              hs_checkpoint=observer.path+".cp-"+std::to_string(n_predict);
              auto tb=prefill_observer::state(ctx_tgt),db=prefill_observer::state(ctx_dft);
              auto &d=drafts[0];std::vector<size_t>sizes;std::ofstream df(hs_checkpoint+".dists",std::ios::binary);
              for(auto&v:d.dists){sizes.push_back(v.size());df.write((char*)v.data(),v.size()*sizeof(llama_token_data));}df.close();
              pilot_write(hs_checkpoint+".target.kv",tb);pilot_write(hs_checkpoint+".draft.kv",db);
              auto ta=prefill_observer::state(ctx_tgt),da=prefill_observer::state(ctx_dft);
              if(tb!=ta||db!=da)throw std::runtime_error("Checkpoint mutated donor");
              pilot_write(hs_checkpoint+".target.source_after.kv",ta);pilot_write(hs_checkpoint+".draft.source_after.kv",da);
              auto cp=continuation_cp;
              pilot_json(hs_checkpoint+".json",{{"schema","heterospec.natural.preverification.v1"},{"request",req.at("request_id")},{"prompt_ids",inp},{"ids",hs_direct_ids.ids},{"eog",hs_direct_ids.eog},{"pending",pending},{"has_eos",has_eos},
                {"n_predict",n_predict},{"n_drafted",n_drafted},{"n_accept",n_accept},{"n_past_tgt",n_past_tgt},{"n_past_dft",n_past_dft},
                {"target_position",prefill_observer::positions(ctx_tgt)},{"draft_position",prefill_observer::positions(ctx_dft)},{"sequence_ownership","serialized API full state; single sequence0"},
                {"target_sampler",pilot_sampler(smpl,ctx_tgt)},{"draft_sampler",pilot_sampler(d.smpl,ctx_dft)},
                {"effective_sampling",{{"temp",params.sampling.temp},{"seed",params.sampling.seed},{"penalty_repeat",params.sampling.penalty_repeat},{"penalty_freq",params.sampling.penalty_freq},{"penalty_present",params.sampling.penalty_present},{"dry_multiplier",params.sampling.dry_multiplier},{"grammar_empty",params.sampling.grammar.empty()},{"grammar_lazy",params.sampling.grammar_lazy},{"reasoning_control",params.sampling.reasoning_control},{"reasoning_budget_tokens",params.sampling.reasoning_budget_tokens},{"backend_sampling",params.sampling.backend_sampling},{"mirostat",params.sampling.mirostat}}},
                {"active",d.active},{"drafting",d.drafting},{"skip",d.skip},{"i_batch_dft",d.i_batch_dft},{"i_batch_tgt",d.i_batch_tgt},{"draft_tokens",d.tokens},{"dist_sizes",sizes},
                {"batch_target",pilot_batch(batch_tgt)},{"batch_draft",pilot_batch(batch_dft)},{"phase","continuation-before-target-verification"},{"k",n_draft},{"ub",llama_n_ubatch(ctx_tgt)},{"prefill_ub",observer.prefill_ub},
                {"outputs_max",cp.n_outputs_max},{"outputs_max_per_seq",cp.n_outputs_max_per_seq},{"source_unchanged",true},{"target_state_bytes",tb.size()},{"draft_state_bytes",db.size()}});
            }
            observer.decode(ctx_tgt,batch_tgt,"target");
            if(!hs_checkpoint.empty()) {
              const int nv=llama_vocab_n_tokens(vocab_tgt);std::vector<float>values;for(int i=0;i<batch_tgt.n_tokens;i++){const float*l=llama_get_logits_ith(ctx_tgt,i);values.insert(values.end(),l,l+nv);}
              pilot_write(hs_checkpoint+".natural.f32",values);
            }
            ++n_past_tgt;
        }

        // the first token is always proposed by the target model before the speculation loop so we erase it here
        for (int s = 0; s < n_seq_dft; ++s) {
            if (!drafts[s].active) {
                continue;
            }

            drafts[s].tokens.erase(drafts[s].tokens.begin());
            drafts[s].dists.erase(drafts[s].dists.begin());
        }
    }

    llama_synchronize(ctx_tgt);llama_synchronize(ctx_dft);
    auto t_dec_end = ggml_time_us();

    LOG("\n\n");

    LOG_INF("encoded %4d tokens in %8.3f seconds, speed: %8.3f t/s\n", n_input,   (t_enc_end - t_enc_start) / 1e6f, inp.size() / ((t_enc_end - t_enc_start) / 1e6f));
    LOG_INF("decoded %4d tokens in %8.3f seconds, speed: %8.3f t/s\n", n_predict, (t_dec_end - t_dec_start) / 1e6f, n_predict  / ((t_dec_end - t_dec_start) / 1e6f));

    LOG_INF("\n");
    LOG_INF("n_draft   = %d\n", n_draft);
    LOG_INF("n_predict = %d\n", n_predict);
    LOG_INF("n_drafted = %d\n", n_drafted);
    LOG_INF("n_accept  = %d\n", n_accept);
    LOG_INF("accept    = %.3f%%\n", 100.0f * n_accept / n_drafted);

    LOG_INF("\n");
    LOG_INF("draft:\n\n");
    // TODO: print sampling/grammar timings for all drafts
    llama_perf_context_print(ctx_dft);

    LOG_INF("\n");
    LOG_INF("target:\n\n");
    common_perf_print(ctx_tgt, smpl);

    pilot_free(smpl);
    for (int s = 0; s < n_seq_dft; ++s) {
        pilot_free(drafts[s].smpl);
    }

    llama_batch_free(batch_dft);

    llama_batch_free(batch_tgt);
    if(ctx_tgt!=source_target)llama_free(ctx_tgt);
    const auto whole_end=ggml_time_us();

    LOG("\n\n");

    observer.finish(hs_direct_ids.ids,hs_direct_ids.eog,inp);
    pj result={{"request_id",req.at("request_id")},{"capture",observer.path},{"generation_ms",(t_dec_end-t_dec_start)/1000.0},{"whole_request_ms",(whole_end-whole_start)/1000.0},{"prefill_ms",(t_enc_end-t_enc_start)/1000.0},{"raw_count",hs_direct_ids.ids.size()},{"drafted",n_drafted},{"accepted",n_accept},{"reset_target",reset_target},{"reset_draft",reset_draft},{"target_continuation_ub",continuation_cp.n_ubatch},{"draft_continuation_ub",llama_n_ubatch(ctx_dft)},{"threads",params.cpuparams.n_threads},{"batch_threads",params.cpuparams_batch.n_threads}};
    std::ofstream result_file(observer.path+".metrics.json",std::ios::binary);result_file<<result.dump(2)<<"\n";result_file.close();
    std::cout<<"HS_RESULT "<<result.dump()<<"\n"<<std::flush;
    }
    llama_backend_free();
    return 0;
}
