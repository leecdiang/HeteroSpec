#pragma once
// Same arithmetic builder as the frozen diagnostic: Q0 and PQ slabs only.
#include "query_head.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
using json=nlohmann::ordered_json;
inline void need(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
constexpr const char*RUN_ID="b570-supervised-numerical-v4-20261016-01";
inline bool executable(ggml_tensor*t){return t->op!=GGML_OP_NONE&&t->op!=GGML_OP_VIEW&&t->op!=GGML_OP_RESHAPE&&t->op!=GGML_OP_PERMUTE&&t->op!=GGML_OP_TRANSPOSE;}
inline void walk(ggml_tensor*t,std::vector<ggml_tensor*>&v){if(!t||std::find(v.begin(),v.end(),t)!=v.end())return;for(auto*s:t->src)walk(s,v);v.push_back(t);}
inline json meta(ggml_tensor*t){return {{"op",ggml_op_name(t->op)},{"type",ggml_type_name(t->type)},
 {"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}},{"nb",{t->nb[0],t->nb[1],t->nb[2],t->nb[3]}},
 {"view_offset",t->view_offs},{"op_parameters",{t->op_params[0],t->op_params[1]}},{"bytes",ggml_nbytes(t)}};}
inline hs_qh::Mode mode(const std::string&s){
 if(s=="MQ")return hs_qh::Mode::MQ;if(s=="PQ")return hs_qh::Mode::PQ;
 if(s=="QH_C")return hs_qh::Mode::QH_C;if(s=="QH_D")return hs_qh::Mode::QH_D;
 if(s=="REPEAT4")return hs_qh::Mode::REPEAT4;throw std::runtime_error("unplanned mode");}
inline hs_qh::Built common(ggml_context*c,ggml_tensor*q,ggml_tensor*k,ggml_tensor*v,ggml_tensor*m){
 hs_qh::Built b;b.common_original=true;auto*s=ggml_mul_mat(c,k,q);ggml_mul_mat_set_prec(s,GGML_PREC_F32);
 auto*p=ggml_soft_max_ext(c,s,m,float(1/std::sqrt(128.0)),0);auto*a=ggml_mul_mat(c,v,p);
 b.scores={s};b.probs={p};b.values={a};auto*r=ggml_permute(c,a,0,2,1,3);
 b.out=ggml_cont_2d(c,r,128*q->ne[2],q->ne[1]);return b;}
struct Graph{
 ggml_context*c;ggml_tensor*base,*q,*k,*v,*m;hs_qh::Built b;ggml_cgraph*g;
 std::vector<ggml_tensor*>nodes,all;std::vector<std::pair<ggml_tensor*,size_t>>slabs;
 int id(ggml_tensor*t)const{return t?int(std::find(all.begin(),all.end(),t)-all.begin()):-1;}
};
inline Graph graph(const json&cell,const std::string&name){
 auto sh=cell.at("geometry");int nq=sh.at("q"),n=sh.at("n"),h=sh.at("h"),hk=sh.at("hk");
 need(sh.at("d")==128&&sh.at("dv")==128&&sh.at("storage")=="permuted"&&h==8&&(hk==8||hk==2)&&nq>=1&&nq<=4&&(n==63||n==257),"fixed shape");
 need(cell.at("mask")=="causal"&&cell.at("pattern")=="dyadic","fixed input family");
 Graph x{};ggml_init_params init{16*1024*1024,nullptr,true};x.c=ggml_init(init);need(x.c,"context");
 x.base=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,128*h*nq);
 x.q=ggml_view_4d(x.c,x.base,128,nq,h,1,512*h,512,512*h*nq,0);
 x.k=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,128,n,hk,1);
 x.v=ggml_new_tensor_4d(x.c,GGML_TYPE_F16,n,128,hk,1);
 x.m=ggml_new_tensor_4d(x.c,GGML_TYPE_F32,n,32,1,1);
 x.b=hs_qh::build(x.c,mode(name),x.q,x.k,x.v,x.m,float(1/std::sqrt(128.0)));
 if(x.b.common_original)x.b=common(x.c,x.q,x.k,x.v,x.m);
 if(nq>1&&name=="PQ")for(int j=0;j<nq;++j){
  auto*old=x.b.probs[j]->src[1];auto*slab=ggml_new_tensor_1d(x.c,GGML_TYPE_F32,n);
  auto*mi=ggml_view_4d(x.c,slab,n,1,1,1,old->nb[1],old->nb[2],old->nb[3],0);
  x.slabs.push_back({slab,size_t(j)*x.m->nb[1]});x.b.probs[j]->src[1]=mi;
 }
 x.g=ggml_new_graph(x.c);ggml_build_forward_expand(x.g,x.b.out);walk(x.b.out,x.nodes);
 for(auto*t=ggml_get_first_tensor(x.c);t;t=ggml_get_next_tensor(x.c,t))x.all.push_back(t);
 return x;
}
inline json descriptor(const Graph&x){
 json ts=json::array(),order=json::array(),stages=json::array(),slabs=json::array();
 for(auto*t:x.all){auto z=meta(t);z["id"]=x.id(t);z["view_root"]=x.id(t->view_src);z["src"]=json::array();z["executable"]=executable(t);
  for(auto*s:t->src)if(s)z["src"].push_back(x.id(s));ts.push_back(z);}
 for(int i=0;i<ggml_graph_n_nodes(x.g);++i)order.push_back(x.id(ggml_graph_node(x.g,i)));
 for(size_t i=0;i<x.b.scores.size();++i)stages.push_back({{"part",i},{"QK",x.id(x.b.scores[i])},{"softmax",x.id(x.b.probs[i])},{"AV",x.id(x.b.values[i])}});
 for(auto&s:x.slabs)slabs.push_back({{"tensor",x.id(s.first)},{"source_mask_byte_offset",s.second},{"bytes",ggml_nbytes(s.first)}});
 return {{"tensors",ts},{"order",order},{"Q_base",x.id(x.base)},{"Q",x.id(x.q)},{"K",x.id(x.k)},{"V",x.id(x.v)},{"mask",x.id(x.m)},
  {"stages",stages},{"final",x.id(x.b.out)},{"slabs",slabs},{"common_original",x.b.common_original},
  {"packed_q",x.b.packed_q},{"dense_mask",x.b.dense_mask},{"copied_kv",x.b.copied_kv}};
}
inline void validate_request(const json&r){
 need(r.at("run_id")==RUN_ID&&r.at("study")=="b570-aligned-numerical-v2","run identity");
 need(r.at("execution_binding_sha256").get<std::string>().size()==64,"execution binding");
 need(r.at("required_alignment_bytes").is_number_unsigned()||r.at("required_alignment_bytes").is_number_integer(),"alignment type");
 need(r.at("required_alignment_bytes").get<size_t>()>0,"alignment condition");
 need(r.at("kind")=="census"||r.at("kind")=="graph","kind");
 if(r.at("kind")=="census")need(r.at("cells").size()==16,"complete census");
 else{mode(r.at("mode"));need(r.at("repeat")==0||r.at("repeat")==1,"two process repeats");}
}
inline std::vector<std::pair<ggml_tensor*,std::vector<char>>> input_bytes(Graph&g,const json&r){
 auto sh=r.at("cell").at("geometry");int q=sh.at("q"),n=sh.at("n"),h=sh.at("h"),hk=sh.at("hk");
 std::ifstream f(r.at("input").get<std::string>(),std::ios::binary);int hdr[7];f.read((char*)hdr,sizeof(hdr));
 need(bool(f)&&hdr[0]==q&&hdr[1]==n&&hdr[2]==h&&hdr[3]==hk&&hdr[4]==1&&hdr[5]==0&&hdr[6]==0,"input descriptor");
 std::vector<std::pair<ggml_tensor*,std::vector<char>>> b;
 for(auto*t:{g.base,g.k,g.v,g.m}){std::vector<char>a(ggml_nbytes(t));f.read(a.data(),a.size());need(bool(f),"complete input");b.push_back({t,std::move(a)});}
 need(f.peek()==EOF,"input trailing bytes");
 for(auto&s:g.slabs)b.push_back({s.first,std::vector<char>(b[3].second.begin()+s.second,b[3].second.begin()+s.second+ggml_nbytes(s.first))});
 return b;
}
