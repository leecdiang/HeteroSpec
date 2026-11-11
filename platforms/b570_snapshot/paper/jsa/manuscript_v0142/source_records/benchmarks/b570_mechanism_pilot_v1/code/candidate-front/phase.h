#pragma once
#include "llama.h"
#include "observer.h"
extern "C" __declspec(dllimport) void llama_b570_pilot_bind_phase_ubatch(llama_context *, uint32_t);
inline pj pilot_phase(llama_context * ctx, prefill_observer & o, uint32_t ub, int pending) {
    auto p=prefill_observer::positions(ctx);auto old=llama_n_ubatch(ctx);
    std::vector<uint8_t> before,after;
    if(o.instrument)before=prefill_observer::state(ctx);
    llama_b570_pilot_bind_phase_ubatch(ctx,ub);
    if(o.instrument)after=prefill_observer::state(ctx);
    if(p!=prefill_observer::positions(ctx)||llama_n_ubatch(ctx)!=ub||(o.instrument&&before!=after))throw std::runtime_error("Phase binding changed KV");
    o.bytes(".phase_before.kv",before);o.bytes(".phase_after.kv",after);
    return {{"source_ub",old},{"destination_ub",ub},{"positions",p},{"same_context",true},{"pending_id",pending},{"capture_state_bytes",before.size()},{"capture_kv_equal",o.instrument?pj(before==after):pj(nullptr)},{"opaque_sampler_bytes","unavailable; same live sampler, no serialization"},{"state_transfer",false}};
}
