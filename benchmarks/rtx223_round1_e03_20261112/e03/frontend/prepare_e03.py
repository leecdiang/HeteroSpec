from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('anchor count '+repr(old[:100]))
    return text.replace(old,new,1)
def main():
    src=ROOT/'continuation/frontend/hooked_frontend_v7';out=HERE/'source-v4';shutil.copytree(src,out)
    shutil.copy2(HERE/'e03_binding.hpp',out/'e03_binding.hpp')
    p=out/'worker.cpp';s=p.read_text(encoding='utf8');s=once(s,'#include "hs_round1_hooks.hpp"','#include "hs_round1_hooks.hpp"\n#include "e03_binding.hpp"');p.write_text(s,encoding='utf8',newline='\n')
    p=out/'entry.cpp';s=p.read_text(encoding='utf8');s=once(s,'    const auto phase1_main_started=Clock::now();','''    if(argc==3&&(std::string(argv[1])=="--e03-preflight"||std::string(argv[1])=="--e03-native-gate")){
        try{const auto job=load(argv[2]);const auto receipt=hs_e03::preflight(job);if(std::string(argv[1])=="--e03-native-gate")hs_e03::require_native_release(job);std::cout<<receipt.dump()<<std::endl;return 0;}
        catch(const std::exception&e){std::cout<<json({{"status","REJECTED_BEFORE_BACKEND"},{"reason",e.what()},{"CUDA_DLL_loads",0},{"models",0}}).dump()<<std::endl;return 2;}
    }
    const auto phase1_main_started=Clock::now();''')
    anchor='need(argc==3,"phase worker JOB OUT");const auto job=load(argv[1]);root=argv[2];need(!fs::exists(root),"fresh native output");fs::create_directories(root);'
    s=once(s,anchor,anchor+'\n        const auto e03_profile=hs_e03::preflight(job);hs_e03::require_native_release(job);\n        const auto e03_runtime=hs_e03::load_isolated_runtime_after_future_release(job);')
    s=once(s,'need(phase_target_reserve==8&&(m2_k==3||m2_k==7)&&job.at("draft")==true&&job.at("draft_width")==4,"M2 explicit k3/7 reserve8 D4 contract");','need(e03_profile.at("execution_profile")=="target_q8_capture"||(phase_target_reserve==8&&(m2_k==3||m2_k==7)&&job.at("draft")==true&&job.at("draft_width")==4),"explicit profile contract mismatch");')
    s=once(s,'const auto bin=fs::path(exe).parent_path();','const auto bin=fs::path(job.at("runtime_binding").at("directory").get<std::string>());')
    s=once(s,'const std::string residency=job.value("residency",std::string("matched"));','result["e03_preflight"]=e03_profile;result["e03_runtime_binding"]=e03_runtime;\n        const std::string residency=job.value("residency",std::string("matched"));')
    p.write_text(s,encoding='utf8',newline='\n')
    p=out/'m1_capability.hpp';s=p.read_text(encoding='utf8')
    s=once(s,'"same_work"};','"same_work","execution_profile","runtime_binding","arm","evidence_capture_byte_reservation","actual_q8_capture"};')
    anchor='    need(d && pool.draft && spec.draft && (spec.k==3||spec.k==7) && phase_draft_width==4 && phase_target_reserve==8,"M2 real k3/7 reserve8 D4 required");'
    s=once(s,anchor,'''    if(job.at("execution_profile")=="target_q8_capture"){
        need(!d&&!pool.draft&&!spec.draft&&phase_draft_width==1&&phase_target_reserve==8,"target q8 profile must actually have no draft");
        const auto target_hash=hash_file(job.at("target_model").get<std::string>());need(target_hash==job.at("target_sha256"),"target capture model hash mismatch");
        json echo={{"schema","heterospec.e03.target-q8-capability.v1"},{"execution_profile","target_q8_capture"},{"target_sha256",target_hash},{"target_structure",m1_structure(t)},{"target_context",m1_context(*pool.target)},{"target_placement",m1_placement(t)},{"projection",M1_PROJECTION},{"arm",job.at("arm")},{"draft",false},{"target_output_reserve",phase_target_reserve},{"reference_scope","dedicated projection capture; no M2/service qualification"}};
        dump(root/"CAPABILITY.json",echo);need(echo==job.at("capability_request"),"dedicated target q8 capability differs from frozen contract");result["native_capability"]=echo;return;
    }
'''+anchor)
    p.write_text(s,encoding='utf8',newline='\n')
    record={'status':'SOURCE_PREPARED_NATIVE_HARD_BLOCKED','parent_frontend':'continuation/frontend/hooked_frontend_v7','source':str(out),'profiles':['m2_dynamic_request','target_q8_capture'],'native_release':'BLOCKED','models':0,'CUDA_DLL_normal_loads':0,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
    (HERE/'SOURCE_v4.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
