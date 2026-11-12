#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "backend.hpp"

namespace probe {
static std::string fault;
const char* implementation() { return "cpu-fake"; }
void preflight() {
    char value[32]{};
    const DWORD length = GetEnvironmentVariableA("HS_B_FAULT", value, sizeof(value));
    require(length < sizeof(value), "fault_length");
    fault = value;
}
void run(Step step) {
    static constexpr const char* faults[] = {"meter","load","count","uuid","close","flush"};
    require(fault != faults[static_cast<int>(step)], "fixture_failure");
    switch (step) {
    case Step::meter: evidence.version = 28; break;
    case Step::load: break;
    case Step::count: evidence.device_count = fault == "count2" ? 2 : 1; break;
    case Step::uuid_query:
        evidence.observed_uuid = fault == "wrong_uuid" ? "wrong" : uuid;
        evidence.observed_name = device_name;
        break;
    case Step::close: break;
    case Step::flush:
        evidence.flush_ok = fault != "incomplete";
        evidence.drained = fault != "pool";
        evidence.runtime_records = 2;
        evidence.callbacks = 4;
        evidence.correlation[0] = 41;
        evidence.correlation[1] = fault == "unattributed" ? 0 : 42;
        evidence.drop_reads[0] = fault == "drop";
        evidence.kernel_records = fault == "kernel";
        break;
    }
}
void cleanup() noexcept {}
}
