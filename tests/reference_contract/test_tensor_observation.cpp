#include "tensor_observation.hpp"
#include "native_cuda_scope.hpp"
#include "ggml-alloc.h"
#include "ggml-cpu.h"
#include <iostream>
using namespace hs_reference_batching;
int main(){
 int n=0;auto check=[&](bool x){++n;if(!x)throw std::runtime_error("observation check "+std::to_string(n));};
 auto backend=ggml_backend_cpu_init();check(backend!=nullptr);
 auto * ctx=ggml_init({1024*1024,nullptr,true});check(ctx!=nullptr);
 auto * tensor=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,32,4,3,1);
 auto * view=ggml_view_4d(ctx,tensor,32,2,3,1,tensor->nb[1],tensor->nb[2],tensor->nb[3],0);
 auto before=observe_tensor(tensor);check(!before.allocated);check(before.shape[2]==3);
 auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);check(buffer!=nullptr);
 auto actual=observe_tensor(tensor);check(actual.allocated && actual.host);check(actual.device_type==-1 || actual.device_type==GGML_BACKEND_DEVICE_TYPE_CPU);
 check(actual.shape==std::array<int64_t,4>{32,4,3,1});check(actual.strides[2]==tensor->nb[2]);
 check(!(actual==before));check(observe_tensor(view).view);check(observe_tensor(view).allocated);
 check(!resident_on(tensor,ggml_backend_buffer_get_type(buffer)));check(!resident_on(tensor,nullptr));
 check(!observe_tensor(nullptr).allocated);
 {NativeCudaAuditScope absent;}
 bool rejected=false;try{NativeCudaAuditScope absent(true);}catch(const std::runtime_error&){rejected=true;}
 check(rejected);
 ggml_backend_buffer_free(buffer);ggml_free(ctx);ggml_backend_free(backend);
 std::cout<<"real CPU tensor observation checks: "<<n<<"\n";
}
