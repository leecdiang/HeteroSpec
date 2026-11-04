#pragma once
#include "ggml-backend.h"
#ifdef __cplusplus
extern "C" {
#endif
// Caller MUST serialize scheduler/graph/buffer access and keep every referenced
// tensor, graph and buffer alive. No concurrent mutation, reset, or free.
// Diagnostic only. No result is an execution certificate or a read lease.
struct hs_sched_plan;
enum hs_plan_result { HS_PLAN_DISABLED=0, HS_PLAN_MATCH_DRY_VETO=1, HS_PLAN_STALE=2, HS_PLAN_UNSUPPORTED=3, HS_PLAN_NOT_ALLOCATED=4, HS_PLAN_ERROR=5 };
struct hs_plan_summary { uint64_t instance, epoch; size_t splits, nodes, transfers, tensors; unsigned blockers; };
enum hs_plan_blocker { HS_PLAN_NO_READER_LEASE=1, HS_PLAN_HIDDEN_BACKEND_PREPARE=2, HS_PLAN_CALLBACK=4, HS_PLAN_PARALLEL_COPIES=8, HS_PLAN_PERSISTENT_WRITE=16, HS_PLAN_DEVICE_NONCPU=32 };
GGML_API struct hs_sched_plan * hs_sched_plan_capture(ggml_backend_sched_t, struct ggml_cgraph *);
GGML_API void hs_sched_plan_free(struct hs_sched_plan *);
GGML_API bool hs_sched_plan_summary(const struct hs_sched_plan *, struct hs_plan_summary *);
GGML_API enum hs_plan_result hs_sched_plan_compare(ggml_backend_sched_t, struct ggml_cgraph *,const struct hs_sched_plan *);
// Arm copies the immutable descriptor; caller may free the original afterward.
// While armed EVERY compute is rejected, including an exact match. There is no allow mode.
GGML_API bool hs_sched_plan_arm_dry(ggml_backend_sched_t, struct ggml_cgraph *,const struct hs_sched_plan *);
GGML_API void hs_sched_plan_disarm(ggml_backend_sched_t);
GGML_API enum hs_plan_result hs_sched_plan_last_result(ggml_backend_sched_t);
#ifdef __cplusplus
}
#endif
