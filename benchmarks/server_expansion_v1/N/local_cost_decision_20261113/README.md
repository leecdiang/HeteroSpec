# LOCAL cost attribution and decision on the eight-request replay

Decision: **retain LOCAL as a qualified execution mechanism under stated conditions; do not promote it to the current natural multi-turn service-acceleration main line. Do not start the eight-request replay for this paper question.** This turn conditionally authorized 8 requests / 2,568 rows / 3 deployments if the experiment was worthwhile. The analysis below does not establish enough signal, attribution or service relevance to activate it. New consumption is **0 requests, 0 rows, 0 deployments and 0 GPU/model contexts**. This is a scientific No-Go, not a claim that permission is missing or that an append microbenchmark can never detect a difference.

Latest verified PR238 is `01d1c98001126ff15fae9fcb49185fe8be20ab76`; PR236 remains `6597489d01d0fa1fb17dce8bf6cade2c53e3a463`. No historical data, STATE, reference, baseline or paper changes. This successor adds a one-off CPU calculation, relevant source excerpts and the decision; no new controller, monitor or GPU entry.

## What the call difference actually removes

Both candidates preserve the same canonical input, token ordering, LCP/trim and state contract. Older canonical assistant KV reuse is common, not a LOCAL benefit. PR233 demonstrated supplied-token state/numerical equivalence with 251 physical calls /989 rows per candidate; it was qualification, not timing. PR236 demonstrated two bounded real-free trajectories, with C1 calls273→272 and rows809 unchanged. Its complete service panel did not show a gain. Do not combine timings across these experiments; their capture/output contracts differ.

| Component | What may be saved | What stays or increases | Evidence depth |
|---|---|---|---|
| In-process caller/CPU | one batch allocation/free, caller bookkeeping, decode entry and explicit synchronization invocation | all input rows still filled; planner/extent scan/owned-output vector setup happen once per logical append in both arms | fixed `PhaseContext` source; observed physical call counts |
| ggml graph scheduler | possibly one scheduling/input-binding round | fewer decode calls need not mean fewer graph builds; a reusable whole graph is already strong | current frozen graph-reuse source; old actual build/reuse counts not exported |
| Activation quantization | one fewer dispatch/pool-handle round per qualifying, fully consumed projection **if the same unfused path applies** | same activation rows/quantization data; tail width/fusion/dispatch can change | `mmvq.cu` quantizes once before its tile loop; actual helper launches/time unknown |
| Core projection/attention | C1 has a small projection grouping change | same token/KV rows and per-token padded attention work; proposed replay has identical ordered four-column and four-query tile positions | observed plans plus source-derived grouping, not CUDA launch counts |
| Local attention assembly | none established | extra concatenate nodes, larger rectangular masks, and strided mask views requiring `cont` copies | exact frozen graph builder; created nodes/data shapes, not optimized launch measurements |
| Output/LM head | no extra requested full vocabulary vector is removed | exactly one final output per append in both; zero flags on intermediate groups remain zero | explicit logits mask, batch output counting and Qwen last-layer output gather source |
| Sampling/history/client transport | no sampling or client request is removed | same 128 samples per turn, same parser/history/LCP/reset and one service request; the proposed replay omits generation and is not whole service | real receipts and actual runner |
| Experiment ledger | one durable per-decode debit transaction is removed | guard/read/check, JSON persistence, rename/fsync are experimental protection costs, not intrinsic GPU/model work | `charged_decode` → `LiveGate.rows/commit`; its duration was not isolated |

The runner's outer call is **not** an HTTP request, CUDA kernel, complete extra model evaluation, or an extra sampled token. The planner's full-vocabulary copy occurs only at requested rows. Batch code does not replace an explicitly all-zero logits mask with a requested output; the fallback “last token” applies when the pointer is absent. Qwen output gathering respects the output count. This prevents attributing a saved vocabulary projection/copy to every removed intermediate caller group.

Source-conditioned lower-bound/input checks are explicit in [REPORT](RESULTS/REPORT.json). Relevant original model/source identity is inherited from PR238/236; only five newly relevant full source files (423,940 bytes) were checked against their frozen source lock once. The original model was not rehashed or loaded. [Source and prior terminal state](SOURCES/SOURCE_AND_PRIOR_STATE.json).

## The proposed 4→3 case is not a pure dispatch deletion

The fixed canonical replay has head232/append89, W `[24,32,32,1]`, L `[32,32,25]`. For each fully consumed intermediate projection and attention layer, the source-derived ordered core tile positions are identical: 22 four-token tiles and one singleton. That does not guarantee identical real kernel counts, because helper operations, pruning and fusion can differ.

| Source-derived append property | W | L |
|---|---:|---:|
| Input rows / requested final outputs |89 /1|89 /1|
| Decode calls |4|3|
| Four-column / four-query tiles |23 /23|23 /23|
| Required width/extent/output-key transitions, assuming reuse enabled and other inputs reusable |3|3|
| Graph builds if reuse is disabled |4|3|
| Logical F32 mask tensor bytes |157,696|182,272|
| Attention concat nodes per layer build |19|20|
| Sum of concat output token-vector widths per layer |360|385|
| Necessarily strided mask `cont` nodes per layer build |0|6|
| Logical data packed by those mask `cont` nodes per layer |0|24,576 bytes|

W's consecutive32-row groups at256 and288 have the same512-entry extent vector and zero requested outputs. Source permits graph reuse. L's first32 group crosses the256 boundary; its next32 group has a different extent vector, so reuse is rejected even at the same width. Its final25-output shape changes again. These are mandatory-key transition predictions, not observed build counts: other inputs or a runtime reuse-disable setting can prevent reuse. **CUDA graph capture being disabled does not imply ggml graph reuse is disabled.** No old receipt records that runtime distinction well enough to promote the predicted count to measurement.

LOCAL's first mask spans512 columns even for its first24 rows that need only256. The graph builder slices those rows back to the correct extent, then creates six contiguous four-row mask copies because their row stride remains512. The per-layer concat output-volume increase is `25 × A × b` bytes for attention-vector width A and element size b, before considering optimizer/fusion behavior. Do not multiply these logical tensors into measured DRAM traffic or assume one node equals one CUDA launch. Even the proposed “equal tile count” case moves or adds work; it is not a clean one-variable removal of a graph build.

For actual C1, the analogous source-derived append counts are: projection133→132, attention133→134, concat115→117, rectangular mask882,688→901,120 bytes, and at least four new strided mask copies per layer build. Minimum required graph-key transitions are5 in both arms if reuse is otherwise allowed. The existing heavy selected-node callbacks, including the loop4-named subset, are not complete backend/kernel accounting.

## Same-panel timing evidence

Positive benefit means W−L, favoring LOCAL. These are all four frozen root/round pairs; no repeat is dropped.

| Case / round | Service benefit | Decode+sync+budget benefit | Non-sampling wall residual benefit* |
|---|---:|---:|---:|
| C0 /0 |−806.80ms|−107.01ms|−67.33ms|
| C0 /1 |−21.51ms|−5.91ms|−11.96ms|
| C1 /0 |−821.35ms|−77.99ms|−111.91ms|
| C1 /1 |+114.33ms|+89.72ms|+75.57ms|

\* Service contrast minus its own recorded, disjoint CPU sampling span. This is an accounting residual, **not measured GPU time or a prediction of an optimized service**. Decode+sync+budget already contains planning, some output handling and durable admission; it is not a standalone kernel timer. Prefix/suffix/generation decode and actual graph/quantizer/concat costs were not separately timed. Cold/qualification timings are not substituted.

C1's mean service is9.72214s W, with mean6.31988s in the aggregate decode span. Its mean decode contrast is only **+5.86ms**, changing sign between rounds; its non-sampling residual mean is **−18.17ms**, also changing sign. The same-partition C0 decode contrasts range from−107.01 to−5.91ms. C0 still includes planner and runtime effects; this is observed contrast scatter, not an independently calibrated noise distribution. It cannot be transferred directly to the proposed append-only experiment.

## Formula and sensitivity, not a fabricated cost stack

Let positive B be append-stage savings excluding the ledger:

`B = Δcaller × h + Δbuild × g + Σ(saved quantizer dispatch overheads) + Δcore_tile_cost − extra_mask/concat/pack_cost + R_shape/cache/fusion`.

For the proposed point, `Δcaller=1`, core ordered tile partitions match, and `Δbuild` can be0 with reuse or1 without it. Shape/fusion/cache residual and all latency coefficients are unknown. Adding the removed durable-debit time d gives the instrumented append contrast `B+d`; it does **not** turn d into a backend saving. Treat claimed savings in actual quantizer launches as conditional until primitive paths/counts are captured. No number from another experiment is inserted into this formula.

For context only, if every physical call carried one identical nonnegative fixed cost h and all other costs were nonnegative, C1's same-panel aggregate implies `h <= 6.31988s/273 =23.15ms`. Saving that one constant charge would be at most0.238% of its9.72214s episode. **This is a conditional uniform-cost model, not a hardware bound or a bound on shape-dependent effects, graph construction, or total LOCAL gain.** Wide calls and singleton generation calls need not share such a constant charge.

| Assumed net append saving | Fraction of current C1 episode |
|---|---:|
|0.1ms|0.00103%|
|1ms|0.01029%|
|5ms|0.05143%|
|20ms|0.20572%|
|100ms|1.02858%|

These are sensitivity inputs, not estimates. More generally service reduction is `f_append × r_append`, where the actual append share f and its net relative improvement r were not separately measured. A large append microbenchmark percentage may still have a tiny complete-service effect. The5% project objective is not a scientific pass threshold; no extra cases are sought to reach it.

## Can eight requests settle the relevant question?

The proposal spends2 requests on independent reference/repeat and2 on matched warm qualification, leaving **two measured W/L pairs**. Under a hypothetical known normal IID pair deviation σ, `SE(mean)=σ/√2` and an approximate80%-power two-sided5% planning threshold is `1.98σ`. A5ms signal would require σ around2.5ms or less. With variance estimated from only two pairs, an ordinary normal-model95% t interval has halfwidth `8.985s`, where s is the pair sample deviation; excluding zero for a5ms point effect would need s below0.56ms. The normal/IID assumptions themselves are unestablished. These are sensitivity formulas, not new confidence intervals or a requirement that descriptive pilots achieve significance.

Actual append-only latency and σ are **unknown**. The observed whole-episode aggregate scatter cannot fill that gap, and omitting sampling does not remove ledger, shape, mask-copy, concat and cache effects. An unusually large, stable append effect could be seen with two pairs; this analysis does not prove the experiment intrinsically powerless. However, there is no measured append bottleneck, calibrated signal/noise, or primitive-cost attribution supporting such an effect. The proposed replay can yield a descriptive fixed-input append number, but still cannot establish real-free session acceleration or a unique removed backend operation. A sufficiently quiet replay could distinguish a small effect; that condition is presently unverified.

Given3 placements, required strict qualification, up to2,568 rows, roughly662MB raw capture, implementation of a new fixed-prefix entry and the substantial chance of an inconclusive two-pair attribution, the marginal information does not justify activating the conditional allocation **for the present paper/service question**. Do not remove R/repeat/warm controls to buy more timing repeats; do not extend the budget or panel. Do not start GPU work merely to populate a table. Runtime/card/space admission was intentionally not attempted after this analytical No-Go, and no claim is made that an old free-card snapshot is current authorization or availability.

## Final recommendation and reproducibility

Keep the limited claim: LOCAL can preserve reference semantics while organizing projection work across local attention boundaries, and an actual one-call reduction exists. Shared canonical cache reuse, fewer token rows, universal assistant-KV preservation, fewer complete model evaluations, and complete-service acceleration are not unique benefits established here. Existing finite numerical/state qualification remains useful; it is not performance evidence. The current evidence supports a **bounded execution mechanism**, not a continuing natural multi-turn service-speedup main line.

A future change in that judgment needs a separately justified service workload with a material measured append share, same-panel split timing of debit versus native work, and actual build/reuse/primitive-path evidence sufficient to test the competing explanations. Collect such evidence in a justified future experiment; do not initiate another generic profiling/control project or enlarge natural roots here. Any common optimization must be offered fairly to strong and LOCAL and requalified. No paper edits are made.

Reproduce using existing Node:

```bash
node benchmarks/server_expansion_v1/N/local_cost_decision_20261113/analyze.js /tmp/local-cost-fresh
```

The script reads three small frozen result/fixture files, keeps every measured pair, derives conditional source geometry and sensitivity values, and emits a fresh report. It neither reads private tensors nor calls a tokenizer/native/GPU binary. Relevant source excerpts preserve original bytes/CRLF; generic whitespace checks intentionally exclude those byte-preserved evidence snippets.
