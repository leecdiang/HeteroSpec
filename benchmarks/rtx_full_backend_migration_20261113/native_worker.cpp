// Build separately inside each pinned complete llama.cpp tree. No mixed DLLs.
#include "llama.h"
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using clock_type = std::chrono::steady_clock;
static double seconds(clock_type::time_point a, clock_type::time_point b) {
    return std::chrono::duration<double>(b-a).count();
}
int main(int argc, char **argv) {
    // Merely building this executable does not initialize a backend.
    if(argc!=5) { std::cerr<<"worker MODEL REQUESTS.tsv RESULTS.jsonl CAPTURE_PREFIX\n"; return 2; }
    llama_model *model=nullptr; llama_context *ctx=nullptr;
    try {
        std::ifstream in(argv[2]); std::ofstream out(argv[3]);
        if(!in || !out) throw std::runtime_error("open input/output");
        auto started=clock_type::now();
        llama_backend_init();
        auto mp=llama_model_default_params(); mp.n_gpu_layers=999; mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        model=llama_model_load_from_file(argv[1],mp);
        if(!model) throw std::runtime_error("load model");
        auto cp=llama_context_default_params();
        cp.n_ctx=1024; cp.n_batch=32; cp.n_ubatch=32; cp.n_seq_max=1;
        cp.n_threads=2; cp.n_threads_batch=2; cp.type_k=GGML_TYPE_F16; cp.type_v=GGML_TYPE_F16;
        cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED; cp.attention_type=LLAMA_ATTENTION_TYPE_CAUSAL;
        ctx=llama_init_from_model(model,cp); if(!ctx) throw std::runtime_error("context");
        const auto *vocab=llama_model_get_vocab(model); int nv=llama_vocab_n_tokens(vocab);
        out<<"{\"event\":\"loaded\",\"load_s\":"<<seconds(started,clock_type::now())<<"}\n";
        int id,np,nc; char mode;
        while(in>>id>>mode>>np>>nc) {
            if((mode!='P'&&mode!='G'&&mode!='Q')||np<1||np>768||nc!=128) throw std::runtime_error("request envelope");
            std::vector<llama_token> prompt(np),forced(nc),emitted;
            for(auto &t:prompt) if(!(in>>t)||t<0||t>=nv) throw std::runtime_error("prompt token");
            for(auto &t:forced) if(!(in>>t)||t<0||t>=nv) throw std::runtime_error("continuation token");
            int pos=0,calls=0,rows=0; bool eog=false; std::vector<float> captures;
            auto begin=clock_type::now();
            llama_memory_clear(llama_get_memory(ctx),true);
            auto decode=[&](const llama_token *ts,int n) {
                auto b=llama_batch_init(n,0,1);
                b.n_tokens=n;
                for(int i=0;i<n;i++) {b.token[i]=ts[i];b.pos[i]=pos+i;b.n_seq_id[i]=1;b.seq_id[i][0]=0;b.logits[i]=(i==n-1);}
                int rc=llama_decode(ctx,b); llama_batch_free(b);
                if(rc) throw std::runtime_error("decode failed");
                llama_synchronize(ctx); pos+=n; rows+=n; calls++;
                if(mode=='Q') {
                    const float *p=llama_get_logits_ith(ctx,-1);
                    if(!p) throw std::runtime_error("no logits");
                    for(int j=0;j<nv;j++) if(!std::isfinite(p[j])) throw std::runtime_error("nonfinite logits");
                    captures.insert(captures.end(),p,p+nv);
                }
            };
            for(int i=0;i<np;i+=32) decode(prompt.data()+i,std::min(32,np-i));
            auto prefill_end=clock_type::now(); double ttft=0;
            for(int i=0;i<nc;i++) {
                llama_token t=forced[i];
                if(mode=='G') {
                    const float *p=llama_get_logits_ith(ctx,-1);
                    if(!p) throw std::runtime_error("no logits");
                    t=0;
                    for(int j=0;j<nv;j++) {if(!std::isfinite(p[j])) throw std::runtime_error("nonfinite logits"); if(p[j]>p[t]) t=j;}
                    // Lowest token ID wins ties. EOG is recorded, not decoded as content.
                    if(i==0) ttft=seconds(begin,clock_type::now());
                    if(llama_vocab_is_eog(vocab,t)) {eog=true;break;}
                }
                emitted.push_back(t);
                // Feed every fixed continuation token, including the final one.
                // G also feeds its final emitted token: declared state-complete response.
                decode(&t,1);
            }
            llama_synchronize(ctx); auto end=clock_type::now();
            if(mode=='Q') {
                std::ofstream f(std::string(argv[4])+"-"+std::to_string(id)+".f32",std::ios::binary);
                f.write(reinterpret_cast<const char*>(captures.data()),captures.size()*sizeof(float));
                if(!f) throw std::runtime_error("capture write");
            }
            out.precision(17);
            out<<"{\"event\":\"request\",\"id\":"<<id<<",\"mode\":\""<<mode<<"\",\"seconds\":"<<seconds(begin,end)
               <<",\"prefill_s\":"<<seconds(begin,prefill_end)<<",\"continuation_s\":"<<seconds(prefill_end,end)
               <<",\"ttft_s\":"<<ttft<<",\"rows\":"<<rows<<",\"calls\":"<<calls<<",\"eog\":"<<(eog?"true":"false")
               <<",\"kv_last_position\":"<<llama_memory_seq_pos_max(llama_get_memory(ctx),0)
               <<",\"capture_floats\":"<<captures.size()<<",\"tokens\":[";
            for(size_t i=0;i<emitted.size();i++){if(i)out<<',';out<<emitted[i];}
            out<<"]}\n"; out.flush(); if(!out) throw std::runtime_error("result write");
        }
        if(!in.eof()) throw std::runtime_error("malformed request");
        llama_free(ctx);ctx=nullptr;llama_model_free(model);model=nullptr;llama_backend_free();
        out<<"{\"event\":\"done\",\"worker_s\":"<<seconds(started,clock_type::now())<<"}\n";
        return 0;
    } catch(const std::exception &e) {
        std::cerr<<e.what()<<'\n'; if(ctx)llama_free(ctx);if(model)llama_model_free(model);llama_backend_free();return 1;
    }
}
