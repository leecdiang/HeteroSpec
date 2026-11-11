# Independent post-study diagnostic notes

Calculated 2026-10-03 from retained observation rows in `derived/inputs.json` inside the original scientific ZIP, `evidence/B570_original_H1.json`, and `evidence/RTX_V4.json` exported by the byte-identical scientific ZIP. No author verifier, model, GPU, capsule download, or manuscript modification was used. `acceptance_diagnostic.py` is independent arithmetic and writes `acceptance_diagnostic.json`; input SHA-256 digests are recorded there. Existing aggregate outcomes were known before these choices. These are post-study descriptive calculations, with original denominators fixed.

## 358H: a ceiling for the original prompt estimator

For original prompt i and repetition j, write B_ij for matched baseline time, T_ij for complete target work (`verification_ms`), and D_ij+X_ij for nonnegative draft/residual time. If a counterfactual removes draft and residual but holds each run's measured baseline, target work, progress and boundary fixed, its speedup is at most u_ij=B_ij/T_ij. For any other nonnegative remaining cost, s'_ij <= u_ij. Monotonicity of median and log/GM therefore gives

`GM_i median_j(s'_ij) <= GM_i median_j(B_ij/T_ij)`.

This matches the original median-of-three-paired-ratios prompt estimator. It is different from the paper's already-correct total-time ceiling `sum(B)/sum(T)`. Both paths retain exactly 90 rows = 30 original prompts x 3 repetitions; no exclusions. Assertions check positive baseline/target time, nonnegative measured draft/residual, component-sum agreement within 0.01 ms, and that each recorded speedup is below its derived ceiling.

| Path | Original prompt GM recomputed | Existing total-time ceiling recomputed | New prompt-GM ceiling | Prompt medians >=1 | Maximum prompt ceiling |
|---|---:|---:|---:|---:|---:|
| CPU | 0.733914586 | 0.827452983 | 0.837219209 | 0/30 | 0.973619676 |
| NPU | 0.351663239 | 0.835185852 | 0.844840109 | 0/30 | 0.999908957 |

The upper bound excludes parity for this original prompt estimator as well as for the pooled-total estimator, under the explicitly fixed premises. It is conditional arithmetic, not an optimization measurement, population statement, persistence forecast, confidence interval or claim of robust per-prompt margins. One NPU *individual repetition* has a bound above one (1.000163695); thus no assertion that all 90 NPU repetitions are individually below parity is justified. NPU HumanEval/64 is only about 0.0091% below one at its prompt median, so measurement/session uncertainty matters for an individual-prompt interpretation. No new CI is computed.

## B570: how much non-reference output was actually predicted

All 72 predictor/live arrays agree and reach 128 IDs. There are 24 distinct prompts, repeated three times. For the four reference-divergent prompts, every position from first divergence through cap differs from reference: /134 has 40 such positions, /42 55, /145 25, /138 35. Across the four distinct trajectories this is 155 predicted non-reference positions, 151 strictly later than the first differing ID. Do not treat positions or 12 repeated executions as independent samples. This describes capped forecasts and does not establish unbounded completion or a numerical cause.

## RTX: equal aggregate totals conceal more than membership

Independent array comparisons reproduce reference/live=51/57, target-only UB2/live=51/57, H2/live=57/57, R_ONLY/live=57/57. The same-set distinguishing cases are:

| Task | Reference / UB2 / live lengths | Reference match | UB2 match | Detail |
|---|---|---|---|---|
| /25 | 75 / 75 / 75 | Yes | No | UB2 differs at exactly one aligned ID, then reconverges. |
| /15 | 28 / 28 / 25 | No | No | Both target-only arrays are identical; 10 mismatches on the common 25-ID extent and 3 extra terminal-side IDs. |
| /18 | 72 / 69 / 69 | No | Yes | Reference has 40 mismatches on the common 69-ID extent and 3 extra IDs. |

A retrospective oracle picking between the two *already measured full target-only arrays* would match 18/19 prompts, still failing /15. It is neither a deployable predictor nor a rejection of arbitrary target-only programs, within-generation shape policies, or hypothetical trace-matched candidates. This sharpens the finite candidate comparison without proving history necessary.

## Other independent agreement checks

From native QPC fields, qualified RTX serialization matches 57/57, batching matches 51/57, and paired prompt-median speedup GM is 0.6773510334393157 with 0/19 serialized-faster prompts. From all 540 M4 retained times, Guard/Always GM is 1.0270760219826773, Always/two-fixed-mode-oracle GM is 1.0006919671212657, and target is faster than Always on 2/60 prompts. These reproduce the paper's point claims. No bootstrap was rerun, and no logging-free timing inference follows.

## Canonical-source cross-check

The pinned `analysis/358h_phase3_prompt_summary.csv` was supplied locally as `358h_phase3_prompt_summary.csv` and is read at its original repository path by the portable delivered scripts. Its 37,068 bytes have SHA-256 `76da1526daeb0a593904692c1eca9a2b9cfe7af84c5ebb8ca74aeb96eca523fc` and the parent reports pinned Git blob `9f34287b11841fdff0af155b16f6e79d0ead8c25` at delivery HEAD. A direct CSV-key join over `(task_id,repetition,condition)` found exactly 180 unique rows; every exported field of every selected row is string-identical to this canonical processed source. The ceiling calculation therefore does not rely solely on an untraced derived summary. Original raw runtime traces are still not claimed available.
