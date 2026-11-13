# Qwen3-32B mixed-Q4 descriptive deployment results

The complete six-arm panel finished at2026-11-09T19:56:42Z (03:56 BJT).
All24 workers,96 measured requests and96 identical-root complete warmups passed
the endpoint, physical execution and strong-control checks. Anonymous byte readback of all170 source/result files at immutable commit
6b58f0573b88239f90f7f170088afe90830c1e25 PASSED. Independent replay using
only those downloaded public bytes also PASSED all96 measured and96 warmup
records, physical counts, totals, contrasts and cumulative accounting. See
PUBLIC_ANONYMOUS_READBACK.json, PUBLIC_STATISTICAL_REPLAY.json and FINAL_STATUS.json.
Public replay is not a new GPU numerical qualification.

Each arm below contains the same16 measured resident requests (four exposed
roots x four rounds, cap128). Complete caller and native-worker columns include
ALL16 warmups for that arm as well as process/model startup, native hashing,
setup, output serialization and exit; caller additionally includes host model
and dependency hashing. These scopes must not be substituted for one another.

| Arm | Measured resident service(s) | Complete caller(s) | Native workers(s) |
|---|---:|---:|---:|
| W_REF1L_M | 124.182883 | 425.996587 | 343.309616 |
| W_REF1G_M | 117.208239 | 409.575583 | 329.629639 |
| L_REF1L_M | 124.100017 | 428.398781 | 344.138895 |
| L_REF1G_M | 117.143582 | 412.088329 | 328.455147 |
| W_REF1L_D4 | 147.748374 | 478.531900 | 396.384739 |
| L_REF1G_D4 | 133.543739 | 455.562432 | 365.014370 |

L_REF1G_D4 takes9.614% less aggregate service time than W_REF1L_D4; the
16 paired root/round ratios have geometric mean0.904576. This comparison
changes BOTH lowering and projection, so the gain cannot be attributed solely
to LOCAL. Relative to the fastest target-only arm L_REF1G_M, L_REF1G_D4 takes
14.000% MORE aggregate service time (paired geometric mean1.145712). Relative
to all four M arms, the D4 candidate takes7.54--14.00% more time. Correctness
and migration succeeded; a general32B speculative performance win did not.

The complete caller ratio L_REF1G_D4/W_REF1L_D4 is0.952000, and
L_REF1G_D4/L_REF1G_M is1.105497. These include all warmups/startup;
they are distinct from resident request time and do not represent GPU kernel time.

The target is the exact19,762,149,024-byte mixed Q4_K_M32B GGUF, with the
fixed0.6B Q8_0 draft, one RTX A500024GB, C1024, F16 KV, no flash attention,
candidate output reserve32 and UB32. All six candidates use the SAME explicit
CUDA-graphs-disabled policy and numerical frontend. Transformer/output layers
are GPU offloaded; the standard CPU-mapped input embedding remains allowed.
Minimum sampled free GPU memory in the formal panel was4452MiB.

The separate REF1-loop/group Q4_K/Q6_K recipes preserve the original scalar
MMVQ dot topology. Grouping uses independent one-column channels; it is not
a relabelled legacy Q8 four-column reduction. Actual target D4 verification
width is4, while PREFILL can be32. A reserve of32 is not a verification width.
Actual typed full-model operand/output comparisons, all60 geometry cases,
real/live and controlled transaction paths, native negative probes, full
C1024 capacity, pending and12 EOG/cap arm-boundary checks passed before timing.
The independent scalar R was repeated and frozen before candidates. Numerical
qualification compares entire requested151936-element vectors and parsed
64-layer active KV/frontier; it is finite. Formal clean requests check complete
output endpoints and physical/lifecycle contracts, and do not repeat heavy
internal-state exports within service.

All514 cumulative32B logical requests and652026 conservative reserved rows
remain charged, including the two inherited diagnostics, all references,
expected negative probes and earlier failures. The640/2000000 registration
was prospective; no reset/refund or borrowing from the old8B envelope occurred.
Projection-only rows are separately labelled in their records. Resident service
comparisons omit the earlier failed qualification/build work; full research
costs and failure records are retained in archive/COSTS.json and audit/FULL_COSTS.json.

Earlier loop qualification timeouts were caused by the recording path, not
evidence that a valid loop control was impossible. The common recording
successor preserves every descriptor and numerical byte while caching immutable
device type once per request and retaining fresh buffer-placement checks on
every callback. This fixes heavy qualification recording; it is not an8B C
hotspot finding or a clean-service D/E optimization result. The pre-timing
output-mask/offline-observer/native-hash adapters, original graph-enabled
attempts, all source epochs and failures remain preserved. The exporter stale
stage-name KeyError and old prospective runtime refusal are retained too.

Four exposed roots and four repeated rounds support descriptive deployment
comparisons only. Root positions/adjacencies use four-row Williams; six-arm
orders balance pairwise precedence and mean position but are not full six-row
Williams. Do not treat repeated roots as independent task samples or infer
population confidence, new blind accuracy, a size-only effect, universal Q4
performance, or that q8 is intrinsically slow. Model size, quantization, recipe
and graph policy differ from previous8B experiments. No old benchmark result
is rewritten. No D/E,576 confirmation, merge, Release or manuscript edit is
automatically launched.

Use REBUILD.md, PLAN.md, exact source epochs, replay_public.py and the
results_20261109 packet. Original full vectors/KV and captured model operands
stay private with complete commitments. Public byte replay is not an independent
GPU numerical rerun. The optional matched-history B supplement is a separate
8B physical-width study and cannot replace this32B panel.

Final cost/closure: known cumulative native worker wall is16756.608s, including
native SHA/load, heavy qualification and failed attempts; it is not GPU kernel
time. Formal native workers total2106.932s; complete formal caller time totals
2610.153612s including ALL warmups and startup. Nine FAILED ledger events
include five expected negative probes; no formal worker failed. Additional
data-only adapter failures are retained separately and start no native work.
Raw private captures total159615548758 bytes in8728 files. The8.850224MB XZ
text stream expands to1221898994 public text bytes across14866 records; JSON
indices and costs add packet size. Model weights remain separate and private.

The optional controlled B supplement was NOT run. Complete32B public delivery
was not ready before its registered04:19:17 BJT whole-panel admission line
(observed25m43s whole estimate plus900s closure margin before05:00). Preserve
the prepared matched-history/Williams design, old32 qualification reuse proof
and SKIPPED_BEFORE_GPU/EXECUTION_STATUS evidence. Old8B accounting stays
1909/2048 requests and3053954/8000000 rows. No new B timing conclusion or
claim about physical q8 performance is made. The original confounded B timing
remains uncorrected by new timing data. No pending native experiment remains.
