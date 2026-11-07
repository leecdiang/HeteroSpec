# Logical inputs, measurement and compact receipts

## Logical data recipe

`study.py` emits geometry and seeds, not tensor files. The RTX adapter must create
and hash actual Q/K/V/mask bytes, construct legal GGML strides and bind references.
All heads/channels/keys are retained. The input generator must use a counter-based
logical-index recipe so a factor change does not accidentally randomize every
overlapping operand. A vectorized implementation is permitted; compare a small
sample of every operand/realization against an independent scalar implementation.

Use the following exact `coordinate_hash_v1` recipe (unsigned64 arithmetic modulo
2^64 after each operation). `mix64(x)` is:

```python
x = (x + 0x9e3779b97f4a7c15) & 0xffffffffffffffff
x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & 0xffffffffffffffff
x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & 0xffffffffffffffff
return x ^ (x >> 31)
```

Counter Q(j,h,d)=((j*64+h)*256+d), K(g,k,d)=((g*8192+k)*256+d),
V(g,d,k)=((g*256+d)*8192+k). Role salts are respectively0x51,0x4b,0x56.
`bits=mix64(counter XOR seed XOR (role_salt << 56))`.
For Q/K use `(int(bits % 17)-8)/32`; for V use `(int(bits % 33)-16)/32`.
Realization0 uses that value; realization1 multiplies by
`2**(int((bits >> 12) % 9)-4)`. Use the exact plan seed for each realization.
Cast Q to little-endian F32, K/V to little-endian F16. These bounded dyadic values
are exactly representable; the second pattern adds dynamic-range/cancellation
stress without overflow. This is a limited synthetic distribution, not a claim
about all possible floating-point inputs. Seed and recipe are fixed before outputs.

Logical Q shape is (d,q,Hq,1). Permuted storage has byte strides
`[4,d*Hq*4,d*4,d*q*Hq*4]`; compact storage uses
`[4,d*4,d*q*4,d*q*Hq*4]`. Populate by logical indices, not a reinterpretation of
unchanged physical bytes. K shape(d,keys,Hkv,1), strides
`[2,d*Hkv*2,d*2,d*keys*Hkv*2]`; V shape(keys,d,Hkv,1), strides
`[2,keys*2,keys*d*2,keys*d*Hkv*2]`. Verify spans/no overlap and actual backend support.

Mask shape(keys,q,1,1), F32, is0 for a visible key and -infinity otherwise:

- causal: query j sees k < keys-q+j+1;
- irregular: `(k+j)%3 != 0` (a synthetic nonempty mask, not a natural causal request);
- single_visible: only k=(keys-q+j)%keys.

GQA maps query head h to `h // (Hq/Hkv)`, with exact divisibility. Use F32-rounded
`1/sqrt(d)` scale and preserve the pinned backend's other declared op parameters,
precision and zero-bias assumption. Validate actual serialized parameters; do not
reuse a d128 scale for d64 unnoticed. Serial q1 captures preserve the full mask
column/position and original KV tensor; concatenate ordinary outputs by query.

No padded-length substitution: record actual extent and per-query visible-key
counts. Single-visible masks deliberately test a different workload and are reported
separately. CPU address/oracle tests do not replace actual CUDA placement/byte checks.

## Native timing adapter

Reusing PR120's graph builder, import binding and owned-input code is encouraged.
Create a new entrypoint with its own run ID/root. Do not import old run.py and invoke
an entry that resumes the sealed old UUID. Record the exact implementation delta.

H0 preserves PR120's checked timing/observer as a diagnostic condition. H1 allocates
input ownership, output arrays and fixed-size timing/receipt storage before the
measured loop. For every call:

1. Read QPC at a; compute graph; read b; perform required completion sync; read c.
2. Read ordinary output into that call's preallocated buffer; read d.
3. Outside [a,c], check completion/status and exact finite ordinary output, update
   in-memory receipts, and retain all raw ticks. If compute failed, do not attempt
   an unsafe readback merely to populate d; preserve the available prefix and stop.
4. After a bounded host/burst, flush raw output occurrences/receipt data to disk.
   Record failures and any unrecoverable in-memory tail as missing, never success.

The completed graph view is(c-a)/QPC_frequency. Its synchronization cost belongs
inside the view. The H1 completed-call view is(d-a), with no per-call JSON or output
buffer allocation between c and d. Status checks needed to safely perform readback
may remain in that interval and must be declared. Report all those boundaries;
do not call them isolated kernel times or subtract guessed observer overhead.
QPC calls, numerical checks and readback can still perturb subsequent work.

Allocate enough output buffers for at most64 full calls; count this memory and
initialization. Do not discard outputs after hashing if no exact bytes remain
recoverable. CAS may deduplicate equal outputs while keeping occurrence identities.
File-write relocation alone does not prove observer-free measurement. Keep before/
after input checks, actual CUDA buffers, numerical modules and final cleanup evidence.

References and qualification may use the same codebase with explicitly separate
capture semantics. A failed reference/qualification excludes its associated timing
arm; it cannot be fixed by a new comparison tolerance. H1 correctness qualification
is necessary even when graph arithmetic source is unchanged.

## Primary analyzer input

One JSON object per **timed host task**, in observations.jsonl. Only stages
aa_pilot/confirm/holdout are accepted. Keep reference/qualification evidence in their
own tables. Export timing records only after numerical/evidence checking. Do not
hand-edit scientific CSVs or use synthetic test receipts as actual data.

Required fields:

| Field | Meaning |
|---|---|
| task_id | Exact generated-plan task ID; unique |
| attempt_id | Actual host attempt ID; unique |
| plan_sha256 | Hash printed by study.py, binding this plan |
| observed_layout | Actual PQ/QB/QH_C, independently observed; both QB labels map to QB |
| method | H0/H1; H2 only after an explicitly amended lifecycle/plan |
| cost_view | `resident_graph`; analyze other cost views separately |
| status | QUALIFIED / NUMERICAL_FAILURE / ENVIRONMENT_INVALID / EXECUTION_FAILED |
| numerical_qualified | Boolean after exact output/input/placement/completion checks |
| environment_qualified | Independent predeclared timing-environment eligibility |
| session_id | Actual acquisition session, not an invented independent day |
| measured_us | Every measured completed-graph interval, excluding warmups; no trimming |
| host_binary_sha256 | Actual consumed executable identity |
| runtime_manifest_sha256 | Pinned numerical-runtime manifest, not changing telemetry |
| execution_policy_sha256 | Common frozen timing/lifecycle/sampling policy for this cohort |
| input_sha256 / reference_sha256 | Exact full-input manifest and canonical ordinary reference |
| evidence_receipt_sha256 | Actual numerical/evidence auditor's receipt |
| failure_reason | Required if a failed attempt legitimately lacks a hash/receipt |

All identity hashes are64 lowercase hexadecimal characters. Failed attempts may
have null final evidence hashes with a reason; do not synthesize an identity.
Input/reference identity must stay fixed for each case across methods and blocks.
Warmup raw ticks/outputs remain in the raw evidence even though excluded here.
The receipt checker does not prove that a reported hash refers to authentic bytes:
the separate collector/auditor must retain and verify those files.

Use status QUALIFIED with numerical_qualified=true, environment_qualified=false
for a numerically correct but timing-ineligible host, or ENVIRONMENT_INVALID with
the same flags. Every observation still appears in the coverage table. Malformed
qualified timing records are analysis errors; repair export from retained raw,
not by rerunning the GPU or discarding inconvenient calls.

The analyzer rejects duplicate task IDs, mixed source/runtime/methods within a
stage, wrong mapping/cost view, invalid clocks/counts and changing input identities.
References, bootstrapping and tests have separate meanings. Do not combine results
from different frozen plans into one file merely because the task labels resemble
each other. Analyze separately and document any later comparison.

## Deliverable results

Retain raw QPC ticks, frequency, warmups, all output/input bytes and occurrence map,
placement/module/graph metadata, commands/exits, environment, amendments and failure
records. Follow CONTRIBUTING: raw telemetry is local or in an already approved
artifact location, not committed to Git. Compact generated results and source may
be committed. Same-host restore is not external independent review.

Required compact results: numerical coverage; per-method A/A pilot; method decision;
per-case/per-geometry and full-panel paired contrasts; QB_A/QB_B sensitivity; factor
edges; all excluded/unstarted slots; power/order/session limitations; optional frozen
predictions and their errors; raw location/hash/restore status. `analyze.py` supplies
statistical JSON and planned timing coverage; the executor supplies numerical/raw
audits, readable tables and the explanatory RESULT.md. None of these counts itself
establishes a hardware benefit or natural decoder qualification.
