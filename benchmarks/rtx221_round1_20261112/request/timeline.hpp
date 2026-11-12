#pragma once
// Host-wall instrumentation only. No CUDA timestamp is admitted here.
// Call finish() at the actual service endpoint including reset, guards and
// reconciliation. Persist the same-request record outside that endpoint.
#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
namespace hs_request_timeline {
inline int64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}
struct Event {std::string category;int64_t begin,end;};
struct Recorder {
    int64_t begin=now_ns(),end=0;std::vector<Event> spans;
    void finish(){if(end)throw std::runtime_error("duplicate service endpoint");end=now_ns();}
};
struct Span {
    Recorder* recorder;std::string category;int64_t begin;bool ended=false;
    Span(Recorder* r,const char* c):recorder(r),category(c),begin(now_ns()){}
    Span(const Span&)=delete;Span& operator=(const Span&)=delete;
    void finish(){if(!ended){ended=true;if(recorder)recorder->spans.push_back({category,begin,now_ns()});}}
    ~Span(){finish();}
};
} // namespace hs_request_timeline
