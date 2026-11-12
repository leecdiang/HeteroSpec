# Independent saved-token review

`CHECK_03/INDEPENDENT_REPORT.json` passes 118,207 checks with no failures. The earlier `CHECK_01` and `CHECK_02` remain preserved. CHECK_03 limits the input snapshot to eight read or freeze-bound N0 inputs and exactly four comparison files. Its 12-check reduction from CHECK_02 removes only byte-preservation checks on unrelated local documents; all semantic, token, ancestry and geometry assertions are unchanged. The standalone verifier imports no comparison, contract, corpus, or geometry implementation. It reads the original raw messages, saved native vocabulary/tokenization receipts, and frozen comparison files; it does not invoke a tokenizer, native runner, model, GPU context, or placement action.

The verifier resolves raw ancestry itself and confirms all 4,401 source messages, 518 roots, 1,645 unique user turns, 1,127 later turns, and 2,241 leaf paths. It checks the input hashes/bytes, exact saved A references, all 518 per-root aggregates, every C suffix reconstruction, and each ordered whole-fixed, strong whole-rechunk, LOCAL outer, and LOCAL inner group. All original and `COMPARISON_01` files remain byte-identical after verification.

| Description | Full supplied-history denominator | Necessary cap/stop-compatible diagnostic |
|---|---:|---:|
| Later turns | 1,127 | 511 |
| Whole old logical history remains a canonical prefix | 0 | 0 |
| C exact canonical reconstructions, including initial turns | 1,645 | 1,029 |
| C distinct strong-rechunk/LOCAL ordered partitions | 512 | 38 |
| Roots containing distinct partitions | 212 | 27 |
| Strong whole-rechunk calls | 9,644 | 2,909 |
| LOCAL outer calls | 9,373 | 2,889 |
| Extra whole-rechunk calls | 271 | 20 |
| LOCAL inner attention groups | 10,054 | 2,946 |
| Canonical full-rebuild token rows | 399,786 | 103,636 |
| C replayed canonical-suffix token rows | 274,923 | 77,473 |
| Common retained token occurrences | 124,863 | 26,163 |

All predicted per-token padded attention work is equal between strong whole-rechunk and LOCAL. The retained rows are an advantage of a common LCP repair policy over full rebuild; they cannot be attributed to LOCAL. The distinct-partition counts describe an opportunity to investigate ordered graph/projection grouping, not an observed speedup or proof that the opportunity is meaningful in a deployed service. Most of the larger raw geometry difference occurs in supplied histories that do not satisfy even the necessary cap/stop condition.

For all later turns, predicted retained head spans 10–1,219 tokens and replayed append spans 16–1,968. For necessary-compatible later turns, the ranges are 10–338 and 16–1,908. For the 38 compatible distinct-partition turns in 27 roots, they are 14–238 and 65–1,908. All canonical prompts fit the stated C4096/cap128 geometry; this is not a measured runtime placement or memory result.

All 1,127 first differences occur at the start of the previous prompt's four-token empty-thinking suffix `[151667, 271, 151668, 271]`. Retaining that old suffix to manufacture append-only matching changes the unchanged canonical input. B therefore has no compatible later turn under the frozen A input contract. C trims to the token LCP, bounded by the predicted materialized head, discards the old hypothetical pending token outside that prefix, and replays exactly the canonical suffix. Every reconstruction is token-identical, but this does not establish KV/frontier or reference-output equivalence.

The old body-only over-cap diagnostic flags 614 later histories. Accounting for the hypothetical provided EOG flags 616: a supplied body of exactly 128 tokens plus an additional EOG cannot fit cap128, and its two descendant user turns are affected. All six actual vocabulary EOG IDs were checked; no supplied body contains one. This sensitivity diagnostic is not a new selected cohort. Real generation could instead stop at cap with a non-EOG pending token; no EOG is manufactured for an actual cap termination.

The source-backed upstream LCP/trim/replay path remains an integration candidate for the N worker, whose present per-request reset does not implement a qualified resident turn handoff. No actual producer output, native head, pending token, stop reason, teacher-forced native replay, or free-generation history was observed here. The reported zero observed compatible free-generation histories means that no such observation exists; it does not estimate the true compatibility rate as zero.

The raw source, model identity, tokenizer identity, and template hashes were checked as saved provenance. This verifier does not reopen or independently hash the model weights, execute the source-supported trim path, or replace future sequential-reference qualification. No numerical, placement, performance, or N1 success is claimed.

Run `independentcheck.js` with explicit comparison-workspace, original-N0-workspace, and a **new** output directory. It refuses to overwrite an existing report. The public report uses portable `N0/<basename>` and `comparison/<basename>` identity keys, retaining file hashes and byte counts. The exact N0 dependency list is `SPEC.json`, `CORPUS.json`, `TURN_CENSUS.json`, `CENSUS_REPORT.json`, `TOKENIZER_OUTPUT.jsonl`, `FOUR_DEVELOPMENT_SOURCE_INPUTS.json`, `MESSAGES.json` and `chat_template.jinja`. The comparison list is `FREEZE.json`, `REPORT.json`, `TURN_COMPARISON.json` and `PER_ROOT.json`. Additional directory contents do not affect the check count or input identity map.
