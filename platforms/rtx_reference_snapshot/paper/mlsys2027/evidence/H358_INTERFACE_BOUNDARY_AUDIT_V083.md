# 358H State-Interface Boundary Audit — v0.8.3 Phase 5

| Active location and phrase | Category | Boundary / action |
|---|---|---|
| Abstract: isolated NPU advantage does not survive measured state interface | Measured | Retained; a comparison of isolated throughput with integrated path, not an intrinsic NPU weakness claim |
| §5.3: CPU and NPU each have direct-ID-qualified but unprofitable integrated paths | Measured | Retained; frozen speedups remain CPU 0.734× and NPU 0.352× |
| §5.3: synchronous OpenVINO call replays prefix and proposes tokens; 58.35% | Measured but wording could permit replay-only reading | Changed to “full committed-prefix replay/reconstruction and proposal”; explicitly inseparable in recorded timing |
| §5.3: complete target work and residual orchestration | Measured | Retained as separate timed regions; no causal split inside the OpenVINO call |
| Figure 4 caption: 58.35% replay-plus-proposal call; replay-only time not measured | Measured and explicit | **NO CHANGE NEEDED**; Figure 4 asset and caption unchanged |
| §7 later intervention: CPU state restore/reconcile not established; Optimum NPU state-capable path unavailable | Measured implementation boundary | Retained; does not imply devices cannot retain state |
| §7 UB2 gate failed; no qualified intervention pair; no formal R2 performance run | Measured qualification outcome | Retained; no intervention speedup or failure of a persistence optimization is inferred |
| Limitations: replay and proposal share one region; persistence benefit not established | Inferred-but-bounded guardrail | Retained |
| Conclusion: state interface consumes isolated advantage; intervention stops at qualification | Inferred-but-bounded summary | Retained; no formal later-intervention performance claim |
| Appendix: synchronous call combines reconstruction and proposal | Measured | Retained; appendix result values and ledger unchanged |

**Unsupported claims excluded:** replay alone costs 58.35%; NPU compute itself is weak; persistence would recover a particular percentage; the later intervention has a formal performance result. None appears in the active paper.
