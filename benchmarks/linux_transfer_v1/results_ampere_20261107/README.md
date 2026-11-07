# Independent Linux Ampere deployment transfer

Native qualification and the complete fixed24-worker panel pass. All384 measured
requests and48 primers match independent free R endpoints and valid transactions.
LOCAL-packed-D4 reduces total measured service by17.2–18.4% against each of the
four fixed M controls and2.0% against SIMPLE-loop4-D4; all five adjusted interval
upper bounds are below1. These are conditional deployment-transfer results on
the fixed exposed roots and four observed sessions, including the disclosed
admission interruption.

This branch starts at the actual PR196 head
`2cfe56e13296d6b81463a9228c4fbfafa6f23e0c`. It ports the pinned PR195 method to one
explicitly allocated RTX A5000, builds an independent pristine-upstream Linux R,
and retains all four true target-only M controls plus SIMPLE-D4 and LOCAL-D4.
The sixteen old Qwen roots are **exposed deployment-transfer inputs**, not new
blind confirmation. Original Windows references, scientific releases and the
manuscript remain unchanged.

## Source, deployment and reference

See [ENVIRONMENT.json](ENVIRONMENT.json) for exact build/tool identities. The
observed platform is Ubuntu22.04.5, kernel5.15, RTX A5000/SM86, driver595.84,
CUDA12.5.40 and GCC11.4; the experiment uses two runtime threads and two compile
jobs. Analysis uses Python3.11.14 and NumPy2.3.5. GPU UUID, company paths, raw
process inventories and unrelated host details remain private.

The authenticated39MB source kit and exact pristine upstream commit
`0cae43063cf15170e91a2ff4d034da0ecef4a1b2` are fixed by `pins.json`. All three
roles freshly compile their llama, ggml-base, CPU and CUDA numerical modules,
including143 real CUDA translation units per role. Internal linking is static;
the actual vendor CUDA/driver ELF dependencies are separately hashed. No Windows
numerical DLL or newer upstream tree participates.

The port changes POSIX clock/hash/file handling, module enumeration, GPU placement
observation, allocated thread configuration and offline heavy-capture coverage.
It makes no numerical-core edits. Compiler dependency closures, generated files,
actual compile/link commands, response files, maps and source manifests are kept.
The source archive fallback verifies both the complete Git tree and original
signed commit object. The candidate projection cores differ only in
`src/llama-graph.cpp`; their backend source is identical.

Before any candidate forward, the independent R repeats passed550 capture-pair
comparisons:526 full requested-logit vectors,12 frontier checks and12 complete
serialized sequence-state checks. Its freeze is
`fa8ceec6d54f98730d63880436a6bf088c119232c0f091406725e724a4665731`.
R uses whole-prompt callers, physical UB1, last-only prompt output, reserve1,
C1024 and F16 K/V without FlashAttention. Candidate reserve4 and target UB32,
two threads instead of the old24, inherited graph reuse and inherited CUDA
`-use_fast_math` were declared before freezing R. This validates the method
against R on this deployment; it does not assert Windows/Ampere bit identity.

## Finite numerical and execution qualification

[QUALIFICATION.json](QUALIFICATION.json) binds all20 native comparison reports.
Both model families pass all four cut/projection M paths and both D4 paths.
The geometry panel covers the retained boundary witness, q1/4/8/32 inside,
crossing and tail cases, and all requested q4 outputs. Its96 arm/family cases
produce216 full-vector and96 committed active-state comparison records.

Natural qualification uses four exposed roots per family, separate free R
endpoints, independently rebuilt forced prefixes, heavy/clean pairs and cap1.
Including cap1, it compares6,524 originally requested complete vectors, plus
frontiers at every observed committed boundary. Together with geometry and
terminal/cap repeats, all4,784 serialized-state comparison records also have
identical raw bytes. The reviewed parser checks dense seq0 positions, all F16
K/V tensor values and layers, exact layout and no trailing bytes. Full vocabularies
are151,936 for Qwen and49,152 for Smol; no floating tolerance is registered.

First and later rejection, trim/rollback, pending and terminal materialization,
cap1/cap128 and reset are checked against independently reconstructed prefixes.
Native EOG is observed on the old Smol `CodeContests/valid/66` input, terminating
at100 generated tokens, across all six paths. Both D4 paths physically prefill
the draft at UB4 with k3. Real M paths create one context and execute no draft;
D4 creates two contexts. Native occupied-width histograms, decoded rows and append
frontiers match actual execution tables. Clean state export/import, heavy capture
and within-service context-creation counters are all zero. No online R replay
or KV migration is added to clean requests. These are finite observation claims,
not a universal equivalence theorem.

## Retained engineering failures and continuation

The first qualification worker packed all12 heavy geometry cases together and
reached the unchanged900s ceiling. Its complete nine cases were diagnosed as
numerically equal, but none counted as completed qualification. Epoch02 uniformly
uses3 geometry cases per candidate worker, re-executes every candidate case and
validates the original completed independent R matrix before reuse. All charged
requests/rows and failed artifacts remain in the shared ledger.

After the first valid formal worker, the old request-hash-only retry guard blocked
the next control before reservation or native launch: loop4 and packed M jobs
legitimately share request JSON. The admission repair binds the original frozen
slot, numerical build and request, retaining protection against true retries.
All46 helper checks pass normally and under `-O`, including six guard regressions.
The explicit continuation validates and preserves the first completed worker,
archives the empty blocked output, and executes only unstarted original slots.
Numerical binaries, frozen plan/jobs, input order, service clocks and first-worker
receipts remain unchanged. The pause after the first worker and all original
failure/status records remain visible. No attempted failed formal native slot is rerun.

## Formal panel and clock scope

| Arm | Test service (64), s | Primers (8), s | Test burst (4), s | Worker wall (4), s | Max observed device MiB |
|---|---:|---:|---:|---:|---:|
| W_L4_M | 174.553 | 17.597 | 174.643 | 203.715 | 8538 |
| W_P_M | 172.146 | 17.415 | 172.233 | 200.739 | 8528 |
| L_L4_M | 174.640 | 17.590 | 174.732 | 203.983 | 8538 |
| L_P_M | 172.246 | 17.443 | 172.334 | 201.066 | 8528 |
| W_L4_D4 | 145.449 | 13.198 | 145.541 | 172.271 | 9266 |
| L_P_D4 | 142.523 | 12.967 | 142.609 | 168.973 | 9256 |

| LOCAL-packed-D4 / fixed control | Total service ratio | Adjusted interval |
|---|---:|---:|
| W_L4_M | 0.8165 | [0.7476, 0.8723] |
| W_P_M | 0.8279 | [0.7539, 0.8883] |
| L_L4_M | 0.8161 | [0.7472, 0.8726] |
| L_P_M | 0.8274 | [0.7539, 0.8875] |
| W_L4_D4 | 0.9799 | [0.9756, 0.9856] |

| Arm | Launch to first complete result, s (min–max) | Launch to first test result, s (min–max) | Model-load episode, s (min–max) |
|---|---:|---:|---:|
| W_L4_M | 4.737–4.867 | 9.000–10.384 | 1.758–1.783 |
| W_P_M | 4.643–4.785 | 8.965–10.282 | 1.711–1.783 |
| L_L4_M | 4.758–4.824 | 9.072–10.363 | 1.759–1.771 |
| L_P_M | 4.757–4.828 | 9.048–10.290 | 1.764–1.870 |
| W_L4_D4 | 4.663–4.804 | 7.796–9.547 | 2.227–2.274 |
| L_P_D4 | 4.608–4.699 | 7.670–9.401 | 2.230–2.277 |

Ratios below1 favor LOCAL-packed-D4. Tests, primers, burst and worker wall are
separate inclusive windows; their totals must not be added. The memory column
is the maximum sampled global-device observation across four workers, a lower
bound on true peak. Full precision, per-root and per-session ratios and geometric
sensitivity remain in [RESULTS.json](RESULTS.json). All432 ordered request rows,
output token IDs/EOG flags, physical row counts and raw receipt hashes are in
[REQUESTS.csv](REQUESTS.csv). All per-worker windows and distributions are retained
in [CLOCK_SUMMARY.json](CLOCK_SUMMARY.json).

The fixed panel has four predeclared cyclic sessions, six arms per session, one
resident load/setup episode and two primers followed by16 distinct reset requests per worker:
384 measured requests plus48 primers. Four cyclic rows are not a full six-arm
Williams design. All M baselines remain real target-only services.
An M episode loads only the target; a D4 episode loads target and draft. The
record's `model_loads:1` denotes one episode, not one GGUF file for D4.

The primary contrasts compare LOCAL-packed-D4 to each fixed M and SIMPLE-loop4-D4.
Analysis uses10,000 PCG64 root-cluster draws, keeps the four sessions together
within each root, and reports five-comparison Bonferroni percentile intervals,
absolute totals, per-root/per-session ratios and equal-root geometric sensitivity.
Inference is conditional on these sessions, including the disclosed interruption;
no Windows timing is pooled and no posthoc minimum-M baseline is selected.

In these four cyclic rows, SIMPLE-loop4-D4 always immediately precedes
LOCAL-packed-D4. Their observed2.0% service difference simultaneously changes
cutting and projection, and fixed order can confound it with warmup/time drift.
The narrow root-cluster interval does not remove this ordering factor. This panel
therefore does not identify an independent causal LOCAL effect. A subsequent
four-D4 factorial panel with balanced positions and directed predecessor pairs
is a separate prospective experiment; this completed panel is not reordered or
rerun after its outcomes.

Service includes reset, planning, output ownership, target/draft execution,
sampling and synchronization. Startup/first complete result/test-burst/worker
wall are actual subprocess and marker-arrival clocks. First response is not TTFT.
The supervisor's artifact verification/input acquisition precedes subprocess
startup; these are not amortized into a fabricated setup/N latency. Memory is
selected-device global usage sampled about every2s, a lower bound on true peak,
not a per-process high-water mark. Phase costs are host envelopes; unmeasured,
partial and inapplicable nested costs remain null with explicit coverage counts.
Inclusive windows must not be added together. No network endpoint/QPS or
unmeasured asynchronous device-time claim is made.

## Rebuild and evidence access

[ALL_SLOT_STATUS.json](ALL_SLOT_STATUS.json) retains all24 COMPLETE native slots.
[BUDGET.json](BUDGET.json) records857 charged logical requests and1,552,339 reserved
rows against unchanged2,048/4M limits, including the failed qualification worker;
no failure is refunded. The blocked formal admission was never reserved or
executed. The original failure statuses and explicit continuation receipt remain
in the exported record. [MEASUREMENT-COST-COVERAGE.json](MEASUREMENT-COST-COVERAGE.json)
and [PRIMER-COST-COVERAGE.json](PRIMER-COST-COVERAGE.json) separately preserve
measured/present/expected counts and null unknown costs for all six arms.

Follow [REBUILD_NATIVE.md](../REBUILD_NATIVE.md), the original protocol and pinned
public inputs. Source/build/freeze receipts, complete request records, controls,
clock/resource observations and failures are exported as derived public text;
their original raw hashes stay explicit. Large `.f32`/`.bin` captures remain in
the complete private work archive with a full relative-path/size/SHA256 index.
[READBACK_LOCAL.json](READBACK_LOCAL.json) verifies all1,393 derived public text
records and all22,586 indexed private captures (269,612,051,436 bytes) by rereading
their bytes. [PRIVACY_SCAN.json](PRIVACY_SCAN.json) scans the complete2,510,564,322
expanded public-text bytes for the known private address/device/home/host/credential
literals. No match remains. [PUBLIC_READBACK.json](PUBLIC_READBACK.json) verifies
public HTTPS readback of the first/middle/last bundle parts plus `RESULTS.json`
and `BUNDLE_PARTS.json` from archive commit
`b68184f8f0ae70f4edee79225ef0b75540efe8a1`; all91 archive Git objects matched
their local content-addressed Git IDs during upload. [VALIDATION.json](VALIDATION.json)
binds the final checks and report artifacts.
This is not a claim that the raw binary capture archive has been published or
independently reproduced by a third party.

The35,843,710-byte compressed text bundle is stored as69 ordinary Git parts to
keep each object small. [BUNDLE_PARTS.json](BUNDLE_PARTS.json) lists every size and
SHA256 plus the assembled SHA256. From this directory, reconstruct and verify it:

```sh
cat scientific-records.json.gz.part????? > scientific-records.json.gz
python ../readback_export.py --export . --materialize /tmp/heterospec-linux-text
```

Use a fresh materialization directory. The expanded text is about2.51GB; allow
sufficient RAM and disk for JSON verification/extraction. The text index preserves
both original raw hashes and transformed public-text hashes. Paths and UUIDs in
public records are placeholders; the original hash fields continue to bind the
private original bytes. Reproduction creates fresh local jobs/freezes at the new
host's actual paths rather than treating transformed text as byte-identical jobs.

No compute is rented, no driver/device is changed, existing services remain
outside the experiment, and neither this results PR nor the manuscript is merged
or updated automatically. C4096 expansion is a separate study.
