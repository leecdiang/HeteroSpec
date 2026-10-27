# Preregistered RTX scope-transfer protocol, schema 1

## State and scope

This is a **pre-execution design** stacked on PR149, commit `9149b6f5f5a4dcde1b6124c654dc0ba1241ca509`. New native executions and results are zero. Source pins identify the actually inspected bridge, PR144 input/model manifests and source-line bindings. Host paths, worker hashes, exact numerical-library manifests, calendar dates and resource caps remain to be bound in a committed execution freeze. Until then the design is not executable admission.

The factorial hypothesis is that numerical-repair scope changes the net value of drafting under a matched complete-request runtime. The principal comparison is GS versus QB. PQ separates the local implementation effect from the repair-scope effect. A separate Llama diagnostic asks which producer/consumer conditions reproduce an already known numerical counterexample. Its outcome does not block Qwen3/SmolLM2 factorial work and need not be a successful repair.

## Fixed input and model contract

Use all twelve Qwen and all twelve SmolLM2 entries, in their original source-index identities, from PR144 `revision_a/INPUT_MANIFEST.json` at `79f6e6d687f87465219a7557bc4c8306e9b13149`. Its SHA256 is `5087de106148cf8497a3753f4075f59f76c8eeab88792869b86b9e12cd0f3ce3`. Native integer IDs are copied without re-rendering, truncation, padding, retokenization or answer-dependent selection. `PANEL.json` preserves source index, dataset revision, source-entry hash, selection hash, cap and a newly defined prompt-ID hash. The prompt-hash encoding is compact UTF-8 JSON integer array with no trailing newline. Any older hash is retained separately, not assumed to use that encoding.

This is **transfer to an independent but now exposed panel**, not a new blind test. Short inputs are mathematical problems and medium/long inputs are code problems; domain and length effects cannot be separated. The fixed panel is not replaced by the old main panel or a newly selected eight-input panel after seeing outcomes. Cross-family reuse of named tasks does not create independent tasks.

The original PR144 model contract pins weights, vocabulary, EOG IDs, tokenizer metadata, template and target/draft shapes. Qwen uses the original source archive; SmolLM2 and diagnostic Llama use metadata4. Within each family all seven arms use the same executable, core, numerical DLLs and model bytes. Across families the executable/core need not match. This is a new runtime cohort: old Qwen qualification does not qualify Smol/Llama, and new R must still reproduce the historical panel's R endpoint.

## Factorial arms and service contract

| Arm | Selector | Scoped target | Target UB/output capacity | Draft | k |
|---|---:|---|---:|---|---:|
| R | 1, inactive | No | 1 / 1 | Off | 0 |
| M_GS | 2 | Yes | 4 / 4 | Off | 0 |
| M_PQ | 1 | Yes | 4 / 4 | Off | 0 |
| M_QB | 0 | Yes | 4 / 4 | Off | 0 |
| C_GS | 2 | Yes | 4 / 4 | On | 3 |
| C_PQ | 1 | Yes | 4 / 4 | On | 3 |
| C_QB | 0 | Yes | 4 / 4 | On | 3 |

GS means the actual scoped target `memory->init_batch(...layout95()==2 ? 1 : n_ubatch...)` mechanism recorded in the source bindings. It is not k=0, an attention-only split or a relabeled PQ run. Its target physical micrographs must have width one even though the speculative caller verifies four logical rows. PQ/QB retain surrounding multirow computation. Logical and physical counts are separate evidence.

All arms use ctx1024, F16 KV, FA off, 24 threads, cap128, native EOG stopping and greedy tie behavior. Both target and draft weights are loaded once per independent family-session, including target-only arms. Draft contexts use UB1. Resident contexts are provisioned before warmup and cleared between requests. Context-pool identity includes family, fixed scope and target configuration; R has its own UB1 context. A target context is never reused across scopes. Within a scope M and C may share the cleared target context; only C invokes its scope-specific draft context. Record resident memory admission. If the pool cannot fit, stop and register an all-fresh alternative before execution; do not mix lifecycles within this study.

The service clock covers reset/setup, full target/draft prefill, generation, verification, transaction/rollback, native stop, synchronization and result assembly. It excludes model loading, resident provisioning, reference comparison and file writing. Record those components separately. Keep complete-request and narrower request-window clocks distinct; neither becomes a decode-only or exclusive-GPU clock. Heavy qualification/capture times are excluded from performance analysis. Retain identical baseline native logging settings across arms; changes in logical work or logging are part of the complete-request path effect.

## Qualification, schedule and budget

New-binary qualification is 2 families × 12 inputs × 7 arms × capture on =168 requests, plus source-index sentinels 0 and 11 × 2 families × 7 arms × capture off =28: **196 total**. Sentinels are fixed without new outcome inspection. Every new R must match historical R; every arm must match that complete R endpoint. Endpoints include full IDs, all EOG flags, length, terminal ID and natural EOG/cap reason. The capture guard also compares canonical state. Qualification is separate from timing and completes before formal requests for its family.

Formal collection uses **three actual Asia/Shanghai dates, two separately loaded sessions per date and family**. Preserve UTC timestamps and derive local dates using UTC+08:00. The first sessions of adjacent date slots must start at least 20 elapsed hours apart, for each family and for the daily first session. Each session and its requests stay inside its declared local date. The old planning text's UTC-date wording is superseded by this local-date contract. Crossing midnight in one continuous run is not another independent date/session.

Per family-session: twelve inputs × seven arms =84 measurements; source-index input0 × seven arms =7 charged warmups. Total: **1008 measurements +84 warmups =1092 formal-stage requests**, twelve family-session workers. Together with qualification the factorial budget is **1288 requests**. No adaptive warmups or replacement inputs.

Within each input block the seven arms are contiguous. A deterministic family-specific base permutation is rotated by `(global_session_index + source_input_index) % 7`. Each input sees six distinct rotations across six sessions; 72 blocks cannot divide evenly by seven, so overall arm-position counts differ by at most one. Input order uses SHA256 ordering with the fixed seed in `PLAN.json`. Family-first order alternates by local date: Qwen/Smol, Smol/Qwen, Qwen/Smol. The exact slots, not a prose randomization claim, define execution order.

At most one whole new technical attempt per family-session, and at most two across the study, may retry a process/device/output failure. Its maximum reserve is 182 requests. Preserve the complete failed attempt, explicit unstarted slots and original receipts; never merge partial attempts. No numerical retry, effect-dependent retry or date extension is allowed. Qualification has no automatic retry. Worker wall time, total owned time, payload ceiling and minimum disk headroom must be committed before any new request; this design supplies no guessed host timings.

## Numerical and work admission

Heavy qualification retains all full-vocabulary target decision vectors, draft proposals and verification rows, including rejected/unexamined rows. PQ/QB claims additionally require complete paired vector inventories and bytes plus canonical cycles, pending ownership and final KV state. Do not infer raw identity from endpoint equality. The CPU auditor uses family-specific layer/head metadata rather than Qwen's hardcoded 36-layer assumption; the host observer must capture the necessary prefill/ordinary/verify geometry.

Reconstruct each speculative transaction from proposal and decision rows. Check accepted prefix, first rejection/correction or bonus, terminal/cap handling, keep positions, rollback and remaining pending state. Compare C_GS/C_PQ/C_QB logical work. Unequal work with equal valid endpoints remains a complete-request result, labeled a **joint path effect**; it cannot support an execution-cost-only or CUDA Graph causal explanation. PQ/QB natural state inequality fails the local equivalence gate.

No source, runtime, model, vocabulary, EOG or input mismatch is repaired by substituting a nearby version. A failed family remains a failed fixed-panel cohort; do not report a passing subset as the planned study. Another family can proceed only when its full identity and qualification hold and all shared process cleanup/host gates are reconciled.

## Estimands and reporting

For layout L, `D_L=T(M_L)/T(C_L)`; above one favors drafting. The two primary contrasts, one per family, are `I=log(D_QB)-log(D_GS)`. Secondary complete-request ratios are C_QB/C_PQ, M_QB/M_PQ and R/C_L. Ratios involving R describe a separate strict-reference baseline, not the marginal value of drafting.

Average twelve input log contrasts equally within session, two session means equally within date, then three date means equally. Retain every input/session effect, all six session points, the three date points, within-date session differences and adjacent-date differences. Require the complete planned task set for a qualified family estimate. Do not impute missing arms, remove reversals or count 1008 requests as independent sampling units.

The main presentation is the three date points and range. Optional 97.5% paired-date t intervals for the two primary family contrasts use df2 and Bonferroni allocation; they are **weak sensitivity only**, conditional on independent approximately normal date means. Three dates do not estimate date-population variance robustly, establish statistical power or support a general random-effects claim. No request bootstrap or session bootstrap is interpreted as date uncertainty. Report session signs even if all date means agree. Cross-date direction requires all three dates to share that direction. Profitable drafting requires D_QB>1 separately; a crossover additionally requires D_GS<1. I>0 alone establishes neither. SmolLM2 may remain below parity under both scopes and is a prespecified informative negative case.

## Independent Llama diagnostic

Fix failure `CodeContests/valid/108` (source index8, 737 tokens), long passing control `CodeContests/valid/43` (index6, 443), and short passing control `GSM8K/test/496` (index3, 77). A0 uses historical records without GPU calls. The pinned summary reproduces endpoint divergence at output81, R token16 versus PQ/QB token15. It does not contain enough byte-level stage evidence to identify the earliest numerical or operator divergence. Retrieve observer/logit/cycle shards with their existing source identities before making that claim; equal stored PQ/QB endpoints alone do not revalidate every vector.

A1 is three inputs × R/C_PQ/C_QB × observer off/heavy =**18** fresh-context requests. Preserve original controls and the counterexample. If the failure disappears in the new driver, report `RUNTIME_DEPENDENT_COUNTEREXAMPLE` and inspect source/config/producer/output extraction; do not name the disappearance a fix.

A2 is three inputs × P1/P4_NATIVE producer recipes × C1/C_PQ/C_QB × off/heavy =**36** diagnostic requests. P1 calls target prefill one ID at a time. P4_NATIVE submits the complete prompt once, internally partitioned at target UB4; this is different from the B570 explicit caller-width4 recipe. C1 is the scoped PQ target-only UB4/output4 control, not strict R. Each context retains its scope for its entire lifetime. Draft prefill is recorded and held fixed across the producer comparison. No checkpoint import or common-donor state transfer is performed. If producer states differ across layouts, only a bundled recipe result is identified; no consumer-only causal claim follows. All these timings are diagnostic, not performance observations.

Default total is **54 Llama requests**, independent of the 1288 factorial requests. Checkpoint/restore (up to12 shams), bounded captures (up to8), operator replay (up to24) and repair confirmation are disabled. Enabling any requires a reviewed, pre-execution amendment and a new freeze. State transfer requires each same-state, same-layout natural/resumed own-path sham, with no hidden forward on restore. If a future repair confirmation uses new indices9/10/11, it costs18 requests (three inputs × three arms × off/on). Repeating the old three inputs after A1 has already been spent costs another18; it cannot silently reuse the A1 allocation. No success-seeking repair loop is part of this PR.

## Completion and evidence preservation

Valid endpoints include complete qualified result, complete counterexample, no trigger, runtime dependence, unresolved localization and explicit incomplete-date replication. Unknown is not pass. Retain historical bytes, new raw records, every started/failed attempt, all NOT_RUN causes, null timing eligibility, logs and content manifests. A budget or date shortfall remains a shortfall. The independent CPU review and a native run on an independent host are distinct statuses. This PR claims only the former tools and design checks, not execution of the latter.
