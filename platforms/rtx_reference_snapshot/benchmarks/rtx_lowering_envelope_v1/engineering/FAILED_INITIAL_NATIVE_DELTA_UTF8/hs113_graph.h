#pragma once
#include "ggml.h"
#include <cstring>
#include <stdexcept>
#include <string>
namespace hs113 {
inline void require(bool ok,const char * s){if(!ok)throw std::runtime_error(s);}
struct Result { ggml_tensor * stage[3];ggml_tensor * ordinary;bool common; };
inline void geometry(ggml_tensor *q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m){
    require(q&&k&&v&&m,"nonempty Q/K/V/mask required");
    require(q->type==GGML_TYPE_F32&&k->type==GGML_TYPE_F16&&v->type==GGML_TYPE_F16&&m->type==GGML_TYPE_F32,"inherited dtypes required; no implicit conversion");
    require((q->ne[0]==64||q->ne[0]==128)&&q->ne[1]>=1&&q->ne[1]<=4&&q->ne[2]==32&&q->ne[3]==1,"admitted Q domain");
    require(k->ne[0]==q->ne[0]&&k->ne[2]>0&&q->ne[2]%k->ne[2]==0&&k->ne[3]==1,"single-owner integral GQA");
    require(v->ne[0]==k->ne[1]&&v->ne[1]==q->ne[0]&&v->ne[2]==k->ne[2]&&v->ne[3]==1,"inherited V geometry");
    require(m->ne[0]==k->ne[1]&&m->ne[1]>=q->ne[1]&&m->ne[2]==1&&m->ne[3]==1,"query mask geometry");
    require(q->nb[0]==4&&k->nb[0]==2&&v->nb[0]==2&&m->nb[0]==4,"supported inner strides");
}
inline ggml_tensor * logical(ggml_context *ctx,ggml_tensor*t,int layout,int64_t q,int64_t H){
    if(layout==1)return ggml_cont(ctx,ggml_permute(ctx,t,0,3,2,1)); // QB
    if(layout>=2)return ggml_reshape_4d(ctx,ggml_cont(ctx,t),t->ne[0],q,H,1);
    return ggml_cont(ctx,t);
}
// Layout 0=MQ,1=QB,2=QH_C,3=QH_D,4=PQ. q1 delegates here.
inline Result build(ggml_context*ctx,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*mask,int layout,float scale,const unsigned char *qkp=nullptr,const unsigned char *smp=nullptr,const unsigned char *avp=nullptr){
    geometry(q,k,v,mask);require(layout>=0&&layout<=4,"unknown concrete layout");
    const int64_t width=q->ne[1],H=q->ne[2];bool common=width==1;
    int l=common?0:layout;ggml_tensor *sum[3]={nullptr,nullptr,nullptr};
    for(int64_t j=0;j<(l==4?width:1);++j){
        auto *qi=q,*mi=mask;
        if(l==4){qi=ggml_view_4d(ctx,q,q->ne[0],1,H,1,q->nb[1],q->nb[2],q->nb[3],j*q->nb[1]);mi=ggml_view_2d(ctx,mask,mask->ne[0],1,mask->nb[1],j*mask->nb[1]);}
        if(l==1){qi=ggml_view_4d(ctx,q,q->ne[0],1,H,width,q->nb[1],q->nb[2],q->nb[1],0);mi=ggml_view_4d(ctx,mask,mask->ne[0],1,1,width,mask->nb[1],mask->nb[1],mask->nb[1],0);}
        if(l==2||l==3){
            // This CONT is an executable packing node for inherited permuted Q.
            qi=ggml_reshape_4d(ctx,ggml_cont(ctx,q),q->ne[0],1,H*width,1);ggml_set_name(qi,"hs113_QH_packed_Q");
            auto *mq=ggml_view_2d(ctx,mask,mask->ne[0],width,mask->nb[1],0);
            mi=ggml_reshape_4d(ctx,ggml_cont(ctx,mq),mask->ne[0],1,width,1);
            if(l==3)mi=ggml_repeat_4d(ctx,mi,mask->ne[0],1,H*width,1);
            ggml_set_name(mi,l==2?"hs113_QH_compact_mask":"hs113_QH_dense_mask");
        }
        auto *a=ggml_mul_mat(ctx,k,qi);ggml_mul_mat_set_prec(a,GGML_PREC_F32);if(qkp)std::memcpy(a->op_params,qkp,GGML_MAX_OP_PARAMS);
        auto *b=ggml_soft_max_ext(ctx,a,mi,scale,0.0f);if(smp)std::memcpy(b->op_params,smp,GGML_MAX_OP_PARAMS);
        float bias;std::memcpy(&bias,(char*)b->op_params+4,4);require(bias==0.0f,"ALiBi excluded");
        auto *c=ggml_mul_mat(ctx,v,b);if(avp)std::memcpy(c->op_params,avp,GGML_MAX_OP_PARAMS);
        ggml_tensor *raw[]={a,b,c};
        for(int s=0;s<3;s++){
            auto *t=logical(ctx,raw[s],l==4?0:l,l==4?1:width,H);
            sum[s]=sum[s]?ggml_concat(ctx,sum[s],t,1):t;
        }
    }
    auto *out=ggml_permute(ctx,sum[2],0,2,1,3);out=ggml_cont_2d(ctx,out,v->ne[1]*H,width);
    ggml_set_name(out,"hs113_ordinary_output");return {{sum[0],sum[1],sum[2]},out,common};
}
inline int layout(const std::string &s){if(s=="MQ")return 0;if(s=="QB")return 1;if(s=="QH_C")return 2;if(s=="QH_D")return 3;if(s=="PQ")return 4;throw std::runtime_error("invalid native layout");}
}
