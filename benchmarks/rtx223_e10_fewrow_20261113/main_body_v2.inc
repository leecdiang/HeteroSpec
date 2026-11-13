extern "C" void e10_u_quantize(const float*,void*,cudaStream_t);
extern "C" void e10_u_project(const void*,const void*,float*,cudaStream_t);
extern "C" int e10_u_shared();
extern "C" cudaError_t e10_u_prepare();
extern "C" cudaError_t e10_u_resources(cudaFuncAttributes*,int*);
static unsigned used=0,limit=0;static ULONGLONG deadline=0;
extern "C" void e10_reserve(unsigned n,const char*) {
    need(n&&used<=limit&&n<=limit-used,"explicit budget refused before dispatch");
    need(GetTickCount64()<deadline,"prelaunch deadline reached");used+=n;
}
static void quantize(int arm,const float*x,void*q,cudaStream_t stream){
    if(arm==1)e10_u_quantize(x,q,stream);
    else {e10_reserve(1,"B_quantizer");quantize_q8_1<<<dim3(16,8,1),256,0,stream>>>(x,q,4096,4096,32768,32768,4096,8,make_uint3(1,0,1));}
    check(cudaGetLastError());
}
static void project(int arm,const void*w,const void*q,float*y,cudaStream_t stream){
    if(arm==1)e10_u_project(w,q,y,stream);
    else {e10_reserve(1,"B_projection");mul_mat_vec_q<GGML_TYPE_Q8_0,4,false><<<dim3(2048,2,1),dim3(32,4,1),0,stream>>>(
       w,q,nullptr,ggml_cuda_mm_fusion_args_device{},y,4096,make_uint3(1,1,2),128,128,4096,make_uint3(1,1,2),524288,512,16384,make_uint3(1,0,1),524288,1024,32768,0);}
    check(cudaGetLastError());
}
static json resource(int arm){
    cudaFuncAttributes a{};int blocks=0;
    if(arm)check(e10_u_resources(&a,&blocks));
    else {check(cudaFuncGetAttributes(&a,mul_mat_vec_q<GGML_TYPE_Q8_0,4,false>));check(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&blocks,mul_mat_vec_q<GGML_TYPE_Q8_0,4,false>,128,0));}
    return {{"registers_per_thread",a.numRegs},{"static_shared_bytes",a.sharedSizeBytes},{"dynamic_shared_bytes",arm?e10_u_shared():0},
     {"local_bytes_per_thread",a.localSizeBytes},{"theoretical_blocks_per_sm",blocks},{"theoretical_warps_per_sm",blocks*4},
     {"actual_occupancy","NOT_MEASURED"},{"DRAM_L2_traffic","NOT_MEASURED"}};
}
static float getf(const std::vector<char>&v,size_t offset){float f;memcpy(&f,v.data()+offset,4);return f;}
static float geth(const std::vector<char>&v,size_t offset){__half h;memcpy(&h,v.data()+offset,2);return __half2float(h);}
static uint32_t bits(float v){uint32_t n;memcpy(&n,&v,4);return n;}
static int uq(const std::vector<char>&q,int col,int b,int k){
    const int i4=(b/8)*144+(b%8/2)*32+4*col+(k%16)/4;
    const int word=2*(b%2)+k/16;
    return int(int8_t(q[size_t(i4)*16+word*4+k%4]));
}
static float ud(const std::vector<char>&q,int col,int b){
    return getf(q,size_t((b/8)*144+128+4*(col/2)+(b%8)/2)*16+(2*(b%2)+col%2)*4);
}
static json compare_u(const std::vector<char>&w,const std::vector<char>&x,const std::vector<char>&q,const std::vector<char>&y,
                      const std::vector<char>&legacyq,const std::vector<char>&legacyy){
    int wrong_q=0,wrong_scales=0,legacy_q_diff=0,legacy_scale_diff=0,output_bit_diff=0,bound_fail=0;uint32_t max_ulp=0;
    double max_error=0,max_bound_ratio=0,l2diff=0,l2ref=0;std::vector<float>d(1024);std::vector<int8_t>canonical(32768);
    for(int c=0;c<8;++c)for(int b=0;b<128;++b){
        float amax=0;for(int k=0;k<32;++k){float v=getf(x,size_t(c*4096+b*32+k)*4);need(std::isfinite(v),"nonfinite input");amax=fmaxf(amax,fabsf(v));}
        need(amax>0,"diagnostic excludes allzero32 activation block");float inv=127.0f/amax,ideal=1.0f/inv,dy=ud(q,c,b);d[c*128+b]=dy;
        need(std::isfinite(dy)&&dy>0&&dy<=1,"U scale domain");uint32_t distance=bits(dy)>bits(ideal)?bits(dy)-bits(ideal):bits(ideal)-bits(dy);max_ulp=std::max(max_ulp,distance);wrong_scales+=distance>8;
        legacy_scale_diff+=bits(dy)!=bits(geth(legacyq,size_t(c*128+b)*36));
        for(int k=0;k<32;++k){int got=uq(q,c,b,k),expected=int(roundf(getf(x,size_t(c*4096+b*32+k)*4)*inv));wrong_q+=got!=expected;canonical[c*4096+b*32+k]=int8_t(got);legacy_q_diff+=got!=int(int8_t(legacyq[size_t(c*128+b)*36+4+k]));}
    }
    const double u=std::ldexp(1.0,-24),gamma=64*u/(1-64*u);
    for(int c=0;c<8;++c)for(int row=0;row<4096;++row){
        double sum=0,absolute=0;
        for(int b=0;b<128;++b){
            size_t offset=size_t(row*128+b)*34;float dw=geth(w,offset);need(std::isfinite(dw)&&fabsf(dw)<=1,"weight scale domain");int dot=0;
            for(int k=0;k<32;++k)dot+=int(int8_t(w[offset+2+k]))*int(canonical[c*4096+b*32+k]);
            double term=double(dot)*double(dw)*double(d[c*128+b]);sum+=term;absolute+=fabs(term);
        }
        const int i=c*4096+row;float value=getf(y,size_t(i)*4),old=getf(legacyy,size_t(i)*4);need(std::isfinite(value),"nonfinite U output");
        double error=fabs(double(value)-sum),bound=gamma*absolute+128*double(FLT_MIN);bound_fail+=error>bound;max_error=std::max(max_error,error);max_bound_ratio=std::max(max_bound_ratio,error/bound);
        output_bit_diff+=bits(value)!=bits(old);l2diff+=(double(value)-old)*(double(value)-old);l2ref+=double(old)*old;
    }
    json report={{"raw_activation_equal_legacy",q==legacyq},{"logical_q_different_from_legacy",legacy_q_diff},{"float_scale_different_from_legacy_half_expanded",legacy_scale_diff},
      {"legacy_half_sum_fields","NOT_REPRESENTED_D4"},{"legacy_output_different_float_bits",output_bit_diff},{"legacy_output_bitwise_equal",y==legacyy},
      {"U_CPU_quant_wrong_values",wrong_q},{"U_CPU_scale_over8ULP",wrong_scales},{"U_CPU_scale_max_ULP",max_ulp},{"U_independent_double_bound_fail_values",bound_fail},
      {"U_max_absolute_error_vs_double_quantized_reference",max_error},{"U_max_error_over_analytic_bound",max_bound_ratio},{"legacy_relative_L2_difference",sqrt(l2diff/l2ref)},
      {"legacy_reference_preservation",q==legacyq&&y==legacyy?"PASS":"NON_EQUIVALENT"}};
    report["U_own_contract_pass"]=!wrong_q&&!wrong_scales&&!bound_fail;return report;
}
int main(int argc,char**argv){
    json result={{"status","FAILED"},{"model_loads",0},{"decode_calls",0}};std::string out;
    try{
        need(argc==2,"probe job.json");std::ifstream config(argv[1]);json job;config>>job;
        need(job.at("schema")=="heterospec-e10-fewrow-v1"&&job.at("gpu_admitted")==true,"job not admitted");
        std::string phase=job.at("phase");need(phase=="qualification"||phase=="timing","phase");limit=phase=="qualification"?14:320;
        char tick[40]{};need(GetEnvironmentVariableA("HS_B_DEADLINE_TICK",tick,sizeof(tick))>0,"deadline binding");deadline=std::stoull(tick);need(GetTickCount64()<deadline,"expired");
        auto w=load(job.at("weight_path"),17825792),x=load(job.at("input_path"),131072),oldq=load(job.at("quantized_activation_path"),36864),oldy=load(job.at("backend_output_path"),131072);
        need(sha256(w)==job.at("weight_sha256")&&sha256(x)==job.at("input_sha256")&&sha256(oldq)==job.at("quantized_activation_sha256")&&sha256(oldy)==job.at("backend_output_sha256"),"operand hashes");
        out=job.at("output_dir");std::cout<<"READY EXECUTE"<<std::endl;std::string permit;need(bool(std::getline(std::cin,permit))&&permit=="GO EXECUTE","parent grant");
        check(cudaSetDevice(0));cudaDeviceProp prop{};check(cudaGetDeviceProperties(&prop,0));need(uuid_text(prop.uuid)==job.at("device_uuid")&&prop.major==12&&prop.minor==0,"device");need(prop.sharedMemPerBlockOptin>=e10_u_shared(),"U dynamic shared limit not supported");check(e10_u_prepare());
        result["device"]={{"name",prop.name},{"uuid",uuid_text(prop.uuid)},{"SMs",prop.multiProcessorCount},{"shared_optin",prop.sharedMemPerBlockOptin}};result["upstream_compile"]="fixed0fb8f157 Q8_0,ncg1,nmt1,PDL0-equivalent raw host launch";
        for(int arm=0;arm<2;++arm)result["resources"][arm?"U":"B"]=resource(arm);
        void*dw=nullptr,*dx=nullptr,*dq=nullptr,*dy=nullptr;check(cudaMalloc(&dw,w.size()));check(cudaMalloc(&dx,x.size()));check(cudaMalloc(&dq,36864));check(cudaMalloc(&dy,131072));check(cudaMemcpy(dw,w.data(),w.size(),cudaMemcpyHostToDevice));check(cudaMemcpy(dx,x.data(),x.size(),cudaMemcpyHostToDevice));cudaStream_t stream;check(cudaStreamCreateWithFlags(&stream,cudaStreamNonBlocking));
        std::vector<std::vector<char>>referenceq(2),referencey(2);referenceq[0]=oldq;referencey[0]=oldy;
        auto copy=[&](std::vector<char>&q,std::vector<char>&y){q.resize(36864);y.resize(131072);check(cudaMemcpy(q.data(),dq,q.size(),cudaMemcpyDeviceToHost));check(cudaMemcpy(y.data(),dy,y.size(),cudaMemcpyDeviceToHost));};
        if(phase=="qualification"){
            for(int arm=0;arm<2;++arm)for(int repeat=0;repeat<2;++repeat){
                quantize(arm,(float*)dx,dq,stream);project(arm,dw,dq,(float*)dy,stream);check(cudaStreamSynchronize(stream));std::vector<char>q,y;copy(q,y);
                save(out+"/"+(arm?"U":"B")+"-r"+std::to_string(repeat)+"-activation.bin",q.data(),q.size());save(out+"/"+(arm?"U":"B")+"-r"+std::to_string(repeat)+"-output.bin",y.data(),y.size());
                if(arm==0)need(q==oldq&&y==oldy,"B legacy bitwise contract failed");else{result["U_qualification"].push_back(compare_u(w,x,q,y,oldq,oldy));need(result["U_qualification"].back().at("U_own_contract_pass")==true,"U separate numerical contract failed");if(repeat==0){referenceq[1]=q;referencey[1]=y;}else need(q==referenceq[1]&&y==referencey[1],"U nondeterminism");}
                result["qualification"].push_back({{"arm",arm?"U":"B"},{"repeat",repeat},{"quant_sha256",sha256(q)},{"output_sha256",sha256(y)}});
            }
        }else{
            referenceq[1]=load(job.at("U_qualified_activation_path"),36864);referencey[1]=load(job.at("U_qualified_output_path"),131072);need(sha256(referenceq[1])==job.at("U_qualified_activation_sha256")&&sha256(referencey[1])==job.at("U_qualified_output_sha256"),"U qualified identities");
            for(int arm=0;arm<2;++arm)for(int i=0;i<2;++i){quantize(arm,(float*)dx,dq,stream);project(arm,dw,dq,(float*)dy,stream);}check(cudaStreamSynchronize(stream));
            cudaEvent_t begin,end;check(cudaEventCreate(&begin));check(cudaEventCreate(&end));
            for(int mode=0;mode<2;++mode)for(int block=0;block<12;++block)for(int pos=0;pos<2;++pos){
                int arm=(block+pos)%2;if(mode==0){quantize(arm,(float*)dx,dq,stream);check(cudaStreamSynchronize(stream));}
                auto t=std::chrono::steady_clock::now();check(cudaEventRecord(begin,stream));for(int i=0;i<4;++i){if(mode)quantize(arm,(float*)dx,dq,stream);project(arm,dw,dq,(float*)dy,stream);}check(cudaEventRecord(end,stream));check(cudaEventSynchronize(end));double host=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();float ms;check(cudaEventElapsedTime(&ms,begin,end));
                std::vector<char>q,y;copy(q,y);bool valid=q==referenceq[arm]&&y==referencey[arm];result["post_batch_bitwise"].push_back({{"arm",arm?"U":"B"},{"mode",mode},{"block",block},{"activation_exact",q==referenceq[arm]},{"output_exact",y==referencey[arm]}});need(valid,"batch differs from own numerical-contract oracle");
                result["paired_timings"].push_back({{"arm",arm?"U":"B"},{"mode",mode?"complete-operator":"kernel-only"},{"block",block},{"position",pos},{"batch_repetitions",4},{"event_ms",ms},{"per_operator_ms",ms/4},{"host_complete_s",host}});
            }
            check(cudaEventDestroy(begin));check(cudaEventDestroy(end));
        }
        check(cudaStreamDestroy(stream));check(cudaFree(dw));check(cudaFree(dx));check(cudaFree(dq));check(cudaFree(dy));result["status"]="PASS_TWO_CONTRACT_DIAGNOSTIC";
    }catch(const std::exception&e){result["error"]=e.what();}
    result["explicit_prelaunch_charged"]=used;result["explicit_limit"]=limit;result["physical_lifecycle_launches"]=nullptr;
    if(!out.empty()){auto s=result.dump(2);save(out+"/result.json",s.data(),s.size());}std::cout<<result.dump()<<std::endl;return result["status"]=="PASS_TWO_CONTRACT_DIAGNOSTIC"?0:2;
}
