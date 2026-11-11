#pragma once
#include <stdexcept>
namespace profile {
inline void init(){throw std::runtime_error("Windows CUPTI collector is not ported; Linux profiling needs a separate instrumented epoch");}
inline void begin(){throw std::runtime_error("Linux profiler unavailable");}
template<class T> void end(const T&){throw std::runtime_error("Linux profiler unavailable");}
}
