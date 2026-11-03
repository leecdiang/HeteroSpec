# RTX shared planner transfer

The frozen candidate passed the retained original-R controls and all eight unseen inputs. The fixed cost panel completed 120 measured requests and 120 immediate warmups.

| Family | Heavy qualification cells | Committed vectors | M_QB/M_PQ | C_QB/C_PQ | M_QB/C_QB | M_PQ/R | M_QB/R | C_PQ/R | C_QB/R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen8b02 | 20 | 2540 | 1.016815 | 0.958175 | 1.194423 | 0.519154 | 0.527884 | 0.461249 | 0.441957 |
| qwen14b02 | 20 | 2560 | 0.983533 | 0.976817 | 1.658557 | 0.552142 | 0.543050 | 0.335194 | 0.327423 |

| Family | Original R preparation (s) | Qualification (s) | Formal model loading (s) | Warmup service (s) | Measured service (s) |
|---|---:|---:|---:|---:|---:|
| qwen8b02 | 65.812 | 242.422 | 12.369 | 296.118 | 297.970 |
| qwen14b02 | 228.594 | 716.140 | 14.916 | 1499.364 | 1517.697 |

The supervisor stopped the first 8B timing attempt after one unpaired warmup because its reference-index file was missing. That warmup and its receipt remain charged separately. Zero measured requests occurred in the failed attempt. The published panel uses the original registered order and includes every matched block.

The old executable supplied each qualification reference. The timed R arm uses the candidate runtime's ordinary path after its complete committed vectors match that reference. Per-session ratios, input ratios, every service interval and the blocks on the opposite side of one from each aggregate are recorded under evidence/.

| Family | Input and start position | Layout | Planned (extent, width) | Observed QK (extent, width) | Layers |
|---|---|---|---|---|---:|
| qwen8b02 | CodeContests/valid/32 at 510 | C_PQ | [[512, 2], [768, 2]] | [[512, 1], [768, 1]] | 36 |
| qwen8b02 | CodeContests/valid/32 at 510 | C_QB | [[512, 2], [768, 2]] | [[512, 2], [768, 2]] | 36 |
| qwen8b02 | GSM8K/test/806 at 99 | C_PQ | [[256, 4]] | [[256, 1]] | 36 |
| qwen8b02 | GSM8K/test/806 at 99 | C_QB | [[256, 4]] | [[256, 4]] | 36 |
| qwen8b02 | CodeContests/valid/32 at 514 | C_PQ | [[768, 4]] | [[768, 1]] | 36 |
| qwen8b02 | CodeContests/valid/32 at 514 | C_QB | [[768, 4]] | [[768, 4]] | 36 |
| qwen14b02 | APPS/test/858 at 254 | C_PQ | [[256, 2], [512, 2]] | [[256, 1], [512, 1]] | 40 |
| qwen14b02 | APPS/test/858 at 254 | C_QB | [[256, 2], [512, 2]] | [[256, 2], [512, 2]] | 40 |
| qwen14b02 | MBPP/123 at 47 | C_PQ | [[256, 4]] | [[256, 1]] | 40 |
| qwen14b02 | MBPP/123 at 47 | C_QB | [[256, 4]] | [[256, 4]] | 40 |
| qwen14b02 | GSM8K/test/111 at 92 | C_PQ | [[256, 4]] | [[256, 1]] | 40 |
| qwen14b02 | GSM8K/test/111 at 92 | C_QB | [[256, 4]] | [[256, 4]] | 40 |
| qwen14b02 | GSM8K/test/120 at 63 | C_PQ | [[256, 4]] | [[256, 1]] | 40 |
| qwen14b02 | GSM8K/test/120 at 63 | C_QB | [[256, 4]] | [[256, 4]] | 40 |
| qwen14b02 | APPS/test/858 at 258 | C_PQ | [[512, 4]] | [[512, 1]] | 40 |
| qwen14b02 | APPS/test/858 at 258 | C_QB | [[512, 4]] | [[512, 4]] | 40 |

qwen8b02 recorded 0 host-weight placement queries where scalar and batch preferences differed and the scalar preference was selected.

qwen14b02 recorded 8398 host-weight placement queries where scalar and batch preferences differed and the scalar preference was selected.


PR159 recorded twelve failing input/arm/producer combinations across GSM8K/test/111 and GSM8K/test/120. Two identical recipes were covered before freeze. A review of the historical failure ledger found ten missing recipes; these were tested after the fixed panel, using the same frozen binary. R/pq and R/qb are historical alternate-producer diagnostics. Every recipe uses the unchanged original R as its oracle. PR159_RECIPE_AUDIT.json records the historical first differing token, the exact old and new record identities and the complete committed-vector comparison for each recipe.

| PR159 input | Arm | Producer | Historical first token difference (zero-based) | Frozen endpoint | Different committed vectors |
|---|---|---|---:|---|---:|
| GSM8K/test/111 | R | pq | 16 | True | 0/128 |
| GSM8K/test/111 | R | qb | 16 | True | 0/128 |
| GSM8K/test/111 | M_PQ | native | 16 | True | 0/128 |
| GSM8K/test/111 | M_QB | native | 16 | True | 0/128 |
| GSM8K/test/111 | C_PQ | reference | 16 | True | 0/128 |
| GSM8K/test/111 | C_QB | reference | 16 | True | 0/128 |
| GSM8K/test/120 | R | pq | 82 | True | 0/128 |
| GSM8K/test/120 | R | qb | 82 | True | 0/128 |
| GSM8K/test/120 | M_PQ | native | 82 | True | 0/128 |
| GSM8K/test/120 | M_QB | native | 82 | True | 0/128 |
| GSM8K/test/120 | C_PQ | native | 82 | True | 0/128 |
| GSM8K/test/120 | C_QB | native | 82 | True | 0/128 |

FREEZE.json records the predicted and observed groups, scalar placement override counts and executed source identities. The 8B all-GPU cohort and partially offloaded 14B cohort are reported separately. The retained audit and Llama control receipts are under evidence/. The per-family SERVICE.json separates loading, reference preparation and every warmup and measured service interval.

The first exploratory epoch inherited a stale static-core digest. The final diagnostics bind the actual compiled libraries and executables. Earlier attempts remain under E:/rtx164. No experimental outcome depends on changing the original R.

Reproduction order: authenticate PR162 sources, stage CUDA through integrate_llama_cpp.py, build the two pinned cohorts, then run focused.py, audit_focused.py, llama_controls.py, freeze.py, select_panel.py and confirm.py. Prepare pool.py before selection. Saved native raw is under E:/rtx164 on the RTX host.
