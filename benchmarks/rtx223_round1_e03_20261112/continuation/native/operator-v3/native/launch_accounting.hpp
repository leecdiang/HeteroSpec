#pragma once
#include <cstdint>
#include <stdexcept>

namespace hs_operator_accounting {
struct LaunchCounts {
    std::uint64_t attempted=0, submitted=0;
    std::uint64_t cap=119;
    void before() {
        if(attempted>=cap) throw std::runtime_error("frozen operator launch cap exhausted before dispatch");
        ++attempted;
    }
    void submission_succeeded() {
        if(submitted>=attempted) throw std::runtime_error("launch submission without attempt");
        ++submitted;
    }
};
}
