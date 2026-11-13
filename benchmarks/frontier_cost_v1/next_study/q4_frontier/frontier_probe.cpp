// Reuse the unchanged SHA-pinned M2 owner, state export, native guard and store.
// No legacy main, run(), or measured_operation() is invoked by this diagnostic.
#include <functional>
#define main heterospec_legacy_matched_cost_main
#include "matched_cost_probe.cpp"
#undef main

struct Mismatch : std::runtime_error { using std::runtime_error::runtime_error; };
struct Arm { const char * name; std::vector<int> schedule; int shared, frontier; const char * reference; };
static const std::vector<Arm> arms = {
    {"macro_reference",{4,4},8,8,""}, {"macro_reference_repeat",{4,4},8,8,"macro_reference"},
    {"macro_wide",{8},8,8,"macro_reference"}, {"frontier4_reference",{4},4,4,""},
    {"frontier4_wide_trim",{8},4,4,"frontier4_reference"},
    {"frontier5_reference_materialize",{4,1},4,5,""},
    {"frontier5_wide_trim",{8},4,5,"frontier5_reference_materialize"}
};
static json fixed_cases() {
    json cases=json::array();
    for(int p:{248,252}) {
        std::vector<int> history,rows;
        for(int i=0;i<p;++i)history.push_back((3+7*i)%128);
        for(int i=0;i<8;++i)rows.push_back((p+5+11*i)%128);
        cases.push_back({{"name","controlled-p"+std::to_string(p)},{"history",history},{"rows",rows},{"continuation",37}});
    } return cases;
}
static json fixed_libraries() {
    return {{"libggml-cpu.so.0.23.0","c6e6e7451cd331ec3c89e5a8ab417ab3888a59c29585ac33af0c6f0fdf1ae2bc"},
            {"libggml-base.so.0.23.0","301735d962b61d5434b19ab9dfafacc9801db8d1fa0319c54c0446320c31bc8f"},
            {"libllama.so.0.4.0","445a5cc6f2162287ef7ea003eacbd4427797f85ee9138edcbf376764bfa15d53"},
            {"libggml.so.0.23.0","658533d605a997f2850ccc51d1dcacc020b1fa33207cc4d6da3c817e89819813"}};
}
static json work_counts() {
    auto value=counters();
    value["prefill_calls"]=hsc::w.target_prefill_calls;
    value["prefill_rows"]=hsc::w.target_prefill_rows;
    value["total_native_calls"]=hsc::w.target_calls+hsc::w.target_prefill_calls;
    value["total_target_rows"]=hsc::w.target_rows+hsc::w.target_prefill_rows;
    return value;
}
template<class F> static json counted(Owner & owner,int base,size_t nc,size_t nr,const std::string & stage,F fn) {
    owner.budget.reserve(nc,nr,stage);hsc::begin("counts",base);
    auto finish=[&]() { owner.budget.finish(hsc::w.target_calls+hsc::w.target_prefill_calls,
                                          hsc::w.target_rows+hsc::w.target_prefill_rows,stage); };
    try { fn(); } catch(...) { finish();throw; }
    finish();auto count=work_counts();
    need(count["total_native_calls"]==nc && count["total_target_rows"]==nr,"reserved/observed native work differs");
    return count;
}
static void finite(const std::vector<float> & values) {
    for(float value:values)need(std::isfinite(value),"nonfinite full vocabulary vector");
}
static void blob_check(json & run,const json & reference,const char * name) {
    const bool equal=run.at("captures").at(name)==reference.at("captures").at(name);
    run["checks"][name]=equal;
    if(!equal)throw Mismatch(std::string("required blob mismatch: ")+name);
}
static void geometry_check(json & run,const json & reference,const char * name) {
    const bool equal=run.at(name)==reference.at(name);run["checks"][name]=equal;
    if(!equal)throw Mismatch(std::string("required geometry mismatch: ")+name);
}
static json inspected_geometry(Owner & owner,int next,json & record,const char * stage,
                               const std::function<void()> & save) {
    record["geometry_check_stage"]=stage;record["geometry_expected_next"]=next;
    try { return owner.geometry(next); }
    catch(...) {
        auto * cache=owner.cache();const auto & cells=cache->get_cells(0);
        record["rejected_native_geometry"]={{"used",cells.get_used()},{"used_min",cells.used_min()},
            {"occupied_end",cells.used_max_p1()},{"extent",cache->phase_current_extent()},
            {"next_q1_extents",cache->phase_append_requirements(next,1)},
            {"expected_next",next},{"exact_head_value_observed",false}};
        save();throw;
    }
}
static void run_arm(llama_model * model,Budget & budget,Store & store,uint64_t & trims,
                    const json & input,const Arm & arm,json & record,const json * reference,
                    const std::function<void()> & save) {
    const auto history=input.at("history").get<std::vector<int>>();
    auto values=input.at("rows").get<std::vector<int>>();
    const int base=int(history.size()),n=std::accumulate(arm.schedule.begin(),arm.schedule.end(),0);
    const size_t vocabulary=llama_vocab_n_tokens(llama_model_get_vocab(model));values.resize(n);
    const std::string stage=input.at("name").get<std::string>()+"/"+arm.name;
    record={{"case",input.at("name")},{"arm",arm.name},{"schedule",arm.schedule},{"base",base},
            {"shared_rows",arm.shared},{"frontier",arm.frontier},{"reference",arm.reference},
            {"status","STARTED"},{"checks",json::object()},{"captures",json::object()},
            {"counts",json::object()},{"trim_calls",0},{"requested_operation_rows",n}};
    save();Owner owner(model,budget,1);
    record["counts"]["prefill"]=counted(owner,0,(history.size()+31)/32,history.size(),stage+"/prefill",[&]() {
        for(size_t p=0;p<history.size();p+=32) {
            const size_t end=std::min(history.size(),p+32);
            owner.decode(std::vector<int>(history.begin()+p,history.begin()+end),int(p),false,"PREFILL",stage+"/prefill",false);
        }
    });
    auto initial=owner.state();record["captures"]["initial_state"]=store.put(initial);
    record["initial_geometry"]=inspected_geometry(owner,base,record,"initial_geometry",save);record["checkpoint"]="INITIAL";save();
    if(reference) { blob_check(record,*reference,"initial_state");geometry_check(record,*reference,"initial_geometry"); }
    owner.plan.clear();std::vector<float> all;
    record["counts"]["operation"]=counted(owner,base,arm.schedule.size(),values.size(),stage+"/operation",[&]() {
        all=operation(owner,values,base,arm.schedule,stage+"/operation");
    });
    need(all.size()==size_t(n)*vocabulary,"operation vector size");
    record["executions"]=owner.plan.executions;
    record["captures"]["all_operation_vectors"]=store.put(all.data(),all.size()*sizeof(float));
    record["captures"]["shared_operation_vectors"]=store.put(all.data(),size_t(arm.shared)*vocabulary*sizeof(float));
    record["all_operation_vectors_finite_diagnostic"]=std::all_of(all.begin(),all.end(),[](float x){return std::isfinite(x);});
    if(arm.frontier==5) {
        record["captures"]["fifth_vector_diagnostic"]=store.put(all.data()+4*vocabulary,vocabulary*sizeof(float));
        record["fifth_vector_is_primary_contract"]=false;
        if(reference)record["fifth_vector_diagnostic_equal"]=record["captures"]["fifth_vector_diagnostic"]==reference->at("captures").at("fifth_vector_diagnostic");
    }
    record["checkpoint"]="OPERATION_VECTORS_CAPTURED";save();
    finite(std::vector<float>(all.begin(),all.begin()+size_t(arm.shared)*vocabulary));
    auto post_operation=owner.state();record["captures"]["untrimmed_state"]=store.put(post_operation);
    record["untrimmed_geometry"]=inspected_geometry(owner,base+n,record,"untrimmed_geometry",save);record["checkpoint"]="OPERATION_CAPTURED";save();
    if(reference)blob_check(record,*reference,"shared_operation_vectors");
    if(n>arm.frontier) {
        need(trims<4,"trim call budget exceeded");++trims;record["trim_calls"]=1;
        need(llama_memory_seq_rm(llama_get_memory(owner.c),0,base+arm.frontier,-1),"trim rejected");
    }
    auto final=owner.state();record["captures"]["final_state"]=store.put(final);
    record["final_geometry"]=inspected_geometry(owner,base+arm.frontier,record,"final_geometry",save);record["checkpoint"]="FRONTIER_CAPTURED";save();
    if(reference) { blob_check(record,*reference,"final_state");geometry_check(record,*reference,"final_geometry"); }
    owner.plan.clear();std::vector<float> continuation;
    record["counts"]["continuation"]=counted(owner,base+arm.frontier,1,1,stage+"/continuation",[&]() {
        owner.decode({input.at("continuation").get<int>()},base+arm.frontier,true,"VERIFY",stage+"/continuation",false);
        auto * p=owner.plan.logits(0);continuation.assign(p,p+vocabulary);
    });
    record["captures"]["continuation_vector"]=store.put(continuation.data(),continuation.size()*sizeof(float));
    record["checkpoint"]="CONTINUATION_VECTOR_CAPTURED";save();finite(continuation);
    auto next=owner.state();
    record["captures"]["continuation_state"]=store.put(next);
    record["continuation_geometry"]=inspected_geometry(owner,base+arm.frontier+1,record,"continuation_geometry",save);
    record["continuation_executions"]=owner.plan.executions;
    record["checkpoint"]="CONTINUATION_CAPTURED";save();
    if(reference) {
        blob_check(record,*reference,"continuation_vector");blob_check(record,*reference,"continuation_state");
        geometry_check(record,*reference,"continuation_geometry");
    }
    record["status"]=reference?"PASS":"REFERENCE_CAPTURED";save();
}
int main(int argc,char ** argv) {
    bool owns=false;fs::path output;Budget budget;Store store;uint64_t trims=0,model_loads=0;
    json result={{"schema","heterospec.q4-frontier-result.v1"},{"status","STARTED"},{"runs",json::array()},
                 {"historical_R_qualification","NOT_ESTABLISHED"},{"performance_admitted",false},{"timing_phase",false},
                 {"natural_acceptance_tested",false},{"production_q8_full_mask_qualified",false}};
    auto save=[&]() { result["work"]=budget.value();result["trim_calls"]=trims;result["model_loads"]=model_loads;
                     result["raw_bytes"]=store.bytes;if(owns)dump(output/"RESULT.json",result); };
    try {
        need(argc==3,"q4_frontier_probe JOB OUT");json job;{std::ifstream input(argv[1]);input>>job;need(bool(input),"job read");}
        output=argv[2];need(!fs::exists(output),"fresh native output required");fs::create_directories(output/"blobs");owns=true;
        store.root=output/"blobs";store.limit=256ull*1024*1024;
        budget.max_contexts=14;budget.max_calls=146;budget.max_rows=3612;
        need(job.at("schema")=="heterospec.q4-frontier-job.v1" && job.at("backend")=="cpu" && job.at("threads")==1,"job profile");
        need(job.at("cases")==fixed_cases(),"frozen known-token histories differ");
        need(job.at("budget")==json({{"contexts",14},{"native_calls",146},{"target_rows",3612},{"trim_calls",4},{"model_loads",1}}),"budget differs");
        need(job.at("raw_byte_limit")==store.limit,"raw byte limit differs");
        need(job.at("expected_native_libraries")==fixed_libraries(),"library profile differs");
        need(job.at("published_source_commit").is_string() && job.at("published_source_commit").get<std::string>().size()==40,"published source identity required");
        result["source_binding"]=job.at("source_binding");result["published_source_commit"]=job.at("published_source_commit");
        result["job_sha256"]=file_sha(argv[1]);result["backend"]="cpu";result["threads"]=1;
        result["reference"]="Same CPU deployment, q4+q4 own-path repeat, fixed LOCAL prefix producer; diagnostic only, not historical R";
        result["frontier5_contract"]="First four shared consumer vectors plus materialized active state/geometry and common forced continuation; fifth output diagnostic only";
        const fs::path model_path=job.at("model").get<std::string>();
        const std::string model_sha="e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044";
        need(fs::file_size(model_path)==7084832 && file_sha(model_path)==model_sha,"synthetic F32 model binding differs");
        result["model"]={{"sha256",model_sha},{"bytes",7084832},{"trained",false}};save();
        const auto lib_dir=job.at("lib_dir").get<std::string>();
        ggml_backend_load_all_from_path(lib_dir.c_str());llama_backend_init();
        for(size_t i=0;i<ggml_backend_dev_count();++i)need(ggml_backend_dev_type(ggml_backend_dev_get(i))!=GGML_BACKEND_DEVICE_TYPE_GPU,"GPU backend forbidden");
        result["native_modules_before"]=native_modules(lib_dir,fixed_libraries());save();
        auto mp=llama_model_default_params();mp.n_gpu_layers=0;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        ++model_loads;save();
        std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(model_path.c_str(),mp),llama_model_free);
        need(bool(model),"model load failed");need(llama_vocab_n_tokens(llama_model_get_vocab(model.get()))==128 && llama_model_n_layer(model.get())==2,"fixture structure differs");
        phase_lowering="LOCAL";phase_target_reserve=8;
        for(const auto & input:fixed_cases()) {
            std::map<std::string,json> references;
            for(const auto & arm:arms) {
                result["runs"].push_back(json::object());auto & record=result["runs"].back();
                const json * reference=std::strlen(arm.reference)?&references.at(arm.reference):nullptr;
                run_arm(model.get(),budget,store,trims,input,arm,record,reference,save);
                if(!reference)references.emplace(arm.name,record);
            }
        }
        need(budget.contexts==14 && budget.calls==146 && budget.rows==3612 && budget.attempted_calls==146 && budget.attempted_rows==3612 && trims==4,"complete panel budget differs");
        result["native_modules_after"]=native_modules(lib_dir,fixed_libraries());
        result["status"]="DIAGNOSTIC_PASS";save();return 0;
    } catch(const Mismatch & error) {
        result["status"]="QUALIFICATION_FAILED";result["error"]=error.what();
        if(!result["runs"].empty()) { result["runs"].back()["status"]="FAIL"; }
        save();return 3;
    } catch(const std::exception & error) {
        result["status"]="GUARD_OR_RUNTIME_FAILED";result["error"]=error.what();
        if(!result["runs"].empty()) { result["runs"].back()["status"]="GUARD_OR_RUNTIME_FAILED"; }
        save();return 2;
    }
}
