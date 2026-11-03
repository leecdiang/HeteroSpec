#pragma once
#include <cstdio>
#include <cstdlib>
#include <string>

#ifdef TRANSFER_CANDIDATE
extern "C" LLAMA_API void hs_b570_set_layout(int);
extern "C" LLAMA_API void hs_b570_set_reference_q8(bool);
extern "C" LLAMA_API void hs_b570_set_prefix_extent(bool);
#endif

struct RequestPolicy {
    int producer = 0;
    int consumer = 0;
    bool precision = true;
    bool prefix = true;
    bool clean = false;
};
static RequestPolicy policy;
static ggml_backend_dev_t selected_device = nullptr;
static size_t min_device_free = SIZE_MAX;
static size_t min_ram_free = SIZE_MAX;
static void capacity_check() {
    size_t available = 0, total = 0;
    ggml_backend_dev_memory(selected_device, &available, &total);
    MEMORYSTATUSEX memory{};
    memory.dwLength = sizeof(memory);
    need(GlobalMemoryStatusEx(&memory), "RAM query");
    min_device_free = std::min(min_device_free,available);
    min_ram_free = std::min(min_ram_free,size_t(memory.ullAvailPhys));
    need(available >= 128ULL*1024*1024, "128 MiB device reserve");
    need(memory.ullAvailPhys >= 2ULL*1024*1024*1024, "2 GiB host reserve");
}
class DecodeScope {
public:
    DecodeScope(const std::string &role, const char *phase) {
#ifdef TRANSFER_CANDIDATE
        const int mode = role == "target" ? (std::string(phase) == "PREFILL" ? policy.producer : policy.consumer) : 0;
        hs_b570_set_layout(mode);
        hs_b570_set_reference_q8(mode != 0 && policy.precision);
        hs_b570_set_prefix_extent(mode != 0 && policy.prefix);
#endif
    }
    ~DecodeScope() {
#ifdef TRANSFER_CANDIDATE
        hs_b570_set_layout(0);
        hs_b570_set_reference_q8(false);
        hs_b570_set_prefix_extent(false);
#endif
    }
};

