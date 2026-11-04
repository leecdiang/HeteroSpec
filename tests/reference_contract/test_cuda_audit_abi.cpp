// CPU ABI fixture for the exact instrumentation body. CUDA selection/launch
// helpers are not executed or claimed compiled by this fixture.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-backend-impl.h"
#include "ggml-alloc.h"
#include "ggml-cpu.h"
#include <array>
#include <iostream>
struct ggml_backend_cuda_context {int device=0;};
struct FixtureDevice {int cc=800,warp_size=32;};
struct FixtureInfo {std::array<FixtureDevice,1> devices;};
static FixtureInfo fixture_info;
static const FixtureInfo & ggml_cuda_info(){return fixture_info;}
static ggml_backend_buffer_type_t fixture_buffer=nullptr;
static ggml_backend_buffer_type_t ggml_backend_cuda_buffer_type(int){return fixture_buffer;}
#define HS_CUDA_AUDIT_SOURCE_DIGEST "CPU_FIXTURE_NOT_CUDA_BUILD"
#include "cuda_audit_runtime.inc"
struct Records {std::array<hs_cuda_dispatch_record,4> values{};int n=0;};
static void record(void * p,const hs_cuda_dispatch_record * r){auto & out=*static_cast<Records*>(p);if(out.n<4)out.values[out.n++]=*r;}
int main(){
 int n=0;auto check=[&](bool b){++n;if(!b)throw std::runtime_error("audit ABI check");};
 auto backend=ggml_backend_cpu_init();auto * context=ggml_init({1024*1024,nullptr,true});
 auto * t=ggml_new_tensor_4d(context,GGML_TYPE_F32,32,4,3,1);
 auto buffer=ggml_backend_alloc_ctx_tensors(context,backend);fixture_buffer=ggml_backend_buffer_get_type(buffer);
 Records records;hs_cuda_audit_binding binding{HS_CUDA_AUDIT_ABI,1,&records,record};
 check(!hs_cuda_audit_active());check(hs_cuda_exchange_audit(&binding)==nullptr);check(hs_cuda_audit_collecting());
 ggml_backend_cuda_context ctx;hs_cuda_audit_route(ctx,t,t,t,"mmvq");
 check(records.n==1);check(records.values[0].phase==1);check(records.values[0].tensors[0].ne[2]==3);
 check(records.values[0].tensors[0].nb[2]==t->nb[2]);check(records.values[0].tensors[0].host_buffer);
 uint64_t args[20]{};args[5]=77;
 hs_cuda_audit_mmvq(GGML_TYPE_Q8_0,4,1,0,0,0,2,3,1,32,4,1,0,args,20);
 check(records.n==2);check(records.values[1].phase==2);check(records.values[1].columns==4);
 check(records.values[1].argument_count==20 && records.values[1].arguments[5]==77);
 check(records.values[1].small_k==1 && records.values[1].block[1]==4);
 binding.mode=2;check(!hs_cuda_audit_collecting());hs_cuda_audit_route(ctx,t,t,t,"mmq");check(records.n==2);
 binding.mode=999;check(!hs_cuda_audit_collecting());binding.mode=1;binding.abi=999;check(!hs_cuda_audit_collecting());
 check(hs_cuda_exchange_audit(nullptr)==&binding);check(!hs_cuda_audit_active());
 ggml_backend_buffer_free(buffer);ggml_free(context);ggml_backend_free(backend);
 std::cout<<"CPU audit ABI fixture checks: "<<n<<"; CUDA compilation NOT_RUN\n";
}
