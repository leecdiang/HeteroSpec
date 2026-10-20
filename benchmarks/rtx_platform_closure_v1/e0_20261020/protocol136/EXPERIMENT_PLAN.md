# RTX platform closure v1 — protocol

Status: prospective design only. No calendar finish time or wall-clock kill deadline is part of this protocol.

## 1. Questions

H1 — Under a frozen RTX runtime and fixed inputs, target-only R, serial per-query speculative attention PQ, and query-to-batch QB preserve the registered native endpoint and speculative state protocol.

H2 — QB has a practical complete-service advantage over two identical PQ controls after A/A noise is considered.

H3 — The chosen speculative service does or does not repay draft cost relative to target-only R. This is separate from H2.

H4 — The request actually executes q>1 on target verification. Phase fields describe software execution but are not GPU critical-path fractions without a dependency timeline.

## 2. Frozen domain

### Platform and models
Use the already-qualified RTX native runtime and one already-qualified target/draft pair, preferably the Qwen pair from the existing fixed panel if exact model files, quantization, tokenizer, executable, DLLs and reference can be recovered unchanged. If not, stop at E0 and document the mismatch. Do not silently substitute another build.

Pin executable/DLL and build hashes, GPU/driver identity, model/tokenizer hashes, sampling and EOS/EOG rules, KV type, context/ubatch settings, graph mode, environment and source identity. No code or binary may differ across arms.

### Inputs
Freeze four previously exposed RTX input-ID sequences before new candidate timing. Include prompt-length spread and a historical positive/weak case if supported by prior data. Publish immutable IDs or manifest references, token count, task identity and exposure status. This is a finite panel, not unseen-input validation.

### Speculative policy
Freeze one proposal per cycle (k=1), but do not assume configured k guarantees q=2. Record actual caller rows, active rows, physical q, visible mask keys, physical key extent, layer, Hq/Hkv, d, dtype, strides, mask, placement, proposal/accept/reject/correction/bonus events and KV updates. If q>1 is not observed, report it as not observed; do not substitute a synthetic micrograph.

Keep historical tokenizer, greedy rule, output cap, pending-logit, correction/bonus and KV-trim protocol. Any necessary change to the output window or runtime requires a new prospective reference.

## 3. Arms and estimands

| Arm | Definition | Purpose |
|---|---|---|
| R | Target-only decode under same target reference; keep draft weights resident if needed to control memory state | Speculative economics |
| PQ_A | Existing serial per-query speculative path | Identical control A |
| PQ_B | Exact same PQ implementation, independently invoked | A/A noise control |
| QB | Existing phase-scoped query-to-batch path | Candidate |

Do not include QH_C, padding, selectors or a new architecture arm.

Primary service ratio per input/session: service(QB) / mean(service(PQ_A), service(PQ_B)). The primary timer starts before fresh-context creation/graph reservation and ends after complete output/state handling, synchronization and context teardown. Shared model loading is recorded separately. Publish request-only time as secondary.

Secondary speculative-economics ratio: service(QB) / service(R). Also publish PQ/R descriptively; do not select a favorable baseline after seeing data.

### Practical screen
Use the established 2% engineering threshold, with all conditions required: (1) all reference, endpoint and state gates pass; (2) equal-input geometric-mean QB/dual-PQ service reduction exceeds max(2%, largest input-aggregate absolute PQ_A/PQ_B imbalance); (3) QB is faster than dual-PQ in every process-session aggregate; (4) all inputs and blocks remain visible and no post-hoc outlier removal occurs.

This is an engineering screen, not a significance or equivalence test. Failure means NO_ESTABLISHED_PRACTICAL_LAYOUT_BENEFIT, not “equivalent”. Separately classify whether QB repays draft cost on this panel. Do not generalize beyond it.

## 4. Ordered gates

### E0 — source/reference/resource audit (read-only)
Recover exact runtime, model, tokenizer, executable and DLL identity; existing R/PQ/QB endpoint/logit/state traces; KV and microbatch settings; GPU/driver identity and potential background load; existing RTX ledger and a new study UUID. Mark each field KNOWN, MISSING or INCOMPATIBLE. If historical reference binding is missing, do not call a replacement historical.

### E1 — qualification and actual geometry
For each of four inputs, qualify R, PQ and QB with full raw capture outside timing. Preserve native IDs, EOG/EOS flags, length, terminal token, stop reason; every decision-relevant target/draft logits vector including rejected verification rows; complete proposal/accept/reject/correction/bonus, pending-logit and KV trace; QK/softmax/AV outputs where exposure does not alter compute; actual q, visible/physical keys, Hq/Hkv, d, dtype/strides/mask and placement.

Native endpoint equality is necessary but does not replace logits/state qualification. If a candidate mismatches, stop that candidate before timing, preserve evidence and do not relax byte equality post hoc.

### E2 — clean balanced service panel
Run four independent native process sessions. Each session covers four inputs × four arms (R, PQ_A, PQ_B, QB), for 64 measured requests total. Add one explicit warmup per input/arm/session (64 warmups total); report and charge them separately. Warmups must pass endpoint/state checks.

Freeze a rotating order for arms and inputs before timing so no arm always receives first-use/cache position. A failed slot stays failed; no scientific retry. Each measured request is checked after the timer against the qualified endpoint and cycle trace. Full-logit qualification occurs in E1; do not add observer reads or raw-file writes to E2 timed paths.

This is a finite panel, not a population estimate. If A/A or background interference is unstable, retain all blocks and mark the screen unresolved; propose a separate preregistered follow-up rather than improvising.

### E3 — sparse diagnostics (conditional)
Only after E2, if phase attribution could change interpretation, collect a separately charged sparse profile of one fixed PQ and one fixed QB request per input. Use clean/profile/clean observer calibration. Verify terminal interval, output projection and active-node counts. If observer perturbation or integrity fails its preregistered gate, reject it as a quantitative attribution tool.

Do not substitute profiled times for clean service, call a GPU subtotal the critical-path share, or use Amdahl's law unless a dependency timeline establishes a serial non-overlapping fraction.

### E4 — platform closure
Close the finite RTX panel when E0–E2 have explicit dispositions and E3 is completed or documented unnecessary/unavailable. Report reference/endpoint qualification; whether real q>1 was observed; QB versus dual-PQ screen; QB versus target-only economics; observer limits; and whether a physical bottleneck is identified.

A target-verification delta alone is not a hardware opportunity. If full-service gain is below threshold or speculation does not repay draft cost, preserve the software result and close this branch without an accelerator claim. Only a robust residual can motivate a separately preregistered physical intervention.

## 5. Stop and accounting rules

Preserve historical failures, stops, UUIDs, source identities and ledgers. No reference replacement, input removal, arm substitution, output-cap change, DLL change or tolerance relaxation after results. No automatic retry. A repaired candidate gets a new source/build identity and qualification. Stop a candidate at the first reference mismatch or unsupported geometry; continue another arm only if preregistration permits it.

Before E2, register complete native-process/request budget including build, load, warmup, qualification, timing, optional profile, failures, cleanup and packaging. Keep model-load time, process lifetime, request service and GPU-active time separate. Do not transfer B570 budget values to RTX.

There is no clock deadline. Complete registered gates or record an explicit resource/engineering stop; do not turn a time-limited stop into a scientific PASS/FAIL. No actor, RTL, PPA, new accelerator, QH/padding/selector or B570 patch is authorized here.

## 6. Required result artifacts

The separate result PR must include frozen PREREGISTRATION.json and DESIGN_SHA256.json; E0 identity/reference/resource inventory; qualification tables and raw vector/logit manifests; native endpoint and cycle traces; actual-geometry table; full timing table including every arm/input/session/warmup/failure; A/A and paired-ratio analysis script; observer evidence if E3 runs; process receipts, exit/cleanup, ledger and raw archive hashes; and a paper addendum that separates layout value from speculative economics.
