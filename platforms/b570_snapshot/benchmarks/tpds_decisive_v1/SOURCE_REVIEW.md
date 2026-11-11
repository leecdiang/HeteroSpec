# Source review supporting the design

Reviewed through the authenticated GitHub connector on 2026-11-05:

- `scripts/experiments/rtx_scope_transfer_v1/worker.cpp` at `29511ed91eb9f3d9773cfdda53e3554b0f4ad08b`: target and draft whole-prompt NATIVE producers, reserve fields, resident reset, k3 transaction. Original exact-worker SHA256 is independently pinned by PR183 stage.py to `4423bf687de4d652809c3ffad9cd9bf31770c2019c383fb54bd7abd24858b124`.
- `experiments/draft_ubatch_probe/stage.py` at `895c20513bd086d389ea52a60d0cd52a89bec73d`, Git blob `bc0dcbeb828683b8ed6d0cfcbbd73f587b04f406`: isolated draft physical UB with reserve1. Our derivative retains the intervention and assigns a separate study identity.
- `scripts/reference_baselines/stage.py` at `7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd`, Git blob `630b4112dfaa51ba8cede64004de306c3c8e68be`: reuse unchanged, rather than reimplement CUDA arithmetic.
- `benchmarks/b570_producer_consumer_boundary_v1/native/boundary.cpp` at `022babfabb3d1b6f4f2a2830dca04b2654d193f9`: singleton draft prompt callers, variable 1/2/4 prefill schedule API, reserve=ub, k1 transaction and native sequence exporter.
- `scripts/b570_qwen_transfer/build_driver.py` at `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f`, Git blob `cf74e1bbec60fc5beb1b7e6f223de9c92178645a`: recovered post-adaptation worker is required; literal old host paths are not portable commands.
- `scripts/b570_qwen_transfer/transfer_scope.hpp` at the same head, Git blob `30f05cf19bf370e8b8d29ba334c9f28724f01a2d`: reference precision/prefix selection applies to target modes; draft uses native mode0. Therefore wider draft arithmetic is intentionally allowed to differ under T.
- `experiments/draft_ubatch_probe/native_replay_bridge/parse_state.py` at PR183, Git blob `eec33db3ffd47affa6f2386da43ae44516274791`: known tiny-profile wire grammar. The new parameterized parser does not preapprove any real model/writer profile.

Documentation/review scope: source and fixed reports, not a new hardware run or independent reconstruction of all platform archives. CPU evidence from the uploaded morning report that was not recovered/committed is not used to satisfy any gate.

## Same-author implementation review corrections

- Explicit producer last-output flags prevent the forced replay helper from silently changing a P1 producer's original per-caller masks.
- B570 caller-only control prevents physical-UB placebo experiments.
- Counterbalance orders spread over roots as well as sessions; development/test overlap rejected.
- Endpoint reconstruction does not trust a candidate's shorter output length or self-reported committed history.
- Correct retained-prefix frontier is captured separately from native sequence export; accepted terminal pending is not copied blindly.
- Full-panel analysis rejects missing/failed/mismatched slots instead of reporting a favorable qualified subset.
- Complete native profiles, candidate/oracle source identity and module evidence remain host work; neither a source-format fixture nor an API stub is described as a native build.
- Ordinary engineering fixes are permitted before freeze; numerical reference changes and post-output policy/selection tuning are not.
