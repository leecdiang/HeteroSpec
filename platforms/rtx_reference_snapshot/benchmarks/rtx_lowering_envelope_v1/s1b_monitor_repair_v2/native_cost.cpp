#include "graph_base.h"
#include "ggml-alloc.h"
#include "timing_loop.h"
#include "s1b_gate.h"

static int64_t main_entry_tick=0;
static J interval_json(const s1b::Interval&r){return {{"index",r.index},{"warmup",r.warmup},{"begin",r.begin},{"compute_return",r.compute_return},{"sync_return",r.sync_return},{"readback_return",r.readback_return},{"audit_return",r.audit_return}};}
static bool finite_bytes(const std::vector<unsigned char>&b){if(b.size()%4)return false;for(size_t i=0;i<b.size();i+=4){uint32_t x;std::memcpy(&x,b.data()+i,4);if((x&0x7f800000)==0x7f800000)return false;}return true;}
static J placement(Graph&g,ggml_backend_t backend,J graph){
    auto intended=ggml_backend_get_device(backend);J owners=J::array();
    auto check=[&](ggml_tensor*t,const J&id){bool has=t->buffer,host=has?ggml_backend_buffer_is_host(t->buffer):true;auto actual=has&&!host?ggml_backend_buft_get_device(ggml_backend_buffer_get_type(t->buffer)):nullptr;bool good=has&&!host&&actual==intended;
        owners.push_back({{"id",id},{"has_buffer",has},{"host",host},{"actual",uint64_t((uintptr_t)actual)},{"intended",uint64_t((uintptr_t)intended)},{"valid",good}});hs113::require(good,"wrong CUDA tensor owner");};
    for(int i=0;i<4;i++)check(g.in[i],"input"+std::to_string(i));
    for(int i=0;i<ggml_graph_n_nodes(g.g);i++){auto*t=ggml_graph_node(g.g,i);graph["nodes"][i]["placement"]=t->buffer?J(ggml_backend_buffer_name(t->buffer)):J(nullptr);if(!metadata(t->op))check(t,i);}
    graph["ownership"]=owners;graph["actual_placement"]="CUDA0 direct graph allocator; no CPU fallback";return graph;
}
struct NativeOps {
    ggml_backend_t backend;Graph&g;int(*complete)();const std::vector<unsigned char>&expected;const fs::path out;
    int starts=0,last_rc=-1,last_sync=-1;std::vector<std::vector<unsigned char>>outputs;
    void before(int i){write(out/("GRAPH_STARTED_"+std::to_string(i)+".json"),{{"index",i},{"warmup",i==0}});}
    int compute(){starts++;last_rc=int(ggml_backend_graph_compute(backend,g.g));return last_rc;}
    int sync(){last_sync=complete();return last_sync;}
    void readback(int){outputs.emplace_back(ggml_nbytes(g.result.ordinary));auto&b=outputs.back();ggml_backend_tensor_get(g.result.ordinary,b.data(),0,b.size());}
    void verify(int){auto&b=outputs.back();hs113::require(finite_bytes(b)&&b==expected,"clean ordinary differs from qualified PR116 bytes");}
};
static int gpu(const J&job,const fs::path&out,bool census){
    auto f=cost116::admit(job,false);hs113::require(job.at("kind")== (census?"support":job.at("kind")),"mode kind mismatch");
    hs113::require(repair113::same_path(out,job.at("native_output").get<std::string>())&&!fs::exists(out),"fresh exact output");fs::create_directories(out);
    s1b::Clock clock;auto a0=clock.now();cost116::core_gate(f,out);auto runtime=fs::path(f.at("runtime_directory").get<std::string>());
    SetDllDirectoryW(runtime.wstring().c_str());repair113::pin_numeric_file(runtime/"ggml-cuda.dll",f.at("numerical_DLLs").at("ggml-cuda.dll"));
    hs113::require(ggml_backend_load((runtime/"ggml-cuda.dll").string().c_str()),"CUDA plugin load");auto&core=repair113::process_core(runtime/"ggml-base.dll",f.at("numerical_DLLs").at("ggml-base.dll"));write(out/"PLUGIN_CORE_IMPORTS.json",repair113::verify_plugin_core_imports(runtime/"ggml-cuda.dll",core.module()));
    auto backend=ggml_backend_init_by_name("CUDA0",nullptr);hs113::require(backend,"CUDA0 init");auto a1=clock.now();
    auto plan=read(f.at("plan_path").get<std::string>());
    if(census){J rows=J::array();size_t queries=0;for(const auto&d:plan["descriptors"])for(std::string l:{"PQ","QB","QH_C"}){Graph g(d["metadata"],l,false);auto r=g.registry(backend);queries+=r["nodes"].size();r["descriptor_id"]=d["id"];r["layout"]=l;rows.push_back(r);}write(out/"CENSUS.json",{{"records",rows},{"support_queries",queries},{"graph_computes",0},{"GPU_initializations",1},{"modules",modules()},{"pid",GetCurrentProcessId()}});ggml_backend_free(backend);return 0;}
    auto meta=read(fs::path(job.at("root").get<std::string>())/"snapshot.json");auto build0=clock.now();Graph g(meta,job.at("layout"),false);auto build1=clock.now();auto graph=g.registry(backend);
    for(auto&n:graph["nodes"])hs113::require(n["CUDA_support"]==true,"clean node unsupported");
    auto alloc0=clock.now();auto allocator=ggml_gallocr_new(ggml_backend_get_default_buffer_type(backend));hs113::require(allocator&&ggml_gallocr_alloc_graph(allocator,g.g),"clean dependency-only allocation failed");auto alloc1=clock.now();graph=placement(g,backend,graph);write(out/"GRAPH_AND_OWNERSHIP.json",graph);
    auto cudart=GetModuleHandleW(L"cudart64_12.dll");hs113::require(cudart,"cudart absent");auto complete=(int(*)())GetProcAddress(cudart,"cudaDeviceSynchronize");hs113::require(complete,"all-stream completion missing");
    const char*roles[]={"Q","K","V","mask"};std::vector<std::vector<unsigned char>>source,prepared;auto prep0=clock.now();
    for(int i=0;i<4;i++){source.push_back(bytes(fs::path(job.at("root").get<std::string>())/meta[roles[i]]["file"].get<std::string>()));hs113::require(source.back().size()==ggml_nbytes(g.in[i]),"whole input span");}auto prep1=clock.now();
    // Exact full-strided source materialization. No hidden CPU QH packing; its
    // required CONT/mask/output restoration remain executable graph dependencies.
    prepared=source;auto prep2=clock.now();
    auto upload0=clock.now();for(int i=0;i<4;i++)ggml_backend_tensor_set(g.in[i],prepared[i].data(),0,prepared[i].size());hs113::require(complete()==0,"input upload synchronization");auto upload1=clock.now();
    auto audit0=clock.now();for(int i=0;i<4;i++){std::vector<unsigned char>b(source[i].size());ggml_backend_tensor_get(g.in[i],b.data(),0,b.size());cost116::retain(job,out,std::string("input_")+roles[i]+".before",b);hs113::require(b==source[i],"input before mismatch");}auto audit1=clock.now();
    auto reference=bytes(job.at("ordinary_reference").at("path").get<std::string>());hs113::require(cost116::hashfile(job.at("ordinary_reference").at("path").get<std::string>())==job.at("ordinary_reference").at("sha256"),"ordinary reference identity");
    NativeOps ops{backend,g,complete,reference,out};std::vector<s1b::Interval> times;
    try{times=s1b::loop(clock,ops,job.at("measured_evaluations"),&times);}
    catch(...){for(size_t i=0;i<ops.outputs.size();i++)cost116::retain(job,out,"ordinary_"+std::to_string(i),ops.outputs[i]);J partial=J::array();for(auto&r:times)partial.push_back(interval_json(r));write(out/"FAILED.json",{{"partial_intervals",partial},{"QPC_frequency",clock.frequency},{"actual_graph_calls",ops.starts},{"last_compute_status",ops.last_rc},{"last_sync_status",ops.last_sync},{"output_count",ops.outputs.size()},{"no_retry",true}});throw;}
    // Full bytes are retained after the clean windows; every actual occurrence
    // has a separate record even when identical bytes deduplicate in CAS.
    for(size_t i=0;i<ops.outputs.size();i++)cost116::retain(job,out,"ordinary_"+std::to_string(i),ops.outputs[i]);
    for(int i=0;i<4;i++){std::vector<unsigned char>b(source[i].size());ggml_backend_tensor_get(g.in[i],b.data(),0,b.size());cost116::retain(job,out,std::string("input_")+roles[i]+".after",b);hs113::require(b==source[i],"input mutation");}
    J intervals=J::array();for(auto&r:times)intervals.push_back(interval_json(r));
    write(out/"RECORD.json",{{"status","COMPLETED"},{"kind",job.at("kind")},{"layout",job.at("layout")},{"pid",GetCurrentProcessId()},{"graph_computes",ops.starts},{"warmups",1},{"measured",job.at("measured_evaluations")},{"QPC_frequency",clock.frequency},{"intervals",intervals},{"cost_ticks",{{"main_entry_admission",a0-main_entry_tick},{"core_CUDA_initialization_and_audit",a1-a0},{"input_before_qualification",audit1-audit0},{"graph_build",build1-build0},{"graph_allocate",alloc1-alloc0},{"source_read",prep1-prep0},{"CPU_materialize_full_inputs",prep2-prep1},{"H2D_and_setup_sync",upload1-upload0}}},{"allocated_graph_bytes",ggml_gallocr_get_buffer_size(allocator,0)},{"modules",modules()},{"ordinary_qualification","Every warmup/measured output full-byte equal to fixed PR116 reference"},{"synchronization","cudaDeviceSynchronize current context/all relevant streams; F+G inclusive host wall, never kernel time"},{"profile","PROFILE_UNAVAILABLE"}});
    ggml_gallocr_free(allocator);ggml_backend_free(backend);return 0;
}
static int cpu_graphs(const J&fixture,const fs::path&out){
    repair113::no_gpu_modules();J rows=J::array();size_t restored=0;
    for(const auto&wirepath:fixture.at("wires")){
        auto job=read(wirepath.get<std::string>());hs113::require(J::parse(job.dump())==job,"actual native serializer roundtrip");cost116::admit(job,true);
        auto&core=repair113::process_core(fs::path(job.at("runtime_directory").get<std::string>())/"ggml-base.dll",job.at("core_sha256"));core.verify_shared_import("ggml_init");
        Graph clean(read(fs::path(job.at("root").get<std::string>())/"snapshot.json"),job.at("layout"),false);Graph numeric(clean.m,job.at("layout"),true);
        auto canonicalAV=bytes(job.at("AV_reference").at("path").get<std::string>());auto ordinary=bytes(job.at("ordinary_reference").at("path").get<std::string>());
        std::vector<ggml_tensor*>avs;for(int i=0;i<ggml_graph_n_nodes(clean.g);i++){auto*t=ggml_graph_node(clean.g,i);if(t->op==GGML_OP_MUL_MAT&&t->src[0]==clean.in[2])avs.push_back(t);}
        int64_t D=clean.in[0]->ne[0],q=clean.in[0]->ne[1],H=clean.in[0]->ne[2];int layout=q==1?0:hs113::layout(job.at("layout"));std::map<ggml_tensor*,std::vector<unsigned char>>raw;
        for(auto*t:avs)raw[t]=std::vector<unsigned char>(ggml_nbytes(t));
        for(int64_t h=0;h<H;h++)for(int64_t j=0;j<q;j++)for(int64_t d=0;d<D;d++){
            auto*t=avs[layout==4?j:0];I ix=layout==1?I{d,0,h,j}:layout==2?I{d,0,h*q+j,0}:layout==4?I{d,0,h,0}:I{d,j,h,0};size_t off=0;for(int k=0;k<4;k++)off+=ix[k]*t->nb[k];std::memcpy(raw[t].data()+off,canonicalAV.data()+4*(d+D*(j+q*h)),4);
        }
        for(int64_t j=0;j<q;j++)for(int64_t h=0;h<H;h++)for(int64_t d=0;d<D;d++){uint32_t want;std::memcpy(&want,ordinary.data()+4*(d+D*(h+H*j)),4);hs113::require(storage(clean.result.ordinary,I{d+D*h,j,0,0},raw)==want,"qualified AV bytes restored ordinary differ");restored++;}
        auto r=clean.registry();r["numeric_graph"]=numeric.registry();r["descriptor_id"]=job.at("descriptor");r["layout"]=job.at("layout");rows.push_back(r);
    }
    repair113::no_gpu_modules();write(out,{{"status","PASS"},{"records",rows},{"graphs",rows.size()},{"actual_PR116_AV_to_ordinary_words_checked",restored},{"modules",modules()},{"new_CUDA_loads",0},{"new_GPU_queries",0},{"graph_computes",0},{"qualification","CPU dependency/storage/serializer only; actual clean CUDA ordinary correspondence NOT_ESTABLISHED"}});return 0;
}
static int cpu_loop(const J&fixture,const fs::path&out){
    repair113::no_gpu_modules();struct C{int64_t frequency=1000,t=1;int64_t now(){return t;}};
    J rows=J::array();for(std::string test:{"good8","good1","compute_error","sync_error","clock_backwards","zero_interval","changed_output","wrong_count","bad_frequency"}){
        C c;int count=test=="good1"?1:8;if(test=="bad_frequency")c.frequency=0;
        struct O{C&c;std::string test;int starts=0,reads=0;void before(int){}int compute(){starts++;c.t+=test=="zero_interval"?0:2;return test=="compute_error"?1:0;}int sync(){c.t+=test=="zero_interval"?0:test=="clock_backwards"?-10:3;return test=="sync_error"?1:0;}void readback(int){reads++;c.t+=5;}void verify(int){hs113::require(test!="changed_output","synthetic output mismatch");c.t+=7;}}ops{c,test};
        bool accepted=false;try{auto t=s1b::loop(c,ops,test=="wrong_count"?9:count);hs113::require(int(t.size())==count+1,"loop cardinality");for(auto&r:t){hs113::require(r.sync_return-r.begin==5&&r.compute_return-r.begin==2&&r.sync_return-r.compute_return==3,"F/G partition");}accepted=true;}catch(...){}
        hs113::require(accepted==(test=="good8"||test=="good1"),"CPU loop expected result");rows.push_back({{"case",test},{"accepted",accepted},{"graph_computes",0},{"synthetic_callback_calls",ops.starts}});
    }
    s1b::Clock real;auto a=real.now();Sleep(3);auto b=real.now();hs113::require(b>a,"real CPU QPC elapsed");repair113::no_gpu_modules();write(out,{{"status","PASS"},{"cases",rows},{"real_CPU_QPC_frequency",real.frequency},{"real_CPU_observation_ticks",b-a},{"synthetic_GPU_latencies",false},{"GPU_queries",0},{"CUDA_loads",0},{"graph_computes",0}});return 0;
}
int main(int argc,char**argv){try{
    s1b::Clock entry_clock;main_entry_tick=entry_clock.now();hs113::require(argc==4,"mode job output");std::string mode=argv[1];auto job=read(argv[2]);fs::path out=argv[3];
    if(mode=="--cpu-graphs")return cpu_graphs(job,out);
    if(mode=="--cpu-loop")return cpu_loop(job,out);
    if(mode=="--cpu-wire"){repair113::no_gpu_modules();cost116::admit(job,true);repair113::no_gpu_modules();write(out,{{"status","PASS"},{"GPU_queries",0}});return 0;}
    hs113::require(mode=="--gpu-census"||mode=="--gpu-clean"||mode=="--gpu-trace","unknown execution mode");
    hs113::require((mode=="--gpu-census"&&job.at("kind")=="support")||(mode=="--gpu-clean"&&job.at("kind")=="clean")||(mode=="--gpu-trace"&&job.at("kind")=="trace"),"mode/kind mismatch");
    gpu_file_limit=mode=="--gpu-census"?4*1024*1024:128*1024;gpu_total_limit=mode=="--gpu-census"?8*1024*1024:512*1024;return gpu(job,out,mode=="--gpu-census");
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
