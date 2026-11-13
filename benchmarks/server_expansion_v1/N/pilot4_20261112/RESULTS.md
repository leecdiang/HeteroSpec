# A5000 single-case resident/cold pilot: strict comparisons passed

Actual native run: `p4-36c27856d91b1c5b`, 2026-11-12 UTC. Base is PR231
301df2f2cb47a432c3d2afb84c69aaebb16ea3f0. The user approved the bounded
four-request pilot and then confirmed the selected GPU1 window without an
additional time restriction. The worker nevertheless had a600-second bound.

**The one supplied-history case passed the exercised numerical bridge.**
The native process exited0, its real systemd cgroup became empty/inactive, and
NVML observed zero processes from this experiment on the allocated UUID afterward.
No fifth request, second deployment, candidate arm, performance panel or N1a
expansion ran. The prior76-request proposal and old STATE/ledgers were not used.

| Actual request | Native rows | Complete requested F32 vectors | Raw capture bytes |
| --- | ---: | ---: | ---: |
| R1: old supplied state in resident A |186 |1 |28,034,560 |
| R2: independent old-state repeat in scratch B |186 |1 |28,034,560 |
| R3: reset B, cold canonical Q and fixed F8 |224 |137 |388,199,936 |
| R4: same A, trim186→88, Q suffix and fixed F8 |136 |136 |387,592,192 |
| Total |**732** |**275** |**831,861,248** |

One model object/deployment and two C4096/F16 contexts were used, on exactly one
allocated A5000 UUID. The original R numerical archives and reference helper
arithmetic were retained. Physical microbatch and output reserve were1, two
threads, flash attention disabled, CUDA graphs disabled by the frozen runtime
environment. Old materialization uses the original whole-initial-API/UB1 helper;
cold starts with its independently computed88-token prefix, and subsequent
suffix/continuation calls are q1. No Windows module, candidate core or modern
producer numerical library was substituted.

The requested-output mask is last-token-only for the whole initial/prefix calls,
and one full vocabulary row for every q1 suffix/continuation call. The275 saved
vectors therefore cover **all actually requested rows**, each151,936 F32 values.
This is not a claim that732 logits rows were requested or captured.

## What the raw comparisons establish

The source-bound native comparison passed, followed by an independent Python
reader that imported no model/runtime/CUDA code and reread the original GPU
captures. It performed137 complete F32 vector pairs and11 full active-KV pairs,
plus a separate retained-prefix comparison using the old/new per-head strides.
No hash, argmax or final-token substitution was an acceptance rule.

All22 active-KV snapshots contain both K/V for all36 layers, eight heads and
128 dimensions, with actual cell/position/sequence metadata. Native extraction
checks every F16 scalar finite; the independent replay checks full raw bytes,
tensor ordering, sizes and active-position coverage. All275 vectors were also
independently checked finite in full. No numerical first difference occurred.

The old state has186 materialized IDs and supplied pending EOG151645. Native
trim retained exactly88 positions; old retained bytes matched both their prior
snapshot and cold B's independently computed prefix. The caller discarded the
old pending token and treated the trimmed frontier as invalid until suffix decode.
Q-complete and all eight fixed-continuation outputs/states then matched.
The cold prefix's fresh vector was deliberately not compared to an invalid
resident post-trim frontier. That temporal exclusion was declared before GPU
execution. Both contexts were cleared at the end with native head-zero checks.

Raw record index and pair details:
`GPU_EVIDENCE/INDEPENDENT_RAW01.json`. Exact original private archive:
833,423,360 bytes, SHA256
`a4ab2f5e612fbb08a53066eb3d6f9e5c4bbcc00869c7876f1a395fa0edb1ba83`.
Archive readback verified all612 original indexed members by full size/hash;
the numerical qualification separately used raw byte comparison. Raw vectors,
KV and private process/job identities stay on the authorized server; the private
handover gives their location. Public text does not independently reproduce
private byte validation or constitute another GPU execution.

## CPU admission and failures

This was not an ordinary-file cgroup mock. Existing user-manager delegation
already exposed memory/pids, so no administrator, ACL, driver or system-policy
change was needed. New owned CPU services proved real64MiB memory.max, swap0,
pids8, parent/child membership, group cleanup and actual kernel OOM termination.
A source-identical standard-only PilotGate substitute then ran inside real
24GiB/pids128 limits, rejecting an excess row reservation before any native work
and refusing reentry after poison. That substitute loaded no model.

The model worker entered its real limited unit before native exec. The launcher
verified the fixed image/case, sealed the executable bytes, and durably reserved
the only deployment. The dedicated PilotGate is compiled to one run/output root,
checks actual cgroup limits and controller heartbeat, and charges requests/rows
before native calls. Existing ProductionGate and old binaries remain denied.
The systemd controller and worker were server-owned processes independent of SSH.

All unsuccessful CPU/build epochs survive: an early deactivation observer check,
a saved-token row discriminator error, one relative-header build failure and two
missing-helper build epochs. None consumed a model request. The sole native
attempt succeeded and was not retried. Executed original controller bytes remain
private; publication parameterizes three deployment literals only, with both
source identities in `GPU_EVIDENCE/SOURCE_PUBLICATION_MAP.json`.

## Cost and limits

The owned native service took302.389 seconds including complete8.7GB model-file
hashing, initialization, one model load, two contexts, decode, heavy capture,
comparison, IO and cleanup. It is not a generation benchmark. State capture read
about13.29GB of physical GPU tensor bytes to produce about664.73MB active KV,
in addition to167.13MB requested vectors. The139 read-only resource samples
observed up to9,065MiB GPU memory use and at least15,050MiB free. Peak sampled
cgroup memory.current was1,277,366,272 bytes; it is not total process RSS or all
shared-page residency. Sampling started before GPU initialization, after CPU
hash admission began; it is not an exact hardware high-water measurement.

The immutable STATE retains its initial `ADMITTED_SETUP` label because the pilot
did not update that descriptive field. It was not rewritten after execution.
Terminal status is established by completed4/rows732, native RESULT, real owned
unit exit0/empty group and post-run NVML release, rather than that stale label.
Host deadline/signals do not promise preemption of uninterruptible GPU/IO calls.

This is supplied-history materialization and fixed **input** continuation, not
free generation, a live chat producer or an EOG/cap generation test. The initial
old state was repeated in a fresh context in the same process/model; the whole
resident transition and independent-process/model-load repeatability were not
repeated. Comprehensive pending/EOG/cap, failure-rebuild, output-ownership and
reset controls remain for later qualification. The old261-check N1a graph is
not promoted to PASS by these four different requests.

## Decision

**Do not stop the resident lifecycle line on a numerical-mismatch assumption:**
the tested canonical suffix repair, retained prefix and fixed continuation were
strictly consistent on this case. This is a useful necessary feasibility result.

**LOCAL-specific value is still undecided.** The case was fixed before native
observations and has identical predicted whole-rechunk/LOCAL partitions. Common
LCP reuse benefits both; it does not establish a LOCAL advantage. Continue only
to prospectively bounded lifecycle repeat/boundary qualification and the already
frozen execution-opportunity cases, then compare equally optimized strong arms.
Do not move directly to timing or add samples to reach5percent. No further GPU
execution is authorized by this result; the4-request/1-deployment allowance is
exhausted even though only732 of8192 rows were needed.
