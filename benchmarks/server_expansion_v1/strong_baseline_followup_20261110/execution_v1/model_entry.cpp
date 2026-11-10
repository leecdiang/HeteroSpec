// The included, pinned frontend is copied and explicitly patched by build_model.
// This adapter cannot start a GPU without a phase-bound host reservation.
#include <set>
#include "work_counts.h"
#include "loaded_modules.hpp"
#include "entry.cpp"
static json strong_echo(const json& j) {
    need(j.at("arm")=="G"||j.at("arm")=="B"||j.at("arm")=="C","Unknown strong arm");
    for(const char* k:{"n_ctx","n_ubatch","output_reserve","threads"})
        need(j.at(k).is_number_integer(),"Integer runtime parameter");
    need(j.at("n_ctx")==1024&&j.at("n_ubatch")==32&&j.at("output_reserve")==32,"Strong context/UB/reserve");
    need(j.at("kv")=="F16"&&j.at("flash_attention")==false&&j.at("cuda_graphs")==false,"Strong common policy");
    need(j.at("lowering")=="WHOLE"&&j.at("draft")==false&&j.at("residency")=="target_only"&&
         j.at("k")==0&&j.at("draft_width")==1&&j.at("target_output_reserve")==32&&
         j.at("proposal_mode")=="live","Target-only whole contract");
    need(j.at("threads").get<int>()>=1&&j.at("threads").get<int>()<=2,"Allocated CPU threads");
    if(j.contains("inputs"))for(const auto& entry:j.at("inputs")){
        const auto& input=entry.at("input");need(input.at("cap").is_number_integer(),"Integer M length cap");
        need(hs_m_input_valid(input.at("prompt_ids").size(),input.at("cap").get<int>(),1024),"M input/capacity contract");
        for(const auto& token:input.at("prompt_ids"))need(token.is_number_integer()&&token.get<int>()>=0&&token.get<int>()<151936,"M token identity");
    }
    return {{"arm",j.at("arm")},{"n_ctx",1024},{"n_ubatch",32},{"output_reserve",32},
            {"kv","F16"},{"flash_attention",false},{"cuda_graphs",false},{"lowering","WHOLE"},
            {"draft",false},{"scope","CPU_PARSE_ONLY_NOT_GPU_QUALIFICATION"},{"cuda_initialized",false},
            {"planned_native_planner","SIMPLE"},
            {"dispatch",j.at("arm")=="G"?"graph_scalar_columns":j.at("arm")=="B"?
              "one_backend_entry_batch_quant_then_scalar_dispatch_loop":"independent_channels_ne11_1"}};
}
int main(int argc,char** argv) {
    try {
        need(argc==3,"--echo JOB or JOB OUT");
        bool echo=std::string(argv[1])=="--echo";
        json job=load(echo?argv[2]:argv[1]);auto cfg=strong_echo(job);
        if(echo){std::cout<<cfg.dump()<<'\n';return 0;}
        const char* p=std::getenv("HS_STRONG_GPU_ADMISSION_FILE");need(p&&*p,"GPU disabled without host reservation");
        json grant=load(p);const char* gpu=std::getenv("CUDA_VISIBLE_DEVICES");
        need(gpu&&grant.at("schema")=="hs.strong.native-reservation.v1"&&(grant.at("phase")=="S1"||grant.at("phase")=="S3")&&
             grant.at("GPU_authorized")==true&&grant.at("complete_F0_readback")==true&&
             grant.at("budget_reserved")==true&&grant.at("private_gpu_uuid")==gpu&&
             grant.at("job_sha256")==hash_file(argv[1]),"Invalid model reservation/freeze/GPU binding");
        if(grant.at("phase")=="S3")need(grant.at("complete_F2_readback")==true&&
             grant.at("numerically_qualified")==true&&grant.at("new_root_oracles_frozen")==true,
             "S3 requires separate input, oracle, source, qualification and budget admission");
        std::string arm=job.at("arm");need(hs_strong_select_arm_once(arm=="G"?1:arm=="B"?2:3),"Immutable arm selection");
        sb217_operand_configure(job,argv[2]);
        int rc=sb217_legacy_main(argc,argv);
        if(rc==0&&job.value("capture_operands",false))dump(fs::path(argv[2])/"OPERAND_COMPLETENESS.json",sb217_operand_complete());
        return rc;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
