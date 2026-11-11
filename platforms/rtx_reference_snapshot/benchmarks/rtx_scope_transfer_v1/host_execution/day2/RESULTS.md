# Registered three-date RTX scope-transfer results

Both families passed the complete public audit:1288 primary requests =196 qualification +1008 formal measurements +84 charged warmups. All three actual Shanghai dates (October30, October31, November1) and twelve independently loaded family-session processes are present. The separate54 Llama diagnostics remain retained; no numerical retry, technical reserve, extra capture, replay or repair experiment was used.

The original October29 date elapsed without formal attempts; the disclosed October30/31/November1 calendar amendment was authorized and committed before the first formal request. These results complete the amended calendar, not the original calendar.

## Primary result and drafting profitability

Let D_L = T(M_L)/T(C_L): values above1 favor enabling draft within the same scope. I = log(D_QB) - log(D_GS), so exp(I) = D_QB/D_GS. Each input log contrast has equal weight within session, each of two sessions equal weight within date, and each of three dates equal weight. Reported ratios are exponentiated mean log contrasts.

| Family | D_GS | D_PQ | D_QB | exp(I) | I (mean log) | Three date exp(I) points |
|---|---:|---:|---:|---:|---:|---|
| Qwen | 0.834652 | 1.121863 | 1.188438 | 1.423874 | 0.353381 | 1.360577, 1.454082, 1.459158 |
| SmolLM2 | 0.684205 | 0.805284 | 0.804877 | 1.176367 | 0.162431 | 1.126491, 1.199075, 1.205188 |

Both family interactions are positive on all three dates and all six session means. Qwen has D_QB>1 and D_GS<1 on every date: profitable QB drafting and a scope-dependent crossover coexist on this fixed panel. SmolLM2 has D_GS<1, D_PQ<1 and D_QB<1 on every date: the positive interaction reduces the drafting penalty but does not produce profitable drafting.

The audit reports matched observed logical work for Qwen. SmolLM2 does not have identical observed logical work across scopes; its estimates are complete-request joint path effects and do not support an execution-cost-only attribution. No operator-local or consumer-only causal effect is claimed.

## All date and session points

| Family | Shanghai date | D_GS | D_QB | exp(I) |
|---|---|---:|---:|---:|
| Qwen | 2026-10-30 | 0.829731 | 1.128913 | 1.360577 |
| Qwen | 2026-10-31 | 0.839248 | 1.220335 | 1.454082 |
| Qwen | 2026-11-01 | 0.835003 | 1.218402 | 1.459158 |
| SmolLM2 | 2026-10-30 | 0.676863 | 0.762481 | 1.126491 |
| SmolLM2 | 2026-10-31 | 0.691716 | 0.829419 | 1.199075 |
| SmolLM2 | 2026-11-01 | 0.684117 | 0.824490 | 1.205188 |

| Family | Date | Session | D_GS | D_QB | exp(I) | I sign |
|---|---|---:|---:|---:|---:|---|
| Qwen | 2026-10-30 | 0 | 0.830111 | 1.130326 | 1.361658 | positive |
| Qwen | 2026-10-30 | 1 | 0.829352 | 1.127501 | 1.359497 | positive |
| Qwen | 2026-10-31 | 0 | 0.866651 | 1.221022 | 1.408897 | positive |
| Qwen | 2026-10-31 | 1 | 0.812711 | 1.219649 | 1.500716 | positive |
| Qwen | 2026-11-01 | 0 | 0.827459 | 1.221824 | 1.476599 | positive |
| Qwen | 2026-11-01 | 1 | 0.842617 | 1.214989 | 1.441924 | positive |
| SmolLM2 | 2026-10-30 | 0 | 0.676932 | 0.762756 | 1.126783 | positive |
| SmolLM2 | 2026-10-30 | 1 | 0.676795 | 0.762206 | 1.126200 | positive |
| SmolLM2 | 2026-10-31 | 0 | 0.686908 | 0.817371 | 1.189927 | positive |
| SmolLM2 | 2026-10-31 | 1 | 0.696557 | 0.841644 | 1.208292 | positive |
| SmolLM2 | 2026-11-01 | 0 | 0.685719 | 0.817952 | 1.192839 | positive |
| SmolLM2 | 2026-11-01 | 1 | 0.682519 | 0.831080 | 1.217666 | positive |

All input/session effects, within-date session differences and adjacent-date changes remain in [ANALYSIS.json](ANALYSIS.json). Individual input/session reversals are not removed:
- Qwen: 67/72 positive, 5/72 negative, 0/72 zero. These72 cells are not independent date samples.
- SmolLM2: 45/72 positive, 27/72 negative, 0/72 zero. These72 cells are not independent date samples.

## Secondary ratios

For C_QB/C_PQ and M_QB/M_PQ, values below1 mean QB takes less time. R/C_L uses a separate strict-reference baseline and must not be interpreted as the marginal gain from drafting.

| Family | C_QB/C_PQ | M_QB/M_PQ | R/C_GS | R/C_PQ | R/C_QB |
|---|---:|---:|---:|---:|---:|
| Qwen | 0.954407 | 1.011045 | 0.812867 | 2.022730 | 2.119357 |
| SmolLM2 | 0.934678 | 0.934205 | 0.709091 | 1.346225 | 1.440309 |

Qwen M_QB/M_PQ changes direction across dates; the pooled value is not a same-direction claim. All secondary date points remain in the analysis artifact.

## Limited date sensitivity and scope

| Family | exp(I) date range | Registered97.5% paired-date sensitivity interval |
|---|---|---|
| Qwen | 1.360577–1.459158 | 1.236342–1.639850 |
| SmolLM2 | 1.126491–1.205188 | 1.028092–1.346028 |

These intervals use df2 and Bonferroni allocation for the two primary family contrasts, conditional on independent approximately normal date means. They are weak sensitivity summaries only. Three dates provide limited date-stability evidence, do not robustly estimate date-population variance and do not establish population power. Neither the1008 formal requests nor the sessions are treated as independent date samples; no request bootstrap is used.

This is transfer to two fixed, already exposed twelve-input panels on one RTX5070Ti Laptop host. Short inputs are mathematics and medium/long inputs are code, so domain and length cannot be separated. Cross-family reuse of tasks does not add independent tasks. The full GS/PQ/QB × draft interaction is now observed on these panels; the claim does not extend to arbitrary models, inputs or hardware.

The registered Llama diagnostic preserves its known failure and both controls. It identifies bundled recipe behavior, not a repair or the earliest internal operator divergence; the latter remains unresolved. Diagnostic clocks are excluded from this performance analysis.

## Evidence

[AUDIT.json](AUDIT.json) contains the full audit; [ANALYSIS.json](ANALYSIS.json) is the unchanged public analysis output; [DAY2_STATUS.json](DAY2_STATUS.json) records counts, process intervals, hashes and archival completion. The frozen scientific source binding remains c73051a1701b9f1ce4f8beee2700dd565fc96df4. Source, EXEs, core libraries, DLLs and calendar were not changed. Earlier924 request bytes and ten attempt receipts are retained.
