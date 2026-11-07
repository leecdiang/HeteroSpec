#pragma once
#include <windows.h>
#include <cstdint>
#include <vector>
#include <stdexcept>
namespace s1b {
inline void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
struct Clock {
    int64_t frequency;
    Clock(){LARGE_INTEGER f{};need(QueryPerformanceFrequency(&f)&&f.QuadPart>0,"invalid QPC frequency");frequency=f.QuadPart;}
    int64_t now(){LARGE_INTEGER t{};need(QueryPerformanceCounter(&t)!=0,"QPC read failed");return t.QuadPart;}
};
struct Interval {int index;bool warmup;int64_t begin,compute_return,sync_return,readback_return,audit_return;};
// Same loop is instantiated by actual CUDA Ops and explicitly synthetic CPU Ops.
// No filesystem, readback, validation or profiler call occurs between begin and
// sync_return. F and G partition one inclusive completed graph interval exactly.
template<class C,class O> std::vector<Interval> loop(C&clock,O&ops,int measured,std::vector<Interval>*partial=nullptr){
    need(clock.frequency>0,"invalid timer units");need(measured==8||measured==1,"unregistered loop length");
    std::vector<Interval> rows;
    for(int i=0;i<measured+1;i++){
        ops.before(i);auto a=clock.now();auto rc=ops.compute();auto b=clock.now();
        auto sync=ops.sync();auto c=clock.now();
        if(partial)partial->push_back({i,i==0,a,b,c,0,0});
        need(a<=b&&b<=c&&c>a,"nonmonotonic/zero completed interval");
        need(rc==0&&sync==0,"graph call or all-stream completion failed");
        ops.readback(i);auto d=clock.now();if(partial)partial->back().readback_return=d;need(d>=c,"readback clock reversed");
        ops.verify(i);auto e=clock.now();if(partial)partial->back().audit_return=e;need(e>=d,"audit clock reversed");
        rows.push_back({i,i==0,a,b,c,d,e});
    }
    return rows;
}
}
