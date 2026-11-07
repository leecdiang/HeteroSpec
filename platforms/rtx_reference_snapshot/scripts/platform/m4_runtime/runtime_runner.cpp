// M4 runtime control; uses llama.cpp v0.4.0 draft-simple from the pinned common library.
// Mechanism adapted from examples/speculative-simple/speculative-simple.cpp (MIT).
#include "arg.h"
#include "common.h"
#include "sampling.h"
#include "speculative.h"
#include "llama.h"
#include "ggml.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct request {
    std::string condition;
    int E;
    double margin;
    double target_ref;
    int cap;
    llama_tokens prompt;
};
struct round_record {
    int round, proposed, accepted, committed;
    int64_t draft_ns, target_ns, accept_ns, reconcile_ns, elapsed_ns;
    double realized_rate;
    bool decision, fallback;
    int32_t target_kv_max;
};
static request parse(const std::string & line) {
    std::vector<std::string> fields;
    std::stringstream ss(line);
    std::string x;
    while (std::getline(ss, x, '\t')) fields.push_back(x);
    if (fields.size() != 6) throw std::runtime_error("Expected six tab-separated fields");
    request r;
    r.condition = fields[0]; r.E = std::stoi(fields[1]); r.margin = std::stod(fields[2]);
    r.target_ref = std::stod(fields[3]); r.cap = std::stoi(fields[4]);
    if (r.condition != "TARGET_ONLY" && r.condition != "ALWAYS_SPEC_K2" && r.condition != "GUARD_K2") throw std::runtime_error("Invalid condition");
    if (r.E < 1 || r.margin < 0 || r.margin >= 1 || r.cap < 1) throw std::runtime_error("Invalid policy");
    if (r.condition == "GUARD_K2" && r.target_ref <= 0) throw std::runtime_error("Invalid target reference");
    std::stringstream ids(fields[5]);
    while (std::getline(ids, x, ',')) r.prompt.push_back(std::stoi(x));
    if (r.prompt.empty()) throw std::runtime_error("Empty prompt");
    return r;
}
static void add(llama_batch & b, llama_token id, int pos, bool output) {
    common_batch_add(b, id, pos, {0}, output);
}
static void emit(const request & req, const llama_tokens & out, const std::vector<round_record> & rounds,
                 int64_t elapsed_ns, int64_t guard_ns, int64_t transition_ns, int fallback_round,
                 int spec_committed, bool ended_on_eog) {
    std::cout << "{\"status\":\"OK\",\"condition\":\"" << req.condition << "\",\"end_to_end_ns\":" << elapsed_ns << ",\"generated_token_ids\":[";
    for (size_t i=0; i<out.size(); ++i) { if (i) std::cout << ','; std::cout << out[i]; }
    std::cout << "],\"generated_token_count\":" << out.size()
              << ",\"stop_reason\":\"" << (ended_on_eog ? "EOS" : "CAP") << "\""
              << ",\"speculative_committed_token_count\":" << spec_committed
              << ",\"target_only_committed_token_count\":" << out.size()-spec_committed
              << ",\"guard_compute_ns\":" << guard_ns
              << ",\"fallback_transition_ns\":" << transition_ns
              << ",\"fallback_triggered\":" << (fallback_round ? "true" : "false")
              << ",\"fallback_round\":" << fallback_round << ",\"rounds\":[";
    for (size_t i=0; i<rounds.size(); ++i) {
        const auto & r=rounds[i]; if (i) std::cout << ',';
        std::cout << "{\"round\":" << r.round << ",\"proposed\":" << r.proposed
                  << ",\"accepted\":" << r.accepted << ",\"committed\":" << r.committed
                  << ",\"draft_ns\":" << r.draft_ns << ",\"target_ns\":" << r.target_ns
                  << ",\"accept_ns\":" << r.accept_ns << ",\"reconcile_ns\":" << r.reconcile_ns
                  << ",\"elapsed_ns\":" << r.elapsed_ns << ",\"realized_ns_per_token\":" << r.realized_rate
                  << ",\"decision\":" << (r.decision ? "true" : "false")
                  << ",\"fallback\":" << (r.fallback ? "true" : "false")
                  << ",\"target_kv_max\":" << r.target_kv_max << '}';
    }
    std::cout << "]}" << std::endl;
}
static void run_one(const request & req, common_params & params, llama_model * model,
                    llama_context * tgt, llama_context * dft, bool ckpt_tgt, bool ckpt_dft) {
    const auto * vocab = llama_model_get_vocab(model);
    llama_memory_clear(llama_get_memory(tgt), true);
    llama_memory_clear(llama_get_memory(dft), true);
    common_sampler_ptr smpl(common_sampler_init(model, params.sampling));
    for (auto id : req.prompt) common_sampler_accept(smpl.get(), id, false);
    common_speculative_ptr spec;
    if (req.condition!="TARGET_ONLY") {
        spec.reset(common_speculative_init(params.speculative, 1));
        if (!spec) throw std::runtime_error("Pinned draft-simple initialization failed");
    }
    if (req.prompt.size()+req.cap+3 > llama_n_ctx(tgt) || req.prompt.size()>llama_n_batch(tgt)) throw std::runtime_error("Prompt/context limit");
    llama_batch prefill=llama_batch_init(llama_n_batch(tgt), 0, 1);
    for (size_t i=0; i<req.prompt.size(); ++i) add(prefill, req.prompt[i], i, i+1==req.prompt.size());
    if (llama_decode(tgt, prefill)) throw std::runtime_error("Target prefill failed");
    if (req.condition!="TARGET_ONLY" && !common_speculative_process(spec.get(), prefill)) throw std::runtime_error("Draft prefill failed");
    llama_synchronize(tgt);
    if (req.condition!="TARGET_ONLY") common_speculative_begin(spec.get(), 0, req.prompt);
    const int64_t start=ggml_time_us();
    llama_tokens out;
    std::vector<round_record> rounds;
    int64_t guard_ns=0, transition_ns=0;
    int fallback_round=0;
    bool speculative=req.condition!="TARGET_ONLY";
    int spec_committed=speculative ? 1 : 0;
    int n_past=req.prompt.size();
    llama_token last=common_sampler_sample(smpl.get(), tgt, -1);
    common_sampler_accept(smpl.get(), last, true);
    out.push_back(last);
    bool done=llama_vocab_is_eog(vocab,last);
    llama_batch & batch=prefill;
    llama_tokens prompt_tgt=req.prompt, proposals;
    common_prompt_checkpoint ckpt;
    while (!done && int(out.size())<req.cap) {
        if (speculative && int(out.size()) + 1 >= req.cap) speculative=false;
        if (!speculative) {
            common_batch_clear(batch); add(batch,last,n_past,true);
            if (llama_decode(tgt,batch)) throw std::runtime_error("Target decode failed");
            ++n_past;
            last=common_sampler_sample(smpl.get(),tgt,0);
            common_sampler_accept(smpl.get(),last,true);
            out.push_back(last); done=llama_vocab_is_eog(vocab,last);
            continue;
        }
        const int rnum=rounds.size()+1;
        const int64_t d0=ggml_time_us();
        proposals.clear();
        ckpt.update_pos(prompt_tgt.size(),llama_memory_seq_pos_min(llama_get_memory(tgt),0),llama_memory_seq_pos_max(llama_get_memory(tgt),0));
        if (ckpt_dft) ckpt.update_dft(dft,0,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
        const int max_draft=std::max(0,std::min(2,req.cap-int(out.size())-1));
        common_speculative_get_draft_params(spec.get(),0)={true,max_draft,n_past,last,&prompt_tgt,&proposals};
        common_speculative_draft(spec.get());
        llama_synchronize(dft);
        if (ckpt_dft) ckpt.load_dft(dft,0,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
        if (!llama_memory_seq_rm(llama_get_memory(dft),0,ckpt.pos_max+1,-1)) throw std::runtime_error("Draft rollback failed");
        if (ckpt_tgt && !proposals.empty()) ckpt.update_tgt(tgt,0,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
        const int64_t d1=ggml_time_us();
        const int base=n_past;
        common_batch_clear(batch); add(batch,last,base,true);
        for (size_t i=0;i<proposals.size();++i) add(batch,proposals[i],base+1+i,true);
        const int64_t t0=ggml_time_us();
        if (llama_decode(tgt,batch)) throw std::runtime_error("Target verification failed");
        if (!common_speculative_process(spec.get(),batch)) throw std::runtime_error("Draft process failed");
        llama_synchronize(tgt);
        llama_synchronize(dft);
        const int64_t t1=ggml_time_us();
        const int proposed=proposals.size();
        const int64_t a0=ggml_time_us();
        auto accepted_ids=common_sampler_sample_and_accept_n(smpl.get(),tgt,proposals);
        if (accepted_ids.empty()) throw std::runtime_error("No verifier output");
        if (ckpt_tgt && accepted_ids.size()-1<proposals.size()) throw std::runtime_error("PRECONDITION_BLOCKED: checkpoint replay required");
        common_speculative_accept(spec.get(),0,accepted_ids.size()-1);
        const int accepted=accepted_ids.size()-1;
        const int64_t a1=ggml_time_us();
        const int64_t k0=ggml_time_us();
        for (auto id: accepted_ids) {
            prompt_tgt.push_back(last); last=id; out.push_back(id);
            if (llama_vocab_is_eog(vocab,last)||int(out.size())>=req.cap) { done=true; break; }
        }
        spec_committed=out.size();
        n_past=base+1+accepted;
        if (!llama_memory_seq_rm(llama_get_memory(tgt),0,n_past,-1)) throw std::runtime_error("Target rollback failed");
        if (!llama_memory_seq_rm(llama_get_memory(dft),0,n_past,-1)) throw std::runtime_error("Draft rollback failed");
        const int kv_max=llama_memory_seq_pos_max(llama_get_memory(tgt),0);
        const int64_t k1=ggml_time_us();
        round_record rr={rnum,proposed,accepted,int(out.size()),(d1-d0)*1000,(t1-t0)*1000,(a1-a0)*1000,(k1-k0)*1000,(k1-start)*1000,0.0,false,false,kv_max};
        if (req.condition=="GUARD_K2" && !done && rnum>=req.E) {
            const auto g0=std::chrono::steady_clock::now();
            rr.decision=true;
            rr.elapsed_ns=(ggml_time_us()-start)*1000;
            rr.realized_rate=rr.committed ? double(rr.elapsed_ns)/rr.committed : -1.0;
            rr.fallback=!(rr.realized_rate<=(1.0-req.margin)*req.target_ref);
            const auto g1=std::chrono::steady_clock::now();
            guard_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(g1-g0).count();
            if (rr.fallback) {
                const auto f0=std::chrono::steady_clock::now();
                speculative=false; proposals.clear(); fallback_round=rnum;
                transition_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-f0).count();
            }
        }
        rounds.push_back(rr);
    }
    llama_synchronize(tgt);
    const int64_t elapsed=(ggml_time_us()-start)*1000;
    llama_batch_free(prefill);
    emit(req,out,rounds,elapsed,guard_ns,transition_ns,fallback_round,spec_committed,
         !out.empty() && llama_vocab_is_eog(vocab,out.back()));
}
int main(int argc,char ** argv) {
    common_params params;
    common_init();
    if (!common_params_parse(argc,argv,params,LLAMA_EXAMPLE_SPECULATIVE)) return 1;
    auto limits=common_speculative_get_output_limits(params.n_batch,1,common_speculative_n_max(&params.speculative));
    params.n_outputs_max=limits.total; params.n_outputs_max_per_seq=limits.per_seq;
    llama_backend_init();
    auto target=common_init_from_params(params);
    auto * model=target->model(); auto * tgt=target->context();
    auto dparams=common_base_params_to_speculative(params);
    auto draft=common_speculative_init_from_params(dparams,model,tgt);
    auto * dft=draft->context();
    if (!dft) throw std::runtime_error("Draft context missing");
    params.speculative.draft.ctx_tgt=tgt; params.speculative.draft.ctx_dft=dft;
    const bool ckpt_tgt=common_context_can_seq_rm(tgt)==COMMON_CONTEXT_SEQ_RM_TYPE_FULL;
    const bool ckpt_dft=common_context_can_seq_rm(dft)==COMMON_CONTEXT_SEQ_RM_TYPE_FULL;
    std::cout << "READY" << std::endl;
    std::string line;
    while (std::getline(std::cin,line)) {
        if (line=="QUIT") break;
        try { run_one(parse(line),params,model,tgt,dft,ckpt_tgt,ckpt_dft); }
        catch (const std::exception & e) {
            std::cout << "{\"status\":\"ERROR\",\"error\":\"" << e.what() << "\"}" << std::endl;
        }
    }
    llama_backend_free();
    return 0;
}
