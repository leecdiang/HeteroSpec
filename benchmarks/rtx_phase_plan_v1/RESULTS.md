# Native resident phase plans: pre-confirmation freeze

Design input: PR188 actual head `de96c18ced307b480f360d4d88a85792fc71fd6c`.
The independent result branch is `codex/rtx-phase-plan-results` (PR190).

Both native paths are implemented, built and GPU-qualified against each family's
unchanged original R. SIMPLE derives maximal compatible whole-graph groups and
uses loop4; LOCAL keeps wide outer projection groups and uses local reference
prefix attention with packed projection. They share the cache/lifecycle repair,
original masks and requested-row owner, and retain one target/KV across phases.
No model-name, prompt-ID or registered-coordinate strategy branch is used.

The retained APPS/train/65 failure is repaired: actual cache requirements at its
observed head767 prescribe SIMPLE1+3 and LOCAL's four local extents
[768,1024,1024,1024]. All requested full-vocabulary vectors and committed active
KV/frontiers agree with independent original R. The old failed D binary/result
remains invalidated. Each final executable also passes all48 fixed boundary/width
cells. Qwen uses36 layers,32 query heads,8 KV heads and128-dimensional heads;
Smol uses24 layers,32 query/KV heads and64-dimensional heads. Exact candidate
bytes and the shared native rule were published at f9c9289a before new Smol
outputs. Both models' six M/D1/D4 arms pass full requested-vector and selected
initial/first-commit/terminal state qualification. Rejection after acceptance,
all-accept/bonus, unequal cap tails, reused contexts and native EOG are retained.
These are finite comparisons, not a theorem or an all-intermediate-state dump.

Clean actual public sequence-export/import/context-init API counts are zero.
The reference runs and heavy observations are separate, charged work. RTX's old
reference was already resident: zero migration alone is not a new RTX speedup.
Initial grouping clocks measure CPU plan generation, not GPU code generation.
Native decode/physical widths and CUDA activities are observed; host CUDA launch
API counts and separate CUDA graph construction/reuse counts are not invented
from the inherited graphs_reused field. Their work remains inside service.

Separate zero-drop CUPTI traces match the pre-output source predictions. SIMPLE
minus LOCAL MMVQ kernel activities are5229 on Qwen and2640 on Smol; quantization
differences are0 and-165 respectively. Smol's tail adds quantization work while
reducing MMVQ work. No speedup or device time is inferred from these counts.

One fixed development pass used four already exposed roots per family, each
with separate heavy qualification, immediate clean warmup and one measurement.
Complete measured resident-service totals (seconds) are:

| Arm | Qwen | Smol |
|---|---:|---:|
| SIMPLE-M |13.490382|3.007996|
| LOCAL-M |13.400889|2.833284|
| SIMPLE-D1 |11.656846|3.182386|
| LOCAL-D1 |11.102030|3.076649|
| SIMPLE-D4 |10.295108|2.716206|
| LOCAL-D4 |10.153777|2.615447|

LOCAL/SIMPLE D4 ratios are0.986272 and0.962905. Two Qwen roots regress; all four
Smol roots improve. Smol D1 remains slower than either M control. This single
pass supports a bounded confirmation, not a significance claim. No development
measurement is repeated or selected for a favorable time. The interrupted Smol
SIMPLE-D1 pass retains its first three completed measurements; a charged recovery
reconstructs the prior history and supplies only the missing fourth warm/measure.

The new panel freezes eight outcome-unexposed natural roots per family, all six
arms, six Williams sessions,576 measurements and576 immediate warmups. Raw source
roots are selected before native token admission; admission is capacity-only,
with no alignment or opportunity filtering. Original tokenizer/template roundtrips
pass12 historical inputs per family. No new test forward output precedes this
freeze. The primary total-service ratios, both fixed M contrasts, all15 paired
contrasts, root-cluster bootstrap and multiplicity handling are in the frozen
confirmation PLAN.json. Confirmation outcomes are pending in this commit.

All initialization/resource failures, partial raw states, failed reservations,
original-R teachers, builds, setup and warm/recovery work remain in the raw bundle
and unified costs. Lossless compression/chunk archives preserve every retired
raw byte. Native D/E output floors20GiB, C system10GiB, RAM4GiB and GPU128MiB
remain enforced. The separate bounded F cold archive has18GiB reserve; it is not
an active native output volume. Some CPU preparation components were not separately
wall-metered and are unknown, never zero or a claimed complete engineering total.

See REPRODUCE.md, RELATED_WORK.md and host_evidence/. Old results, B570 and arXiv
are unchanged; no AUTO/MMA extension, rental or merge is performed.
