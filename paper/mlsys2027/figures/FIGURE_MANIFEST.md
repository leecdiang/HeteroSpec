# MLSys 2027 candidate figure manifest

**Status: PUBLICATION-CANDIDATE.** Four selected main figures plus appendix candidate A1 (legacy asset Figure 5). Actual OLD/NEW comparison completed; manuscript prose and float integration intentionally remain unchanged.

Scientific source commit: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`. Branch: `paper/mlsys2027-figures-v0.3`. This base includes manuscript v0.1 and the independently audited v0.2 candidates.

Figure IDs follow the actual manuscript roles (F2 paths; F3 M4), not the numeric prefixes of its TeX filenames. All 40 sources are pinned to current main in `data/source_lock.json`. Closed scientific inputs are unchanged from v0.2; only WRITING_STATUS.md changed. Comparison provenance is in `comparison/comparison_lock.json`.

Skills discovered and read in this environment: visualize-data (primary plotting discipline), validate-data (independent per-figure pass), analyze-data-quality (input audit), jupyter-notebooks (audit companion), and PDF (export/render QA). No System Design skill was available. Scientific authority remains the repository.

Common extraction: `scripts/extract.py`. Common vector renderer: `scripts/plot.py` (`figure1`–`figure5`). Independent numerical pass: `scripts/validate.py --figure N --require-outputs`. Native-size rendering: `scripts/render_qa.py`.

Typography: embedded STIXGeneral/STIX; white background; no gradients/shadows/vendor colors. PNG files are preview-only. PDF/SVG are authoritative.

## Figure 1 — main
 
**Selection:** REDESIGN BOTH. See actual OLD/NEW comparison in `FIGURE_REVIEW.md`.

**Question:** Do favorable local measurements reliably indicate realized gain in the tested cases?

**Manuscript claim:** Favorable target batching and isolated drafting coexist with profitable, exact-negative and correctness-blocked outcomes.

**Evidence class:** PRIMARY outcomes; MECHANISM_SUPPORTED / diagnostic local signals. Heterogeneous measurements are not placed on one numerical axis.

**Correctness:** M4 HumanEval 90/90 and 24Q 72/72 exact; RTX batched gate fails; 358H NPU 90/90 exact.

**Estimator / CI:** Categorical overview. Micro ranges are ratio-of-medians ranges across contexts, not CIs. Isolated values are median tok/s at 8192 tokens. Outcome speedups are campaign prompt GMs; uncertainty and full estimators are in Figures 3/4.

**Caveats:** M4 local proxy is shared-path evidence from a separate micro study, not workload-specific measurement. Opposite regimes do not isolate workload-only causality. The 8192-token example is contextualized by all three contexts in Figure 4. Post-prefill speedups are not whole-request latency. No universal theory or hardware leaderboard.

**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure1`. Numerical pass: `qa/figure1_validation.json`.

**Insertion test:** 6.75 × 3.63 in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.

### Source files

- [`work/m4/llama_verify_q8_synced.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/work/m4/llama_verify_q8_synced.csv)
- [`analysis/m4_confirmatory_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_confirmatory_prompt_summary.csv)
- [`analysis/m4_humaneval_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_humaneval_prompt_summary.csv)
- [`analysis/m4_confirmatory_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_confirmatory_summary.json)
- [`analysis/m4_humaneval_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_humaneval_summary.json)
- [`artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json)
- [`reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md)
- [`analysis/358h_draft_device_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_draft_device_summary.csv)
- [`analysis/358h_phase3_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_prompt_summary.csv)
- [`analysis/358h_phase3_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_summary.json)

### Plotted values

Full precision and references: [`data/figure1_overview.csv`](data/figure1_overview.csv).

| case | local_low | local_high | local_unit | speedup | ci_low | ci_high | exact | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Preregistered HumanEval30 | 1.02218185 | 1.07612561 | baseline target-decode steps | 1.38735234 | 1.35057448 | 1.42162539 | 90/90 | qualified |
| Representative 24Q | 1.02218185 | 1.07612561 | baseline target-decode steps | 0.841965102 | 0.808693455 | 0.876765035 | 72/72 | qualified |
| RTX batched | 0.983147983 | 1.00903043 | baseline target-decode steps | not_admissible | not_applicable | not_applicable | gate failed | blocked |
| 358H NPU | 30.8070621 | 48.0830269 | tokens/s (CPU, NPU) | 0.351663239 | 0.332594836 | 0.36894873 | 90/90 | qualified |

### Final outputs and SHA256

- [pdf/figure1.pdf](pdf/figure1.pdf): `42be723f84994697a8456c3706bff3db7e29a631ef7e3794999357c313ac9b17`
- [svg/figure1.svg](svg/figure1.svg): `9b66b7c5302bdd255a1c64b172ccd23e4240a8d246ac7c1c3e579bc53447a439`

## Figure 2 — main
 
**Selection:** TAKE NEW. See actual OLD/NEW comparison in `FIGURE_REVIEW.md`.

**Question:** Does the physically cheapest target-forward path remain usable after correctness qualification?

**Manuscript claim:** Cheap physical target batching may be blocked; serialization alone does not imply exactness.

**Evidence class:** MECHANISM_SUPPORTED for qualified M4/RTX serialized; DIAGNOSTIC for RTX batched and both B570 timing paths.

**Correctness:** M4 tested cells exact; RTX batched blocked; RTX serialized exact secondary control; B570 fast 45/90 and serialized 60/90, both globally inadmissible.

**Estimator / CI:** Ratio of median PP2 to median PP1 (7 M4 or 20 RTX/B570 repetitions per cell). Range endpoints span tested contexts; no CI is drawn.

**Caveats:** Contexts/stacks are not fully matched. V2_micro is not complete R_target or speedup. Formal B570 V2 was NOT RUN; contaminated earlier serialized values are excluded.

**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure2`. Numerical pass: `qa/figure2_validation.json`.

**Insertion test:** 6.75 × 3.58 in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.

### Source files

- [`work/m4/llama_verify_q8_synced.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/work/m4/llama_verify_q8_synced.csv)
- [`artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/artifacts/windows_verification_mechanism/windows-exact-verification-microbench.json)
- [`reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/WINDOWS_EXACT_VERIFICATION_COST.csv)
- [`reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md)
- [`artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/v2_raw.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/v2_raw.json)
- [`artifacts/b570_backend_control/exact-fallback-v1-20260912-222617/exact_fallback/processed/v2_exact.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/artifacts/b570_backend_control/exact-fallback-v1-20260912-222617/exact_fallback/processed/v2_exact.json)
- [`analysis/b570_exact_fallback_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/b570_exact_fallback_summary.json)
- [`reports/b570/B570_VERIFICATION_MECHANISM.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/b570/B570_VERIFICATION_MECHANISM.md)

### Plotted values

Full precision and references: [`data/figure2_micro_cells.csv`](data/figure2_micro_cells.csv).

| path | context | pp1_ms | pp2_ms | v2_micro | repetitions | status |
| --- | --- | --- | --- | --- | --- | --- |
| M4 Metal | 512 | 100.872584 | 103.110125 | 1.02218185 | 7 | qualified |
| M4 Metal | 2048 | 99.968 | 107.578125 | 1.07612561 | 7 | qualified |
| M4 Metal | 8192 | 115.490333 | 119.216458 | 1.03226352 | 7 | qualified |
| RTX batched | 0 | 14.25735 | 14.3861 | 1.00903043 | 20 | blocked |
| RTX batched | 256 | 21.4099 | 21.0491 | 0.983147983 | 20 | blocked |
| RTX serialized | 0 | 14.2897 | 34.7382 | 2.43099575 | 20 | qualified |
| RTX serialized | 256 | 21.41575 | 45.7657 | 2.13701131 | 20 | qualified |
| B570 fast | 512 | 27.8399 | 34.5932 | 1.2425763 | 20 | diagnostic |
| B570 fast | 2048 | 28.1841 | 46.1457 | 1.6372955 | 20 | diagnostic |
| B570 serialized | 512 | 27.6536 | 54.8279 | 1.98266772 | 20 | diagnostic |
| B570 serialized | 2048 | 81.5255 | 162.3749 | 1.99170689 | 20 | diagnostic |

### Final outputs and SHA256

- [pdf/figure2.pdf](pdf/figure2.pdf): `c62e822b347929109e1258c023f7b330a239f93094afc32e4d911bd1d42bf500`
- [svg/figure2.svg](svg/figure2.svg): `16f3ed7ecfe734d2bc7078ce38038569f6e2f9c333f57571bb3c61e0e1a05f80`

## Figure 3 — main
 
**Selection:** HYBRID. See actual OLD/NEW comparison in `FIGURE_REVIEW.md`.

**Question:** Can the same tested M4 platform/runtime exhibit opposite profitability regimes?

**Manuscript claim:** The same tested Metal stack exhibits opposite regimes in two separate frozen studies; this is an observation, not a workload-only causal effect.

**Evidence class:** PRIMARY (both workloads)

**Correctness:** 24Q 72/72; HumanEval fixed-k2 90/90 exact token-ID pairs.

**Estimator / CI:** Across-prompt GM of within-prompt GMs of 3 paired ratios. 95% prompt bootstrap: 24Q Python RNG seed 20260907, 10,000 draws, sorted indices 249/9749; HumanEval seed 20260910, 100,000 draws, indices 2500/97499. Original input order preserved.

**Caveats:** Not statistically paired between workloads. CIs condition on campaign and omit full session/thermal uncertainty. Exactness is not functional pass@k. No unified-memory causal claim.

**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure3`. Numerical pass: `qa/figure3_validation.json`.

**Insertion test:** 3.25 × 2.40 in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.

### Source files

- [`analysis/m4_confirmatory_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_confirmatory_prompt_summary.csv)
- [`analysis/m4_confirmatory_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_confirmatory_summary.json)
- [`analysis/m4_humaneval_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_humaneval_prompt_summary.csv)
- [`analysis/m4_humaneval_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_humaneval_summary.json)
- [`scripts/summarize_m4_confirmatory.py`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/scripts/summarize_m4_confirmatory.py)
- [`scripts/summarize_m4_humaneval.py`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/scripts/summarize_m4_humaneval.py)
- [`benchmarks/m4_code_conditioned_30q/preregistration.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/benchmarks/m4_code_conditioned_30q/preregistration.json)

### Plotted values

Full precision and references: [`data/figure3_workloads.csv`](data/figure3_workloads.csv).

| workload | speedup | ci_low | ci_high | prompts | pairs | exact_pairs |
| --- | --- | --- | --- | --- | --- | --- |
| Representative 24Q | 0.841965102 | 0.808693455 | 0.876765035 | 24 | 72 | 72 |
| Preregistered HumanEval30 | 1.38735234 | 1.35057448 | 1.42162539 | 30 | 90 | 90 |

### Final outputs and SHA256

- [pdf/figure3.pdf](pdf/figure3.pdf): `f520c3edc6c285a16bfe90d0c0d9444bcd88bde9f6049efff33f696cda7ed940`
- [svg/figure3.svg](svg/figure3.svg): `78f78e74656684506cfa78093248d672ee5ec365beb258065b1454065a4ce7d0`

## Figure 4 — main
 
**Selection:** TAKE NEW. See actual OLD/NEW comparison in `FIGURE_REVIEW.md`.

**Question:** Why can isolated NPU drafting look favorable while the qualified realized path is much slower?

**Manuscript claim:** The measured OpenVINO state interface incurs large replay-plus-proposal cost; CPU remains target-side dominated.

**Evidence class:** PRIMARY Phase-3 outcome + MECHANISM_SUPPORTED decomposition; formal Phase-1 isolated characterization.

**Correctness:** CPU and NPU each 90/90 exact in Phase 3. Phase-1 throughput is a separate measurement boundary.

**Estimator / CI:** A: isolated median steady-state tok/s, n=5, 95% bootstrap CI (10,000 NumPy draws; seed 20260921+context). B: arithmetic mean seconds/request, 90 rows/device; shares are ratio of total component time to total speculative time. Headline speedup: GM of 30 within-prompt median paired ratios, 10,000 NumPy prompt-bootstrap draws, seed 20260919.

**Caveats:** Post-prefill decode, not whole-request latency. Replay/proposal inseparable. Absolute bars preserve total-duration difference. Aggregate ratios differ from prompt-GM speedups. Phase-1 medians/CIs checked against summaries and retained TPOT vectors; separately tracked raw throughput arrays unavailable. No energy or persistent-state intervention claim.

**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure4`. Numerical pass: `qa/figure4_validation.json`.

**Insertion test:** 6.75 × 3.75 in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.

### Source files

- [`analysis/358h_draft_device_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_draft_device_summary.csv)
- [`analysis/358h_draft_device_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_draft_device_summary.json)
- [`analysis/358h_threshold_input_cpu.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_threshold_input_cpu.json)
- [`analysis/358h_threshold_input_npu.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_threshold_input_npu.json)
- [`analysis/358h_phase3_prompt_summary.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_prompt_summary.csv)
- [`analysis/358h_phase3_decomposition.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_decomposition.csv)
- [`analysis/358h_phase3_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_summary.json)
- [`scripts/platform/358h/process_phase1_phase2_results.py`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/scripts/platform/358h/process_phase1_phase2_results.py)
- [`scripts/platform/358h/analyze_phase3_campaign.py`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/scripts/platform/358h/analyze_phase3_campaign.py)
- [`scripts/platform/358h/phase3_heterogeneous_runner.py`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/scripts/platform/358h/phase3_heterogeneous_runner.py)
- [`reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/358h/358H_PHASE3_END_TO_END_VALIDATION.md)

### Plotted values

Full precision and references: [`data/figure4_isolated.csv`](data/figure4_isolated.csv).

| device | context | tokens_s | ci_low | ci_high |
| --- | --- | --- | --- | --- |
| CPU | 512 | 89.8678818 | 88.3267059 | 90.3137283 |
| CPU | 2048 | 64.8491058 | 64.1509399 | 65.7633133 |
| CPU | 8192 | 30.8070621 | 30.3430347 | 31.3615818 |
| NPU | 512 | 91.036232 | 90.7696304 | 91.4895782 |
| NPU | 2048 | 74.9264526 | 72.4079056 | 75.923584 |
| NPU | 8192 | 48.0830269 | 47.1034164 | 48.40382 |

Full precision and references: [`data/figure4_realized.csv`](data/figure4_realized.csv).

| device | total_s | draft_s | target_s | residual_s | draft_pct | target_pct | residual_pct | headline_speedup | aggregate_speedup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CPU | 13.2531257 | 1.67350703 | 11.574811 | 0.00480765222 | 12.627263 | 87.3364614 | 0.0362756102 | 0.733914586 | 0.722668156 |
| NPU | 27.5437801 | 16.0710817 | 11.4676415 | 0.00505698778 | 58.3474076 | 41.6342325 | 0.0183598176 | 0.351663239 | 0.34772322 |

### Final outputs and SHA256

- [pdf/figure4.pdf](pdf/figure4.pdf): `c9332f4b43e79ea545ffbb04e05661c369d7a846dbc52d869eb4df0735a26b4b`
- [svg/figure4.svg](svg/figure4.svg): `bfb29bd0177adc451cf17dd911b972916d3ffe00e3bea2f37ca7778869fcefcc`

## Figure 5 — appendix A1
 
**Selection:** TAKE NEW. See actual OLD/NEW comparison in `FIGURE_REVIEW.md`.

**Question:** Which correctness/profitability regimes are supported by the tested cases?

**Manuscript claim:** Observed regimes differ by path, workload and realized interface, rather than defining a hardware ranking.

**Evidence class:** Mixed, explicitly labeled P/S/M/D; 358H outcome/mechanism labels are P/M.

**Correctness:** Five qualified case groups; three blocked groups. RTX serialized group includes two separately exact controls. Neither B570 group is qualified.

**Estimator / CI:** Categorical classification; no numerical coordinates or CI. 358H percentages use the same total-time denominator as Figure 4.

**Caveats:** Blocked paths have no admissible profitability estimate. Blank cells mean no case shown. Cross-platform hardware/software/workloads co-vary. Mechanism rows are not an exhaustive taxonomy or continuous measure.

**Extraction / rendering:** `scripts/extract.py`; `scripts/plot.py:figure5`. Numerical pass: `qa/figure5_validation.json`.

**Insertion test:** 6.75 × 4.10 in. Color and grayscale PASS; see `qa/VISUAL_QA.md`.

### Source files

- [`paper/notes/CROSS_PLATFORM_MECHANISM.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/paper/notes/CROSS_PLATFORM_MECHANISM.md)
- [`paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md)
- [`analysis/m4_confirmatory_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_confirmatory_summary.json)
- [`analysis/m4_humaneval_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/m4_humaneval_summary.json)
- [`reports/5070ti/windows_humaneval_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/windows_humaneval_summary.json)
- [`reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/HUMANEVAL_LLAMA_REPLICATION.csv)
- [`reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md)
- [`artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/artifacts/b570_backend_control/diagnostic-v1-20260912-170834/raw/diagnostic_summary.json)
- [`analysis/b570_exact_fallback_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/b570_exact_fallback_summary.json)
- [`analysis/358h_phase3_summary.json`](https://github.com/leecdiang/HeteroSpec/blob/1a11361f8526ec361e20dd6878d6e67352fb7bbd/analysis/358h_phase3_summary.json)

### Plotted values

Full precision and references: [`data/figure5_regimes.csv`](data/figure5_regimes.csv).

| case | mechanism | admissibility | profitability | exact | evidence_class |
| --- | --- | --- | --- | --- | --- |
| M4 representative 24Q | Workload-conditioned | qualified | negative | 72/72 | PRIMARY |
| M4 HumanEval30 | Workload-conditioned | qualified | profitable | 90/90 | PRIMARY |
| RTX batched | Verification-constrained | blocked | not_admissible | frozen gate FAIL | MECHANISM_SUPPORTED |
| RTX serialized controls | Verification-constrained | qualified | negative | 90/90 each | SECONDARY |
| B570 fast | Correctness-blocked | blocked | not_admissible | 45/90 | DIAGNOSTIC |
| B570 serialized | Correctness-blocked | blocked | not_admissible | 60/90 | DIAGNOSTIC |
| 358H CPU | Target-side dominated | qualified | negative | 90/90 | PRIMARY |
| 358H NPU | State-interface bound | qualified | negative | 90/90 | PRIMARY |

Full precision and references: [`data/figure4_realized.csv`](data/figure4_realized.csv).

| device | total_s | draft_s | target_s | residual_s | draft_pct | target_pct | residual_pct | headline_speedup | aggregate_speedup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CPU | 13.2531257 | 1.67350703 | 11.574811 | 0.00480765222 | 12.627263 | 87.3364614 | 0.0362756102 | 0.733914586 | 0.722668156 |
| NPU | 27.5437801 | 16.0710817 | 11.4676415 | 0.00505698778 | 58.3474076 | 41.6342325 | 0.0183598176 | 0.351663239 | 0.34772322 |

### Final outputs and SHA256

- [pdf/figure5.pdf](pdf/figure5.pdf): `eecacdd535731d3673eff9b45c523a34beb97c85ef6b74a5c1bf3d3a5996c84a`
- [svg/figure5.svg](svg/figure5.svg): `2009a7912ba57506cb56a0d8f469dc57f7ee309ea2ae281d15f228afb751ed8a`

