#include "llama.h"
#include <cstdint>
static uint64_t phase_exports=0,phase_imports=0,phase_contexts=0;
static size_t counted_get(llama_context*c,uint8_t*d,size_t n,llama_seq_id s){++phase_exports;return llama_state_seq_get_data(c,d,n,s);}
static size_t counted_set(llama_context*c,const uint8_t*d,size_t n,llama_seq_id s){++phase_imports;return llama_state_seq_set_data(c,d,n,s);}
static llama_context* counted_context(llama_model*m,llama_context_params p){++phase_contexts;return llama_init_from_model(m,p);}
#define llama_state_seq_get_data counted_get
#define llama_state_seq_set_data counted_set
#define llama_init_from_model counted_context
#define main historical_entry
#include "worker.cpp"
#undef main
#include "llama-model.h"

static json module_inventory(){HMODULE modules[1024];DWORD bytes=0;need(EnumProcessModules(GetCurrentProcess(),modules,sizeof(modules),&bytes),"module inventory");json r=json::array();for(size_t i=0;i<bytes/sizeof(HMODULE);++i){wchar_t name[32768];need(GetModuleFileNameW(modules[i],name,32768)>0,"module path");r.push_back(fs::path(name).string());}return r;}
static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){
#if PHASE_CANDIDATE
    llama_synchronize(c.c);const int n=llama_vocab_n_tokens(llama_model_get_vocab(c.model));auto*p=c.plan.logits(row);
    fs::create_directories(dir);tpds_decisive::capture_write_new(dir/"frontier.f32",p,size_t(n)*4);
    if(state){const auto size=llama_state_seq_get_size(c.c,0);std::vector<uint8_t> bytes(size);need(llama_state_seq_get_data(c.c,bytes.data(),size,0)==size,"offline state export");tpds_decisive::capture_write_new(dir/"sequence.bin",bytes.data(),bytes.size());}
#else
    if(state)tpds_decisive::capture_existing(c.c,c.model,dir,row);
    else{auto*p=llama_get_logits_ith(c.c,row);need(p,"reference requested row");fs::create_directories(dir);tpds_decisive::capture_write_new(dir/"frontier.f32",p,size_t(llama_vocab_n_tokens(llama_model_get_vocab(c.model)))*4);}
#endif
}
int main(int argc,char**argv){
    llama_model*t=nullptr,*d=nullptr;Pair pool;fs::path root;
    try{
        need(argc==3,"phase worker JOB OUT");const auto job=load(argv[1]);root=argv[2];need(!fs::exists(root),"fresh native output");fs::create_directories(root);
        wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);const auto bin=fs::path(exe).parent_path();
        auto base=LoadLibraryW((bin/"ggml-base.dll").c_str());need(base,"base DLL");auto init=(void(*)())GetProcAddress(base,"ggml_time_init");need(init,"shared clock init");init();
        ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();++i){auto x=ggml_backend_dev_get(i);if(ggml_backend_dev_type(x)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"ambiguous GPU");gpu=x;}}need(gpu,"GPU required");
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        json result={{"requests",json::array()},{"trajectories",0},{"token_rows",0},{"modules_before",module_inventory()},{"GPU_device",ggml_backend_dev_description(gpu)}};
        auto start=Clock::now();t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);d=llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(),mp);need(t&&d,"models");result["model_load_s"]=since(start);
        const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");for(int i=0;i<llama_vocab_n_tokens(tv);++i)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab mismatch");
#if PHASE_CANDIDATE
        phase_lowering=job.at("lowering");phase_draft_width=job.value("draft_width",1);need(phase_draft_width==1||phase_draft_width==4,"draft width");
        auto spec=ArmSpec{"phase","QB",0,32,job.value("draft",false)?3:0,true,job.value("draft",false)};
#else
        auto spec=arm_spec("R");
#endif
        start=Clock::now();provision(pool,t,d,spec,root/"pool");
        // Match resident model/context occupancy for M and speculative controls.
        if(!pool.draft)pool.draft=std::make_unique<Context>(d,1,false,false,false,root/"pool/draft",0);
        result["pool_setup_s"]=since(start);result["vocab"]=llama_vocab_n_tokens(tv);result["eog_ids"]=json::array();for(int i=0;i<llama_vocab_n_tokens(tv);++i)if(llama_vocab_is_eog(tv,i))result["eog_ids"].push_back(i);
        result["model_structure"]={{"layers",t->hparams.n_layer()},{"query_heads",t->hparams.n_head()},{"kv_heads",t->hparams.n_head_kv()},{"head_k",t->hparams.n_embd_head_k()},{"head_v",t->hparams.n_embd_head_v()},{"K_elements",t->hparams.n_embd_k_gqa()},{"V_elements",t->hparams.n_embd_v_gqa()}};
        if(job.contains("forced")||job.contains("cases")){
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
            record["executions"]=ctx->plan.executions;record["planning_s"]=ctx->plan.planning_s;record["output_copy_s"]=ctx->plan.output_copy_s;
            if(!job.contains("cases"))result["executions"]=ctx->plan.executions;
#endif
            result["cases"].push_back(record);result["trajectories"]=result["trajectories"].get<int>()+1;dump(root/"result.json",result);
          }
        }else{
            for(const auto& entry:job.at("inputs")){
                std::string name=entry.at("name");bool capture=entry.value("capture",false);auto input=entry.at("input");auto dir=root/name;fs::create_directories(dir);
                const auto exports=phase_exports,imports=phase_imports,contexts=phase_contexts;
                auto r=request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool);
                r["observed_API_calls_within_service"]={{"state_exports",phase_exports-exports},{"state_imports",phase_imports-imports},{"context_creates",phase_contexts-contexts}};
                if(capture){const int row=r["cycles"].empty()?-1:r["cycles"].back().at("accepted").get<int>();observe_state(*pool.target,dir/"target/state/terminal",row);}
                r["online_state_exports"]=capture?json(nullptr):json(0);r["online_state_imports"]=0;r["online_reference_replays"]=0;r["online_context_creates"]=0;
#if PHASE_CANDIDATE
                r["executions"]=pool.target->plan.executions;r["planning_s"]=pool.target->plan.planning_s;r["output_copy_s"]=pool.target->plan.output_copy_s;r["first_call_plan_s"]=pool.target->plan.first_call_plan_s;
#endif
                dump(dir/"receipt.json",r);result["requests"].push_back({{"name",name},{"record",name+"/receipt.json"}});result["trajectories"]=result["trajectories"].get<int>()+1;
                result["token_rows"]=result["token_rows"].get<int>()+int(input.at("prompt_ids").size())+(spec.draft?int(input.at("prompt_ids").size())+8*int(r["cycles"].size()):int(r["ids"].size())-1);dump(root/"result.json",result);
            }
        }
#if PHASE_CANDIDATE
        result["resident_initial_plan_compile_s"]=pool.target->plan.resident_initial_plan_s;
#endif
        result["total_observed_API_calls"]={{"state_exports",phase_exports},{"state_imports",phase_imports},{"context_creates",phase_contexts}};result["modules_after"]=module_inventory();pool.draft.reset();pool.target.reset();llama_model_free(d);d=nullptr;llama_model_free(t);t=nullptr;llama_backend_free();result["status"]="COMPLETE";dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){if(!root.empty()&&fs::exists(root))dump(root/"failure.json",{{"error",e.what()}});std::cerr<<e.what()<<std::endl;return 2;}
}
