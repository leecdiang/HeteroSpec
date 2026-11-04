#include "loop4_tensor.hpp"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-alloc.h"
#include <iostream>
#include <vector>
int main(){
 int n=0;auto check=[&](bool b){++n;if(!b)throw std::runtime_error("CPU isolation check");};
 auto backend=ggml_backend_cpu_init();auto ctx=ggml_init({1024*1024,nullptr,true});
 auto w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,32,8),x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,32,8);
 auto out=ggml_mul_mat(ctx,w,x);auto graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,out);
 auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);check(buffer!=nullptr);
 check(ggml_backend_dev_supports_op(ggml_backend_get_device(backend),out));
 auto before_mark=ggml_backend_graph_plan_create(backend,graph);check(before_mark!=nullptr);
 hs_loop4::mark(out);hs_loop4::require(w,x,out);
 check(ggml_backend_graph_plan_compute(backend,before_mark)==GGML_STATUS_FAILED);
 ggml_backend_graph_plan_free(backend,before_mark);
 check(!ggml_backend_dev_supports_op(ggml_backend_get_device(backend),out));
 check(!ggml_backend_supports_op(backend,out));
 check(ggml_backend_graph_compute(backend,graph)==GGML_STATUS_FAILED);
 check(ggml_backend_graph_plan_create(backend,graph)==nullptr);
 auto legacy=ggml_graph_plan(graph,1,nullptr);std::vector<uint8_t> work(legacy.work_size);legacy.work_data=work.data();
 check(ggml_graph_compute(graph,&legacy)==GGML_STATUS_FAILED);
 check(ggml_graph_compute_with_ctx(ctx,graph,1)==GGML_STATUS_FAILED);
 auto huge=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,65536,2097152);
 auto huge_x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,65536,5);auto huge_out=ggml_mul_mat(ctx,huge,huge_x);hs_loop4::mark(huge_out);
 bool rejected=false;try{hs_loop4::require(huge,huge_x,huge_out);}catch(const std::overflow_error&){rejected=true;}check(rejected);
 ggml_backend_buffer_free(buffer);ggml_free(ctx);ggml_backend_free(backend);
 std::cout<<"ACTUAL_CPU_WRONG_BACKEND_REJECTION_CHECKS="<<n<<"\n";
}
