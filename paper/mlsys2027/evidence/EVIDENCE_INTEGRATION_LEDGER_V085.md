# Evidence integration ledger — v0.8.5

Base: `98e8470f2559f78335de8d3473997d21b4bb55b8`. Canonical JSON and file SHA256 are authoritative. No new hardware/model execution.

## RTX_original_direct_ID

30 distinct prompts × 3 repeats. Reference/runtime: llama.cpp b10839; campaign-specific frontend/reference in protocol (RTX ctx4096 original CLI target-only UB1; B570 ctx1024 instrumented completion).

Primary: `"Direct-ID reference qualification"`. Secondary: `null`.

Allowed: Only this RTX serialized path qualifies in its own campaign. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Matched latency in these qualification-only runs.

Locations: Abstract, Introduction, Section 5.1, Figure 3B, Appendix I.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/rtx_direct_id_v2/protocol_v2.json` | `52ea5c6de24b4e3fcc85e9b4cd7e0b57cde1f100ac61864a402ef3403c354508` |
| `benchmarks/rtx_direct_id_v2/FORMAL_ANALYSIS.json` | `be1d64aa36cab1433d161ac88ae4b4c331178d2754261c1e696198610164ec67` |

## B570_original_direct_ID

30 distinct prompts × 3 repeats. Reference/runtime: llama.cpp b10839; campaign-specific frontend/reference in protocol (RTX ctx4096 original CLI target-only UB1; B570 ctx1024 instrumented completion).

Primary: `"Direct-ID reference qualification"`. Secondary: `null`.

Allowed: Both B570 paths remain blocked despite increased serialized agreement. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Matched latency in these qualification-only runs.

Locations: Abstract, Introduction, Section 5.1, Figure 3B, Appendix I.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/b570_direct_id_v1/protocol_v1.json` | `ca12dfddd10a1e3cfc9227aff93d0a2dc5bafe37cca5a2ba04af0327ce2b9a52` |
| `benchmarks/b570_direct_id_v1/FORMAL_ANALYSIS.json` | `fb9f211b00445b08ab534e7d9039bbd319e46ebe2d7bc5312d57864efd30568b` |

## B570_original_H1

24 distinct prompts × 3 repeats. Reference/runtime: llama.cpp b10839 Vulkan0; ctx1024; target-only UB128 reference; target-only UB1 predictor and native serialized live.

Primary: `"Frozen complete trajectory prediction"`. Secondary: `"4 reference-divergent prompts / 12 runs; all reserved arrays reach cap"`.

Allowed: Predictive target-only partition sufficiency on tested B570 path. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Live intervention from original prediction; B570 H1 directly transfers to RTX.

Locations: Abstract, Introduction, Figure 2, Section 5.2, Original appendix ledger.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/b570_mechanism_v08/VALIDATION_ANALYSIS.json` | `4e156eabb4ed8a04a3812b25958bdecc8485398fdf78669b166685219b2d161e` |
| `benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json` | `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826` |
| `benchmarks/b570_mechanism_v08/hypothesis_freeze.json` | `0fb6eba1fc57595dd9c4487c30ff8c5b9a0929a7714511a1278b01be4615aefe` |

## B570_live_intervention

24 distinct prompts × 3 repeats. Reference/runtime: b10839 Vulkan0; same-state native UB1 vs restored alternate UB128; batch512 ctx1024; alternate persists at UB128 after fork.

Primary: `{"score": {"executions": 72, "prompts": 24}, "raw_top1": {"executions": 0, "prompts": 0}, "immediate": {"executions": 0, "prompts": 0}, "continuation": {"executions": 18, "prompts": 6}, "paired_decision_events": 195}`. Secondary: `"Full continuation divergence: 18/72 executions, 6/24 prompts"`.

Allowed: Score and continuation effects on frozen sampled states/policy; No immediate decision effect detected at sampled first block starting with >=64 committed IDs. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; 195 independent samples; Whole-generation absence of partition effects; Single block restores reference.

Locations: Abstract, Contribution 2, Section 5.2, Appendix follow-ups.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/b570_partition_intervention_v1/ENDPOINT_ANALYSIS.json` | `0bbc42f7ba53e506dc69c6d05296a291068a0c98d18dbc55d003746cf9e656d7` |
| `benchmarks/b570_partition_intervention_v1/FORMAL_FREEZE.json` | `97ffc4f79c6a21885ffe8e715aa498907ba8db801b46c062573d8e466df96aa5` |
| `benchmarks/b570_partition_intervention_v1/INDEPENDENT_VALIDATION.json` | `b54f59f86146cc241b05d9e4709e85e557df06e60128209274a0cd2943bb95e8` |

## RTX_H1_failed_discovery

12 distinct prompts × 3 repeats. Reference/runtime: Original b10839 Windows26300 CUDA0 CLI; target-only UB2 predictor vs batched native live; ctx4096.

Primary: `"36/36 selection gate failed"`. Secondary: `"No selected hypothesis; H2 unavailable in that frozen arm"`.

Allowed: Lawful zero-reserved stop. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Successful target-only RTX predictor; V2 H2 backfilled into V1 tree.

Locations: Section 5.3, Limitations, Appendix.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/rtx_transfer_latency_v1/prediction/REPORT.json` | `bd2752ce1061b2fdc3d1c5be30b4586090816879cbf727dc27f851cea558f4e3` |
| `benchmarks/rtx_transfer_latency_v1/protocol.json` | `620656429a7735eb5fd12326cc54dbd492c3986696d00c4beb6b4b6f01c0d49a` |
| `benchmarks/rtx_transfer_latency_v1/runtime_freeze.json` | `ddee7133bf2dfe86c45b3747ec9bb395f579a1dc733289b6d5a8c97290b0bcf3` |

## RTX_H2_V2

24 distinct prompts × 3 repeats. Reference/runtime: b10839 original shared llama.cpp/GGML/CUDA DLLs; Windows26300; ctx4096 batch2048 target/draft UB2; reference target-only UB1.

Primary: `"Prospective H2/live equality; 72/72"`. Secondary: `"Reference qualification remains 60/72; four divergent prompts; endpoint distribution in projection"`.

Allowed: Independent application/process/API orchestration and target-only sequential sealed-tape replay reproduce tested live trajectories. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Independently implemented numerical runtime; Draft-free prediction construction; OS-wide adversarial isolation; Qualified batched performance.

Locations: Abstract, Contribution 2, Section 5.3, Related Work, Conclusion, Appendix.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/rtx_independent_proposal_replay_v2/FORMAL_REPORT.json` | `42ba71b0f149a386bffd11890e8c901bf988a9aed102e84d544e5d3c122b85a3` |
| `benchmarks/rtx_independent_proposal_replay_v2/RESERVED_PREDICTIONS.json` | `7a97193342b2dfa744de607d2d5720c60c10ca8013fc4c64ec48a970a47e5b09` |
| `benchmarks/rtx_independent_proposal_replay_v2/EFFECTIVE_CONFIGURATION.json` | `5200e4e50f7cc64b78b04dfb9da5c909dd46ab8d9c1598333f316164f5292273` |
| `benchmarks/rtx_independent_proposal_replay_v2/EXPOSURE_AUDIT.json` | `241dc13443571f08829528054c6f5502306b9bf599c7f319b9e206a534dcd967` |
| `benchmarks/rtx_independent_proposal_replay_v2/F0_REMOTE_RECEIPT.json` | `9922c0f85fbff55209277ef9c0376f6ad6c73a1a41aba7ea7b7ee6bd4b6a4bd7` |
| `benchmarks/rtx_independent_proposal_replay_v2/F1_REMOTE_RECEIPT.json` | `260d25fff4b0387ef48eb1371c43b5404f2cb3e1224fb9c6d3d21f8e8d6f33c4` |
| `benchmarks/rtx_independent_proposal_replay_v2/F2_REMOTE_RECEIPT.json` | `f67c2420e92e8b55753d37da05829e658971d064033e44e1bb034d4fceba1cc9` |

## RTX_matched_serialized_latency

30 distinct prompts × 3 repeats. Reference/runtime: New Clang21.1 timer frontend/core with original hashed CUDA DLLs; Windows26300; ctx4096 target/draft initial prefill synchronized; both conditions same instrumented build.

Primary: `{"target_over_serialized": 0.6458157742698286, "ci95": [0.629802205379344, 0.6598843928244866], "faster_prompts": 0}`. Secondary: `"Empty-hook qualification does not bound all debug logging overhead"`.

Allowed: Freshly qualified serialized path is slower in its own instrumented timer boundary. Excluded: Unique numerical operation/kernel; Universal backend or model rule; HumanEval functional pass@k; Historical timing retroactively qualified; Historical 0.650 replacement; Full batched-to-serialized speed tradeoff; Uninstrumented deployment/whole-request latency; H2 reserved count pooled with latency.

Locations: Abstract, Contribution 1, Table 2 new block, Section 5.4, Limitations, Conclusion, Appendix.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/rtx_transfer_latency_v1/latency/REPORT.json` | `b94eaeb3eb7ccc8d723b2e8a8e4c1ff4ac4944ad3a2b02f4137d92356efdff96` |
| `benchmarks/rtx_transfer_latency_v1/latency/PROMPT_MEDIANS.csv` | `491f01e65794a075dd14822ee4beceaaa291bf4ced03602db5e5ab7f5c0909f0` |
| `benchmarks/rtx_transfer_latency_v1/protocol.json` | `620656429a7735eb5fd12326cc54dbd492c3986696d00c4beb6b4b6f01c0d49a` |
| `benchmarks/rtx_transfer_latency_v1/timer_build_manifest.json` | `cfe0663067d3e657aa83d3c279b96eb729098bc56dd6d1209d13cfe639a27578` |
| `benchmarks/rtx_transfer_latency_v1/environment.json` | `46769ea02eb1541ed4fff84b452ebfd69afe1265872ef1453c50ef64388b547e` |

## M4_runtime

60 distinct prompts × 3 repeats. Reference/runtime: llama.cpp Metal; Qwen3-8B/0.6B Q8_0; same frozen held-out target-only baseline; offline oracle=min(target,Always).

Primary: `"Guard target-relative speedup 1.3114; Always 1.3469"`. Secondary: `{"Guard_over_Always": 1.0270760219826773, "Guard_over_Always_CI": [1.0129560055428655, 1.0435592653980876], "distinct_oracle_regret": "Guard/oracle 1.0278 [1.0137,1.0446]"}`.

Allowed: Direct-ID qualified runtime test; Guard slower than fixed Always in post-study paired secondary. Excluded: Incremental control gain; Oracle deployability; Runtime energy benefit.

Locations: Abstract, Contribution 3, Section 7, Table 3, Limitations, Conclusion, Appendix.

| Canonical file | SHA256 |
|---|---|
| `benchmarks/m4_runtime/FORMAL_ANALYSIS.json` | `ad5dc5073a1784d20117518776cd61d1ab9bc9049405cbaac88167ab540390cd` |
| `benchmarks/m4_runtime/GUARD_ALWAYS_SECONDARY_ANALYSIS.json` | `6973e608f4f22f8f1a7c7a942bb78d9199291933f0c9b2473b6cdf73f31c1977` |
| `benchmarks/m4_runtime/CALIBRATION_FREEZE.json` | `3c179a35f046b57edb4ddc8772a1aba609b496878efc2b7849a66947c8b7830b` |

## 358H_Phase3

30 distinct prompts × 3 repeats. Reference/runtime: b10839 Vulkan0 target Q8_0; symmetric INT4 OpenVINO CPU/NPU draft; matched integrated post-prefill baseline.

Primary: `"Qualified CPU/NPU slower; direct C and complete measured regions"`. Secondary: `"Later intervention blocked at qualification, no formal runtime performance"`.

Allowed: Combined reconstruction/replay plus proposal cost; no separable replay-only estimate. Excluded: Persistence savings; Runtime performance or energy; Compact diagnostic called raw replay.

Locations: Contribution 3, Table 2, Section 5.5, Section 7, Conclusion, Appendix.

| Canonical file | SHA256 |
|---|---|
| `analysis/358h_phase3_summary.json` | `90f4a0725ffc8999d46e3f93dd446b5eb4dc9c5700fd09e3ace6118aa71d640e` |
| `analysis/358h_phase3_prompt_summary.csv` | `76da1526daeb0a593904692c1eca9a2b9cfe7af84c5ebb8ca74aeb96eca523fc` |
| `paper/mlsys2027/evidence/RUNTIME_358H_PIN_V04.json` | `d31130c0288aee45beebcad86bb4ff84a1f9e70c829fe055e48bec204313a183` |

The JSON retains exact task sets, execution/comparison denominators, estimator/CI and freeze order. Old scientific ledgers and artifacts remain unchanged. The two M4 ratios near 1.027 have different comparators.
