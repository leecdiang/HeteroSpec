# Stage C: first-use cost occurs in both widths; no optimization admitted

Native work and automatic local archive completed on2026-11-09 at20:40:18
Asia/Shanghai. All16 charged profile operations completed across8 fresh native
processes. Every cell restores the identical B-bound scalar KV/frontier before
each of two same-path operations. Both operations are reported and charged.
There are no extra/free primers, draft calls, new reference forwards, numerical
code changes or repeated slots. This is host-phase profiling, not CUDA-kernel
profiling, new live speculative service, population inference or a blind sample.

| Projection | Position | Operation | First use ms | Follow-up ms |
|---|---:|---|---:|---:|
| loop4 | 248 | q4pair | 65.334 | 32.349 |
| loop4 | 248 | q8 | 61.158 | 35.598 |
| loop4 | 252 | q4pair | 64.417 | 37.561 |
| loop4 | 252 | q8 | 63.593 | 38.050 |
| packed | 248 | q4pair | 65.171 | 32.242 |
| packed | 248 | q8 | 60.576 | 34.553 |
| packed | 252 | q4pair | 63.506 | 37.725 |
| packed | 252 | q8 | 68.051 | 38.455 |

First use is25.543–32.984ms slower than follow-up in these8 cells. Most of the
difference is inside the host VERIFY boundary; output-copy differences are
1.605–1.900ms and planning differences are below2 microseconds. These categories
are nested, not additive independent service costs. The experiment does not
identify a unique internal lazy initialization, allocator, clock or kernel cause.

Both widths have this first-use/call-history effect. B's second round put a
fresh-process q8 ahead of q4pair; it must not be interpreted as a width-only
penalty. At matching follow-up ordinal, q8/q4pair is1.1004/1.0130 for loop4
within/crossing and1.0717/1.0193 for packed. These are one observation per cell,
across independent processes, not a demonstrated steady-state distribution.
Do not replace B's registered data, pool these profiles with B's measurements,
or turn this into a live k7-versus-k3 effect.

Graph counts reinforce the need for limited attribution: within-extent follow-up
requests reuse their graph, but crossing q4pair records2 builds/0 reuse on BOTH
first and follow-up while still showing a25–27ms difference. Counts alone do
not time graph construction or count CUDA kernel launches. No profiled removable
hotspot with a demonstrated material complete-service contribution is established.

## Eligibility and cost

The exact B loop4/packed executables, numerical archives, actual loaded modules,
Qwen3-8B Q8_0 model, C1024/F16/noFA/UB32/reserve8/LOCAL configuration, original
first root and scalar oracle payloads are reused. B's32 all-vector and initial/
final-active-KV proofs are hash-bound. Every C operation independently checks all8
full-vector hashes, row masks, bounds and physical counters against those fixed
operands. q4pair has two physical4 calls; q8 has one physical8 call. New clean
profiles export no full KV and do not add live EOG/pending/rollback qualification.
No tolerance, precision, output-policy or numerical source change is made.

The16 requests reserve4128 conservative rows and execute128 target rows, zero
draft rows and zero new reference requests. All8 workers complete with no failed
native event. Adapter-inclusive wall totals480.179s; native-process wall389.479s
and host-wrapper wall398.553s overlap with it. Complete startup/model/hash/restore
and request logs are retained. The2s sampled selected-device total-minus-free
maximum is8510MiB, a lower bound rather than an exact per-process high-water mark.
Observer samples cannot exclude all short events or shared interconnect effects.

The cumulative original budget is now1909/2048 requests and3053954/8000000
reserved rows;139 requests and4946046 rows remain. This is not a new envelope or
permission to transfer unused stage quota. B and its public delivery stay intact.

## Decision and32B assessment

Stop after C. No common numerical optimization is implemented, so D and E are
NOT RUN. Original finite k3 advice is retained; no claim that future optimization
is impossible. The original live panel already has primers, and this diagnostic
does not measure how much internal first-use expense remains in that service.
Moving setup across a timer would not demonstrate an end-to-end optimization.

The optional32B file receives ONLY a CPU header/type inventory after C. The
19762149024-byte Qwen3-32B Q4_K_M GGUF has707 tensors:385 Q4_K,65 Q6_K and257
F32, across64 layers. No tensor payload is read by the inventory; it binds the
prior full-SHA acquisition receipt and does not rehash the complete file. The
previous allocation/short-forward smoke remains its prior limited evidence.
This mixed-type/size extension needs an exact independent32B scalar R and its
own full-vector/state/lifecycle qualification; B/C's8B Q8_0 evidence cannot
admit it. PR210 reserves zero32B GPU requests. No guard widening, implicit recipe
substitution, new32B forward, numerical or performance panel is launched.

## Reproduction and archive

TEXT_RECORDS.jsonl.gz contains147 sanitized text records,148242 compressed
bytes, SHA`03b9d6dfb7059c3bb26e6c7ebd9a0f5d4bb02750590e114d1bf13a607a50d198`.
TEXT_INDEX.json binds original and exported text. Native receipts, full launch /
request strings, modules, resources, inherited ledger commitments and actual
source are retained. Allocation UUID, credentials and unrelated foreign-job
identifiers are excluded. B's raw numerical payloads remain private and bound;
there are no new C heavy captures to independently requalify from this archive.

```sh
node benchmarks/server_expansion_v1/M2_followup_20261109/stage_c/replay.cjs \
  benchmarks/server_expansion_v1/M2_followup_20261109/results_stage_c_20261109 \
  /path/to/FRESH-replay
```

The helper verifies all147 records, original receipt/table identity, job/build/
module commitments,16 operations/128 rows, exact summary arithmetic and budget.
It runs no model. Native reconstruction inherits the exact B source/build/oracle
contract. stage_c/run.py preparation fixes the8 jobs, original cumulative
ledgers and source freeze; public admission/readback precedes execution. A new
host needs its own approved allocation, independent Linux R and budget; do not
invent old private snapshots or reset counters to rerun this stage on the
retained host. Public byte/statistic replay is distinct from numerical eligibility.

See DIAGNOSIS.json, DECISION.json and Q32_TYPE_INVENTORY.json. Public readback is
committed separately after upload. No D/E/32B auto-expansion, paper edit, merge,
Release or data deletion.
