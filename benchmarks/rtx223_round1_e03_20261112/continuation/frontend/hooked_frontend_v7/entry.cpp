#include "llama.h"
#include <cstdint>
static uint64_t phase_exports=0,phase_imports=0,phase_contexts=0,phase_heavy_captures=0;
static size_t counted_get(llama_context*c,uint8_t*d,size_t n,llama_seq_id s){++phase_exports;return llama_state_seq_get_data(c,d,n,s);}
static size_t counted_set(llama_context*c,const uint8_t*d,size_t n,llama_seq_id s){++phase_imports;return llama_state_seq_set_data(c,d,n,s);}
static llama_context* counted_context(llama_model*m,llama_context_params p){++phase_contexts;return llama_init_from_model(m,p);}
#define llama_state_seq_get_data counted_get
#define llama_state_seq_set_data counted_set
#define llama_init_from_model counted_context
#define main historical_entry
#include "worker.cpp"
#undef main
#define FRONTIER_PROFILE
#include "profiler.inc"
static bool phase1_profiling=false;
#include "llama-model.h"

#include "m1_capability.hpp"
static json module_inventory(){HMODULE modules[1024];DWORD bytes=0;need(EnumProcessModules(GetCurrentProcess(),modules,sizeof(modules),&bytes)&&bytes<=sizeof(modules),"module inventory bounded");json r=json::array();for(size_t i=0;i<bytes/sizeof(HMODULE);++i){wchar_t name[32768];need(GetModuleFileNameW(modules[i],name,32768)>0,"module path");r.push_back(fs::path(name).string());}return r;}
static json module_disk_inventory(){
    const auto paths=module_inventory();json files=json::array();
    for(const auto& item:paths){const fs::path path=item.get<std::string>();files.push_back({{"path",path.string()},{"bytes",fs::file_size(path)},{"sha256",hash_file(path)},{"basis","loaded module path, disk hash not memory"}});}
    return files;
}
static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){
    ++phase_heavy_captures;
#if PHASE_CANDIDATE
    llama_synchronize(c.c);const int n=llama_vocab_n_tokens(llama_model_get_vocab(c.model));auto*p=c.plan.logits(row);
    fs::create_directories(dir);tpds_decisive::capture_write_new(dir/"frontier.f32",p,size_t(n)*4);
    if(state){const auto size=llama_state_seq_get_size(c.c,0);std::vector<uint8_t> bytes(size);need(llama_state_seq_get_data(c.c,bytes.data(),size,0)==size,"offline state export");tpds_decisive::capture_write_new(dir/"sequence.bin",bytes.data(),bytes.size());}
#else
    if(state)tpds_decisive::capture_existing(c.c,c.model,dir,row);
    else{auto*p=llama_get_logits_ith(c.c,row);need(p,"reference requested row");fs::create_directories(dir);tpds_decisive::capture_write_new(dir/"frontier.f32",p,size_t(llama_vocab_n_tokens(llama_model_get_vocab(c.model)))*4);}
#endif
}
#include "rtx_append.inc"
#include "m2_tapes.hpp"
#include "same_work.hpp"
int main(int argc,char**argv){
    if(argc==2&&std::string(argv[1])=="--selftest")return hs_round1::selftest();
    if(argc==3&&std::string(argv[1])=="--selftest-json")return hs_round1::selftest(fs::path(argv[2]));
    const auto phase1_main_started=Clock::now();
    llama_model*t=nullptr,*d=nullptr;Pair pool;fs::path root;
    try{
        need(argc==3,"phase worker JOB OUT");const auto job=load(argv[1]);root=argv[2];need(!fs::exists(root),"fresh native output");fs::create_directories(root);
        const auto capture_limit=job.at("evidence_capture_byte_reservation").get<uint64_t>();
        need(capture_limit>0&&capture_limit<=2147483648ULL,"bounded capture reservation required before backend/model initialization");
        need(!job.value("profile",false),"profiling not admitted by evidence-byte writer");
        tpds_decisive::capture_byte_limit=capture_limit;
        std::unique_ptr<hs_q8_capture::Capture> actual_q8_capture;
        struct ClearCapture {~ClearCapture(){hs_q8_capture::active=nullptr;}} clear_capture;
        if(job.contains("actual_q8_capture")){actual_q8_capture=std::make_unique<hs_q8_capture::Capture>(hs_q8_capture::json(job.at("actual_q8_capture")));hs_q8_capture::active=actual_q8_capture.get();}
        phase_target_reserve=job.at("target_output_reserve");
        const int m2_k=job.at("k");phase_proposal_mode=job.at("proposal_mode");
        need(phase_target_reserve==8&&(m2_k==3||m2_k==7)&&job.at("draft")==true&&job.at("draft_width")==4,"M2 explicit k3/7 reserve8 D4 contract");
        need(phase_proposal_mode=="live"||phase_proposal_mode=="replay"||phase_proposal_mode=="producer","M2 proposal mode");
        wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);const auto bin=fs::path(exe).parent_path();
        auto base=LoadLibraryW((bin/"ggml-base.dll").c_str());need(base,"base DLL");auto init=(void(*)())GetProcAddress(base,"ggml_time_init");need(init,"shared clock init");init();
        ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();++i){auto x=ggml_backend_dev_get(i);if(ggml_backend_dev_type(x)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"ambiguous GPU");gpu=x;}}need(gpu,"GPU required");
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        json result={{"requests",json::array()},{"trajectories",0},{"token_rows",0},{"modules_before",module_inventory()},{"GPU_device",ggml_backend_dev_description(gpu)}};
        const std::string residency=job.value("residency",std::string("matched"));
        need(residency=="matched" || residency=="target_only","unknown residency");
        const bool target_only=residency=="target_only";
        need(!target_only || !job.value("draft",false),"target-only cannot execute draft");
        auto start=Clock::now();
        t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);
        if(!target_only)d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);
        need(t && (target_only || d),"models");
        result["model_load_s"]=since(start);result["phase1_residency"]=residency;
        const auto*tv=llama_model_get_vocab(t);
        if(d){const auto*dv=llama_model_get_vocab(d);
        need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
        for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");}
#if PHASE_CANDIDATE
        phase_lowering=job.at("lowering");phase_draft_width=job.value("draft_width",1);need(phase_draft_width==1||phase_draft_width==4,"draft width");
        auto spec=ArmSpec{"phase","QB",0,32,m2_k,true,job.value("draft",false)};
#else
        auto spec=arm_spec("R");
#endif
        start=Clock::now();provision(pool,t,d,spec,root/"pool");
        // Match resident model/context occupancy for M and speculative controls.
        if(d && !pool.draft)pool.draft=std::make_unique<Context>(d,1,false,false,false,root/"pool/draft",0);
        result["pool_setup_s"]=since(start);result["vocab"]=llama_vocab_n_tokens(tv);result["eog_ids"]=json::array();for(int i=0;i<llama_vocab_n_tokens(tv);++i)if(llama_vocab_is_eog(tv,i))result["eog_ids"].push_back(i);
        result["model_structure"]={{"layers",t->hparams.n_layer()},{"query_heads",t->hparams.n_head()},{"kv_heads",t->hparams.n_head_kv()},{"head_k",t->hparams.n_embd_head_k()},{"head_v",t->hparams.n_embd_head_v()},{"K_elements",t->hparams.n_embd_k_gqa()},{"V_elements",t->hparams.n_embd_v_gqa()}};
        m1_capability(job,pool,t,d,spec,root,result);
        result["modules_disk_before"]=module_disk_inventory();
        result["executable_disk_sha256"]=hash_file(exe);
        result["models_disk"]={{"target",{{"path",job.at("target_model")},{"sha256",hash_file(job.at("target_model").get<std::string>())}}},{"draft",target_only?json(nullptr):json({{"path",job.at("draft_model")},{"sha256",hash_file(job.at("draft_model").get<std::string>())}})}};
        phase1_profiling=job.value("profile",false);if(phase1_profiling){profile::init();if(!job.contains("append_probes"))profile::begin();}
        if(job.contains("same_work")){same_work(job,result,root,pool);}
        else if(job.contains("proposal_tape_requests")){m2_tapes(job,result,root,pool,d);}
        else if(job.contains("append_probes")){phase1_append(job,result,root,pool);}
        else if(job.contains("forced")||job.contains("cases")){
          const json cases=job.contains("cases")?job.at("cases"):json::array({job});result["cases"]=json::array();
          for(size_t index=0;index<cases.size();++index){
            const auto& one=cases[index];const auto& f=one.at("forced");auto*ctx=pool.target.get();auto case_root=job.contains("cases")?root/one.at("name").get<std::string>():root;ctx->reset(true,case_root/"forced");int position=0;hsc::begin("heavy",int(f.at(0).at("ids").size()));
            const auto wanted=one.at("observe_positions").get<std::vector<int>>(),states=one.at("state_positions").get<std::vector<int>>();
            auto observe=[&](int p,int row){if(std::find(wanted.begin(),wanted.end(),p)!=wanted.end())observe_state(*ctx,case_root/"captures"/std::to_string(p),row,std::find(states.begin(),states.end(),p)!=states.end());};
            for(const auto& call:f){auto tokens=call.at("ids").get<std::vector<int>>();std::string phase=call.value("phase",std::string("VERIFY"));bool all=call.value("all",phase!="PREFILL");
#if PHASE_CANDIDATE
                ctx->decode(tokens,position,all,phase.c_str());for(size_t j=0;j<tokens.size();++j)if(all||j+1==tokens.size())observe(position+int(j)+1,all?int(j):-1);
#else
                if(phase=="PREFILL"){ctx->decode(tokens,position,false,"PREFILL");observe(position+int(tokens.size()),-1);}
                else for(size_t j=0;j<tokens.size();++j){ctx->decode({tokens[j]},position+int(j),false,phase.c_str());observe(position+int(j)+1,-1);}
#endif
                position+=int(tokens.size());result["token_rows"]=result["token_rows"].get<int>()+int(tokens.size());
            }
            json record={{"index",index},{"rows",position},{"graphs_reused",hsc::w.graphs_reused},{"geometry",json::array()}};for(auto& x:ctx->obs.signatures)record["geometry"].push_back(x.second);
#if PHASE_CANDIDATE
            record["target_physical_width_hist"]=width_histogram(hsc::w.target_physical);
            record["draft_physical_width_hist"]=width_histogram(hsc::w.draft_physical);
            record["executions"]=ctx->plan.executions;record["planning_s"]=ctx->plan.planning_s;record["output_copy_s"]=ctx->plan.output_copy_s;
            if(!job.contains("cases"))result["executions"]=ctx->plan.executions;
#endif
            result["cases"].push_back(record);result["trajectories"]=result["trajectories"].get<int>()+1;dump(root/"result.json",result);
          }
        }else{
            for(const auto& entry:job.at("inputs")){
                std::string name=entry.at("name");bool capture=entry.value("capture",false);auto input=entry.at("input");auto dir=root/name;fs::create_directories(dir);
                const auto exports=phase_exports,imports=phase_imports,contexts=phase_contexts,heavy_before=phase_heavy_captures;
                auto r=request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool);
                r["observed_API_calls_within_service"]={{"state_exports",phase_exports-exports},{"state_imports",phase_imports-imports},{"context_creates",phase_contexts-contexts}};
                r["observed_API_calls_within_service"]["heavy_captures"]=phase_heavy_captures-heavy_before;
                // Terminal state is captured within request() for both owners and is included in the measured endpoint.
                r["online_state_exports"]=capture?json(nullptr):json(0);r["online_state_imports"]=0;r["online_reference_replays"]=0;r["online_context_creates"]=0;
#if PHASE_CANDIDATE
                r["executions"]=pool.target->plan.executions;r["planning_s"]=pool.target->plan.planning_s;r["output_copy_s"]=pool.target->plan.output_copy_s;r["first_call_plan_s"]=pool.target->plan.first_call_plan_s;
#endif
                r["phase1_main_to_result_s"]=since(phase1_main_started);
                dump(dir/"receipt.json",r);
                std::cout << "PHASE1_RESULT_READY " << name << " " << r["phase1_main_to_result_s"] << std::endl;
                result["requests"].push_back({{"name",name},{"record",name+"/receipt.json"}});result["trajectories"]=result["trajectories"].get<int>()+1;
                int actual_rows=0;for(auto it=r.at("target_physical_width_hist").begin();it!=r.at("target_physical_width_hist").end();++it)actual_rows+=std::stoi(it.key())*it.value().get<int>();
                for(auto it=r.at("draft_physical_width_hist").begin();it!=r.at("draft_physical_width_hist").end();++it)actual_rows+=std::stoi(it.key())*it.value().get<int>();
                result["token_rows"]=result["token_rows"].get<int>()+actual_rows;dump(root/"result.json",result);
            }
        }
#if PHASE_CANDIDATE
        result["resident_initial_plan_compile_s"]=pool.target->plan.resident_initial_plan_s;
#endif
        if(phase1_profiling && !job.contains("append_probes"))profile::end(root/"cuda-events.json");
        if(actual_q8_capture)actual_q8_capture->require_complete();
        result["total_observed_API_calls"]={{"state_exports",phase_exports},{"state_imports",phase_imports},{"context_creates",phase_contexts}};result["modules_after"]=module_inventory();result["modules_disk_after"]=module_disk_inventory();result["evidence_bytes_before_final_receipt"]={{"limit",tpds_decisive::capture_byte_limit},{"reserved_no_refund",tpds_decisive::capture_bytes_reserved},{"written",tpds_decisive::capture_bytes_written},{"counting","all instrumented binary and JSON writes; includes repeated atomic JSON replacements; stdout excluded and externally bounded"}};pool.draft.reset();pool.target.reset();if(d)llama_model_free(d);d=nullptr;llama_model_free(t);t=nullptr;llama_backend_free();result["status"]="COMPLETE";dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){if(!root.empty()&&fs::exists(root))dump(root/"failure.json",{{"error",e.what()},{"target_owner_invalid",pool.target?json(pool.target->status.invalid):json(nullptr)},{"draft_owner_invalid",pool.draft?json(pool.draft->status.invalid):json(nullptr)}});std::cerr<<e.what()<<std::endl;return 2;}
}
