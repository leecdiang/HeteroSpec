#define main inherited_main
#include "probe.cpp"
#undef main
static double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static std::string render(llama_model*m,const json&messages,bool assistant){
    std::vector<std::string>roles,texts;for(auto&x:messages){roles.push_back(x.at("role"));texts.push_back(x.at("content"));}
    std::vector<llama_chat_message> chat;for(size_t i=0;i<roles.size();i++)chat.push_back({roles[i].c_str(),texts[i].c_str()});
    auto tmpl=llama_model_chat_template(m,nullptr);check(tmpl,"template absent");
    int n=llama_chat_apply_template(tmpl,chat.data(),chat.size(),assistant,nullptr,0);check(n>=0,"native template unsupported");
    std::string s(n,'\0');check(llama_chat_apply_template(tmpl,chat.data(),chat.size(),assistant,s.data(),n)==n,"render size");return s;
}
static std::vector<int> tokenize(llama_model*m,const std::string&s){auto*v=llama_model_get_vocab(m);int n=-llama_tokenize(v,s.data(),s.size(),nullptr,0,true,true);check(n>0,"token count");std::vector<int>ids(n);check(llama_tokenize(v,s.data(),s.size(),ids.data(),n,true,true)==n,"tokenize");return ids;}
static void raw(const fs::path&p,const void*b,size_t n){std::ofstream f(p,std::ios::binary);f.write((const char*)b,n);check(bool(f),"raw write");}
static std::vector<uint8_t> snapshot(llama_context*c){std::vector<uint8_t>b(llama_state_seq_get_size(c,0));check(llama_state_seq_get_data(c,b.data(),b.size(),0)==b.size(),"snapshot");return b;}
static void service_decode(llama_context*c,const int*ids,int n,int pos,bool last,bool all=false){auto b=llama_batch_init(n,0,1);b.n_tokens=n;for(int i=0;i<n;i++){b.token[i]=ids[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=all||(last&&i==n-1);}hsc::decode_begin(c,"target",true,n);int rc=llama_decode(c,b);llama_batch_free(b);check(rc==0,"decode");llama_synchronize(c);hsc::decode_end();}
static void request(llama_model*m,llama_context*c,const json&u,const fs::path&out){
    auto ids=u.at("tokens").get<std::vector<int>>();int head=u.at("head");std::string arm=u.at("arm");bool capture=u.value("capture",false);int cap=u.value("cap",128);
    check(head>=0&&head<int(ids.size())&&ids.size()+cap<=llama_n_ctx(c),"request capacity");check(arm=="R"||arm=="QB"||arm=="WB-cut"||arm=="WB-rechunk","arm");
    fs::path dir=out/u.at("id").get<std::string>();check(fs::create_directories(dir),"exclusive request");
    llama_memory_clear(llama_get_memory(c),true);hs_scope::active=false;hsc::begin("baseline",32);auto t=Clock::now();
    std::vector<uint8_t>state;
    if(u.contains("state")){std::ifstream f(u.at("state").get<std::string>(),std::ios::binary|std::ios::ate);check(bool(f),"state open");state.resize(size_t(f.tellg()));f.seekg(0);f.read((char*)state.data(),state.size());check(bool(f),"state read");}
    else{for(int i=0;i<head;i++)service_decode(c,ids.data()+i,1,i,false);state=snapshot(c);raw(dir/"prefix.bin",state.data(),state.size());}
    double producer=seconds(t);llama_memory_clear(llama_get_memory(c),true);
    // Resident host snapshot lookup/import is within the complete service clock.
    t=Clock::now();check(llama_state_seq_set_data(c,state.data(),state.size(),0)==state.size(),"restore");check(llama_memory_seq_pos_max(llama_get_memory(c),0)==head-1,"restored position");
    double import_s=seconds(t);json calls=json::array();
#ifndef TPDS_ORACLE
    auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(c));check(kv&&kv->get_cells(0).get_used()==uint32_t(head)&&kv->get_cells(0).used_max_p1()==uint32_t(head),"dense physical restore");
#endif
    hs_scope::active=arm!="R";hs_scope::requested_layout=0;int pos=head;
    while(pos<int(ids.size())){int n=std::min(arm=="R"?1:32,int(ids.size())-pos);auto widths=cuts(c,arm=="WB-rechunk"?"WB-cut":arm,pos,n);if(arm=="WB-rechunk")widths.resize(1);for(auto w:widths){calls.push_back({{"head",pos},{"width",w}});service_decode(c,ids.data()+pos,int(w),pos,pos+int(w)==int(ids.size()));pos+=int(w);}}
    double append_s=seconds(t);std::vector<int>output;int vocab=llama_vocab_n_tokens(llama_model_get_vocab(m));double io=0;
    for(int k=0;k<cap;k++){auto*logits=llama_get_logits_ith(c,-1);check(logits,"logits");if(capture){auto z=Clock::now();raw(dir/(std::to_string(k)+".f32"),logits,size_t(vocab)*4);io+=seconds(z);}int best=0;for(int v=0;v<vocab;v++){check(std::isfinite(logits[v]),"finite");if(logits[v]>logits[best])best=v;}output.push_back(best);if(llama_vocab_is_eog(llama_model_get_vocab(m),best)||k+1==cap)break;service_decode(c,&best,1,pos++,true);}
    llama_synchronize(c);double service=seconds(t);auto final=snapshot(c);if(capture)raw(dir/"final.bin",final.data(),final.size());
    // Read-only retained snapshot bytes remain untouched after every request.
    save(dir/"receipt.json",{{"arm",arm},{"head",head},{"physical_dense_head",head},{"calls",calls},{"output",output},{"producer_or_file_read_s",producer},{"import_s",import_s},{"append_from_receipt_s",append_s},{"service_s",service},{"observer_io_s",io},{"state_bytes",state.size()},{"pending_token",output.back()},{"final_position",llama_memory_seq_pos_max(llama_get_memory(c),0)},{"capture",capture}});hs_scope::active=false;
}
int main(int argc,char**argv){try{
    check(argc==4,"worker MODEL manifest out");auto j=read(argv[2]);fs::path out=argv[3];auto bin=fs::absolute(argv[0]).parent_path();
    ggml_backend_load_all_from_path(bin.string().c_str());llama_backend_init();ggml_backend_dev_t gpu=nullptr;
    for(size_t i=0;i<ggml_backend_dev_count();i++){auto d=ggml_backend_dev_get(i);if(std::string(ggml_backend_dev_description(d)).find("5070")!=std::string::npos)gpu=d;}
    check(gpu,"RTX required");ggml_backend_dev_t devices[]={gpu,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
    std::string mode=j.at("mode");mp.vocab_only=mode=="tokenize";auto t=Clock::now();
    std::unique_ptr<llama_model,decltype(&llama_model_free)> m(llama_model_load_from_file(argv[1],mp),llama_model_free);check(bool(m),"load");save(out/"load.json",{{"seconds",seconds(t)}});
    if(mode=="tokenize"){
        save(out/"template.json",{{"template",llama_model_chat_template(m.get(),nullptr)},{"renderer","llama_chat_apply_template"},{"add_special",true},{"parse_special",true}});
        std::ofstream f(out/"tokens.jsonl");for(auto&row:j.at("rows")){auto r=row;auto msgs=row.at("messages");auto cached=msgs;cached.erase(cached.size()-1);auto a=render(m.get(),cached,false),b=render(m.get(),msgs,true);r["cached_text"]=a;r["request_text"]=b;r["cached_ids"]=tokenize(m.get(),a);r["request_ids"]=tokenize(m.get(),b);f<<r.dump()<<'\n';}return 0;
    }
    auto p=llama_context_default_params();p.n_ctx=j.at("capacity");p.n_batch=1024;p.n_ubatch=32;p.n_outputs_max=32;p.n_outputs_max_per_seq=32;p.n_threads=p.n_threads_batch=24;p.type_k=p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
    hs_scope::active=false;t=Clock::now();std::unique_ptr<llama_context,decltype(&llama_free)>ctx(llama_init_from_model(m.get(),p),llama_free);check(bool(ctx),"context");
    if(mode=="admit"){size_t free=0,total=0;ggml_backend_dev_memory(gpu,&free,&total);save(out/"admission.json",{{"capacity",p.n_ctx},{"free",free},{"total",total},{"init_s",seconds(t)},{"reserve_bytes",536870912},{"admitted",free<=total&&free>=536870912}});return 0;}

    if(mode=="allocator_census"){
        auto*kv=dynamic_cast<llama_kv_cache*>(llama_get_memory(ctx.get()));check(kv,"dense KV");json result=json::array();
        for(auto&r:j.at("rows")){
            auto ids=r.at("tokens").get<std::vector<int>>();int head=r.at("head");kv->clear(false);llama_seq_id seq=0;
            auto meta=[&](int pos,int n,bool apply){llama_batch_allocr alloc(1);auto b=alloc.ubatch_reserve(n,1);b.seq_id_unq[0]=0;for(int i=0;i<n;i++){b.token[i]=ids[pos+i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i]=&seq;b.output[i]=0;}auto slot=kv->find_slot(b,false);check(!slot.empty(),"allocator slot");auto h=slot.head();if(apply)kv->apply_ubatch(slot,b);return h;};
            if(head)check(meta(0,head,true)==0,"dense prefix origin");int physical=meta(head,std::min(32,int(ids.size())-head),false);
            check(physical==head&&kv->get_cells(0).get_used()==uint32_t(head)&&kv->get_cells(0).used_max_p1()==uint32_t(head),"allocator head");
            result.push_back({{"id",r.at("id")},{"physical_head",physical},{"padding",kv->scalar_padding()},{"metadata_only",true},{"kv_bytes_computed",false}});
        }save(out/"allocator.json",result);return 0;
    }
    if(mode=="requests"){for(auto&u:j.at("units"))request(m.get(),ctx.get(),u,out);return 0;}
    throw std::runtime_error("unsupported mode");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
