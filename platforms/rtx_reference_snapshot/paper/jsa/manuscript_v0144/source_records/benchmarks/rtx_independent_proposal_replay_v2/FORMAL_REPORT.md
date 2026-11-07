# Prospective reserved formal results

Status: **PROSPECTIVE_REPLAY_MATCH_DISCRIMINATING**.

| Comparison | Full arrays | Wholly matching distinct prompts |
|---|---:|---:|
| H2_live | 72/72 | 24/24 |
| R_ONLY_live | 72/72 | 24/24 |
| reference_live | 60/72 | 20/24 |
| H2_R_ONLY | 72/72 | 24/24 |

All within-condition three-repeat arrays stable: True. Repetitions are not independent prompts.

Actual reference-divergent distinct prompts: 4.

Every first difference (zero-based committed-ID position; missing ID is null):

| Comparison | Task | Rep | Position | Left ID | Right ID |
|---|---|---:|---:|---:|---:|
| reference_live | HumanEval/17 | 1 | 4 | 1406 | 271 |
| reference_live | HumanEval/17 | 2 | 4 | 1406 | 271 |
| reference_live | HumanEval/17 | 3 | 4 | 1406 | 271 |
| reference_live | HumanEval/33 | 1 | 8 | 14937 | 4210 |
| reference_live | HumanEval/33 | 2 | 8 | 14937 | 4210 |
| reference_live | HumanEval/33 | 3 | 8 | 14937 | 4210 |
| reference_live | HumanEval/14 | 1 | 4 | 1406 | 271 |
| reference_live | HumanEval/14 | 2 | 4 | 1406 | 271 |
| reference_live | HumanEval/14 | 3 | 4 | 1406 | 271 |
| reference_live | HumanEval/22 | 1 | 0 | 1499 | 750 |
| reference_live | HumanEval/22 | 2 | 0 | 1499 | 750 |
| reference_live | HumanEval/22 | 3 | 0 | 1499 | 750 |

The paired arrays and native/tape events are retained in the content-addressed evidence package. Equality is assessed element by element through inclusive EOG or 128 committed IDs, including length.
