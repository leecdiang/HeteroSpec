# M4 Guard Interpretation Audit — v0.8.3 Phase 5

| Active location | Phase-4 headline wording / issue | Classification | Phase-5 disposition |
|---|---|---|---|
| Abstract | Guard beats target-only but fixed speculation is faster | Safe direction; incremental-control conclusion implicit | Added “no incremental control benefit is shown”; retained both target-relative point estimates and 180/180 generated-ID result |
| Introduction | M4 historical text-path observations are supporting cases; M4 Guard is not a headline contribution | Safe | Kept the three contributions unchanged; moved established prior-work sentence immediately before them |
| Runtime section opening | Guard faster than target-only; fixed has higher aggregate speedup point estimate | Could obscure paired adverse result | Names fixed speculation as faster in the post-study paired secondary comparison and says no incremental benefit |
| Runtime methods | Guard fallback, offline oracle, frozen policy and direct-ID gate | Safe; no claim that a controller wins | No method or number change |
| Runtime held-out result | Guard profitable; Guard/Always-Spec latency above one, interval above parity, 24 versus 36 prompts | Safe and explicit | Retained; adverse paired comparison remains visible |
| Runtime final interpretation | “profitable prospective execution of a complete-cost continuation rule” | Could be read as controller success | States direct-ID preservation and target-only profitability, then no incremental benefit over Always-Spec |
| Table 3 | Target/Guard and Target/Always-Spec adjacent; Guard/Always-Spec labeled post-study secondary | Safe | **NO CHANGE NEEDED**; values and row order retained |
| Conclusion | Guard beats target-only but trails fixed speculation | Safe direction; post-study status and control conclusion implicit | Names post-study paired secondary status and no demonstrated incremental control benefit |
| Limitations | Post-study secondary, not registered primary; Guard higher latency; no transfer claim | Safe | Unchanged |
| Appendix runtime section | Recomputed paired ratio, chronology, and post-study status | Safe | Unchanged |

## Frozen values and interpretation

- Target/Guard speedup: **1.3114×**, 95% prompt CI **[1.2487, 1.3787]**.
- Target/Always-Spec speedup: **1.3469×**, 95% prompt CI **[1.2867, 1.4088]**.
- Guard/Always-Spec latency: **1.0270760219826773**, 95% paired prompt-bootstrap CI **[1.0129560055428655, 1.0435592653980876]**; the manuscript displays rounded **1.0271 [1.0130, 1.0436]**.
- Faster prompt medians: Guard **24**, Always-Spec **36**, ties **0**.
- Guard is profitable relative to target-only. Fixed speculation is faster on the frozen paired comparison. The latter is reviewer-requested post-study secondary analysis, not the registered primary endpoint. No incremental advantage of control is established.

No result, statistical method, Table 3 value, or archive record changed.
