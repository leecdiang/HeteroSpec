# B570 online cost scan — source work identified, phase milliseconds not invented

Fixed result: PR187 b01040d3b303abfc31c5ce2dbcb100cac7490b27.
This authoring run scanned published costs and the inherited/executed source
chain, and ran `analysis/b570_online_scan.py`. It did not fetch/decompress all
private release objects or run a model. The per-slot metrics/online phase
aggregation remains available only in the retained host archive; it is NOT
claimed completed here. Per-operation timings were not recorded by the reviewed
online move implementation and cannot be recovered by subtracting total service.

## Concrete finding

`prefill_observer::move` in PR63's `code/src/observer.h`, retained by PR187's
Smol source derivation, runs:
1. synchronized full state export from source;
2. pending-logit copy and sampler clone/history work;
3. fresh continuation context construction;
4. full state import;
5. another full state export from destination;
6. a third full state export from original source;
7. two host full-buffer equality comparisons and sampler/state checks.

`HS_TRACE_OFF` disables `bytes()` file writes, metadata trace and top-two reporting;
it does NOT disable these state() calls, import, allocation or comparisons.
The continuation context is freed in the request. M uses HS_NO_TRANSFER=1 and
stays in its source context, while preserving matched unused draft residency.
The fast tensor-coalescing `smol_bulk.hpp` is a separate OFFLINE observer. It does
not accelerate this online `move`. It cannot be cited as a speedup of clean service.

## Recomputed scale, without pretending to have a device-time decomposition

Profile: 24 layers,2048 K and2048 V elements/layer/token,F16 =196608 bytes/token.
Twelve test prompts sum to5400 tokens, mean450. At mean length one active KV is
84.375MiB. Three exports plus one import imply at least337.5MiB of logical active
KV payload movement per speculative request; headers/logits/inactive space are
excluded. One speculative arm's72 measurements imply23.73046875GiB, all five
speculative arms118.65234375GiB, before warmups. This is a source-derived work
volume, not measured PCIe traffic, DMA count or time. No bandwidth is assumed.

C4U4 complete mean service11.235785s versus M1.201086s: parity requires removal of
10.034700s/request,89.3102% of present speculative service. A few-percent draft
prefill optimization alone is not the indicated target. Nevertheless these
numbers do NOT prove migration accounts for that gap or that deleting it makes
speculation profitable. Transfer, context creation and verification remain
unseparated measurements.

## What saved clocks can and cannot answer

The inherited `generation_ms` starts BEFORE `observer.move`, so it includes the
migration and context allocation. It is not pure target/draft decode. The online
helper has no independent export/import/create/compare timers. Existing metrics
can partition prefill, generation-including-transition, host residual and final
capture output; they cannot supply a migration-only percentage.

Run on already-restored metadata only (zero model requests):
`python analysis/b570_online_scan.py --runs <secondary-smol/campaign02/runs> --output <new.json>`
The scanner checks all864 slots and the published six service totals. It does
not load KV tensors, invoke a runner, or silently mark absent metrics as zero.
An absent/incomplete archive produces an explicitly incomplete report.

## Next actual intervention, only after measurement supports it

First export the compact per-request metrics and transfer byte metadata, not a
new huge raw archive. If separate online component time is required, add
exclusive timers around existing move operations on four exposed roots, keeping
an uninstrumented control to measure timing disturbance. That is a small new
GPU diagnostic, not an offline recomputation, and is NOT launched by this PR.
Then investigate (a) bulk serialization with exact payload correspondence, or
(b) eliminating the migration by a qualified resident phase plan. Preserve the
whole old service baseline and measure the new implementation; never subtract
an estimated cost and call the difference a speedup. Optimizations legal for M
must be given to M too. A new same-R candidate lifecycle is allowed; the original
PR187 negative result remains immutable.

## Strategic meaning

A fixed R does not require perpetuating a historically expensive candidate
lifecycle. This is a concrete design opportunity, not evidence of a new theorem
or a promised TPDS acceptance. RTX is used first to build and qualify a reusable
phase-plan interface. Its no-transfer lifecycle is already present in old RTX
work and earns no novelty credit by itself. Future B570 transfer is the separate
place where elimination of migration could have value.

Exact source links and calculations are in analysis/B570_SCAN.json. Missing
per-operation milliseconds are represented as null.
