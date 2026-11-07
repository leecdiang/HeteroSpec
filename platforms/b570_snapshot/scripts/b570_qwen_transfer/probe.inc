static json structural_probe(llama_model *model, const json &input) {
    const auto ids=input.at("prompt_ids").get<std::vector<int>>();
    need(ids.size() >= 267,"teacher-forcing extent");
    json runs=json::array();
    policy.producer=1; policy.consumer=2; policy.prefix=true; policy.clean=true;
    _putenv_s("HS_TRANSFER_TRACE","1");
    for(int head:{254,253}) {
        policy.precision=true;
        request_start=Clock::now();
#ifdef TRANSFER_CANDIDATE
        constexpr int ub=4;
#else
        constexpr int ub=1;
#endif
        NativeContext context(model,ub,false,"target");
        const std::vector<int> prefix(ids.begin(),ids.begin()+head);
        context.prefill(prefix,std::vector<int>(head,1));
        json calls=json::array();
        for(int p=head;p+2<=267;p+=2) {
            const int actual_head=llama_memory_seq_pos_max(llama_get_memory(context.c),0)+1;
            need(actual_head==p,"unexpected occupied position");
            policy.precision=p!=261;
            const int before=llama_perf_context(context.c).n_reused;
            std::fprintf(stderr,"HS_PROBE_BEGIN prefix=%d pos=%d width=%d precision=%d\n",head,p,ub==1?1:2,int(policy.precision));
            json vectors=json::array();
#ifdef TRANSFER_CANDIDATE
            context.decode({ids[p],ids[p+1]},p,true,"VERIFY");
            for(int row=0;row<2;++row) {
                auto v=context.logits(row);
                vectors.push_back(save_bytes(v.data(),v.size()*sizeof(float)));
            }
#else
            for(int row=0;row<2;++row) {
                context.decode({ids[p+row]},p+row,true,"ORDINARY");
                auto v=context.logits(-1);
                vectors.push_back(save_bytes(v.data(),v.size()*sizeof(float)));
            }
#endif
            calls.push_back({{"base",p},{"actual_prior_max",actual_head-1},{"precision_enabled",policy.precision},
                {"reuse_delta",llama_perf_context(context.c).n_reused-before},{"vectors",vectors}});
            std::fprintf(stderr,"HS_PROBE_END pos=%d\n",p);
        }
        runs.push_back({{"prefix_tokens",head},{"calls",calls}});
    }
    return runs;
}

