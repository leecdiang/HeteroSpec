"""Generate additive native evidence/timeline hooks; never execute a model."""
from pathlib import Path
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "request/prepared_frontend"
OUT = HERE / "hooked_frontend_v7"


def once(s, old, new):
    if s.count(old) != 1:
        raise ValueError("source anchor count: " + old[:100])
    return s.replace(old, new, 1)


def wrap_method(s, signature, prefix, suffix):
    start = s.index(signature)
    left = s.index("{", start)
    depth = 1
    i = left + 1
    quote = None
    escape = False
    while depth:
        c = s[i]
        if quote:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
        elif c in ('"', "'"):
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    return s[:left + 1] + prefix + s[left + 1:i - 1] + suffix + s[i - 1:]


HOOKS = r'''#pragma once
#include <exception>
#include <cstdint>
#include <iterator>
namespace hs_round1 {
inline int64_t ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
struct Recorder {
    int64_t begin=ns(),end=0;json spans=json::array();bool valid=true;
    void finish(){need(end==0&&valid,"timeline invalid or duplicate endpoint");end=ns();need(end>begin,"timeline endpoint ordering");}
};
inline thread_local Recorder* active=nullptr;
struct Span {
    Recorder* r;std::string category;int64_t begin;bool ended=false;
    explicit Span(const char* c):r(active),category(c),begin(ns()){}
    void finish(){if(ended)return;ended=true;if(r){try{r->spans.push_back({{"category",category},{"begin",begin},{"end",ns()},{"clock","steady_clock_ns"},{"lane","host_critical"}});}catch(...){r->valid=false;throw;}}}
    ~Span(){if(!ended)try{finish();}catch(...){if(r)r->valid=false;}}
};
struct ActiveRecorder {
    Recorder* previous;explicit ActiveRecorder(Recorder&r):previous(active){need(!previous,"nested request recorder");active=&r;}
    ~ActiveRecorder(){active=previous;}
};
inline uint64_t next_owner=0;
struct OwnerStatus {
    uint64_t id=++next_owner,generation=0;bool invalid=false;
    void check()const{need(!invalid,"invalidated request owner cannot be reused");}
    void reset_generation(){check();++generation;}
    void poison()noexcept{invalid=true;}
};
inline int selftest(const fs::path& fixture={}){
    OwnerStatus status;status.reset_generation();need(status.generation==1,"owner generation selftest");
    status.poison();bool refused=false;try{status.check();}catch(const std::exception&){refused=true;}need(refused,"owner poison selftest");
    const auto old_limit=tpds_decisive::capture_byte_limit,old_reserved=tpds_decisive::capture_bytes_reserved,old_written=tpds_decisive::capture_bytes_written;
    tpds_decisive::capture_byte_limit=8;tpds_decisive::capture_bytes_reserved=0;
    tpds_decisive::reserve_capture_bytes(8);bool byte_refused=false;try{tpds_decisive::reserve_capture_bytes(1);}catch(const std::exception&){byte_refused=true;}
    need(byte_refused&&tpds_decisive::capture_bytes_reserved==8,"capture ceiling boundary selftest");
    tpds_decisive::capture_byte_limit=old_limit;tpds_decisive::capture_bytes_reserved=old_reserved;tpds_decisive::capture_bytes_written=old_written;
    Recorder r;{ActiveRecorder a(r);{Span reset("reset");}{Span guard("guard");}{Span verify("verify");{Span sync("sync");}}r.finish();}
    need(r.end>r.begin&&r.spans.size()==4,"timeline selftest");
    bool json_file_checked=false;size_t json_file_bytes=0;
    if(!fixture.empty()){
        need(!fs::exists(fixture)&&fs::exists(fixture.parent_path()),"fresh JSON selftest path required");
        const json value={{"multiline",json::array({1,2,3})},{"utf8","\xE7\x8A\xB6\xE6\x80\x81\xE6\x8D\x95\xE8\x8E\xB7"},{"nested",{{"key","value"}}}};
        const auto encoded=value.dump(2)+"\n";
        const auto prior_limit=tpds_decisive::capture_byte_limit,prior_reserved=tpds_decisive::capture_bytes_reserved,prior_written=tpds_decisive::capture_bytes_written;
        tpds_decisive::capture_byte_limit=encoded.size();tpds_decisive::capture_bytes_reserved=0;tpds_decisive::capture_bytes_written=0;
        ::dump(fixture,value);
        std::ifstream input(fixture,std::ios::binary);need(bool(input),"JSON selftest binary reread");
        const std::string actual((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
        need(actual==encoded,"JSON output bytes differ from reserved UTF8 encoding");
        need(fs::file_size(fixture)==encoded.size()&&tpds_decisive::capture_bytes_reserved==encoded.size()&&tpds_decisive::capture_bytes_written==encoded.size(),"JSON physical/reserved/written byte equality");
        bool extra_refused=false;try{tpds_decisive::reserve_capture_bytes(1);}catch(const std::exception&){extra_refused=true;}
        need(extra_refused&&tpds_decisive::capture_bytes_reserved==encoded.size(),"JSON exact-limit extra-byte rejection");
        json_file_checked=true;json_file_bytes=encoded.size();
        tpds_decisive::capture_byte_limit=prior_limit;tpds_decisive::capture_bytes_reserved=prior_reserved;tpds_decisive::capture_bytes_written=prior_written;
    }
    std::cout<<json({{"status","PASS_HOST_SELFTEST_ONLY"},{"owner_poison",true},{"capture_ceiling_boundary",true},{"timeline_nested_spans",r.spans.size()},{"multiline_UTF8_JSON_file_checked",json_file_checked},{"multiline_UTF8_JSON_bytes",json_file_bytes},{"models",0},{"backend_initializations",0},{"CUDA_calls",0}}).dump()<<std::endl;
    return 0;
}
}
inline void hs_round1_sync(llama_context*c){hs_round1::Span span("sync");llama_synchronize(c);}
'''

CAPTURE = r'''
    void native_snapshot(const std::string& key) {
        status.check();if(!capture)return;
        hs_round1::Span state_span("state");++phase_heavy_captures;
        hs_round1_sync(c);
        auto* cache=dynamic_cast<llama_kv_cache*>(llama_get_memory(c));need(cache,"state capture dense cache required");
        need(cache->type_k()==GGML_TYPE_F16&&cache->type_v()==GGML_TYPE_F16,"state capture F16 recipe required");
        const auto& cells=cache->get_cells(0);need(!cells.get_has_shift(),"state capture shifted cache unsupported");
        const uint32_t used=cells.get_used();need(used==cells.used_max_p1(),"state capture requires dense nonwrapping cells");
        json positions=json::array(),sequences=json::array();
        for(uint32_t i=0;i<used;++i){need(i<cells.size()&&!cells.is_empty(i),"state capture cell gap");need(cells.pos_get(i)==int(i),"state capture position mapping");need(cells.seq_count(i)==1&&cells.seq_has(i,0),"state capture sequence ownership");positions.push_back(cells.pos_get(i));sequences.push_back(0);}
        const auto append=used<cells.size()?cache->phase_append_requirements(used,1):std::vector<uint32_t>{};
        const auto n=llama_state_seq_get_size(c,0);need(n>0,"native sequence state unavailable");
        std::vector<uint8_t> bytes(n);need(llama_state_seq_get_data(c,bytes.data(),bytes.size(),0)==n,"incomplete native sequence export");
        const auto dir=path/"state"/key;need(!fs::exists(dir),"state capture output collision");fs::create_directories(dir);
        tpds_decisive::capture_write_new(dir/"sequence.bin",bytes.data(),bytes.size());
        json geometry={{"capacity",cells.size()},{"active_positions",used},{"physical_used",cells.get_used()},{"used_max_p1",cells.used_max_p1()},{"positions",positions},{"sequence_ids",sequences},{"has_shift",cells.get_has_shift()},{"attention_extent",cache->phase_current_extent()},{"append_probe_extents",append},{"physical_head",append.size()==1?json(used):json(nullptr)},{"physical_head_basis",append.size()==1?"native phase_append_requirements verifies v_heads[0]==used":"not observable: append preflight unavailable"}};
        json record={{"schema","heterospec.native-state-stage.v2"},{"stage",key},{"role",target?"target":"draft"},{"owner_id",status.id},{"generation",status.generation},{"owner_invalid",status.invalid},{"geometry",geometry},{"sequence_bytes",bytes.size()},{"sequence_sha256",hash_file(dir/"sequence.bin")},{"sequence_payload","raw_native_sequence"},{"independent_active_KV_parse_required",true},{"capture_only_not_clean_guard",true}};
        dump(dir/"metadata.json",record);state_captures.push_back(record);
    }
    void capture_requested(const std::vector<int>&ids,int pos,bool all,const char*phase){
        status.check();if(!capture)return;
        hs_round1::Span state_span("state");++phase_heavy_captures;
        const int vocab=llama_vocab_n_tokens(llama_model_get_vocab(model));need(vocab>0,"vocabulary capture");
        const auto call=++capture_calls;const auto dir=path/"requested"/std::to_string(call);need(!fs::exists(dir),"requested capture collision");fs::create_directories(dir);
        for(size_t row=0;row<ids.size();++row){if(!all&&row+1!=ids.size())continue;
            const float*p=target?plan.logits(int(row)):llama_get_logits_ith(c,all?int(row):-1);need(p,"requested full row unavailable");
            std::vector<float> owned(p,p+vocab);for(float value:owned)need(std::isfinite(value),"requested full row nonfinite");
            const auto file=dir/(std::to_string(row)+".f32");tpds_decisive::capture_write_new(file,owned.data(),owned.size()*sizeof(float));
            requested_captures.push_back({{"owner_id",status.id},{"generation",status.generation},{"call",call},{"phase",phase},{"position",pos+int(row)},{"caller_row",row},{"caller_rows",ids.size()},{"all_outputs",all},{"vocab",vocab},{"bytes",owned.size()*sizeof(float)},{"sha256",hash_file(file)},{"path",fs::relative(file,path).generic_string()},{"owned_copy",true}});
        }
    }
'''

POISON = r'''
struct Round1Transaction {
    Context*&target;Context*&draft;Pair&resident;bool complete=false;
    ~Round1Transaction(){if(!complete){if(target)target->status.poison();if(draft)draft->status.poison();if(resident.target)resident.target->status.poison();if(resident.draft)resident.draft->status.poison();}}
};
'''


def prepare():
    if OUT.exists():
        raise FileExistsError("new output required")
    shutil.copytree(SOURCE, OUT)
    s = (OUT / "worker.cpp").read_text(encoding="utf8")
    s = once(s, 'inline bool phase_observe=false;', '#include "hs_round1_hooks.hpp"\ninline bool phase_observe=false;')
    s = once(s, '#include "hs_round1_hooks.hpp"', '#include "hs_round1_hooks.hpp"\n#include "capture_operand.hpp"')
    s = once(s, 'auto&o=*static_cast<Observer*>(opaque);if(!phase_observe)return false;', 'auto&o=*static_cast<Observer*>(opaque);if(auto decision=hs_q8_capture::callback(t,ask,o.phase,o.base,o.caller))return *decision;if(!phase_observe)return false;')
    s = once(s, '    PhaseContext plan;', '    PhaseContext plan;\n    hs_round1::OwnerStatus status;\n    uint64_t capture_calls=0;json requested_captures=json::array(),state_captures=json::array();')
    s = wrap_method(s, '    void reset(bool cap,const fs::path&dir)', '\n        hs_round1::Span timer("reset");status.reset_generation();capture_calls=0;requested_captures=json::array();state_captures=json::array();try{', '\n        }catch(...){status.poison();throw;}\n    ')
    s = wrap_method(s, '    void decode(const std::vector<int>&ids,int pos,bool all,const char*phase)', '\n        status.check();const std::string phase_name=phase;hs_round1::Span timer(phase_name=="PREFILL"?(target?"prefill_target":"prefill_draft"):(target?"verify":"draft"));try{', '\n        capture_requested(ids,pos,all,phase);\n        }catch(...){status.poison();throw;}\n    ')
    s = once(s, 'plan.decode(*this,ids,pos,all,phase);return;', 'plan.decode(*this,ids,pos,all,phase);capture_requested(ids,pos,all,phase);return;')
    s = wrap_method(s, '    int sample(int row,const std::string&name)', '\n        status.check();hs_round1::Span timer("sampling");try{', '\n        }catch(...){status.poison();throw;}\n    ')
    s = wrap_method(s, '    void trim(int keep)', '\n        status.check();hs_round1::Span timer("reconciliation");try{', '\n        }catch(...){status.poison();throw;}\n    ')
    old = '''    void snapshot(const std::string & key,int row) {
        if (!capture || !target) return;
        ++phase_heavy_captures;tpds_decisive::capture_existing(c,model,path/"state"/key,row,plan.logits(row));
    }'''
    new = '''    void snapshot(const std::string & key,int row) {
        status.check();if(!capture)return;native_snapshot(key);
        auto*p=target?plan.logits(row):llama_get_logits_ith(c,row);need(p,"snapshot frontier missing");
        const int n=llama_vocab_n_tokens(llama_model_get_vocab(model));tpds_decisive::capture_write_new(path/"state"/key/"frontier.f32",p,size_t(n)*sizeof(float));
    }
''' + CAPTURE
    s = once(s, old, new)
    s = once(s, 'struct Pair {std::unique_ptr<Context> target,draft;};', 'struct Pair {std::unique_ptr<Context> target,draft;};\n' + POISON)
    s = once(s, '    const auto& arm=spec.name;int k=spec.k;', '    hs_round1::Recorder timeline;hs_round1::ActiveRecorder active_recorder(timeline);hs_round1::Span initial_guard("guard");\n    const auto& arm=spec.name;int k=spec.k;')
    s = once(s, '    Pair fresh;Context*target=nullptr,*draft=nullptr;', '    Pair fresh;Context*target=nullptr,*draft=nullptr;Round1Transaction transaction{target,draft,resident};initial_guard.finish();')
    s = once(s, '    if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft width differs");', '    {hs_round1::Span guard("guard");if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft width differs");}\n    need(!capture||phase_proposal_mode=="live","complete state capture requires native live draft");')
    s = once(s, '    if(capture)target->snapshot("initial",-1);', '    if(capture){target->snapshot("initial",-1);if(draft)draft->native_snapshot("initial");}')
    s = once(s, '        std::vector<int> verify={seed};verify.insert(verify.end(),proposals.begin(),proposals.end());', '        if(capture){target->native_snapshot("before-verify-"+std::to_string(cycle));draft->native_snapshot("untrimmed-"+std::to_string(cycle));}\n        std::vector<int> verify={seed};verify.insert(verify.end(),proposals.begin(),proposals.end());')
    s = once(s, '        target->decode(verify,base,true,"VERIFY");', '        target->decode(verify,base,true,"VERIFY");\n        if(capture)target->native_snapshot("untrimmed-"+std::to_string(cycle));')
    s = once(s, '        int accepted=0;bool rejected=false;std::string last;', '        hs_round1::Span reconcile("reconciliation");\n        int accepted=0;bool rejected=false;std::string last;')
    s = once(s, '        final_frontier=accepted;if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);', '        final_frontier=accepted;if(capture){target->snapshot("commit-"+std::to_string(cycle),accepted);draft->native_snapshot("commit-"+std::to_string(cycle));}reconcile.finish();')
    s = once(s, '    r["ids"]=ids;', '    if(capture){target->native_snapshot("terminal");if(draft)draft->native_snapshot("terminal");}\n    r["ids"]=ids;')
    s = once(s, '    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;', '    r["requested_vector_captures"]={{"target",target->requested_captures},{"draft",draft?draft->requested_captures:json::array()}};\n    r["native_state_captures"]={{"target",target->state_captures},{"draft",draft?draft->state_captures:json::array()}};\n    r["output_owner"]={{"target_owner",target->status.id},{"target_generation",target->status.generation},{"target_invalid",target->status.invalid},{"draft_owner",draft?json(draft->status.id):json(nullptr)},{"draft_generation",draft?json(draft->status.generation):json(nullptr)},{"draft_invalid",draft?json(draft->status.invalid):json(nullptr)}};\n    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;')
    s = once(s, '    r["teardown_seconds"]=since(teardown);', '    r["teardown_seconds"]=since(teardown);if(life=="fresh"){target=nullptr;draft=nullptr;}')
    s = once(s, 'auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;', 'auto teardown=Clock::now();if(life=="fresh"){target=nullptr;draft=nullptr;}fresh.draft.reset();fresh.target.reset();hs_scope::active=false;')
    s = once(s, 'if(capture){++phase_heavy_captures;std::ofstream f(path/(name+".f32"),std::ios::binary);f.write((char*)p,size_t(n)*sizeof(float));need(bool(f),"full logits write");}', 'if(capture){++phase_heavy_captures;tpds_decisive::capture_write_new(path/(name+".f32"),p,size_t(n)*sizeof(float));}')
    s = once(s, r'''static void dump(const fs::path&p,const json&j){auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp);f<<j.dump(2)<<'\n';f.flush();need(bool(f),"write JSON");}''', r'''static void dump(const fs::path&p,const json&j){const auto encoded=j.dump(2)+"\n";tpds_decisive::reserve_capture_bytes(encoded.size());auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp,std::ios::binary);f<<encoded;f.flush();need(bool(f),"write JSON");tpds_decisive::capture_bytes_written+=encoded.size();}''')
    s = once(s, '    return r;\n}', '    timeline.finish();r["service_timeline"]={{"clock","steady_clock_ns"},{"service",{timeline.begin,timeline.end}},{"spans",timeline.spans},{"endpoint_qualification","UNVERIFIED_REQUIRES_INDEPENDENT_SOURCE_ENDPOINT_AUDIT"},{"state_capture_enabled",capture},{"fallback_work",0},{"fallback_basis","this executor rejects unsupported work; no fallback implemented"}};transaction.complete=true;\n    return r;\n}')
    s = s.replace('llama_synchronize(', 'hs_round1_sync(')
    (OUT / "worker.cpp").write_text(s, encoding="utf8", newline="\n")
    r = (OUT / "resident_context.hpp").read_text(encoding="utf8")
    r = once(r, '        auto began=Clock::now();', '        hs_round1::Span planning("planning");\n        auto began=Clock::now();')
    r = once(r, '        outputs.assign(ids.size(),{});', '        planning.finish();\n        outputs.assign(ids.size(),{});')
    r = r.replace('llama_synchronize(', 'hs_round1_sync(')
    (OUT / "resident_context.hpp").write_text(r, encoding="utf8", newline="\n")
    e = (OUT / "entry.cpp").read_text(encoding="utf8")
    e = once(e, 'int main(int argc,char**argv){', 'int main(int argc,char**argv){\n    if(argc==2&&std::string(argv[1])=="--selftest")return hs_round1::selftest();')
    e = once(e, '    if(argc==2&&std::string(argv[1])=="--selftest")return hs_round1::selftest();', '    if(argc==2&&std::string(argv[1])=="--selftest")return hs_round1::selftest();\n    if(argc==3&&std::string(argv[1])=="--selftest-json")return hs_round1::selftest(fs::path(argv[2]));')
    e = once(e, 'need(EnumProcessModules(GetCurrentProcess(),modules,sizeof(modules),&bytes),"module inventory");', 'need(EnumProcessModules(GetCurrentProcess(),modules,sizeof(modules),&bytes)&&bytes<=sizeof(modules),"module inventory bounded");')
    e = once(e, 'static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){', '''static json module_disk_inventory(){
    const auto paths=module_inventory();json files=json::array();
    for(const auto& item:paths){const fs::path path=item.get<std::string>();files.push_back({{"path",path.string()},{"bytes",fs::file_size(path)},{"sha256",hash_file(path)},{"basis","loaded module path, disk hash not memory"}});}
    return files;
}
static void observe_state(Context& c,const fs::path& dir,int row,bool state=true){''')
    e = once(e, '        m1_capability(job,pool,t,d,spec,root,result);', '''        m1_capability(job,pool,t,d,spec,root,result);
        result["modules_disk_before"]=module_disk_inventory();
        result["executable_disk_sha256"]=hash_file(exe);
        result["models_disk"]={{"target",{{"path",job.at("target_model")},{"sha256",hash_file(job.at("target_model").get<std::string>())}}},{"draft",target_only?json(nullptr):json({{"path",job.at("draft_model")},{"sha256",hash_file(job.at("draft_model").get<std::string>())}})}};''')
    e = once(e, '        phase_target_reserve=job.at("target_output_reserve");', '''        std::unique_ptr<hs_q8_capture::Capture> actual_q8_capture;
        struct ClearCapture {~ClearCapture(){hs_q8_capture::active=nullptr;}} clear_capture;
        if(job.contains("actual_q8_capture")){actual_q8_capture=std::make_unique<hs_q8_capture::Capture>(hs_q8_capture::json(job.at("actual_q8_capture")));hs_q8_capture::active=actual_q8_capture.get();}
        phase_target_reserve=job.at("target_output_reserve");''')
    e = once(e, '        std::unique_ptr<hs_q8_capture::Capture> actual_q8_capture;', '''        const auto capture_limit=job.at("evidence_capture_byte_reservation").get<uint64_t>();
        need(capture_limit>0&&capture_limit<=2147483648ULL,"bounded capture reservation required before backend/model initialization");
        need(!job.value("profile",false),"profiling not admitted by evidence-byte writer");
        tpds_decisive::capture_byte_limit=capture_limit;
        std::unique_ptr<hs_q8_capture::Capture> actual_q8_capture;''')
    e = once(e, '        result["total_observed_API_calls"]=', '        if(actual_q8_capture)actual_q8_capture->require_complete();\n        result["total_observed_API_calls"]=')
    e = once(e, 'result["modules_after"]=module_inventory();', 'result["modules_after"]=module_inventory();result["modules_disk_after"]=module_disk_inventory();result["evidence_bytes_before_final_receipt"]={{"limit",tpds_decisive::capture_byte_limit},{"reserved_no_refund",tpds_decisive::capture_bytes_reserved},{"written",tpds_decisive::capture_bytes_written},{"counting","all instrumented binary and JSON writes; includes repeated atomic JSON replacements; stdout excluded and externally bounded"}};')
    e = once(e, '                if(capture){const int row=r["cycles"].empty()?-1:r["cycles"].back().at("accepted").get<int>();observe_state(*pool.target,dir/"target/state/terminal",row);}', '                // Terminal state is captured within request() for both owners and is included in the measured endpoint.')
    e = once(e, 'dump(root/"failure.json",{{"error",e.what()}});', 'dump(root/"failure.json",{{"error",e.what()},{"target_owner_invalid",pool.target?json(pool.target->status.invalid):json(nullptr)},{"draft_owner_invalid",pool.draft?json(pool.draft->status.invalid):json(nullptr)}});')
    (OUT / "entry.cpp").write_text(e, encoding="utf8", newline="\n")
    (OUT / "hs_round1_hooks.hpp").write_text(HOOKS, encoding="utf8", newline="\n")
    capture_source=HERE.parents[0]/"native/capture_operand.hpp"
    shutil.copy2(capture_source,OUT/"capture_operand.hpp")
    t=(OUT/"target_capture.hpp").read_text(encoding="utf8")
    t=once(t,'namespace tpds_decisive {',r'''namespace tpds_decisive {
inline uint64_t capture_byte_limit=0,capture_bytes_reserved=0,capture_bytes_written=0;
inline void ensure_capture_capacity(uint64_t n){if(!capture_byte_limit||capture_bytes_reserved>capture_byte_limit||n>capture_byte_limit-capture_bytes_reserved)throw std::runtime_error("evidence capture byte ceiling exceeded");}
inline void reserve_capture_bytes(uint64_t n){ensure_capture_capacity(n);capture_bytes_reserved+=n;}
''')
    t=once(t,'    std::ofstream f(p,std::ios::binary|std::ios::out);','    reserve_capture_bytes(n);\n    std::ofstream f(p,std::ios::binary|std::ios::out);')
    t=once(t,'    if(!f)throw std::runtime_error("capture write failed");','    if(!f)throw std::runtime_error("capture write failed");\n    capture_bytes_written+=n;')
    t=once(t,'#include <limits>','#include <limits>\n#include <sstream>')
    t=once(t,'    std::ofstream meta(dir/"capture.txt");','    std::ostringstream meta;')
    t=once(t,'    meta.flush();if(!meta)throw std::runtime_error("capture metadata write");','    const auto encoded=meta.str();capture_write_new(dir/"capture.txt",encoded.data(),encoded.size());')
    (OUT/"target_capture.hpp").write_text(t,encoding="utf8",newline="\n")
    c=(OUT/"capture_operand.hpp").read_text(encoding="utf8")
    c=once(c,'    HANDLE file = CreateFileW(', '    tpds_decisive::reserve_capture_bytes(bytes);\n    HANDLE file = CreateFileW(')
    c=once(c,'    need(okay, "capture write incomplete");','    need(okay, "capture write incomplete");\n    tpds_decisive::capture_bytes_written+=bytes;')
    c=once(c,'            std::vector<char> weights(wb), input(xb), output(yb);','            tpds_decisive::ensure_capture_capacity(wb+xb+yb+metadata_margin);\n            std::vector<char> weights(wb), input(xb), output(yb);')
    (OUT/"capture_operand.hpp").write_text(c,encoding="utf8",newline="\n")
    result = {"schema": "heterospec.native-evidence-hook-source.v2", "status": "SOURCE_GENERATED_NOT_BUILT_NOT_NATIVE_QUALIFIED", "source": str(SOURCE), "output": str(OUT), "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}, "models": 0, "GPU_launches": 0, "limitations": ["Geometry stage schema v2 needs independently frozen reader adaptation", "native phase append guard establishes head equality only when its one-row probe succeeds", "no numerical correctness or performance result", "clean actual-dispatch guards are not supplied by capture observer", "complete endpoint admission still requires external independent source audit", "C runtime kernel not integrated here"]}
    (HERE / "HOOK_SOURCE_v7.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    prepare()
