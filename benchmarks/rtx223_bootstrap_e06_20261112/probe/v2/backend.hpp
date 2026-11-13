#pragma once
#include <cstdint>
#include <stdexcept>
#include <string>

namespace probe {
inline constexpr char uuid[] = "GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd";
inline constexpr char device_name[] = "NVIDIA GeForce RTX 5070 Ti Laptop GPU";
enum class Step { meter, load, count, uuid_query, close, flush };
inline constexpr const char* names[] = {"METER","LOAD","COUNT","UUID","CLOSE","FLUSH"};
inline void require(bool value, const char* error) {
    if (!value) throw std::runtime_error(error);
}
struct Evidence {
    unsigned version = 0, device_count = 0;
    std::string observed_uuid, observed_name;
    std::uint32_t correlation[2]{};
    unsigned runtime_records = 0, driver_records = 0, context_records = 0;
    unsigned memcpy_records = 0, kernel_records = 0, callbacks = 0;
    // Read/reset deltas before root load and after drained final flush.
    std::uint64_t drop_reads[2]{};
    unsigned drop_mask = 0;
    bool flush_ok = false, drained = false;
};
extern Evidence evidence;
const char* implementation();
void preflight();
void check_deadline();
void verify_receipt_boundary();
std::string failure_details();
void run(Step step);
void cleanup() noexcept;
}
