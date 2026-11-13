#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <charconv>
#include "backend.hpp"

namespace probe {
Evidence evidence;
static ULONGLONG deadline_tick{};
static void read_deadline() {
    char value[32]{};
    const DWORD length = GetEnvironmentVariableA("HS_B_DEADLINE_TICK", value, sizeof(value));
    require(length && length < sizeof(value), "deadline_missing");
    const auto parsed = std::from_chars(value, value + length, deadline_tick);
    const auto now = GetTickCount64();
    require(parsed.ec == std::errc{} && parsed.ptr == value + length &&
            now < deadline_tick && deadline_tick - now <= 80000, "deadline_binding");
}
void check_deadline() {
    require(GetTickCount64() < deadline_tick, "deadline_elapsed");
}
// Only accept one exact byte-framed grant. Never parse a script or extra arguments.
static void grant(const char* stage) {
    const std::string command = std::string("GO_") + stage + "\n";
    for (char expected : command) {
        char actual{};
        DWORD read{};
        require(ReadFile(GetStdHandle(STD_INPUT_HANDLE), &actual, 1, &read, nullptr)
                && read == 1 && actual == expected, "grant_denied");
    }
}
static void line(const std::string& body) {
    const auto data = body + "\n";
    DWORD written{};
    require(WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), data.data(), static_cast<DWORD>(data.size()),
                      &written, nullptr) && written == data.size(), "channel_write");
}
static void validate(Step step) {
    const auto& e = evidence;
    if (step == Step::meter) require(e.version == 28, "meter_version");
    if (step == Step::count) require(e.device_count == 1, "device_count");
    if (step == Step::uuid_query)
        require(e.observed_uuid == uuid && e.observed_name == device_name, "device_identity");
    if (step != Step::flush) return;
    require(e.kernel_records == 0 && e.drop_mask == 3 && !e.drop_reads[0] && !e.drop_reads[1],
            "trace_loss_or_kernel");
    require(e.runtime_records >= 2 && e.callbacks == 4 && e.correlation[0] != 0 &&
            e.correlation[1] != 0 && e.correlation[0] != e.correlation[1], "trace_attribution");
    require(e.flush_ok && e.drained, "trace_incomplete");
}
static std::string receipt() {
    const auto& e = evidence;
    char data[1536]{};
    const int bytes = std::snprintf(data, sizeof(data),
        "RECEIPT {\"schema\":\"heterospec.e06.probe.v1\",\"backend\":\"%s\","
        "\"pid\":%lu,\"uuid\":\"%s\",\"device_count\":%u,\"device_name\":\"%s\","
        "\"cupti_version\":%u,\"count_correlation\":%u,\"uuid_correlation\":%u,"
        "\"runtime_records\":%u,\"driver_records\":%u,\"context_records\":%u,"
        "\"memcpy_records\":%u,\"kernel_records\":%u,\"api_callbacks\":%u,"
        "\"drop_reads\":[%llu,%llu],\"dropped\":0,\"flush_ok\":true,"
        "\"drained\":true,\"physical_upper_bound\":null}",
        implementation(), GetCurrentProcessId(), uuid, e.device_count, device_name,
        e.version, e.correlation[0], e.correlation[1], e.runtime_records, e.driver_records,
        e.context_records, e.memcpy_records, e.kernel_records, e.callbacks,
        static_cast<unsigned long long>(e.drop_reads[0]), static_cast<unsigned long long>(e.drop_reads[1]));
    require(bytes > 0 && static_cast<size_t>(bytes) < sizeof(data), "receipt_size");
    return data;
}
}

int wmain(int argc, wchar_t**) {
    using namespace probe;
    const char* stage = "PREFLIGHT";
    try {
        require(argc == 1, "arguments");
        require(GetFileType(GetStdHandle(STD_INPUT_HANDLE)) == FILE_TYPE_PIPE &&
                GetFileType(GetStdHandle(STD_OUTPUT_HANDLE)) == FILE_TYPE_PIPE, "private_pipes");
        read_deadline();
        preflight();
        line("READY");
        for (int index = 0; index < 6; ++index) {
            const Step step = static_cast<Step>(index);
            stage = names[index];
            grant(names[index]);
            if (step != Step::close && step != Step::flush) check_deadline();
            run(step);
            validate(step);
            line(std::string("OK_") + names[index]);
        }
        const auto success_receipt = receipt();
        verify_receipt_boundary();
        line(success_receipt);
        line("END");
        return 0;
    } catch (const std::exception& exc) {
        cleanup();
        try { line(std::string("ERROR ") + stage + " " + exc.what() + " " + failure_details()); } catch (...) {}
        return 2;
    } catch (...) {
        cleanup();
        return 3;
    }
}
