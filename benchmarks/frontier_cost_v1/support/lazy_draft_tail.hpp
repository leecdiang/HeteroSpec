#pragma once
// CPU-tested protocol helper. This is not GPU numerical qualification.
// Keep the original scalar (q1) draft decode for every retained last proposal.
#include <limits>
#include <stdexcept>

namespace heterospec_tail {
enum class Outcome { discarded, materialized };

template<class Decode>
Outcome complete_if_retained(int base, int k, int keep, int token, Decode&& decode) {
    if (base < 0 || k < 1 || k > std::numeric_limits<int>::max() - base - 1)
        throw std::invalid_argument("invalid deferred draft-tail extent");
    const int position = base + k;
    if (keep < base + 1 || keep > position + 1 || token < 0)
        throw std::invalid_argument("invalid deferred draft-tail frontier");
    // The last proposed token already exists as an ID, but has not been fed to
    // the draft model. Its KV is needed iff the old commit frontier retains it.
    if (keep <= position) return Outcome::discarded;
    decode(token, position);  // Exception propagates; caller must abort owner.
    return Outcome::materialized;
}
}  // namespace heterospec_tail
