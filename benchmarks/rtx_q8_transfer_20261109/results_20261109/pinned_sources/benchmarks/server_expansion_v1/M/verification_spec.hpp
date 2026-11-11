#pragma once
// Native-adapter helper: parameter relationships, not an implementation of SD.
// Does not alter model/reference dispatch or authorize a GPU request.
#include <cstdint>
#include <stdexcept>
#include <vector>
namespace server_expansion {
struct VerificationSpec {
    uint32_t k=3, draft_prefill_ub=4, target_requested_capacity=4;
    void check() const {
        if((k!=3 && k!=7) || draft_prefill_ub!=4 || target_requested_capacity<k+1)
            throw std::invalid_argument("Bind k=3/7 separately from draft prefill UB and output capacity");
    }
    uint32_t max_rows() const {check();return k+1;}
    void check_observed(uint32_t rows, const std::vector<uint8_t>& mask, uint32_t copied) const {
        check();if(rows==0 || rows>k+1 || mask.size()!=rows)throw std::invalid_argument("actual caller rows/mask");
        uint32_t expected=0;for(auto b:mask){if(b>1)throw std::invalid_argument("nonboolean mask");expected+=b;}
        if(expected!=copied || expected>target_requested_capacity)throw std::invalid_argument("requested output ownership");
    }
    uint64_t conservative_position_limit(uint64_t committed) const {return committed+max_rows();}
};
}
