# B570 FINAL CAUSAL CLOSEOUT — NORMATIVE, PROSPECTIVE EXPERIMENT PROTOCOL

Status: DESIGN ONLY. This PR commits a preregistered **conditional** experimental design; **zero new GPU model forwards are performed by this PR**. Execute on the real Intel Arc B570/Vulkan host only, publish raw results in a separate stacked Draft PR.

## 0. Authority, immutable facts and aim

**Exact design parent:** PR #99 head c0e16aff9f3eeb0e677a52fcdc092068c096bf5d (B570 external Prefill partition causality), itself stacked on PR #97 5a66653bd0ce413d4eb9aef3a4501b93c138071b, audited PR #93 and experimental PR #92. Read the actual frozen source capsules rather than inventing interface signatures.

Inherited real host: Intel Arc B570 PCI 8086:E20C, native Vulkan0; Llama-3.2 target GGUF Q6_K, target-only in PR #99 (no draft); for optional P3 only, matched Llama-3.2 1B Q4_K_M draft/k1 from PR #92/97. Context 1024, logical batch 512, 10 threads, F16 KV, non-Flash attention, single sequence, greedy sampler, cap128. Pin the **actual** full model GGUF SHA256, all numerical DLLs, build/compiler/driver/runtime hashes, prompt native IDs, native API ABI, output reservation and source commit. Never assume third-party version sameness from filenames. At least 512 MiB same-PID signed dedicated GPU budget headroom required for each loaded actor; GPU weight/KV placement must be checked; **continuous physical residency stays UNKNOWN** unless same-scope proof actually exists.

**Existing PR99 proof:** fixed UB512/capacity1, external one-caller Prefill A vs split128+rem B; UB128 one-caller C internally splits128+rem. For exposed GSM8K/test/1248 (161 prompt IDs) and /831 (133 IDs), A != B in complete output (first index47/81), B = C in complete output AND bitwise full FP32 prefill logits and source-defined 64 K/V tensor payloads. Two stable >128 prompts (/1011 length190, /1249 length163) have A/B numerical-state differences **without** final-output difference. Same-prefix ID127/128 are unchanged; ID129 differs first at57. All 63/63 historical new requests complete. PR99 intervention includes unavoidable per-caller queue/scheduler handling, so its result does NOT isolate a Vulkan kernel as sole cause, prove KV mediation, identify first divergent op or partition-independent timing. Preserve all historical negative and null observations.

**Stock gate remains failed:** original #92 R_stock (UB128) is not equal to R_prod/M_match/C_k1 on the two historical GSM tasks. That original stock-relative qualified speedup remains NULL even if later post-hoc R_prod=M_match=C_k1 paid costs are negative (R_prod/C=0.719264; M/C=0.727927, 24/24 task regressions). These are two **different reference contracts**. Don't rerun historical 1200 paid slots or rebase a failed qualification to make a positive claim.

**Questions, not conclusions:**
- H1 — Does controlling both external partition and internal physical work refine which execution geometry/caller factors are necessary for PR99's observed output/state difference?
- H2 — Under bitwise-controlled logical-input alignment, at which native layer/op does numerical difference FIRST arise, and does a matched-input operator replay reproduce any differing output?
- H3 — Is retained prefill KV a causal source of delayed differences, separately from first-sample logits, under a **validated complete resumed-context contract**? A successful own-path restoration is the hard gate; partial sequence-KV restore alone cannot pass.
- H4 (OPTIONAL) — Can completed GPU timestamps attribute exclusive/overlapping work without changing official paid request latency, or must stage-wall remain UNKNOWN?
No claim in this protocol guarantees a positive or identifiable result.

## 1. Strict execution order and prospective freezes

**F0-BASE, BEFORE ANY NEW FORWARD:** Read source and complete existing evidence for #99/#97/#93/#92, inspect actual device/driver/models/hash, and audit all proposed hook APIs. Produce `F0_BASE.json` with exact pinned bytes and hashes, actor and condition inventory, fixed input native IDs/hashes, commands/build options, phase semantics, output/EOG criteria, geometry and memory guards, observer behavior, allowed implementation edits, and every budget gate. Push/commit and **read back authenticated actual GitHub blobs** before first new request or diagnostic forward. A zero-forward model load is allowed only after actor pins are authenticated and is charged to the global starts ledger as a probe.

**F0-P1:** Before P1 request #1, freeze exact new D/sweep/operator coordinates and exact selection of observable logical tensor positions, first-difference thresholds and capture limits; authenticate remote blobs. No choosing after seeing A/B/C output, tensor differences or performance.

**F0-RESTORE:** Before any attempted KV or logits import, independently confirm source-level retained-state boundaries. Declare precisely serialized fields, omitted fields, reset/reconstruction of outputs, sampler/pending, KV ownership, scheduler, sequence positions, output slots and synchronizations; define OWN-path shams and invalid-state injection rejection tests. If complete contract cannot be implemented/verified within budget, record `FULL_STATE_RESTORE_NOT_ADMITTED` and **do NOT run cross-state arms**. The other independent stages continue.

**F0-P3 (optional):** Before GPU timestamp experiment, inspect VK queue family timestampValidBits, timestampPeriod, calibrated/regular query support, actual stage boundaries, delayed completion/fence semantics, profiler overhead and safe byte caps. If unavailable, `GPU_TIMELINE_NOT_AVAILABLE` and stop P3 only.

After each gate, retain initial freezes byte-for-byte. Corrections, if absolutely required for build/resource safety, use an authenticated versioned amendment **before any affected previously unstarted test**, identify prior valid slots and scope, no timing/result-driven hyperparameter/panel change and no retry of charged scientific requests. Do not turn a post-hoc alternative into a preregistered experiment.

## 2. P1-A: fourth-arm caller/physical-geometry control (21 new whole requests)

Use all exact PR99 seven exposed input IDs and the original pinned Q6 numerical DLLs. Four conceptual arms:
- A: Context UB512, capacity1, **one** full-prompt caller; physical e.g 161 for ID161.
- B: Context UB512, capacity1, external chunks 128+remainder; physical e.g 128+33.
- C: Context UB128, capacity1, **one** full-prompt caller; native internal micrographs e.g 128+33.
- **D (NEW)**: Context UB128, capacity1, explicit external chunks 128+remainder; physical e.g 128+33. For prompt length <=128 use a single caller and declare the no-split negative control.

Do **not rerun A/B/C as new paid science**: compare D to immutable #99 per-task complete native arrays, exact time-independent payload hashes and prefill state. Run **7 inputs × 1 new arm D × 3 fresh-worker repeats =21 started requests**, rotated deterministic order; repeat0 capture-off, repeats1/2 bounded capture-on. If D is ineligible due to true submission/graph constraints, mark D unavailable, don't improvise equivalent geometry. All paths request logits ONLY on the final absolute prompt token; D's intermediate chunk has logits=false at all rows. Contiguous positions, natural first sample and subsequent single-token continuation are mandatory. Compare full FP32 prefill logits+serialized sequence K/V payload, complete native output/EOG/length/terminal/stop, actual successful graph width history, tensor placement.

Interpretation:
- B=C=D bitwise state + full trajectory on observed cases supports sufficiency of shared **observed partition recipe**, not proof of kernel-only causality; scheduling differences may be numerically inert or unobserved.
- C!=D despite equal measured physical widths demonstrates caller-boundary dependence.
- Different output with equal recorded prefill KV/logits demands investigation of omitted state/caller effects; do not silently upgrade hashes to full-state equivalence.

## 3. P1-B: partition-position sweep (38 new whole requests)

Freeze **exact** per-input caller schedules below on the existing four historical inputs and a pre-exposed 129-ID synthetic prefix of GSM/1248. Keep Context UB512, capacity1, target-only, same final-only logits, contiguity, unchanged continuation and pinned model. Two fresh-worker repeats per schedule, one capture-off and one bounded capture-on. This is a **diagnostic** sweep, not a blind cohort nor a tuning campaign.

| Input (native IDs pinned from PR99) | Prompt N | Four registered NEW schedules (caller token lengths) |
|---|---:|---|
| GSM8K/test/1248 |161|64+64+33 ; 96+65 ; 128+33 ; 160+1|
| GSM8K/test/831 |133|64+64+5 ; 96+37 ; 128+5 ; 132+1|
| GSM8K/test/1011 (stable) |190|64+64+62 ; 96+94 ; 128+62 ; 160+30|
| GSM8K/test/1249 (stable) |163|64+64+35 ; 96+67 ; 128+35 ; 160+3|
| FIXED_PREFIX_1248/129 |129|64+65 ; 96+33 ; 128+1 (only three)|

**Arithmetic:** 4×4×2 + 3×2 = **38 new whole requests**. The 128+remainder schedules are exact diagnostic replications of a **previously seen** B configuration; label them EXPOSED_REPLICATION, not new discovery. All starts charge budget and are never overwritten. Record complete A/C immutables from #99 and the physical width histogram/number of external callers and source-defined full prefill FP32/KV hashes for each sweep arm. Report no-trigger and differences, no monotonic or threshold guarantee, no model-answer accuracy claim for cropped prefix. Partition includes caller count/queue semantics; physical width alone is not an isolated randomized factor.

## 4. P1-C: native first-divergent-op localization and fixed-input replay (≤18 additional whole requests)

Use two registered affected cases GSM1248/831 ONLY, with original pinned A/B/C conditions. Replay/capture enough source-bound logical positions to observe post-prefill/final-position state, the token immediately before/after the internal 128 boundary, and layer0, then later layers only **as triggered by a frozen forward source-traversal rule**. Do not infer from #99's 64/64 differing K/V that Attention itself is the FIRST cause: layer0 input/norm/QKV projections can already differ.

For each native layer traverse actual graph dataflow in a fixed order: (embedding/layer input) → RMS norm → Q/K/V projections → QK or equivalent attention scores → mask/softmax → attention AV/output → residual → FFN. For each comparable intermediate pair: actual op name, dtype, logical position mapping, q/head/GQA, ne/nb strides, masks, KV positions, buffer identity, exact input bytes/hash, first divergent element, count of unequal elements, max-abs/max-rel and bitwise state. Only compare semantically aligned logical rows; split chunks cannot be byte- compared by raw buffer order.

**Fixed-input operator replay:** when A/B differ, capture Q/K/V/mask AND upstream operands; run two physically different admitted graph geometries under the **same frozen operand values** to distinguish current operator geometry from upstream-state inheritance. Include same-arm replay and bitwise source-input readback. If equivalent kernel/operator paths cannot be reproduced, report `OPERATOR_CAUSAL_ISOLATION_UNRESOLVED`; native tensor first-difference location may still be reported but not a unique numerical kernel cause. Record actual Vulkan dispatcher/selected pipeline/shader and, where supported, dispatch dimensions (a ggml graph-node label does not prove the GPU instruction schedule). Capture-on/off full endpoint shams mandatory. Per-arm operational crashes/over-budget capture stop only this diagnostic endpoint, never eat the earlier PR99 conclusion.

**Maximum:** 2 cases ×3 native arms ×up to 3 extra capture repeats =18 new whole requests; up to **72 GPU-only fixed-operand operator replay starts** (separately counted; no official paid wall claim); independent source payload budget <=512 MiB NEW total for P1-C, enforced synchronously **before each append/write**. No unbounded vkCmdDispatch API dumping or polling-based overrun of an asynchronous large file. If under instrumentation some tensor cannot be captured, report UNKNOWN per operator rather than synthetic zero differences.

## 5. P0 / P2: qualified retained-state intervention (P0 ≤16 + P2 ≤40 new whole requests)

**CRITICAL:** PR97 source inspection proved `state_write_data` stores model architecture + memory-module state, and sequence serialization stores memory state only. They do not by themselves serialize dynamic logits/output, frontend committed prefix/pending token, sampler ownership or scheduler/queue state. PR99's full FP32 logits and K/V raw payloads help diagnosis but **are not an authenticated complete context restore**. Safe restore requires implementing and validating all changed necessary state boundaries; no arbitrary pointer copying, fabricated model outputs, cross-model edits or future-reference token forcing.

**P0: own-path restoration admission ≤16 requests.** Use the two affected tasks plus two stable long controls from #99, with A and B donor prefill recipes; perform at most 4 inputs × 2 donors × 2 repetitions =16 full original-own-path restoration shams in clean receiver contexts (or same process independently initialized equivalent contexts). Verify all full original native outputs, EOG/stop/terminal, prefill and post-restore KV bytes/logits bytes, first continuation row, positions, sampling provenance, scheduler/output geometry and no extra forward. Compare to a separate un-restored own-path natural execution from immutable #99. At least one alternate-run capture-off native output guard required. Any aliasing/unsafe restore, lack of required output/logits injection or non-matching sham -> `RESTORE_GATE_FAILED` and **skip all P2 donor-cross rows**. A single no-op native bind guard does **not** count as restoration.

**P2 2×2 donor-KV × first-output-logits** only if full restore admission PASS:
- AA: donor A KV, A full initial FP32 logits.
- AB: donor A KV, B full initial FP32 logits.
- BA: donor B KV, A full initial FP32 logits.
- BB: donor B KV, B full initial FP32 logits.

All use the **same** subsequent continuation semantics, same target owned context+sampler, full output capacity and pending-token rules; sampler chooses first natural greedy top1 from the injected source logits and consumes it once, no forced future suffix or recorded answer. Preserve a separate immutable register of natural AA/BB un-restored outcomes. Run the two known divergent cases ×4 cells ×3 fresh repetitions = **24 new whole requests**; two long stable controls ×4 cells ×2 repetitions = **16 new whole requests**. **Total ≤40**. Freeze complete-cell order balanced by task and session. Include A and B donors' exact first top1 (historically both 1271 on affected cases). Since A/B logits choose the SAME greedy initial top1 for those cases, swapping only initial logits is a **negative control** for the first decision in greedy decoding; it does not by itself identify a future logits-mediated effect. The primary estimand is any change **by KV source under the validated other-state-equal continuation**. A/AB and BA/BB matching with AA!=BA supports conditional KV-mediated suffix sensitivity, but not universal sufficiency/necessity of KV state or all backend hidden state. If changes follow other state/receiver geometry, record as interaction/UNRESOLVED.

Extra hard gates: source-defined complete sequence KV import at exact logical positions, full FP32 output-slot/logits import or explicitly equivalent native sampler execution, no hidden forward, context ownership and sampler/pending obligations, reference full endpoints, receiver geometry identical, source-state shams for EACH donor, every native result complete. Failure in a single invalid donor class blocks the full factorial causal inference; do not retain favorable isolated cells as causal proof. No post-outcome arm substitutions. Store all raw K/V and full logits for import validation with SHA and native payload match. A proof that KV differs at prefill is NOT proof the difference mediates all later outputs.

## 6. P3 OPTIONAL — measured GPU timeline and physical-work accounting (≤18 new whole requests)

P3 is **not a prerequisite** for submitting the scientific paper. If source+driver capability preflight admits real command-buffer GPU timestamps and completion, use 3 immutable exposed inputs (GSM1248, GSM831, stable GSM1011) × three **existing** original recipes R_prod, M_match, C_k1 × two sessions = **18 new instrumented requests**, predeclared balanced order and outputs/counters. Pin old Q6 target + Q4 draft/k1/UB1 physical verify/old phase binding, complete output contract and actual model/driver DLL hashes. Do not change model, quantization, k or runtime to force profitability. Preserve original #92 paid metrics separately; these 18 heavy instrumented timings are NOT comparable paid request ratios.

Measure actual **completed GPU** queue intervals with Vulkan timestamp query only if timestampValidBits>0 and query/fence/resource barriers and calibration/pass-completion gates succeed on this host. Track periods with timestampPeriod; record queue, command buffer, timer scope, completion marker and observer overhead. Avoid assuming asynchronously overlapped GPU/CPU/draft/target phases add up; overlapping events require an explicit timeline, not naive sum. If not supported, record `GPU_TIMELINE_NOT_AVAILABLE`, old `MODEL_TIMING_UNAVAILABLE` stays true. Source counters (target width1, two physical micrographs/cycle, draft proposal/catchup) remain separate from shader dispatch and exclusive stage wall. API logging from #97 once overshot 128MiB; never repeat an unbounded trace. Enforce hard synchronous byte cap ≤64MiB for optional P3 metadata. Do not try alternative profilers indefinitely.

## 7. Global cap, zero retries, output contract, evidence package

**Registered NEW request ceiling by stage:** P1-A=21, P1-B=38, P1-C≤18, P0 shams≤16, P2 cross≤40, P3 optional≤18. Sum maximum planned native whole requests = **151**. Engineering/load/failed-start contingency ≤49, so **ALL NEW request starts including failures/warmups/engineering ≤200**, plus at most 8 explicitly counted zero-forward load probes; operator replay starts ≤72 separately charged. **Total owned B570 GPU-process lifetime ≤6 hours**, all processes PID-owned with capped memory and disk. No native-science retries: a started formal/diagnostic registered coordinate is terminal even on failure; follow-up can continue only previously unstarted and independently admissible slots. No extension just because budget remains. If full admitted grid cannot fit, freeze deterministic stage/row reduction *before* any new P1/P2 native outputs; do not shorten based on observed favorability. P3 always drops first.

A complete output comparison uses **all native token IDs, EOG per ID, length, stop reason, final token, cap and prompt ID hash**, with repeated same-task reference stability and actual EOG-vs-CAP semantics. Report input exposure and synthetic-prefix status accurately. Original stock gate remains NULL, posthoc equal-output negative cost remains descriptive, and no new paid cost speedups are claimed for diagnosis.

Capture-off and capture-on tests must agree in FULL native endpoints; capture cost is never subtracted from a paid timer or reported as one. Preserved PID, Vulkan0 weight+KV placement, no CPU fallback, ≥512MiB headroom. Kernel dispatch, KV mediation, full-state cloning, completed stage wall and continuous physical residency **must have separate verdicts**: SUPPORTED / REFUTED / UNRESOLVED / NOT_ADMITTED. A failed gate may null one specific hypothesis; independent valid evidence remains reportable.

**Deliver in ONE new result subtree** `benchmarks/b570_final_causal_closeout_v1/`:
- `F0_BASE.json`, `F0_P1.json`, `F0_RESTORE.json`, optional `F0_P3.json`, authenticated GitHub blob receipts and amendments;
- `PARTITION_MATRIX.json`, `OPERATOR_FIRST_DIFF.json`, `FIXED_INPUT_REPLAY.json`, `STATE_RESTORE_ADMISSION.json`, `KV_LOGITS_CROSS.json`, optional `GPU_TIMELINE.json`;
- `RAW_EVIDENCE` content-address index, exact native source/models/GGUF/DLL/driver/ABI hashes, capture-off native IDs, observer checks, crash/log truncation evidence, request-start and process/byte/seconds ledger;
- `QUALIFICATION.json` keeping original stock-relative NULL plus separate exposed intervention contrasts and historical posthoc pairs;
- `RESULTS.json` and `RESULTS.md` with conclusions/missing/negative/blocked paths, per-input tables and explicitly allowed paper wording;
- Standalone stdlib **independent** CPU validator that imports no executor, recomputes the whole new grid from unmodified raw payloads, checks source/native arrays and numeric tensor equality, bounded byte budgets, failure ledger and old-PR anchor, with synthetic malformed-evidence rejection tests;
- actual local archive restore and **fresh authenticated GitHub full-byte restoration** with independent rederivation and exact output equality. No metadata-only claim; GitHub references to externally stored source/weight bytes must verify actual SHA. If archive upload cap imposes chunks, provide length+SHA of every chunk and entire reconstructed archive.

**Results branch:** from this **DESIGN PR head**, create a **new Draft RESULT PR** titled `B570 result: final partition, operator, KV-state and timeline closeout`. Do not merge. Preserve main, all earlier PRs, manuscript, release, benchmarks and frozen evidence unchanged. Do not silently replace or renumber #99's historical benchmark.

**Scientific terminal test:** a valid closeout may include P1 first-op localization, P2 NOT_ADMITTED and P3 GPU_TIMELINE_NOT_AVAILABLE. All three are legitimate outcomes. A result PR containing only a plan/dry run/CPU audit without real eligible native work is **NOT EXECUTED**; report that blocker accurately rather than claiming success.
