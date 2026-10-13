# Frozen experiment skeleton and exact accounting

The Work owner must pin original PR #99 native IDs/hash for every input in F0-BASE before new requests. All are **exposed mechanism diagnostics**, not blind transfer evaluation.

## Historical A/B/C (NO new charges by default)
- A: UB512 + one Prefill caller. B: UB512 + external 128/remainder caller split. C: UB128 + one caller internally split at 128.
- Two affected: GSM8K/test/1248 (N161, first output divergence47), GSM8K/test/831 (N133, first divergence81).
- Two stable long: GSM8K/test/1011 (N190), GSM8K/test/1249 (N163).
- Synthetic native-ID fixed prefixes of GSM/1248: N127, N128, N129 (N129 first divergence57).
- #99 B=C all complete trajectories and prefill serialized KV/full FP32 logits. A != B only for affected tasks and N129 synthetic prefix.

## P1-A: fourth arm (7×3=21)
D = UB128, capacity1, explicit external Prefill split128/remainder (N≤128 → single caller), natural final-only logits, all else same. All seven historical inputs, 3 fresh-process repeats including 1 capture-off+2 capture-on. Against immutable PR99 A/B/C, not replacing old records.

## P1-B: non-adaptive caller partition grid (38 new)
A selected external split is a vector of *caller token lengths*, not a change in GPU numeric DLLs.
- 1248 N161: [64,64,33], [96,65], [128,33], [160,1].
- 831 N133: [64,64,5], [96,37], [128,5], [132,1].
- 1011 N190: [64,64,62], [96,94], [128,62], [160,30].
- 1249 N163: [64,64,35], [96,67], [128,35], [160,3].
- Fixed prefix1248 N129: [64,65], [96,33], [128,1].
Context UB512/capacity1; two fresh-process repeats (capture-off, capture-on). 4×4×2 +3×2=38. [128,remainder] is already exposed in #99: call it a replication only.

## P1-C: source op mechanism
At most **2 affected inputs ×3 original arms A/B/C ×3 added diagnostic repeats=18** whole requests. Traverse actual native op order (source-identified layer0 input/norm/proj/QK/softmax/AV/residual/FFN), align logical rows and pointer/strides, then advance only under frozen traversal policy; max72 additional standalone fixed-operand GPU operator starts; max512MiB additional P1-C payload with synchronous hard cap. Captures on/off must preserve complete native output.

## P0 state import qualification
4 inputs (both affected + both stable long) ×2 donors A/B ×2 fresh-worker own-path shams = **16**. Required complete restore scope includes actual KV tensor content+positions, full logits/output buffer, native greedy sampler/pending/committed prefix and relevant context/scheduler/queue ownership. No partial KV-only import promoted to complete restore. If unavailable, mark `FULL_STATE_RESTORE_NOT_ADMITTED`; P2=0 starts, but P1 continues.

## P2 conditional donor cross
2 affected ×4 cells (AA,AB,BA,BB) ×3 fresh repeats=24.
2 stable long ×4 cells ×2 fresh repeats=16.
Total40. All full native IDs/EOG/terminal+stop. A/B initial top1 historically both 1271 on affected tasks: a logits swap is a **first-greedy-decision negative control**, not evidence of deeper logits causality. If failed state own-path sham for any donor, zero causal cross claim.

## P3 optional GPU timeline
3 old exposed tasks (1248,831,1011) ×3 existing recipes (R_prod, M_match, C_k1) ×2 repeated real GPU-timestamp sessions=**18**. Only if completed GPU timestamp/query/fence capability/overlap audit passes and safety controls are in place. Not comparable to #92 paid ratios; if unavailable report null and stop. No ETW/API-log flooding.

## Budget ledger — immutable maxima
| Stage | New native whole requests |
|---|---:|
| P1-A |21|
| P1-B |38|
| P1-C |≤18|
| P0 restore shams |≤16|
| P2 donor crosses |≤40|
| P3 optional GPU timeline |≤18|
| **Total registered maximum** |**151**|
| Engineering/failure/start reserve |≤49|
| **ALL new native whole request starts** |**≤200**|
| Zero-forward load probes |≤8, counted separately|
| Standalone GPU operator replay starts |≤72, counted separately|
| Owned B570 GPU-process time |≤6 hours|

The exact sequence and conditional admissions must be versioned/authenticated before corresponding first new forwards. No after-result selection, no retry, and no pooling unlike paid/observer timers. A blocked P2 or P3 is a closed gate, not failed scientific work.
