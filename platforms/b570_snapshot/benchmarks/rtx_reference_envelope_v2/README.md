# RTX reference envelope v2 — measured reference and cost boundary

Status: **PARTIAL_QUALIFIED_COST; SOFTWARE_FIRST/HOLD** (2026-10-18).

See **[RESULT.md](RESULT.md)** and [generated tables](results/).
D0 located destructive K/V input-storage reuse with byte witnesses and reversal;
separately owned persistent inputs restored repeated execution. N1 completed
216/216 hosts and 7,344 calls. T1 completed 432/432 numerical hosts and 16,416 calls;
five of six timing blocks remain eligible after a post-exit CPU retention pause.
No completed GPU coordinate was repeated. R1 completed 24 logical synthetic
fixtures × two value realizations, independent serial references, and 144 qualified
mapping cells up to selected 4096-visible-key coordinates. M1 is an explicitly
abstract finite-resource model, not RTX hardware qualification.

For eligible q2–q4 pairs, T_QB/T_QH_C=0.885627 and T_PQ/T_QB=1.814620
(resident completed graph). This favors QB; it is not a decoder speedup claim.
All failures, reversals, tails and missing scope are retained. Full raw stays
local: 110,693 archived members, fresh-restored and CPU-recomputed; no remote raw
or external independent review. Historical PR118 evidence remains unchanged.

This new lane turns the existing results into a testable chain:
**reference constraints → admissible mappings → measured cost boundary → hardware decision**.
It first addresses PR118's repeated-execution failure. It does not assume QH wins,
that KV commit is a bottleneck, or that a hardware contribution is inevitable.

## Start here

Actual results: [RESULT.md](RESULT.md), [RAW_LOCATION.json](RAW_LOCATION.json),
[COMMANDS.md](COMMANDS.md). The following are the original research framework.

1. [FRAMEWORK.md](FRAMEWORK.md): established evidence, research questions, falsifiers,
   generalization limits, prior work, and the hardware decision.
2. [PROTOCOL.md](PROTOCOL.md): implementation freedom, diagnostics, qualification,
   timing, boundary expansion, full-geometry modeling, and reporting rules.
3. [RTX_PROMPT.md](RTX_PROMPT.md): complete dispatch prompt for the RTX platform.
4. [RUN_SPEC.template.json](RUN_SPEC.template.json): planning defaults; materialize
   a real run specification before execution. Null fields are intentionally unresolved.
5. [EVIDENCE.md](EVIDENCE.md): compact evidence contract and required output tables.
6. [SOURCES.json](SOURCES.json): immutable repository evidence and external references.

The initial design was dispatched by the author and is now accompanied by actual
Windows/CUDA implementation and measurements. Self-tests and same-host fresh
recomputation are not external independent review. Publishing this result does
not authorize another execution or any W1/actor/RTL work.

## Branch and historical scope

Stack on PR118 branch `research/rtx-s1b-clean-cost-20261016`, pinned parent
`8a4cbb4246323a3f159f94cae8c92544d5a215dc`. The diff adds only this directory.
Do not resume `pr116-s1b-exact-r2`: it permanently stopped with 1/72 coordinates
started, zero qualified, and an unexplained second-execution discrepancy.
PR118's opening description predates that result; use its actual r2 result file.

Old code, frozen approvals, results, and raw evidence remain unchanged. Reuse
source by importing/copying the necessary modules into this lane with provenance,
or extracting a shared implementation without changing old execution behavior.
Do not remove old guards or forge an old approval to launch an old entrypoint.
This lane has its own entrypoint and run identities. The new development and
progression rules apply only here. Existing platform access controls still apply.

PR104/110/111 are **external immutable evidence dependencies**, not all files
present in this stacked checkout. Fetch only selected required source/manifests/
snapshots by their pinned commits; list what was actually obtained. Missing PR110
code cannot block D0/N1/T1, and missing profiler cannot block valid host timing.

## Minimum useful completion

First dispatch defaults to eight hours, with one hour reserved for delivery.
Prioritize D0 (diagnosis and a stable execution path), N1 (qualification), and T1
(the original 24-context costs). Publish a useful partial result if time expires.
R1 (boundary expansion), M1 (full-geometry model), and W1 (whole-request validation)
are progressive extensions, not prerequisites for reporting the core result.
CPU framework/model work may proceed while GPU timing is unavailable, but never
invent missing inputs or replace RTX measurements with model cycles.

The complete research program is deliberately larger than one dispatch. A blocked
stage does not erase completed evidence or automatically block independent work.
Negative results, unsupported mappings, unresolved causes, and inconclusive costs
are valid outcomes. No automatic RTL, FPGA, model download, paper-claim expansion,
merge, release, B570 change, or unrelated process termination is part of this lane.
