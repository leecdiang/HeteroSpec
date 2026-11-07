#pragma once
#include <cstdint>
#include <stdexcept>
namespace hs_llama_contract {
inline int output_index(int already_emitted, int row, int width) {
    if (already_emitted<1 || width<1 || width>4 || row<0 || row>=width)
        throw std::invalid_argument("invalid verify row mapping");
    return already_emitted+row;
}
inline void preverify_bound(int maximum, int base) {
    if (base<0 || maximum!=base-1) throw std::invalid_argument("pending/KV boundary mismatch");
}
inline bool probe_allowed(bool diagnostic, bool heavy, bool draft, int cycle) {
    return diagnostic && heavy && draft && cycle>=0;
}
}
