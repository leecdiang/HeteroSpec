from pathlib import Path
R=Path(__file__).parent
p=R/'src/native.cpp';t=p.read_text()
t=t.replace('#include "observer.h"','#include "pilot_state.h"\n#include "observer.h"')
for a,b in [('common_sampler_init','pilot_init'),('common_sampler_clone','pilot_clone'),('common_sampler_accept','pilot_accept'),('common_sampler_free','pilot_free')]:t=t.replace(a,b)
t=t.replace('    observer.phase="prefill";', '    const bool hs_resuming=req.contains("resume");\n    observer.phase="prefill";')
t=t.replace('    observer.decode(ctx_tgt,llama_batch_get_one( inp.data(), n_input - 1),"target");','    if(!hs_resuming) {\n    observer.decode(ctx_tgt,llama_batch_get_one( inp.data(), n_input - 1),"target");')
t=t.replace('    observer.decode(ctx_dft,llama_batch_get_one( inp.data(), n_input),"draft");','    observer.decode(ctx_dft,llama_batch_get_one( inp.data(), n_input),"draft");\n    }')
t=t.replace('if(std::getenv("HS_NO_TRANSFER")==nullptr){','if(!hs_resuming && std::getenv("HS_NO_TRANSFER")==nullptr){')
t=t.replace('    heterospec_direct_ids hs_direct_ids;\n    while (true) {',r'''    heterospec_direct_ids hs_direct_ids;
    bool hs_resume_ready=hs_resuming;
    if(hs_resuming) {
      std::string file=req.at("resume");auto j=pilot_load(file);std::string base=file.substr(0,file.size()-5);
      if(j.at("prompt_ids")!=inp || j.at("pending")!=-1 || j.at("has_eos")!=false)throw std::runtime_error("Resume contract mismatch");
      if(std::getenv("HS_NO_TRANSFER")==nullptr){ctx_tgt=llama_init_from_model(model_tgt,continuation_cp);if(!ctx_tgt)throw std::runtime_error("Resume context");}
      mem_tgt=llama_get_memory(ctx_tgt);
      auto tb=pilot_read(base+".target.kv"),db=pilot_read(base+".draft.kv");
      auto tc=llama_state_set_data(ctx_tgt,tb.data(),tb.size()),dc=llama_state_set_data(ctx_dft,db.data(),db.size());
      auto tr=prefill_observer::state(ctx_tgt),dr=prefill_observer::state(ctx_dft);
      if(tc!=tb.size()||dc!=db.size()||tr!=tb||dr!=db)throw std::runtime_error("Resume KV roundtrip mismatch");
      pilot_free(smpl);pilot_free(drafts[0].smpl);
      smpl=pilot_restore_sampler(model_tgt,ctx_tgt,params.sampling,j.at("target_sampler"));
      drafts[0].smpl=pilot_restore_sampler(model_dft,ctx_dft,params.sampling,j.at("draft_sampler"));
      hs_direct_ids.ids=j.at("ids").get<std::vector<int>>();hs_direct_ids.eog=j.at("eog").get<std::vector<bool>>();
      n_predict=j.at("n_predict");n_drafted=j.at("n_drafted");n_accept=j.at("n_accept");n_past_tgt=j.at("n_past_tgt");n_past_dft=j.at("n_past_dft");
      auto&d=drafts[0];d.active=j.at("active");d.drafting=j.at("drafting");d.skip=j.at("skip");d.i_batch_dft=j.at("i_batch_dft");
      d.i_batch_tgt=j.at("i_batch_tgt").get<std::vector<int>>();d.tokens=j.at("draft_tokens").get<std::vector<int>>();
      d.dists.clear();std::ifstream df(base+".dists",std::ios::binary);
      for(auto&n:j.at("dist_sizes")){std::vector<llama_token_data>v(n.get<size_t>());df.read((char*)v.data(),v.size()*sizeof(llama_token_data));d.dists.push_back(std::move(v));}
      if(!df)throw std::runtime_error("Draft distribution restore failed");
      pilot_restore_batch(batch_tgt,j.at("batch_target"));pilot_restore_batch(batch_dft,j.at("batch_draft"));
      pilot_json(observer.path+".resume.json",{{"source",file},{"target_roundtrip",true},{"draft_roundtrip",true},{"target_position",prefill_observer::positions(ctx_tgt)},{"draft_position",prefill_observer::positions(ctx_dft)},{"target_sampler",pilot_sampler(smpl,ctx_tgt)},{"draft_sampler",pilot_sampler(d.smpl,ctx_dft)},{"effective_greedy_only",true},{"no_prefill_recompute",true}});
    }
    while (true) {
      if(!hs_resume_ready) {''')
needle='        // evaluate the target model on the drafted tokens'
t=t.replace(needle,'      } else { hs_resume_ready=false; }\n'+needle)
needle='            observer.decode(ctx_tgt,batch_tgt,"target");'
assert t.count(needle)==1
t=t.replace(needle,r'''            std::string hs_checkpoint;
            if(!hs_resuming && req.contains("checkpoint_window") && n_predict>=req.at("checkpoint_window").at(0).get<int>() && n_predict<=req.at("checkpoint_window").at(1).get<int>()) {
              hs_checkpoint=observer.path+".cp-"+std::to_string(n_predict);
              auto tb=prefill_observer::state(ctx_tgt),db=prefill_observer::state(ctx_dft);
              auto &d=drafts[0];std::vector<size_t>sizes;std::ofstream df(hs_checkpoint+".dists",std::ios::binary);
              for(auto&v:d.dists){sizes.push_back(v.size());df.write((char*)v.data(),v.size()*sizeof(llama_token_data));}df.close();
              pilot_write(hs_checkpoint+".target.kv",tb);pilot_write(hs_checkpoint+".draft.kv",db);
              auto ta=prefill_observer::state(ctx_tgt),da=prefill_observer::state(ctx_dft);
              if(tb!=ta||db!=da)throw std::runtime_error("Checkpoint mutated donor");
              auto cp=continuation_cp;
              pilot_json(hs_checkpoint+".json",{{"schema","heterospec.natural.preverification.v1"},{"request",req.at("request_id")},{"prompt_ids",inp},{"ids",hs_direct_ids.ids},{"eog",hs_direct_ids.eog},{"pending",pending},{"has_eos",has_eos},
                {"n_predict",n_predict},{"n_drafted",n_drafted},{"n_accept",n_accept},{"n_past_tgt",n_past_tgt},{"n_past_dft",n_past_dft},
                {"target_position",prefill_observer::positions(ctx_tgt)},{"draft_position",prefill_observer::positions(ctx_dft)},{"sequence_ownership","serialized API full state; single sequence0"},
                {"target_sampler",pilot_sampler(smpl,ctx_tgt)},{"draft_sampler",pilot_sampler(d.smpl,ctx_dft)},
                {"active",d.active},{"drafting",d.drafting},{"skip",d.skip},{"i_batch_dft",d.i_batch_dft},{"i_batch_tgt",d.i_batch_tgt},{"draft_tokens",d.tokens},{"dist_sizes",sizes},
                {"batch_target",pilot_batch(batch_tgt)},{"batch_draft",pilot_batch(batch_dft)},{"phase","continuation-before-target-verification"},{"k",n_draft},{"ub",llama_n_ubatch(ctx_tgt)},{"prefill_ub",observer.prefill_ub},
                {"outputs_max",cp.n_outputs_max},{"outputs_max_per_seq",cp.n_outputs_max_per_seq},{"source_unchanged",true},{"target_state_bytes",tb.size()},{"draft_state_bytes",db.size()}});
            }
            observer.decode(ctx_tgt,batch_tgt,"target");
            if(!hs_checkpoint.empty()) {
              const int nv=llama_vocab_n_tokens(vocab_tgt);std::vector<float>values;for(int i=0;i<batch_tgt.n_tokens;i++){const float*l=llama_get_logits_ith(ctx_tgt,i);values.insert(values.end(),l,l+nv);}
              pilot_write(hs_checkpoint+".natural.f32",values);
            }''')
p.write_text(t,encoding='utf8')
p=R/'src/observer.h';t=p.read_text().replace('auto * clone=common_sampler_clone(sampler);','auto * clone=pilot_clone(sampler);');p.write_text(t,encoding='utf8')
# Target frontend remains identical; tracking is only needed to link observer's real clone.
p=R/'src/target.cpp';t=p.read_text().replace('#include "observer.h"','#include "pilot_state.h"\n#include "observer.h"');p.write_text(t,encoding='utf8')
print('IMPLEMENTED true pre-forward snapshots and greedy-scope restore',flush=True)
