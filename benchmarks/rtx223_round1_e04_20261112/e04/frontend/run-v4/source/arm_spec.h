#pragma once
#include <stdexcept>
#include <string>

namespace rtx_scope_transfer {
struct ArmSpec {
    std::string name, scope;
    int selector, target_ub, k;
    bool scoped, draft;
};

inline ArmSpec arm_spec(const std::string & name) {
    if (name == "R") return {name, "R", 1, 1, 0, false, false};
    if (name == "M_GS") return {name, "GS", 2, 4, 0, true, false};
    if (name == "M_PQ") return {name, "PQ", 1, 4, 0, true, false};
    if (name == "M_QB") return {name, "QB", 0, 4, 0, true, false};
    if (name == "C_GS") return {name, "GS", 2, 4, 3, true, true};
    if (name == "C_PQ") return {name, "PQ", 1, 4, 3, true, true};
    if (name == "C_QB") return {name, "QB", 0, 4, 3, true, true};
    throw std::invalid_argument("unknown scope-transfer arm: " + name);
}

inline std::string source_variant(const std::string & family) {
    if (family == "Qwen") return "original";
    if (family == "SmolLM2" || family == "Llama") return "metadata4";
    throw std::invalid_argument("unknown scope-transfer family: " + family);
}

inline std::string pool_key(const std::string & family, const ArmSpec & arm) {
    source_variant(family);
    return family + "/" + arm.scope + "/ctx1024/ub" + std::to_string(arm.target_ub)
        + "/out" + std::to_string(arm.target_ub) + "/f16/fa0/t24";
}
}
