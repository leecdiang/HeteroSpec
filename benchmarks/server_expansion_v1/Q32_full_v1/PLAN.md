# Qwen3-32B mixed-Q4 deployment: explicit continuation scope

The user explicitly requested completion of32B after the delivered PR210 B/C
diagnosis and extended the assigned server window until the following morning.
This supersedes the earlier no-automatic32B-GPU scope. It is a separate model /
precision study, not a rewrite or extension of the closed8B measurements.

Inherit the existing Q32 diagnostic ledger:2 requests/128 conservative rows,
including its completed allocation and limited short-forward history. Never
refund or reset those counts. The8B PR197 ledger stays1909/2048 requests and
3053954/8000000 rows. New Q32 cumulative ceilings are512 logical requests and
2000000 conservative rows, including prior diagnostics, references, primers,
all failures and native negative cases. These ceilings are not claims that
qualification will fit, and no correctness gate may be omitted to fit them.
Track the studies separately and report both counters, not a disguised reset.

Use only the previously assigned single GPU1 UUID (private), protect GPU0,
retain the existing minimum GPU/RAM reserves and raise disk reserve to100GiB.
No sudo, device resets, driver/upstream upgrade, foreign-task signalling or
multi-GPU sharding. Native jobs have2 threads on32,33; at most2 CPU build tasks
may run on34,35 during untimed preparation. No concurrent build/download during
clean timing. Pause only allocation conflicts, reserves or observed interference.

Target: exact19762149024-byte Qwen3-32B-Q4_K_M.gguf, SHA
`efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689`.
Draft: unchanged Qwen3-0.6B-Q8_0, SHA
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Preserve acquisition revisions/licenses. The file mixes385 Q4_K,65 Q6_K and257
F32 tensors. Inventory or old UB32/reserve4 smoke is not numerical eligibility.

## Gates

1. Before candidate forwards, run the pristine Linux scalar R (UB1/reserve1,
   C1024,F16 KV,noFA) twice on each of the four immutable exposed M2 roots.
   Capture every requested full vocabulary vector and all active states;
   compare repeats and independently parsed64-layer state, and freeze this
   model's own R. Never use8B or Windows outputs as32B oracles.
2. Preserve the old Q8-only marker/guard. Register separate Q4_K/Q6_K recipes:
   original per-type scalar-MMVQ arithmetic (atomic column1), either explicit
   scalar-column loop or independent column groups. These are REF1-loop /
   REF1-group modes, not a relabelled legacy four-column recipe. Bind block/type,
   quantization/reduction/stride/dispatch source and actual32B operand evidence.
   A graph/buffer/type guard is not a numerical proof.
3. Build into new source/archive/frontend roots, verify complete unchanged
   compiled dependency closure, and record the exact modified translation unit,
   archive members, commands and modules. No old source/build is written. Reuse
   only hash-identical original CUDA translation units; compile every modified
   numerical source. No moving upstream.
4. Qualify supported real32B recipes and full model vectors/active KV/frontier,
   all target-only controls, draft/tokenizer/template compatibility, clean/heavy
   bridge, physical extents/packing, acceptance/rejection/rollback/pending,
   all-accept/bonus, native EOG, cap and reset/capacity. Enumerate every actual
   reference branch before execution and charge it. Reuse exact oracle operands
   only with full commitments. Preserve all failed source epochs and counters.
5. Only after all gates pass, freeze a six-arm descriptive deployment panel:
   W_REF1L_M,W_REF1G_M,L_REF1L_M,L_REF1G_M,W_REF1L_D4,L_REF1G_D4.
   Four original exposed roots x6 arms x4 rounds =96 measurements. Before EACH
   measurement, run one full identical root/cap/live path as an untimed warmup
   in the same native process, with the same reset policy. Thus96 full warmups
   plus96 measurements cost192 requests. Every arm/round worker is fresh and
   receives four warm/measurement pairs. Use the predeclared complementary arm
   rows and four-round Williams root rows (0,1,3,2), (1,2,0,3), (2,3,1,0),
   (3,0,2,1). Each root occupies every within-worker position once and each
   directed root adjacency occurs once. The six-arm schedule itself has
   partial balance, not a fully balanced6-round Williams design. Retain all
   strong controls, full service/startup/hash/load/request/memory costs. It
   changes model size AND weight precision/recipe; no size-only inference,
   new blind sample or population-confirmation claim.

Keep192 panel slots and at least16 failure/closure requests unavailable for
qualification admission. If complete eligibility needs the reserved panel
quota, stop panel admission and expose the exact shortfall; never shrink gates
or selectively retry. Before each native job bind its exact payload/build /
logical count/conservative row reservation. Prior2 diagnostics remain charged.

Whole-panel admission no later than03:00 Asia/Shanghai on2026-11-10, also
requiring conservative observed runtime for the entire panel. Each new worker
requires at least960s before05:00 (900s original worker timeout plus margin).
End new measurement starts at05:00, then archive/readback/statistic checks and
safe delivery by08:00. Do not interrupt a healthy running measurement to insert
other work. A failed gate or insufficient window yields a precise stopped-stage
report with all artifacts, not a lowered criterion or partial-panel speed claim.

Keep completed B/C and earlier PR205/206/208/209 results immutable. No automatic
merge, Release, manuscript edit, rental or data deletion. Public output omits
credentials, allocation UUID and unrelated company information. Archive byte
replay is distinct from numerical qualification.

## Pre-panel source epochs

The first unqualified frontend inherited reserve8. Before a timing freeze, review
identified that the registered width32/all-output geometry requires32 output
slots. All six new32B arms therefore use common reserve32 in the successor;
the scalar R remains reserve1. Source/build epochs01 (reserve8),02 (reserve32
without the later observer adaptation),03 (reserve32, structural observer dedup)
are retained. No previously qualified8B/14B/Llama baseline is changed.

The separate observer adaptation compares exact tensor descriptors before JSON
allocation, rather than repeatedly constructing/dumping identical JSON during
every long prefill. Device placement is still checked on every invocation;
all unique type/shape/stride/device descriptors and occurrence counts remain,
as does every physical position/width/request-mask execution. No vector, KV,
frontier, transaction or numerical equality check is removed. An offline operand
observer is a separate ELF with an explicit full-model bridge; it is never timed.

Add finite synthetic capacity stress (real input token IDs repeated, explicitly
not natural/performance inputs) at C1024, plus actual autonomous EOG one-before /
at-length cap checks. These gates are charged before the descriptive panel.

Source04 prepares a common CUDA-graphs-disabled candidate configuration for all
six32B arms, using the fixed backend's original documented-in-source switch.
Source03's record adapter alone did not establish that long-loop qualification
could fit its900s worker window. This is an explicit new candidate policy before
any timing freeze, not a change to R or the completed graph-enabled8B results.
Kernel fusion is left unchanged; every numerical/lifecycle gate must be repeated
for this exact policy. Retain graph-enabled failures and both costs; do not claim
the timeout alone identifies the cause, or that this deployment measures only
model scale. The private host adapter charges each actual empty-input native
invalid-contract probe as one logical request, with zero forward rows.

Before any formal freeze, clarify the provisional panel quota: if exact necessary
qualification/teacher-branch enumeration exceeds the304-request admission line,
write `PANEL_NOT_ADMITTED_QUOTA.json`, cancel the entire192-request panel, and
continue complete gates within496 requests, keeping16 for failure/closure. The
512/2M total ceilings and all inherited/failed counters remain unchanged. No
partial panel substitutes for the full design. Without this explicit marker,
require192 remaining panel requests plus16 failure slots at panel admission.

## Observer correction and timing review before any formal freeze

The all-six recording successor completed the short p31, p32 and p33/q4 full
vector/state checks, plus the original p764/q4 W-loop and W-group checks. The
long W-loop job completed in863.15s; its success means that the previous900s
timeouts cannot establish hardware incapability. Preserve all prior attempts.

A separate own-process CUDA/SIGPROF diagnostic ran identical p31/cap1 work in
H,C,C,H order. Heavy service times were38.039/38.359s and clean times1.103/1.102s.
These profiled, tiny diagnostic samples are not a performance panel or an8B/q8
finding. Source inspection identified repeated per-node device-type queries;
this backend implements that query with cudaGetDeviceProperties. The common
successor queries immutable type once per distinct device PER REQUEST, while
looking up and checking each tensor's actual buffer device on every callback.
No tensor descriptors, placement checks, full vectors, KV checks, output masks,
callback decisions, arithmetic archives or independent R are removed/changed.
The new frontend and actual dispatch must pass all six-arm gates again.

Review also found three direct finisher job constructors still writing the old
reserve8 despite the reserve32 contract. Correct all three before native gates
or formal timing; no formal request had started. Native failures remain charged.

The original provisional48-primer plan is superseded BEFORE timing by the96
exact-root warmups above. Do not interpret warm-root receipts as measurements
or use the old two-primer burst clock formula. Record complete caller SHA/load,
startup, all warmups, service, serialization and exit costs. Keep the unchanged
512/2M ceiling and all predecessors/failures; no silent budget expansion.
