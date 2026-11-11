void equivalent(const json&a,const json&b,bool trace){
 for(auto k:{"ids","eog","length","terminal_id","stop_reason"})need(a.at(k)==b.at(k),"reference endpoint mismatch");
 if(trace)need(a.at("cycles")==b.at("cycles"),"reference state mismatch");
}
int main(int argc,char**argv){
 whole=Clock::now();llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;
 json result={{"status","STARTED"},{"requests",json::array()}};
 auto cleanup=[&](){if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
 try{
  need(argc==8,"draft_cpu OUTPUT TARGET DRAFT PANEL MODE INDEX STUDY_ROOT");
  root=argv[1];need(!fs::exists(root),"fresh output");fs::create_directories(root);
  std::ifstream fi(argv[4]);json panel;fi>>panel;std::string mode=argv[5];int index=std::stoi(argv[6]);fs::path study=argv[7];
  need((mode=="qual"||mode=="time")&&index>=0&&index<4,"mode/index");deadline=mode=="qual"?170:590;
  result["mode"]=mode;result["index"]=index;dump(root/"result.json",result);
  llama_backend_init();initialized=true;ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("B570")!=std::string::npos){need(!gpu,"ambiguous");gpu=x;}}
  need(gpu,"B570 absent");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*){return seconds(whole)<deadline;};
  auto ls=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");
  result["model_load_seconds"]=seconds(ls);
  const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);
  need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"vocab");
  auto run=[&](const json&input,std::string label,bool capture,std::string category){
   draft_threads=label=="DRAFT1"?1:8;std::string arm=label=="R"?"R":"QB";
   auto prompt=input["prompt_ids"].get<std::vector<int>>();need(prompt.size()+int(input["cap"])+2<512,"extent");
   auto st=Clock::now();auto o=request(t,d,prompt,arm,root/(category+"-"+std::to_string(result["requests"].size())),capture,int(input["cap"]));
   o.record["service_seconds"]=seconds(st);o.record["label"]=label;o.record["input_id"]=input["id"];o.record["category"]=category;
   result["requests"].push_back(o.record);dump(root/"result.json",result);return o.record;
  };
  fs::path prior="C:/hs/b570-formal-request-20261020";
  if(mode=="qual"){
   auto x=run(panel["inputs"][index],"DRAFT1",true,"qual");
   auto old=prior/("qual-"+std::to_string(index));std::ifstream f(old/"result.json");json ref;f>>ref;
   need(ref["status"]=="QUALIFICATION_PASS","prior qualification");
   equivalent(ref["requests"][2],x,true);
   int matched=0;
   for(auto&e:fs::recursive_directory_iterator(old/"qual-2"))if(e.is_regular_file()&&e.path().extension()==".f32"){
    auto rel=fs::relative(e.path(),old/"qual-2");std::ifstream a(e.path(),std::ios::binary),b(root/"qual-0"/rel,std::ios::binary);
    std::vector<char>aa((std::istreambuf_iterator<char>(a)),{}),bb((std::istreambuf_iterator<char>(b)),{});
    need(!aa.empty()&&aa==bb,"historical QB full logits byte mismatch");matched++;
   }
   int actual=0;for(auto&e:fs::recursive_directory_iterator(root/"qual-0"))if(e.is_regular_file()&&e.path().extension()==".f32")actual++;
   need(matched==actual&&actual>0,"raw inventory");
   result["historical_full_logits_matched"]=matched;result["status"]="QUALIFICATION_PASS";
  }else{
   std::vector<std::vector<std::string>>orders={{"R","BASE_A","DRAFT1","BASE_B"},{"BASE_A","BASE_B","R","DRAFT1"},{"BASE_B","DRAFT1","BASE_A","R"},{"DRAFT1","R","BASE_B","BASE_A"}};
   std::ifstream f("C:/hs/b570-spec-bridge-20261020200000/results/result.json");json warm;f>>warm;
   for(auto label:orders[index]){auto x=run(panel["warmup"],label,false,"warmup");equivalent(warm["requests"][label=="R"?0:2],x,label!="R");}
   for(int j=0;j<4;j++){
    int task=(index+j)%4;std::ifstream f(prior/("qual-"+std::to_string(task))/"result.json");json ref;f>>ref;
    std::ifstream gate(study/("qual-"+std::to_string(task))/"result.json");json g;gate>>g;need(g["status"]=="QUALIFICATION_PASS","candidate not qualified");
    for(auto label:orders[(index+task)%4]){
     auto x=run(panel["inputs"][task],label,false,"steady");equivalent(ref["requests"][label=="R"?0:2],x,label!="R");
    }
   }
   result["status"]="TIMING_PASS";
  }
  cleanup();result["normal_cleanup_returned"]=true;dump(root/"result.json",result);return 0;
 }catch(const std::exception&e){result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<"\n";return 2;}
}
