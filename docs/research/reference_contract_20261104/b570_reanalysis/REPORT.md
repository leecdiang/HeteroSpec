# Independent B570 historical recomputation

Run date: 2026-11-04 UTC. No native GPU execution, user device access, PR changes, or new empirical observations. All calculations are reproducible with Python's standard library: `python recompute.py`. Inputs are in `sources/`, computed results in `RECOMPUTED.json`. Exploratory bootstrap uses 10,000 root-level resamples, seed 20261104; it is not a preregistered confirmatory analysis or population guarantee.

## Findings that change how the paper should be written

1. **PR152's 39/48 `strict_reference_equal` cells are token-endpoint equalities, NOT the later full-FP32-vector/KV reference contract.** `analyze.py` lines 26 and 35 directly compare `row['endpoint']`; endpoint contains IDs, EOG flags, length, stop reason and terminal ID. Its local PQ/QB equality has a separately audited stronger full-vector/cycle comparison. The 39 successful cells cannot qualify the later stronger contract. Both producer KV and initial full-vocabulary logits differ on all eight inputs. A reader needs an explicit contract/evidence legend separating these historical generations.
2. **Fewer calls does not imply lower latency.** In PR169's 129 matched crossing cells, 48 have fewer QB calls but slower QB than WB. At q32 WB is faster in 9/9 Qwen C1024, 11/12 Qwen-target C4096, and 6/6 Smol C4096 cells. Qwen q16 also reverses in 9/9 cells. Any AUTO objective that minimizes call count alone is falsified by already available evidence.
3. **The natural-workload null is not a failure to count the old positive microbenchmarks.** PR169 natural WB/QB is 1.000292 over 72 matched blocks/12 independent inputs, root-bootstrap interval [0.999661, 1.001204]. Leave out MBPP/519 and the mean reverses to 0.999899. The much larger 1.477964 PQ/QB and 2.121786 S1/QB improvements survive leave-one-root-out but concern weaker baselines. The strongest WB comparison remains null.
4. **PR175's apparent crossing subgroup advantage is fragile.** Only 4/32 heldout roots cross, and 0/12 calibration roots cross. In those four, WB-cut/QB is 1.004802, but individual root ratios are 1.000832, 0.984909, 1.033839, 1.000259. Removing the head205/append84 root reverses it to 0.995306. Do not present this post-hoc 0.48% subgroup as rescued evidence of a general gain.
5. **Rechunking is not always a call-count optimization.** On all PR175 roots, WB-cut and WB-rechunk have identical total call counts. The four crossing roots have calls 2/2, 2/2, 4/4, 2/2 respectively (QB 1,1,3,1). The crossing cut/rechunk ratio 1.004736 must not be explained by fewer calls; ordering/shape/extent or noise are possible explanations requiring a controlled intervention.
6. **An initial logit norm threshold cannot certify safety.** In PR152 a divergent input has initial max-absolute producer difference 0.345907569, while an all-six-endpoints-equal input has 0.616662025. All eight have nearly every vocabulary component differing. State/vector difference neither predicts greedy divergence monotonically nor permits dropping the strict contract.

## What was actually recomputed

### Historical clean receiver causal study (PR101, not PR126/127)

PR126 and PR127 changed source-only CPU8 guard/audit work and are not fresh independent native experiment panels. The relevant native causal study is `b570_final_causal_closeout_v1`, originally PR101.

Direct equality of the serialized full endpoint objects in `KV_LOGITS_CROSS.json` reconfirms AA=AB and BA=BB on all four tasks. KV-source first differences are zero-based 47 and 81 on affected GSM8K1248/831; stable1011/1249 remain equal. All four initial logits choose the same top1 token. This supports the conditional KV-mediated continuation outcome within the specific clean receiver. The initial-logit swap is a negative control, not proof that logits generally do not matter. Three or two repetitions of the same task do not increase independent task coverage.

The partition matrix retains a useful nonmonotonic counterexample: for1248, 128+33 produces B/C while160+1 returns A; for831,132+1 matches none of A/B/C. Thus neither “longer than128” nor a single boundary flag fully describes the numerical recipe. Different state bytes on stable1011/1249 also do not entail different token outputs. Full-state equivalence is a stricter property than finite observed output equivalence.

Native same-arm replay qualification failures for eight MUL calls remain excluded; exact Vulkan pipeline identity was unknown. This pass does not use invalid operator replays as causal evidence.

### PR152 producer × consumer

From raw endpoint IDs in `COUNTEREXAMPLE_ENDPOINTS.json`, independently recomputed all18 affected producer/consumer endpoints across input indices2/4/6, rather than trusting MATRIX equality booleans. Results reproduce first differences (one-based): GSM1184 P1 local30, P4T C1/local30 against R; MATH1865 P1 local5; MATH1804 P1 local25. All endpoints have registered full CAP/EOG semantics. P4T local versus its own C1 on GSM1184 has a separate reported first difference32, which should not be confused with local versus R30.

Full MATRIX count is39/48 token-endpoint matches; 16/16 local input-producer PQ/QB pairs have separately reported full-vector agreement. Two MATH matrices have C1 safe under both producers, local unsafe afterP1/safe afterP4T. This rules out independently assigned binary producer-safe and consumer-safe flags as a complete acceptance model. It does not rule out relational contracts, state-indexed proofs, or a stronger operator-level reference-preserving implementation.

PR152 changes KV+initial-logits together. The older Llama factorial intervention isolates KV under a different model/runtime and cannot be used as if it independently isolates Qwen PR152's mechanism.

### PR165 repair and timing

The later F32 activation repair supersedes the historical Qwen failure. The retained original P1 MATH states resume with all128 committed vectors matching original R; the precision-only reversal reproduces the old205-vector failure. Historical failures remain valuable regression cases, not proof the current repair still fails.

From all120 raw timing records, paired by input/session:

| Contrast | Geometric time ratio | Exploratory root-bootstrap95 | Leave-one-root-out range |
|---|---:|---:|---:|
| M_QB/M_PQ |0.915047|[0.902088,0.927997]|[0.910508,0.919555]|
| C_QB/C_PQ |0.969123|[0.965904,0.971714]|[0.968380,0.970475]|
| M_QB/C_QB |0.269172|[0.260014,0.279320]|[0.265279,0.272207]|
| M_QB/R |0.603813|[0.570862,0.639851]|[0.589944,0.613494]|
| C_QB/R |2.243222|[2.190386,2.301686]|[2.223862,2.258098]|

These are eight finite, selected roots with three sessions each, not24 independent inputs. R has scalar prefill while integrated M/C use P4T, so M/R cannot isolate a decode innovation. The existing instrumented single-input phase report has ordinary decode3.519s versus3.516s: almost all measured M_QB/R benefit there comes from prefill6.301s versus2.350s. Speculative C_QB's2.243xR cost and M_QB/C_QB0.269 demonstrate that continuing to make speculation the headline is unsupported for this deployment.

### PR169 geometry and service

Independently paired all1395 fixed-work observations by `(family,C,B,head,q,rep)`, classified a crossing from `head//256 != (head+q-1)//256`, and recomputed all strata.1395 is an arm-observation count, not independent comparison count.129 crossing WB/QB pairs include repeated geometries. The 48 counterexamples split19Qwen+23Qwen-target+6Smol.

At crossing q2/q4/q8 Qwen WB/QB is1.216865/1.313815/1.193294; q16/q32 becomes0.954744/0.947835. Qwen-target similarly changes from1.129786/1.133288/1.076499 to0.990039/0.985473. Smol's reversal occurs only atq32: q16=1.083004, q32=0.918310. The boundary depends on model/deployment and width; pooling all widths obscures the sign change.

This is an empirical cost-model counterexample, not a unique causal identification of the kernel responsible. A q16/q32 dispatch threshold, smaller split geometry, memory traffic, utilization, and allocation shape require separate trace/ablation to distinguish. The C4096 Qwen-target deployment omits the draft model relative to C1024 dual deployment, so differences must not be attributed solely to context capacity.

All288 natural timing records (four arms ×72 blocks) reproduce the published ratios. Twelve roots, not72, are the conservative resampling unit. The natural WB/QB sign is unstable under root omission; the scientific conclusion remains no demonstrated practical advantage over WB.

### PR175 natural prefix reuse

Joined pinned panel metadata to the32 root-level aggregate ratios. Main per-session native timings are not in the fetched compact repository files, so this is a root-summary reanalysis, not a fresh512-record main timing reconstruction. Noncrossing28 roots have WB-cut/QB1.000162 and cut/rechunk0.999923. The4crossing roots have1.004802 and1.004736, but the leave-one-root-out reversal above prevents a robust subgroup claim. WB-rechunk is the frozen constant AUTO policy; a named AUTO arm is not proof an adaptive selector learned anything.

## Proposed research decisions

- Make the contract hierarchy explicit: complete greedy endpoint; committed full-vector reference; full state/KV; local PQ/QB equivalence; runtime admissibility. Use distinct field names in new reports, preserving old immutable artifacts.
- Use the repaired reference-preserving ordinary batch path as an essential baseline. Do not compare an optimized verifier only against old scalar or PQ paths and call that the novel system gain.
- Model cost by qualified kernel/shape/extent and lifecycle overhead, not just crossing count. Keep q16/q32 reversals as mandatory negative regression tests.
- Prioritize the new packed-kernel work only if it beats the strongest qualified whole-batch/loop baseline under the same output/state contract and costs. These historical results justify that experiment; they do not predict its result.
- A new cache study needs a prospectively stratified calibration set covering decision-relevant crossings and a natural heldout set retaining its real frequency. Do not train a selector on0crossings then infer lack of a learnable crossing effect; conversely do not oversample crossings and report the resulting gain as production average.
- Test a direct cost mechanism with same state/input/tokens and identical call counts but deliberately varied grouping. A kernel policy switch without restoring prior state must remain separately guarded: PR165 native probes show numerical history can persist after switching back.
- Treat exact-state validation overhead as a separately measured production cost; historical results cannot establish the performance of the new checkpoint/guard implementation.

## Evidence and reproducibility limits

This pass directly reads complete repository-visible endpoint IDs and compact per-request native timing records; it does **not** newly download/re-hash every full binary32 vector/KV object from the multi-GB private release archives. Existing remote readback receipts are prior claims, not a substitute for this pass's own raw reconstruction. Full-vector assertions above are explicitly source-reported unless they are endpoint comparisons. Raw operator attribution, exact full-state equality and repeatability on another physical device are not independently reproduced here.

Fixed source commits:
- PR101 study as preserved at `41ff8fd61f1c1275cf2c36103af0fa0e889b908a`, `benchmarks/b570_final_causal_closeout_v1/`.
- PR152 `022babfabb3d1b6f4f2a2830dca04b2654d193f9`, `benchmarks/b570_producer_consumer_boundary_v1/`.
- PR165 `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f`, `benchmarks/reference_batching_transfer_20261103/b570_host/`.
- PR169 `8ca17478c292275b3515a91b51d0e791a8fae256`, `benchmarks/b570_parallel_v1/`.
- PR175 `cd5f542a851d192e21187bc00566de0f685e2383`, `benchmarks/b570_prefix_reuse_v1/`.

Example direct source: https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/analyze.py#L35 . Complete fetched-source SHA256 receipts are in RECOMPUTED.json; compact input projections and downloaded-source hashes are in SOURCE_INDEX.json. Complete sources remain accessible at the pinned GitHub paths.

## Observer qualification and packaged input limits

PR152 endpoint reconstruction here uses observer-off entries; the original source separately retains heavy/off shams. PR165 and PR169 formal timing records are reported as clean observer-off timing windows, not instrumented phase estimates. This CPU pass does not independently re-attest their loaded binaries or observer state. PR175 phase fields were unmeasured in clean main timings; zeros are not zero-cost evidence. Compact source files in this folder are deterministic field projections, not unaltered copies of the full source files. SOURCE_INDEX.json records both source-content and compact-content SHA256.
