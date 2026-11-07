#include "query_head.h"
#include <iostream>
int main(){
 int cases=0;
 for(int qn:{1,2,3,4})for(int storage:{0,1})for(auto mode:{hs_qh::Mode::MQ,hs_qh::Mode::PQ,hs_qh::Mode::QB4,hs_qh::Mode::QH_C,hs_qh::Mode::QH_D,hs_qh::Mode::REPEAT4}){
  ggml_context c;auto*q=tensor(&c,GGML_TYPE_F32,128,qn,8,1);
  if(storage){q->nb[1]=128*8*4;q->nb[2]=128*4;}
  auto*k=tensor(&c,GGML_TYPE_F16,128,257,2,1);auto*v=tensor(&c,GGML_TYPE_F16,257,64,2,1);auto*m=tensor(&c,GGML_TYPE_F32,257,32,1,1);
  auto b=hs_qh::build(&c,mode,q,k,v,m,.125f);cases++;
  if(qn==1||mode==hs_qh::Mode::MQ){assert(b.common_original&&b.out==nullptr);continue;}
  assert(b.out&&b.out->ne[0]==64*8&&b.out->ne[1]==qn);
  assert(b.scores.size()==size_t(mode==hs_qh::Mode::PQ?qn:1));
  if(mode==hs_qh::Mode::QH_C||mode==hs_qh::Mode::QH_D){
   assert(b.scores[0]->ne[1]==1&&b.scores[0]->ne[2]==8*qn&&b.scores[0]->ne[3]==1);
   assert(b.scores[0]->src[0]==k&&b.values[0]->src[0]==v&&!b.copied_kv);
   assert(b.probs[0]->src[1]->ne[2]==(mode==hs_qh::Mode::QH_C?qn:8*qn));
  }
 }
 std::cout<<"DESCRIPTOR_MOCK_ONLY cases="<<cases<<" numerical_compute=0 gpu=0\n";
 return 0;
}
