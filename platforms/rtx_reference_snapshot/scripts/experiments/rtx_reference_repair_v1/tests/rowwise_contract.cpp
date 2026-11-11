#define HSR_MM_ROLES 7
#include "repair_mm.hpp"
#include <iostream>
int main(){
 ggml_context c;auto*a=make(3,2);a->type=GGML_TYPE_Q8_0;std::strcpy(a->name,"blk.0.attn_q.weight");
 for(int j=0;j<2;j++)for(int i=0;i<3;i++)put(a,i,j,float(i+j+1));
 for(int q=1;q<=4;q++){
  auto*b=make(3,q,8);for(int j=0;j<q;j++)for(int i=0;i<3;i++)put(b,i,j,float(i-j));
  native_calls=0;auto*r=hs_repair_mm::mul_mat(&c,a,b);GGML_ASSERT(native_calls==q);auto*expected=ggml_mul_mat(&c,a,b);
  GGML_ASSERT(r->ne[0]==2&&r->ne[1]==q);for(int j=0;j<q;j++)for(int i=0;i<2;i++)GGML_ASSERT(get(r,i,j)==get(expected,i,j));
 }
 auto*b=make(3,4);hs_scope::active=false;native_calls=0;hs_repair_mm::mul_mat(&c,a,b);GGML_ASSERT(native_calls==1);
 hs_scope::active=true;std::strcpy(a->name,"output.weight");native_calls=0;hs_repair_mm::mul_mat(&c,a,b);GGML_ASSERT(native_calls==1);
 std::strcpy(a->name,"blk.0.attn_q.weight");a->type=GGML_TYPE_F32;bool rejected=false;try{hs_repair_mm::mul_mat(&c,a,b);}catch(const std::runtime_error&){rejected=true;}GGML_ASSERT(rejected);
 std::cout<<"CPP_GRAPH_ADDRESS_CONTRACT_PASS; mock CPU backend only, no Q8/CUDA numerical qualification\n";
}
