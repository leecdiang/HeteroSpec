void equivalent(const json&a,const json&b,bool trace){
 for(auto k:{"ids","eog","length","terminal_id","stop_reason"})need(a.at(k)==b.at(k),"reference endpoint mismatch");
 if(trace)need(a.at("cycles")==b.at("cycles"),"reference state mismatch");
}
json read_json(fs::path p){std::ifstream f(p);need(bool(f),"reference file absent");json j;f>>j;return j;}
int compare_vectors(fs::path a,fs::path b){
 int count=0,other=0;
 for(auto&e:fs::recursive_directory_iterator(a))if(e.is_regular_file()&&e.path().extension()==".f32"){
  auto rel=fs::relative(e.path(),a);std::ifstream fa(e.path(),std::ios::binary),fb(b/rel,std::ios::binary);
  std::vector<char>x((std::istreambuf_iterator<char>(fa)),{}),y((std::istreambuf_iterator<char>(fb)),{});
  need(!x.empty()&&x==y,"historical full logits mismatch");count++;
 }
 for(auto&e:fs::recursive_directory_iterator(b))if(e.is_regular_file()&&e.path().extension()==".f32")other++;
 need(count==other&&count>0,"full vector inventory mismatch");return count;
}
int main(int argc,char**argv){
 whole=Clock::now();llama_model*t=nullptr,*d=nullptr;bool initialized=false;fs::path root;
 json result={{"status","STARTED"},{"requests",json::array()}};
 auto cleanup=[&](){if(d){llama_model_free(d);d=nullptr;}if(t){llama_model_free(t);t=nullptr;}if(initialized){llama_backend_free();initialized=false;}};
 try{
  need(argc==8,"closeout OUTPUT TARGET DRAFT PANEL MODE INDEX STUDY_ROOT");
  root=argv[1];need(!fs::exists(root),"fresh output");fs::create_directories(root);
  json panel=read_json(argv[4]);std::string mode=argv[5];int index=std::stoi(argv[6]);fs::path study=argv[7];
  need((mode=="E0"&&index==0)||((mode=="E1"||mode=="E2")&&index>=0&&index<4),"mode/index");
  deadline=mode=="E0"?170:(mode=="E1"?590:1190);
  result["mode"]=mode;result["index"]=index;dump(root/"result.json",result);
  llama_backend_init();initialized=true;ggml_backend_dev_t gpu=nullptr;
  for(size_t i=0;i<ggml_backend_dev_count();i++){auto*x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("B570")!=std::string::npos){need(!gpu,"ambiguous B570");gpu=x;}}
  need(gpu,"B570 absent");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
  mp.progress_callback=[](float,void*){return seconds(whole)<deadline;};
  auto ls=Clock::now();t=llama_model_load_from_file(argv[2],mp);need(t,"target load");d=llama_model_load_from_file(argv[3],mp);need(d,"draft load");
  result["model_load_seconds"]=seconds(ls);
  const auto*tv=llama_model_get_vocab(t);const auto*dv=llama_model_get_vocab(d);
  need(llama_vocab_n_tokens(tv)==llama_vocab_n_tokens(dv),"vocab size");
  for(int i=0;i<llama_vocab_n_tokens(tv);i++)need(strcmp(llama_vocab_get_text(tv,i),llama_vocab_get_text(dv,i))==0&&llama_vocab_is_eog(tv,i)==llama_vocab_is_eog(dv,i),"tokenizer identity");
  auto run=[&](const json&input,std::string label,bool capture,std::string category,std::string slot){
   bulk_prefill=label=="SUBMIT";std::string arm=label=="R"?"R":"QB";
   auto prompt=input["prompt_ids"].get<std::vector<int>>();need(prompt.size()+int(input["cap"])+2<512,"extent");
   auto request_dir=root/("request-"+std::to_string(result["requests"].size()));
   auto st=Clock::now();auto o=request(t,d,prompt,arm,request_dir,capture,int(input["cap"]));
   o.record["service_seconds"]=seconds(st);
   o.record["label"]=label;o.record["input_id"]=input["id"];o.record["category"]=category;
   o.record["slot"]=slot;o.record["raw_dir"]=request_dir.filename().string();
   result["requests"].push_back(o.record);dump(root/"result.json",result);return o.record;
  };
  fs::path prior="C:/hs/b570-formal-request-20261020";
  if(mode=="E0"||mode=="E1"){
   json input=mode=="E0"?panel["warmup"]:panel["inputs"][index];
   json ref=mode=="E0"?read_json("C:/hs/b570-spec-bridge-20261020200000/results/result.json"):read_json(prior/("qual-"+std::to_string(index))/"result.json");
   std::vector<std::string>arms=mode=="E0"?std::vector<std::string>{"BASE","SUBMIT"}:std::vector<std::string>{"R","BASE","SUBMIT"};
   std::map<std::string,json>captures;
   for(auto label:arms){
    auto slot=mode+"/"+std::to_string(index)+"/"+label;
    auto a=run(input,label,true,"capture",slot+"/capture");
    equivalent(ref["requests"][label=="R"?0:2],a,label!="R");
    fs::path rawref=mode=="E0"?fs::path("C:/hs/b570-spec-bridge-20261020200000/results/QB"):(prior/("qual-"+std::to_string(index))/(label=="R"?"qual-0":"qual-2"));
    result["raw_vectors_matched"][label]=compare_vectors(rawref,root/a["raw_dir"].get<std::string>());
    captures[label]=a;
    auto b=run(input,label,false,"count",slot+"/count");
    equivalent(a,b,label!="R");
   }
   auto base=read_json(root/captures["BASE"]["raw_dir"].get<std::string>()/"prefill-events.json");
   auto submit=read_json(root/captures["SUBMIT"]["raw_dir"].get<std::string>()/"prefill-events.json");
   need(base==submit,"prefill layer/ubatch/key/mask metadata or state mismatch");
   result["prefill_event_sequences_equal"]=true;result["prefill_qk_events"]=base["qk"].size();
   result["status"]=mode+"_PASS";
  }else{
   need(read_json(study/"QUALIFICATION_AUDIT.json")["status"]=="E1_FULL_PASS","independent E1 gate absent");
   auto order=read_json(study/"ORDER.json");
   for(auto row:order){
    if(row["session"]!=index)continue;
    int i=row["input_index"];std::string label=row["arm"],category=row["category"];
    auto ref=read_json(prior/("qual-"+std::to_string(i))/"result.json");
    auto x=run(panel["inputs"][i],label,false,category,row["slot"]);
    equivalent(ref["requests"][label=="R"?0:2],x,label!="R");
   }
   need(result["requests"].size()==32,"incomplete session");result["status"]="E2_PASS";
  }
  cleanup();result["normal_cleanup_returned"]=true;dump(root/"result.json",result);return 0;
 }catch(const std::exception&e){
  result["status"]="STOPPED_FIRST_FAILURE";result["error"]=e.what();cleanup();result["normal_cleanup_returned"]=true;
  if(!root.empty())dump(root/"result.json",result);std::cerr<<e.what()<<"\n";return 2;
 }
}
