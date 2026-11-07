from pathlib import Path
import json,shutil,hashlib
r=Path(__file__).parent;p=Path("C:/hs/b570-spec-bridge-20261020200000")
s=(p/"spec_bridge.cpp").read_text()
prefix=s[:s.index("int main(int argc,char**argv)")]
main=r'''int main(int argc,char**argv){
 whole=Clock::now();llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;
 json result={{"status","STARTED"},{"requests",json::array()}};
 auto cleanup=[&](){if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
 try{
  need(argc==7,"spec_cost OUTPUT TARGET DRAFT INPUT REFERENCE SESSION");root=argv[1];need(!fs::exists(root),"fresh output");fs::create_directories(root);
  std::ifstream fi(argv[4]),fr(argv[5]);json input,reference;fi>>input;fr>>reference;
  auto prompt=input["prompt_ids"].get<std::vector<int>>();int session=std::stoi(argv[6]);need(session>=0&&session<3,"session");
  llama_backend_init();initialized=true;ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("B570")!=std::string::npos){need(!gpu,"ambiguous");gpu=x;}}
  need(gpu,"B570 absent");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*){return seconds(whole)<45;};
  t=llama_model_load_from_file(argv[2],mp);need(t,"target load");
  d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");
  const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);
  need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab identity");
  std::vector<std::vector<std::string>>orders={{"PQ_A","PQ_B","QB"},{"PQ_B","QB","PQ_A"},{"QB","PQ_A","PQ_B"}};
  result["session"]=session;result["order"]=orders[session];dump(root/"result.json",result);
  for(auto label:orders[session]){
   std::string arm=label=="QB"?"QB":"PQ";
   auto o=request(t,d,prompt,arm,root/label,false);
   o.record["label"]=label;result["requests"].push_back(o.record);dump(root/"result.json",result);
   const auto&ref=reference["requests"][1];
   for(auto field:{"ids","eog","length","terminal_id","stop_reason","cycles"})need(o.record[field]==ref[field],"reference endpoint/state mismatch");
   result["requests"].back()["reference_endpoint_and_cycles_match"]=true;dump(root/"result.json",result);
  }
  cleanup();result["normal_cleanup_returned"]=true;result["status"]="COST_SESSION_PASS";dump(root/"result.json",result);return 0;
 }catch(const std::exception&e){result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<"\n";return 2;}
}
'''
# One explicit operational difference: longer per-process cooperative deadline.
prefix=prefix.replace('seconds(whole)<35,"internal deadline"','seconds(whole)<45,"internal deadline"')
(r/"spec_cost.cpp").write_text(prefix+main)
for n in ("INPUT.json","MODEL_IDENTITY.json"):
    shutil.copy2(p/n,r/n)
shutil.copy2(p/"results/result.json",r/"QUALIFIED_REFERENCE.json")
(r/"CMakeLists.txt").write_text('''cmake_minimum_required(VERSION 3.20)
project(b570_spec_cost LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(spec_cost spec_cost.cpp)
target_include_directories(spec_cost PRIVATE "C:/hs/b570-direct-id-v1-src/include" "C:/hs/b570-direct-id-v1-src/ggml/include" "C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/pr97/dependencies/pinned-source/vendor")
target_compile_options(spec_cost PRIVATE /O2 /W4 /fp:precise /utf-8)
target_link_libraries(spec_cost PRIVATE "C:/hs/b570-spec-bridge-20261020200000/build/Release/llama.lib" "C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml.lib" "C:/hs/b570-direct-id-v1-build/ggml/src/Release/ggml-base.lib")
''')
reg={"study":"B570_SPECULATIVE_REQUEST_COST","uuid":"c88ca86b-6581-4dc4-8ccb-5882092df22d",
 "authorization":"User explicitly instructed continuation beyond previous remaining-budget barrier after bridge; new prospective bounded accounting, no old reset",
 "old_budget":{"cap":300,"cumulative":285.6803089,"unused":14.3196911,"status":"PRESERVED_NOT_RESTARTED"},
 "new_study_budget_seconds":180,"native_processes":3,"per_process_deadline":50,"per_process_cleanup_capture_margin":10,
 "internal_cutoff":45,"requests_per_process":3,
 "orders":[["PQ_A","PQ_B","QB"],["PQ_B","QB","PQ_A"],["QB","PQ_A","PQ_B"]],
 "reference":"Successful real q2 bridge: complete16token IDs/EOG/length/terminal/stop and full cycle trace. Full-logit PQ/QB qualification precedes timing and is preserved separately.",
 "input":"Same exposed HumanEval/42,124IDs,16cap,k1,one model pair,no workload-generalization claim",
 "window":"Fresh contexts excluded; target+draft prefill, native proposal/verify/accept/bonus/correction/trim, host sampling and cycle metadata, completion sync included. No observer or raw-file I/O in timed window; comparisons/writeout after.",
 "interpretation":"One Latin rotation across3 independent processes, not all6 permutations; one input/date. Descriptive pilot, no population CI.",
 "benefit_screen":"QB faster than each PQ control in all3 sessions and equal-weight mean reduction greater than max(2percent of dualPQ,largest absolute within-session PQ_A-PQ_B difference). Otherwise no established practical gain.",
 "stop":"First native/reference/capture failure; no automatic retries. No actor/RTL/CPU8. Existing old failures unchanged."}
(r/"PREREGISTRATION.json").write_text(json.dumps(reg,indent=2))
print("Prepared bounded3-session cost study; no GPU run")
