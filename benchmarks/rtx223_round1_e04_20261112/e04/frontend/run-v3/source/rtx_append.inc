// Known-token diagnostic only. A fresh valid state precedes EVERY append.
// Heavy qualification uses the separate original-R/forced path.
static void phase1_append(const json& job,json& result,const fs::path& root,Pair& pool){
    auto* ctx=pool.target.get();need(ctx,"append target missing");
    for(const auto& probe:job.at("append_probes")){
        const std::string name=probe.at("name");const auto dir=root/name;fs::create_directories(dir);
        const auto prefix=probe.at("prefix").get<std::vector<int>>();
        const auto ids=probe.at("ids").get<std::vector<int>>();
        need(!prefix.empty()&&!ids.empty(),"append material missing");
        auto preparation=Clock::now();ctx->reset(false,dir/"unused-heavy");hsc::begin("counts",int(prefix.size()));
        ctx->decode(prefix,0,false,"PREFILL");llama_synchronize(ctx->c);
        const double preparation_s=since(preparation);
        need(llama_memory_seq_pos_max(llama_get_memory(ctx->c),0)==int(prefix.size())-1,"append state head");
        ctx->plan.clear();ctx->phases.clear();hsc::begin("counts",int(prefix.size()));
        if(phase1_profiling){need(job.at("append_probes").size()==1,"one profiled append per process");profile::begin();}
        const auto exports=phase_exports,imports=phase_imports,contexts=phase_contexts,heavy=phase_heavy_captures;
        const auto begin=Clock::now();
        ctx->decode(ids,int(prefix.size()),false,"VERIFY");
        const auto* output=ctx->plan.logits(-1);need(output,"append requested row missing");
        const auto end=Clock::now();
        if(phase1_profiling)profile::end(dir/"cuda-events.json");
        const int64_t begin_us=std::chrono::duration_cast<std::chrono::microseconds>(begin.time_since_epoch()).count();
        const int64_t end_us=std::chrono::duration_cast<std::chrono::microseconds>(end.time_since_epoch()).count();
        size_t copied=0;for(const auto& row:ctx->plan.outputs)if(!row.empty())++copied;
        json row={{"append_begin_us",begin_us},{"append_end_us",end_us},{"append_ms",double(end_us-begin_us)/1000.},
            {"preparation_s",preparation_s},{"capacity",llama_n_ctx(ctx->c)},{"head",prefix.size()},{"width",ids.size()},
            {"requested_outputs","last"},{"copied_requested_rows",copied},{"executions",ctx->plan.executions},
            {"planning_s",ctx->plan.planning_s},{"output_copy_s",ctx->plan.output_copy_s},{"target_phases",ctx->phases},
            {"graphs_built",hsc::w.graphs_built},{"graphs_reused",hsc::w.graphs_reused},{"physical_widths",hsc::w.target_physical},
            {"append_observer_calls",{{"state_exports",phase_exports-exports},{"state_imports",phase_imports-imports},
                {"context_creates",phase_contexts-contexts},{"heavy_captures",phase_heavy_captures-heavy}}},
            {"window","append_after_valid_state"},{"phase1_clean",true}};
        need(copied==1,"changed append output mask");
        dump(dir/"receipt.json",row);result["requests"].push_back({{"name",name},{"record",name+"/receipt.json"}});
        result["trajectories"]=result["trajectories"].get<int>()+1;
        result["token_rows"]=result["token_rows"].get<int>()+int(prefix.size()+ids.size());
        dump(root/"result.json",result);
    }
}
