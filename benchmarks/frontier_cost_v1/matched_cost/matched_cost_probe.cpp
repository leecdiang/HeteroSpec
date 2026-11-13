#include "llama.h"
#include "llama-kv-cache.h"
#include "llama-model.h"
#include "ggml-backend.h"
#include "hs_scope.h"
#include "hsc_counter.h"
extern "C" {
#include "hash/sha256/sha256.h"
}
#include <nlohmann/json.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using json = nlohmann::json;
namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;
using Bytes = std::vector<unsigned char>;
static void need(bool ok, const char * message) { if (!ok) throw std::runtime_error(message); }
static double since(Clock::time_point start) { return std::chrono::duration<double>(Clock::now()-start).count(); }
inline bool phase_observe = false;
// These two headers are the exact reconstructed M2 frontend, not a new lowering.
#include "resident_context.hpp"

static void dump(const fs::path & path, const json & value) {
    auto temp = path; temp += ".tmp";
    { std::ofstream f(temp); f << value.dump(2) << '\n'; f.flush(); need(bool(f), "JSON write"); }
    fs::rename(temp, path);
}
static std::string sha(const void * data, size_t n) {
    sha256_t ctx; sha256_init(&ctx);
    sha256_update(&ctx, static_cast<const unsigned char *>(data), n);
    unsigned char out[32]; sha256_final(&ctx, out);
    const char * hex = "0123456789abcdef"; std::string text;
    for (auto byte : out) { text += hex[byte >> 4]; text += hex[byte & 15]; }
    return text;
}
static std::string file_sha(const fs::path & path) {
    std::ifstream f(path,std::ios::binary);need(bool(f),"native module file open");
    sha256_t ctx;sha256_init(&ctx);std::vector<unsigned char> block(1024*1024);
    while(f) { f.read(reinterpret_cast<char *>(block.data()),block.size());sha256_update(&ctx,block.data(),size_t(f.gcount())); }
    need(f.eof(),"native module read");unsigned char bytes[32];sha256_final(&ctx,bytes);
    const char * hex="0123456789abcdef";std::string result;for(auto b:bytes){result+=hex[b>>4];result+=hex[b&15];}return result;
}
static json native_modules(const fs::path & directory,const json & expected) {
    std::ifstream f("/proc/self/maps");need(bool(f),"Linux native module map required");
    json result=json::object();std::string line;
    while(std::getline(f,line)) {
        auto start=line.find('/');if(start==std::string::npos)continue;
        fs::path path=line.substr(start);auto name=path.filename().string();
        if(name.rfind("libllama",0)!=0 && name.rfind("libggml",0)!=0)continue;
        path=fs::canonical(path);name=path.filename().string();
        need(path.parent_path()==fs::canonical(directory),"native module loaded outside frozen library directory");
        need(expected.contains(name),"unbound native module loaded");
        if(!result.contains(name)) {
            auto hash=file_sha(path);need(hash==expected.at(name).get<std::string>(),"native module hash changed");
            result[name]={{"sha256",hash},{"bytes",fs::file_size(path)}};
        }
    }
    need(result.size()>=4,"incomplete native module inventory");return result;
}
struct Store {
    fs::path root; uint64_t bytes = 0, limit = 0; std::map<std::string,size_t> written;
    json put(const void * data, size_t n) {
        const auto hash = sha(data,n);
        if (!written.count(hash)) {
            need(n <= limit-bytes, "raw output byte budget exceeded");
            std::ofstream f(root/(hash+".bin"),std::ios::binary);
            f.write(static_cast<const char *>(data),std::streamsize(n)); f.flush(); need(bool(f),"raw write");
            written[hash]=n; bytes+=n;
        } else need(written.at(hash)==n,"blob identity collision");
        return {{"sha256",hash},{"bytes",n},{"path","blobs/"+hash+".bin"}};
    }
    json put(const Bytes & b) { return put(b.data(),b.size()); }
};
struct Budget {
    uint64_t contexts=0,calls=0,rows=0,attempted_calls=0,attempted_rows=0,max_contexts=0,max_calls=0,max_rows=0;
    json stages=json::object();
    void context() { need(contexts<max_contexts,"context budget exceeded"); ++contexts; }
    void reserve(size_t nc,size_t nr,const std::string & stage) {
        need(nc<=max_calls-calls && nr<=max_rows-rows,"native work budget exceeded"); calls+=nc;rows+=nr;
        if (!stages.contains(stage)) stages[stage]={{"reserved_calls",0},{"reserved_rows",0},{"attempted_calls",0},{"attempted_rows",0}};
        stages[stage]["reserved_calls"]=stages[stage]["reserved_calls"].get<uint64_t>()+nc;
        stages[stage]["reserved_rows"]=stages[stage]["reserved_rows"].get<uint64_t>()+nr;
    }
    void finish(size_t nc,size_t nr,const std::string & stage) {
        attempted_calls+=nc;attempted_rows+=nr;
        stages[stage]["attempted_calls"]=stages[stage]["attempted_calls"].get<uint64_t>()+nc;
        stages[stage]["attempted_rows"]=stages[stage]["attempted_rows"].get<uint64_t>()+nr;
    }
    void call(size_t n,const std::string & stage) { reserve(1,n,stage);finish(1,n,stage); }
    json value() const { return {{"contexts",contexts},{"reserved_native_calls",calls},{"reserved_target_rows",rows},
                                {"attempted_native_calls",attempted_calls},{"attempted_target_rows",attempted_rows},{"by_stage",stages}}; }
};
struct Owner {
    llama_model * model; llama_context * c=nullptr; PhaseContext plan;
    struct { std::string phase; int base=0,caller=0; bool bad=false; } obs;
    bool capture=false; int calls=0; std::map<std::string,double> phases; Budget & budget;
    Owner(llama_model * m,Budget & b,int threads) : model(m),budget(b) {
        budget.context(); auto p=llama_context_default_params();
        p.n_ctx=1024;p.n_batch=1024;p.n_ubatch=32;
        p.n_threads=threads;p.n_threads_batch=threads;p.n_outputs_max=8;p.n_outputs_max_per_seq=8;
        p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;
        hs_scope::active=false;c=llama_init_from_model(model,p);need(c,"context init");hs_scope::active=true;
        need(llama_n_ubatch(c)==32 && llama_n_ctx(c)==1024,"actual context configuration differs");
    }
    ~Owner() { if(c) llama_free(c); }
    llama_kv_cache * cache() { auto * k=dynamic_cast<llama_kv_cache *>(llama_get_memory(c));need(k,"dense cache required");return k; }
    void reset() { plan.clear();llama_memory_clear(llama_get_memory(c),false);need(llama_memory_seq_pos_max(llama_get_memory(c),0)<0,"reset did not empty sequence"); }
    void decode(const std::vector<int> & ids,int pos,bool all,const char * phase,const std::string & stage,bool account=true) {
        if(account)budget.call(ids.size(),stage);
        plan.decode(*this,ids,pos,all,phase);
    }
    void prefix(const std::vector<int> & ids,const std::string & stage) {
        for(size_t p=0;p<ids.size();p+=32) {
            auto end=std::min(ids.size(),p+32);decode(std::vector<int>(ids.begin()+p,ids.begin()+end),int(p),false,"PREFILL",stage);
        }
    }
    Bytes state() {
        llama_synchronize(c);size_t n=llama_state_seq_get_size(c,0);Bytes b(n);
        need(llama_state_seq_get_data(c,b.data(),n,0)==n,"sequence export");return b;
    }
    json geometry(int next) {
        auto * k=cache();const auto & cells=k->get_cells(0);
        bool dense=cells.get_used()==uint32_t(next)&&cells.used_max_p1()==uint32_t(next)&&cells.used_min()==0;
        for(int i=0;i<next;++i) dense=dense&&!cells.is_empty(i)&&cells.pos_get(i)==i&&cells.seq_has(i,0);
        auto requirements=k->phase_append_requirements(next,1);
        need(dense && requirements.size()==1,"native append head, extent or dense mapping failed");
        return {{"used",cells.get_used()},{"occupied_end",cells.used_max_p1()},{"extent",k->phase_current_extent()},
                {"next_q1_extents",requirements},{"dense_seq0",true},{"head_equals_next_by_native_guard",true},
                {"n_ubatch",llama_n_ubatch(c)},{"n_ctx",llama_n_ctx(c)}};
    }
};
struct Capture {
    Bytes initial,final,next;json initial_geometry,final_geometry,next_geometry;
    std::vector<float> vectors,continuation;double operation_s=0;
    json work,executions,artifact;
};
static std::vector<int> chunks(int q,int width) {
    std::vector<int> out;while(q){int take=std::min(q,width);out.push_back(take);q-=take;}return out;
}
static std::vector<std::vector<int>> schedules(int q) {
    std::vector<std::vector<int>> all;
    for(int width:{1,4,8}) { auto v=chunks(q,width);if(std::find(all.begin(),all.end(),v)==all.end())all.push_back(v); }
    return all;
}
static json counters() {
    json physical=json::object();for(size_t q=0;q<hsc::w.target_physical.size();++q)if(hsc::w.target_physical[q])physical[std::to_string(q)]=hsc::w.target_physical[q];
    return {{"outer_calls",hsc::w.target_calls},{"target_rows",hsc::w.target_rows},{"physical_widths",physical},
            {"physical_calls",hsc::w.physical_calls},{"graphs_built",hsc::w.graphs_built},{"graphs_reused",hsc::w.graphs_reused}};
}
static std::vector<float> operation(Owner & owner,const std::vector<int> & rows,int base,const std::vector<int> & schedule,const std::string & stage) {
    const size_t vocab=llama_vocab_n_tokens(llama_model_get_vocab(owner.model));
    std::vector<float> output;output.reserve(rows.size()*vocab);size_t begin=0;
    for(int width:schedule) {
        need(begin+size_t(width)<=rows.size(),"schedule overflow");
        owner.decode(std::vector<int>(rows.begin()+begin,rows.begin()+begin+width),base+int(begin),true,"VERIFY",stage,false);
        for(int i=0;i<width;++i) {
            auto * p=owner.plan.logits(i);need(p,"requested full vector absent");
            output.insert(output.end(),p,p+vocab);
        }
        begin+=width;
    }
    need(begin==rows.size(),"schedule incomplete");
    return output;
}
static std::pair<std::vector<float>,double> measured_operation(Owner & owner,const std::vector<int> & rows,int base,
        const std::vector<int> & schedule,const std::string & stage) {
    owner.budget.reserve(schedule.size(),rows.size(),stage);hsc::begin("counts",base);
    std::vector<float> vectors;double elapsed=0;
    try {
        const auto start=Clock::now();vectors=operation(owner,rows,base,schedule,stage);elapsed=since(start);
    } catch(...) {
        owner.budget.finish(hsc::w.target_calls,hsc::w.target_rows,stage);throw;
    }
    owner.budget.finish(hsc::w.target_calls,hsc::w.target_rows,stage);
    need(hsc::w.target_calls==int64_t(schedule.size()) && hsc::w.target_rows==int64_t(rows.size()),"observed native calls disagree with reserved operation");
    return {std::move(vectors),elapsed};
}
static Capture run(llama_model * model,Budget & budget,const json & input,int q,const std::vector<int> & schedule,
                   const std::string & phase,bool warm,int threads,Store & store) {
    Owner owner(model,budget,threads);auto history=input.at("history").get<std::vector<int>>();
    auto values=input.at("rows").get<std::vector<int>>();values.resize(q);const int base=int(history.size());
    hsc::begin("counts",base);owner.prefix(history,phase+"/prefill");
    Capture out;out.initial=owner.state();out.initial_geometry=owner.geometry(base);
    if(warm) {
        auto warmup=measured_operation(owner,values,base,schedule,phase+"/warmup");
        for(float x:warmup.first)need(std::isfinite(x),"nonfinite warmup vector");
        owner.reset();owner.prefix(history,phase+"/reset_prefill");
        auto reset_state=owner.state();auto reset_geometry=owner.geometry(base);
        need(reset_state==out.initial && reset_geometry==out.initial_geometry,"warm reset changed initial checkpoint");
    }
    owner.plan.clear();auto measured=measured_operation(owner,values,base,schedule,phase+"/operation");
    out.vectors=std::move(measured.first);out.operation_s=measured.second;
    out.work=counters();out.executions=owner.plan.executions;
    for(float x:out.vectors)need(std::isfinite(x),"nonfinite operation vector");
    out.final=owner.state();out.final_geometry=owner.geometry(base+q);
    owner.decode({input.at("continuation").get<int>()},base+q,true,"VERIFY",phase+"/continuation");
    const auto * p=owner.plan.logits(0);out.continuation.assign(p,p+llama_vocab_n_tokens(llama_model_get_vocab(model)));
    for(float x:out.continuation)need(std::isfinite(x),"nonfinite continuation vector");
    out.next=owner.state();out.next_geometry=owner.geometry(base+q+1);
    out.artifact={{"initial_state",store.put(out.initial)},{"operation_vectors",store.put(out.vectors.data(),out.vectors.size()*sizeof(float))},
                  {"final_state",store.put(out.final)},{"continuation_vector",store.put(out.continuation.data(),out.continuation.size()*sizeof(float))},
                  {"continuation_state",store.put(out.next)}};
    return out;
}
static bool equal_vector(const std::vector<float> & a,const std::vector<float> & b) {
    return a.size()==b.size() && std::memcmp(a.data(),b.data(),a.size()*sizeof(float))==0;
}
static json comparison(const Capture & a,const Capture & b) {
    return {{"initial_state",a.initial==b.initial},{"initial_geometry",a.initial_geometry==b.initial_geometry},
            {"full_operation_vectors",equal_vector(a.vectors,b.vectors)},{"final_state",a.final==b.final},{"final_geometry",a.final_geometry==b.final_geometry},
            {"full_continuation_vector",equal_vector(a.continuation,b.continuation)},{"continuation_state",a.next==b.next},{"continuation_geometry",a.next_geometry==b.next_geometry}};
}
static bool passed(const json & comp) { for(auto it=comp.begin();it!=comp.end();++it)if(!it.value().get<bool>())return false;return true; }
static json row(const Capture & c,const std::vector<int> & schedule) {
    return {{"schedule",schedule},{"captures",c.artifact},{"initial_geometry",c.initial_geometry},{"final_geometry",c.final_geometry},
            {"continuation_geometry",c.next_geometry},{"work",c.work},{"executions",c.executions}};
}
int main(int argc,char ** argv) {
    bool owns=false;fs::path output;json result={{"schema","heterospec.matched-local-operation.v1"},{"status","STARTED"},
        {"historical_GPU_reference_qualification","NOT_ESTABLISHED"},{"full_service_performance_claim",false},
        {"qualification",json::array()},{"measurements",json::array()}};
    Budget budget;
    try {
        need(argc==3,"matched_cost_probe JOB OUT");std::ifstream input_stream(argv[1]);json job;input_stream>>job;need(bool(input_stream),"job read");
        output=argv[2];need(!fs::exists(output),"fresh native output required");fs::create_directories(output/"blobs");owns=true;
        const auto limits=job.at("budget");budget.max_contexts=limits.at("contexts");budget.max_calls=limits.at("native_calls");budget.max_rows=limits.at("target_rows");
        Store store{output/"blobs",0,job.at("raw_byte_limit").get<uint64_t>(),{}};
        const std::string backend=job.at("backend");need(backend=="cpu"||backend=="cuda","backend");
        ggml_backend_load_all_from_path(job.at("lib_dir").get<std::string>().c_str());llama_backend_init();
        ggml_backend_dev_t gpu=nullptr;size_t gpu_count=0;
        for(size_t i=0;i<ggml_backend_dev_count();++i) {
            auto d=ggml_backend_dev_get(i);if(ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_GPU)continue;
            ++gpu_count;gpu=d;
        }
        if(backend=="cpu")need(gpu_count==0,"CPU binding unexpectedly loaded a GPU backend");
        else {
            need(gpu_count==1,"CUDA requires exactly one visible GPU");
            need(std::string(ggml_backend_reg_name(ggml_backend_dev_backend_reg(gpu)))=="CUDA","selected GPU is not CUDA");
        }
        auto mp=llama_model_default_params();ggml_backend_dev_t devices[]={gpu,nullptr};
        mp.n_gpu_layers=backend=="cuda"?999:0;mp.split_mode=LLAMA_SPLIT_MODE_NONE;if(gpu)mp.devices=devices;
        std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(job.at("model").get<std::string>().c_str(),mp),llama_model_free);
        need(bool(model),"model load");if(gpu)for(int layer=0;layer<=llama_model_n_layer(model.get());++layer)need(model->dev_layer(layer)==gpu,"model layer/output not wholly on selected GPU");
        result["native_modules_before"]=native_modules(job.at("lib_dir").get<std::string>(),job.at("expected_native_libraries"));
        const int vocab=llama_vocab_n_tokens(llama_model_get_vocab(model.get()));
        if(job.contains("expected_vocab"))need(vocab==job.at("expected_vocab").get<int>(),"model vocabulary differs from bound input profile");
        result["backend"]=backend;result["vocab"]=vocab;result["GPU_kernel_execution_scope"]=backend=="cpu"?"NOT_RUN":"LOCAL_TARGET_OPERATION_ONLY";
        result["reference"]= "same newly loaded backend/model, fixed LOCAL producer, q1 outer calls, identical n_ubatch32; not the historical paper R";
        result["timing_window"]="instrumented matched LOCAL operation: schedule/batch construction, original planning and native counters, decode synchronization, and owned full-logit-row materialization; budget JSON accounting, prefill, state capture, comparison, file IO, continuation, draft and sampling are outside";
        result["timing_state_condition"]="initial state was exported before the measured window; warm mode also exports reset state. This capture-conditioned operation is not a clean service or steady-state latency.";
        phase_lowering="LOCAL";phase_target_reserve=8;
        const int threads=job.at("threads");need(threads>=1&&threads<=2,"thread budget");
        const auto cases=job.at("cases");const auto qs=job.at("q_values").get<std::vector<int>>();
        need(cases.size()>=1&&cases.size()<=2&&!qs.empty()&&qs.size()<=8,"input scope");
        for(const auto & c:cases) {
            auto history=c.at("history").get<std::vector<int>>();auto tokens=c.at("rows").get<std::vector<int>>();
            need(!history.empty()&&history.size()<=512&&tokens.size()==8,"token history scope");
            for(auto group:{history,tokens,std::vector<int>{c.at("continuation").get<int>()}})for(int token:group)need(token>=0&&token<vocab,"token outside model vocabulary");
            for(int q:qs)need(q>=1&&q<=8,"q scope");
        }
        dump(output/"RESULT.json",result);
        std::map<std::string,Capture> qualified;
        for(size_t ci=0;ci<cases.size();++ci)for(int q:qs) {
            const auto key=std::to_string(ci)+"/"+std::to_string(q);auto plans=schedules(q);
            auto reference=run(model.get(),budget,cases[ci],q,plans.front(),"qualification",false,threads,store);
            json cell={{"case",cases[ci].at("name")},{"q",q},{"reference",row(reference,plans.front())},{"candidates",json::array()}};
            for(size_t arm=1;arm<plans.size();++arm) {
                auto candidate=run(model.get(),budget,cases[ci],q,plans[arm],"qualification",false,threads,store);
                auto comp=comparison(reference,candidate);auto record=row(candidate,plans[arm]);record["comparison"]=comp;record["qualified"]=passed(comp);cell["candidates"].push_back(record);
                if(!passed(comp)) {
                    cell["status"]="UNQUALIFIED";result["qualification"].push_back(cell);result["status"]="QUALIFICATION_FAILED";
                    result["timing_started"]=false;result["work"]=budget.value();result["raw_bytes"]=store.bytes;
                    result["native_modules_after"]=native_modules(job.at("lib_dir").get<std::string>(),job.at("expected_native_libraries"));
                    dump(output/"RESULT.json",result);return 3;
                }
            }
            cell["status"]="PASS";result["qualification"].push_back(cell);qualified.emplace(key,std::move(reference));result["work"]=budget.value();dump(output/"RESULT.json",result);
        }
        const int repeats=job.at("repeats");need(repeats==2,"fixed repeat budget");result["timing_started"]=true;
        for(const std::string mode:{"first_after_fresh_context","one_shape_warmup_then_reset"})for(int repeat=0;repeat<repeats;++repeat) {
            for(size_t ci=0;ci<cases.size();++ci)for(int q:qs) {
                auto plans=schedules(q);if(repeat%2)std::reverse(plans.begin(),plans.end());
                const auto & reference=qualified.at(std::to_string(ci)+"/"+std::to_string(q));
                for(const auto & plan:plans) {
                    auto candidate=run(model.get(),budget,cases[ci],q,plan,"measurement/"+mode,mode=="one_shape_warmup_then_reset",threads,store);
                    auto comp=comparison(reference,candidate);auto record=row(candidate,plan);
                    record["case"]=cases[ci].at("name");record["q"]=q;record["mode"]=mode;record["repeat"]=repeat;record["comparison"]=comp;
                    record["operation_seconds"]=candidate.operation_s;record["qualified"]=passed(comp);
                    result["measurements"].push_back(record);result["work"]=budget.value();result["raw_bytes"]=store.bytes;
                    if(!passed(comp)){result["status"]="MEASUREMENT_QUALIFICATION_FAILED";dump(output/"RESULT.json",result);return 4;}
                    dump(output/"RESULT.json",result);
                }
            }
        }
        result["status"]="PASS";result["work"]=budget.value();result["raw_bytes"]=store.bytes;result["raw_unique_blobs"]=store.written.size();
        result["CPU_timing_is_GPU_evidence"]=false;result["native_modules_after"]=native_modules(job.at("lib_dir").get<std::string>(),job.at("expected_native_libraries"));dump(output/"RESULT.json",result);
        std::cout<<json({{"status","PASS"},{"work",budget.value()},{"raw_bytes",store.bytes},{"backend",backend},{"historical_GPU_reference_qualification","NOT_ESTABLISHED"}}).dump()<<'\n';return 0;
    } catch(const std::exception & e) {
        result["status"]="FAILED";result["error"]=e.what();result["work"]=budget.value();if(owns)dump(output/"RESULT.json",result);std::cerr<<e.what()<<'\n';return 2;
    }
}
