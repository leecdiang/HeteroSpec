#pragma once
#include "ggml.h"
#include <cmath>
#include <stdexcept>
#include <vector>

// Graph prototype. Not a device-support predicate or a numerical certificate.
// Inputs AFTER native positional processing/permutations:
// Q[d,q,H,1], K[d,n,Hkv,1], V[n,dv,Hkv,1], mask[n,>=q,1,1].
namespace hs_qh {
enum class Mode { MQ, PQ, QB4, QH_C, QH_D, REPEAT4 };
struct Built {
    ggml_tensor *out=nullptr;
    std::vector<ggml_tensor*> scores, probs, values;
    bool common_original=false, packed_q=false, dense_mask=false, copied_kv=false;
};
inline void require(bool b, const char *m) { if (!b) throw std::runtime_error(m); }
inline Built build(ggml_context *ctx, Mode mode, ggml_tensor *q, ggml_tensor *k,
                   ggml_tensor *v, ggml_tensor *mask, float scale) {
    require(ctx && q && k && v && mask, "null input");
    const int64_t d=q->ne[0], nq=q->ne[1], h=q->ne[2], n=k->ne[1], hk=k->ne[2], dv=v->ne[1];
    require(d>0 && d<=256 && dv>0 && dv<=256 && nq>0 && nq<=4 && n>=nq && n<=4096 &&
        h>0 && h<=128 && hk>0 && hk<=h && h%hk==0, "extent/GQA domain");
    require(q->ne[3]==1 && k->ne[3]==1 && v->ne[3]==1 && k->ne[0]==d &&
        v->ne[0]==n && v->ne[2]==hk, "single sequence K/V mapping");
    require(q->type==GGML_TYPE_F32 && k->type==GGML_TYPE_F16 && v->type==GGML_TYPE_F16 &&
        mask->type==GGML_TYPE_F32 && mask->ne[0]==n && mask->ne[1]>=nq &&
        mask->ne[2]==1 && mask->ne[3]==1 && mask->nb[0]==4 && mask->nb[1]>=size_t(4*n), "dtype/mask");
    const bool compact=q->nb[0]==4 && q->nb[1]==size_t(4*d) && q->nb[2]==size_t(4*d*nq);
    const bool permuted=q->nb[0]==4 && q->nb[1]==size_t(4*d*h) && q->nb[2]==size_t(4*d);
    require(compact || permuted, "unsupported Q strides; do not fake a contiguous view");
    require(std::isfinite(scale) && scale>0, "scale");
    Built b;
    if (nq==1 || mode==Mode::MQ) {
        b.common_original=true; return b; // CALLER MUST EXECUTE ORIGINAL CHAIN, not mark this PASS.
    }
    auto chain=[&](ggml_tensor *qi,ggml_tensor *ki,ggml_tensor *vi,ggml_tensor *mi) {
        auto *s=ggml_mul_mat(ctx,ki,qi); ggml_mul_mat_set_prec(s,GGML_PREC_F32);
        if (mode==Mode::QH_D) {
            mi=ggml_repeat_4d(ctx,mi,n,1,h*nq,1); b.dense_mask=true;
        }
        auto *p=ggml_soft_max_ext(ctx,s,mi,scale,0.0f);
        auto *a=ggml_mul_mat(ctx,vi,p); // Preserve inherited AV precision selection.
        b.scores.push_back(s); b.probs.push_back(p); b.values.push_back(a);
        return a;
    };
    auto finish=[&](ggml_tensor *a) {
        auto *p=ggml_permute(ctx,a,0,2,1,3);
        return ggml_cont_2d(ctx,p,p->ne[0]*p->ne[1],p->ne[2]*p->ne[3]);
    };
    if (mode==Mode::PQ) {
        for (int64_t j=0;j<nq;++j) {
            auto *qi=ggml_view_4d(ctx,q,d,1,h,1,q->nb[1],q->nb[2],q->nb[3],size_t(j)*q->nb[1]);
            auto *mi=ggml_view_4d(ctx,mask,n,1,1,1,mask->nb[1],mask->nb[2],mask->nb[3],size_t(j)*mask->nb[1]);
            auto *col=finish(chain(qi,k,v,mi));
            b.out=b.out?ggml_concat(ctx,b.out,col,1):col;
        }
        return b;
    }
    if (mode==Mode::QB4 || mode==Mode::REPEAT4) {
        auto *qi=ggml_view_4d(ctx,q,d,1,h,nq,q->nb[1],q->nb[2],q->nb[1],0);
        auto *mi=ggml_view_4d(ctx,mask,n,1,1,nq,mask->nb[1],mask->nb[2],mask->nb[1],0);
        auto *ki=k,*vi=v;
        if (mode==Mode::REPEAT4) {
            ki=ggml_repeat_4d(ctx,k,d,n,hk,nq); vi=ggml_repeat_4d(ctx,v,n,dv,hk,nq);
            b.copied_kv=true; // Charge BOTH actual repeat operations and allocator liveness.
        }
        b.out=finish(chain(qi,ki,vi,mi)); return b;
    }
    require(mode==Mode::QH_C || mode==Mode::QH_D, "mode");
    // Physical r=h*q+j requires d-fast, then query, then head ordering.
    auto *qc=ggml_is_contiguous(q)?q:ggml_cont(ctx,q);
    b.packed_q=qc!=q;
    auto *qi=ggml_reshape_4d(ctx,qc,d,1,h*nq,1);
    // compact head mask: mask[r % q] selects original logical query j.
    auto *mi=ggml_view_4d(ctx,mask,n,1,nq,1,mask->nb[1],mask->nb[1],mask->nb[3],0);
    auto *a=chain(qi,k,v,mi); // K/V objects remain the identical source objects.
    auto *ac=ggml_is_contiguous(a)?a:ggml_cont(ctx,a);
    auto *restored=ggml_reshape_4d(ctx,ac,dv,nq,h,1);
    b.out=finish(restored); return b;
}
} // namespace hs_qh
