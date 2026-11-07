#define main historical_main
#include "worker.cpp"
#undef main
#include "replay_path.hpp"
int main(int argc,char**argv){
    llama_model*t=nullptr,*d=nullptr;std::map<std::string,Pair> residents;fs::path root;
    try{
        need(argc==6,"forced OUT TARGET DRAFT JOB BINDING");root=argv[1];need(!fs::exists(root),"fresh forced output");fs::create_directories(root);
        const auto job=load(argv[4]),binding=load(argv[5]);auto identity=binding.at("families").at("Qwen");
        need(job.at("no_candidate_payload")==true,"token-only forced jobs");
        wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);auto bin=fs::path(exe).parent_path();
        need(hash_file(exe)==identity.at("executable_sha256"),"forced executable");
        for(auto it=identity.at("numerical_modules").begin();it!=identity.at("numerical_modules").end();++it)need(hash_file(bin/it.key())==it.value(),"forced module");
        need(hash_file(argv[2])==identity.at("models").at("target").at("sha256")&&hash_file(argv[3])==identity.at("models").at("draft").at("sha256"),"forced model");
        ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();i++){auto x=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(x)).find("5070")!=std::string::npos){need(!gpu,"ambiguous GPU");gpu=x;}}need(gpu,"RTX GPU");
        ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        auto began=Clock::now();t=llama_model_load_from_file(argv[2],mp);d=llama_model_load_from_file(argv[3],mp);need(t&&d,"forced model loading");
        json result={{"model_load_seconds",since(began)},{"paths",json::array()},{"requests",0},{"token_rows",0}};
        began=Clock::now();for(const char*name:{"R","C_GS","C_PQ","C_QB"}){auto s=arm_spec(name);provision(residents[pool_key("Qwen",s)],t,d,s,root/"pool");}
        result["provision_seconds"]=since(began);auto*ctx=residents[pool_key("Qwen",arm_spec("R"))].target.get();
        if(job.contains("sentinel_state")){
            std::ifstream f(job.at("sentinel_state").get<std::string>(),std::ios::binary|std::ios::ate);need(bool(f),"sentinel open");std::vector<uint8_t> bytes(size_t(f.tellg()));f.seekg(0);f.read((char*)bytes.data(),bytes.size());need(bool(f),"sentinel read");
            ctx->reset(false,root/"sentinel");need(llama_state_seq_set_data(ctx->c,bytes.data(),bytes.size(),0)==bytes.size(),"sentinel import");llama_synchronize(ctx->c);
            std::vector<uint8_t> exported(llama_state_seq_get_size(ctx->c,0));need(llama_state_seq_get_data(ctx->c,exported.data(),exported.size(),0)==exported.size(),"sentinel export");
            std::ofstream dest(root/"sentinel-export.bin",std::ios::binary);dest.write((char*)exported.data(),exported.size());need(bool(dest),"sentinel write");
            result["requests"]=1;result["sentinel_bounds"]=ctx->bounds();result["sentinel_only_no_model_forward"]=true;
        }
        auto prompt=job.at("prompt_ids").get<std::vector<int>>();int index=0;
        for(const auto&path:job.at("paths")){
            auto dir=root/std::to_string(index++);fs::create_directories(dir);ctx->reset(false,dir);hsc::begin("baseline",int(prompt.size()));
            auto suffix=path.at("suffix").get<std::vector<int>>();need(prompt.size()+suffix.size()<=1024,"forced capacity");
            auto wanted=path.at("positions").get<std::vector<int>>();json captures=json::array();began=Clock::now();
            tpds_decisive::replay_path(prompt,suffix,job.at("producer").at("caller_lengths").get<std::vector<int>>(),job.at("producer").at("last_output_flags").get<std::vector<bool>>(),
                [&](const std::vector<int>&ids,int pos,bool all,const char*phase,bool last){need(last,"historical NATIVE whole-prompt last flag");ctx->decode(ids,pos,all,phase);result["token_rows"]=result["token_rows"].get<int64_t>()+ids.size();},
                [&](int row,int count){if(std::find(wanted.begin(),wanted.end(),count)!=wanted.end()){auto key=std::to_string(count);tpds_decisive::capture_existing(ctx->c,t,dir/key,row);captures.push_back({{"position",count},{"directory",std::to_string(index-1)+"/"+key}});}});
            result["requests"]=index;result["paths"].push_back({{"index",index-1},{"seconds",since(began)},{"captures",captures},{"suffix",suffix}});dump(root/"result.json",result);
        }
        residents.clear();llama_model_free(d);d=nullptr;llama_model_free(t);t=nullptr;llama_backend_free();result["status"]="COMPLETE";dump(root/"result.json",result);return 0;
    }catch(const std::exception&e){residents.clear();if(d)llama_model_free(d);if(t)llama_model_free(t);if(!root.empty()&&fs::exists(root))dump(root/"failure.json",{{"error",e.what()}});std::cerr<<e.what()<<std::endl;return 2;}
}
