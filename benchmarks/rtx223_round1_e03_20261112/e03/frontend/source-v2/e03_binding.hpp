#pragma once
// This epoch has no authenticated live parent channel or universal launch coverage.
// Ordinary CUDA-DLL initialization remains blocked even for identity-only jobs.
#include <cctype>
namespace hs_e03 {
inline bool hex64(const json& v){if(!v.is_string())return false;const auto s=v.get<std::string>();return s.size()==64&&std::all_of(s.begin(),s.end(),[](unsigned char c){return std::isdigit(c)||(c>='a'&&c<='f');});}
inline std::string lower(std::string s){std::transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return char(std::tolower(c));});return s;}
inline json preflight(const json& job){
    const std::vector<std::string> keys={"execution_profile","runtime_binding","arm","family","target_model","target_sha256","draft_model","draft_sha256","n_ctx","threads","lowering","draft_width","draft","residency","profile","inputs","cases","forced","observe_positions","state_positions","capability_request","k","target_output_reserve","proposal_mode","proposal_tape_requests","same_work","evidence_capture_byte_reservation","actual_q8_capture"};
    for(auto it=job.begin();it!=job.end();++it)need(std::find(keys.begin(),keys.end(),it.key())!=keys.end(),"Unknown e03 native job field before backend initialization");
    const auto profile=job.at("execution_profile").get<std::string>(),arm=job.at("arm").get<std::string>();
    need(profile=="m2_dynamic_request"||profile=="target_q8_capture","unknown explicit e03 execution profile");
    need(arm=="A"||arm=="B"||arm=="C","unknown A/B/C arm");
    need((arm=="A"&&std::string(M1_PROJECTION)=="loop4")||(arm!="A"&&std::string(M1_PROJECTION)=="packed"),"arm does not match linked graph core");
    need(job.at("n_ctx")==1024&&job.at("threads")==24,"fixed context and CPU thread recipe required");
    need(job.at("target_output_reserve")==8,"reserve8 required");
    need(job.at("lowering")=="LOCAL","this prepared e03 profile fixes LOCAL for all arms");
    need(job.at("proposal_mode")=="live","e03 native evidence requires live producer semantics");
    need(!job.value("profile",false),"profiling not admitted by e03 profile");
    need(job.at("evidence_capture_byte_reservation").is_number_unsigned()||job.at("evidence_capture_byte_reservation").is_number_integer(),"capture reservation integer required");
    const auto capture=job.at("evidence_capture_byte_reservation").get<uint64_t>();need(capture>0&&capture<=2147483648ULL,"bounded capture bytes required");
    need(hex64(job.at("target_sha256")),"target SHA required");
    if(profile=="m2_dynamic_request"){
        need(job.at("draft")==true&&job.at("draft_width")==4&&job.at("residency")=="matched","M2 dynamic profile requires actual D4 resident draft");
        need(job.at("k")==3||job.at("k")==7,"M2 k3/7 required");
        need(job.contains("inputs")&&job.at("inputs").is_array()&&!job.at("inputs").empty()&&!job.contains("forced")&&!job.contains("cases"),"M2 request profile must use nonempty real request inputs");
        need(hex64(job.at("draft_sha256"))&&job.at("draft_model").is_string(),"M2 draft identity required");
    }else{
        need(job.at("draft")==false&&job.at("draft_width")==1&&job.at("residency")=="target_only"&&job.at("k")==7,"dedicated q8 capture profile has no draft, reserve8 and width8");
        need(!job.contains("draft_model")&&!job.contains("draft_sha256"),"target-only capture profile must not contain unused draft identities");
        need((job.contains("forced")!=job.contains("cases"))&&!job.contains("inputs"),"dedicated target q8 profile requires one forced/cases source");
        need(job.contains("actual_q8_capture"),"dedicated target q8 capture contract required");
        need(arm=="A"||arm=="B","C replays the shared admitted operand; dedicated capture oracle is A/B only");
        const auto& capture=job.at("actual_q8_capture");
        need(capture.at("schema")=="heterospec.actual-q8-capture.v1"&&capture.at("arm")==arm&&capture.at("q")==8&&capture.at("weight_type")=="Q8_0"&&capture.at("activation_type")=="F32"&&capture.at("allow_derived_input")==false&&capture.at("phase")=="VERIFY"&&capture.at("weight_name")=="blk.0.attn_q.weight","dedicated capture descriptor contract mismatch");
        need(capture.at("capture_byte_reservation").get<uint64_t>()>0&&capture.at("capture_byte_reservation").get<uint64_t>()<=job.at("evidence_capture_byte_reservation").get<uint64_t>(),"capture subreservation outside worker ceiling");
        auto check_forced=[](const json& calls){need(calls.is_array()&&!calls.empty(),"nonempty forced native input required");bool has_q8=false;for(const auto& call:calls){const auto& ids=call.at("ids");need(ids.is_array()&&!ids.empty(),"nonempty token rows required");for(const auto& id:ids)need(id.is_number_integer()&&id.get<int64_t>()>=0&&id.get<int64_t>()<151936,"token outside frozen vocabulary");if(call.value("phase",std::string("VERIFY"))=="VERIFY"&&ids.size()==8&&call.value("all",true))has_q8=true;}need(has_q8,"actual eight-row requested verification required");};
        if(job.contains("forced"))check_forced(job.at("forced"));else{need(job.at("cases").is_array()&&!job.at("cases").empty(),"nonempty capture cases required");for(const auto& c:job.at("cases"))check_forced(c.at("forced"));}
    }
    const auto& binding=job.at("runtime_binding");
    need(binding.at("schema")=="heterospec.e03.isolated-runtime.v1","runtime binding schema");
    need(binding.at("device_uuid")=="GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd","wrong frozen physical device");
    need(binding.at("graph_policy")=="disabled_for_all_arms_draft_and_reference","common graph policy must be explicit");
    need(binding.at("arm")==arm&&binding.at("budget_family")=="rtx221-round1-20261112-e01","runtime arm/budget family binding");
    need(binding.at("native_release")=="BLOCKED","this prepared epoch cannot self-release native admission");
    const fs::path directory=binding.at("directory").get<std::string>();need(directory.is_absolute(),"isolated absolute bin directory required");
    need(binding.at("modules").is_object()&&binding.at("modules").contains("ggml-cuda.dll")&&binding.at("modules").contains("ggml-base.dll"),"numeric module allowlist incomplete");
    for(auto it=binding.at("modules").begin();it!=binding.at("modules").end();++it){need(fs::path(it.key()).filename().string()==it.key()&&hex64(it.value().at("sha256")),"bad DLL allowlist entry");}
    need(binding.at("expected_runtime_metadata").is_object(),"expected runtime metadata must be externally bound");
    const auto& budget=binding.at("launch_budget");
    need(budget.at("schema")=="heterospec.e03.worker-launch-reservation.v1"&&budget.at("family_limit")==4096&&budget.at("epoch_tag")=="rtx223-round1-20261112-e03","launch budget ABI/family/epoch mismatch");
    const auto inherited=budget.at("inherited_charged").get<uint64_t>(),reserved=budget.at("worker_reservation").get<uint64_t>();
    need(inherited<=4096&&reserved>0&&reserved<=4096-inherited,"launch reservation outside original family cap");
    need(budget.at("coverage")=="UNQUALIFIED_BLOCKED"&&budget.at("expected_metadata").is_object(),"unqualified physical launch coverage cannot be self-released");
    return {{"schema","heterospec.e03.preflight.v1"},{"execution_profile",profile},{"arm",arm},{"linked_graph_core",M1_PROJECTION},{"native_gate","NATIVE_BLOCKED"},{"CUDA_DLL_loads",0},{"model_loads",0},{"contexts",0},{"qualification","NOT_RUN"}};
}
inline void require_native_release(const json&){throw std::runtime_error("NATIVE_BLOCKED: no authenticated parent intent or universal physical-kernel coverage; do not load CUDA DLL");}
inline fs::path loaded_path(HMODULE module){wchar_t text[32768];const DWORD n=GetModuleFileNameW(module,text,32768);need(n>0&&n<32768,"actual loaded module path unavailable");return fs::weakly_canonical(fs::path(text));}
inline json load_isolated_runtime_after_future_release(const json& job){
    // Every caller must pass require_native_release first. It currently always refuses.
    const auto& binding=job.at("runtime_binding");const fs::path directory=fs::weakly_canonical(binding.at("directory").get<std::string>());
    const char* graph=std::getenv("GGML_CUDA_DISABLE_GRAPHS");need(graph&&std::string(graph)=="1","graph policy not actually configured");
    for(const auto& entry:fs::directory_iterator(directory))if(lower(entry.path().extension().string())==".dll")need(binding.at("modules").contains(lower(entry.path().filename().string())),"unlisted DLL in isolated numerical directory");
    for(auto it=binding.at("modules").begin();it!=binding.at("modules").end();++it){
        const auto path=directory/it.key();need(hash_file(path)==it.value().at("sha256"),"runtime DLL disk hash changed");
        if(auto old=GetModuleHandleW(fs::path(it.key()).c_str()))need(loaded_path(old)==fs::weakly_canonical(path),"old/foreign numerical DLL already resolved");
    }
    auto base=LoadLibraryExW((directory/"ggml-base.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(base,"isolated base DLL load failed");
    auto runtime=LoadLibraryExW((directory/"ggml-cuda.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);need(runtime,"isolated CUDA DLL load failed");
    need(loaded_path(runtime)==fs::weakly_canonical(directory/"ggml-cuda.dll"),"actual CUDA DLL resolved to wrong path");
    auto metadata=reinterpret_cast<const char*(*)()>(GetProcAddress(runtime,"hs_e03_runtime_metadata"));
    auto select=reinterpret_cast<int(*)(int)>(GetProcAddress(runtime,"hs_e03_select_arm"));
    auto selected=reinterpret_cast<int(*)()>(GetProcAddress(runtime,"hs_e03_selected_arm"));
    auto budget_metadata=reinterpret_cast<const char*(*)()>(GetProcAddress(runtime,"hs_launch_budget_metadata_v1"));
    auto configure=reinterpret_cast<int(*)(uint64_t,uint64_t,uint64_t,const char*)>(GetProcAddress(runtime,"hs_launch_budget_configure_v1"));
    struct BudgetSnapshot {uint64_t abi_version,family_limit,inherited_charged,worker_reservation,admitted_attempts,rejected_attempts;int32_t terminal_code,configured;};
    static_assert(sizeof(BudgetSnapshot)==56,"budget ABI1 layout");
    auto snapshot=reinterpret_cast<int(*)(BudgetSnapshot*)>(GetProcAddress(runtime,"hs_launch_budget_snapshot_v1"));
    need(metadata&&select&&selected&&budget_metadata&&configure&&snapshot,"missing e03 numerical identity/budget exports");
    const auto actual=json::parse(metadata());need(actual==binding.at("expected_runtime_metadata"),"runtime metadata identity differs");
    const auto& budget=binding.at("launch_budget");need(json::parse(budget_metadata())==budget.at("expected_metadata"),"launch budget metadata differs from frozen ABI");
    const auto epoch=budget.at("epoch_tag").get<std::string>();const int configure_result=configure(budget.at("family_limit").get<uint64_t>(),budget.at("inherited_charged").get<uint64_t>(),budget.at("worker_reservation").get<uint64_t>(),epoch.c_str());
    BudgetSnapshot observed{};need(snapshot(&observed)==0&&observed.abi_version==1,"launch budget snapshot ABI unavailable");
    need(configure_result==0&&observed.configured==1,"physical kernel budget configuration refused before backend/context/model initialization");
    need(observed.family_limit==budget.at("family_limit")&&observed.inherited_charged==budget.at("inherited_charged")&&observed.worker_reservation==budget.at("worker_reservation")&&observed.admitted_attempts==0,"launch budget differs or work preceded admission");
    const auto arm=job.at("arm").get<std::string>();const int request=arm=="A"?0:(arm=="B"?1:2);const int result=select(request);
    need(result==0&&selected()==request,"runtime arm selector refused or readback mismatched");
    json modules=json::array();for(auto it=binding.at("modules").begin();it!=binding.at("modules").end();++it){auto h=GetModuleHandleW(fs::path(it.key()).c_str());need(h,"declared runtime dependency not actually loaded");const auto path=loaded_path(h);need(path==fs::weakly_canonical(directory/it.key())&&hash_file(path)==it.value().at("sha256"),"actual loaded dependency identity mismatch");modules.push_back({{"path",path.string()},{"sha256",hash_file(path)},{"basis","loaded path disk hash, not memory hash"}});}
    return {{"arm_requested",arm},{"selector_return",result},{"runtime_metadata",actual},{"loaded_modules",modules},{"actual_numeric_route_observed",false},{"route_qualification","NOT_RUN"}};
}
}
