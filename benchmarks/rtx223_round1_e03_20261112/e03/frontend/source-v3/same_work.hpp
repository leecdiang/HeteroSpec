#pragma once
template<class Widths> static json width_histogram(const Widths& widths) {
    json hist=json::object();
    for(size_t i=0;i<widths.size();++i)if(widths[i])hist[std::to_string(i)]=widths[i];
    return hist;
}
static void same_work(const json& job,json& result,const fs::path& root,Pair& pool) {
    need(phase_lowering=="LOCAL","Equal work requires fixed LOCAL cut");
    result["same_work"]=json::array();
    for(const auto& probe:job.at("same_work")) {
        auto started=Clock::now();const std::string name=probe.at("name"),mode=probe.at("execution");
        need(mode=="q4pair"||mode=="q8","Equal work execution");
        const auto prefix=probe.at("prefix_ids").get<std::vector<int>>();
        const auto tokens=probe.at("append_ids").get<std::vector<int>>();
        need(!prefix.empty()&&tokens.size()==8&&prefix.size()+8<=1024,"Equal work capacity");
        const bool capture=probe.at("capture");auto dir=root/name;fs::create_directories(dir);
        auto& c=*pool.target;c.reset(capture,dir/"target");hsc::begin(capture?"heavy":"counts",int(prefix.size()));
        c.decode(prefix,0,false,"PREFILL");
        const auto prep_widths=width_histogram(hsc::w.target_physical);
        const auto prefix_executions=c.plan.executions;
        const size_t vocab=llama_vocab_n_tokens(llama_model_get_vocab(c.model));
        std::vector<float> initial(c.plan.logits(-1),c.plan.logits(-1)+vocab);
        auto save_started=Clock::now();const auto bytes=llama_state_seq_get_size(c.c,0);std::vector<uint8_t> saved(bytes);
        need(llama_state_seq_get_data(c.c,saved.data(),bytes,0)==bytes,"Equal work initial state export");
        const double save_s=since(save_started);
        auto restore_started=Clock::now();c.reset(capture,dir/"target");
        need(llama_state_seq_set_data(c.c,saved.data(),bytes,0)==bytes,"Equal work initial state restore");
        llama_synchronize(c.c);const double restore_s=since(restore_started);
        tpds_decisive::capture_write_new(dir/"initial-sequence.bin",saved.data(),saved.size());
        tpds_decisive::capture_write_new(dir/"initial-frontier.f32",initial.data(),initial.size()*sizeof(float));
        const double setup_s=since(started);hsc::begin(capture?"heavy":"counts",int(prefix.size()));
        const auto ex=phase_exports,im=phase_imports,contexts=phase_contexts,heavy=phase_heavy_captures;
        std::vector<std::vector<float>> owned;owned.reserve(8);
        auto operation_started=Clock::now();
        const size_t width=mode=="q8"?8:4;
        for(size_t offset=0;offset<8;offset+=width) {
            c.decode(std::vector<int>(tokens.begin()+offset,tokens.begin()+offset+width),int(prefix.size()+offset),true,"VERIFY");
            for(size_t row=0;row<width;++row) {
                auto* vector=c.plan.logits(int(row));owned.emplace_back(vector,vector+vocab);
            }
        }
        const double operation_s=since(operation_started);
        need(phase_exports==ex&&phase_imports==im&&phase_contexts==contexts&&phase_heavy_captures==heavy,"Equal work timer scope");
        const auto physical=width_histogram(hsc::w.target_physical);
        need(physical.size()==1&&physical.at(std::to_string(width))==int(8/width),"Equal work actual physical width");
        need(width_histogram(hsc::w.draft_physical).empty(),"Equal work executed drafting");
        need(c.bounds().at("max")==int(prefix.size()+7),"Equal work final frontier");
        c.plan.outputs.clear();need(owned.size()==8,"Equal work owned eight rows");
        auto output_started=Clock::now();json rows=json::array();
        for(size_t i=0;i<8;++i) {
            need(owned[i].size()==vocab,"Equal work full vocabulary");
            for(float x:owned[i])need(std::isfinite(x),"Equal work finite output");
            auto path=dir/("row-"+std::to_string(i)+".f32");
            tpds_decisive::capture_write_new(path,owned[i].data(),vocab*sizeof(float));rows.push_back(hash_file(path));
        }
        const auto final_size=llama_state_seq_get_size(c.c,0);std::vector<uint8_t> final_state(final_size);
        need(llama_state_seq_get_data(c.c,final_state.data(),final_size,0)==final_size,"Equal work final state export");
        tpds_decisive::capture_write_new(dir/"final-sequence.bin",final_state.data(),final_state.size());
        const double output_s=since(output_started);
        json r={{"origin",probe.at("origin")},{"geometry",probe.at("geometry")},{"execution",mode},{"capture",capture},
            {"position",prefix.size()},{"append_ids",tokens},{"operation_seconds",operation_s},{"setup_seconds",setup_s},
            {"save_seconds",save_s},{"restore_seconds",restore_s},{"post_timer_output_and_state_seconds",output_s},
            {"full_output_sha256",rows},{"outputs_survive_next_decode_and_plan_clear",true},
            {"prefix_physical_width_hist",prep_widths},{"target_physical_width_hist",physical},{"draft_physical_width_hist",json::object()},
            {"prefix_executions",prefix_executions},{"executions",c.plan.executions},{"geometry_descriptors",json::array()},
            {"final_bounds",c.bounds()},{"graphs_built",hsc::w.graphs_built},{"graphs_reused",hsc::w.graphs_reused},
            {"planning_seconds",c.plan.planning_s},{"output_copy_seconds",c.plan.output_copy_s},
            {"timer_exports",phase_exports-ex-1},{"timer_imports",phase_imports-im},{"timer_context_creates",phase_contexts-contexts},
            {"elapsed_seconds",since(started)}};
        for(const auto& x:c.obs.signatures)r["geometry_descriptors"].push_back(x.second);
        dump(dir/"receipt.json",r);result["same_work"].push_back({{"name",name},{"record",name+"/receipt.json"}});
        result["trajectories"]=result["trajectories"].get<int>()+1;
        result["token_rows"]=result["token_rows"].get<int>()+int(prefix.size()+8);
        dump(root/"result.json",result);hsc::w.active=false;
    }
}
