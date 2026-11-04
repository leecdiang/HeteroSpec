#include "hs_cuda_audit.h"
namespace {
thread_local const hs_cuda_audit_binding * hs_cuda_audit=nullptr;
thread_local hs_cuda_dispatch_record hs_cuda_pending{};
}
extern "C" const hs_cuda_audit_binding * hs_cuda_exchange_audit(const hs_cuda_audit_binding * next) {
    const auto * previous=hs_cuda_audit;hs_cuda_audit=next;return previous;
}
static bool hs_cuda_audit_active(){return hs_cuda_audit!=nullptr;}
static bool hs_cuda_audit_collecting(){return hs_cuda_audit && hs_cuda_audit->abi==HS_CUDA_AUDIT_ABI && hs_cuda_audit->mode==1 && hs_cuda_audit->record;}
static void hs_cuda_audit_route(ggml_backend_cuda_context & ctx,const ggml_tensor * a,const ggml_tensor * b,const ggml_tensor * out,const char * route) {
    if(!hs_cuda_audit_collecting())return;
    hs_cuda_pending={};hs_cuda_pending.abi=HS_CUDA_AUDIT_ABI;hs_cuda_pending.phase=1;
    hs_cuda_pending.device=ctx.device;hs_cuda_pending.cc=ggml_cuda_info().devices[ctx.device].cc;
    hs_cuda_pending.warp=ggml_cuda_info().devices[ctx.device].warp_size;hs_cuda_pending.route=route;
    hs_cuda_pending.source_digest=HS_CUDA_AUDIT_SOURCE_DIGEST;
    const ggml_tensor * tensors[]={a,b,out};
    for(int j=0;j<3;++j){
        const auto * t=tensors[j];auto & r=hs_cuda_pending.tensors[j];r.type=int(t->type);
        for(int i=0;i<4;++i){r.ne[i]=t->ne[i];r.nb[i]=t->nb[i];}
        auto buffer=t->buffer ? t->buffer : (t->view_src ? t->view_src->buffer : nullptr);
        r.allocated=buffer && t->data;
        if(buffer){r.same_device_buffer=buffer->buft==ggml_backend_cuda_buffer_type(ctx.device);r.host_buffer=ggml_backend_buft_is_host(buffer->buft);}
    }
    hs_cuda_audit->record(hs_cuda_audit->user,&hs_cuda_pending);
}
// Defined in this module; called by mmvq.cu at the selected template launch.
extern "C" void hs_cuda_audit_mmvq(int type,int columns,int small_k,int halve_iters,int fusion,int ids,
    unsigned gx,unsigned gy,unsigned gz,unsigned bx,unsigned by,unsigned bz,unsigned shared_bytes,const uint64_t * arguments,size_t count) {
    if(!hs_cuda_audit_collecting())return;
    auto r=hs_cuda_pending;r.phase=2;r.type=type;r.columns=columns;r.small_k=small_k;r.halve_iters=halve_iters;r.fusion=fusion;r.ids=ids;
    r.grid[0]=gx;r.grid[1]=gy;r.grid[2]=gz;r.block[0]=bx;r.block[1]=by;r.block[2]=bz;r.shared_bytes=shared_bytes;
    r.argument_count=uint32_t(count);
    if(count>24)return;
    for(size_t i=0;i<count;++i)r.arguments[i]=arguments[i];
    hs_cuda_audit->record(hs_cuda_audit->user,&r);
}
