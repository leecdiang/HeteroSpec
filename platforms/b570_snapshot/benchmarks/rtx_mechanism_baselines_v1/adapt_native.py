"""Mechanical host adaptation; numerical graph headers remain exact parent copies."""
from pathlib import Path
V=Path(__file__).resolve().parent
src=(V.parent/'rtx_boundary_confirmation_v1/collector.cpp').read_text()
src=src.replace('rtx-boundary-confirmation-v1','rtx-mechanism-baselines-v1')
src=src.replace('#include <memory>','#include <memory>\n#include "cupti_observer.h"')
src=src.replace('auto t0=tick();','std::string graph_mode=job.at("graph_mode");hs113::require(graph_mode=="OFF"||graph_mode=="ON","unknown graph mode");char off[16]={0};auto offn=GetEnvironmentVariableA("GGML_CUDA_DISABLE_GRAPHS",off,16);hs113::require(graph_mode=="OFF"?(offn>0&&std::string(off)=="1"):(offn==0),"graph mode environment mismatch");trace122::Observer tracer;bool profiling=job.value("profile",false);auto t0=tick();')
src=src.replace('SetDllDirectoryW(runtime.wstring().c_str());','if(profiling)tracer.start(job.at("cupti_path").get<std::string>(),job.at("cupti_sha256"));SetDllDirectoryW(runtime.wstring().c_str());')
src=src.replace('bool capture=requested_capture;', '''bool integrated=job.value("integrated_q_update",false);std::vector<unsigned char>permuted;
    if(integrated){permuted=bytes(job.at("producer_source").get<std::string>());hs113::require(permuted.size()==prepared[0].size(),"complete producer Q");}
    auto materialize_q=[&](){int64_t D=g.in[0]->ne[0],q=g.in[0]->ne[1],H=g.in[0]->ne[2];
        if(context.at("storage")=="compact"){for(int64_t j=0;j<q;j++)for(int64_t h=0;h<H;h++)memcpy(prepared[0].data()+4*D*(j+q*h),permuted.data()+4*D*(h+H*j),4*D);}
        else memcpy(prepared[0].data(),permuted.data(),permuted.size());};
    bool capture=requested_capture;''')
src=src.replace('bool capture=requested_capture;', '''bool alternating=job.contains("alternate_context");std::vector<std::vector<unsigned char>> alternate;std::vector<unsigned char>alternate_expected;
    if(alternating){auto ac=job.at("alternate_context");for(int a=0;a<4;a++){alternate.push_back(bytes(fs::path(ac.at("root").get<std::string>())/(std::string(roles[a])+".bin")));hs113::require(alternate[a].size()==source[a].size(),"alternate input geometry");}alternate_expected=bytes(ac.at("reference").get<std::string>());}
    bool capture=requested_capture;''')
src=src.replace('int64_t a=0,b=0,c=0,d=0;','int64_t e=0,p=0,u=0,a=0,b=0,c=0,d=0;')
src=src.replace('x.a=tick();x.rc=', 'if(alternating){auto& value=(i%2)?alternate:source;for(int a=0;a<4;a++)ggml_backend_tensor_set(g.in[a],value[a].data(),0,value[a].size());hs113::require(complete()==0,"alternating upload synchronize");for(int a=0;a<4;a++){std::vector<unsigned char>back(value[a].size());ggml_backend_tensor_get(g.in[a],back.data(),0,back.size());blob(out/("update_"+std::to_string(i)+"_"+roles[a]+".bin"),back);hs113::require(back==value[a],"alternating full input byte audit");}}if(profiling)tracer.call.store(i);x.e=tick();if(integrated){materialize_q();x.p=tick();ggml_backend_tensor_set(g.in[0],prepared[0].data(),0,prepared[0].size());hs113::require(complete()==0,"Q update synchronization");x.u=tick();}else{x.p=x.e;x.u=x.e;}x.a=tick();x.rc=')
src=src.replace('memcmp(ptr,expected.data(),expected.size())==0','memcmp(ptr,(alternating&&i%2)?alternate_expected.data():expected.data(),expected.size())==0')
src=src.replace('{"begin",x.a}', '{"transaction_begin",x.e},{"Q_materialized",x.p},{"Q_upload_complete",x.u},{"begin",x.a}')
src=src.replace('record["observer_method"]=method;', 'record["graph_mode"]=graph_mode;record["GGML_CUDA_DISABLE_GRAPHS"]=graph_mode=="OFF"?J("1"):J(nullptr);record["profile"]=profiling;record["integrated_q_update"]=integrated;record["observer_method"]=method;')
src=src.replace('bool input_equal=getinputs("after");','if(profiling){tracer.call.store(-2);tracer.finish(out);}if(alternating)upload();bool input_equal=getinputs("after");')
(V/'collector.cpp').write_text(src)
