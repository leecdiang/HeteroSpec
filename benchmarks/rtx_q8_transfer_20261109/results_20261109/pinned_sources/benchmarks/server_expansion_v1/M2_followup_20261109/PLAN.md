# M2 follow-up: explain width cost before changing the implementation

Status: DESIGN ONLY / NOT RUN. This PR adds a bounded protocol, not an implementation, new result, or permission to execute GPU work. It is stacked on PR #209, source `2d076402b4ddc29c92549d360cd974af40d3f0a4`. Existing sources, baselines, results and paper remain unchanged.

## Decision and evidence

The question is whether avoidable implementation cost materially contributes to k7's slower service, not how to obtain a winning k7 result. Here **q8 means physical verification width eight**, not weight quantization: both original Qwen3 models are Q8_0.

[The frozen M2 result](../M2/results_pilot_20261108/README.md) reports finite qualification followed by 64 live measurements and 32 replay measurements. LOCAL-packed live service is 11.878694 versus 13.548505 s (+14.057%) for k3/k7; free replay is +10.610%. At fixed k7, packed saves 1.826% service versus loop4. All are four-exposed-input descriptive results, not population inference.

Fewer verification cycles (288 to 172) coexist with more VERIFY rows (1152 to 1376) and more total target/draft rows (1868 to 2092). A change to q8 performance cannot be inferred from either call count or accepted count alone. Generated native source and executable bindings, not an untouched template header, establish the actual width-eight path.

The main evidence in #203–#208 is not reopened. Paper reconstruction need not wait for this protocol or 32B. A neutral or negative follow-up is a valid terminal outcome.

## Stage A: zero-GPU source and saved-record audit

1. Pin repository/source, generated source transform, native binary/module, model hashes, driver and configuration. Read M2 build_native.py, transform.py, panel.py and SOURCE_BINDINGS.json together; identify actual compiled code.
2. Reproduce saved live/replay and complete-cost tables. Audit phase clock boundaries, synchronization, proposal generation, requested-vector copies, ownership/lifetime, allocations, reset and cap termination.
3. Decompose the LOCAL-packed live increase using saved phase fields: target verify about +0.629439 s, draft about +0.681317 s, prefill about +0.003388 s, residual about +0.355665 s. Recompute exact values from bound records before publishing.
4. Only name a measured cost if an archived field actually measures it. Residual is unassigned time, not evidence of logging overhead. Phase host clocks may include synchronization and are not kernel times.
5. Report near-cap unconsumed proposals separately from rejected incorrect tokens. Derive per-row economics as descriptive accounting, not an equal-work comparison.
6. Stop here if the source and receipts already explain the engineering question and no concrete optimization hypothesis remains. No automatic full panel.

## Stage B: equal-work target diagnostic

Purpose: separate physical batching cost from k-dependent acceptance/work inflation. This diagnostic is NOT a live speculative-decoding speedup benchmark.

Hold target model/hash, C1024, F16 KV, noFA, target UB32, reserve8, CPU threads, GPU UUID, LOCAL cut, output policy and executable constant. No draft calls occur inside the target diagnostic. Do not infer a new whole/local or M-versus-D result.

Eight cells = two projection modes (loop4/packed) x two executions (two sequential physical q4 calls / one physical q8 call) x two geometries (within-extent / crossing-extent).

* Bind four deterministic origins from the existing four exposed M2 roots and their unchanged R continuations. Construct state just before absolute positions 248 and 252: eight appended positions are respectively within [248,255] and crossing [252,259] of the observed 256-token extent. Verify positions and actual padded extent in native receipts; do not assume labels imply geometry. If an origin lacks enough authorized frozen continuation, stop that fixture rather than inventing or silently substituting it.
* Both paths start from identical restored target KV/frontier and consume the exact same eight known token IDs. q4 call two sees the committed first four tokens. Both return all eight requested full vocabulary vectors, own them beyond the decode call, and finish at the same active KV/frontier.
* A scalar UB1/reserve1 R produces the independent oracle at the unchanged reference configuration. Existing content-addressed R state may be reused only if exact operands and output/state commitments match; new reference work is charged.
* For all four origins and every cell, check the unchanged numerical criteria, all eight vectors, active target state/frontier and requested-output mask before timing. A mismatch is evidence against eligibility, not a reason to relax tolerances.
* Freeze the first origin in immutable input order for each geometry for timing, irrespective of measured performance. Two measurements/cell use paired q4pair/q8 order AB in the first round and BA in the second (reverse projection/geometry block order too), with matched resets and one unmeasured-but-charged primer/cell. This is a small diagnostic, not fully neighbor-balanced inference.
* Time the complete equivalent target operation including required output materialization. Snapshot restore is outside the primary timer for BOTH paths; record restore/copy costs separately. Reject any unequal-output, unequal-work or failed-state cell.
* Record per-call physical rows, projection dimensions, mask, actual split and packed eligibility. Distinguish LOCAL actual q8 from a hidden q4 decomposition. Host timings alone do not establish kernel fusion or launch efficiency.

Stage-B ceiling: 80 logical requests: 32 candidate qualification +16 timed +8 primer +24 reserved for independent oracle/bridge/failure work. Exact oracle jobs must be enumerated before admission; valid content-addressed oracle reuse may reduce that cost. If required oracle work exceeds this reservation, stop and obtain a separately approved budget amendment BEFORE running. Never call the matrix executable when oracle costs are unaccounted. A paired q4 operation counts as one logical diagnostic request but its two calls and all rows are separately charged. Fix this accounting convention before the first request.

## Stage C: bounded profiling and candidate decision

Ceiling 16 additional requests, including profiling primers/references/failures. Use only Stage-B-bound cells and expose profiler overhead; profiling measurements are not clean performance results. Require an explicit measured hotspot and expected end-to-end contribution before editing.

Prefer lifecycle-neutral buffer reuse, redundant allocation removal or bookkeeping improvements shared by BOTH k values. Preserve full-vector shape, ownership, exact requested outputs, state and graph-reuse rules. Do not replace owned vectors with dangling views or argmax-only outputs.

Deleting the last draft forward, changing proposal depth near cap, or skipping draft-state updates is a semantic/lifecycle change. It needs independent pending/KV suffix/correction/all-accept/rejection/EOG/cap/reset qualification and a separately approved plan; it is not included as a quick optimization here. No token-specific exception, tolerance change, model substitution, k sweep or precision change.

If measured overhead cannot plausibly alter the decision, publish the diagnosis and stop. No requirement that k7 win.

## Stage D: one common candidate epoch, conditional on C

Ceiling 64 new requests for reference/bridge/qualification, including failures. Before admission enumerate exact fixtures, oracle reuse and conservative row bounds. If the required correctness coverage cannot fit, stop and request a budget amendment; never shrink a correctness gate to fit a quota.

Freeze one implementation candidate used by both k3 and k7 at common reserve8. Requalify all touched lifecycle/output paths against the unchanged R and relevant existing natural, geometry, rejection-rank, all-accept, bonus, cap/EOG and reset fixtures. Existing proof reuse requires a documented dependency analysis and identical code/data bindings for untouched paths. Keep heavy qualification separate from clean timing and bridge endpoint/state/trace/output policy.

Preserve every source epoch and failure. A candidate that cannot satisfy existing criteria is ineligible for timing.

## Stage E: contemporaneous old-versus-new bounded pilot

Only after D passes. Fix LOCAL-packed as the previously chosen diagnostic path; do not infer behavior for the other cut/projection combinations.

Four arms: old-common-reserve8 k3, old-common-reserve8 k7, new-common-reserve8 k3, new-common-reserve8 k7. Old and new are source/executable epochs, not historical timings. Same libraries, hardware, model/config/output policy; record source differences and any unavoidable library difference as a disqualifying confound.

Two sessions x four original exposed roots x four arms = 32 clean measured requests. Two distinct original primers/arm/session =16 primers. Total ceiling 48 requests. Use one prespecified complementary arm-order row and its reverse, also reverse root order; label this partial balance, not a full Williams design. Retain all cells and failures, no favorable root selection or retries.

Primary descriptive contrasts are new/old service at EACH k and new-k7/new-k3 service, plus their ratio-of-ratios. Report per-root and aggregate service, prefill/draft/verify/residual, cycles, proposal/acceptance/unconsumed work, target/draft physical rows, complete process/load/primer cost and memory sampling limits. Do not pool original reserve4 or original pilot timings into this comparison.

This does not establish speculation-versus-M superiority or a new population claim. Such a claim would require the separate full contemporary M/D control design described in [M/PLAN.md](../M/PLAN.md), a new cohort and separately approved resources. No automatic expansion to that panel.

## Budget and execution admission

The published PR197 cumulative ledger is 1826/2048 requests and 3,021,131/8,000,000 conservative reserved rows. Thus the snapshot remainder is **222 requests and 4,978,869 reserved rows**, not a fresh envelope. Re-read the latest ledger at actual admission; other work may have consumed it.

Hard stage reservation: B 80 + C 16 + D 64 + E 48 + failure/closure reserve 14 =222. Stage A has zero native requests. These are ceilings, not permission to bypass necessary qualification or an assertion every stage will fit. Existing hidden oracle work cannot be free. No auto transfer of unused stage budget; record any prespecified amendment before execution.

Before GPU work, publish a manifest with exact job and oracle counts, worst-case reserved target/draft/reference rows, available GPU UUID/mutex, source hashes, wall budget, worker timeout and shutdown boundary in Asia/Shanghai. Every reference, primer, failed request and profiling run consumes ledger budget. Preserve the historical 900-second worker timeout unless a separate justified amendment is approved. Never reset counters in a new directory.

Monday server access is not presumed. Obtain actual available window and resource authorization; stop admission with enough time for the largest worker plus archive verification. Do not interrupt other services or active foreign jobs. No run starts solely because this design PR exists.

## 32B: separate conditional qualification, not a paper gate

The Qwen3-32B-Q4_K_M allocation/short-forward smoke is not a qualified scalar reference or performance result. Its UB32/reserve4 cannot substitute for UB1/reserve1 R; sampled free memory is not a guaranteed peak budget. It changes both model size and weight quantization.

If separately authorized time and budget remain, first inventory every actual mixed-Q4 tensor type and required arithmetic recipe. Qualify supported recipes on captured real 32B operands or a separately labelled smaller-Q4 diagnostic; a smaller model does NOT qualify 32B. Do not widen a Q8 guard and call it Q4 support.

Only after an independent exact-32B scalar R and candidate full-vector/state/lifecycle checks pass may a separately registered timing plan be proposed. This protocol reserves zero 32B GPU requests and authorizes no 32B timing panel. A typed-kernel gap, insufficient oracle budget or unavailable server is a recorded stop, not a blocker for paper reconstruction.

## Required outputs and stop decision

Publish a source/receipt manifest, cumulative budget ledger, Stage-A attribution with missing fields explicit, eligible equal-work results, profiler/candidate rationale, and either the complete prespecified pilot or a precise stopped-stage report. Bind raw and derived hashes, preserve failures and use fresh output directories. Public readback/recomputation proves archive consistency, not new numerical qualification.

Terminal decisions: (1) no actionable implementation defect; keep current width recommendation, (2) common optimization helps but k3 remains preferable, (3) finite descriptive width preference changes, with its exact scope, or (4) correctness/resource blocker prevents an answer. All four are acceptable. No merge, release, paper edit, baseline overwrite, data deletion or unattended additional experiments.

## Source anchors

* [PR #209](https://github.com/leecdiang/HeteroSpec/pull/209): M2 and Q32 archived evidence.
* [Frozen M2 README](https://github.com/leecdiang/HeteroSpec/blob/2d076402b4ddc29c92549d360cd974af40d3f0a4/benchmarks/server_expansion_v1/M2/results_pilot_20261108/README.md).
* [M2 source/rebuild contract](https://github.com/leecdiang/HeteroSpec/blob/2d076402b4ddc29c92549d360cd974af40d3f0a4/benchmarks/server_expansion_v1/M2/REBUILD.md).
* [Original M1/M2 plan](https://github.com/leecdiang/HeteroSpec/blob/2d076402b4ddc29c92549d360cd974af40d3f0a4/benchmarks/server_expansion_v1/M/PLAN.md).
