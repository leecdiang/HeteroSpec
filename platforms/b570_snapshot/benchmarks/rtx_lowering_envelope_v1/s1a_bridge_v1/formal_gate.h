#pragma once
// Included after the unchanged Graph/address interpreter. No arithmetic here.
namespace formal113 {
static constexpr const char* RUN="pr113-s1a-bridge-v1";
static std::string file_hash(const fs::path&p){
    HANDLE f=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    hs113::require(f!=INVALID_HANDLE_VALUE,"hash input missing");auto s=repair113::hash_handle(f);CloseHandle(f);return s;
}
static std::string data_hash(const std::vector<unsigned char>&b){
    BCRYPT_ALG_HANDLE a=nullptr;hs113::require(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"blob SHA provider");
    std::array<unsigned char,32>d{};hs113::require(BCryptHash(a,nullptr,0,(PUCHAR)b.data(),ULONG(b.size()),d.data(),ULONG(d.size()))>=0,"blob SHA");BCryptCloseAlgorithmProvider(a,0);
    std::ostringstream s;for(auto x:d)s<<std::hex<<std::setw(2)<<std::setfill('0')<<int(x);return s.str();
}
static J admit(const J&job,bool cpu){
    hs113::require(job.at("run_id")==RUN,"wrong formal run_id");
    fs::path f0path=job.at("F0_path").get<std::string>();
    hs113::require(f0path.is_absolute(),"absolute F0 required");
    if(!cpu)hs113::require(repair113::same_path(f0path,repair113::module_path(nullptr).parent_path()/"F0.json"),"registered F0 path required");
    auto digest=job.at("approved_stage_F0").get<std::string>();hs113::require(digest.size()==64&&file_hash(f0path)==digest,"exact F0 SHA binding");
    J f0=read(f0path);hs113::require(f0.at("run_id")==RUN&&f0.at("stage")=="S1A_BRIDGE_V1","F0 stage/run binding");
    hs113::require(cpu||!f0.value("CPU_fixture_only",false),"CPU fixture is never GPU authorization");
    hs113::require(file_hash(repair113::module_path(nullptr))==f0.at("executable_sha256"),"actual host SHA binding");
    fs::path pp=f0.at("plan_path").get<std::string>();hs113::require(file_hash(pp)==f0.at("plan_sha256"),"frozen plan SHA");J plan=read(pp);
    hs113::require(plan.at("run_id")==RUN,"plan run_id");
    J expected;
    if(job.at("stage")=="NUMERICAL"){
        auto index=integer(job.at("index"),0,239);expected=plan.at("numerical_slots").at(size_t(index));
        integer(job.at("repeat"),0,1);hs113::require(job.at("kind")=="numeric"&&job.at("graph_computes")==1&&job.at("warmups")==0,"one numeric call only");
    }else {hs113::require(job.at("stage")=="CENSUS","unsupported stage");expected=plan.at("census_wire");}
    J supplied=job;supplied.erase("F0_path");supplied.erase("approved_stage_F0");
    hs113::require(supplied==expected,"wire differs from registered actual slot");
    hs113::require(job.at("runtime_directory")==f0.at("runtime_directory")&&job.at("core_sha256")==f0.at("numerical_DLLs").at("ggml-base.dll")&&job.at("registry_sha256")==f0.at("numerical_DLLs").at("ggml.dll")&&job.at("cuda_plugin_sha256")==f0.at("numerical_DLLs").at("ggml-cuda.dll"),"runtime wire identity");
    if(job.at("stage")=="NUMERICAL")for(const auto&p:job.at("input_files"))hs113::require(file_hash(p.at("path").get<std::string>())==p.at("sha256"),"complete snapshot input identity");
    return plan;
}
static void retain(const J&job,const fs::path&out,const std::string&name,const std::vector<unsigned char>&b){
    hs113::require(b.size()<=16*1024*1024,"single complete tensor bound");
    auto hash=data_hash(b);fs::path root=job.at("cas_root").get<std::string>();hs113::require(root.is_absolute(),"absolute CAS root");fs::create_directories(root);auto p=root/(hash+".bin");
    if(fs::exists(p))hs113::require(bytes(p)==b&&file_hash(p)==hash,"existing CAS differs from actual readback");
    else {HANDLE f=CreateFileW(p.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);hs113::require(f!=INVALID_HANDLE_VALUE,"exclusive blob create");DWORD n=0;bool ok=WriteFile(f,b.data(),DWORD(b.size()),&n,nullptr)&&n==b.size();CloseHandle(f);hs113::require(ok&&file_hash(p)==hash,"complete blob write/hash");}
    write(out/(name+".BLOB.json"),{{"artifact",name},{"slot",job.at("id")},{"pid",GetCurrentProcessId()},{"bytes",b.size()},{"sha256",hash},{"cas_relative","cas/"+hash+".bin"},{"evidence","Actual full backend readback retained; equal blobs deduplicated only after full byte/hash verification"}});
}
static J shared_core(const J&job,const fs::path&out){
    fs::path runtime=job.at("runtime_directory").get<std::string>();auto&core=repair113::process_core(runtime/"ggml-base.dll",job.at("core_sha256"));
    J gate={{"core",core.receipt()},{"host_import",core.verify_shared_import("ggml_init")},{"registry_import",repair113::verify_registry_import(runtime,job.at("registry_sha256"))}};
    // Resolve ggml_init before taking the final receipt, as in GPU14.
    gate["core"]=core.receipt();write(out/"CORE_ADMITTED_BEFORE_CUDA.json",gate);return gate;
}
static int census(const J&job,const fs::path&out){
    auto plan=admit(job,false);hs113::require(job.at("stage")=="CENSUS"&&repair113::same_path(out,job.at("native_output").get<std::string>())&&!fs::exists(out),"one fresh census output");fs::create_directories(out);
    shared_core(job,out);fs::path runtime=job.at("runtime_directory").get<std::string>();SetDllDirectoryW(runtime.wstring().c_str());
    repair113::pin_numeric_file(runtime/"ggml-cuda.dll",job.at("cuda_plugin_sha256"));hs113::require(ggml_backend_load((runtime/"ggml-cuda.dll").string().c_str()),"census CUDA load");
    auto&core=repair113::process_core(runtime/"ggml-base.dll",job.at("core_sha256"));write(out/"PLUGIN_CORE_IMPORTS.json",repair113::verify_plugin_core_imports(runtime/"ggml-cuda.dll",core.module()));
    auto backend=ggml_backend_init_by_name("CUDA0",nullptr);hs113::require(backend,"census CUDA0 init");J records=J::array();size_t queries=0;
    for(const auto&slot:plan.at("numerical_slots"))if(slot.at("repeat")==0){Graph g(read(fs::path(slot.at("root").get<std::string>())/"snapshot.json"),slot.at("layout"),true);auto r=g.registry(backend);queries+=r["nodes"].size();r["descriptor_id"]=slot.at("descriptor");r["layout"]=slot.at("layout");r["stage_outputs"]=true;records.push_back(r);}
    hs113::require(records.size()==120&&queries==1806,"complete registered census cardinality");
    write(out/"CENSUS.json",{{"run_id",RUN},{"records",records},{"support_queries",queries},{"GPU_initializations",1},{"graph_computes",0},{"allocations",0},{"modules",modules()},{"pid",GetCurrentProcessId()}});ggml_backend_free(backend);return 0;
}
static int cpu_wires(const J&fixture,const fs::path&output){
    repair113::no_gpu_modules();J records=J::array();size_t checks=0;J binding;
    for(const auto&p:fixture.at("wire_files")){
        J job=read(p.get<std::string>());auto roundtrip=J::parse(job.dump());hs113::require(roundtrip==job,"native serializer semantic roundtrip");admit(roundtrip,true);
        if(records.empty()){auto&core=repair113::process_core(fs::path(job.at("runtime_directory").get<std::string>())/"ggml-base.dll",job.at("core_sha256"));binding={{"host_import",core.verify_shared_import("ggml_init")},{"registry_import",repair113::verify_registry_import(job.at("runtime_directory"),job.at("registry_sha256"))},{"core",core.receipt()}};}
        Graph graph(read(fs::path(job.at("root").get<std::string>())/"snapshot.json"),job.at("layout"),true);auto r=graph.registry();checks+=r["nodes"].size();
        r["slot"]=job.at("id");r["descriptor_id"]=job.at("descriptor");r["layout"]=job.at("layout");r["repeat"]=job.at("repeat");r["stage_outputs"]=true;r["stage_descriptors"]={{"QK",descriptor(graph.result.stage[0])},{"softmax",descriptor(graph.result.stage[1])},{"AV",descriptor(graph.result.stage[2])},{"ordinary",descriptor(graph.result.ordinary)}};r["wire_file_sha256"]=file_hash(p.get<std::string>());records.push_back(r);
    }
    hs113::require(records.size()==240&&checks==3612,"all actual numeric wires required");repair113::no_gpu_modules();
    write(output,{{"status","PASS"},{"records",records},{"graphs",records.size()},{"nodes",checks},{"shared_core",binding},{"modules",modules()},{"GPU_queries",0},{"CUDA_loads",0},{"graph_computes",0},{"model_requests",0}});return 0;
}
static int cpu_cas(const J&plan,const fs::path&output){
    repair113::no_gpu_modules();hs113::require(!fs::exists(output),"fresh CPU CAS fixture");fs::create_directories(output);
    J job={{"id","CPU_ONLY_STORAGE_FIXTURE"},{"cas_root",(output/"cas").u8string()}};auto data=bytes(plan.at("input").get<std::string>());
    retain(job,output/"events","read0",data);retain(job,output/"events","read1",data);auto changed=data;changed[0]^=1;
    retain(job,output/"events","mutation_before_rejection",changed);hs113::require(changed!=data,"negative fixture mutation");
    hs113::require(read(output/"events/read0.BLOB.json")["sha256"]==read(output/"events/read1.BLOB.json")["sha256"],"equal full blobs deduplicate");
    hs113::require(read(output/"events/mutation_before_rejection.BLOB.json")["sha256"]!=read(output/"events/read0.BLOB.json")["sha256"],"mutation evidence must survive rejection");
    repair113::no_gpu_modules();write(output/"RESULT.json",{{"status","PASS"},{"full_actual_CPU_reads",3},{"distinct_complete_blobs",2},{"mutation_retained_before_reject",true},{"GPU_queries",0},{"graph_computes",0}});return 0;
}
static int all_addresses(const J&plan,const fs::path&output){
    repair113::no_gpu_modules();size_t words=0,restored=0,cases=0;
    for(const auto&d:plan.at("descriptors"))for(const std::string name:{"MQ","PQ","QB","QH_C","QH_D"}){
        Graph g(d.at("metadata"),name,true);auto q=g.in[0],mask=g.in[3];auto width=q->ne[1],H=q->ne[2],D=q->ne[0];int layout=width==1?0:hs113::layout(name);
        fs::path root=d.at("root").get<std::string>();std::map<ggml_tensor*,std::vector<unsigned char>>raw;
        raw[q]=bytes(root/g.m["Q"]["file"].get<std::string>());raw[mask]=bytes(root/g.m["mask"]["file"].get<std::string>());
        std::vector<ggml_tensor*>mm,sm,av;
        for(int i=0;i<ggml_graph_n_nodes(g.g);i++){auto t=ggml_graph_node(g.g,i);if(t->op==GGML_OP_MUL_MAT&&t->src[0]==g.in[1])mm.push_back(t);if(t->op==GGML_OP_SOFT_MAX)sm.push_back(t);if(t->op==GGML_OP_MUL_MAT&&t->src[0]==g.in[2])av.push_back(t);}
        hs113::require(mm.size()==(layout==4?width:1)&&sm.size()==mm.size()&&av.size()==mm.size(),"actual arithmetic-chain cardinality");
        for(auto t:av)raw[t]=std::vector<unsigned char>(ggml_nbytes(t));
        for(int64_t h=0;h<H;h++)for(int64_t j=0;j<width;j++){
            size_t which=layout==4?j:0;auto qq=mm[which]->src[1],mk=sm[which]->src[1];
            for(int64_t a=0;a<D;a++){
                I ix=layout==1?I{a,0,h,j}:layout==2||layout==3?I{a,0,h*width+j,0}:layout==4?I{a,0,h,0}:I{a,j,h,0};
                hs113::require(storage(qq,ix,raw)==storage(q,I{a,j,h,0},raw),"all-layout exact Q address");words++;
                auto t=av[which];size_t off=0;for(int k=0;k<4;k++)off+=ix[k]*t->nb[k];uint32_t marker=uint32_t(1+a+D*(j+width*h));hs113::require(off+4<=raw[t].size(),"AV marker owner");std::memcpy(raw[t].data()+off,&marker,4);
            }
            for(int64_t key=0;key<mask->ne[0];key++){
                I ix=layout==1?I{key,0,0,j}:layout==2?I{key,0,j,0}:layout==3?I{key,0,h*width+j,0}:layout==4?I{key,0,0,0}:I{key,j,0,0};
                hs113::require(storage(mk,ix,raw)==storage(mask,I{key,j,0,0},raw),"all-layout exact mask address");words++;
            }
        }
        for(int64_t h=0;h<H;h++)for(int64_t j=0;j<width;j++)for(int64_t a=0;a<D;a++){
            hs113::require(storage(g.result.ordinary,I{a+h*D,j,0,0},raw)==uint32_t(1+a+D*(j+width*h)),"all-layout AV ordinary restoration");restored++;
        }cases++;
    }
    repair113::no_gpu_modules();write(output,{{"status","PASS"},{"actual_full_snapshot_graph_cases",cases},{"Q_mask_native_word_checks",words},{"synthetic_AV_restore_word_checks",restored},{"modules",modules()},{"arithmetic_computes",0},{"CUDA_queries",0}});return 0;
}
}
