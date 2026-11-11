#include "reference_batching.hpp"
#include <cassert>
#include <iostream>

using namespace hs_reference_batching;

static std::vector<uint32_t> scalar_oracle(const DenseAppendState & s) {
    std::vector<uint32_t> out;
    for (uint64_t position = s.head; position < uint64_t(s.head) + s.rows; ++position) {
        uint64_t extent = s.padding;
        while (extent <= position) extent += s.padding;
        out.push_back(uint32_t(std::min<uint64_t>(extent, s.capacity)));
    }
    return out;
}

static size_t exhaustive_minimum(const std::vector<RowRequirement> & rows) {
    if (rows.empty()) return 0;
    size_t minimum = rows.size();
    for (unsigned cuts = 0; cuts < (1u << (rows.size() - 1)); ++cuts) {
        bool valid = true;
        size_t count = 1;
        for (size_t i = 1; i < rows.size(); ++i) {
            if (cuts & (1u << (i - 1))) ++count;
            else if (!(rows[i] == rows[i - 1])) valid = false;
        }
        if (valid) minimum = std::min(minimum, count);
    }
    return minimum;
}

int main() {
    DenseAppendState state{765, 4, 769, 769, 1024, 256, 1, true, false};
    const auto historical = scalar_prefix_requirements(state);
    assert(historical.status == PrefixStatus::supported);
    assert((historical.extents == std::vector<uint32_t>{768,768,768,1024}));
    const auto groups = partition_adjacent(historical.extents);
    assert(groups.size() == 2 && groups[0].begin == 0 && groups[0].end == 3 &&
           groups[1].begin == 3 && groups[1].end == 4);

    // Exercise cache capacity tails, small/large query batches and every boundary
    // with an independent scalar allocation loop, not the planner's formula.
    size_t states = 0;
    for (uint32_t padding : {1u, 3u, 32u, 256u, 512u}) {
        for (uint32_t capacity : {7u, 33u, 257u, 1000u, 1024u}) {
            for (uint32_t head = 0; head < capacity; ++head) {
                for (uint32_t width : {1u, 2u, 4u, 9u, 255u, 256u, 257u, 600u}) {
                    if (uint64_t(head) + width > capacity) continue;
                    DenseAppendState s{head,width,head+width,head+width,capacity,padding,1,true,false};
                    const auto actual = scalar_prefix_requirements(s);
                    assert(actual.status == PrefixStatus::supported);
                    assert(actual.extents == scalar_oracle(s));
                    const auto p = partition_adjacent(actual.extents);
                    if (width <= padding) assert(p.size() <= 2);
                    assert(p.front().begin == 0 && p.back().end == width);
                    ++states;
                }
            }
        }
    }

    state.head = std::numeric_limits<uint32_t>::max() - 1;
    state.rows = 1;
    state.used = state.occupied_end = state.capacity = std::numeric_limits<uint32_t>::max();
    assert(scalar_prefix_requirements(state).extents.at(0) == state.capacity);
    state.rows = 2;
    assert(scalar_prefix_requirements(state).status == PrefixStatus::inconsistent_state);
    state = {765,4,769,769,1024,256,1,true,false};
    state.used = 768; assert(scalar_prefix_requirements(state).status == PrefixStatus::inconsistent_state);
    state.used = 769; state.streams = 2;
    assert(scalar_prefix_requirements(state).status == PrefixStatus::unsupported_state);
    state.streams = 1; state.sliding_window = true;
    assert(scalar_prefix_requirements(state).status == PrefixStatus::unsupported_state);
    state.sliding_window = false; state.contiguous = false;
    assert(scalar_prefix_requirements(state).status == PrefixStatus::unsupported_state);
    state.contiguous = true; state.padding = 0;
    assert(scalar_prefix_requirements(state).status == PrefixStatus::inconsistent_state);

    // Exhaust all sequences of three distinct structural requirements, including
    // equal extents with different arithmetic paths and nonmonotonic extents.
    const RowRequirement alphabet[] = {{256,1,1},{256,2,1},{512,1,2}};
    size_t sequences = 0;
    for (size_t n = 1, count = 3; n <= 7; ++n, count *= 3) {
        for (size_t code = 0; code < count; ++code) {
            size_t remaining = code;
            std::vector<RowRequirement> rows;
            for (size_t i = 0; i < n; ++i) { rows.push_back(alphabet[remaining % 3]); remaining /= 3; }
            const auto planned = partition_adjacent(rows);
            assert(planned.size() == exhaustive_minimum(rows));
            std::vector<RowRequirement> reconstructed;
            for (const auto & group : planned)
                for (size_t i = group.begin; i < group.end; ++i) reconstructed.push_back(group.requirement);
            assert(reconstructed == rows);
            ++sequences;
        }
    }
    bool rejected = false;
    try { (void)partition_adjacent(std::vector<uint32_t>{256,0}); }
    catch (const std::invalid_argument &) { rejected = true; }
    assert(rejected);

    const GraphIdentity original{{Backend::vulkan,2,true,true,false,1},{768,768,768,1024}};
    auto changed = original;
    assert(changed == original);
    changed.policy.f32_q8_activation = false; assert(!(changed == original));
    changed = original; changed.policy.layout = 1; assert(!(changed == original));
    changed = original; changed.policy.prefix = false; assert(!(changed == original));
    changed = original; changed.policy.scalar_head_norm_offload = true; assert(!(changed == original));
    changed = original; changed.extents = {1024,1024,1024,1024}; assert(!(changed == original));
    changed = original; changed.policy.implementation = 2; assert(!(changed == original));

    using A = ActivationPath;
    assert(projection_requirement(true,true,A::f32,A::q8_1,true) == ProjectionAction::retain_f32_batch);
    assert(projection_requirement(true,true,A::f32,A::q8_1,false) == ProjectionAction::unsupported);
    assert(projection_requirement(false,true,A::f32,A::q8_1,true) == ProjectionAction::unsupported);
    assert(projection_requirement(true,true,A::q8_1,A::f32,true) == ProjectionAction::unsupported);
    assert(projection_requirement(true,true,A::f32,A::f32,true) == ProjectionAction::unchanged);
    // A scalar veto applies only to an admitted active rotary head scale.
    assert(!use_scalar_head_preference(true, true, 4, false, true));
    assert(use_scalar_head_preference(false, true, 4, false, true));
    assert(use_scalar_head_preference(true, false, 4, false, true));
    assert(use_scalar_head_preference(true, true, 5, false, true));
    std::cout << "PASS: " << states << " scalar allocation states; " << sequences
              << " exhaustive partition cases; policy identity and projection decisions\n";
}
