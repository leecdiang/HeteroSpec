#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cuda_runtime_api.h>
#include <cupti_activity.h>
#include <cupti_runtime_cbid.h>
#include <cupti_version.h>
#include <array>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include "backend.hpp"

namespace probe {
namespace fs = std::filesystem;
static_assert(CUPTI_API_VERSION == 28, "expected CUPTI 12.9 update 1");
static_assert(sizeof(cudaUUID_t) == 16, "CUDA UUID ABI");
const char* implementation() { return "native"; }

static fs::path meter_path, root_path;
static HMODULE meter_lib{}, root_lib{};
static DWORD owner_thread{};
static decltype(&cudaGetDeviceCount) query_count{};
static decltype(&cudaGetDeviceProperties) query_props{};
struct MeterAPI {
    decltype(&cuptiGetVersion) version{};
    decltype(&cuptiSubscribe) subscribe{};
    decltype(&cuptiEnableCallback) enable_callback{};
    decltype(&cuptiActivityRegisterCallbacks) buffers{};
    decltype(&cuptiActivityEnable) enable{};
    decltype(&cuptiActivityDisable) disable{};
    decltype(&cuptiActivityFlushAll) flush{};
    decltype(&cuptiActivityGetNextRecord) next{};
    decltype(&cuptiActivityGetNumDroppedRecords) drops{};
    decltype(&cuptiUnsubscribe) unsubscribe{};
} api;
constexpr CUpti_ActivityKind kinds[] = {
    CUPTI_ACTIVITY_KIND_RUNTIME, CUPTI_ACTIVITY_KIND_DRIVER, CUPTI_ACTIVITY_KIND_CONTEXT,
    CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL, CUPTI_ACTIVITY_KIND_MEMCPY
};
constexpr CUpti_CallbackId ids[] = {
    CUPTI_RUNTIME_TRACE_CBID_cudaGetDeviceCount_v3020,
    CUPTI_RUNTIME_TRACE_CBID_cudaGetDeviceProperties_v2_v12000
};
constexpr const wchar_t* modules[] = {
    L"ggml-cuda.dll", L"ggml-base.dll", L"cudart64_12.dll", L"cublas64_12.dll",
    L"cublasLt64_12.dll", L"msvcp140.dll", L"vcruntime140.dll", L"vcruntime140_1.dll", L"vcomp140.dll"
};
static CUpti_SubscriberHandle subscriber{};
static unsigned enabled_kinds{};
static bool registered{}, finish_attempted{};
static std::atomic<bool> invalid{false};
static std::atomic<const char*> first_trace_error{nullptr};
static const char* cleanup_error = "none";
static void invalidate(const char* reason) noexcept {
    const char* none = nullptr;
    first_trace_error.compare_exchange_strong(none, reason);
    invalid.store(true);
}
static std::atomic<int> expected_api{-1};

static std::wstring env(const wchar_t* key) {
    wchar_t value[32768];
    const DWORD count = GetEnvironmentVariableW(key, value, static_cast<DWORD>(std::size(value)));
    require(count && count < std::size(value), "missing_binding");
    return {value, count};
}
static void check_path(HMODULE handle, const fs::path& expected) {
    wchar_t path[32768]{};
    const DWORD count = handle ? GetModuleFileNameW(handle, path, static_cast<DWORD>(std::size(path))) : 0;
    std::error_code ec;
    require(count && count < std::size(path) && fs::equivalent(path, expected, ec) && !ec,
            "actual_module_identity");
}
void preflight() {
    BOOL in_job{};
    require(IsProcessInJob(GetCurrentProcess(), nullptr, &in_job) && in_job, "job_membership");
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION job{};
    require(QueryInformationJobObject(nullptr, JobObjectExtendedLimitInformation, &job, sizeof(job), nullptr),
            "job_limits");
    const auto flags = job.BasicLimitInformation.LimitFlags;
    const DWORD mandatory = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_ACTIVE_PROCESS |
                            JOB_OBJECT_LIMIT_PROCESS_MEMORY;
    require((flags & mandatory) == mandatory &&
            !(flags & (JOB_OBJECT_LIMIT_BREAKAWAY_OK | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK)) &&
            job.BasicLimitInformation.ActiveProcessLimit == 1 && job.ProcessMemoryLimit == (size_t(2) << 30),
            "job_policy");
    const std::wstring fixed = L"GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd";
    require(env(L"HS_B_UUID") == fixed && env(L"CUDA_VISIBLE_DEVICES") == fixed &&
            env(L"GGML_CUDA_DISABLE_GRAPHS") == L"1", "device_binding");
    meter_path = env(L"HS_B_CUPTI");
    root_path = env(L"HS_B_NUMERIC");
    require(root_path.is_absolute() && meter_path.is_absolute() &&
            !_wcsicmp(root_path.filename().c_str(), modules[0]) &&
            !_wcsicmp(meter_path.filename().c_str(), L"cupti64_2025.2.1.dll"), "module_binding");
    require(!GetModuleHandleW(meter_path.filename().c_str()) &&
            !GetModuleHandleW(modules[0]) && !GetModuleHandleW(modules[2]), "startup_module");
    owner_thread = GetCurrentThreadId();
}
template<class T> static T resolve(HMODULE lib, const char* name) {
    const auto address = GetProcAddress(lib, name);
    require(address != nullptr, "missing_export");
    HMODULE owner = nullptr;
    require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, reinterpret_cast<LPCWSTR>(address), &owner) &&
            owner == lib, "forwarded_export");
    return reinterpret_cast<T>(address);
}

// No callback allocates memory or throws across the CUPTI ABI.
constexpr size_t block_size = 4 * 1024 * 1024;
alignas(8) static uint8_t pool[4][block_size];
static SRWLOCK guard = SRWLOCK_INIT;
struct Lock {
    Lock() { AcquireSRWLockExclusive(&guard); }
    ~Lock() { ReleaseSRWLockExclusive(&guard); }
};
static bool leased[4]{};
static unsigned requested_buffers{}, returned_buffers{}, callback_entries[2]{}, callback_exits[2]{};
static unsigned active_completions{};
// After sealing, callbacks can only invalidate. The main thread owns the
// immutable success snapshot from this boundary through pipe serialization.
static bool sealed{};
struct Witness {
    uint32_t id, corr, pid, tid, result;
    uint64_t start, end;
};
// Retain only the two queried API kinds; more witnesses than capacity fail closed.
static Witness witnesses[128]{};
static size_t witness_count{};
static void CUPTIAPI request_buffer(uint8_t** data, size_t* size, size_t* maximum) {
    Lock lock;
    *data = nullptr; *size = 0; *maximum = 0;
    if (sealed) { invalidate("late_buffer_request"); return; }
    for (size_t i = 0; i < std::size(pool); ++i) {
        if (leased[i]) continue;
        leased[i] = true;
        *data = pool[i]; *size = block_size;
        ++requested_buffers;
        return;
    }
    invalidate("buffer_exhausted");
}
static void read_record(CUpti_Activity* record) {
    Lock lock;
    if (sealed) { invalidate("late_record"); return; }
    switch (record->kind) {
    case CUPTI_ACTIVITY_KIND_RUNTIME:
    case CUPTI_ACTIVITY_KIND_DRIVER: {
        const auto& info = *reinterpret_cast<CUpti_ActivityAPI*>(record);
        if (!info.start || info.end < info.start || info.processId != GetCurrentProcessId())
            invalidate("api_record_incomplete");
        if (info.kind == CUPTI_ACTIVITY_KIND_DRIVER) { ++evidence.driver_records; break; }
        ++evidence.runtime_records;
        if (info.cbid != ids[0] && info.cbid != ids[1]) break;
        if (witness_count == std::size(witnesses)) { invalidate("witness_capacity"); break; }
        witnesses[witness_count++] = {info.cbid,info.correlationId,info.processId,info.threadId,
                                     info.returnValue,info.start,info.end};
        break;
    }
    case CUPTI_ACTIVITY_KIND_CONTEXT: {
        const auto& info = *reinterpret_cast<CUpti_ActivityContext3*>(record);
        if (info.deviceId != 0) invalidate("context_wrong_device");
        ++evidence.context_records;
        break;
    }
    case CUPTI_ACTIVITY_KIND_MEMCPY: {
        const auto& info = *reinterpret_cast<CUpti_ActivityMemcpy6*>(record);
        if (!info.start || info.end < info.start || info.deviceId != 0) invalidate("copy_record_invalid");
        ++evidence.memcpy_records;
        break;
    }
    case CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL:
    case CUPTI_ACTIVITY_KIND_KERNEL:
        ++evidence.kernel_records;
        invalidate("kernel_observed");
        break;
    default:
        invalidate("unexpected_activity");
    }
}
static void CUPTIAPI complete_buffer(CUcontext context, uint32_t stream, uint8_t* data,
                                     size_t size, size_t valid) {
    size_t index = 0;
    {
        Lock lock;
        if (sealed) { invalidate("late_buffer_completion"); return; }
        while (index < std::size(pool) && data != pool[index]) ++index;
        if (index == std::size(pool) || !leased[index] || context || stream || size != block_size ||
            valid > size) { invalidate("buffer_frame"); return; }
        ++active_completions;
    }
    if (valid) {
        CUpti_Activity* record = nullptr;
        CUptiResult rc;
        while ((rc = api.next(data, valid, &record)) == CUPTI_SUCCESS) {
            if (!record) { invalidate("empty_record"); break; }
            read_record(record);
        }
        if (rc != CUPTI_ERROR_MAX_LIMIT_REACHED) invalidate("record_parse");
    }
    {
        Lock lock;
        leased[index] = false;
        ++returned_buffers;
        --active_completions;
    }
}
static void CUPTIAPI api_callback(void*, CUpti_CallbackDomain domain, CUpti_CallbackId id,
                                  const void* payload) {
    const int index = expected_api.load();
    Lock lock;
    if (sealed) { invalidate("late_api_callback"); return; }
    if (index < 0 || GetCurrentThreadId() != owner_thread) return;
    if (domain != CUPTI_CB_DOMAIN_RUNTIME_API || id != ids[index] || !payload) {
        invalidate("callback_identity");
        return;
    }
    const auto& data = *static_cast<const CUpti_CallbackData*>(payload);
    ++evidence.callbacks;
    if (data.callbackSite == CUPTI_API_ENTER) {
        if (++callback_entries[index] != 1 || data.correlationId == 0) invalidate("callback_enter");
        evidence.correlation[index] = data.correlationId;
    } else if (data.callbackSite == CUPTI_API_EXIT) {
        if (++callback_exits[index] != 1 || !data.functionReturnValue ||
            *static_cast<const cudaError_t*>(data.functionReturnValue) != cudaSuccess ||
            evidence.correlation[index] != data.correlationId) invalidate("callback_exit");
    } else invalidate("callback_site");
}
static void global_drops(size_t index) {
    size_t delta{};
    require(api.drops(nullptr, 0, &delta) == CUPTI_SUCCESS, "global_drops");
    evidence.drop_reads[index] = delta;
    evidence.drop_mask |= 1U << index;
    require(!delta, "records_dropped");
}
static void start_meter() {
    check_deadline();
    meter_lib = LoadLibraryExW(meter_path.c_str(), nullptr,
                               LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    check_path(meter_lib, meter_path);
    api.version = resolve<decltype(api.version)>(meter_lib, "cuptiGetVersion");
    api.subscribe = resolve<decltype(api.subscribe)>(meter_lib, "cuptiSubscribe");
    api.enable_callback = resolve<decltype(api.enable_callback)>(meter_lib, "cuptiEnableCallback");
    api.buffers = resolve<decltype(api.buffers)>(meter_lib, "cuptiActivityRegisterCallbacks");
    api.enable = resolve<decltype(api.enable)>(meter_lib, "cuptiActivityEnable");
    api.disable = resolve<decltype(api.disable)>(meter_lib, "cuptiActivityDisable");
    api.flush = resolve<decltype(api.flush)>(meter_lib, "cuptiActivityFlushAll");
    api.next = resolve<decltype(api.next)>(meter_lib, "cuptiActivityGetNextRecord");
    api.drops = resolve<decltype(api.drops)>(meter_lib, "cuptiActivityGetNumDroppedRecords");
    api.unsubscribe = resolve<decltype(api.unsubscribe)>(meter_lib, "cuptiUnsubscribe");
    check_deadline();
    require(api.version(&evidence.version) == CUPTI_SUCCESS && evidence.version == CUPTI_API_VERSION,
            "meter_version");
    check_deadline();
    require(api.subscribe(&subscriber, api_callback, nullptr) == CUPTI_SUCCESS, "subscribe");
    for (const auto id : ids) {
        check_deadline();
        require(api.enable_callback(1, subscriber, CUPTI_CB_DOMAIN_RUNTIME_API, id) == CUPTI_SUCCESS,
                "enable_callback");
    }
    check_deadline();
    require(api.buffers(request_buffer, complete_buffer) == CUPTI_SUCCESS, "register_buffers");
    registered = true;
    for (const auto kind : kinds) {
        check_deadline();
        require(api.enable(kind) == CUPTI_SUCCESS, "enable_activity");
        ++enabled_kinds;
    }
    global_drops(0);
}
static void load_numeric() {
    require(!GetModuleHandleW(modules[0]), "numeric_preloaded");
    check_deadline();
    root_lib = LoadLibraryExW(root_path.c_str(), nullptr,
                              LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    check_path(root_lib, root_path);
    for (auto name : modules) check_path(GetModuleHandleW(name), root_path.parent_path() / name);
    const auto runtime = GetModuleHandleW(modules[2]);
    query_count = resolve<decltype(query_count)>(runtime, "cudaGetDeviceCount");
    query_props = resolve<decltype(query_props)>(runtime, "cudaGetDeviceProperties_v2");
}
static void get_count() {
    int count{};
    check_deadline();
    expected_api.store(0);
    const auto result = query_count(&count);
    expected_api.store(-1);
    require(result == cudaSuccess && count == 1, "device_count");
    evidence.device_count = static_cast<unsigned>(count);
}
static void get_uuid() {
    cudaDeviceProp prop{};
    check_deadline();
    expected_api.store(1);
    const auto result = query_props(&prop, 0);
    expected_api.store(-1);
    require(result == cudaSuccess && std::memchr(prop.name, 0, sizeof(prop.name)), "properties");
    evidence.observed_name = prop.name;
    std::string id = "GPU-";
    constexpr char hex[] = "0123456789abcdef";
    for (size_t i = 0; i < 16; ++i) {
        if (i == 4 || i == 6 || i == 8 || i == 10) id += '-';
        const auto byte = static_cast<unsigned char>(prop.uuid.bytes[i]);
        id += hex[byte >> 4]; id += hex[byte & 15];
    }
    evidence.observed_uuid = id;
}
static void close_root() {
    const auto handle = root_lib;
    root_lib = nullptr; // One release attempt even on failure.
    require(handle && FreeLibrary(handle), "root_release");
}
static void finish_meter() {
    finish_attempted = true;
    bool success = true;
    while (enabled_kinds) {
        if (api.disable(kinds[--enabled_kinds]) != CUPTI_SUCCESS) success = false;
    }
    if (subscriber) {
        if (api.unsubscribe(subscriber) != CUPTI_SUCCESS) success = false;
        subscriber = nullptr;
    }
    if (!registered) return;
    evidence.flush_ok = api.flush(CUPTI_ACTIVITY_FLAG_FLUSH_FORCED) == CUPTI_SUCCESS;
    {
        Lock lock;
        evidence.drained = active_completions == 0 && requested_buffers == returned_buffers;
        for (bool outstanding : leased) evidence.drained &= !outstanding;
        sealed = true;
        uint64_t first_end{};
        for (size_t i = 0; i < 2; ++i) {
            unsigned matches{};
            for (size_t j = 0; j < witness_count; ++j) {
                const auto& w = witnesses[j];
                if (w.id != ids[i] || w.corr != evidence.correlation[i]) continue;
                ++matches;
                if (w.pid != GetCurrentProcessId() || w.tid != owner_thread ||
                    w.result != cudaSuccess || !w.start || w.end < w.start)
                    invalidate("activity_identity");
                if (i == 0) first_end = w.end;
                else if (w.start < first_end) invalidate("activity_order");
            }
            if (matches != 1 || callback_entries[i] != 1 || callback_exits[i] != 1)
                invalidate("missing_or_duplicate_witness");
        }
    }
    global_drops(1);
    require(success && evidence.flush_ok && evidence.drained && !invalid.load(), "meter_incomplete");
    // The registered buffer callbacks have process lifetime. Retain CUPTI through exit.
}
void run(Step step) {
    require(!invalid.load(), "trace_invalid");
    switch (step) {
    case Step::meter: start_meter(); break;
    case Step::load: load_numeric(); break;
    case Step::count: get_count(); break;
    case Step::uuid_query: get_uuid(); break;
    case Step::close: close_root(); break;
    case Step::flush: finish_meter(); break;
    }
    require(!invalid.load(), "trace_invalid");
}
void cleanup() noexcept {
    if (root_lib) { try { close_root(); } catch (...) { cleanup_error = "root_release"; } }
    if (!finish_attempted && (registered || subscriber)) {
        try { finish_meter(); } catch (...) { cleanup_error = "meter_teardown"; }
    }
}
void verify_receipt_boundary() {
    Lock lock;
    require(sealed && !invalid.load(), "late_or_invalid_trace");
}
std::string failure_details() {
    Lock lock;
    const char* trace = first_trace_error.load();
    return "dropped_first=" + std::to_string(evidence.drop_reads[0]) +
           " dropped_final=" + std::to_string(evidence.drop_reads[1]) +
           " drop_reads_valid=" + std::to_string(evidence.drop_mask) +
           " kernels=" + std::to_string(evidence.kernel_records) +
           " complete=0 flush_ok=" + std::to_string(evidence.flush_ok) +
           " drained=" + std::to_string(evidence.drained) +
           " cleanup=" + cleanup_error + " trace=" + (trace ? trace : "none");
}
}
