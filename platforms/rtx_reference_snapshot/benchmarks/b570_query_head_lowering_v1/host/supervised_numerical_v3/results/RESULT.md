# v3 executed and stopped: partial numerical evidence, no global PASS

Reviewed execution commit `8008be6ce831a86b3074e16f57a6746187775491`, run_id
`b570-supervised-numerical-v3-20261015-01`, approved F0 SHA256
`56f5787e41dcf8dcc4ecad83eb26bf406a483664e67a939dc66edf0af5015fdc`.
The exact frozen absolute-path entry was invoked once after the current human
confirmation was independently recorded. Admission verified frozen identities,
all wires/references/history and an absent new run root; OS preflight found no
conflicting task. No F0, numerical/supervision rule, input or program was changed.

**The panel stopped incomplete on the initial directory observation deadline.**
There are nevertheless real q2/q3 numerical results: PQ/QH_C/QH_D/REPEAT4 agree
bitwise at all four stages on every available same-input/repeat comparison;
MQ agrees at QK/softmax but differs at AV/final for every available q>1 comparison.
Those finite differences were retained, not treated as a reason to change the
candidate/tolerance or stop. The actual stop was monitoring, with no retry or
additional GPU task afterward. QH_C remains the fixed primary candidate.

## Actual attempts, failure and complete missing inventory

| Experiment hosts | Planned | Started | Admitted | Invalid | Unstarted | Graph calls |
|---|---:|---:|---:|---:|---:|---:|
| Complete support census |1|1|1|0|0|0|
| Numerical |160|116|115|1|44|115|
| Total |161|117|116|1|44|115|

All80 census descriptions admitted every executable node without graph compute.
All115 started numerical graphs returned status0, complete finite four-stage
outputs, unchanged inputs, correct binding/ownership/bounds and exact AV-to-final
restoration. All117 experiment PID/creation-FILETIME pairs are distinct.

The failed host is plan index116, q3/K257/H8/Hkv2/MQ/repeat1, slot
`1bc547f9d4b5d289813e5f1eb71114c14ef3f902e6636b29da436f0ca4da173a`,
PID42788. Its identity audit passed but **GO was never sent**. The initial
directory scan had not produced a valid result when the coordinator observed
1,016,000,000ns since launch, exceeding the frozen1,000,000,000ns initial interval.
The resource stream continued while the directory stream was pending.

| Actual boundary | Monotonic ns | Offset from launch |
|---|---:|---:|
|Launch|53681015000000|0|
|Directory read begins|53681156000000|141ms|
|Identity admitted|53681609000000|594ms|
|STOP and target termination requested|53682031000000|1016ms|
|Directory read discarded|53682046000000|1031ms|
|Coordinator confirms target exit|53682078000000|1063ms|

The discarded scan's recorded read duration was890ms, but its first completion
deadline includes launch/startup. It has no admitted values and cannot repair
initial coverage. It was discarded after termination was requested. Target
exit1 is the supervisor's termination, not an observed shader assertion. There
are no GRAPH_START/RETURN/OUTPUT events, vectors or actual graph bindings for
this failed host. This is no claim that initialization executed no shader.

Monitor PID14932 exited0. Auditor PID45192 recorded POST_AUDIT_BEGIN and then
AUDIT_ERROR `complete child close event`, exiting1 after target termination.
This is a retained failed closing audit, not a predeclared expected failure.
The failed lifecycle's post-audit success/end remain missing. No successful
post-audit duration is invented for it.

The44 unstarted slots are exactly:

- q3/K257/Hkv2/repeat1: PQ,QH_C,QH_D,REPEAT4 (indices117..120).
- Every q4 input K63/257 ×Hkv8/2 ×five modes ×two repeats (indices121..160).

Full slot IDs/statuses are in `SUMMARY.json` and `INDEPENDENT_RECONSTRUCTION.json`.
The failed MQ repeat1 is not counted among the44 unstarted coordinates.

## Separate time, monitoring and process costs

Whole frozen controller engineering wall through closeout: **218.921s**;
external launch-to-controller-return wall219.1024221s. Both are below3600s.
Admitted complete-slot engineering max2.734s; failed slot through lifecycle
commit1.203s, below180s. Sum of admitted slot costs216.435s; controller wall also
includes preflight, inter-slot work and failed cleanup, so these are not identical.

Observed native lifetimes sum92.439s, max1.500s, over117 experiment hosts.
Successful post-exit audits:116, sum118.951s, max1.594s. These are distinct timing
scopes. Post-audit delay>1s did not expand live coverage or invalidate those
otherwise-qualified hosts. The failed host has a failed audit event, not a
successful duration. These observations do not decompose old v2's1.032s.

| Admitted hosts' monitor stream | Valid reads | Max read duration | Max initial completion | Max effective inter-observation | Max terminal interval |
|---|---:|---:|---:|---:|---:|
|Resource|754|16ms|234ms|110ms|141ms|
|Directory|132|844ms|985ms|844ms|907ms|

All admitted intervals use unrounded integer source ns under the exact1s rule.
Directory exit races produced34 discarded reads among admitted hosts; none
contains invented resource values. The failed host's1016ms first-directory gap
is reported separately, not hidden by the admitted-host maxima. FILETIME is
independent OS evidence, never mixed into these intervals. Original source-clock
timestamps are retained; ns units do not claim a timer's nanosecond resolution.

One controller ran separately. CPU control workers: **117 monitors +117 auditors
=234**, within322. All monitors exited0;116 auditors exited0 and the last exited1
as above. Aggregate helper kernel+user CPU time281.203125s is a CPU-time sum over
parallel processes, not wall time. Monitoring uses two reading threads per
monitor plus its main; auditor has its main. Native internal OS/driver thread
totals are not inferred. Delivery tools are separate, not experiment hosts.

Peak sampled native RSS109,367,296bytes; during live-target monitoring the peak
sampled control RSS was112,263,168. Another20,116 post-exit CPU-control readings
had peak RSS114,827,264bytes, all within8GiB and all after target exit; they are
not target resource samples (`POST_CONTROL_CHECK.json`).
Minimum host available RAM19,840,438,272bytes; disk158,430,789,632. All463 in-host
GPU memory checkpoints had free>=9,722,339,328bytes. Actual interface alignment64
was recorded by all117 hosts. No continuous GPU residency or performance claim.

## Complete geometry and four-stage relationships

`====` means bitwise equal at QK/softmax/AV/final; `==DD` means QK/softmax equal,
AV/final different. Every comparison uses full restored vectors. Available
repeats are both0/1 unless only0 is shown. All geometries have H8,d/dv128.

|q|K|Hkv|Admitted / invalid / unstarted|Available repeats|PQ/QH_C|PQ/QH_D|MQ/REPEAT4|
|---:|---:|---:|---|---|---|---|---|
|1|63|8|10/0/0|0,1|====|====|====|
|1|63|2|10/0/0|0,1|====|====|====|
|1|257|8|10/0/0|0,1|====|====|====|
|1|257|2|10/0/0|0,1|====|====|====|
|2|63|8|10/0/0|0,1|====|====|==DD|
|2|63|2|10/0/0|0,1|====|====|==DD|
|2|257|8|10/0/0|0,1|====|====|==DD|
|2|257|2|10/0/0|0,1|====|====|==DD|
|3|63|8|10/0/0|0,1|====|====|==DD|
|3|63|2|10/0/0|0,1|====|====|==DD|
|3|257|8|10/0/0|0,1|====|====|==DD|
|3|257|2|5/1/4|0 only|====|====|==DD|
|4|63|8|0/0/10|none|UNKNOWN|UNKNOWN|UNKNOWN|
|4|63|2|0/0/10|none|UNKNOWN|UNKNOWN|UNKNOWN|
|4|257|8|0/0/10|none|UNKNOWN|UNKNOWN|UNKNOWN|
|4|257|2|0/0/10|none|UNKNOWN|UNKNOWN|UNKNOWN|

All40 q1 common controls pass; q1 remains a degenerate common graph under all
five labels. All55 available independent-repeat pairs (20q1+20q2+15q3, out of80
planned) are four-stage bitwise equal with distinct actual process identities.
The other25 repeat pairs are incomplete. No old v2 result is used as a repeat.

## All ten mode pairs and a concrete counterexample

Each pair has23/32 complete same-input/repeat comparisons and9 missing/invalid.
Across pairs:230 available and90 missing/invalid out of320.

|Pair|Four-stage equal|First divergence for differing comparisons|QK/softmax max abs/ULP|AV/final max abs|AV/final max ULP|
|---|---:|---|---|---:|---:|
|MQ/PQ|8/23|AV,15/23|0/0|3.858376294374466e-5|1824759808|
|MQ/QH_C|8/23|AV,15/23|0/0|3.858376294374466e-5|1824759808|
|MQ/QH_D|8/23|AV,15/23|0/0|3.858376294374466e-5|1824759808|
|MQ/REPEAT4|8/23|AV,15/23|0/0|3.858376294374466e-5|1824759808|
|PQ/QH_C|23/23|none|0/0|0|0|
|PQ/QH_D|23/23|none|0/0|0|0|
|PQ/REPEAT4|23/23|none|0/0|0|0|
|QH_C/QH_D|23/23|none|0/0|0|0|
|QH_C/REPEAT4|23/23|none|0/0|0|0|
|QH_D/REPEAT4|23/23|none|0/0|0|0|

First example: q2/K63/Hkv8/repeat0, logical query0/head0/d0, AV (and final).
MQ=-0.00011706352233886719; PQ/QH_C/QH_D/REPEAT4=-0.00012361817061901093;
independent scalar FP64=-0.00012361304536925508. Thus MQ bitwise equality to
the other modes is disproved on these actual operands. The first AV element
differs even though the complete QK and softmax arrays agree. This is not a
dynamic attribution to a unique shader, precision path or reduction; none was
profiled or modified. Full indices, raw bits, all pair/stage metrics and missing
coordinates are retained in `ALL_STAGE_RELATIONS.json` and `NUMERICAL_BREAKDOWN.json`.

## Independent FP64, not a pairwise-only certificate

The separate CPU reconstruction freshly decodes all16 original stored inputs,
recomputes scalar QK/softmax/AV/final and matches all64 frozen FP64 vectors
byte-for-byte. All115 GPU raw-stage layouts are independently restored, checked
against native input/slab/source addresses, and matched to the auditor's stored
normalized bytes. Before/after bytes and original KV ownership pass. This is
not native CPU graph computation or GPU fallback. The pure CPU delivery process
took24.797s and started no subprocess/device/model/graph.

QK error to FP64 is0 for all115 hosts. Softmax maximum absolute error is
3.5764847299002422e-9, maximum defined relative2.1480298907265481e-7 and ULP3.
The first scalar difference is softmax, distinct from the first cross-mode
difference AV. All outputs are finite; masked softmax zeros and full stage counts
are checked by the unchanged independent analyzer.

|Mode,23 admitted hosts each|AV/final max abs to FP64|Max defined relative|Max ULP to F32-rounded FP64|
|---|---:|---:|---:|
|MQ|3.8581274510109294e-5|1.8514231259384153|1824765211|
|PQ|1.2325743438488385e-8|0.0023201451097174374|35835|
|QH_C|1.2325743438488385e-8|0.0023201451097174374|35835|
|QH_D|1.2325743438488385e-8|0.0023201451097174374|35835|
|REPEAT4|1.2325743438488385e-8|0.0023201451097174374|35835|

Relative/ULP maxima and absolute maxima may occur at different elements; signed
values near zero can produce large ordered-ULP distances. All maxima/witnesses
are kept. No tolerance was selected after observing this separation; mutual
equality does not replace scalar meaning, and finite errors are not automatically
called either PASS or GPU error. No remaining q4 GPU data are manufactured from
its available CPU references.

## Non-free storage/copy costs and authenticated evidence

PQ q>1 actually ran15 times. Extra CPU-copy/API-upload/logical-slab bytes total
**22,516 each**, with23,616bytes allocator rounding derived from actual alignment64.
Original32-row mask storage remains allocated/uploaded in addition; extra slab
before/after readbacks are retained. These are logical/API amounts, not measured
VRAM residency or DRAM traffic. Per-geometry amounts remain in NUMERICAL_BREAKDOWN.

Actual submitted graphs retain30 packed-Q CONT nodes (303,104 logical bytes),
15 QH_D mask REPEAT nodes (180,128 logical bytes), and15 REPEAT4 graphs with
two actual KV REPEAT nodes each (15,594,496 extra root logical bytes). Their
complete support, binding/ownership and successful graph records remain; no
operator is silently removed or its copy/storage treated as free.

`RAW_EVIDENCE.zip` preserves all4,995 stopped-run files /124,879,060 raw bytes,
including authorization, preflight, all lifecycle/state/monitor/auditor/module
records, complete native inputs and stage/normalized vectors, the failed host's
missing output, and all controller relations/closeouts. Archive6,369,030bytes,
SHA256 `19e0c975b62879375cd826c1673b9059aa96238cd8c5419b91a314a255989188`.
Every member was read back and rehashed against RAW_MANIFEST. No file in the
stopped run root was added, overwritten or repaired by delivery.

`BINDINGS_CHECK.json` verifies all586 frozen bindings and694 old v2 raw files
unchanged. The
delivery-stage full v3 plus additional raw-export reserve was332,600,604bytes,
below2GiB; final publication accounting is separate. The confirmed F0 stays
byte-identical, including its historical preparation status; current approval
is carried by separate actual-time authorization records.

Old v2 stays37 attempts/36 admitted/1 invalid/124 unstarted/36 calls/41.327s;
old1.032s is neither decomposed nor requalified. S1 stays2/5.109s/159 unstarted;
the diagnostics stay7/13.172s/5 successes/2 declared negatives. No samples are
merged between runs. These16 operands are exposed synthetic inputs, not unseen
natural prompts. The panel is incomplete and establishes no global QH bitwise
equivalence, full decoder qualification or speed gain. S2/S3, actor, performance
timing/profile and every further GPU task remain unstarted. Keep PR112 Draft.
