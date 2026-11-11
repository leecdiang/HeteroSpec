# Frozen comparison and execution rules for aligned numerical v2

This new finite panel uses the16 already exposed synthetic S1 inputs byte-for-byte.
It does not resume old S1 or repeat the seven diagnostics. QH_C is fixed primary.
No GPU launch is authorized by preparation, compilation, CPU tests or this file.

Plan: one charged80-graph-descriptor support census, then160 graph hosts:
16 inputs × MQ/PQ/QH_C/QH_D/REPEAT4 ×2 separate process creations. All40 q1
graphs precede the120 q>1 graphs. Input order is the original input-manifest
order, stable partitioned q1 first; within input: repeat0 modes in the listed
order, then repeat1 modes. No negative crash slots, retries, warmups or probes.
All80 repaired census graphs must admit every actual executable node or stop.
The census never computes a graph and never selects a new primary candidate.

Ceilings:161 host attempts,160 graph calls,3600 cumulative owned seconds,
180 seconds/host,2GiB total v2 artifacts. The supervisor also reserves a full raw
copy plus ZIP overhead within2GiB for export. Preparation/build bytes in this
new directory/output root are included in storage accounting. Worker sampled
RSS<=8GiB, available host RAM>=8GiB, disk>=4GiB;100ms nominal supervision,
actual gap<=1000ms. GPU free memory>=512MiB at checkpoints, no continuous
residency claim.0 models, extra probe, warmup, scientific retry or automatic S2/S3.
Owned wall includes process setup/device initialization/copies/readbacks/logs;
it is not graph latency and cannot generate speed claims.

One native parser, graph builder and descriptor serializer serve census,
execution and the CPU-only metadata binary. The actual CPU binary parses all161
formal wire files:80 census descriptors +160 numerical descriptors, without
device initialization or graph computation. Every wire carries run_id, slot_id
and a prospective execution-binding SHA; F0 binds that binding and all actual
wire bytes. Avoiding a self-referential F0-in-wire hash is intentional.

Only storage repairs: all Q views offset0 at independent Q storage origin;
PQ q>1 has independent per-query mask slabs. The original32-row mask stays
allocated. Q shape/stride, logical Q/K/V/mask bytes, F32/F16 types, arithmetic
operations, precision, K63/257 and output restoration remain. QH_CONT,
QH_D mask REPEAT and REPEAT4 KV REPEAT remain real operators. PQ extra CPU
copy/API upload/logical bytes and observed allocator rounding are separate costs.
No assertion/shader/reduction/backend change or CPU fallback is introduced.

The deployment condition freezes required alignment64 from the prior diagnosis,
not an eternal backend constant. Each charged host reads the actual interface
and stops on mismatch. All roots/views have bounds and ownership observations.
Only executable nodes and their actual operands impose descriptor conditions;
disconnected old mask views remain recorded and do not fail descriptor gates.
Strict matvec/softmax and this panel's conservative matrix-start precondition
require zero descriptor delta. Unary CONT/REPEAT and CONCAT have their frozen
element-offset encoding limits; no allow_misalign override is made.

Strict structural gates: exact graph signature versus CPU-frozen descriptors;
actual complete supports_op; B570/direct Vulkan device and bound ownership;
root/view bounds; source header/byte lengths; input before/after bytes;
original KV objects (or explicitly actual REPEAT of them), affine Q/GQA/mask
source addresses and scales/precision; exact stage element counts/layouts;
AV-to-final bit-preserving output restoration; all GPU QK/softmax/AV/final
values finite; explicitly -infinity-masked softmax elements exactly zero.
Softmax mass error is separately descriptive, not a chosen tolerance gate.
An assertion/crash or malformed/incomplete raw record stops.

Independent reference: decode actual stored F32 Q, F16 K/V and F32 mask bytes.
Logical j,h,GQA loops with fixed-order scalar binary64 dot/exp/normalization/AV;
scale first rounds to F32(1/sqrt128). No candidate pack or graph helper enters
the reference. Frozen FP64 vectors and source hashes are retained separately.
Absolute error, relative error where defined, zero-reference cases, ULP against
the F32-rounded reference, nonfinite counts, witnesses and first nonzero-error
stage are reported. Error bins are descriptions, not acceptance thresholds.
There is no GPU/FP64 bitwise requirement or post-result tolerance selection.

All QK/softmax/AV vectors restore to logical j,h,element order independently:
MQ uses query axis1; PQ uses separate part j; QH uses compute-head h*q+j;
REPEAT4 uses fourth-axis j. The final vector is already j,h,d. Every complete
stage and every element is compared. All10 mode pairs at each input/repeat are
reported, along with first bitwise divergence stage and abs/relative/ULP metrics.
MQ/PQ/QH_D/REPEAT4 bitwise relations are not assumed from CPU history.

Hard process controls: same implementation's repeat0/repeat1 must be bitwise
equal at all four stages and come from separate Popen creations, identified by
actual PID plus OS creation FILETIME. All modes/repeats of a given q1 input
must be bitwise equal to the common MQ control at all four stages. Such failures
stop later slots. q>1 ordinary finite cross-mode or FP64 rounding differences
are retained without changing the candidate/input/mask/tolerance or deleting
coordinates. Neither mutual PQ/QH equality nor a small scalar error alone is
an independent meaning certificate or broad numerical qualification.

Missing, native-failed, structurally invalid and unstarted slots are distinct.
The offline reconstructor reports the complete161-coordinate denominator and
all available relations; incomplete panels cannot claim full-domain passage.
History remains immutable. No dynamic data are manufactured during preparation.
Only after this panel actually completes can equivalent natural-actor layout
and mask processing be reviewed; any request pilot needs a separate F0/approval.
