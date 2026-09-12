# Cross-platform Backend Summary

| Platform | Backend | Fast-path correctness | V2 fast/raw | Exact fallback | V2 exact | HumanEval exactness | Valid speedup | Energy boundary | Main limitation |
|---|---|---|---|---|---|---|---|---|---|
| Apple M4 | Metal | PASS | not recorded here | available | not recorded here | 90/90 | 1.387x | Apple package | representative 24Q was 0.842x |
| RTX 5070 Ti | CUDA | blocked | 1.009 / 0.983 | available | 2.431 / 2.137 | fallback 90/90 | 0.650x | RTX component where measured | exact fallback expensive |
| Intel Arc B570 | Vulkan | blocked, 45/90 | 1.2426 / 1.6373 | unique serialized candidate | 1.9827 / 1.9917 | 60/90 | not globally admissible | Arc B570 board | strict exactness changes the admissible path |

Strict exactness can alter the admissible execution path across multiple tested discrete-GPU backends. This does not claim that CUDA and Vulkan share an identical root cause.
