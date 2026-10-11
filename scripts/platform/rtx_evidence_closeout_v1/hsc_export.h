#pragma once
#include "../src/hsc_counter.h"
#include "nlohmann/json.hpp"
#include "hs_observer.h"
namespace hsc {
template<size_t N> inline nlohmann::ordered_json hist(const std::array<int64_t,N>& a){
    auto j=nlohmann::ordered_json::object();for(size_t i=0;i<N;i++)if(a[i])j[std::to_string(i)]=a[i];return j;
}
inline nlohmann::ordered_json snapshot(llama_context * ctx){
    stamp("request_native_response_snapshot");
    static auto modules=hs::modules();
    const char * modes[]={"baseline","counts","lite","heavy"};
    nlohmann::ordered_json out={{"adapter","hsc89-v1"},{"mode",modes[w.mode]},
        {"phase_timers",timed()},{"heavy_capture",is_heavy()},{"etw",false},{"added_sync",is_heavy()},
        {"scope_mask",hs_scope::mask()},{"context",llama_n_ctx(ctx)},{"effective_batch",llama_n_batch(ctx)},
        {"target_ub",llama_n_ubatch(ctx)},{"modules",modules},
        {"timing_semantics","decode API return is enqueue-only; natural sampling ready markers do not prove a disjoint completed wall partition"}};
    if(w.mode!=baseline){
        out["workload"]={{"prompt_ids_count",w.prompt},{"output_ids_count",w.output},
          {"proposal_generated",w.generated},{"proposal_verified",w.verified},{"accepted_committed",w.accept},
          {"first_mismatch_rejected",w.mismatch},{"unexamined_after_mismatch",w.unexamined},
          {"terminal_discarded",w.terminal},{"unverified_before_verify",w.generated-w.verified},
          {"initial_target_committed",w.origin[initial]},{"bonus_committed",w.origin[bonus]},
          {"correction_committed",w.origin[correction]},{"fallback_committed",w.origin[fallback]},
          {"verify_cycles",w.cycles},{"verification_seed_rows",w.cycles},
          {"draft_continuation_calls",w.draft_calls},{"draft_continuation_rows",w.draft_rows},{"rollback_calls",w.rollback},
          {"accepted_prefix_hist",hist(w.prefix)},{"cycle_progress_hist",hist(w.progress)},
          {"verification_caller_width_hist",hist(w.verify_width)},
          {"attempted_positions",hist(w.attempted_pos)},{"accepted_positions",hist(w.accepted_pos)},
          {"draft_prefill_calls",w.draft_prefill_calls},{"draft_prefill_ids",w.draft_prefill_rows},
          {"draft_continuation_caller_calls",w.draft_caller_calls},{"draft_continuation_caller_rows",w.draft_caller_rows},
          {"draft_proposal_calls",w.draft_proposal_calls},{"draft_proposal_rows",w.draft_proposal_rows},
          {"draft_catchup_calls",w.draft_catchup_calls},{"draft_catchup_rows",w.draft_catchup_rows},
          {"target_prefill_calls",w.target_prefill_calls},{"target_prefill_ids",w.target_prefill_rows},
          {"target_continuation_calls",w.target_calls},{"target_continuation_rows",w.target_rows},
          {"target_verification_calls",w.target_verify_calls},{"target_replay_calls",w.target_replay_calls},
          {"target_fallback_calls",w.target_fallback_calls},{"target_caller_width_hist",hist(w.target_width)},
          {"physical_micrograph_calls",w.physical_calls},{"physical_micrograph_rows",w.physical_rows},
          {"graphs_reused",w.graphs_reused},{"target_prefill_physical_calls",w.target_prefill_physical_calls},
          {"draft_prefill_physical_calls",w.draft_prefill_physical_calls},{"target_continuation_physical_width_hist",hist(w.target_continuation_physical)},
          {"target_physical_width_hist",hist(w.target_physical)},{"draft_physical_width_hist",hist(w.draft_physical)},
          {"physical_semantics","actual tokens passed to graph_compute; not hardware occupancy"},
          {"unsupported_replay",w.unsupported_replay}};
        out["feature_units"]={{"target_prefill_ids",w.target_prefill_rows},{"draft_prefill_ids",w.draft_prefill_rows},
          {"draft_continuation_rows",w.draft_rows},{"reconcile_output_ids",w.output},{"rollback_calls",w.rollback},{"request_channel",1}};
        for(int i=1;i<=4;i++)out["feature_units"]["target_continuation_calls_w"+std::to_string(i)]=w.target_width[i];
    }
    if(timed()){
        out["elapsed_hooks"]=nlohmann::ordered_json::array();
        for(const auto & s:w.stamps)out["elapsed_hooks"].push_back({{"event",s.event},{"role",s.role},{"rows",s.rows},{"steady_ns",s.ns}});
        out["completed_wall_partition"]=false;out["gpu_event_ms"]=nullptr;
    }
    return out;
}
}
