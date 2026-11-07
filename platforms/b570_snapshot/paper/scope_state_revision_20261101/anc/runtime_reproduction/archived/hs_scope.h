#pragma once
#include <cstdlib>
#include <cstring>
#include <stdexcept>
namespace hs_scope {
inline thread_local bool active = false;
inline int requested_layout=0;
inline int layout95(){return requested_layout;}
inline int mask() {
    static const int value = [] {
        const char * p = std::getenv("HS_SCOPE_MASK");
        if (!p) return -1;
        char * end = nullptr;
        long v = std::strtol(p, &end, 10);
        if (!*p || *end || v < 0 || v > 15) throw std::runtime_error("invalid scope mask");
        return int(v);
    }();
    return value;
}
struct guard {
    bool prior;
    guard(const char * role, bool prefill) : prior(active) {
        int m = mask();
        if (m < 0) { active = std::getenv("HS_ATTENTION_QUERY_BATCH") != nullptr; return; }
        int bit;
        if (std::strcmp(role, "target") == 0) bit = prefill ? 1 : 2;
        else if (std::strcmp(role, "draft") == 0) bit = prefill ? 4 : 8;
        else throw std::runtime_error("unsupported scope role");
        active = (m & bit) != 0;
    }
    ~guard() { active = prior; }
};
}
