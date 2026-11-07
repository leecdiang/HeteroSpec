#pragma once
// Descriptor-only test double. NO GGML numerical implementation and NO backend.
#include <cstdint>
#include <cstddef>
#include <cassert>
#include <vector>
enum ggml_type {GGML_TYPE_F32,GGML_TYPE_F16};
enum {GGML_PREC_F32=10};
struct ggml_tensor {int64_t ne[4];size_t nb[4];ggml_type type;ggml_tensor *src[2]={};int prec=0;};
struct ggml_context {std::vector<ggml_tensor*> all;~ggml_context(){for(auto*p:all)delete p;}};
inline ggml_tensor* tensor(ggml_context*c,ggml_type t,int64_t a,int64_t b,int64_t h,int64_t k){
 auto*r=new ggml_tensor{{a,b,h,k},{},t};r->nb[0]=t==GGML_TYPE_F32?4:2;
 for(int i=1;i<4;i++) { r->nb[i]=r->nb[i-1]*r->ne[i-1]; }
 c->all.push_back(r); return r;
}
inline bool ggml_is_contiguous(ggml_tensor*t){size_t n=t->type==GGML_TYPE_F32?4:2;
 for(int i=0;i<4;i++){if(t->ne[i]!=1&&t->nb[i]!=n)return false;n*=t->ne[i];}return true;}
inline ggml_tensor* ggml_cont(ggml_context*c,ggml_tensor*t){auto*r=tensor(c,t->type,t->ne[0],t->ne[1],t->ne[2],t->ne[3]);r->src[0]=t;return r;}
inline ggml_tensor* ggml_view_4d(ggml_context*c,ggml_tensor*t,int64_t a,int64_t b,int64_t h,int64_t k,size_t n1,size_t n2,size_t n3,size_t){auto*r=tensor(c,t->type,a,b,h,k);r->nb[1]=n1;r->nb[2]=n2;r->nb[3]=n3;r->src[0]=t;return r;}
inline ggml_tensor* ggml_reshape_4d(ggml_context*c,ggml_tensor*t,int64_t a,int64_t b,int64_t h,int64_t k){assert(ggml_is_contiguous(t));assert(a*b*h*k==t->ne[0]*t->ne[1]*t->ne[2]*t->ne[3]);auto*r=tensor(c,t->type,a,b,h,k);r->src[0]=t;return r;}
inline ggml_tensor* ggml_repeat_4d(ggml_context*c,ggml_tensor*t,int64_t a,int64_t b,int64_t h,int64_t k){assert(a%t->ne[0]==0&&b%t->ne[1]==0&&h%t->ne[2]==0&&k%t->ne[3]==0);auto*r=tensor(c,t->type,a,b,h,k);r->src[0]=t;return r;}
inline ggml_tensor* ggml_mul_mat(ggml_context*c,ggml_tensor*a,ggml_tensor*b){assert(a->ne[0]==b->ne[0]&&b->ne[2]%a->ne[2]==0&&b->ne[3]%a->ne[3]==0);auto*r=tensor(c,GGML_TYPE_F32,a->ne[1],b->ne[1],b->ne[2],b->ne[3]);r->src[0]=a;r->src[1]=b;return r;}
inline void ggml_mul_mat_set_prec(ggml_tensor*t,int p){t->prec=p;}
inline ggml_tensor* ggml_soft_max_ext(ggml_context*c,ggml_tensor*s,ggml_tensor*m,float,float){assert(s->ne[0]==m->ne[0]&&m->ne[1]>=s->ne[1]&&s->ne[2]%m->ne[2]==0&&s->ne[3]%m->ne[3]==0);auto*r=tensor(c,s->type,s->ne[0],s->ne[1],s->ne[2],s->ne[3]);r->src[0]=s;r->src[1]=m;return r;}
inline ggml_tensor* ggml_permute(ggml_context*c,ggml_tensor*t,int a,int b,int h,int k){int p[4]={a,b,h,k};auto*r=tensor(c,t->type,1,1,1,1);for(int i=0;i<4;i++){r->ne[p[i]]=t->ne[i];r->nb[p[i]]=t->nb[i];}r->src[0]=t;return r;}
inline ggml_tensor* ggml_cont_2d(ggml_context*c,ggml_tensor*t,int64_t a,int64_t b){assert(a*b==t->ne[0]*t->ne[1]*t->ne[2]*t->ne[3]);auto*r=tensor(c,t->type,a,b,1,1);r->src[0]=t;return r;}
inline ggml_tensor* ggml_concat(ggml_context*c,ggml_tensor*a,ggml_tensor*b,int dim){assert(dim==1&&a->ne[0]==b->ne[0]);auto*r=tensor(c,a->type,a->ne[0],a->ne[1]+b->ne[1],1,1);r->src[0]=a;r->src[1]=b;return r;}
