# Stage A: zero-GPU audit of frozen M2

Status: Stage A complete. No CUDA context, model execution, compilation, new
native request, optimization candidate or Stage B–E timing was started. This
audit is pinned to protocol3268a63dcbde99d5d9f8dd461f34d56e9840d3a0 and frozen
M2 result2d076402b4ddc29c92549d360cd974af40d3f0a4. The protocol documents and all
old sources, baselines, results and paper remain unchanged.

The existing evidence explains a substantial work increase. It does not establish
a removable hotspot that changes the width decision. Keep the existing finite
k3 recommendation; no new hardware-performance or population claim follows from
this CPU-only audit. Equal-work diagnostics remain potentially useful, with the
fixture/admission issue below resolved first.

## Reproduced observations

All144 saved timed/primer receipts were checked against their original SHA
bindings and the fixed analyzer. Both complete live/replay tables and the full
three-epoch cost table reproduce. No prior failure charge is removed. These are
old M2 timings, not new measurements on the restarted server.

LOCAL-packed live has eight measured requests per k. Exact archived-scalar
accounting gives:

|Component|k3 seconds|k7 seconds|k7 minus k3 seconds|
|---|---:|---:|---:|
|Complete service|11.878693907|13.548504627|1.669810720|
|Target prefill|2.644503909|2.647892372|0.003388463|
|Target verify|4.689199546|5.318639008|0.629439462|
|Draft phases|3.171241107|3.852558470|0.681317363|
|Unassigned residual|1.373749345|1.729414777|0.355665432|

The residual is service minus the three phase categories. It contains other
operations and timer boundaries; it is not measured logging, allocation,
synchronization or kernel time. Target output-copy time is nested within this
residual:0.073760943 to0.091253893s, a0.017492950s increase (about1.05% of the
service increase). Planning decreases by about73 microseconds. Do not add these
nested fields to the residual again.

The copy field covers getters plus owned-vector assignment, including any
allocation inside that assignment. Outer-vector work, batch setup, sampling,
metadata and final synchronization have no separate complete attribution.
Removing the entire k7 copy field would be less than0.7% of k7 service, but that
is not an upper bound on every possible allocation optimization outside the
field. Full outputs and ownership are required, so deleting copies is not an
admitted optimization.

## Unaccepted proposals are not all observed incorrect tokens

|Live LOCAL-packed accounting|k3|k7|
|---|---:|---:|
|Proposed|864|1204|
|Accepted|736|852|
|First compared mismatch in rejecting cycles|58|74|
|Unexamined suffix after that mismatch|62|262|
|Unconsumed suffix at terminal accepted CAP|8|16|
|Terminal accepted EOG suffix|0|0|

Each column partitions proposed tokens exactly. The saved pilot has no terminal
EOG suffix in these roots; this does not replace the earlier EOG qualification.
Unexamined proposals after rejection are conditioned on a different prefix and
must not all be called incorrect tokens. A lower aggregate acceptance fraction
does not prove changed draft-model quality: both k values share the observed
proposal tape and visit different bases.

Target VERIFY rows rise1152 to1376; total target and live draft rows each rise
1868 to2092. Recorded VERIFY seconds per row decrease about5.04% for live and
3.91% for replay. These are descriptive per-row ratios over different trajectories,
positions and extents, not the equal-work q4pair/q8 experiment.

## Actual generated source and ownership

The fixed build chain is original qualified frontend → pinned transform.py →
the two added native headers → Linux entry insertion → recorded GCC compile/link
against unchanged qualified Linux CUDA archives. Text-only reconstruction of all
12 generated files matches the build inventory and current generated files
exactly. Current loop4, packed and pristine-R executable bytes match their saved
BUILD receipts and are ELF. Saved module-map commitments and current module file
bytes match. Model hashes are the historical full-hash bindings; this static
audit records current file sizes but does not reread the weight payloads.

The read-only generated copies in generated_frontend are the old compiled
frontend, not new candidate code. Linux entry.cpp owns main. The legacy Windows
main in worker.cpp is inside _WIN32 and is excluded by the recorded Linux compile
configuration. The default phase_target_reserve=4 is overridden and checked to8
before pool construction; the actual context parameters use that value. R stays
its separate unchanged UB1/reserve1 executable.

Source findings:

- resident_context.hpp:40,52 stores full vocabulary vectors in owning
  std::vector<float> buffers. Sample/capture reads them after decode. They remain
  valid until the next decode/reset changes that owning context; these are not
  borrowed llama logits views with indefinite lifetime.
- outputs.assign(count,{}) does not imply a fresh allocation for every inner
  vector on every stable-width cycle. In the bound GCC11 vector.tcc, outer
  fill-assignment invokes inner copy-assignment from an empty vector; with the
  standard allocator and adequate capacity, the inner allocation is retained.
  Range assignment can reuse it. Reset/clear, size changes and destruction can
  still destroy buffers. The exact header SHA matches both compiled dependency
  closures. Replacing assign with resize/clear alone is not evidence of a speedup.
- For a future q4pair diagnostic, the first four owned outputs must survive the
  second decode. Merely reading the context's last four rows afterward violates
  the eight-output contract. Both paths need equivalent explicit output ownership.
- Target phase clocks include llama_decode, batch-free and an explicit
  synchronize. Target getters/copies occur afterward in output_copy_s. The
  bound llama_get_logits_ith wrapper also calls context synchronization; these
  calls may already be satisfied. No saved field separates their wait/host cost.
- Target finite checks/argmax run for all requested rows, even rows unused after
  acceptance terminates. Draft sampling does the same finite/argmax scan for
  every proposed token. Source-derived explicit synchronize API sites for this
  live pair are3516/4188, not measured CUDA waits or launches. Counts alone do
  not establish synchronization inefficiency.
- request() begins service timing before reset/setup, then includes prefill,
  native drafting/replay, verification, output ownership, sampling, transaction
  bookkeeping and final synchronization. In-memory receipt assembly also occurs
  before the service endpoint. Entry adds some fields and writes receipt/result
  files with fsync only after request() returns. Those disk writes belong to
  process/burst costs, not the service residual.
- The last proposal forward materializes draft KV for the all-accepted path.
  After keep=base+1+accepted, that KV is needed when the next pending bonus is
  synchronized. It is not universally dead work. Deleting it, changing cap-aware
  proposal depth or skipping draft-state updates changes lifecycle/output policy
  and is outside a quick buffer optimization.

Unmeasured candidates for later profiling include finite/argmax scans, the cost
of synchronization entry points, batch/metadata allocations and request-boundary
buffer destruction. None is declared a measured removable hotspot. No tolerance,
output policy, draft depth or synchronization behavior was changed.

## Stage B fixture admission is not ready

The registered states need a frozen token stream of at least256 tokens for
position248 plus8, and260 for position252 plus8. The four original roots have:

|Original order/root|Prompt|Frozen R continuation|Available tokens|Missing to260|
|---|---:|---:|---:|---:|
|MATH/geometry/train/333|71|128|199|61|
|MATH/algebra/train/313|68|128|196|64|
|MATH/intermediate_algebra/train/315|150|128|278|0|
|MATH/geometry/train/654|69|128|197|63|

Only one origin has enough existing token IDs. This is a data/admission gap,
not a numerical failure. It also affects the first prespecified timing origin.
Existing states from different roots cannot substitute just because their
positions match. Even the long origin's known IDs do not establish a reusable
R state/complete output proof at248/252 by themselves.

Before Stage B, explicitly register either an authorized unchanged-R continuation
extension with exact oracle/bridge/request/row accounting, or an amended origin
design. Do not pad, silently replace roots, invent tokens or assume an extension
will avoid EOG. New reference work may fit the existing24-request oracle allowance
only after exact enumeration; no budget increase or automatic transfer is assumed.
The registered B ceiling remains32 qualification +16 timed +8 primers +24 oracle/
bridge/failure requests. No GPU admission manifest or available execution window
has been approved by this Stage-A-only task.

## Reproduction, budget and limits

audit_saved.py reads the retained raw jobs/receipts, checks source/receipt
commitments, invokes the fixed archived analyzer and cost reader, then produces
the additional accounting and origin inventory. audit_bindings.py reproduces
generated text and hashes files; it never compiles, loads a CUDA backend or runs
an ELF executable. Use a fresh output path and the retained predecessor layout.
Public consumers can use the immutable M2 archive and the public data-only replay
helpers linked from the parent result. Raw capture payloads/weights are not in
this audit. Raw/derived file commitments are in PUBLIC_RECORD_INDEX.json.

PR197 is unchanged at1826/2048 requests and3021131/8000000 conservative reserved
rows, leaving222 requests and4978869 rows. Stage A charges zero native requests.
The saved M2 native-worker wall total remains13437.936s; this is historical
process wall, not GPU kernel time or today's audit CPU cost. CPU/file/SSH work
of this audit exists but has no separately instrumented aggregate timer.

The host reboot preceding this audit is recorded privately. Driver595.84 and
file identities are observations, not a new post-reboot numerical qualification.
Stage B–E and32B GPU work were not run. Old k3 remains the supported finite
recommendation; Stage A does not settle intrinsic equal-work q8 efficiency or
prove that no future common optimization can help. No merge, Release, paper
edit, baseline overwrite or data deletion.
