# Qwen3-14B Q8 migration: reference counterexample

Status: **REFERENCE_COUNTEREXAMPLE**, 2026-11-01. PR155 was executed on the
Windows RTX host. Preparation, native compilation, the first capacity rung and
all40 pilot requests completed. The pilot failed the shared-reference gate;
120 qualification,288 measured and288 warmup requests were not started.
No performance estimate is admissible.

## Deployment and admission

Official14B Q8 target SHA256
`a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d`,
15,698,533,728bytes; original0.6B Q8 draft
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Actual geometry40layers,40/8heads,d128. Original authenticated source capsule
and all21 pinned numerical DLLs were retained. New worker SHA256
`db4bc97fef83f7ff2204ba76f58958b55339a96f998049ff245f0ff60beed516`;
see BUILD.json and HOST_SOURCE_REVIEW.json for full identities.

RTX5070Ti Laptop12GB, Core Ultra9 275HX,48GB RAM, driver616.92;
24threads, context1024, cap128/EOG, k3, F16KV, non-flash, fixed resident pools.
Target offload parameter24 passed without trying20/16. This pinned core counts
the output layer in that parameter: weights for layers0–16 are CPU-resident,
17–39 and output40 are GPU-resident; draft is fully offloaded.
All pools left22,248,693,760bytes available RAM and1,507,852,288bytes free VRAM,
above the8GiB/1GiB thresholds. Native admission returned normally, owned count0.

Actual QK compute placement is unresolved. The observer records buffer-type
device ownership, not scheduler execution backend; the pinned CUDA_Host buffer
type also identifies the NVIDIA device (ggml-cuda.cu:1297–1326). Thus the v1
closeout's all-GPU interpretation was unsupported. The original auditor's
weight-to-QK inference was also unsupported and remains failed in PILOT_AUDIT.json.
Correction v2 verifies weight logs and 40-layer QK/GQA shapes separately without
claiming CPU or GPU compute coverage. The original archive and v1 interpretation
are preserved; CLOSEOUT_CORRECTION_V2 supersedes only the interpretation and
derived closeout reports. This unresolved placement is an additional gate failure.

## Complete pilot outcome

Pilot ran21:37:07–21:45:37 Asia/Shanghai,40/40 completed in one owned process.
Every R heavy/off pair repeats; every candidate heavy/off endpoint, transaction
and final logical bounds agrees. First divergence indices below are zero-based.

| Existing input | M_PQ / M_QB versus R | C_PQ / C_QB versus R |
|---|---|---|
| MBPP/123 | preserve | preserve |
| MBPP/140 | preserve | preserve |
| GSM8K/test/111 | fail at16:576→3070 | preserve |
| GSM8K/test/120 | fail at82:6291→12478 | fail at82:6291→12478 |

Both heavy/off runs show the same counterexamples. The full-vocabulary
decision rows at the first divergence have identical natural token prefixes
to R. FIRST_DIVERGENCE_VECTORS.json pins their files, top-two logits and margins.
For GSM8K/test/111, the M winner3070 exceeds576 by0.0008277893; R instead selects
576 with margin0.0308647156. This confirms a real greedy rank reversal, not
a JSON/text-comparison artifact. No operator-level causal claim is established.

Independent reconstruction checked3,059 complete151,936-float vectors, all
finite, all recorded greedy decisions, complete speculative transactions and
all target/applicable draft state artifacts. Across all eight input×path
PQ/QB pairs, endpoints, recorded logical work, full captured logits, final
target state and applicable draft state are byte-identical. **PQ/QB mutual
correspondence does not imply preservation of the UB1 R reference.**

## Budget, cleanup and scope

Actual/charged requests40/800; engineering recovery requests0/64. One
zero-generation admission; total owned native time528.516seconds, including
18.485seconds admission and510.031seconds pilot. All failures and initial
audit refusals remain. No model, reference, panel or precision replacement ran.

The selected12-input natural prospective panel remains unexposed to14B output.
UNSTARTED_SLOTS.json in the raw bundle enumerates all696 dependent slots.
No selected-subset timing, synthetic success or speedup is reported. Host
telemetry is sampled every10seconds: minimum available RAM15,314,792,448bytes,
maximum sampled GPU temperature72C. Sampling is not an instantaneous peak
guarantee; provisioning memory is separately retained. Both owned processes
ended with active count0, GPU compute inventory is empty and the lock is gone.

The original freeze is preserved, and STATE.json closes the study. No further
requests are queued. See PAPER_ADDENDUM.md, INDEPENDENT_RECOMPUTE.json,
RECOMPUTE_PROVENANCE.json and the delivered RAW_ACCESS index for audit access.
