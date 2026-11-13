# Causal trace correspondence fixed before held-out selection

The inherited draft-simple implementation calls `common_sampler_sample(smpl, ctx_dft, i_batch, true)` but discards its returned token. It then sorts the candidate list, sets the actual proposal to `cur_p->data[0].id`, accepts that token and appends it to the draft result. This is visible in the unchanged historical `common/speculative.cpp` around lines320–350.

Accordingly, all raw sampler events and full draft logit vectors are preserved, including the unused intermediate `selected_id`. That unused draft return is not a causal proposal or committed decision and is not required to be identical across independent workers. Its owner, prefix, logit index, raw vector and sorted top scores remain checked. Actual draft proposals, target samples, accepted/correction/bonus tokens, complete outputs, pending ownership and KV reconciliation must correspond. Target sampled IDs are never exempted.

The old-input calibration revealed that PQ/QB full decision-vector byte streams are identical while the discarded draft sampler return can differ. This rule follows the pinned source semantics, not an observed speed or held-out outcome. No sampler, seed, precision, tolerance or native execution path is changed. The complete unfiltered raw events remain available, so the result cannot be described as byte-for-byte identity of every sampler diagnostic field.

The independent raw auditor remains strict about declared byte offsets in the corrected E1 binary. Calibration's incorrect offset metadata is separately retained and explicitly reconstructed from complete append order; it is not silently rewritten or retried.
