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
    for(std::size_t i=0;i<tokens;i+=std::size_t(caller))
        out.push_back(int(std::min<std::size_t>(tokens-i,std::size_t(caller))));
    return out;
}
}
