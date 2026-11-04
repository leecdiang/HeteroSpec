#include "hs_plan_probe.h"
#include "ggml-cpu.h"
#include "ggml-impl.h"
#include "ggml-backend-impl.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <dlfcn.h>
#include <cstdlib>
static int checks=0,calls=0,copies=0,submissions=0;
extern "C" void ggml_backend_tensor_copy(const ggml_tensor*s,ggml_tensor*d){
 ++copies;static auto fn=reinterpret_cast<void(*)(const ggml_tensor*,ggml_tensor*)>(dlsym(RTLD_NEXT,"ggml_backend_tensor_copy"));if(!fn)std::abort();fn(s,d);
}
static ggml_backend_device devices[2];static ggml_backend_buffer_type types[2];
static decltype(ggml_backend_i::graph_compute) original_compute;
static decltype(ggml_backend_buffer_i::cpy_tensor) original_copy;
static bool supports(ggml_backend_dev_t d,ggml_backend_buffer_type_t t){return (d==&devices[0]&&t==&types[0])||(d==&devices[1]&&t==&types[1]);}
static bool copy_count(ggml_backend_buffer_t b,const ggml_tensor*s,ggml_tensor*d){return original_copy(b,s,d);}
static ggml_backend_buffer_t alloc(ggml_backend_buffer_type_t type,size_t size){auto*b=ggml_backend_cpu_buffer_type()->iface.alloc_buffer(type,size);if(b){original_copy=b->iface.cpy_tensor;b->iface.cpy_tensor=copy_count;}return b;}
static ggml_status compute_count(ggml_backend_t b,ggml_cgraph*g){++submissions;return original_compute(b,g);}
#define CHECK(x) do {++checks;if(!(x)){fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#x);return 1;}}while(0)
static bool callback(ggml_tensor*,bool,void*){++calls;return false;}
int main(){
 ggml_backend_t backends[]={ggml_backend_cpu_init(),ggml_backend_cpu_init()};
 // Test-only isolated buffer domains force real scheduler transfers between
 // two real CPU compute backends. This is NOT a heterogeneous/GPU test.
 for(int i=0;i<2;++i){devices[i]=*backends[i]->device;types[i]=*ggml_backend_cpu_buffer_type();types[i].device=&devices[i];types[i].iface.alloc_buffer=alloc;devices[i].iface.supports_buft=supports;backends[i]->device=&devices[i];original_compute=backends[i]->iface.graph_compute;backends[i]->iface.graph_compute=compute_count;}
 ggml_backend_buffer_type_t bufts[]={&types[0],&types[1]};
 ggml_backend_sched_t sched=ggml_backend_sched_new(backends,bufts,2,1024,false,false);
 ggml_init_params ip{1024*1024,nullptr,true};auto *ctx=ggml_init(ip);
 auto *a=ggml_new_tensor_1d(ctx,GGML_TYPE_F32,16),*b=ggml_new_tensor_1d(ctx,GGML_TYPE_F32,16);
 ggml_set_input(a);ggml_set_input(b);ggml_set_output(a);ggml_set_output(b);auto*c=ggml_add(ctx,a,b);auto*d=ggml_mul(ctx,c,b);auto*e=ggml_add(ctx,d,a);
 ggml_set_output(c);ggml_set_output(d);ggml_set_output(e);
 auto*g=ggml_new_graph_custom(ctx,1024,false);ggml_build_forward_expand(g,e);
 ggml_backend_sched_set_tensor_backend(sched,a,backends[0]);ggml_backend_sched_set_tensor_backend(sched,b,backends[0]);
 ggml_backend_sched_set_tensor_backend(sched,c,backends[0]);ggml_backend_sched_set_tensor_backend(sched,d,backends[1]);ggml_backend_sched_set_tensor_backend(sched,e,backends[0]);
 CHECK(hs_sched_plan_capture(sched,g)==nullptr);CHECK(ggml_backend_sched_alloc_graph(sched,g));
 std::vector<float>x(16,2),y(16,3),sentinel(16,-100),got(16);
 ggml_backend_tensor_set(a,x.data(),0,64);ggml_backend_tensor_set(b,y.data(),0,64);
 for(auto*t:{c,d,e})ggml_backend_tensor_set(t,sentinel.data(),0,64);
 auto*p=hs_sched_plan_capture(sched,g);CHECK(p);struct hs_plan_summary summary{};CHECK(hs_sched_plan_summary(p,&summary));
 printf("splits=%zu transfers=%zu nodes=%zu tensors=%zu blockers=%u\n",summary.splits,summary.transfers,summary.nodes,summary.tensors,summary.blockers);
 CHECK(summary.splits>=3);CHECK(summary.transfers>=2);CHECK(summary.nodes>=3);CHECK(summary.blockers&HS_PLAN_NO_READER_LEASE);CHECK(summary.blockers&HS_PLAN_HIDDEN_BACKEND_PREPARE);
 CHECK(hs_sched_plan_compare(sched,g,p)==HS_PLAN_MATCH_DRY_VETO);
 auto*other=ggml_new_graph_custom(ctx,1024,false);ggml_build_forward_expand(other,e);CHECK(hs_sched_plan_capture(sched,other)==nullptr);
 CHECK(hs_sched_plan_arm_dry(sched,g,p));hs_sched_plan_free(p);
 CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_MATCH_DRY_VETO);
 for(auto*t:{c,d,e}){ggml_backend_tensor_get(t,got.data(),0,64);CHECK(got==sentinel);}
 // Live descriptor mutations must be noticed before ANY split executes.
 e->op_params[0]^=1;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->op_params[0]^=1;
 auto oldnb=e->nb[1];e->nb[1]+=4;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->nb[1]=oldnb;
 auto oldsrc=e->src[0];e->src[0]=a;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->src[0]=oldsrc;
 auto uid=g->uid;g->uid=42;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);g->uid=uid;
 // Other value-relevant descriptors are compared by value, not digest.
 auto olddata=e->data;e->data=a->data;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->data=olddata;
 auto oldne=e->ne[0];e->ne[0]+=1;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->ne[0]=oldne;
 auto oldflags=a->flags;a->flags^=GGML_TENSOR_FLAG_INPUT;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);a->flags=oldflags;
 auto oldoffset=e->view_offs;e->view_offs=4;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->view_offs=oldoffset;
 auto usage=e->buffer->usage;e->buffer->usage=GGML_BACKEND_BUFFER_USAGE_WEIGHTS;CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);e->buffer->usage=usage;
 auto nodes=g->n_nodes;g->n_nodes=g->size+1;CHECK(hs_sched_plan_capture(sched,g)==nullptr);g->n_nodes=nodes;
 // Content-only changes deliberately do NOT become numerical/zero-tail evidence.
 std::vector<float>dirty(16,99);ggml_backend_tensor_set(a,dirty.data(),0,64);
 CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_MATCH_DRY_VETO);ggml_backend_tensor_set(a,x.data(),0,64);
 ggml_backend_sched_set_tensor_backend(sched,c,backends[1]);CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);ggml_backend_sched_set_tensor_backend(sched,c,backends[0]);
 // Callback cannot bypass or observe the gate, even if it normally stops work.
 ggml_backend_sched_set_eval_callback(sched,callback,nullptr);
 CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_STALE);CHECK(calls==0);
 auto*cp=hs_sched_plan_capture(sched,g);CHECK(cp);CHECK(hs_sched_plan_compare(sched,g,cp)==HS_PLAN_UNSUPPORTED);CHECK(hs_sched_plan_arm_dry(sched,g,cp));hs_sched_plan_free(cp);
 CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_UNSUPPORTED);CHECK(calls==0);
 ggml_backend_sched_set_eval_callback(sched,nullptr,nullptr);
 // Cycles are rejected without recursion or launching.
 oldsrc=e->src[0];e->src[0]=e;CHECK(hs_sched_plan_capture(sched,g)==nullptr);e->src[0]=oldsrc;
 CHECK(copies==0);CHECK(submissions==0);
 // Explicit disarm is required for ordinary execution, which remains unchanged.
 hs_sched_plan_disarm(sched);CHECK(ggml_backend_sched_graph_compute(sched,g)==GGML_STATUS_SUCCESS);
 ggml_backend_tensor_get(e,got.data(),0,64);if(got!=std::vector<float>(16,17)){for(auto*t:{a,b,c,d,e}){std::vector<float>v(16);ggml_backend_tensor_get(t,v.data(),0,64);printf("tensor=%s first=%f data=%p\n",ggml_get_name(t),v[0],t->data);}}CHECK(got==std::vector<float>(16,17));CHECK(copies>=2);CHECK(submissions>=3);
 auto*before_reset=hs_sched_plan_capture(sched,g);CHECK(before_reset);CHECK(hs_sched_plan_arm_dry(sched,g,before_reset));hs_sched_plan_free(before_reset);
 ggml_backend_sched_reset(sched);CHECK(ggml_backend_sched_graph_compute_async(sched,g)==GGML_STATUS_FAILED);CHECK(hs_sched_plan_last_result(sched)==HS_PLAN_NOT_ALLOCATED);
 hs_sched_plan_disarm(sched);ggml_backend_sched_free(sched);ggml_free(ctx);for(auto*bkd:backends)ggml_backend_free(bkd);
 printf("PASS native scheduler dry-preflight checks=%d\n",checks);return 0;
}
