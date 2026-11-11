#pragma once
// Reuse #64's bind/reserve mechanism through an original-host supplied callback.
// This wrapper does not implement or certify llama's private runtime mutation.
#include <cstdint>
#include <stdexcept>
#include "cost_clock.hpp"
namespace b570_econ {
struct Snapshot { const void* context; const void* kv_owner; std::int64_t lo,hi; std::uint32_t width; };
template<class Observe,class Bind> void bind_phase(std::uint32_t wanted,Observe observe,Bind bind){
 if(!wanted)throw std::invalid_argument("zero phase width");
 const auto before=observe();if(!before.context||!before.kv_owner)throw std::runtime_error("unbound owner");
 if(before.width!=wanted)b570_cost::measure(b570_cost::Phase::phase_bind,[&]{bind(wanted);});
 const auto after=observe();
 if(after.context!=before.context||after.kv_owner!=before.kv_owner||after.lo!=before.lo||after.hi!=before.hi||after.width!=wanted)
  throw std::runtime_error("phase binding changed ownership/positions or wrong width");
 // Positions/identity are necessary checks, NOT evidence that KV bytes are equal.
 // Byte/frontier/pending checks run offline against the original R.
}
struct CycleWork {std::uint64_t logical_verifies=0, occupied_graphs=0, occupied_rows=0, proposals=0, accepted=0;};
// Physical work must be filled by actual scheduler observations. A caller width
// of two is not evidence of one occupied width-two target micrograph.
}
