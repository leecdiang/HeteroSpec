#pragma once
#include <cstddef>
#include <stdexcept>
#include <vector>
#include <algorithm>
#include <limits>
namespace tpds_decisive {
inline std::vector<int> draft_schedule(std::size_t tokens, int caller) {
    if (tokens==0 || tokens>std::size_t(std::numeric_limits<int>::max()) ||
        (caller!=1 && caller!=4)) throw std::invalid_argument("invalid draft schedule");
    std::vector<int> out;
    out.reserve((tokens+std::size_t(caller)-1)/std::size_t(caller));
    // The inherited NativeContext::prefill accepts only widths 1, 2 and 4.
    // Keep q4 callers, but decompose a three-token tail as 2+1. The inherited
    // routine still requests the single final output on the final call only.
    for(std::size_t i=0;i<tokens;) {
        int width=int(std::min<std::size_t>(tokens-i,std::size_t(caller)));
        if(width==3)width=2;
        out.push_back(width);i+=std::size_t(width);
    }
    return out;
}
}
