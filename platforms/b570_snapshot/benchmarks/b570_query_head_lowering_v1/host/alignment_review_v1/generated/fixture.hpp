#pragma once
#include "query_head.h"
#include "nlohmann/json.hpp"
#include <algorithm>
#include <iostream>
#include <utility>
using json=nlohmann::ordered_json;
static void fixture_need(bool b,const char*m){if(!b)throw std::runtime_error(m);}
static void walk(ggml_tensor*t,std::vector<ggml_tensor*>&v){if(!t||std::find(v.begin(),v.end(),t)!=v.end())return;for(auto*s:t->src)walk(s,v);v.push_back(t);}
static hs_qh::Built common(ggml_context*c,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m){hs_qh::Built b;b.common_original=true;
 auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);auto*p=ggml_soft_max_ext(c,s,m,float(1/std::sqrt(128.0)),0);auto*a=ggml_mul_mat(c,v,p);
 b.scores={s};b.probs={p};b.values={a};auto*r=ggml_permute(c,a,0,2,1,3);b.out=ggml_cont_2d(c,r,128*q->ne[2],q->ne[1]);return b;}
struct Graph{ggml_context*c;ggml_tensor*base,*q,*k,*v,*m;hs_qh::Built built;ggml_cgraph*g;std::vector<ggml_tensor*>nodes;std::vector<std::pair<ggml_tensor*,size_t>>slabs;};
static hs_qh::Mode mode(std::string s){if(s=="QB4")return hs_qh::Mode::QB4;if(s=="MQ")return hs_qh::Mode::MQ;if(s=="PQ")return hs_qh::Mode::PQ;if(s=="QH_C")return hs_qh::Mode::QH_C;if(s=="QH_D")return hs_qh::Mode::QH_D;if(s=="REPEAT4")return hs_qh::Mode::REPEAT4;throw std::runtime_error("unplanned GPU mode");}
static Graph graph(json cell,std::string name,int q_offset=32,bool relocate_pq_mask=false){auto shape=cell["geometry"];int q=shape["q"],n=shape["n"],h=shape["h"],hk=shape["hk"];
 fixture_need(shape["d"]==128&&shape["dv"]==128&&shape["storage"]=="permuted"&&q>=1&&q<=4&&(n==63||n==257)&&h==8&&(hk==8||hk==2),"S1 frozen shape");
 ggml_init_params init{16*1024*1024,nullptr,true};Graph x{};x.c=ggml_init(init);fixture_need(x.c,"metadata context");
 x.base=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,q_offset/4+128*h*q);x.q=ggml_view_4d(x.c,x.base,128,q,h,1,512*h,512,512*h*q,q_offset);
 x.k=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,128,n,hk,1);x.v=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,n,128,hk,1);x.m=ggml_new_tensor_4d(x.c,GGML_TYPE_F32,n,32,1,1);
 x.built=hs_qh::build(x.c,mode(name),x.q,x.k,x.v,x.m,float(1/std::sqrt(128.0)));if(x.built.common_original)x.built=common(x.c,x.q,x.k,x.v,x.m);
 fixture_need(q_offset==0||q_offset==32,"declared Q storage offset");
 if(relocate_pq_mask&&q>1&&name=="PQ")for(int j=0;j<q;++j){
  auto*old=x.built.probs[j]->src[1];auto*slab=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,n);
  auto*mi=ggml_view_4d(x.c,slab,n,1,1,1,old->nb[1],old->nb[2],old->nb[3],0);
  x.slabs.push_back({slab,size_t(j)*x.m->nb[1]});x.built.probs[j]->src[1]=mi;
 }
 x.g=ggml_new_graph(x.c);ggml_build_forward_expand(x.g,x.built.out);walk(x.built.out,x.nodes);return x;}
