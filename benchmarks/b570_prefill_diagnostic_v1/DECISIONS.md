# Output-affecting decisions, engineering version 1

1. Candidate changes only target prefill UB capacity to 128 and returns to UB1
   continuation. Native logical grouping remains prompt[:-1] then prompt[-1];
   H1 retains common_prompt_batch_decode chunks <=512. These caller differences
   remain disclosed, so UB capacity is not mislabeled as identical backend shape.
2. Pinned state_get/set serializes model identity and memory, not logits or
   sampler. Before transfer, sample the pending first ID exactly once using
   prefill logits. Preserve its scores and all pending logits as raw f32,
   clone the post-sample common_sampler and consume that ID without sampling
   again in the destination. Acceptance occurs at the original loop site.
   Original source context/sampler remains alive; the continuation uses a clone.
   KV before/restored/source-after bytes and positions are retained and compared.
3. Native target context initializes from a separate params copy with candidate
   UB. Original global params stays UB1, including draft context, parameters,
   rollback, k2 and sampler rules. Destination context uses captured original
   target context params. No T1 IDs or evaluator inputs are given to native.
4. Native source is mechanically derived from the retained pinned direct-ID
   speculative.cpp, hash caf649be15a1d3f19a76f7ea72ef0530e2b7f859de6d2a3f715f05c4f620a9cd.
   Its speculative loop, draft own history and legacy overshoot remain intact.
   The collector applies the existing inclusive-first-EOG/cap128 contract and
   retains all raw overshoot. This preserves the original output comparison
   contract; it does not silently redefine native n-predict behavior.
5. Instrumentation callback returns false and observes scheduler graph tensor
   metadata without copying or splitting graphs. embd.ne1 records occupied
   graph token count; result_output.ne1 is selected output count, separately.
   Neither establishes a unique internal Vulkan operation or kernel cause.
   Inputs/positions/sequence/logits selection and native KV mutations are logged.
6. Opaque sampler bytes are unavailable. Pinned common_sampler_clone source,
   chain, seed, accepted history, pending sample and complete behavioral sham
   equality are the available qualification; no bytewise sampler claim.
7. Source-owned sampler must not be freed manually during transfer (its
   common_init_result owns it). This lifetime issue was found by source review
   before G0; move() keeps it alive. No formal data existed at this fix.
8. Initial prepare failed on Windows path-key normalization before any formal
   run. Fixed the dict lookup and strengthened pinned native-source verification.
   Subsequent controller engineering added source/asset drift, duplicate lock,
   independent archive-extraction and protocol-hash tests. ASSET_MANIFEST source
   hashes are refreshed only before formal freeze; all pilot outputs retained.
9. Fetch initially stalled on large historical blobs. A filtered fetch and sparse
   checkout retrieved fixed authority materials. No newer runtime was adopted.

Any implementation correction after FREEZE.json requires an explicit retained
version/amendment and renewed qualification. This controller never auto-edits
source in response to N1 results.
