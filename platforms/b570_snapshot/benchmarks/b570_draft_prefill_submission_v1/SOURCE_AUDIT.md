# Draft prefill submission candidate

Scientific reference: PR134 commit 51febaddcf49bb18565e568cf964a6e5c78876c9. The separate CPU-thread policy experiment did not establish a practical cost benefit; this candidate retains threads8.

Only draft prompt submission changes: one llama_decode call containing the prompt, instead of one call plus explicit synchronization per prompt token. The configured physical microbatch remains1, batch capacity512, q1 draft arithmetic, original backend DLLs, last-token logits flag, KV types and target implementation.

The runtime llama_kv_cache::init_batch splits a logical batch using the configured microbatch bound. prepare simulates allocations and restores metadata, then process_ubatch applies each physical token. This suggests the original physical key evolution can be retained, but is not numerical qualification by itself. Callback metadata must observe draft PREFILL Qcur with q=1; every retained full target/draft logits vector and the complete state/output trace must match original PR134 bytes before timing.

No query batching is being claimed. Removing repeated API setup and synchronization boundaries may reduce host overhead, but an observed total effect cannot uniquely attribute savings to API setup versus synchronization, scheduler reuse, or backend dispatch. Timed requests omit observers and raw-vector writes.

The four-input qualification is unchanged. The prospective cost screen uses two declared representatives (short CAP and long EOG), three independent processes, identical BASE_A/BASE_B controls and three balanced order rotations. This narrower screen cannot certify a four-input or general workload speedup, and contains no new target-only arm.
