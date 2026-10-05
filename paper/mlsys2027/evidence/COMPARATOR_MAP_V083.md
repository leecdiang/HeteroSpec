# Comparator map — v0.8.3 Phase 3

This map records endpoint provenance. A qualification result applies only to its own frozen path and reference; it does not transfer a timing result across campaigns.

| Campaign | Timing endpoint | Output-comparison endpoint | Evidence class | Can timing be called strict-ID qualified? | Notes |
|---|---|---|---|---|---|
| M4 representative 24Q | Historical post-prefill decode speedup | Parsed CLI text-path agreement, 72/72 | H | No | Distinct estimator and session from M4 HumanEval. |
| M4 HumanEval historical | Historical post-prefill decode speedup | Parsed CLI text-path agreement, 90/90 | H | No | Prompt is included in parsed text. |
| RTX historical | Historical post-prefill decode speedup and target-forward proxy | Text-path agreement; serialized controls 90/90 each | H | No | Fast path blocked; serialized controls are secondary. |
| B570 historical | Diagnostic post-prefill decode speedup and target-forward proxy | Normalized/re-tokenized text-path agreement, fast 45/90 and serialized 60/90 | H | No | Both paths remain globally inadmissible. |
| 358H Phase 3 | Integrated post-prefill decode time and stateful cost | Direct generated-ID sequence equality, CPU and NPU each 90/90 | Q | Yes, for its own integrated path | A later intervention stops at qualification and has no formal performance endpoint. |
| M4 prospective runtime | Held-out post-prefill target/Guard/Always-Spec latency | Direct generated-ID sequence equality, 180/180 held-out pairs per speculative condition | Q | Yes, for its own runtime path | Historical M4 outcomes informed design; Guard is slower than Always-Spec in the secondary comparison. |
| RTX direct-ID v2 | Operational elapsed fields only; no matching fresh latency endpoint | Direct generated-ID sequence equality, batched 75/90 BLOCKED and serialized 90/90 QUALIFIED | Q | No fresh strict-ID timing claim | The serialized output path qualifies, but historical timing is a different experiment. |
| B570 direct-ID v1 | Operational elapsed fields only; no matching fresh latency endpoint | Direct generated-ID sequence equality, fast 60/90 and serialized 78/90, both BLOCKED | Q | No | Historical timing remains diagnostic. |
| B570 mechanism reserved | No performance endpoint | Frozen UB1 predictor/live complete-ID agreement 72/72; reference/live direct-ID equality 60/72 BLOCKED | P for prediction; Q for reference gate | No | 24/24 prompt classifications and 12/12 divergent first indices over four prompts; predictor reproduction is not reference qualification. |

H = historical text-path agreement. Q = fresh direct-ID qualification. P = frozen predictor-to-live complete-ID agreement.
