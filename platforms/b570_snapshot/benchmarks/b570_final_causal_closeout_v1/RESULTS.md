# B570 final causal closeout

PR #100 design head a1925c4a3b040f9ad3db7ec4301042791a82fe75; inherited audited PR #99 head c0e16aff9f3eeb0e677a52fcdc092068c096bf5d. Intel Arc B570, original Meta-Llama-3.1-8B-Instruct Q6_K target, unchanged numeric DLLs and frozen finite exposed inputs.

133/133 whole native requests and 40/40 standalone operator requests completed; no retries, warmups or native failures. 32 operator calls passed full native same-arm shams; 8 MUL calls failed and are excluded from causal inference. Independent CPU rederivation passed, with 15 malformed-evidence rejection controls. All CAP/EOG endpoint IDs, flags, length, terminal ID and stop reason are retained; no cropped output comparison.

| Hypothesis | Audited result | Boundary |
|---|---|---|
| H1 partition recipe | Supported on these inputs: D=B=C complete output and initial FP32/KV bytes on all seven inputs | Geometry recipe, not a universal kernel-only explanation |
| H2 operator location | Native first divergence at layer-0 K/V (1248), Q/K/V (831); faithful fixed-input geometry replays reproduce those differences | Exact Vulkan pipeline/shader/dispatch identity UNKNOWN; MUL replay not admitted |
| H3 KV × initial logits | 16/16 own-path shams pass; 40/40 cross cells give AA=AB=A and BA=BB=B | Conditional complete necessary-state boundary resume; no general opaque context clone |
| H4 timeline | GPU_TIMELINE_NOT_AVAILABLE | Hardware timestamps supported, pinned backend does not expose qualified absolute queue/query intervals; no P3 GPU starts |

## Partition causality and negative controls

D uses UB128 and external 128+remainder; B uses UB512 with the same caller partition, C is historical native UB128. D=B=C includes the full 128256 FP32 vector and all 64 serialized K/V tensors, with fresh-worker repeats and observer-off/on endpoint agreement. Relative to A, first full-output differences are zero-based 47 (1248), 81 (831), and 57 (fixed prefix129). Stable long prompts 1011/1249 have different numeric states but identical complete outputs. Prefix127/128 is bitwise invariant.

The frozen 19-schedule exposed sweep has observer-off/on full endpoint agreement for every schedule. It does not imply that every partition exceeding128 triggers divergence. The 831 132+1 schedule produces a third endpoint (first difference40 from every reference).

| Task | Caller schedule | Complete reference outputs matched | First difference from A |
|---|---|---|---|
| GSM8K/test/1248 | 64+64+33 | A | none |
| GSM8K/test/1248 | 96+65 | A | none |
| GSM8K/test/1248 | 128+33 | B, C | 47 |
| GSM8K/test/1248 | 160+1 | A | none |
| GSM8K/test/831 | 64+64+5 | A | none |
| GSM8K/test/831 | 96+37 | A | none |
| GSM8K/test/831 | 128+5 | B, C | 81 |
| GSM8K/test/831 | 132+1 | none | 40 |
| GSM8K/test/1011 | 64+64+62 | A, B, C | none |
| GSM8K/test/1011 | 96+94 | A, B, C | none |
| GSM8K/test/1011 | 128+62 | A, B, C | none |
| GSM8K/test/1011 | 160+30 | A, B, C | none |
| GSM8K/test/1249 | 64+64+35 | A, B, C | none |
| GSM8K/test/1249 | 96+67 | A, B, C | none |
| GSM8K/test/1249 | 128+35 | A, B, C | none |
| GSM8K/test/1249 | 160+3 | A, B, C | none |
| FIXED_PREFIX_1248/129 | 64+65 | A | none |
| FIXED_PREFIX_1248/129 | 96+33 | A | none |
| FIXED_PREFIX_1248/129 | 128+1 | B, C | 57 |

## Operator numerical evidence and failed shams

Aligned embedding GET_ROWS, pre-attention RMS producer and projection activation operands agree bitwise A/B; all B/C named tensors agree bitwise. Layer0 projection frontier already diverges before attention: 1248 K maxabs0.052734375 and V0.0023193359375; 831 Q0.020766258239746094 (only logical positions128–132), K0.0703125 and V0.0021639540791511536. RMS and 1248Q fixed-input controls remain bitwise invariant. Topological first is Vcur for1248 and Qcur for831; frozen family order selecting K first does not establish K as the unique cause.

All 8 MUL replay calls are preserved as FAILED_NATIVE_SAME_ARM_SHAM_POST_CONSUMER_OPERAND_ALIAS. Callback captures were after the in-place consumer, so the replay operand was not the pristine pre-consumer activation. No retry or repair of native conditions was performed. Independent audit first rejected a producer/operand alias assumption, retained the rejected audit source and logs, then used captured producer identity and qualified projection inputs to rederive only admissible conclusions.

Before relevant runs, authenticated amendments bound logical micrograph positions to actual inp_tokens/inp_pos (the stale observer metadata is retained), and selected RMS by the actual attn_norm operand producer identity rather than a duplicate norm label. Frozen original scripts and amendment receipts remain in the archive.

## Necessary-state restoration and causal crosses

The prospectively defined boundary0 resume restores every sequence K/V layer and exact positions, consumes the complete FP32 initial logits through the identical native greedy sampler, reconstructs an empty committed prefix, preserves pending-token semantics and recreates single-token continuation under one clean common receiver. All16 own-path shams reproduce the entire natural endpoint and pinned continuation states before P2 admission. No partial KV-only opaque restore is represented as complete state.

For affected1248/831 and stable1011/1249, all40 four-cell repeats give AA=AB=naturalA and BA=BB=naturalB. KV source controls the affected suffix at47/81; stable tasks retain the same output despite different KV bytes. All initial vectors select top1 token1271; swapping initial logits is therefore a negative control within this receiver contract, not proof that future logits are irrelevant. General opaque full-context cloning remains unimplemented.

## Budgets, inherited costs and limits

Owned GPU process lifetime1656.326s, minimum signed same-PID memory headroom2193162240 bytes, operator payload330472800 bytes; no new paid request-cost benchmark. Physical work counts, observed state causality and actual paid request cost are separate artifacts. Original R_stock qualification failure and all qualified request ratios remain NULL. Historical diagnostic paid ratios R_prod/C_k1=0.7192637597463166 and M_match/C_k1=0.7279267978304574 imply losses of about39.03% and37.38% in C_k1 request cost relative to those baselines; these are inherited diagnostic cost observations, not qualified stock-compatible speedups. Full historical PR97 capsule (8358 logical files, including complete PR92/93 evidence) and full remotely restored PR99 evidence are included unchanged.

Initial F0 pinned complete model/numeric DLL/executable hashes and live driver version/capabilities. Full external driver body hashes were authenticated later before P1C/P0, not before P1A/B; this preregistration incompleteness is explicitly retained. Continuous physical residency, exact shader identity, exclusive or overlapping GPU phase time, blind transfer and universal causal necessity remain unproved. Hardware timestamp support alone does not establish timeline availability.

Local and authenticated remote restoration receipts are published after the sealed archive to avoid a circular archive hash. Completion requires their explicit PASS statuses; this report alone is not a remote restoration receipt. See JSON artifacts for full machine-readable decisions, original failures and byte-level evidence.
