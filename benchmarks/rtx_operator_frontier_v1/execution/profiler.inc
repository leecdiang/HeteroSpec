#ifdef FRONTIER_PROFILE
#define NOMINMAX
#include <windows.h>
#include <cupti_activity.h>
#include <mutex>
namespace profile {
static decltype(&cuptiActivityGetNextRecord) next_record;
static decltype(&cuptiActivityFlushAll) flush;
static decltype(&cuptiGetTimestamp) timestamp;
static uint64_t begin_time;
static json events=json::array();
static std::mutex mutex;
static void CUPTIAPI allocate(uint8_t** p,size_t* n,size_t* max){
    *n=4*1024*1024;*p=(uint8_t*)_aligned_malloc(*n,8);*max=0;
}
static void CUPTIAPI consume(CUcontext,uint32_t,uint8_t* buf,size_t,size_t valid){
    std::lock_guard<std::mutex> lock(mutex);
    CUpti_Activity* rec=nullptr;
    while(next_record(buf,valid,&rec)==CUPTI_SUCCESS){
        if(rec->kind==CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL){
            auto*k=(CUpti_ActivityKernel9*)rec;
            if(begin_time && k->start>=begin_time)events.push_back({{"kind","kernel"},{"name",k->name},{"start",k->start},{"end",k->end},{"grid",{k->gridX,k->gridY,k->gridZ}},{"block",{k->blockX,k->blockY,k->blockZ}}});
        }else if(rec->kind==CUPTI_ACTIVITY_KIND_MEMCPY){
            auto*m=(CUpti_ActivityMemcpy6*)rec;
            if(begin_time && m->start>=begin_time)events.push_back({{"kind","copy"},{"bytes",m->bytes},{"direction",m->copyKind},{"start",m->start},{"end",m->end}});
        }
    }
    _aligned_free(buf);
}
static void init(){
    auto lib=LoadLibraryW(L"E:/rtx170/profiler/sdk/nvidia/cuda_cupti/bin/cupti64_2025.2.1.dll");check(lib,"CUPTI DLL");
    next_record=(decltype(next_record))GetProcAddress(lib,"cuptiActivityGetNextRecord");
    flush=(decltype(flush))GetProcAddress(lib,"cuptiActivityFlushAll");
    timestamp=(decltype(timestamp))GetProcAddress(lib,"cuptiGetTimestamp");
    auto reg=(decltype(&cuptiActivityRegisterCallbacks))GetProcAddress(lib,"cuptiActivityRegisterCallbacks");
    auto enable=(decltype(&cuptiActivityEnable))GetProcAddress(lib,"cuptiActivityEnable");
    check(next_record && flush && timestamp && reg && enable,"CUPTI functions");
    check(reg(allocate,consume)==CUPTI_SUCCESS,"CUPTI registration");
    for(auto k:{CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL,CUPTI_ACTIVITY_KIND_MEMCPY}){
        auto rc=enable(k);if(rc!=CUPTI_SUCCESS)throw std::runtime_error("CUPTI activity enable "+std::to_string(int(rc)));
    }
}
static void begin(){flush(0);std::lock_guard<std::mutex> lock(mutex);events=json::array();check(timestamp(&begin_time)==CUPTI_SUCCESS,"CUPTI timestamp");}
static void end(const fs::path&p){check(flush(1)==CUPTI_SUCCESS,"CUPTI flush");std::lock_guard<std::mutex> lock(mutex);begin_time=0;save(p,events);}
}
#else
namespace profile {static void init(){}static void begin(){}static void end(const fs::path&){}}
#endif

