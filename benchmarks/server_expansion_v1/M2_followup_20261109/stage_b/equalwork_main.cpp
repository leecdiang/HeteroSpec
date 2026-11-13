// Appended to the exact M2 entry preamble, sharing its unchanged Context and
// PhaseContext. Diagnostic only: no draft, acceptance, sampling or optimization.
static std::vector<uint8_t> ew_bytes(const fs::path& p) {
    std::ifstream f(p,std::ios::binary);need(bool(f),"snapshot open");
    return {std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};
}
int main(int argc,char**argv) {
    llama_model* t=nullptr;Pair pool;fs::path root;
    try {
        need(argc==3,"equalwork JOB OUT");const auto job=load(argv[1]);root=argv[2];
        need(!fs::exists(root),"fresh output");fs::create_directories(root);
        const std::vector<std::string> keys={"family","target_model","target_sha256","n_ctx","threads","diagnostics","pause_file"};
        for(auto it=job.begin();it!=job.end();++it)need(std::find(keys.begin(),keys.end(),it.key())!=keys.end(),"unknown diagnostic field");
        need(job.at("family")=="Qwen"&&job.at("n_ctx")==1024&&job.at("threads")==2,"fixed diagnostic configuration");
        phase_threads=2;phase_target_reserve=8;phase_lowering="LOCAL";phase_draft_width=4;
        need(hash_file(job.at("target_model").get<std::string>())==job.at("target_sha256"),"target hash");
        const auto began=Clock::now();ggml_time_init();llama_backend_init();ggml_backend_dev_t gpu=nullptr;
        for(size_t i=0;i<ggml_backend_dev_count();++i){auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)==GGML_BACKEND_DEVICE_TYPE_GPU){need(!gpu,"one visible GPU required");gpu=d;}}
        need(gpu,"GPU required");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();
        mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        t=llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(),mp);need(t,"target load");
        auto spec=ArmSpec{"equalwork","QB",0,32,0,true,false};provision(pool,t,nullptr,spec,root/"pool");
        auto& ctx=*pool.target;const int nv=llama_vocab_n_tokens(llama_model_get_vocab(t));
        json result={{"schema","heterospec.pr210.equalwork.v1"},{"modules_before",module_inventory()},
          {"context",m1_context(ctx)},{"placement",m1_placement(t)},{"projection",M1_PROJECTION},
          {"setup_s",since(began)},{"vocab",nv},{"draft_calls",0},{"requests",json::array()}};
        for(const auto& x:job.at("diagnostics")) {
            need(!fs::exists(job.at("pause_file").get<std::string>()),"new work detected; no next logical request");
            const std::string name=x.at("name");need(name.find('/')==std::string::npos&&name.find("..") ==std::string::npos,"safe diagnostic name");
            const auto dir=root/name;fs::create_directories(dir);
            const int base=x.at("position");const auto ids=x.at("ids").get<std::vector<int>>();
            const std::string path=x.at("execution");const bool heavy=x.at("capture");
            need((base==248||base==252)&&ids.size()==8&&(path=="q4pair"||path=="q8"),"registered equal work");
            for(int id:ids)need(id>=0&&id<nv,"token bounds");
            auto at=Clock::now();auto bytes=ew_bytes(x.at("state_path").get<std::string>());
            auto front=ew_bytes(x.at("frontier_path").get<std::string>());const double disk=since(at);
            need(hash_file(x.at("state_path").get<std::string>())==x.at("state_sha256")&&hash_file(x.at("frontier_path").get<std::string>())==x.at("frontier_sha256"),"bound initial operands");
            need(front.size()==size_t(nv)*4,"initial full frontier");
            ctx.reset(heavy,dir/"context");at=Clock::now();
            need(llama_state_seq_set_data(ctx.c,bytes.data(),bytes.size(),0)==bytes.size(),"snapshot import");
            llama_synchronize(ctx.c);ctx.plan.outputs.resize(1);ctx.plan.outputs[0].resize(nv);
            std::memcpy(ctx.plan.outputs[0].data(),front.data(),front.size());
            const double restore=since(at);need(ctx.bounds()==json({{"min",0},{"max",base-1}}),"restored frontier bounds");
            if(heavy)observe_state(ctx,dir/"initial",0);
            const auto imports=phase_imports,exports=phase_exports,captures=phase_heavy_captures;
            hsc::begin(heavy?"heavy":"counts",8);
            const auto start=Clock::now();
            // Exactly eight owned vectors on both paths; moves retain the first
            // q4 outputs across the second decode without an extra payload copy.
            std::vector<std::vector<float>> owned(8);
            for(int off=0;off<8;) {
                const int width=path=="q8"?8:4;
                std::vector<int> call(ids.begin()+off,ids.begin()+off+width);
                ctx.decode(call,base+off,true,"VERIFY");
                need(ctx.plan.outputs.size()==size_t(width),"complete requested row array");
                for(int row=0;row<width;++row){need(ctx.plan.outputs[row].size()==size_t(nv),"full requested vector");owned[off+row]=std::move(ctx.plan.outputs[row]);}
                off+=width;
            }
            llama_synchronize(ctx.c);const double seconds=since(start);hsc::w.active=false;
            json r={{"name",name},{"position",base},{"ids",ids},{"execution",path},{"capture",heavy},
              {"operation_s",seconds},{"snapshot_disk_read_s",disk},{"restore_and_frontier_copy_s",restore},
              {"executions",ctx.plan.executions},{"planning_s",ctx.plan.planning_s},{"output_copy_s",ctx.plan.output_copy_s},
              {"phase_seconds",ctx.phases},{"final_bounds",ctx.bounds()},{"output_vectors",8},{"output_floats",8*nv},
              {"graph_built",hsc::w.graphs_built},{"graph_reused",hsc::w.graphs_reused},
              {"online_state_imports",phase_imports-imports},{"online_state_exports",phase_exports-exports},
              {"online_heavy_captures",phase_heavy_captures-captures},{"physical_width_histogram",json::object()},
              {"output_sha256",json::array()},{"geometry",json::array()}};
            need(ctx.bounds()==json({{"min",0},{"max",base+7}}),"final active frontier");
            for(size_t i=0;i<hsc::w.target_physical.size();++i)if(hsc::w.target_physical[i])r["physical_width_histogram"][std::to_string(i)]=hsc::w.target_physical[i];
            for(int i=0;i<8;++i){for(float v:owned[i])need(std::isfinite(v),"nonfinite output");Sha256 h;h.update(reinterpret_cast<const char*>(owned[i].data()),size_t(nv)*4);r["output_sha256"].push_back(h.finish());if(heavy)tpds_decisive::capture_write_new(dir/("row-"+std::to_string(i)+".f32"),owned[i].data(),size_t(nv)*4);}
            for(auto& kv:ctx.obs.signatures)r["geometry"].push_back(kv.second);
            if(heavy){const auto size=llama_state_seq_get_size(ctx.c,0);std::vector<uint8_t> state(size);need(llama_state_seq_get_data(ctx.c,state.data(),size,0)==size,"final state export");tpds_decisive::capture_write_new(dir/"final-sequence.bin",state.data(),state.size());}
            dump(dir/"receipt.json",r);result["requests"].push_back({{"name",name},{"record",name+"/receipt.json"}});
            dump(root/"result.json",result);std::cout<<"PHASE1_RESULT_READY "<<name<<" "<<since(began)<<std::endl;
        }
        result["modules_after"]=module_inventory();pool.target.reset();llama_model_free(t);t=nullptr;llama_backend_free();result["status"]="COMPLETE";dump(root/"result.json",result);return 0;
    } catch(const std::exception& e){if(!root.empty()&&fs::exists(root))dump(root/"failure.json",{{"error",e.what()}});std::cerr<<e.what()<<std::endl;return 2;}
}
