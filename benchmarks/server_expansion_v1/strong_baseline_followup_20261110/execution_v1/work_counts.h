#pragma once
#include <cstdint>
struct hs_work_counts {
    uint64_t kernel_calls, quant_calls, quant_rows, quant_bytes;
    uint64_t scalar_dot_dispatches, scalar_dot_columns, backend_loop_entries;
    uint64_t copy_calls, copy_bytes, sync_calls, alloc_calls, alloc_bytes;
};
extern "C" void hs_work_reset();
extern "C" hs_work_counts hs_work_finish();
extern "C" void hs_work_quant(uint64_t rows, uint64_t bytes);
extern "C" void hs_work_dot(uint64_t columns);
extern "C" void hs_work_backend();
extern "C" int hs_strong_selected_arm();
extern "C" bool hs_strong_select_arm_once(int arm);
extern "C" void hs_quant_capture_reset(bool enabled);
extern "C" void hs_work_quant_payload(const void* data,uint64_t rows,uint64_t bytes,void* stream);
extern "C" uint64_t hs_quant_capture_count();
extern "C" const unsigned char* hs_quant_capture_data(uint64_t index,uint64_t* rows,uint64_t* bytes);
