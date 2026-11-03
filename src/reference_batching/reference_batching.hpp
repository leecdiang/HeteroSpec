#pragma once

// Shared planning primitives for a fixed numerical reference. This header does
// not assert that an arbitrary backend implements a reference-equivalent kernel.
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

namespace hs_reference_batching {

enum class PrefixStatus { supported, empty, unsupported_state, inconsistent_state };

struct DenseAppendState {
    uint32_t head = 0;
    uint32_t rows = 0;
    uint32_t used = 0;
    uint32_t occupied_end = 0;
    uint32_t capacity = 0;
    uint32_t padding = 0; // actual scalar get_n_kv padding, already normalized
    uint32_t streams = 1;
    bool contiguous = true;
    bool sliding_window = false;
};

struct PrefixRequirements {
    PrefixStatus status = PrefixStatus::empty;
    std::vector<uint32_t> extents;
};

// The caller supplies the physical slot state after appending the batch.
// Arithmetic is widened before addition/rounding: capacities near UINT32_MAX
// are valid inputs, and a malformed state must never wrap into a smaller prefix.
inline PrefixRequirements scalar_prefix_requirements(const DenseAppendState & s) {
    if (s.rows == 0) return {};
    if (s.sliding_window || s.streams != 1 || !s.contiguous)
        return {PrefixStatus::unsupported_state, {}};
    const uint64_t end = uint64_t(s.head) + s.rows;
    if (s.padding == 0 || s.capacity == 0 || end > s.capacity ||
        s.used != s.occupied_end || uint64_t(s.occupied_end) != end)
        return {PrefixStatus::inconsistent_state, {}};
    PrefixRequirements out{PrefixStatus::supported, {}};
    out.extents.reserve(s.rows);
    for (uint32_t row = 0; row < s.rows; ++row) {
        const uint64_t used = uint64_t(s.head) + row + 1;
        const uint64_t padded = ((used + s.padding - 1) / s.padding) * s.padding;
        out.extents.push_back(uint32_t(std::min<uint64_t>(s.capacity,
            std::max<uint64_t>(s.padding, padded))));
    }
    return out;
}

// Path IDs are structural decisions supplied by the backend extractor. They
// identify arithmetic/dispatch requirements, never model names or prompt IDs.
struct RowRequirement {
    uint32_t extent = 0;
    uint64_t arithmetic_path = 0;
    uint64_t dispatch_path = 0;
    bool operator==(const RowRequirement & o) const {
        return extent == o.extent && arithmetic_path == o.arithmetic_path &&
            dispatch_path == o.dispatch_path;
    }
};

struct Group {
    size_t begin = 0;
    size_t end = 0; // exclusive; original row order is retained
    RowRequirement requirement;
};

// Every change in a row requirement forces a cut. Maximal runs therefore use
// the minimum number of contiguous groups under exact requirement equality.
inline std::vector<Group> partition_adjacent(const std::vector<RowRequirement> & rows) {
    std::vector<Group> groups;
    for (size_t begin = 0; begin < rows.size();) {
        if (rows[begin].extent == 0) throw std::invalid_argument("zero physical prefix");
        size_t end = begin + 1;
        while (end < rows.size() && rows[end] == rows[begin]) ++end;
        groups.push_back({begin, end, rows[begin]});
        begin = end;
    }
    return groups;
}

inline std::vector<Group> partition_adjacent(const std::vector<uint32_t> & extents,
                                            uint64_t arithmetic_path = 0,
                                            uint64_t dispatch_path = 0) {
    std::vector<RowRequirement> rows;
    rows.reserve(extents.size());
    for (const auto extent : extents) rows.push_back({extent, arithmetic_path, dispatch_path});
    return partition_adjacent(rows);
}

enum class Backend : uint32_t { cuda = 1, vulkan = 2 };
struct PolicyIdentity {
    Backend backend = Backend::cuda;
    int layout = 0;
    bool prefix = false;
    bool f32_q8_activation = false;
    bool scalar_head_norm_offload = false;
    uint32_t implementation = 1;
    bool operator==(const PolicyIdentity & o) const {
        return backend == o.backend && layout == o.layout && prefix == o.prefix &&
            f32_q8_activation == o.f32_q8_activation &&
            scalar_head_norm_offload == o.scalar_head_norm_offload &&
            implementation == o.implementation;
    }
    bool operator!=(const PolicyIdentity & o) const { return !(*this == o); }
};

struct GraphIdentity {
    PolicyIdentity policy;
    std::vector<uint32_t> extents;
    bool operator==(const GraphIdentity & o) const {
        return policy == o.policy && extents == o.extents;
    }
};

// A backend preflight can describe the actual scalar and batch projection
// dispatches. This decides which existing path is required; it does not invent
// a path or infer numerical equivalence merely from the weight quantization.
enum class ActivationPath { f32, q8_1, other };
enum class ProjectionAction { unchanged, retain_f32_batch, unsupported };
inline ProjectionAction projection_requirement(bool q8_0_weight, bool f32_input,
        ActivationPath scalar, ActivationPath batch, bool f32_batch_available) {
    if (scalar == batch) return ProjectionAction::unchanged;
    if (q8_0_weight && f32_input && scalar == ActivationPath::f32 &&
        batch == ActivationPath::q8_1 && f32_batch_available)
        return ProjectionAction::retain_f32_batch;
    return ProjectionAction::unsupported;
}

} // namespace hs_reference_batching
