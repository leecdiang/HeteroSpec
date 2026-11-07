#include "transaction_contract.h"
// CPU graph metadata only. No backend discovery, model loader, compute, or Vulkan.
#include "local_attention.h"
#include <iostream>
#include <vector>
#include <functional>
void check(bool x){if(!x)throw std::runtime_error("CPU graph contract failure");}
int main(){ggml_init_params p{32*1024*1024,nullptr,true};auto*c=ggml_init(p);check(c);int checks=0;
for(int heads:{8,32})for(int kvheads:{1,8}){if(heads%kvheads)continue;
auto*raw=ggml_new_tensor_3d(c,GGML_TYPE_F32,128,heads,2);auto*q=ggml_permute(c,raw,0,2,1,3);
auto*k=ggml_new_tensor_4d(c,GGML_TYPE_F16,128,256,kvheads,1);auto*v=ggml_new_tensor_4d(c,GGML_TYPE_F16,256,128,kvheads,1);auto*m=ggml_new_tensor_4d(c,GGML_TYPE_F32,256,32,1,1);
for(int layout:{1,2}){auto*out=b570_local_attention(c,layout,q,k,v,m,.125f);check(out->ne[0]==128*heads&&out->ne[1]==2);++checks;
std::vector<ggml_tensor*>nodes;std::function<void(ggml_tensor*)>walk=[&](ggml_tensor*t){if(!t)return;for(auto*n:nodes)if(n==t)return;nodes.push_back(t);for(auto*s:t->src)walk(s);};walk(out);
int soft=0;for(auto*t:nodes)if(t->op==GGML_OP_SOFT_MAX){++soft;auto*mask=t->src[1];check(mask->ne[0]==256&&mask->ne[1]==1&&ggml_is_contiguous(mask));if(layout==2)check(mask->ne[3]==2&&mask->nb[3]==m->nb[1]);else check(mask->view_offs==0||mask->view_offs==m->nb[1]);++checks;}check(soft==(layout==1?2:1));++checks;}
check(b570_local_attention(c,0,q,k,v,m,.125f)==nullptr);++checks;auto*q1=ggml_view_4d(c,q,128,1,heads,1,q->nb[1],q->nb[2],q->nb[3],0);check(b570_local_attention(c,2,q1,k,v,m,.125f)==nullptr);++checks;
auto*bad=ggml_new_tensor_4d(c,GGML_TYPE_F32,256,2,2,1);bool rejected=false;try{b570_local_attention(c,2,q,k,v,bad,.125f);}catch(const std::runtime_error&){rejected=true;}check(rejected);++checks;}
for(int initial:{126,127})for(bool eog:{false,true}){std::vector<int>out(initial,1);std::vector<bool>flags(initial,false);bool done=b570_commit(out,flags,eog?128009:2,128,eog);check(done==(eog||initial==127));++checks;if(done){bool rejected=false;try{b570_commit(out,flags,3,128,false);}catch(const std::runtime_error&){rejected=true;}check(rejected);++checks;}}
check(b570_keep(100,0)==101&&b570_keep(100,1)==102);++checks;bool rejected=false;try{b570_keep(100,2);}catch(const std::runtime_error&){rejected=true;}check(rejected);++checks;
ggml_free(c);std::cout<<"PASS CPU graph structure checks="<<checks<<" model/GPU forwards=0\n";}
