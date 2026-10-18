# RTX reference envelope v2 — research and execution design

Status: **D0_COMPLETE; N1/T1_PENDING** (2026-10-18).

PR120 now has a new native host and runnable Python entrypoint, offline build,
72 actual CPU graphs, 15 CPU self-tests and 12 D0 hosts / 216 graph calls.
Original resident allocation reproduces the PR118 symptom in all three runs
and all three reversal runs. Re-upload restores output but does not preserve
input storage. Separately allocated persistent inputs retain full input/output
bytes over 3 fresh processes ×34 calls. Actual input/node address overlap is
recorded in the original allocation and absent with persistent inputs.
This is a host allocation/lifetime intervention, not a CUDA arithmetic change
or a QB-specific fault. Full-panel qualification and costs remain pending.
See COMMANDS.md, INVENTORY.json and CPU_TESTS.json. Raw stays in the UUID root
recorded in INVENTORY; historical PR118 evidence is unchanged.

This new lane turns the existing results into a testable chain:
**reference constraints → admissible mappings → measured cost boundary → hardware decision**.
It first addresses PR118's repeated-execution failure. It does not assume QH wins,
that KV commit is a bottleneck, or that a hardware contribution is inevitable.

## Start here

1. [FRAMEWORK.md](FRAMEWORK.md): established evidence, research questions, falsifiers,
   generalization limits, prior work, and the hardware decision.
2. [PROTOCOL.md](PROTOCOL.md): implementation freedom, diagnostics, qualification,
   timing, boundary expansion, full-geometry modeling, and reporting rules.
3. [RTX_PROMPT.md](RTX_PROMPT.md): complete dispatch prompt for the RTX platform.
4. [RUN_SPEC.template.json](RUN_SPEC.template.json): planning defaults; materialize
   a real run specification before execution. Null fields are intentionally unresolved.
5. [EVIDENCE.md](EVIDENCE.md): compact evidence contract and required output tables.
6. [SOURCES.json](SOURCES.json): immutable repository evidence and external references.

The present PR delivers a protocol, not a repaired native host, runnable GPU
entrypoint, new measurements, or an independent implementation review. No RTX
task is dispatched by publishing these files. The author will dispatch the
platform separately. After that dispatch, the executor may implement, diagnose,
qualify, and progress within this lane and the selected budget without seeking
permission for every routine repair or stage.

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
