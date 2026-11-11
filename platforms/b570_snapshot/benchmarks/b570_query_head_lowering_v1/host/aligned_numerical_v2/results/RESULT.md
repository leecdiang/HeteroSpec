# Formal repaired-layout panel stopped on the frozen observer limit

Execution used reviewed commit `d12a82d38a438425b8a9a54c899e076fae64456c`,
F0 SHA256 `332c5d5d309a97f5073b7fd3d8228a5ef46ade7b87315632165251fe89b7786c`,
run_id `b570-aligned-numerical-v2-20261015-01` and the exact README entry. No
source, rule, candidate, input, binary, dependency or F0 was regenerated/changed.
The current explicit human confirmation was recorded in `AUTHOR_CONFIRMATION.json`
before the controller invocation; its current receipt time is not backdated into
F0. The frozen entry rehashed identities and its OS-only inventory found no
conflicting compute task. The new run root did not previously exist.

**This is an incomplete panel.** The census admitted all 80 repaired graph
descriptions. After 35 admitted numerical graphs, numerical attempt 36 (plan
index 36, q1/K257/H8/Hkv2/MQ/repeat1, PID33684) returned status0 and complete
output, but its final observer interval was **1.032 seconds > frozen 1 second**.
The frozen controller stopped at `final observer gap`. It did not retry, relax
the limit, continue q1, enter q>1 or initiate any extra GPU work.

The actual failing check is `audit_lifecycle`'s interval from the last watchdog
sample to recorded lifecycle end. This includes controller-side runtime-gate and
close work; it is not a GPU kernel duration or proof of GPU numerical failure.
Its last sample was elapsed0, its recorded lifecycle end1.032s. The native exit
was0, and GRAPH_START/GRAPH_RETURN/GRAPH_OUTPUT/CLOSE and all four vectors remain.
The lifecycle's own stop field is null; the later controller gate failure is
authentically recorded in LEDGER/CLOSEOUT and independently reproduced. The slot
remains observer-invalid despite its complete output. There is no expected-crash
classification or assertion-callsite investigation in this result.

## Separate execution and resource accounting

| Charged experiment hosts | Planned | Started | Admitted complete | Invalid | Unstarted | Graph calls | Owned seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Support census | 1 | 1 | 1 | 0 | 0 | 0 | 1.016 |
| Numerical | 160 | 36 | 35 | 1 observer | 124 | 36 | 40.311 |
| Total | 161 | 37 | 36 | 1 | 124 | 36 | 41.327 |

All36 numerical processes exited0 and returned complete output; none crashed.
The table's admitted count additionally requires the frozen observer gate, so
native returned-output count36 must not be presented as36 qualified samples.
All37 experiment hosts have distinct actual PID/creation-FILETIME identities.
Maximum owned host time1.844s. One Python controller ran separately (wall50.264s),
one frozen offline reconstructor ran separately (wall4.750s), and pure CPU
inventory/delivery/publication audit tools are separate from these experiment
hosts. This is not a claim about the total number of OS processes on the machine.

Peak sampled worker RSS99,471,360bytes; minimum available host RAM18,605,486,080;
minimum disk158,312,857,600. Largest interval between actual samples515ms; final
sample-to-close maximum1032ms caused the stop. All146 in-host GPU memory
checkpoints had at least9,754,648,576 free bytes. No continuous residency claim.
Every37 charged host reported actual interface alignment64, matching frozen
conditions. The complete native bounds/ownership/binding reconstruction is
retained separately from supports_op and process-control eligibility.

No model, extra probe, warmup, scientific retry, actor run, S2/S3, profiling or
performance experiment occurred. Owned time includes initialization, queries,
copies/readbacks/logging and control work and supports no speed conclusion.

## q1 controls, repetitions and every geometry

An equality below means full QK/softmax/AV/final arrays, restored to the common
logical order, are all bitwise equal. It is restricted to admitted data.

| q | K | Hkv (H8) | Admitted / invalid / unstarted numerical hosts | Complete admitted repeat pairs | All ten mode pairs, each available repeat |
|---:|---:|---:|---|---:|---|
|1|63|8|10 / 0 / 0|5/5|All4 stages equal, both repeats|
|1|63|2|10 / 0 / 0|5/5|All4 stages equal, both repeats|
|1|257|8|10 / 0 / 0|5/5|All4 stages equal, both repeats|
|1|257|2|5 / 1 / 4|0/5|All4 stages equal at repeat0; repeat1 unqualified|
|2|63|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|2|63|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|2|257|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|2|257|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|3|63|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|3|63|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|3|257|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|3|257|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|4|63|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|4|63|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|4|257|8|0 / 0 / 10|0/5|All4 stages UNKNOWN|
|4|257|2|0 / 0 / 10|0/5|All4 stages UNKNOWN|

Only35/40 q1 hosts are admitted;1 invalid and4 unstarted. All35 admitted hosts
meet the common-path control. Fifteen independent new-process repeat pairs meet
all4-stage bitwise controls, out of20 planned q1 pairs (80 full-panel pairs).
For the invalid fourth input's MQ repeat1, an offline descriptive comparison of
its complete output to repeat0 is also equal, but this does not fix its observer
eligibility. The other4 repeat1 modes are absent; all120 q>1 slots are absent.

**q1 is a degenerate common path:** the five labels all built the original MQ
common graph at Q0. The q>1 QH packed-Q CONT, QH_D mask REPEAT, REPEAT4 KV REPEAT
and PQ independent mask slabs were support-queried but never numerically executed
in this panel. This result cannot establish those paths' numerical equivalence,
reproducibility, input invariance or actual physical-binding eligibility.

## All ten representation comparisons

The denominator is16 inputs ×2 repeats =32 comparisons per pair. Each available
comparison includes every element of all4 stages. Missing includes the invalid
last q1 repeat1 and all q>1 coordinates, never zero-filled.

| Pair | Admitted comparisons | Missing/invalid | First bitwise divergence | QK/softmax/AV/final max abs and ULP |
|---|---:|---:|---|---|
|MQ / PQ|7/32|25|None among available|0 / 0 / 0 / 0|
|MQ / QH_C|7/32|25|None among available|0 / 0 / 0 / 0|
|MQ / QH_D|7/32|25|None among available|0 / 0 / 0 / 0|
|MQ / REPEAT4|7/32|25|None among available|0 / 0 / 0 / 0|
|PQ / QH_C|7/32|25|None among available|0 / 0 / 0 / 0|
|PQ / QH_D|7/32|25|None among available|0 / 0 / 0 / 0|
|PQ / REPEAT4|7/32|25|None among available|0 / 0 / 0 / 0|
|QH_C / QH_D|7/32|25|None among available|0 / 0 / 0 / 0|
|QH_C / REPEAT4|7/32|25|None among available|0 / 0 / 0 / 0|
|QH_D / REPEAT4|7/32|25|None among available|0 / 0 / 0 / 0|

There are70 available admitted comparisons and250 missing/invalid out of320.
`ALL_COORDINATE_STAGE_RELATIONS.json` retains every input, mode, repeat and stage,
including explicit UNKNOWN entries and complete absolute/relative/ULP metrics.
`NATIVE_AND_CPU_REANALYSIS.json` separately retains the invalid slot's descriptive
full-vector analysis without promoting it into this table.

## Independent FP64 meaning and error description

The frozen offline reconstructor independently rechecked raw lifecycle,
wire/graph/support/module/resource/bounds/inputs and admitted output data. A
separate pure CPU delivery process freshly decoded all16 original stored inputs
and recomputed the scalar binary64 QK, softmax, AV and final references. All64
vectors match the prospectively frozen reference bytes exactly. No native CPU
graph or GPU/device query was used for this recomputation. These references
exist for the unexecuted inputs too; they are not substitute GPU results.

Admitted GPU outputs are finite, their full inputs unchanged, and AV-to-final
restoration is bit-preserving. QK is exact to FP64 on these q1 operands; every
admitted host first differs from FP64 at softmax. This first scalar difference
is distinct from a cross-representation divergence (none available).

| Stage, all35 admitted q1 hosts | Maximum absolute error | Maximum defined relative error | Maximum ULP against F32-rounded FP64 | Nonfinite |
|---|---:|---:|---:|---:|
|QK|0|0|0|0|
|softmax|3.072604951720459e-9|1.954721664904310e-7|2|0|
|AV|8.567088468323936e-9|0.0011585384956523822|13668|0|
|final|8.567088468323936e-9|0.0011585384956523822|13668|0|

Per-input error detail (QK0 in all cases; final equals AV):

| q/K/Hkv | softmax max abs / ULP | AV max abs / max relative / ULP |
|---|---|---|
|1/63/8|2.6299317237854503e-9 /2|8.567088468323936e-9 /1.0367606336859962e-4 /1452|
|1/63/2|3.072604951720459e-9 /2|7.678213825162983e-9 /6.581411129098427e-5 /724|
|1/257/8|5.752303000247649e-10 /2|3.9296950459302704e-9 /4.5882213055528446e-5 /583|
|1/257/2|6.193313379504461e-10 /2|4.814293301036790e-9 /0.0011585384956523822 /13668|

Absolute, relative and ULP maxima may occur at different elements. The large ULP
or relative maximum is retained along with absolute error; no tolerance was
selected to label these values PASS or GPU error. Full witnesses, zero-reference
cases, softmax mass descriptions and stage-level errors remain in JSON. Mutual
GPU equality does not replace this separate meaning check or qualify the decoder.

## Costs, authenticated evidence and limitations

PQ extra CPU-copy/API-upload/logical-slab/rounded-allocation bytes actually
executed here are each0, because all PQ executions were q1 common controls.
Original mask storage remains. This is **no evidence that repaired q>1 PQ is
free**: its fixed prospective costs and original buffers remain in the frozen
plan, but no q>1 upload, slab binding or specialized operator execution occurred.

`RAW_EVIDENCE.zip` contains all694 stopped-run files (36,684,307 raw bytes),
including actual authorization, OS preflight, ledger, all37 process lifecycles,
full support/physical/binding records, all36 returned stage vectors and input
before/after bytes, closeout and frozen independent reconstruction. Failed
eligibility's existing output is retained; unstarted output remains absent.
`RAW_MANIFEST.json` authenticates every path, length and SHA256; every archived
member was read back and rehashed. The archive is1,002,592bytes with SHA256:

`4371847d0f14af541f26fc754ee04a53797a3e0fe785e1d4f119adbc85353089`

The delivery-stage whole-v2 plus additional full raw-export reserve was
153,311,612bytes, below2GiB; final publication accounting is recorded separately.
`FROZEN_BINDING_RECHECK.json` rehashes all frozen code/runtime/driver/build/input/
serializer/reference/analyzer/history bindings after execution. Original S1
remains2 attempts/5.109s/159 unstarted; the seven diagnostics remain7 attempts/
13.172s/5 success/2 declared negatives. Nothing is backfilled into old slots.

No all-domain QH equivalence, successful complete panel, natural/unseen input
qualification, decoder reference qualification, performance gain, continuous
GPU residency, or permission to continue is inferred. These are the16 already
exposed synthetic inputs, with only q1 numerically entered. S2/S3, actor execution,
timing/profile and every further GPU task remain closed. PR112 stays Draft.
