#include "llama.h"
#include "ggml-backend.h"
#include "httplib.h"
#include "json.hpp"
#include <algorithm>
#include <chrono>
#include <iostream>
#include <limits>
#include <filesystem>
#include <fstream>
#include <cstdlib>
#include <mutex>
#include <stdexcept>
#include <vector>
using json=nlohmann::ordered_json;
using clock_type=std::chrono::steady_clock;
static double ms(clock_type::time_point a){return std::chrono::duration<double,std::milli>(clock_type::now()-a).count();}
struct Engine {
    llama_model *model=nullptr;
    llama_context *fast=nullptr,*verify=nullptr;
    const llama_vocab *vocab=nullptr;
    llama_sampler *greedy=nullptr;
    bool fixtures=false;
    std::string stage="init";
    json graph_observations=json::array();
    std::mutex lock;
    Engine(const char *model_path,const char *backend_path,bool allow_fixtures):fixtures(allow_fixtures){
        ggml_backend_load_all_from_path(backend_path);
        auto dev=ggml_backend_dev_by_name("CUDA0");if(!dev)throw std::runtime_error("CUDA0 unavailable");
        ggml_backend_dev_t devices[]={dev,nullptr};auto mp=llama_model_default_params();mp.devices=devices;mp.n_gpu_layers=999;mp.split_mode=LLAMA_SPLIT_MODE_NONE;
        model=llama_model_load_from_file(model_path,mp);if(!model)throw std::runtime_error("model load failed");vocab=llama_model_get_vocab(model);
        auto cp=llama_context_default_params();cp.n_ctx=4096;cp.n_batch=2048;cp.n_seq_max=1;cp.n_threads=24;cp.n_threads_batch=24;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.offload_kqv=true;cp.kv_unified=false;
        if(fixtures){cp.cb_eval=[](ggml_tensor*t,bool ask,void*data){auto*self=static_cast<Engine*>(data);if(ask&&(std::string(t->name)=="attn_norm-0"||std::string(t->name)=="result_output"))self->graph_observations.push_back({{"stage",self->stage},{"name",t->name},{"ne",{t->ne[0],t->ne[1],t->ne[2],t->ne[3]}}});return false;};cp.cb_eval_user_data=this;}
        cp.n_ubatch=4;fast=llama_init_from_model(model,cp);cp.n_ubatch=32;verify=llama_init_from_model(model,cp);
        if(!fast||!verify)throw std::runtime_error("two-context allocation failed");
        greedy=llama_sampler_chain_init(llama_sampler_chain_default_params());int32_t ns=0;const auto* suppressed=llama_vocab_get_suppress_tokens(vocab,&ns);std::vector<llama_logit_bias> biases;
        for(int32_t i=0;i<ns;++i)biases.push_back({suppressed[i],-std::numeric_limits<float>::infinity()});
        if(!biases.empty())llama_sampler_chain_add(greedy,llama_sampler_init_logit_bias(llama_vocab_n_tokens(vocab),(int)biases.size(),biases.data()));
        llama_sampler_chain_add(greedy,llama_sampler_init_greedy());
        std::cerr<<"JSA_DVR shared model; fast UB4; verifier UB32; contexts4096; single sequence; FA off; CUDA0\n";
    }
    ~Engine(){if(greedy)llama_sampler_free(greedy);if(fast)llama_free(fast);if(verify)llama_free(verify);if(model)llama_model_free(model);}
    void decode(llama_context *ctx,const std::vector<llama_token>&tokens,int start,bool all_logits){
        auto batch=llama_batch_init((int)tokens.size(),0,1);batch.n_tokens=(int)tokens.size();
        for(int i=0;i<batch.n_tokens;++i){batch.token[i]=tokens[i];batch.pos[i]=start+i;batch.n_seq_id[i]=1;batch.seq_id[i][0]=0;batch.logits[i]=all_logits||i==batch.n_tokens-1;}
        int rc=llama_decode(ctx,batch);llama_batch_free(batch);if(rc)throw std::runtime_error("decode failed "+std::to_string(rc));
    }
    llama_token sample(llama_context *ctx,int row){return llama_sampler_sample(greedy,ctx,row);}
    std::vector<uint8_t> state(llama_context *ctx){
        llama_synchronize(ctx);std::vector<uint8_t>b(llama_state_seq_get_size(ctx,0));
        if(llama_state_seq_get_data(ctx,b.data(),b.size(),0)!=b.size())throw std::runtime_error("short KV export");return b;
    }
    json complete(const json&q){
        std::lock_guard<std::mutex> guard(lock);
        const auto begun=clock_type::now();const auto prompt=q.at("prompt").get<std::string>();int cap=q.at("n_predict").get<int>();
        if(cap<1||cap>128)throw std::runtime_error("cap outside frozen range");
        const bool fixture=q.contains("fixture_bad_proposal_at")||q.contains("fixture_padding_token")||q.contains("fixture_pending_eog")||q.contains("fixture_save_state")||q.contains("fixture_verified_eog_at");
        if(fixture&&!fixtures)throw std::runtime_error("fixtures disabled in formal process");
        llama_memory_clear(llama_get_memory(fast),true);llama_memory_clear(llama_get_memory(verify),true);llama_sampler_reset(greedy);
        graph_observations=json::array();stage="prefill";
        std::vector<llama_token> input(prompt.size()+64);int n=llama_tokenize(vocab,prompt.c_str(),(int)prompt.size(),input.data(),(int)input.size(),true,true);
        if(n<=0||n+cap+32>=4096)throw std::runtime_error("invalid context input");input.resize(n);
        // The verifier owns the consistent prefill and every retained continuation KV.
        decode(verify,input,0,false);llama_token pending=sample(verify,-1);
        if(q.value("fixture_pending_eog",false))pending=llama_vocab_eos(vocab);
        double prefill=ms(begun);auto gen_started=clock_type::now();std::vector<llama_token> out{pending};json blocks=json::array();size_t copied=0;int fast_calls=0,verify_calls=0;
        while((int)out.size()<cap&&!llama_vocab_is_eog(vocab,out.back())){
            int position=llama_memory_seq_pos_max(llama_get_memory(verify),0)+1;
            auto kv=state(verify);llama_memory_clear(llama_get_memory(fast),true);
            if(llama_state_seq_set_data(fast,kv.data(),kv.size(),0)!=kv.size())throw std::runtime_error("short KV import");copied+=kv.size();
            if(llama_memory_seq_pos_max(llama_get_memory(fast),0)!=position-1)throw std::runtime_error("copied position mismatch");
            bool copy_equal=true;if(fixtures)copy_equal=state(fast)==kv;
            if(!copy_equal)throw std::runtime_error("KV round trip mismatch");
            if(fixtures&&q.value("fixture_save_state",false)&&blocks.empty()){
                auto source_after=state(verify),destination=state(fast);if(source_after!=kv||destination!=kv)throw std::runtime_error("copy changed verifier prefix");
                const char*path=std::getenv("JSA_E_STATE_DIR");if(!path)throw std::runtime_error("state proof destination missing");std::filesystem::create_directories(path);
                auto write=[&](const char*name,const std::vector<uint8_t>&b){std::ofstream f(std::filesystem::path(path)/name,std::ios::binary);f.write((const char*)b.data(),b.size());if(!f)throw std::runtime_error("state proof write failed");};
                write("verifier_prefix.state",kv);write("verifier_after_copy.state",source_after);write("fast_loaded_prefix.state",destination);
            }
            std::vector<llama_token> proposal;llama_token token=pending;int maximum=std::min(31,cap-(int)out.size());
            for(int i=0;i<maximum;++i){
                stage="fast";decode(fast,{token},position+i,true);++fast_calls;token=sample(fast,0);proposal.push_back(token);
                if(llama_vocab_is_eog(vocab,token))break;
            }
            const int inject=q.value("fixture_bad_proposal_at",-1);
            if(inject>=0&&inject<(int)proposal.size()&&blocks.empty())proposal[inject]=(proposal[inject]+1)%llama_vocab_n_tokens(vocab);
            std::vector<llama_token> rows{pending};rows.insert(rows.end(),proposal.begin(),proposal.end());int real=(int)rows.size();
            int dummy=q.value("fixture_padding_token",32);if(dummy<0||dummy>=llama_vocab_n_tokens(vocab))throw std::runtime_error("invalid dummy ID");rows.resize(32,dummy);
            stage="verify";decode(verify,rows,position,true);++verify_calls;
            std::vector<llama_token> predictions;for(int i=0;i<32;++i)predictions.push_back(sample(verify,i));
            const auto native_predictions=predictions;const auto native_proposal=proposal;
            const int eog_fixture=q.value("fixture_verified_eog_at",-1);
            if(eog_fixture>=0&&blocks.empty()){
                if(eog_fixture>30||proposal.size()!=31)throw std::runtime_error("synthetic EOG decision fixture requires31 actual proposals");
                // Explicit synthetic decision-branch injection, never an ordinary
                // model output or a continuation/KV equivalence claim. Preserve
                // all real native predictions before forcing this terminal case.
                for(int j=0;j<eog_fixture;++j)proposal[j]=predictions[j];
                predictions[eog_fixture]=llama_vocab_eos(vocab);proposal[eog_fixture]=predictions[eog_fixture];
            }
            int accepted=0,keep=1;bool mismatch=false,terminal=false;llama_token correction=-1;
            for(int j=0;j<(int)proposal.size();++j){
                llama_token selected=predictions[j];out.push_back(selected);keep=j+1;
                if(selected!=proposal[j]){mismatch=true;correction=selected;pending=selected;break;}
                ++accepted;
                if(llama_vocab_is_eog(vocab,selected)||(int)out.size()==cap){terminal=true;break;}
            }
            if(!mismatch&&!terminal){
                keep=real;
                if((int)out.size()<cap&&!llama_vocab_is_eog(vocab,out.back())){pending=predictions[real-1];out.push_back(pending);}
            }
            // Remove all rejected and padded KV; keep excludes the new pending token.
            if(!llama_memory_seq_rm(llama_get_memory(verify),0,position+keep,-1))throw std::runtime_error("verifier rollback failed");
            if(llama_memory_seq_pos_max(llama_get_memory(verify),0)!=position+keep-1)throw std::runtime_error("rollback position mismatch");
            if(fixtures&&q.value("fixture_save_state",false)&&blocks.empty()){
                auto retained=state(verify);const char*path=std::getenv("JSA_E_STATE_DIR");std::ofstream f(std::filesystem::path(path)/"verifier_retained.state",std::ios::binary);f.write((const char*)retained.data(),retained.size());if(!f)throw std::runtime_error("retained state proof write failed");
            }
            json record={{"position",position},{"actual_queries",32},{"real_queries",real},{"padding_queries",32-real},{"accepted_proposals",accepted},{"mismatch",mismatch},{"correction",correction},{"kv_kept_queries",keep},{"retained_kv_owner","verifier"},{"copy_bytes",kv.size()},{"fast_ub",4},{"verifier_ub",32}};
            if(fixtures){record["pending_in"]=rows[0];record["proposal"]=proposal;record["verification_predictions"]=predictions;record["native_proposal"]=native_proposal;record["native_verification_predictions"]=native_predictions;record["synthetic_verified_eog_at"]=blocks.empty()?eog_fixture:-1;record["copy_roundtrip_equal"]=copy_equal;}
            blocks.push_back(record);
        }
        llama_synchronize(fast);llama_synchronize(verify);bool eos=llama_vocab_is_eog(vocab,out.back());
        std::string content;
        for(auto id:out){std::vector<char>b(64);int count=llama_token_to_piece(vocab,id,b.data(),(int)b.size(),0,false);if(count<0){b.resize(-count);count=llama_token_to_piece(vocab,id,b.data(),(int)b.size(),0,false);}if(count>0)content.append(b.data(),count);}
        llama_memory_clear(llama_get_memory(fast),true);llama_memory_clear(llama_get_memory(verify),true);
        double generation=ms(gen_started);
        return {{"tokens",out},{"tokens_predicted",out.size()},{"prompt",prompt},{"prompt_ids",input},{"content",content},{"stop_type",eos?"eos":"limit"},{"truncated",false},{"timings",{{"cache_n",0},{"prompt_n",n},{"prompt_ms",prefill},{"predicted_ms",generation}}},{"method","LLM42_DVR_GGML_W32"},{"blocks",blocks},{"fast_decode_calls",fast_calls},{"verify_decode_calls",verify_calls},{"state_copy_bytes",copied},{"shared_model_weights",true},{"fixtures",fixture},{"request_reset",true},{"kv_provenance","verifier-only; optimistic KV discarded each block"},{"graph_observations",graph_observations}};
    }
};
int main(int argc,char**argv){
    if(argc<4)return 2;
    try{
        Engine engine(argv[1],argv[2],argc>4&&std::string(argv[4])=="fixtures");httplib::Server server;
        server.Get("/health",[](const httplib::Request&,httplib::Response&r){r.set_content("{\"status\":\"ok\"}","application/json");});
        server.Post("/completion",[&](const httplib::Request&q,httplib::Response&r){try{r.set_content(engine.complete(json::parse(q.body)).dump(),"application/json");}catch(const std::exception&e){r.status=500;r.set_content(json({{"error",e.what()}}).dump(),"application/json");}});
        server.listen("127.0.0.1",std::stoi(argv[3]));
    }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
    return 0;
}
