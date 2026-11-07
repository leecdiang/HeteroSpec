# Why these experiments, and not another rescue campaign

## Research decision

The next decision is whether any concrete reference-compatible transformation offers useful value beyond a simpler same-contract implementation. The two most direct alternatives are (1) a backend four-column loop instead of graph-level tiling/concat, and (2) an ordinary wider draft prefill. Contract machinery, masked MMA and AUTO do not replace these comparisons.

The old numerical reference matters because this project promises compatibility with an already selected deployed trajectory and its continuation state. It is not more mathematically accurate by definition. The primary contract is **T**: preserve target values on the actual compared prefixes, committed active target state/frontier and autonomous greedy endpoint. Draft logits/proposals/acceptance and number of target calls may differ. A separate TD claim, fixing draft trajectory as well, is not tested or substituted when T competitors are faster.

## Evidence that led to this design

- PR171 `371223b696bb805030c29f04e39eb17b57fb2ebb`: packing improved four-input resident service ~4% versus graph tiles, but equally optimized WB was slightly faster than QB. The new packing comparator is PR180 loop4, not another weak per-row implementation.
- PR174 `aa7ff4e64752be3de0d7974febbce453ae3a96c0`, PR175 `cd5f542a851d192e21187bc00566de0f685e2383`: no demonstrated natural AUTO service benefit.
- PR177 `610fd3a364bec6e8a3881ef666bedacd2035679a`: the simple rechunk caller was faster on the conditional append point estimate; no stable service improvement. Stop searching for a QB-winning offset.
- PR180 `7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd`: compiled strong CUDA control, no GPU equivalence or speed result.
- PR183 `895c20513bd086d389ea52a60d0cd52a89bec73d`: useful synthetic CPU bridge, not the original GPU/resident R. Source and synthetic checks can be reused, not their numerical qualification.
- The uploaded morning report's additional 240-pair budgets and late-rejection results were not yet independently recovered. They are opportunity estimates only. Rebuilt results get new run identities and cannot backfill missing original artifacts.

## A design correction discovered in the actual sources

RTX PR151 calls draft prefill once on the full prompt; physical UB1/2/4 is a clean caller-preserving intervention. B570 PR152/165 instead calls `draft->prefill(prompt, vector<int>(prompt.size(),1))`. Raising its physical microbatch alone leaves all actual calls scalar. Therefore B570 needs a caller-only C4U1 control, then C4U2/C4U4. A positive result must be attributed to caller consolidation, physical microbatch, or their combination—not described as a pure UB effect.

## Scope restraint

No third GPU, new model download, MMA kernel, dual cache, asynchronous prefill overlap, online AUTO, general transaction subsystem, HTTP/concurrency benchmark, or arbitrary quantization sweep is part of this package. Per-request full captures are diagnostic work; they are not an always-on production requirement unless the candidate really needs them. Compare with identical legal optimizations in the baselines. If a simple fixed implementation is best, recommend it.

GPU experiments are allowed only in the finite, authorized original-host research setup after a minimal actual reference/observer bridge. This is not a requirement to finish an adversarial remote-attestation product or prove arbitrary hidden-state equivalence before collecting any useful evidence.

## What would change the paper decision

1. Packed beats backend-loop4 with the same quantizer/reference, and the difference survives the full request window: useful new positive evidence.
2. Ordinary wide draft gains under T: identify the attainable strong baseline; the configuration change alone is not new research.
3. A proposed additional transformation would then have to beat that baseline, not the previous artificially restricted draft.
4. Loop4 or ordinary wide draft explains all gains: keep the mechanism findings, reduce performance/novelty claims and reassess TPDS rather than adding safeguards to manufacture a bigger contribution.

No percentage is an IEEE acceptance threshold. No number of CPU tests counts as an additional model or a GPU replication.
