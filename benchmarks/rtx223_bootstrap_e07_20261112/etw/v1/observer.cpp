// Manifest-based Windows process/image events, in the existing CPU supervisor.
// No CUDA or NVML imports. All production operations require an explicit start.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <evntrace.h>
#include <evntcons.h>
#include <tdh.h>
#include <array>
#include <atomic>
#include <deque>
#include <mutex>
#include <thread>

namespace {
constexpr GUID provider{0x22fb2cd6,0x0e7b,0x422b,{0xa0,0xc7,0x2f,0xad,0x1f,0xd0,0xe7,0x16}};
constexpr wchar_t name[] = L"HeteroSpec-B1-6dd57db3-image";
constexpr size_t capacity = 1024;
struct Properties {
    EVENT_TRACE_PROPERTIES value{};
    wchar_t logger[128]{};
};
struct Record {
    ULONG pid;
    ULONG event;
    ULONGLONG creation;
    LONGLONG stamp;
    wchar_t path[1024];
};
TRACEHANDLE session{};
TRACEHANDLE consumer = INVALID_PROCESSTRACE_HANDLE;
HANDLE thread_handle{};
std::mutex guard;
std::deque<Record> records;
ULONG bound_pid{};
std::atomic<ULONG> error{};
std::atomic<bool> ended{};
bool used{};
ULONG last_stage{};

Properties properties() {
    Properties p{};
    p.value.Wnode.BufferSize = sizeof(p);
    p.value.Wnode.Flags = WNODE_FLAG_TRACED_GUID;
    p.value.Wnode.ClientContext = 1;
    p.value.LogFileMode = EVENT_TRACE_REAL_TIME_MODE;
    p.value.BufferSize = 64;
    p.value.MinimumBuffers = 4;
    p.value.MaximumBuffers = 32;
    p.value.FlushTimer = 1;
    p.value.LoggerNameOffset = offsetof(Properties, logger);
    return p;
}

ULONG property(EVENT_RECORD* rec, const wchar_t* field, void* out, ULONG max, ULONG& actual) {
    PROPERTY_DATA_DESCRIPTOR d{};
    d.PropertyName = reinterpret_cast<ULONGLONG>(field);
    d.ArrayIndex = ULONG_MAX;
    ULONG rc = TdhGetPropertySize(rec, 0, nullptr, 1, &d, &actual);
    if (rc != ERROR_SUCCESS) return rc;
    if (!actual || actual > max) return ERROR_INVALID_DATA;
    return TdhGetProperty(rec, 0, nullptr, 1, &d, actual, static_cast<PBYTE>(out));
}

void WINAPI on_event(EVENT_RECORD* e) noexcept {
    if (!IsEqualGUID(e->EventHeader.ProviderId, provider) || error.load()) return;
    ULONG id = e->EventHeader.EventDescriptor.Id;
    if (id != 1 && id != 2 && id != 5 && id != 6) return;
    Record r{};
    ULONG n = 0;
    if (property(e,L"ProcessID",&r.pid,sizeof(r.pid),n) || n != sizeof(r.pid)) {
        error = ERROR_INVALID_DATA; return;
    }
    try {
        std::lock_guard<std::mutex> lock(guard);
        if (bound_pid && bound_pid != r.pid) return;
        r.event = id;
        r.stamp = e->EventHeader.TimeStamp.QuadPart;
        if (id == 1 || id == 2) {
            if (property(e,L"CreateTime",&r.creation,sizeof(r.creation),n) || n != sizeof(r.creation)) {
                error = ERROR_INVALID_DATA; return;
            }
        } else if (property(e,L"ImageName",r.path,sizeof(r.path),n) ||
                   n % sizeof(wchar_t) || !r.path[0] || r.path[n/sizeof(wchar_t)-1]) {
            error = ERROR_INVALID_DATA; return;
        }
        if (records.size() == capacity) {error = ERROR_BUFFER_OVERFLOW; return;}
        records.push_back(r);
    } catch (...) {error = ERROR_NOT_ENOUGH_MEMORY;}
}

DWORD WINAPI drain(void*) {
    ULONG rc = ProcessTrace(&consumer, 1, nullptr, nullptr);
    if (rc != ERROR_SUCCESS) error = rc;
    ended = true;
    return rc;
}
}
#define API extern "C" __declspec(dllexport) ULONG WINAPI

API hs_trace_start() {
    if (used) return ERROR_ALREADY_EXISTS;
    used = true;
    auto props = properties();
    TRACEHANDLE fresh{};
    last_stage=1;
    ULONG rc = StartTraceW(&fresh, name, &props.value);
    if (rc != ERROR_SUCCESS) return rc; // never adopt an existing session
    session = fresh;
    EVENT_TRACE_LOGFILEW log{};
    log.LoggerName = const_cast<LPWSTR>(name);
    log.ProcessTraceMode = PROCESS_TRACE_MODE_REAL_TIME | PROCESS_TRACE_MODE_EVENT_RECORD;
    log.EventRecordCallback = on_event;
    last_stage=2;
    consumer = OpenTraceW(&log);
    if (consumer == INVALID_PROCESSTRACE_HANDLE) return GetLastError();
    last_stage=3;
    thread_handle = CreateThread(nullptr,0,drain,nullptr,0,nullptr);
    if (!thread_handle) return GetLastError();
    last_stage=4;
    return EnableTraceEx2(session,&provider,EVENT_CONTROL_CODE_ENABLE_PROVIDER,
                          TRACE_LEVEL_INFORMATION,0x50,0,2000,nullptr);
}

API hs_trace_bind(ULONG pid) {
    std::lock_guard<std::mutex> lock(guard);
    if (!pid || bound_pid) return ERROR_INVALID_PARAMETER;
    bound_pid = pid;
    for (auto it = records.begin(); it != records.end();) {
        if (it->pid != pid) it = records.erase(it);
        else ++it;
    }
    return error.load();
}

API hs_trace_next(Record* out, ULONG size) {
    if (!out || size != sizeof(Record)) return ERROR_INVALID_PARAMETER;
    if (error.load()) return error.load();
    std::lock_guard<std::mutex> lock(guard);
    if (!bound_pid || records.empty()) return ERROR_NO_MORE_ITEMS;
    *out = records.front(); records.pop_front();
    return ERROR_SUCCESS;
}

API hs_trace_health() {
    if (ended) return ERROR_BROKEN_PIPE;
    return error.load();
}

API hs_trace_stop(ULONG* lost) {
    if (!session || !lost) return ERROR_INVALID_HANDLE;
    auto p = properties();
    ULONG rc = ControlTraceW(session,nullptr,&p.value,EVENT_TRACE_CONTROL_STOP);
    if (rc != ERROR_SUCCESS) return rc;
    session = 0;
    lost[0] = p.value.EventsLost; lost[1] = p.value.LogBuffersLost;
    lost[2] = p.value.RealTimeBuffersLost;
    if (thread_handle) {
        if (WaitForSingleObject(thread_handle,5000) != WAIT_OBJECT_0) return ERROR_TIMEOUT;
        CloseHandle(thread_handle); thread_handle = nullptr;
    }
    if (consumer != INVALID_PROCESSTRACE_HANDLE) {
        rc = CloseTrace(consumer); consumer = INVALID_PROCESSTRACE_HANDLE;
        if (rc != ERROR_SUCCESS) return rc;
    }
    return error.load();
}

API hs_trace_stage() {return last_stage;}
