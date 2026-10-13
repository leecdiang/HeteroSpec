# Claim–Evidence Matrix — v0.15.0

This is the author-side claim map for the reconstruction, not a new GPU replication or independent peer-review vote. Source IDs resolve in `provenance/SOURCE_MANIFEST.json`.

| ID | Claim | Destination | Source | Evidence level | Required boundary |
|---|---|---|---|---|---|
| C01 | Attention query organization can be decoupled from target-wide batching | Main §3, Fig1 | rtx98_method | Source-described implementation | Not all surrounding operators are numerically invariant on every backend. |
| C02 | Query/mask view preserves mathematical scalar indexing under stated preconditions | Main §3.2, Proposition1 | rtx98_method + explicit derivation | Mathematical conditional proof | Not a floating-point reduction-order or full-model theorem. |
| C03 | Phase scope acts on capture-off execution; layout flag protects graph reuse | Main §3.4, Table1 | rtx98_method | Source-bound obligations | No dynamic automatic minimal-constraint selector. |
| C04 | Mask3 is inclusion-minimal in the historical four-bit/four-probe experiment | Main §3.5; SupplementS2.3 | legacy_ledger E20 | Finite factorial | Not cross-family global minimality. |
| C05 | PQ and QB match bitwise at QK,softmax,AV in24 captured contexts | Main §5.1, Fig2 | rtx98_results | Fixed-input operator observation | Layer0 sampled contexts,not24 independent shapes;kernel schedule unknown. |
| C06 | R=M3=C3 complete endpoints across240 repetitions/family in three-family confirmation | Main §5.2, Table3; SupplementS3 | rtx91_results | Finite full native output qualification | Not all-input or stochastic-distribution guarantee. |
| C07 | M0 and some production baselines fail reference output | Main §5.2; SupplementS3 | rtx91_results | Explicit negative baseline tests | Failed comparisons cannot be promoted to lossless speedups. |
| C08 | All seven arms qualify96 outputs each/family in2016-request repair comparison | Main §5; SupplementS4 | rtx98_results | Finite exposed-panel qualification | Not a new blind transfer cohort. |
| C09 | QB has lower aggregate request cost than PQ and GS in the reported campaign | Main §5.3, Table4, Fig3 | rtx98_results + rtx98_results_json | Qualified same-reference request ratios | Some task regressions; target-only Qwen3/Llama session reversals; small PQ effects; no date-level uncertainty or SOTA superiority. |
| C10 | Incremental speculation is positive for Qwen/Llama but negative for SmolLM2 | Main §5.4; SupplementS4 | rtx98_results + rtx91_results | Measured net request comparison | Do not infer component costs or pool panel/version results. |
| C11 | External fixed-context prefill partition reproduces selected historical B570 output boundaries | Main §6.1; SupplementS5.1 | b57099_results | Controlled exposed intervention | Includes inherent per-caller scheduling;not unique shader cause. |
| C12 | Fourth arm and partition sweep show multiple endpoint classes | Main §6.2, Fig4; SupplementS5.2 | b570101_results | Supplementary diagnostic observations | P1A/B driver-body freeze gap;not fully compliant confirmation or universal128 threshold. |
| C13 | B570 projection frontier differs before attention;32/40 operator calls qualify | Main §6.3; SupplementS5.3 | b570101_results | Native alignment + qualified fixed-input replay | All8 scale/MUL failures excluded;no exact shader identity or unique K root cause. |
| C14 | Validated boundary0 KV source changes affected suffix under common receiver | Main §6.4, Fig5; SupplementS5.4 | b570101_results | 16 shams then40 crosses | Necessary-state reconstruction,not arbitrary opaque clone;initial-logit swap a negative control. |
| C15 | Same-output B570 production-path costs remain negative with width1 verification | Main §6.5; SupplementS5.5 | b57092_cost + b57093_audit + b57097_work | Inherited paired output/cost and separate work witness | Original stock gate remains failed/null;no new timeline or residency certificate. |
| C16 | All28 old experiment groups keep an explicit destination | SupplementS6/S8 and data/historical_disposition.csv | legacy_ledger | Editorial provenance/disposition | Original raw data are not all recopied into the present ZIP or re-audited here. |

Finalization review: all 21 aggregate ratios and 42 session ratios were recomputed from the pinned PR98 report's task/session median times. The selected report fields are preserved in `data/rtx_repair_report_extract.json`; this remains a report-level check, not a fresh raw/native archive audit. The six PQ/QB session pairs are also provided in `data/rtx_repair_sessions.csv` and Supplement S4.
