#pragma once
#include <cstdint>

extern "C" {
__declspec(dllexport) const char * hs_e03_runtime_metadata();
__declspec(dllexport) int hs_e03_select_arm(int arm);
__declspec(dllexport) int hs_e03_selected_arm();
__declspec(dllexport) std::uint64_t hs_e03_pair4_dispatches();
__declspec(dllexport) std::uint64_t hs_e03_packed_dispatches();
__declspec(dllexport) std::uint64_t hs_e03_loop4_dispatches();
__declspec(dllexport) int hs_e03_failure_code();
__declspec(dllexport) const char * hs_e03_failure_message();
}
void hs_e03_note_dispatch(int route);


void hs_e03_record_failure(int code,const char * message) noexcept;
