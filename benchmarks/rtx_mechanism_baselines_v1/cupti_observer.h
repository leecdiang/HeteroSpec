#pragma once
#include <cupti_callbacks.h>
#include <cupti_common.h>
// Official Windows header uses MSVC spelling. Zig's GNU-target clang uses the
// exactly corresponding packed+8-byte-alignment attribute; tool bytes untouched.
#if defined(__GNUC__) && defined(_WIN32)
#undef START_PACKED_ALIGNMENT
#undef PACKED_ALIGNMENT
#undef END_PACKED_ALIGNMENT
#define START_PACKED_ALIGNMENT
#define PACKED_ALIGNMENT __attribute__((packed,aligned(8)))
#define END_PACKED_ALIGNMENT
#endif
#include <cupti_activity.h>
#include <mutex>
#include <atomic>
// Explicit tool module, never a replacement for any numerical DLL. Only profile
// jobs enable callbacks/activity. Clean jobs neither load CUPTI nor call its APIs.
namespace trace122 {
struct Observer {
    HMODULE module=nullptr;CUpti_SubscriberHandle subscriber=nullptr;
    std::mutex mutex;std::atomic<int> call{-1};J events=J::array(),activities=J::array();bool overflow=false;size_t dropped=0;
    decltype(&cuptiSubscribe) subscribe=nullptr;decltype(&cuptiEnableDomain) enable=nullptr;decltype(&cuptiUnsubscribe) unsubscribe=nullptr;
    decltype(&cuptiActivityGetNextRecord) next=nullptr;decltype(&cuptiActivityGetNumDroppedRecords) drops=nullptr;decltype(&cuptiActivityFlushAll) flush=nullptr;
    static Observer* instance;
    static int64_t qpc(){LARGE_INTEGER v;QueryPerformanceCounter(&v);return v.QuadPart;}
    static void CUPTIAPI callback(void* user,CUpti_CallbackDomain domain,CUpti_CallbackId id,const void* info){
        auto*o=(Observer*)user;auto*d=(const CUpti_CallbackData*)info;std::lock_guard<std::mutex>lock(o->mutex);
        if(o->events.size()>=100000){o->overflow=true;return;}
        // symbolName is only valid for specific launch callbacks. Never read it
        // for arbitrary runtime/driver APIs (including device initialization).
        o->events.push_back({{"QPC",qpc()},{"call",o->call.load()},{"domain",int(domain)},{"cbid",id},{"site",int(d->callbackSite)},{"name",d->functionName?d->functionName:""},{"correlation",d->correlationId},{"status",d->callbackSite==CUPTI_API_EXIT&&d->functionReturnValue?J(*(int*)d->functionReturnValue):J(nullptr)}});
    }
    static void CUPTIAPI request(uint8_t**buffer,size_t*size,size_t*maxRecords){*size=4*1024*1024;*buffer=(uint8_t*)_aligned_malloc(*size,8);*maxRecords=0;}
    static void CUPTIAPI complete(CUcontext ctx,uint32_t stream,uint8_t*buffer,size_t size,size_t valid){
        auto*o=instance;if(!o){_aligned_free(buffer);return;}CUpti_Activity*rec=nullptr;
        while(o->next(buffer,valid,&rec)==CUPTI_SUCCESS){std::lock_guard<std::mutex>lock(o->mutex);if(o->activities.size()>=100000){o->overflow=true;break;}
            J r={{"kind",int(rec->kind)}};
            if(rec->kind==CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL){auto*k=(CUpti_ActivityKernel9*)rec;r.update({{"name",k->name?k->name:""},{"start_ns",k->start},{"end_ns",k->end},{"device",k->deviceId},{"context",k->contextId},{"stream",k->streamId},{"correlation",k->correlationId},{"graph_id",k->graphId},{"graph_node_id",k->graphNodeId}});}
            else if(rec->kind==CUPTI_ACTIVITY_KIND_MEMCPY){auto*k=(CUpti_ActivityMemcpy6*)rec;r.update({{"start_ns",k->start},{"end_ns",k->end},{"bytes",k->bytes},{"copy_kind",int(k->copyKind)},{"stream",k->streamId},{"correlation",k->correlationId}});}
            else if(rec->kind==CUPTI_ACTIVITY_KIND_RUNTIME||rec->kind==CUPTI_ACTIVITY_KIND_DRIVER){auto*k=(CUpti_ActivityAPI*)rec;r.update({{"start_ns",k->start},{"end_ns",k->end},{"cbid",k->cbid},{"correlation",k->correlationId},{"thread",k->threadId}});}
            o->activities.push_back(r);
        }
        size_t n=0;if(o->drops(ctx,stream,&n)==CUPTI_SUCCESS)o->dropped+=n;_aligned_free(buffer);
    }
    template<class T>T fn(const char*name){auto f=(T)GetProcAddress(module,name);hs113::require(f,"CUPTI exact export absent");return f;}
    void start(const fs::path&path,const std::string&sha){repair113::pin_numeric_file(path,sha);module=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);hs113::require(module&&repair113::same_path(repair113::module_path(module),path),"CUPTI module identity");instance=this;
        subscribe=fn<decltype(subscribe)>("cuptiSubscribe");enable=fn<decltype(enable)>("cuptiEnableDomain");unsubscribe=fn<decltype(unsubscribe)>("cuptiUnsubscribe");
        next=fn<decltype(next)>("cuptiActivityGetNextRecord");drops=fn<decltype(drops)>("cuptiActivityGetNumDroppedRecords");flush=fn<decltype(flush)>("cuptiActivityFlushAll");
        hs113::require(subscribe(&subscriber,callback,this)==CUPTI_SUCCESS,"CUPTI subscribe unavailable");
        hs113::require(enable(1,subscriber,CUPTI_CB_DOMAIN_RUNTIME_API)==CUPTI_SUCCESS&&enable(1,subscriber,CUPTI_CB_DOMAIN_DRIVER_API)==CUPTI_SUCCESS,"CUPTI callback domains");
        auto reg=fn<decltype(&cuptiActivityRegisterCallbacks)>("cuptiActivityRegisterCallbacks");auto activity=fn<decltype(&cuptiActivityEnable)>("cuptiActivityEnable");
        hs113::require(reg(request,complete)==CUPTI_SUCCESS,"CUPTI buffer callback");
        J admitted=J::array();for(auto kind:{CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL,CUPTI_ACTIVITY_KIND_MEMCPY,CUPTI_ACTIVITY_KIND_RUNTIME,CUPTI_ACTIVITY_KIND_DRIVER})admitted.push_back({{"kind",int(kind)},{"status",int(activity(kind))}});
        write_path=path;identity=sha;activity_status=admitted;
    }
    fs::path write_path;std::string identity;J activity_status;
    void finish(const fs::path&out){auto status=flush(0);enable(0,subscriber,CUPTI_CB_DOMAIN_RUNTIME_API);enable(0,subscriber,CUPTI_CB_DOMAIN_DRIVER_API);unsubscribe(subscriber);subscriber=nullptr;write(out/"CUDA_TRACE.json",{{"module_path",write_path.u8string()},{"module_sha256",identity},{"flush_status",int(status)},{"activity_enable",activity_status},{"dropped",dropped},{"overflow",overflow},{"API_events",events},{"activities",activities},{"external_review",false}});hs113::require(status==CUPTI_SUCCESS&&!overflow&&dropped==0,"trace incomplete");}
};
inline Observer* Observer::instance=nullptr;
}
