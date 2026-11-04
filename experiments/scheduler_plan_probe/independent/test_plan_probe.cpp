#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "hs_plan_probe.h"
#include "ggml-impl.h"
#include "ggml-backend-impl.h"
#include <cassert>
#include <cstdio>

static int sync_calls=0;
static void (*original_sync)(ggml_backend_t)=nullptr;
static void count_sync(ggml_backend_t backend){++sync_calls;if(original_sync)original_sync(backend);}
struct Callback { int called=0; };
static bool cb(ggml_tensor *,bool,void*opaque){++static_cast<Callback*>(opaque)->called;return true;}
int main(){
    ggml_init_params params{1024*1024,nullptr,true};auto *ctx=ggml_init(params);assert(ctx);
    auto *a=ggml_new_tensor_1d(ctx,GGML_TYPE_F32,4);ggml_set_input(a);
    auto *b=ggml_add(ctx,a,a);ggml_set_output(b);
    auto *graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,b);
    auto *other=ggml_new_graph(ctx);auto *other_result=ggml_mul(ctx,a,a);ggml_build_forward_expand(other,other_result);
    auto cpu=ggml_backend_cpu_init();original_sync=cpu->iface.synchronize;cpu->iface.synchronize=count_sync;ggml_backend_t backends[]{cpu};auto s=ggml_backend_sched_new(backends,nullptr,1,1024,false,false);assert(s);
    assert(ggml_backend_sched_alloc_graph(s,graph));
    const float in[]{1,2,3,4},sentinel[]{-90,-90,-90,-90};ggml_backend_tensor_set(a,in,0,sizeof(in));ggml_backend_tensor_set(b,sentinel,0,sizeof(sentinel));
    auto *plan=hs_sched_plan_capture(s,graph);assert(plan);hs_plan_summary summary{};assert(hs_sched_plan_summary(plan,&summary));
    assert(hs_sched_plan_compare(s,graph,plan)==HS_PLAN_MATCH_DRY_VETO);
    assert((summary.blockers&HS_PLAN_NO_READER_LEASE)&&(summary.blockers&HS_PLAN_HIDDEN_BACKEND_PREPARE));
    // Metadata equality intentionally does not inspect or qualify tensor data.
    float different[]{9,8,7,6};ggml_backend_tensor_set(a,different,0,sizeof(different));assert(hs_sched_plan_compare(s,graph,plan)==HS_PLAN_MATCH_DRY_VETO);
    // Auxiliary use-count metadata influences fusion and must be snapshotted.
    auto index=ggml_hash_find(&graph->visited_hash_set,b);
    assert(index!=GGML_HASHSET_FULL);
    auto uses=graph->use_counts[index];graph->use_counts[index]=uses+1;
    assert(hs_sched_plan_compare(s,graph,plan)==HS_PLAN_STALE);
    graph->use_counts[index]=uses;
    // A malformed caller count must be rejected before reading beyond nodes.
    auto node_count=graph->n_nodes;graph->n_nodes=graph->size+1;
    assert(hs_sched_plan_capture(s,graph)==nullptr);graph->n_nodes=node_count;
    assert(hs_sched_plan_arm_dry(s,graph,plan));hs_sched_plan_free(plan);
    sync_calls=0;
    auto status=ggml_backend_sched_graph_compute(s,graph);assert(status==GGML_STATUS_FAILED);assert(sync_calls==1);assert(hs_sched_plan_last_result(s)==HS_PLAN_MATCH_DRY_VETO);
    float out[4];ggml_backend_tensor_get(b,out,0,sizeof(out));for(float x:out)assert(x==-90);
    // Detect mutation of operator metadata before any computation.
    b->op_params[0]^=1;
    status=ggml_backend_sched_graph_compute(s,graph);assert(status==GGML_STATUS_FAILED);assert(hs_sched_plan_last_result(s)==HS_PLAN_STALE);b->op_params[0]^=1;
    hs_sched_plan_disarm(s);
    // Existing evaluation callbacks must be diagnosed, never invoked while armed.
    Callback count;ggml_backend_sched_set_eval_callback(s,cb,&count);
    plan=hs_sched_plan_capture(s,graph);assert(plan);assert(hs_sched_plan_compare(s,graph,plan)==HS_PLAN_UNSUPPORTED);
    assert(hs_sched_plan_arm_dry(s,graph,plan));hs_sched_plan_free(plan);
    status=ggml_backend_sched_graph_compute(s,graph);assert(status==GGML_STATUS_FAILED);assert(count.called==0);
    hs_sched_plan_disarm(s);ggml_backend_sched_set_eval_callback(s,nullptr,nullptr);
    // A different caller graph is not the graph the scheduler allocated.
    auto *wrong=hs_sched_plan_capture(s,other);int wrong_result=wrong?hs_sched_plan_compare(s,other,wrong):HS_PLAN_ERROR;
    const bool wrong_rejected=!wrong||wrong_result==HS_PLAN_STALE||wrong_result==HS_PLAN_ERROR||wrong_result==HS_PLAN_NOT_ALLOCATED;
    hs_sched_plan_free(wrong);
    // Cyclic source metadata must terminate and fail capture.
    a->src[0]=a;auto *cycle=hs_sched_plan_capture(s,graph);assert(!cycle);a->src[0]=nullptr;
    plan=hs_sched_plan_capture(s,graph);assert(plan);assert(hs_sched_plan_arm_dry(s,graph,plan));
    ggml_backend_sched_reset(s);
    status=ggml_backend_sched_graph_compute_async(s,graph);assert(status==GGML_STATUS_FAILED);assert(hs_sched_plan_last_result(s)==HS_PLAN_NOT_ALLOCATED);
    hs_sched_plan_free(plan);
    std::printf("{\"matching_plan_vetoed\":true,\"sync_wrapper_still_calls_synchronize\":true,\"metadata_mutation_vetoed\":true,\"callback_not_invoked\":true,\"reset_does_not_disarm\":true,\"data_not_certified\":true,\"use_counts_mutation_detected\":true,\"oversized_caller_graph_rejected\":true,\"cycle_rejected\":true,\"wrong_caller_graph_rejected\":%s,\"wrong_caller_compare\":%d,\"gpu_tested\":false}\n",wrong_rejected?"true":"false",wrong_result);
    ggml_backend_sched_free(s);ggml_backend_free(cpu);ggml_free(ctx);
    return wrong_rejected?0:1;
}
