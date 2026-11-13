# Why assistant KV was trimmed, and what remains for LOCAL

CPU-only successor of [PR236](https://github.com/leecdiang/HeteroSpec/pull/236), latest verified head `6597489d01d0fa1fb17dce8bf6cade2c53e3a463`; PR233 remains `4fc07500fbf4b8ac18fa5490eb53bf9c98b54845`. No new model/tokenizer/context/placement/forward ran. The old grant is exhausted at 43 requests / 14,444 rows / 4 deployments. No old STATE, references, data, negative result or baseline was modified.

The answer is **normal canonical serialization under the fixed nonthinking profile**, rather than an erroneous trim. The generation prompt contains an empty-think conditioning suffix, while canonical past assistant messages omit it. Exact prefix reuse must therefore stop before that suffix. The two-turn experiment also cannot reveal reuse of older, already canonicalized assistant history in a third turn. LOCAL has a real but small grouping opportunity beyond the common LCP reuse; it has not demonstrated service value here. Do not expand the natural-service panel to chase 5%.

## Direct reconstruction of the two actual free histories

All positions below are zero-based. [Machine-readable reconstruction](RESULTS/REPORT.json) reads the actual original R receipts from the PR236 public text packet, not a supplied assistant body. Both 128-token responses pass through their actual parser, OAI JSON, stored content and next request. In these two cases, concatenated sampled token-piece bytes equal client content, and re-tokenized canonical assistant bodies equal **all 128 sampled IDs**. Neither parser loss nor BPE resegmentation explains the first difference.

| Quantity | C0, English satellite question | C1, Spanish Mars question |
|---|---:|---:|
| Initial prompt length |92|27|
| First differing position / retained head |88|23|
| Old tokens there |151667, 271, 151668, 271|same|
| New first token there |785 (`The…`)|86693 (`Crear…`)|
| Materialized head after generation |219|154|
| Trimmed materialized rows |131 = 4 stub + 127 generated|same|
| Pending last sample, not yet in KV |279 at old position 219|12941 at old position 154|
| Canonical assistant body interval |[88,216)|[23,151)|
| Fresh canonical `im_end` position |216|151|
| Next canonical prompt length |250|551|
| Prefix reuse / canonical suffix / continuation rows |88 / 162 / 127|23 / 528 / 127|
| Second-request total rows |289|655|
| Cold same-input total rows |377|678|

The retained prefix includes user/template tokens **and the assistant role header**. It contains none of this response's body. The exact sequence is:

```text
old materialized:
  common user/template prefix || assistant role header
  || [<think>, double-LF, </think>, double-LF] || sampled body[0:127]
old logical only:
  ... || sampled body[127]                       # pending, no KV yet
next canonical:
  common user/template prefix || assistant role header
  || all 128 body tokens || <|im_end|> || next user || next generation prompt
```

The same body tokens shift four positions earlier and their causal conditioning changes. Equality of token IDs later in the stream cannot make their old KV valid: cache reuse is an exact **prefix**, not a search for matching substrings. The pending final body token is decoded at its new canonical position, not committed at its old position. After trim, the previous output frontier is invalidated; canonical suffix decode produces a new owned full output. Both strong and LOCAL perform the same trim and suffix reconstruction.

### What is source fact, observation, or inference?

**Source facts.** The fixed [4,100-byte template](RESULTS/chat_template.jinja), SHA256 `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`, appends `<think>\n\n</think>\n\n` when `add_generation_prompt=true` and `enable_thinking=false`. Its historical-assistant branch, before the latest user, emits role + content without that stub. [Actual producer](../free_service_retry_20261113/producer.cpp) explicitly uses that profile. It stores sampled content/reasoning via the real parser/JSON chain, never copies the generation prompt into assistant content. [Native reconciliation](../free_service_retry_20261113/native.cpp) computes token LCP, bounds it by materialized head, trims the suffix, then decodes the exact canonical remainder. This is source-visible intended behavior, not an assumed production deployment beyond the tested prototype.

**Observed.** Both actual first responses stopped at CAP128 and sampled no EOG. Their first difference is the opening think token, before any body token. The six-token EOG predicate was active; `151645` is one EOG ID, and is also the canonical message delimiter. No EOS was invented as an actually generated token. The next template legitimately emits `151645` even after a capped response. The prior ABI consumer failure is preserved but does not cause this behavior: original R and independent repeat exhibit it before candidates; repaired candidates reproduce exact output/state.

**Inference, with scope.** Cap affects body length, pending and opportunity geometry, but cannot explain an earlier first difference already inside the prompt stub in these receipts. A hypothetical earlier EOG would change the tail; it would not repair this already mismatched prefix if the same historical-body serialization remains. We have not measured free EOG in these runs, nor proved all future responses behave this way. The nonthinking profile is a legitimate chosen mode, not every deployment's default. Changing thinking mode, retaining the obsolete stub in content, or switching to raw-token completion would change the request contract and cannot repair this result under its frozen semantics.

**PR233 is a different evidence tier.** It performed real numerical execution on supplied/forced assistant token IDs and a synthetic pending EOG, not free generation. Its reused native state receipts show C0 heads `92 → 186 → 88 → 216`, C1 `27 → 143 → 23 → 539` (initial prompt / supplied old state / trimmed / next canonical). The same stub mismatch is present. These records corroborate trim execution; their supplied EOG must not be described as a model's observed stop. This review reuses text receipts/certificates and does not independently revalidate private tensor bytes.

## Older assistant history can survive without changing the contract

At turn 3, the previous prompt already contains assistant 1 in canonical form. The next prompt repeats that same old content before reaching assistant 2's obsolete generation stub. Thus assistant 1's **recomputed canonical KV** can remain in the LCP. This is not recovery of the original sampled assistant 1 KV that was discarded at turn 2, and is shared by strong and LOCAL.

We inspect the saved original OASST1 validation universe, revision `fdf72ae0827c1cda404aff25b6603abec9e3399b`: 4,401 messages, 518 roots, 1,645 unique user turns, 1,127 subsequent turns. No new corpus, template, offset or output search, and no N0 tokenizer/model census rerun. All 331 third-or-later supplied user-turn nodes contain retained older canonical assistant message spans (29.37% of later nodes); 93 do in the inherited short-body/synthetic-EOG subset (93/511 = 18.20%). Span assignment has 0 unsupported literal-delimiter cases. These are **saved supplied-history token predictions**, not new resident/free-generation observations or independent-root samples.

[First source-order examples](RESULTS/SOURCE_ORDER_EXAMPLES.json) include the ordinary three-user Berlin conversation, retained head42 with 7 interior older assistant-body tokens. Strong and LOCAL both use three outer calls for its 87-row suffix: historical assistant KV reuse alone does not establish a unique LOCAL opportunity. The first unrestricted older-history example has a long supplied response incompatible with the old 128-token synthetic-EOG replay; it is retained as a denominator/example, not admitted as a GPU candidate.

## LOCAL's exclusive opportunity is grouping, not fewer tokens

| Evidence / scope | Whole-rechunk W | LOCAL L | Meaning |
|---|---:|---:|---|
| PR236 C0, observed complete episode |263 decode calls|263|identical plans and selected graph callbacks|
| PR236 C1, observed complete episode |273 decode calls|272|one fewer actual caller/physical decode|
| C1 second canonical suffix, observed plan |18 groups / 528 rows|17 / 528|same rows and retained KV|
| C1 selected GPU-resident graph-node callbacks, heavy |159,861|159,788|recorded callback count, not CUDA launch count|
| C1 loop4-named callbacks, heavy |684|648|recorded tagged subset, not all projections|
| C1 suffix, source-derived four-column groups* |133|132|small projection grouping opportunity|
| C1 suffix, source-derived four-query attention tiles* |133|134|an offsetting fragmentation cost|

\* Fully consumed intermediate-projection/query grouping proxies derived from actual plan extents and fixed source. They are not measured CUDA kernel launches, complete layer FLOPs or isolated GPU time. Requested-output pruning remains unchanged. The [five relevant frozen source files](SOURCES/RELEVANT_SOURCE_IDENTITIES.json), only 504,303 bytes, were checked once: graph, KV extent, CUDA dispatch and the original planner. Exact [graph excerpts](SOURCES/graph-3007-3047.txt) show attention-local splitting; [projection excerpt](SOURCES/graph-1570-1587.txt) and [CUDA excerpt](SOURCES/cuda-1819-1844.txt) show the four-column path.

For a suffix of N rows, width32 and padding256, whole-rechunk is already strong. All complete 256-row extents fit eight 32-row calls. Only the first/last partial segments can change rounding, so `0 <= calls_W − ceil(N/32) <= 1`. LOCAL cannot save an increasing number of outer calls just by making one append longer in this profile. Splitting projection groups at an attention boundary may also alter four-column tails; keeping them wide may add attention tile fragments. Decode rows, required state and per-token padded attention arithmetic remain equal.

### Frequency in the existing supplied workload, not a free-request estimate

| Saved cohort | Later nodes | Different partitions | Fewer W→L outer calls | Fewer intermediate four-column groups* | Either grouping opportunity* |
|---|---:|---:|---:|---:|---:|
| All supplied histories |1,127|512|271|203|345|
| Original short-body + synthetic-EOG diagnostic |511|38|20 (3.91%)|9|24 (4.70%)|

All source rows remain in the [per-turn CSV](RESULTS/TURN_OPPORTUNITIES.csv). In the short cohort, total outer calls are 2,909→2,889, intermediate four-column proxies 19,771→19,762, attention tile proxies 19,771→19,809; both decode 77,473 suffix/prefill rows. These cohort totals include initial requests. The all-supplied totals and root denominators are in [REPORT](RESULTS/REPORT.json).

The old diagnostic requires each supplied body **plus synthetic EOG** to fit128. It is not an observed free-generation rate, and not even a necessary condition for all genuine CAP128 histories: PR236 actually generated128 body tokens without EOG. Conversely, long provided bodies need not be realizable under a fixed cap. No cohort percentage here is promoted to natural free-service prevalence. Of the two preselected actual free cases, one saves a call; 1/2 is merely that development pair, not a prevalence estimate.

## Cost judgment and next step

PR236 already performed the two-case service A/B: W36.3853s, L37.9207s. About1.4197s of the1.5353s gap falls in the common O0 full-vocabulary CPU sampling span, while the equal-partition control also slows and C1 reverses direction between rounds. Neither a stable LOCAL slowdown nor an attributable gain is established. No separate suffix-only latency or CUDA launch cost was recorded; we do not reconstruct one by subtracting unrelated experiments or overlapping phases.

A cleaner **mechanism** candidate exists without offset selection: the first source-order short supplied-history node with a positive call gap is the Catalan videogame conversation, message `110d8fa6-0701-455d-b3f9-ebf8064db601`. Its saved canonical head232/suffix89 gives W `[24,32,32,1]`, L `[32,32,25]`. Both have23 four-column groups and23 attention tiles, making it a graph/quantizer/caller-overhead question rather than the C1 tile tradeoff. The input contains an ordinary third-user follow-up; it is not a manufactured prompt. However, this geometry is from supplied history, and free generation could produce a different head/append. Do not force a free session to match it or call replay a live session.

Recommended decision: preserve the correctness and bounded grouping result; **do not start another natural-service GPU panel**. If distinguishing call overhead matters to the paper, the [minimal 8-request A/B design](MINIMAL_AB_PLAN.md) isolates this existing canonical append, with independent reference/repeat, full state/output comparison, matched warm modes and reversed order. It needs new explicit authorization and is not currently implemented/launched. It cannot establish whole-session speedup. Otherwise this investigation is a sufficient negative/limited-opportunity closeout.

Paper-usable: the fixed producer requires canonical suffix repair; limited free resident/cold/strong/LOCAL equivalence exists; a real one-call grouping reduction was observed; larger supplied histories can retain older canonical assistant states conditionally. Not usable: “assistant KV is never reusable,” “LOCAL uniquely saves history tokens/attention FLOPs,” “331 GPU-qualified natural sessions,” stable 4.22% slowdown, general 5% speedup, or a new blind/confirmatory panel. No paper edits are made here.

Reproduce with existing Node only:

```bash
node benchmarks/server_expansion_v1/N/resident_opportunity_20261113/analyze.js /tmp/resident-opportunity-fresh
```

This reads prior public text/token evidence and writes a fresh derived report; it runs no tokenizer or native binary. Relevant model/template/source identities are reused or checked once, not a sweep of historical files. One initial CPU extraction incorrectly associated dispatch by overlapping positions across turns; a row-count assertion rejected it before reports. It was corrected to bind each physical record's request ID. The failed local output/log is retained; no GPU budget was consumed. Source, identity, input/output and stop-contract assertions pass on the completed review.
