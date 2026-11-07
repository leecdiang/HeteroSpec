
// All policies use the exact same inherited token sampling and k3 rollback loop.
static ArmSpec policy(const std::string& name,int width) {
    if(name=="R")return {name,name,1,1,0,false,false};
    if(name=="S1")return {name,name,1,1,3,false,true};
    if(name=="PQ-ext")return {name,name,1,width,3,true,true};
    if(name=="QB-local" || name=="WB-cut")return {name,name,0,width,3,true,true};
    if(name=="native32")return {name,name,0,width,3,false,true};
    if(name=="native-full")return {name,name,0,512,3,false,true};
    if(name=="native-ordinary")return {name,name,0,512,0,false,false};
    throw std::runtime_error("unknown policy");
}
int main(int argc,char** argv){
    try {
        need(argc==5,"service TARGET DRAFT MANIFEST OUT");
        auto panel=load(argv[3]);context_capacity=panel.at("ctx");dense_target_layers=panel.at("layers");
        auto bin=fs::absolute(argv[0]).parent_path();ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();
        ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){
            auto dev=ggml_backend_dev_get(i);
            if(std::string(ggml_backend_dev_description(dev)).find("5070")!=std::string::npos)gpu=dev;
        }
        need(gpu,"RTX GPU missing");ggml_backend_dev_t devices[]={gpu,nullptr};
        auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=dense_target_layers;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto begin=Clock::now();
        std::unique_ptr<llama_model,decltype(&llama_model_free)> t(llama_model_load_from_file(argv[1],mp),llama_model_free);
        mp.n_gpu_layers=999;
        std::unique_ptr<llama_model,decltype(&llama_model_free)> d(llama_model_load_from_file(argv[2],mp),llama_model_free);
        need(bool(t) && bool(d),"model admission");auto load_seconds=since(begin);
        for(const auto& block:panel.at("blocks")){
            auto spec=policy(block.at("arm"),panel.at("width"));
            auto setup=Clock::now();Pair pair;
            pair.target=std::make_unique<Context>(t.get(),spec.target_ub,true,spec.scoped,false,"",spec.selector);
            if(spec.draft)pair.draft=std::make_unique<Context>(d.get(),1,false,false,false,"",spec.selector);
            auto setup_seconds=since(setup);
            for(const auto& slot:block.at("slots")){
                auto dir=fs::path(argv[4])/slot.at("id").get<std::string>();
                need(fs::create_directories(dir),"attempt exists");
                auto input=slot.at("input");
                need(input["cap"]==128 && input["prompt_ids"].size()+132<=size_t(context_capacity),"k3 capacity");
                auto rec=request(t.get(),d.get(),input,spec,"resident",slot.at("capture"),"native",dir,pair);
                rec["pool_setup_seconds"]=setup_seconds;rec["model_load_seconds"]=load_seconds;
                rec["context_capacity"]=context_capacity;
                dump(dir/"receipt.json",rec);
            }
        }
        d.reset();t.reset();llama_backend_free();return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
