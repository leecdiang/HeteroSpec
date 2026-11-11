# A5000/Linux M1: cut scope versus projection packing

All 16 prospective workers completed: **256 measurements + 32 primers**. Four
real D4 paths share Qwen3-8B/0.6B Q8_0, C1024, F16 KV, greedy decoding, no FA,
k3, draft prefill UB4, target UB32 and output reserve4. The 16 exposed PR195
roots are deployment-transfer attribution inputs, **not new blind samples**.
M2 was not run.

Packing supplies the main resident-service benefit in this configuration.
LOCAL's cut-only increment is substantially smaller than the earlier combined
comparison. These results sharpen attribution rather than assigning that entire
difference to LOCAL.

## Complete service and every registered contrast

Each total covers 64 measured requests; primers have separate records.

| Arm | Cut | Projection | Resident service total, s |
|---|---|---|---:|
|W_L4_D4|whole/rechunk|loop4|142.271207231|
|W_P_D4|whole/rechunk|packed|139.944720542|
|L_L4_D4|LOCAL|loop4|141.974241640|
|L_P_D4|LOCAL|packed|139.765106784|

The predeclared analysis sums sessions within each root and resamples the 16
paired roots 10,000 times, seed19720261107. Four direct contrasts plus the root
interaction form one five-member Bonferroni family. The table gives the
corresponding 99% per-estimand bootstrap intervals, conditional on this exposed
cohort and these four observed sessions. They do not quantify all host drift or
justify population-wide performance claims.

| Numerator / denominator | Total-time ratio | Adjusted interval | Point service reduction |
|---|---:|---:|---:|
|L_L4_D4 / W_L4_D4|0.997912680|[0.995369746, 0.999575753]|0.209%|
|L_P_D4 / W_P_D4|0.998716538|[0.995952615, 1.000569735]|0.128%|
|W_P_D4 / W_L4_D4|0.983647523|[0.980235857, 0.988654413]|1.635%|
|L_P_D4 / L_L4_D4|0.984439890|[0.981228283, 0.989390965]|1.556%|

LOCAL has a small positive conditional estimate under loop4. Under packed its
interval includes no benefit. The registered interaction,
`geomean((L_P/W_P)/(L_L4/W_L4))` across roots, is **1.000696007**,
interval [1.000069260, 1.001392812]. This tiny estimate points toward attenuation,
not beneficial synergy; its estimand differs from a ratio of pooled totals.

Descriptively, L_P_D4 takes **1.7615%** less service time than W_L4_D4. This
combined comparison is not an additional registered inferential contrast.
Historical timings are not pooled. Earlier target-only M comparisons remain in
[PR203](https://github.com/leecdiang/HeteroSpec/pull/203); this D4-only panel is not
a new speculation-versus-M experiment.

## What actually ran

Within each of the 64 root/session blocks, all four arms have identical output
IDs, EOG flags and complete saved proposal/acceptance transactions. Each arm
executes 25,232 target rows, 25,232 draft rows, 2,224 verification cycles, 5,476
accepted proposals and 552 rejection cycles. Each has 48 CAP and 16 EOG measured
endpoints. Clean service exports/imports/heavy captures/context creation are all
zero, and actual graph reuse is observed.

SIMPLE executes 2,244 physical verification calls: width4 x2204, width2 x16,
width1 x12 and width3 x12. LOCAL executes 2,224 calls, all width4. Thus only 20 of
2,224 logical cycles require SIMPLE rechunking here. Prefill width histograms
are identical across arms. This limited boundary frequency helps explain the
small cut-only opportunity at k3.

A separate heavy observer, linked to exactly the same numerical archives,
records actual GPU MUL_MAT graph descriptors. Each loop4 diagnostic observes
108 marked loop4 nodes; each packed diagnostic observes 747 packed nodes with
independent four-column groups. Wide packing occurs in prefill and is absent
from q4 verification. The diagnostic uses generation cap8 with k3/reserve4/q4,
not M2 or q8 verification. Its complete vectors/states match frozen R, and its
clean counterpart is bridged to the actual formal executable. These are
scheduled graph/device-buffer observations, not CUDA kernel-symbol profiling.

Descriptive target-prefill totals are 63.2263/60.9222/63.2269/60.9910s for
W_L4/W_P/L_L4/L_P, consistent with packing's prefill opportunity. Partial phase
clocks do not replace complete service; q4 timing variation is not attributed
to wide packing.

## Prospective order, source and independent R

The qualified Linux dependency is commit
`592abdfe9267fd97ecbde18cd0ee9a1bfc319e20`, with unchanged R freeze SHA256
`fa8ceec6d54f98730d63880436a6bf088c119232c0f091406725e724a4665731`.
`RUNTIME_PIN.json` fixes its supervisor/readers and published reference indices.
Measurement/checker integration was committed at
`35cdf20d56e29edc196188441626400df176639d` before formal timing.

M1 verifies and reuses read-only numerical archives from the predecessor's
complete CUDA source builds, compiling/relinking new observer frontends.
No fresh M1 CUDA recompilation or arithmetic implementation is claimed.
The completed predecessor's sources, binaries, inputs, R, panel and ledger remain
unchanged.

The prospective plan was publicly committed before formal outputs. With
A=W_L4_D4, B=W_P_D4, C=L_L4_D4, D=L_P_D4:

```text
A B D C
B C A D
C D B A
D A C B
```

Each arm occupies each position once; every directed adjacent pair occurs once
within sessions. The three between-session edges are outside this balance claim.
Root order is prospectively shuffled per session and shared across arms.

The versioned native gate reports actual model hashes/structures, context and
output parameters, target/draft placement, k, draft width and cut/projection
bindings. Unknown fields and mismatched output capacity are separately observed
native failures before input execution; both remain charged.

## Finite qualification and retained failure

Eight new natural reports cover four D4 paths x Qwen/Smol: 5,064 original
requested full target vectors, 1,288 committed target states, 32 terminal states
and 8 cap1 states. Full committed/terminal frontiers also match. Every serialized
active target state pair is raw-byte equal, with all reviewed F16 KV payloads
and metadata checked, without tolerance. Real Smol EOG, first/later rejection,
rollback, pending/correction/bonus, cap1/cap128, tails/reset and heavy/clean
correspondence are covered. The predecessor's geometry evidence is reused because
the numerical archives are unchanged.

Supplemental projection bridges add 36 requested full vectors and 16 serialized
states (12 committed +4 terminal). These are finite checks, not a universal proof.
Formal requests check independent endpoints, transactions/physical work,
capabilities, modules and clean service; **they do not repeat every internal
state/vector comparison**.

A Python projection-checker version shadowed a callable with a graph-node list,
stopping after the second arm's native jobs had completed. Failed source commit
`f05ca4a2ab9f203e348139a8972bfc1c9cc2dce9`, the failed pipeline status and logs
are retained. The repaired verifier checked original COMPLETE jobs/builds/modules,
preserved the first successful proof, checked the second arm's existing bytes,
and ran only the remaining unstarted diagnostics. No native request, numerical
binary, reference or formal slot was replayed/replaced. Helper tests passed
48 normal and48 optimized; native qualification is independently evidenced.

## Complete windows and resource accounting

These are sums of four actual workers per arm. Inclusive windows overlap and
must not be added. Startup includes native model-hash capability verification;
the outer adapter clock also includes supervisor preflight.

| Arm | Test burst, s | Worker wall, s | Entire adapter invocation, s |
|---|---:|---:|---:|
|W_L4_D4|142.356739|367.460103|420.561674|
|W_P_D4|140.029693|368.214262|420.122304|
|L_L4_D4|142.058927|368.075289|421.038826|
|L_P_D4|139.849084|367.734723|419.386912|

Worker totals are nearly equal; a corresponding cold-start advantage is not
established. Sum-to-first-complete-result clocks are 217.524–220.600s per arm
across four workers, not TTFT. Primers, phase coverage and unmeasured components
remain explicit. No setup/N amortization, sum of overlapping clocks or invented
total engineering cost is reported.

One explicitly allocated RTX A5000 is used, with2 runtime threads and a2-job
build limit. Other company services remain running. Maximum sampled selected
total-minus-free is 9,266MiB. This includes reserved/unavailable device memory,
not just NVML memory.used. The 2s samples bound the peak of that unavailable-memory
quantity, not a per-process high-water measure. The archived original labels and
values are retained; see MEMORY_SCOPE_NOTE.json. M1 charges 382 logical requests, 889,908 reserved rows and
34 native workers, including two expected native admission failures. Historical
plus M1 counters are 1,239 requests and2,442,247 rows. Counters were not reset and
no costs refunded.

## Material and reconstruction

`RESULTS.json`, `REQUESTS.csv`, control trajectories, clocks, costs and physical
censuses accompany 2,125 complete derived text records:451,870,712 uncompressed
bytes, 8,894,728 compressed bytes in17 parts. All public parts and binding JSONs
are read back anonymously over HTTPS. The text index distinguishes original
private raw hashes from derived public hashes. Privacy scanning covers the entire
decompressed public bundle.

All11,596 new binary captures,61,111,589,136 bytes, are indexed and fully read
back locally. They remain private on the experimental host. This is not a public
full-binary archive or third-party replication claim. Credentials, company
UUIDs/host/account identifiers, unrestricted inventory and unrelated process
records are excluded.

See [M1_REBUILD.md](../M1_REBUILD.md) and the pinned predecessor for source/model
acquisition and full numerical rebuild. Assemble the archive here, then use the
predecessor's readback tool:

```sh
cat scientific-records.json.gz.part* > scientific-records.json.gz
sha256sum scientific-records.json.gz
# Expected:141a1dcd53f738cb1a11e0c13c960b61318a93c96783a9129495746ba9d77c8f
python /path/to/pinned/linux_transfer_v1/readback_export.py --export .
```

M2, additional model panels, rentals, manuscript edits and automatic merges are
not part of this result.
