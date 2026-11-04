#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include <cassert>
#include <cstdio>

struct State { int asks=0, completed=0; };
static bool stop_after_first(ggml_tensor *, bool ask, void * opaque) {
    auto & s=*static_cast<State *>(opaque);
    if (ask) { ++s.asks; return true; }
    ++s.completed;
    return false;
}
int main() {
    ggml_init_params p{1024*1024,nullptr,true};
    auto * ctx=ggml_init(p);
    assert(ctx);
    auto * a=ggml_new_tensor_1d(ctx,GGML_TYPE_F32,4);
    ggml_set_input(a);
    auto * b=ggml_add(ctx,a,a);
    ggml_set_output(b);
    auto * c=ggml_mul(ctx,b,b);
    auto * d=ggml_add(ctx,c,c);
    ggml_set_output(d);
    auto * graph=ggml_new_graph(ctx);
    ggml_build_forward_expand(graph,d);
    auto cpu=ggml_backend_cpu_init(); assert(cpu);
    ggml_backend_t backends[]{cpu};
    auto sched=ggml_backend_sched_new(backends,nullptr,1,1024,false,false); assert(sched);
    assert(ggml_backend_sched_alloc_graph(sched,graph));
    float inputs[]{1,2,3,4};
    float sentinel[]{-100,-100,-100,-100};
    ggml_backend_tensor_set(a,inputs,0,sizeof(inputs));
    ggml_backend_tensor_set(d,sentinel,0,sizeof(sentinel));
    State state;
    ggml_backend_sched_set_eval_callback(sched,stop_after_first,&state);
    auto status=ggml_backend_sched_graph_compute(sched,graph);
    float first[4],out[4];
    ggml_backend_tensor_get(b,first,0,sizeof(first));
    ggml_backend_tensor_get(d,out,0,sizeof(out));
    assert(status==GGML_STATUS_SUCCESS);
    assert(state.completed==1);
    for(int i=0;i<4;++i) { assert(first[i]==2*inputs[i]);assert(out[i]==-100); }
    std::printf("{\"scheduler_status_success\":true,\"first_node_executed\":true,\"final_output_untouched\":true,\"callback_completions\":%d,\"gpu_tested\":false}\n",state.completed);
    ggml_backend_sched_free(sched);ggml_backend_free(cpu);ggml_free(ctx);
}
