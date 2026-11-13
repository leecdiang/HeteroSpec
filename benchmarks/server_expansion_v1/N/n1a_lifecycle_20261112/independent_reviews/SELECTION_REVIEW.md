# Independent N1a episode selection review

`REVIEW_01/SELECTION_REVIEW.json` passes 27,386 checks with no failures. The checker imports no selection, candidate, tokenizer or geometry implementation. It rebuilds leaf ancestry from the raw messages, verifies each saved source path, fixes one leaf per root using only the declared leaf hash, and only then looks up frozen supplied-history predictions. Original data and all four episode-freeze files are unchanged after the review.

| Denominator | Count |
|---|---:|
| Raw messages | 4,401 |
| Unique user turns | 1,645 |
| Roots | 518 |
| Leaf paths | 2,241 |
| Paths containing at least two user turns | 1,456 |
| Roots with no such path | 218 |
| Fixed paths failing necessary supplied-history cap/stop compatibility | 145 |
| Fixed paths satisfying that necessary diagnostic | 155 |
| Compatible fixed-path predicted-difference roots | 4 |
| Compatible fixed-path predicted-no-difference roots | 151 |
| Selected development roots | 4: two per predicted stratum |

All 518 root outcomes remain represented. In particular, a fixed incompatible path is not replaced by a better path within its root. Root hashes select the first two roots within each requested predicted-geometry stratum; there is no token-offset, padding, template, timing or acceptance search. The original four N0 development fixtures and predictions remain unchanged, and all four retain their no-difference classification.

The two difference fixtures predict second-turn `(head, append)` of `(23,516)` and `(104,172)`; the two no-difference fixtures predict `(88,128)` and `(59,94)`. These values come from the immutable supplied-history predictions. Actual R output, native materialized head, stop condition, pending token, prefix repair and grouping are unknown. The saved episode file correctly records native head and actual free-generation compatibility as null, and native state as NOT_RUN.

The policy's wording correctly identifies this as exposed-source development coverage. It must not be described as representative natural-session sampling, a confirmation cohort, N2 eligibility, or evidence of the frequency of free-generation opportunities. The field `eligible_fixed_path_roots` is eligibility for the declared supplied-history fixture selection only, not native admission or future free-generation compatibility. Keeping that distinction adjacent to any reported denominator avoids a stronger reading.

Future R must generate its own assistant responses. The source assistant bodies are provenance for the prediction category, not the response text that may be forced into a future free session. Neither path nor user text may be replaced after observing native R output. If future free-generation grouping differs from its prediction, the episode remains selected and the discrepancy is reported.

The episode packet was also checked for absolute home paths, private IPv4 addresses and credential assignments; none were found. The selected user texts match the public raw corpus exactly. No native code, model forward, tokenizer, context, placement action or GPU operation was executed.
