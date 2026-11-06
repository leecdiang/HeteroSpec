// Separate known-token mechanism harness. Never enters the natural pilot.
if(req.contains("known_suffix")) {
 auto prelude=req.at("prelude").get<std::vector<int>>();
 auto suffix=req.at("known_suffix").get<std::vector<int>>();
 const int width=req.at("width");
 if(width!=2&&width!=4&&width!=32)throw std::runtime_error("probe width");
 if(input.size()+prelude.size()+suffix.size()+2>1024)throw std::runtime_error("probe context");
 for(auto token:prelude){
  auto b=llama_batch_init(1,0,1);common_batch_add(b,token,int(all.size()),{0},true);
  observer.decode(ctx,b,"target");llama_batch_free(b);all.push_back(token);
 }
 observer.evidence.commit(ctx);
 const auto probe_phase=econ_phase(ctx,observer,width,-1);
 for(size_t at=0;at<suffix.size();at+=width){
  const int count=std::min(size_t(width),suffix.size()-at);auto b=llama_batch_init(count,0,1);
  for(int j=0;j<count;++j)common_batch_add(b,suffix[at+j],int(all.size()+j),{0},true);
  observer.decode(ctx,b,"target");llama_batch_free(b);
  all.insert(all.end(),suffix.begin()+at,suffix.begin()+at+count);observer.evidence.commit(ctx);
 }
 const int rollback=req.value("rollback",0);
 if(rollback){
  if(rollback!=1||suffix.size()!=2)throw std::runtime_error("probe rollback profile");
  const int keep=int(all.size())-rollback;
  if(!llama_memory_seq_rm(llama_get_memory(ctx),0,keep,-1))throw std::runtime_error("probe trim");
  all.resize(keep);observer.evidence.commit(ctx);
  auto after=req.at("after_rollback").get<std::vector<int>>();
  if(after.size()!=2)throw std::runtime_error("probe post rollback width");
  auto b=llama_batch_init(2,0,1);
  for(int j=0;j<2;++j)common_batch_add(b,after[j],int(all.size()+j),{0},true);
  observer.decode(ctx,b,"target");llama_batch_free(b);all.insert(all.end(),after.begin(),after.end());observer.evidence.commit(ctx);
 }
 llama_synchronize(ctx);observer.finish({}, {}, input);
 const auto service_end=ggml_time_us();
 pj metrics={{"mechanism_only",true},{"natural_timing",false},{"request_id",req.at("request_id")},{"service_ms",(service_end-whole_start)/1000.0},{"probe_phase",probe_phase},{"rollback",rollback},{"known_tokens",prelude.size()+suffix.size()},{"requested_width",width},{"explicit_output_reserve",32}};
 std::ofstream mf(observer.path+".metrics.json");mf<<metrics.dump(2)<<"\n";mf.close();
 b570_cost::write(observer.path+".cost.json");
 std::cout<<"HS_RESULT "<<metrics.dump()<<"\n"<<std::flush;
 continue;
}
