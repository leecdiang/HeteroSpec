#pragma once
// Admission and execution protocol, not an IEEE equivalence prover.
// Registered evidence is trusted input; no strings or hashes prove semantics.
#include "reference_batching.hpp"
#include <functional>
#include <string>
#include <tuple>
#include <utility>

namespace hs_reference_batching {

enum class EvidenceLevel { none, empirical_replay, structural_assumptions, bit_semantics };
enum class Admission { optimized, scalar, reject, empty };
enum class Reason {
    admitted, empty_request, missing_identity, deployment_mismatch,
    reference_mismatch, unsupported_prefix, inconsistent_prefix,
    unsupported_layout, unsupported_type, unsupported_width,
    unsupported_device, reduction_unknown, reduction_mismatch,
    no_qualification, evidence_too_weak, state_untrusted, state_mismatch,
    invalid_dimensions, invalid_registry, stale_plan, assumptions_unmet
};
inline const char * reason_name(Reason r) {
    switch (r) {
#define HS_REASON(x) case Reason::x: return #x
        HS_REASON(admitted); HS_REASON(empty_request); HS_REASON(missing_identity);
        HS_REASON(deployment_mismatch); HS_REASON(reference_mismatch);
        HS_REASON(unsupported_prefix); HS_REASON(inconsistent_prefix);
        HS_REASON(unsupported_layout); HS_REASON(unsupported_type);
        HS_REASON(unsupported_width); HS_REASON(unsupported_device);
        HS_REASON(reduction_unknown); HS_REASON(reduction_mismatch);
        HS_REASON(no_qualification); HS_REASON(evidence_too_weak);
        HS_REASON(state_untrusted); HS_REASON(state_mismatch);
        HS_REASON(invalid_dimensions); HS_REASON(invalid_registry);
        HS_REASON(stale_plan); HS_REASON(assumptions_unmet);
#undef HS_REASON
    }
    return "invalid_reason";
}

struct DeploymentIdentity {
    std::string backend, device, build, runtime, model, reference;
    bool complete() const {
        return !backend.empty() && !device.empty() && !build.empty() &&
            !runtime.empty() && !model.empty() && !reference.empty();
    }
    auto key() const { return std::tie(backend,device,build,runtime,model,reference); }
    bool operator==(const DeploymentIdentity & o) const { return key()==o.key(); }
    bool operator!=(const DeploymentIdentity & o) const { return !(*this==o); }
};

// Describes actual selected arithmetic, not just nominal weight dtype.
// Backend extractors must provide these fields. Unknown stays unknown.
struct ReductionIdentity {
    std::string quantizer, accumulator, reduction, rounding, dispatch;
    bool complete() const {
        return !quantizer.empty() && !accumulator.empty() && !reduction.empty() &&
            !rounding.empty() && !dispatch.empty();
    }
    auto key() const { return std::tie(quantizer,accumulator,reduction,rounding,dispatch); }
    bool operator==(const ReductionIdentity & o) const { return key()==o.key(); }
};
struct PackingInput {
    uint64_t k=0, output_rows=0, columns=0;
    std::string weight_type, activation_type;
    bool contiguous=false, unbatched_weight=false, singleton_high_dims=false;
    bool all_gpu=false;
    auto key() const {
        return std::tie(k,output_rows,columns,weight_type,activation_type,contiguous,
                        unbatched_weight,singleton_high_dims,all_gpu);
    }
    bool operator==(const PackingInput & o) const { return key()==o.key(); }
};
struct PackingPiece {
    uint64_t column_begin=0, columns=0, group_width=0, groups=0;
    bool packed=false;
};
struct PackingPlan {
    uint64_t k=0, columns=0;
    std::vector<PackingPiece> pieces;
};

// Geometry only. This does not grant numerical qualification.
inline PackingPlan packing_geometry(uint64_t k, uint64_t q) {
    if (!k || q<5 || q>32 || k>uint64_t(std::numeric_limits<int64_t>::max())/q/4)
        throw std::invalid_argument("unsupported or overflowing packing geometry");
    PackingPlan p{k,q,{}};
    uint64_t first=0;
    if (q>=8) {
        first=(q/4)*4;
        p.pieces.push_back({0,first,4,first/4,true});
    }
    for (uint64_t i=first;i<q;i+=4)
        p.pieces.push_back({i,std::min<uint64_t>(4,q-i),std::min<uint64_t>(4,q-i),1,false});
    return p;
}
inline bool valid_geometry(const PackingPlan & p) {
    if (!p.k || p.columns<5 || p.columns>32) return false;
    uint64_t end=0;
    for (const auto & x:p.pieces) {
        if (x.column_begin!=end || !x.columns || !x.group_width || !x.groups ||
            x.columns>p.columns-end || x.groups>32 || x.group_width>4 ||
            x.columns!=x.group_width*x.groups ||
            (x.packed ? (x.group_width!=4 || x.groups<2) : x.groups!=1)) return false;
        end+=x.columns;
    }
    return end==p.columns;
}

// Exact deployment + exact geometry, not broad shape ranges inferred from a
// few captures. The evidence record's contents are an external trust boundary.
struct PackingRequest;
struct PackingQualification {
    DeploymentIdentity deployment;
    PackingInput input;
    ReductionIdentity scalar, grouped;
    EvidenceLevel level=EvidenceLevel::none;
    std::string evidence_id, assumptions;
    bool full_vectors=false, committed_state=false;
    // Evaluated for the CURRENT request, not a precomputed metadata flag.
    // The trusted host must bind actual data-dependent proof preconditions.
    std::function<bool(const PackingRequest &)> validate_assumptions={};
};

class PackingRegistry {
    std::vector<PackingQualification> entries_;
public:
    void add(PackingQualification q) {
        if (!q.deployment.complete() || !q.scalar.complete() || !q.grouped.complete() ||
            q.evidence_id.empty() ||
            (q.level!=EvidenceLevel::empirical_replay && q.level!=EvidenceLevel::structural_assumptions &&
             q.level!=EvidenceLevel::bit_semantics) ||
            !q.full_vectors || !q.committed_state ||
            (q.level==EvidenceLevel::structural_assumptions && q.assumptions.empty()) ||
            (!q.assumptions.empty() && !q.validate_assumptions))
            throw std::invalid_argument("incomplete explicit qualification");
        for (const auto & old:entries_)
            if (old.deployment==q.deployment && old.input==q.input)
                throw std::invalid_argument("duplicate qualification scope");
        entries_.push_back(std::move(q));
    }
    const PackingQualification * find(const DeploymentIdentity & d,const PackingInput & i) const {
        for (const auto & x:entries_) if (x.deployment==d && x.input==i) return &x;
        return nullptr;
    }
};

// A policy identity alone never establishes clean state. The host grants this
// token only from a qualified reference producer or verified full restoration.
struct StateIdentity {
    DeploymentIdentity deployment;
    std::string recipe, prefix_identity;
    uint64_t position=0, generation=0;
    bool clean=false;
};
struct PackingRequest {
    DeploymentIdentity deployment;
    PackingInput input;
    ReductionIdentity selected_scalar, selected_grouped;
    StateIdentity state;
    PrefixRequirements prefix;
    // false by default: finite empirical replay does not prove unseen inputs.
    bool allow_empirical=false;
};
struct PackingDecision {
    Admission action=Admission::reject;
    Reason reason=Reason::missing_identity;
    PackingPlan plan;
    std::string evidence_id;
    EvidenceLevel evidence_level=EvidenceLevel::none;
    // generation and prefix are rechecked at the immediate execution boundary.
    uint64_t generation=0, position=0;
    std::string prefix_identity;
};
inline PackingDecision packing_admission(const PackingRequest & r,const PackingRegistry & registry) {
    PackingDecision d;
    d.generation=r.state.generation; d.position=r.state.position;
    d.prefix_identity=r.state.prefix_identity;
    const auto deny=[&](Reason reason,bool safe_scalar=true) {
        d.reason=reason;
        d.action=safe_scalar && r.state.clean && r.state.deployment==r.deployment ? Admission::scalar:Admission::reject;
        return d;
    };
    if (!r.deployment.complete()) return deny(Reason::missing_identity,false);
    if (!r.state.clean) return deny(Reason::state_untrusted,false);
    if (r.state.deployment!=r.deployment || r.state.recipe.empty() || r.state.prefix_identity.empty())
        return deny(Reason::state_mismatch,false);
    if (r.input.columns==0 && r.prefix.status==PrefixStatus::empty) {
        d.action=Admission::empty; d.reason=Reason::empty_request; return d;
    }
    if (r.prefix.status==PrefixStatus::unsupported_state) return deny(Reason::unsupported_prefix);
    if (r.prefix.status!=PrefixStatus::supported || r.prefix.extents.size()!=r.input.columns)
        return deny(Reason::inconsistent_prefix,false);
    for (auto extent:r.prefix.extents) if (!extent) return deny(Reason::inconsistent_prefix,false);
    if (r.deployment.backend!="cuda" || !r.input.all_gpu) return deny(Reason::unsupported_device);
    if (r.input.weight_type!="Q8_0" || r.input.activation_type!="F32") return deny(Reason::unsupported_type);
    if (!r.input.contiguous || !r.input.unbatched_weight || !r.input.singleton_high_dims)
        return deny(Reason::unsupported_layout);
    if (r.input.columns<8 || r.input.columns>32) return deny(Reason::unsupported_width);
    if (!r.input.k || !r.input.output_rows ||
        r.input.output_rows>uint64_t(std::numeric_limits<int64_t>::max())/r.input.columns/4 ||
        r.input.k>uint64_t(std::numeric_limits<int64_t>::max())/r.input.columns/4)
        return deny(Reason::invalid_dimensions,false);
    if (!r.selected_scalar.complete() || !r.selected_grouped.complete()) return deny(Reason::reduction_unknown);
    const auto * found=registry.find(r.deployment,r.input);
    if (!found) return deny(Reason::no_qualification);
    // Keep a stable copy across trusted predicate invocation.
    const auto qualification=*found;
    const auto * q=&qualification;
    if (!(q->scalar==r.selected_scalar) || !(q->grouped==r.selected_grouped)) return deny(Reason::reduction_mismatch);
    if (q->level==EvidenceLevel::empirical_replay && !r.allow_empirical) return deny(Reason::evidence_too_weak);
    if (!q->assumptions.empty()) {
        try {
            if (!q->validate_assumptions || !q->validate_assumptions(r)) return deny(Reason::assumptions_unmet);
        } catch (...) { return deny(Reason::assumptions_unmet); }
    }
    d.plan=packing_geometry(r.input.k,r.input.columns);
    d.action=Admission::optimized; d.reason=Reason::admitted;
    d.evidence_id=q->evidence_id; d.evidence_level=q->level;
    return d;
}

// Stateless operator callback boundary for a host adapter. This does not
// append tokens or commit KV. Stateful execution uses the checkpoint owner. The host must bind the exact frozen
// scalar deployment and serialize access. This API is not a GPU implementation.
// Failed execution taints state even if no mutation was reported. Restoring is
// never inferred from a graph-key change; host verification is mandatory.
struct ExecutionResult { bool success=false; bool optimized=false; Reason reason=Reason::state_untrusted; };
inline ExecutionResult execute_operator(const PackingRequest & request,
        const PackingRegistry & registry, StateIdentity & live,
        const std::function<bool(const PackingPlan &)> & optimized,
        const std::function<bool()> & scalar,
        const std::function<bool()> & verify_committed_state) {
    const auto d=packing_admission(request,registry);
    if (live.deployment!=request.state.deployment || live.generation!=d.generation ||
        live.position!=d.position || live.prefix_identity!=d.prefix_identity ||
        live.recipe!=request.state.recipe || !live.clean)
        return {false,false,Reason::stale_plan};
    if (d.action==Admission::reject) return {false,false,d.reason};
    if (d.action==Admission::empty) return {true,false,d.reason};
    if (live.generation==std::numeric_limits<uint64_t>::max()) return {false,false,Reason::invalid_dimensions};
    live.clean=false; ++live.generation;
    // A callback may accidentally write the shared identity. Every noncommit
    // exit must restore taint, including false returns and exceptions.
    struct TaintOnFailure {
        StateIdentity & state; bool committed=false;
        ~TaintOnFailure() { if (!committed) state.clean=false; }
    } transaction{live};
    try {
        const bool ok=d.action==Admission::optimized ? optimized(d.plan):scalar();
        if (!ok || !verify_committed_state() || live.deployment!=request.state.deployment ||
            live.position!=request.state.position || live.prefix_identity!=request.state.prefix_identity ||
            live.recipe!=request.state.recipe || live.generation!=request.state.generation+1)
            return {false,d.action==Admission::optimized,d.reason};
        live.clean=true; transaction.committed=true;
        return {true,d.action==Admission::optimized,d.reason};
    } catch (...) { // Preserve taint; the owner may restore a separately verified checkpoint.
        throw;
    }
}
} // namespace hs_reference_batching
