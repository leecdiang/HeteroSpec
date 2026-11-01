    // get_sched()/get_tensor_backend returns scheduler assignment. Buffer ownership
    // is retained as a distinct field and is never used to infer execution placement.
    llama_context* context=nullptr;
    bool observe_target=true,metadata_enabled=false;
    int call_index=0;
    std::map<std::string,int> occurrences;
    static bool callback(ggml_tensor*t,bool ask,void*opaque){
        auto&o=*static_cast<Observer*>(opaque);
        try{
            if(!o.observe_target||!o.metadata_enabled)return false;
            if(o.phase!="VERIFY"&&o.phase!="PREFILL"&&o.phase!="ORDINARY")return false;
            std::string name=t->name;
            const bool want=hs_repair::selected(name,o.phase,o.base);
            const bool geometry=name.rfind("kq",0)==0||name.rfind("hs_",0)==0;
            if(ask && !want && !geometry)return false;
            auto j=meta(t);j["buffer_owner_device"]=j["device"];j.erase("device");
            auto sched=o.context?o.context->get_sched():nullptr;
            auto backend=sched?ggml_backend_sched_get_tensor_backend(sched,t):nullptr;
            j["scheduler_backend"]=backend?json(ggml_backend_name(backend)):json(nullptr);
            auto device=backend?ggml_backend_get_device(backend):nullptr;
            j["scheduler_device"]=device?json(ggml_backend_dev_description(device)):json(nullptr);
            j["scheduler_device_type"]=device?json(int(ggml_backend_dev_type(device))):json(nullptr);
            j["backend_evidence"]="scheduler node assignment, not buffer owner or kernel-level profiler";
            j["evaluation_observed"]=!ask;
            j["phase"]=o.phase;j["op"]=ggml_op_name(t->op);j["call_index"]=o.call_index;
            j["caller_rows"]=o.caller;j["caller_first_position"]=o.base;
            j["sources"]=json::array();
            for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(meta(t->src[i]));
            std::smatch layer;std::regex suffix("-([0-9]+)$");
            j["layer"]=std::regex_search(name,layer,suffix)?json(std::stoi(layer[1])):json(nullptr);
            if(ask){
                if(geometry){
                    need(backend!=nullptr,"scheduler assignment unavailable for observed QK node");
                    o.signatures[j.dump()]=j;
                }
                return want;
            }
            need(want,"unexpected post-evaluation observation");
            auto n=ggml_nbytes(t);
            need(hs_repair::opt.files<hs_repair::opt.max_files && n<=hs_repair::opt.max_bytes-hs_repair::opt.bytes,"trace budget exhausted; retain partial trace");
            need(t->buffer!=nullptr,"observed tensor unallocated");
            // Only the output is copied here. A source may have been overwritten by
            // in-place execution; we do not label post-op sources as native operands.
            std::vector<uint8_t> data(n);ggml_backend_tensor_get(t,data.data(),0,n);
            const auto serial=hs_repair::opt.files++;
            auto rel=std::string("trace/")+std::to_string(serial)+"_"+hs_repair::safe_name(name)+".bin";
            hs_repair::write_bytes(hs_repair::opt.root/rel,data.data(),data.size());
            hs_repair::opt.bytes+=n;j["file"]=rel;j["bytes"]=n;j["sha256"]=hash_file(hs_repair::opt.root/rel);
            j["occurrence"]=o.occurrences[o.phase+"/"+name]++;
            j["alignment_scope"]="caller positions and node occurrence only; multi-ubatch token alignment requires explicit row map";
            std::ofstream index(hs_repair::opt.root/"trace/INDEX.jsonl",std::ios::app);index<<j.dump()<<'\n';need(bool(index),"trace index write");
            return true; // false here would cancel scheduler execution.
        }catch(const std::exception&e){o.bad=true;hs_repair::opt.error=e.what();return false;}
    }
