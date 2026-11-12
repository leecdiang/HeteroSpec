#pragma once
#include <exception>
#include <cstdint>
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
inline int selftest(){
    OwnerStatus status;status.reset_generation();need(status.generation==1,"owner generation selftest");
    status.poison();bool refused=false;try{status.check();}catch(const std::exception&){refused=true;}need(refused,"owner poison selftest");
    const auto old_limit=tpds_decisive::capture_byte_limit,old_reserved=tpds_decisive::capture_bytes_reserved,old_written=tpds_decisive::capture_bytes_written;
    tpds_decisive::capture_byte_limit=8;tpds_decisive::capture_bytes_reserved=0;
    tpds_decisive::reserve_capture_bytes(8);bool byte_refused=false;try{tpds_decisive::reserve_capture_bytes(1);}catch(const std::exception&){byte_refused=true;}
    need(byte_refused&&tpds_decisive::capture_bytes_reserved==8,"capture ceiling boundary selftest");
    tpds_decisive::capture_byte_limit=old_limit;tpds_decisive::capture_bytes_reserved=old_reserved;tpds_decisive::capture_bytes_written=old_written;
    Recorder r;{ActiveRecorder a(r);{Span reset("reset");}{Span guard("guard");}{Span verify("verify");{Span sync("sync");}}r.finish();}
    need(r.end>r.begin&&r.spans.size()==4,"timeline selftest");
    std::cout<<json({{"status","PASS_HOST_SELFTEST_ONLY"},{"owner_poison",true},{"capture_ceiling_boundary",true},{"timeline_nested_spans",r.spans.size()},{"models",0},{"backend_initializations",0},{"CUDA_calls",0}}).dump()<<std::endl;
    return 0;
}
}
inline void hs_round1_sync(llama_context*c){hs_round1::Span span("sync");llama_synchronize(c);}
