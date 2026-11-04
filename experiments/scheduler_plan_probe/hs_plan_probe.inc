// Included inside ggml-backend.cpp after scheduler internals. No callbacks invoked.
#include "hs_plan_probe.h"
#include <array>
#include <set>
#include <tuple>
#include <atomic>
#include <stdexcept>
#include <limits>
static std::atomic<uint64_t> hs_plan_next_instance{1};
static uint64_t hs_plan_allocate_instance(){
    uint64_t current=hs_plan_next_instance.load();
    while(current!=UINT64_MAX){if(hs_plan_next_instance.compare_exchange_weak(current,current+1))return current;}
    return 0; // saturated; capture refuses, never reuse an instance id
}
struct hs_tensor_descriptor {
    const ggml_tensor * identity; const void *data; ggml_backend_buffer_t buffer;
    ggml_backend_buffer_type_t buft; const void *buffer_context; size_t buffer_size; ggml_backend_buffer_usage usage;
    ggml_type type; ggml_op op; int32_t flags;
    std::array<int64_t,GGML_MAX_DIMS> ne;
    std::array<size_t,GGML_MAX_DIMS> nb;
    std::array<int32_t,GGML_MAX_OP_PARAMS/sizeof(int32_t)> params;
    std::array<const ggml_tensor*,GGML_MAX_SRC> src;
    const ggml_tensor * view; size_t view_offset; const void *extra;
    auto key()const{return std::tie(identity,data,buffer,buft,buffer_context,buffer_size,usage,type,op,flags,ne,nb,params,src,view,view_offset,extra);}
    bool operator==(const hs_tensor_descriptor&o)const{return key()==o.key();}
};
struct hs_graph_aux {
    uint64_t uid;ggml_cgraph_eval_order order;const void *grads,*grad_accs,*counts_identity;
    size_t hash_size;std::vector<std::tuple<size_t,const ggml_tensor*,int32_t>> used;
    auto key()const{return std::tie(uid,order,grads,grad_accs,counts_identity,hash_size,used);}
    bool operator==(const hs_graph_aux&o)const{return key()==o.key();}
};
static hs_graph_aux hs_read_graph_aux(const ggml_cgraph&g){
    hs_graph_aux a{g.uid,g.order,g.grads,g.grad_accs,g.use_counts,g.visited_hash_set.size,{}};
    if(a.hash_size>2000000||(a.hash_size&&(!g.visited_hash_set.used||!g.visited_hash_set.keys)))throw std::invalid_argument("invalid graph hash table");
    for(size_t i=0;i<a.hash_size;++i)if(ggml_bitset_get(g.visited_hash_set.used,i))a.used.emplace_back(i,g.visited_hash_set.keys[i],g.use_counts?g.use_counts[i]:0);
    return a;
}
struct hs_split_descriptor {
    hs_graph_aux aux;
    int backend_id,start,end;ggml_backend_t backend;ggml_backend_buffer_type_t buft; ggml_backend_dev_t device;const void *backend_context;decltype(ggml_backend_i::graph_compute) compute;
    std::vector<const ggml_tensor*> nodes,inputs,copies;
    std::vector<std::pair<int,ggml_backend_t>> source_backends;
    auto key()const{return std::tie(aux,backend_id,start,end,backend,buft,device,backend_context,compute,nodes,inputs,copies,source_backends);}
    bool operator==(const hs_split_descriptor&o)const{return key()==o.key();}
};
struct hs_sched_plan {
    hs_graph_aux caller_aux;
    ggml_backend_sched_t owner; const ggml_cgraph * caller;
    uint64_t instance,epoch,graph_uid;ggml_cgraph_eval_order graph_order;int current_copy,next_copy,ncopies;
    ggml_backend_sched_eval_callback callback;void *callback_data;
    std::vector<const ggml_tensor*> caller_nodes,caller_leafs;
    std::vector<hs_split_descriptor> splits;std::vector<hs_tensor_descriptor> tensors;
    std::vector<ggml_backend_event_t> events;
    unsigned blockers=HS_PLAN_NO_READER_LEASE|HS_PLAN_HIDDEN_BACKEND_PREPARE;
    auto key()const{return std::tie(caller_aux,owner,caller,instance,epoch,graph_uid,graph_order,current_copy,next_copy,ncopies,callback,callback_data,caller_nodes,caller_leafs,splits,tensors,events,blockers);}
    bool operator==(const hs_sched_plan&o)const{return key()==o.key();}
};
static hs_sched_plan hs_plan_read(ggml_backend_sched_t sched,ggml_cgraph *graph) {
    if(!sched||!graph||!sched->is_alloc||sched->n_splits<=0||sched->n_splits>100000||graph->n_nodes<=0||graph->n_nodes>100000||graph->n_leafs<0||graph->n_leafs>100000||sched->hs_plan_instance==0||sched->hs_plan_epoch==UINT64_MAX)throw std::invalid_argument("unallocated/empty plan");
    if(sched->hs_plan_graph!=graph||!graph->nodes||graph->n_nodes>graph->size||graph->n_leafs>graph->size||(graph->n_leafs&&!graph->leafs)||
       sched->n_splits>sched->splits_capacity||!sched->splits||sched->n_backends<=0||sched->n_backends>GGML_SCHED_MAX_BACKENDS||
       sched->n_copies<=0||sched->n_copies>GGML_SCHED_MAX_COPIES||sched->cur_copy<0||sched->cur_copy>=sched->n_copies||
       sched->next_copy<0||sched->next_copy>=sched->n_copies)throw std::invalid_argument("unbound/malformed graph");
    hs_sched_plan p;p.caller_aux=hs_read_graph_aux(*graph);p.owner=sched;p.caller=graph;p.instance=sched->hs_plan_instance;p.epoch=sched->hs_plan_epoch;
    p.graph_uid=graph->uid;p.graph_order=graph->order;
    p.current_copy=sched->cur_copy;p.next_copy=sched->next_copy;p.ncopies=sched->n_copies;
    p.callback=sched->callback_eval;p.callback_data=sched->callback_eval_user_data;
    if(p.callback)p.blockers|=HS_PLAN_CALLBACK;if(p.ncopies!=1)p.blockers|=HS_PLAN_PARALLEL_COPIES;
    std::vector<const ggml_tensor*> queue;std::set<const ggml_tensor*> seen;
    auto add=[&](const ggml_tensor*t){if(t&&seen.insert(t).second){if(queue.size()>=100000)throw std::invalid_argument("tensor census limit");queue.push_back(t);}};
    for(int i=0;i<graph->n_nodes;++i){p.caller_nodes.push_back(graph->nodes[i]);add(graph->nodes[i]);}
    for(int i=0;i<graph->n_leafs;++i){p.caller_leafs.push_back(graph->leafs[i]);add(graph->leafs[i]);}
    for(int b=0;b<sched->n_backends;++b)for(int c=0;c<sched->n_copies;++c)p.events.push_back(sched->events[b][c]);
    for(int i=0;i<sched->n_splits;++i){
        const auto&s=sched->splits[i];if(s.backend_id<0||s.backend_id>=sched->n_backends||s.graph.n_nodes<=0||s.graph.n_nodes>100000||!s.graph.nodes||s.n_inputs<0||s.n_inputs>s.inputs_capacity||(s.n_inputs&&!s.inputs))throw std::invalid_argument("invalid split");
        hs_split_descriptor d;d.aux=hs_read_graph_aux(s.graph);d.backend_id=s.backend_id;d.start=s.i_start;d.end=s.i_end;d.backend=sched->backends[s.backend_id];d.buft=sched->bufts[s.backend_id];
        d.device=d.backend->device;d.backend_context=d.backend->context;d.compute=d.backend->iface.graph_compute; // no virtual metadata getter
        for(int j=0;j<s.graph.n_nodes;++j){d.nodes.push_back(s.graph.nodes[j]);add(s.graph.nodes[j]);}
        for(int j=0;j<s.n_inputs;++j){
            const ggml_tensor*t=s.inputs[j];size_t id=ggml_hash_find(&sched->hash_set,t);
            if(id==GGML_HASHSET_FULL||!ggml_bitset_get(sched->hash_set.used,id)||sched->hash_set.keys[id]!=t)throw std::invalid_argument("missing transfer binding");
            int source_id=sched->hv_tensor_backend_ids[id];if(source_id<0||source_id>=sched->n_backends)throw std::invalid_argument("invalid transfer source backend");
            d.source_backends.emplace_back(source_id,sched->backends[source_id]);
            const ggml_tensor*copy=tensor_id_copy(id,s.backend_id,sched->cur_copy);if(!copy)throw std::invalid_argument("null transfer");
            d.inputs.push_back(t);d.copies.push_back(copy);add(t);add(copy);
        }
        p.splits.push_back(std::move(d));
    }
    // Traverse actual sources/views, including allocated transfer tensors. Do not read tensor data.
    for(size_t i=0;i<queue.size();++i){
        const auto*t=queue[i];hs_tensor_descriptor d{};d.identity=t;d.data=t->data;d.buffer=t->buffer;
        if(t->buffer){d.buft=t->buffer->buft;d.buffer_context=t->buffer->context;d.buffer_size=t->buffer->size;d.usage=t->buffer->usage;}
        d.type=t->type;d.op=t->op;d.flags=t->flags;std::copy_n(t->ne,GGML_MAX_DIMS,d.ne.begin());std::copy_n(t->nb,GGML_MAX_DIMS,d.nb.begin());std::copy_n(t->op_params,d.params.size(),d.params.begin());
        for(int k=0;k<GGML_MAX_SRC;++k){d.src[k]=t->src[k];add(t->src[k]);}d.view=t->view_src;d.view_offset=t->view_offs;d.extra=t->extra;add(t->view_src);
        if(t->op==GGML_OP_SET_ROWS||t->op==GGML_OP_CPY||t->view_src)p.blockers|=HS_PLAN_PERSISTENT_WRITE;
        p.tensors.push_back(d);
    }
    // Reject cyclic source/view graphs without recursion or data access.
    std::unordered_map<const ggml_tensor*,int> color;
    for(auto *root:queue){
        if(color[root]==2)continue;std::vector<std::pair<const ggml_tensor*,bool>> stack{{root,false}};
        while(!stack.empty()){
            auto item=stack.back();stack.pop_back();auto*t=item.first;
            if(item.second){color[t]=2;continue;}
            if(color[t]==1)throw std::invalid_argument("cyclic tensor descriptors");if(color[t]==2)continue;
            color[t]=1;stack.push_back({t,true});
            if(t->view_src)stack.push_back({t->view_src,false});
            for(int j=GGML_MAX_SRC-1;j>=0;--j)if(t->src[j])stack.push_back({t->src[j],false});
        }
    }
    return p;
}
extern "C" struct hs_sched_plan * hs_sched_plan_capture(ggml_backend_sched_t s,ggml_cgraph*g){try{return new hs_sched_plan(hs_plan_read(s,g));}catch(...){return nullptr;}}
extern "C" void hs_sched_plan_free(hs_sched_plan*p){delete p;}
extern "C" bool hs_sched_plan_summary(const hs_sched_plan*p,struct hs_plan_summary*out){if(!p||!out)return false;*out={p->instance,p->epoch,p->splits.size(),0,0,p->tensors.size(),p->blockers};for(const auto&s:p->splits){out->nodes+=s.nodes.size();out->transfers+=s.inputs.size();}return true;}
extern "C" enum hs_plan_result hs_sched_plan_compare(ggml_backend_sched_t s,ggml_cgraph*g,const hs_sched_plan*p){
    if(!s||!p||!g)return HS_PLAN_ERROR;if(!s->is_alloc)return HS_PLAN_NOT_ALLOCATED;
    if(p->owner!=s||p->instance!=s->hs_plan_instance||p->epoch!=s->hs_plan_epoch||p->caller!=g)return HS_PLAN_STALE;
    try {auto now=hs_plan_read(s,g);if(!(now==*p))return HS_PLAN_STALE;
        if(now.blockers&(HS_PLAN_CALLBACK|HS_PLAN_PARALLEL_COPIES|HS_PLAN_PERSISTENT_WRITE|HS_PLAN_DEVICE_NONCPU))return HS_PLAN_UNSUPPORTED;
        return HS_PLAN_MATCH_DRY_VETO; // A structural match explicitly never grants execution.
    }catch(...){return HS_PLAN_ERROR;}
}
extern "C" bool hs_sched_plan_arm_dry(ggml_backend_sched_t s,ggml_cgraph*g,const hs_sched_plan*p){
    if(!s||!p)return false;auto result=hs_sched_plan_compare(s,g,p);if(result!=HS_PLAN_MATCH_DRY_VETO&&result!=HS_PLAN_UNSUPPORTED)return false;
    try{auto*copy=new hs_sched_plan(*p);delete s->hs_plan_armed;s->hs_plan_armed=copy;s->hs_plan_result=HS_PLAN_DISABLED;return true;}catch(...){return false;}
}
extern "C" void hs_sched_plan_disarm(ggml_backend_sched_t s){if(s){delete s->hs_plan_armed;s->hs_plan_armed=nullptr;s->hs_plan_result=HS_PLAN_DISABLED;}}
extern "C" enum hs_plan_result hs_sched_plan_last_result(ggml_backend_sched_t s){return s?static_cast<hs_plan_result>(s->hs_plan_result):HS_PLAN_ERROR;}
