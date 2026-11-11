# B570 Diagnostic Extension

## Frozen prior result

The valid formal v2 gate remains **CORRECTNESS = FAIL** (9/18 exact pairs). This post-gate work is a **DIAGNOSTIC EXTENSION**, not a rescue or replacement validation. The fast Vulkan speculative path remains correctness-blocked.

## V2_raw

- context 512: `1.2426`
- context 2048: `1.6373`

These are raw PP2/PP1 target-forward mechanism ratios, not V2_exact and not end-to-end speedup. Per-operation microbenchmark energy is not reliable because each telemetry trace combines PP1 and PP2 work.

## Frozen HumanEval30 diagnostic

- exact prompts: 15/30
- mismatch prompts: 15/30
- exact pairs: 45/90
- mismatch pairs: 45/90
- stable divergence prompts: HumanEval/3, HumanEval/10, HumanEval/28, HumanEval/44, HumanEval/48, HumanEval/62, HumanEval/68, HumanEval/70, HumanEval/89, HumanEval/101, HumanEval/104, HumanEval/123, HumanEval/126, HumanEval/129, HumanEval/162

## Raw performance and board energy

The all-pair geometric-mean raw speedup is `0.5383x` (95% prompt-bootstrap CI `[0.5301585792983731, 0.5464679011613864]`). This is **DIAGNOSTIC / NOT CORRECTNESS-ADMISSIBLE AS A WHOLE**. The raw board-energy-efficiency ratio is `0.6961x`, at the Intel Arc B570 GPU board boundary only.

The exact-only geometric-mean speedup is `0.5475x` across 15 wholly exact prompts; its board-energy ratio is `0.7107x`. Both are **POST-HOC EXACT-SUBSET DESCRIPTIVE STATISTICS**, not unbiased primary estimates.

## Single predefined fallback

- candidate: serialized speculative `n_ubatch=1`
- correctness: `PASS`
- V2_exact 512 raw observation: `2.0352` — **INVALID / REMOTE-INTERFERENCE**
- V2_exact 2048 raw observation: `2.0177` — **NOT ADMISSIBLE / REMOTE STATE NOT PROVEN CLEAN**
- fallback HumanEval30: **NOT AUTHORIZED / NOT RUN**

The fallback correctness result (18/18 exact pairs) completed before the user reconnected and remains valid. During the subsequent fallback V2 measurement, a user status query established that ToDesk had reconnected while the 512 cell was still running. The 512 timing is therefore invalid. The session state was not independently proven clean before the immediately following 2048 cell, so it is conservatively excluded as well. Neither value is reported as admissible V2_exact, and no cell was rerun.

## Limitations

Mismatch timing and energy are descriptive only. GPU board energy is not whole-system or CPU package energy. Correlations are exploratory and do not establish causality. No backend, model, runtime, driver, k, p_min, prompt, or numerical-instrumentation search was performed. The two remote-contaminated fallback V2 observations are retained only as provenance and are excluded from admissible inference.
