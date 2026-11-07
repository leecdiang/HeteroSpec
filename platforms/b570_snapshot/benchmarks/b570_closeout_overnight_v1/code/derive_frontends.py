from pathlib import Path
import shutil,json,hashlib
ROOT=Path(__file__).parent
OLD=Path('C:/hs/b570-prefill-v1/scripts/platform/b570_prefill_diagnostic_v1')
OUT=ROOT/'src';OUT.mkdir(exist_ok=True)
def rep(s,a,b,n=1):
    assert s.count(a)==n,(a,s.count(a),n)
    return s.replace(a,b)
o=(OLD/'observer.h').read_text()
o=rep(o,'    int prefill_ub=1;','    int prefill_ub=1;\n    int target_calls=0,draft_calls=0,target_tokens=0,draft_tokens=0;\n    void reset(const pj &req){path=req.at("output");trace=pj::array();graphs=pj::array();commits=pj::array();transfer=nullptr;phase="initialization";role="target";target_calls=draft_calls=target_tokens=draft_tokens=0;}')
o=rep(o,'        graphs=pj::array(); if (!instrument) return;','        if(role=="target"){++target_calls;target_tokens+=b.n_tokens;}else{++draft_calls;draft_tokens+=b.n_tokens;}\n        graphs=pj::array(); if (!instrument) return;')
o=rep(o,'        if (code) throw', '        if(instrument)llama_synchronize(ctx);\n        if (code) throw')
o=rep(o,'        cp.n_ubatch=1;auto * dst=', '        auto * dst=')
o=rep(o,'if (prefill_ub!=1 && prefill_ub!=128)', 'if ((prefill_ub<1 || prefill_ub>8) && prefill_ub!=128)')
o=rep(o,'        std::ofstream f(path+suffix,std::ios::binary);','        if(!instrument)return;\n        std::ofstream f(path+suffix,std::ios::binary);')
o=rep(o,'        int n=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(c))),a=-1,b=-1;','        if(std::getenv("HS_TRACE_OFF"))return pj::object();\n        int n=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(c))),a=-1,b=-1;')
o=rep(o,'{"prefill_ub",prefill_ub},{"trace",trace}', '{"prefill_ub",prefill_ub},{"work",{{"target_calls",target_calls},{"draft_calls",draft_calls},{"target_caller_tokens",target_tokens},{"draft_caller_tokens",draft_tokens}}},{"trace",trace}')
(OUT/'observer.h').write_text(o,newline='\n')
s=(OLD/'native.cpp').read_text()
s=rep(s,'#include <vector>','#include <vector>\n#include <iostream>')
s=rep(s,'    // max number of parallel drafting sequences (i.e. tree branches)','    params.warmup=false; // Explicit session warm request; speculative CLI lacks --no-warmup.\n    // max number of parallel drafting sequences (i.e. tree branches)')
s=rep(s,'if(params.n_parallel!=1||params.n_ctx!=1024||params.n_batch!=512||params.n_ubatch!=1||params.sampling.temp!=0||params.sampling.seed!=123||params.speculative.draft.n_max!=2||params.n_predict!=127) return 80;', 'if(params.n_parallel!=1||params.n_ctx!=1024||params.n_batch!=512||params.n_ubatch<1||params.n_ubatch>8||params.sampling.temp!=0||params.sampling.seed!=123||params.speculative.draft.n_max<1||params.speculative.draft.n_max>7||params.n_predict<127||params.n_predict>511) return 80;')
s=rep(s,'    params.devices = params.speculative.draft.devices;', '    params.n_ubatch=1;\n    params.devices = params.speculative.draft.devices;')
s=rep(s,'    auto * mem_tgt = llama_get_memory(ctx_tgt);', '''    std::cout << "HS_READY\\n" << std::flush;
    std::string line;
    auto * source_target=ctx_tgt;
    while(std::getline(std::cin,line)) {
    const auto req=pj::parse(line);
    observer.reset(req);
    const auto whole_start=ggml_time_us();
    ctx_tgt=source_target;
    llama_memory_clear(llama_get_memory(ctx_tgt),true);
    llama_memory_clear(llama_get_memory(ctx_dft),true);
    llama_synchronize(ctx_tgt);llama_synchronize(ctx_dft);
    auto reset_target=prefill_observer::positions(ctx_tgt),reset_draft=prefill_observer::positions(ctx_dft);
    auto * mem_tgt = llama_get_memory(ctx_tgt);''')
s=rep(s,'    if(const char * p=std::getenv("HS_MECHANISM_INPUT_IDS")){std::ifstream f(p);pj j;f>>j;inp=j.get<std::vector<llama_token>>();}\n    else inp = common_tokenize(ctx_tgt, params.prompt, true, true);', '    inp=req.at("prompt_ids").get<std::vector<llama_token>>();\n    if(inp.empty()||inp.size()+params.n_predict+params.speculative.draft.n_max+4>1024)return 81;')
s=rep(s,'      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());mem_tgt=llama_get_memory(ctx_tgt);}', '      auto * original_sampler=smpl;\n      ctx_tgt=observer.move(ctx_tgt,model_tgt,continuation_cp,smpl,pending,inp.size());common_sampler_free(original_sampler);mem_tgt=llama_get_memory(ctx_tgt);}')
s=rep(s,'    auto t_dec_end = ggml_time_us();','    llama_synchronize(ctx_tgt);llama_synchronize(ctx_dft);\n    auto t_dec_end = ggml_time_us();')
s=rep(s,'    llama_backend_free();','    llama_batch_free(batch_tgt);\n    if(ctx_tgt!=source_target)llama_free(ctx_tgt);\n    const auto whole_end=ggml_time_us();')
s=rep(s,'    if (!hs_direct_ids.write()) { return 2; }\n    return 0;', '''    pj result={{"request_id",req.at("request_id")},{"capture",observer.path},{"generation_ms",(t_dec_end-t_dec_start)/1000.0},{"whole_request_ms",(whole_end-whole_start)/1000.0},{"prefill_ms",(t_enc_end-t_enc_start)/1000.0},{"raw_count",hs_direct_ids.ids.size()},{"drafted",n_drafted},{"accepted",n_accept},{"reset_target",reset_target},{"reset_draft",reset_draft},{"target_continuation_ub",continuation_cp.n_ubatch},{"draft_continuation_ub",llama_n_ubatch(ctx_dft)},{"threads",params.cpuparams.n_threads},{"batch_threads",params.cpuparams_batch.n_threads}};
    std::ofstream result_file(observer.path+".metrics.json",std::ios::binary);result_file<<result.dump(2)<<"\\n";result_file.close();
    std::cout<<"HS_RESULT "<<result.dump()<<"\\n"<<std::flush;
    }
    llama_backend_free();
    return 0;''')
s=rep(s,'    const auto t_dec_start = ggml_time_us();','')
s=rep(s,"    // target model sampling context (reuse the llama_context's sampling instance)",'    const auto t_dec_start = ggml_time_us();\n'+"    // target model sampling context (reuse the llama_context's sampling instance)")
s=rep(s,'    // init llama.cpp','    common_log_set_verbosity_thold(4);\n    // init llama.cpp')
s=rep(s,'    std::cout << "HS_READY\\n" << std::flush;','    common_log_set_verbosity_thold(3);\n    std::cout << "HS_READY\\n" << std::flush;')
(OUT/'native.cpp').write_text(s,newline='\n')
t=(OLD/'target.cpp').read_text()
t=rep(t,'(params.n_ubatch != 128 && params.n_ubatch != 1) || params.n_predict != 128 ||', '(params.n_ubatch != 128 && (params.n_ubatch < 1 || params.n_ubatch > 8)) || (params.n_predict < 128 || params.n_predict > 512) ||')
t=rep(t,'    std::vector<llama_token> input;', '''    auto * source_target=ctx;
    std::cout<<"HS_READY\\n"<<std::flush;
    std::string line;
    while(std::getline(std::cin,line)){
    const auto req=json::parse(line);observer.reset(req);
    const auto whole_start=ggml_time_us();
    ctx=source_target;
    llama_memory_clear(llama_get_memory(ctx),true);llama_synchronize(ctx);
    common_sampler_reset(init->sampler(0));sampler=init->sampler(0);
    auto reset_target=prefill_observer::positions(ctx);
    std::vector<llama_token> input;''')
start=t.index('    const char * input_path =')
end=t.index('    for (auto id : input)',start)
t=t[:start]+'''    input=req.at("prompt_ids").get<std::vector<llama_token>>();
    if(input.empty()||input.size()+params.n_predict>1024)return 4;
'''+t[end:]
t=rep(t,'    const char * output_path = std::getenv("HS_MECHANISM_OUTPUT");','    const char * output_path = observer.path.c_str();')
start=t.index('    for (size_t i=0;i<input.size();i+=512)')
end=t.index('    int pending=-1;',start)
t=t[:start]+'''    const bool matched=std::getenv("HS_MATCHED_TARGET")!=nullptr;
    if(matched){
        observer.decode(ctx,llama_batch_get_one(input.data(),input.size()-1),"target");
        observer.decode(ctx,llama_batch_get_one(&input.back(),1),"target");
        all=input;n_past=input.size();
    }else{
    for(size_t i=0;i<input.size();i+=512){
        const int size=std::min(size_t(512),input.size()-i);
        std::vector<llama_token> chunk(input.begin()+i,input.begin()+i+size);
        all.insert(all.end(),chunk.begin(),chunk.end());
        for(auto id:chunk)common_sampler_accept(sampler,id,false);
        observer.begin(ctx,llama_batch_get_one(chunk.data(),size));
        if(!common_prompt_batch_decode(ctx,all,size,n_past,512,"",false))return 7;
        observer.end(ctx,0);
    }}
    llama_synchronize(ctx);
    const auto generation_start=ggml_time_us();
'''+t[end:]
t=rep(t,'std::getenv("HS_NO_TRANSFER")==nullptr && continuation_cp.n_ubatch==1','std::getenv("HS_NO_TRANSFER")==nullptr && matched')
t=rep(t,'for (int i=0;i<128;++i)', 'for (int i=0;i<params.n_predict;++i)')
t=rep(t,'if (stop || i==127) break;', 'if (stop || i==params.n_predict-1) break;')
t=rep(t,'if(logits) for (int id=0;id<llama_vocab_n_tokens(vocab);++id)', 'if(logits && observer.instrument) for (int id=0;id<llama_vocab_n_tokens(vocab);++id)')
t=rep(t,'if(!logits){top1=pending_scores["top1"];top2=pending_scores["top2"];}','if(!logits && observer.instrument){top1=pending_scores["top1"];top2=pending_scores["top2"];}')
t=rep(t,'const float first=logits?logits[top1]:pending_scores["top1_score"].get<float>(),second=logits?logits[top2]:pending_scores["top2_score"].get<float>();','const float first=observer.instrument?(logits?logits[top1]:pending_scores["top1_score"].get<float>()):0,second=observer.instrument?(logits?logits[top2]:pending_scores["top2_score"].get<float>()):0;')
t=rep(t,'    result["generated_ids"]=generated;', '''    llama_synchronize(ctx);
    const auto generation_end=ggml_time_us();
    if(ctx!=source_target){common_sampler_free(sampler);llama_free(ctx);}
    const auto whole_end=ggml_time_us();
    result["generated_ids"]=generated;''')
t=rep(t,'    std::cout << "Mechanism capture complete: " << generated.size() << " committed IDs\\n";\n    return 0;', '''    pj metrics={{"request_id",req.at("request_id")},{"capture",observer.path},{"generation_ms",(generation_end-generation_start)/1000.0},{"whole_request_ms",(whole_end-whole_start)/1000.0},{"raw_count",generated.size()},{"drafted",0},{"accepted",0},{"reset_target",reset_target},{"target_continuation_ub",continuation_cp.n_ubatch},{"threads",params.cpuparams.n_threads},{"batch_threads",params.cpuparams_batch.n_threads}};
    std::ofstream metrics_file(observer.path+".metrics.json",std::ios::binary);metrics_file<<metrics.dump(2)<<"\\n";metrics_file.close();
    std::cout<<"HS_RESULT "<<metrics.dump()<<"\\n"<<std::flush;
    }
    return 0;''')
t=rep(t,'    if (!out) return 10;','    if (!out) return 10;\n    out.close();')
t=rep(t,'#include <limits>','#include <limits>\n#include "log.h"')
t=rep(t,'    llama_backend_init();','    common_log_set_verbosity_thold(4);\n    llama_backend_init();')
t=rep(t,'    std::cout<<"HS_READY\\n"<<std::flush;','    common_log_set_verbosity_thold(3);\n    std::cout<<"HS_READY\\n"<<std::flush;')
t=rep(t,'    const auto continuation_cp=common_context_params_to_llama(params);','    auto continuation_cp=common_context_params_to_llama(params);\n    if(std::getenv("HS_MATCHED_TARGET")){continuation_cp.n_outputs_max=1;continuation_cp.n_outputs_max_per_seq=1;}')
(OUT/'target.cpp').write_text(t,newline='\n')
for name in ['native.cpp','target.cpp']:
 p=OUT/name
 s2=p.read_text(encoding='utf-8')
 s2=s2.replace('    const auto req=pj::parse(line);\n    observer.reset(req);\n    const auto whole_start=ggml_time_us();','    const auto whole_start=ggml_time_us();\n    const auto req=pj::parse(line);\n    observer.reset(req);')
 s2=s2.replace('    const auto req=json::parse(line);observer.reset(req);\n    const auto whole_start=ggml_time_us();','    const auto whole_start=ggml_time_us();\n    const auto req=json::parse(line);observer.reset(req);')
 p.write_text(s2,encoding='utf-8',newline='\n')
c=(OLD/'CMakeLists.txt').read_text().replace('heterospec-mechanism','b570-closeout-target').replace('heterospec-prefill-native','b570-closeout-native')
(OUT/'CMakeLists.txt').write_text(c,newline='\n')
manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()}
(ROOT/'DERIVATION.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(manifest)
