# Cross-platform Backend Summary

This is a compact mechanism summary, not a controlled hardware leaderboard. Target-forward `V_2^micro` values are batching proxies and are not automatically complete realized target-round costs.

| Platform | Backend/path | Fast-path correctness | Fast/raw `V_2^micro` | Serialized/exact-control path | Control `V_2^micro` | HumanEval exactness | Admissible end-to-end result | Energy boundary / limitation |
|---|---|---|---|---|---|---|---|---|
| Apple M4 / llama.cpp | Metal | PASS in tested final cells | not recorded in this compact table | exact qualified path available | not recorded here | 90/90 in HumanEval fixed-k2 | 1.387x [1.351,1.422] on preregistered HumanEval; representative 24Q 0.842x | Apple package aggregate; workload-conditioned |
| **RTX 5070 Ti Laptop** / llama.cpp | CUDA | batched `ubatch=2` blocked on frozen replication | 1.009 / 0.983 | serialized `ubatch=1` exact control | 2.431 / 2.137 | serialized control 90/90 | CPU→RTX 0.404x; RTX→RTX 0.650x | component domains where measured; fast raw path is inadmissible |
| Intel Arc B570 / llama.cpp | Vulkan | blocked, 45/90 | 1.2426 / 1.6373 | unique serialized `ubatch=1` candidate | **1.9827 / 1.9917 (`V2_serialized`)** | serialized fallback 60/90 | **none globally admissible** | Arc B570 board only; all fallback timing/energy diagnostic |

The B570 historical analysis object retains the field name `V2_exact` for provenance. Paper-facing text must not treat that field name as proof of workload-global exactness; serialization is an execution property, while exactness is established empirically by the frozen correctness comparison.

Strict token equivalence can alter the admissible execution path across multiple tested backends. This does not imply that CUDA and Vulkan share one numerical root cause, and the target-forward ratios above must not be compared as complete end-to-end verification cost across platforms.
