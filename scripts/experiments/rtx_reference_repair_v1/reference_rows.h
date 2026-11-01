#pragma once
// Experimental graph repair, not a floating-point equivalence theorem.
// Independent rows call the existing single-column MUL_MAT path. Numeric
// backend libraries are unchanged; actual correspondence must be qualified.
#include "ggml.h"
#include "hs_scope.h"
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <set>
#include <sstream>
namespace hs_repair_rows {
inline const std::set<std::string>& groups() {
    static const std::set<std::string> value=[](){
        std::set<std::string> s;const char* p=std::getenv("HS_REPAIR_ROWS");
        if(!p || !*p || std::string(p)=="off")return s;
        std::stringstream in(p);std::string k;
        while(std::getline(in,k,',')){
            if(k!="qkv"&&k!="attn_out"&&k!="ffn"&&k!="lm_head")
                throw std::runtime_error("invalid process-fixed row-repair family");
            s.insert(k);
        }return s;
    }();return value;
}
inline bool selected(const char* n) {
    const auto& g=groups();std::string s=n?n:"";
    if(g.count("qkv") && (s.find(".attn_q.weight")!=s.npos || s.find(".attn_k.weight")!=s.npos || s.find(".attn_v.weight")!=s.npos))return true;
    if(g.count("attn_out")&&s.find(".attn_output.weight")!=s.npos)return true;
    if(g.count("ffn")&&(s.find(".ffn_gate.weight")!=s.npos||s.find(".ffn_up.weight")!=s.npos||s.find(".ffn_down.weight")!=s.npos))return true;
    return g.count("lm_head")&&s=="output.weight";
}
inline ggml_tensor* mul_mat(ggml_context* ctx,ggml_tensor* a,ggml_tensor* b) {
    // R and draft keep original graph arithmetic. Policy is immutable per process.
    if(!hs_scope::active || !selected(ggml_get_name(a)) || b->ne[1]==1)return ggml_mul_mat(ctx,a,b);
    if(a->ne[2]!=1||a->ne[3]!=1||b->ne[2]!=1||b->ne[3]!=1||b->type!=GGML_TYPE_F32||b->nb[0]!=sizeof(float)||b->ne[1]>4||a->ne[0]!=b->ne[0])
        throw std::runtime_error("selected row repair outside audited 2D q<=4/F32 input domain");
    ggml_tensor* out=nullptr;
    for(int64_t i=0;i<b->ne[1];i++){
        auto* row=ggml_view_2d(ctx,b,b->ne[0],1,b->nb[1],size_t(i)*b->nb[1]);
        auto* part=ggml_mul_mat(ctx,a,row);
        ggml_format_name(part,"rr-%s-%lld",ggml_get_name(a),(long long)i);
        out=out?ggml_concat(ctx,out,part,1):part;
    }
    return out;
}

// Propagate a caller's explicit accumulation precision to the generated leaves.
// The leaves carry an internal name; root names may be overwritten by graph cb.
inline bool row_tree(ggml_tensor* t) {
    if(t->op==GGML_OP_MUL_MAT)return std::string(ggml_get_name(t)).rfind("rr-",0)==0;
    return t->op==GGML_OP_CONCAT && t->src[0]&&t->src[1]&&row_tree(t->src[0])&&row_tree(t->src[1]);
}
inline void set_prec(ggml_tensor* t,enum ggml_prec p) {
    if(t->op==GGML_OP_CONCAT && row_tree(t)) {set_prec(t->src[0],p);set_prec(t->src[1],p);}
    else ggml_mul_mat_set_prec(t,p);
}
}
