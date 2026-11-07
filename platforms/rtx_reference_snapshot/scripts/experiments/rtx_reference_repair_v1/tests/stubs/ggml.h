#pragma once
// CPU graph/address test double; does not emulate Q8 quantization or GPU kernels.
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <vector>
#define GGML_ASSERT(x) do{if(!(x))throw std::runtime_error("mock GGML assertion: " #x);}while(0)
enum ggml_type {GGML_TYPE_F32,GGML_TYPE_Q8_0};
struct ggml_context {};
struct ggml_tensor {
 ggml_type type=GGML_TYPE_F32;int64_t ne[4]={1,1,1,1};size_t nb[4]={4,4,4,4};
 std::shared_ptr<std::vector<unsigned char>> storage;size_t offset=0;char name[128]={};
};
inline std::vector<std::unique_ptr<ggml_tensor>> owners;
inline int native_calls=0;
inline ggml_tensor* make(int64_t d,int64_t q,int padding=0){
 auto p=std::make_unique<ggml_tensor>();p->ne[0]=d;p->ne[1]=q;p->nb[1]=size_t(4*d+padding);p->nb[2]=p->nb[1]*q;p->nb[3]=p->nb[2];p->storage=std::make_shared<std::vector<unsigned char>>(p->nb[2]);auto r=p.get();owners.push_back(std::move(p));return r;
}
inline float get(ggml_tensor*t,int64_t i,int64_t j){float v;std::memcpy(&v,t->storage->data()+t->offset+i*t->nb[0]+j*t->nb[1],4);return v;}
inline void put(ggml_tensor*t,int64_t i,int64_t j,float v){std::memcpy(t->storage->data()+t->offset+i*t->nb[0]+j*t->nb[1],&v,4);}
inline const char* ggml_get_name(ggml_tensor*t){return t->name;}
inline void ggml_format_name(ggml_tensor*t,const char*f,...){va_list a;va_start(a,f);std::vsnprintf(t->name,sizeof(t->name),f,a);va_end(a);}
inline ggml_tensor* ggml_view_2d(ggml_context*,ggml_tensor*t,int64_t n0,int64_t n1,size_t nb1,size_t offset){
 auto p=std::make_unique<ggml_tensor>(*t);p->ne[0]=n0;p->ne[1]=n1;p->nb[1]=nb1;p->offset+=offset;auto r=p.get();owners.push_back(std::move(p));return r;
}
inline ggml_tensor* ggml_mul_mat(ggml_context*,ggml_tensor*a,ggml_tensor*b){
 ++native_calls;GGML_ASSERT(a->ne[0]==b->ne[0]);auto r=make(a->ne[1],b->ne[1]);
 for(int64_t j=0;j<b->ne[1];++j)for(int64_t i=0;i<a->ne[1];++i){float v=0;for(int64_t k=0;k<a->ne[0];++k)v+=get(a,k,i)*get(b,k,j);put(r,i,j,v);}
 return r;
}
inline ggml_tensor* ggml_concat(ggml_context*,ggml_tensor*a,ggml_tensor*b,int axis){
 GGML_ASSERT(axis==1&&a->ne[0]==b->ne[0]);auto r=make(a->ne[0],a->ne[1]+b->ne[1]);
 for(int64_t j=0;j<r->ne[1];++j)for(int64_t i=0;i<r->ne[0];++i)put(r,i,j,j<a->ne[1]?get(a,i,j):get(b,i,j-a->ne[1]));
 return r;
}
