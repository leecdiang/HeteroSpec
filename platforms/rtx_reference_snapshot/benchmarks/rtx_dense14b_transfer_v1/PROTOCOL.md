# Dense-model transfer: Qwen3-14B / original Qwen3-0.6B

**2026-11-01 · implementation provided; no native inference executed in the authoring container.**
The user's instruction authorizes host preparation, ordinary engineering repairs and automatic progression when gates pass. This is not the Strata/MoE plan. It adds one larger supported dense deployment without replacing the existing paper or experimental evidence.

## Question and claim

Does the existing phase-scoped PQ/QB method preserve a new, explicitly defined 14B deployment reference, and what is its complete-request cost under a fixed CPU/GPU layer placement? It is a larger-model transfer test, **not a causal estimate of parameter count alone**: 14B has 40 layers, 40 query heads, eight KV heads and head dimension128, versus the original 8B shape. Partial offload additionally changes placement. No old 8B ratio is pooled with this panel.

Target: official `Qwen/Qwen3-14B-GGUF`, revision `c75e7b2d0234068f674a1bacf548ea32e27ccd29`, `Qwen3-14B-Q8_0.gguf`, 15,698,533,728 bytes, SHA256 `a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d`.
Draft: original qualified Qwen3-0.6B Q8_0, 639,446,688 bytes, SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Models and runtime libraries are not redistributed.

Native ancestor: PR151 `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b`, original Qwen source archive `62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e`. Rebuild from that source and the same 21 numerical-library files. Do not upgrade llama.cpp, quantization, CUDA libraries or model family to obtain a positive result.

## Fixed numerical and timing policy

One request/sequence; context1024; cap128 or natural EOG; native greedy tie breaking; k3; target UB4 for PQ/QB and UB1 for R; draft UB1; F16 KV; non-flash attention; 24 host threads; target phase mask semantics inherited. Use the original model formatting policy, saving actual rendered token IDs and tokenizer/template provenance. Greedy is a reference study, not a model quality benchmark.

Target placement is chosen **before generated calibration output** from 24,20,16 GPU layers in that order, solely by resource admission. The fully offloaded original draft remains loaded in all arms, including R. Target embeddings/output and remaining layers follow the pinned core's native offload policy. All arms use the same actual target/draft placement. No unified-memory oversubscription or implicit pagefile-based capacity claim is accepted.

Use at least 8GiB available system RAM and 1GiB free dedicated VRAM after all pools are provisioned; these are conservative admission gates, not a prediction of true peak. Capture observed QK placement at every one of the 40 target layers and verify Q shape/head and GQA geometry on CPU and GPU. Do not merely permit CPU in the old GPU-only auditor. A mapping that differs from the documented pinned layer policy is investigated before freeze, not silently accepted as a different comparison.

Primary clock: inherited **native resident-model complete request**, from request-state reset through prefill, generation, native sampling, counters and output assembly. Shared model loading and pool provisioning are separately measured. Clean measured requests contain no full-logit writes; heavy qualification captures do write logits during diagnostic execution and their times are never used as performance data. Final sequence-state serialization is after the request clock, and host evidence comparison/record serialization is outside it. This is not an HTTP or fresh-context timer, not cold-start deployment latency, and not directly comparable to old absolute times. CPU/GPU intervals may overlap; do not add them into an invented bottleneck decomposition.

## Stages and auto-progression

### S0: source, assets, resource admission

Recover original source capsule, build tools, draft and 21 DLLs on the existing Windows RTX host. Verify every pin. The native adapter changes device admission, configurable fixed layer placement, 14B geometry identity, study ID, pool count and post-clock state export; it does not replace the attention arithmetic or speculative loop. Build into a fresh directory, never overwrite old DLLs/EXEs. Check the generated source diff before compiling.

Collect CPU/GPU/driver/power/memory/disk identity, choose the existing shared GPU lock and confirm no other experiment is running. Record all build/monitoring processes separately from model workers. Download only the pinned target when absent and disk/license checks pass. No generation in admission; at most the three prescribed placements are tried. Only a proved resource-capacity refusal permits moving to the next placement; an operator/source failure does not.

The runner freezes identity, assets, input/order policy and its code before the first pilot request. The actual capacity probes and final chosen mapping are retained. If none fit, close as RESOURCE_BLOCKED; do not switch to Q4/MoE or purchase hardware automatically.

### E0: 40-request feasibility pilot

Four existing, predeclared calibration inputs, disjoint from the formal panel. Five distinct arms R, M_PQ, M_QB, C_PQ, C_QB, each heavy/callback-off once: **40 requests**, in one separately loaded process. There is no extra hidden generation warmup.

Check complete R endpoint repeatability, observer equivalence, source/draft vocabulary agreement, real q4 speculative verification, all40-layer placement and actual memory/cleanup. The native transaction auditor reconstructs proposals, all verification rows, acceptance/correction/bonus and pending/KV bounds. Inspect full-vocabulary logits, not just top-1 or a matching text string. A technical parser/build error can be repaired under ENGINEERING_POLICY; a real reference mismatch is a scientific outcome.

### E1: 120-request complete qualification

Select **12 project-unseen natural tasks**: code/math × short128–384/long512–768 formatted prompt tokens ×3 per cell. Domain and length are crossed. Freeze source revisions, actual prompt bytes/token IDs, natural-input review, old exposure by ID/text/token hash, and deterministic SHA ordering. No padding, concatenation, answer-dependent truncation or outcome-driven replacement. Eligible-count shortage can be resolved with one prospective pool amendment before E1, not by fabricating length coverage. No previous task is relabelled unseen.

Execute each input under all five distinct arms, heavy/off once: **120 requests**, one separately loaded process. R heavy/off establishes that input's new 14B reference; all candidate endpoints must match it. Output equality covers full IDs/EOG/length/terminal/stop. Every arm's heavy/off trace and state bounds must agree. Full decision vectors and end-of-request sequence state are retained, including rejected verification rows. Reconstruct each native greedy decision from its full vector.

Important distinction: PQ/QB internal byte equality is reported **separately** from shared-reference endpoint qualification. If outputs preserve R but internal vectors or recorded logical work differ, timing may continue, but the result is an implementation/joint-path comparison, not proof of bitwise correspondence or an isolated arithmetic-cost effect. Do not impose hidden-state byte equality as a universal requirement for endpoint preservation. Observer interference or an incorrect speculative transaction remains a gate failure.

Natural early-EOG inputs stay in the panel; at least one true q4 verification witness must exist, with coverage reported rather than invented. If any required endpoint fails, finish the finite safe qualification matrix, retain the counterexample, and do not report a selected-subset speedup. Stop before E2.

### E2: paired complete cost, only after E1

Six labels: **R, M_PQ, M_QB, C_PQ_A, C_PQ_B, C_QB**. A/B are identical PQ speculative controls; both share the same reset PQ context, with labels and order separately recorded. There are three target pools and two draft pools, all loaded for every arm. M arms never execute draft.

Four separately loaded sessions ×12 inputs ×6 arms = **288 measured requests**. Each arm/input has one explicit matching warmup before measurement, adding **288 warmups**. Six-arm cyclic rotation balances positions over12 inputs per session; four sessions per input are not a six-period Latin square. Actual date/power/temperature information is reported; four sessions are not four independent days. No mandatory three-day wait, no optional fifth session and no favorable-result stopping.

Primary per block: `C_QB / mean(C_PQ_A,C_PQ_B)`, aggregated with equal input and session log weights. Report all48 input/session blocks and all12 input aggregates. The engineering benefit screen is reduction above `max(2%, maximum input-aggregate A/A imbalance)` and QB faster in every session aggregate. Secondary ratios: M_QB/M_PQ, M_QB/C_QB, M_PQ/dual-C_PQ, C_QB/R and M_QB/R. No manufactured population CI, request bootstrap, hidden outlier deletion or cross-study pooling.

Every measured and warmup endpoint remains checked outside the paid clock. Compare its trace to the corresponding qualified arm. Later divergence stops further measurement and invalidates a full-panel speedup; keep all completed and missing slots.

## Budget, repair and finish

Planned requests:40 pilot +120 qualification +288 measurement +288 warmup = **736**. At most64 additional actual/at-risk requests are reserved for documented engineering recovery, giving an **800-request hard ceiling across successor epochs**, not a positivity reserve. At most three zero-generation resource admissions. Nominal scientific processes:one pilot, one qualification and four timing; compiler/monitor processes are separate. Host-derived finite time/disk/memory/cleanup reservations are filled before native work; there is no time-of-day deadline.

The runner has process containment, append-only receipts, exclusive GPU lock, hash freeze, no silent retry and recovery of already-complete units without rerunning them. It does not yet constitute Windows acceptance: the actual host must compile and exercise it. Agent repairs and source-level checks are specifically permitted by the user's instruction. See ENGINEERING_POLICY for what may be changed without another approval.

Finish with one of RESOURCE_BLOCKED, ENGINEERING_BLOCKED, REFERENCE_COUNTEREXAMPLE, QUALIFIED_NO_PRACTICAL_GAIN or QUALIFIED_PRACTICAL_GAIN. Do not add GS, an 8B rerun, new quantization, Strata, another model, broader k/length sweeps or hardware/RTL automatically. Failure may still establish a useful transfer boundary. No paper or arXiv update until results have been reviewed.

## Delivery

Commit exact source/model/runtime/configuration/selection identities, raw endpoint/vector/state hashes and authorized access, all slot/process/memory/resource receipts, the complete qualification matrix, analysis and a PAPER_ADDENDUM explaining what can and cannot be claimed. Local ZIP reopening is not remote download verification. Use archive.py for local sharding, then separately upload and independently download/readback via the approved repository/release workflow. Weights and numerical DLLs stay out of the evidence archive.
