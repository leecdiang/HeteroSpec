#pragma once
namespace cost116 {
static constexpr const char*RUN="pr116-s1b-cost-v1";
static std::string hashfile(const fs::path&p){HANDLE h=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);hs113::require(h!=INVALID_HANDLE_VALUE,"hash file missing");auto d=repair113::hash_handle(h);CloseHandle(h);return d;}
static J admit(const J&job,bool cpu){
    hs113::require(job.at("run_id")==RUN,"wrong S1B run");fs::path fp=job.at("F0_path").get<std::string>();
    hs113::require(fp.is_absolute()&&hashfile(fp)==job.at("approved_stage_F0"),"exact absolute F0 required");
    if(!cpu)hs113::require(repair113::same_path(fp,repair113::module_path(nullptr).parent_path()/"F0.json"),"F0 beside host required");
    auto f=read(fp);hs113::require(f.at("run_id")==RUN&&f.at("stage")=="S1B_COST_V1","S1B freeze identity");
    hs113::require(cpu||!f.value("CPU_fixture_only",false),"CPU fixture cannot authorize GPU");
#ifdef S1B_TRACE_BUILD
    const char*role="trace";
#else
    const char*role="clean";
#endif
    hs113::require(hashfile(repair113::module_path(nullptr))==f.at("hosts").at(role).at("sha256"),"actual host hash");
    auto plan=read(f.at("plan_path").get<std::string>());hs113::require(hashfile(f.at("plan_path").get<std::string>())==f.at("plan_sha256"),"plan hash");
    J expected;
    if(job.at("kind")=="support")expected=plan.at("census_job");
    else {auto idx=integer(job.at("index"),0,job.at("kind")=="trace"?71:215);expected=plan.at(job.at("kind")=="trace"?"trace_slots":"clean_slots").at(size_t(idx));}
    J supplied=job;supplied.erase("F0_path");supplied.erase("approved_stage_F0");hs113::require(expected==supplied,"exact serialized slot binding");
    hs113::require(plan.at("run_id")==RUN&&job.at("runtime_directory")==f.at("runtime_directory"),"runtime/run binding");
    if(!cpu){
        if(job.at("kind")=="trace")hs113::require(std::string(role)=="trace"&&f.at("profile").at("status")=="ADMITTED","PROFILE_UNAVAILABLE; no trace start");
        else hs113::require(std::string(role)=="clean","trace binary cannot run clean/census");
    }
    if(job.contains("input_files"))for(const auto&p:job["input_files"])hs113::require(hashfile(p.at("path").get<std::string>())==p.at("sha256"),"input drift");
    return f;
}
static J core_gate(const J&f,const fs::path&out){auto runtime=fs::path(f.at("runtime_directory").get<std::string>());auto&core=repair113::process_core(runtime/"ggml-base.dll",f.at("numerical_DLLs").at("ggml-base.dll"));
    auto h=core.verify_shared_import("ggml_init");auto reg=repair113::verify_registry_import(runtime,f.at("numerical_DLLs").at("ggml.dll"));J gate={{"core",core.receipt()},{"host_import",h},{"registry_import",reg}};write(out/"CORE_ADMITTED_BEFORE_CUDA.json",gate);return gate;}
static void retain(const J&job,const fs::path&out,const std::string&name,const std::vector<unsigned char>&b){
    hs113::require(b.size()<=16*1024*1024,"blob size cap");fs::path root=job.at("cas_root").get<std::string>();fs::create_directories(root);
    BCRYPT_ALG_HANDLE alg=nullptr;hs113::require(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA provider");unsigned char digest[32];hs113::require(BCryptHash(alg,nullptr,0,(PUCHAR)b.data(),ULONG(b.size()),digest,32)>=0,"blob SHA");BCryptCloseAlgorithmProvider(alg,0);std::ostringstream h;for(auto x:digest)h<<std::hex<<std::setw(2)<<std::setfill('0')<<int(x);auto hash=h.str();auto p=root/(hash+".bin");
    if(fs::exists(p))hs113::require(bytes(p)==b&&hashfile(p)==hash,"existing CAS mismatch");else {HANDLE h=CreateFileW(p.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);hs113::require(h!=INVALID_HANDLE_VALUE,"exclusive CAS create");DWORD n=0;bool ok=WriteFile(h,b.data(),DWORD(b.size()),&n,nullptr)&&n==b.size();FlushFileBuffers(h);CloseHandle(h);hs113::require(ok&&hashfile(p)==hash,"full exclusive CAS write");}
    write(out/(name+".BLOB.json"),{{"artifact",name},{"slot",job.at("id")},{"pid",GetCurrentProcessId()},{"bytes",b.size()},{"sha256",hash},{"cas_relative","cas/"+hash+".bin"}});
}
}
