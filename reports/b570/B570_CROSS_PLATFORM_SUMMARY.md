# Cross-platform Backend Summary

| Platform | Fast-path correctness | V2 raw | V2 exact | Frozen HumanEval | Speed status | Energy boundary | Key limitation |
|---|---|---|---|---|---|---|---|
| M4 / Metal | PASS, 90/90 | not recorded here | not recorded here | 90/90 exact; 1.387x | admissible for this conditioned workload | Apple package | representative 24Q was 0.842x |
| RTX 5070 Ti / CUDA | correctness-blocked | 1.009 / 0.983 at registered depths | 2.431 / 2.137 serialized | fast path failed; exact RTX fallback 90/90 and 0.650x | fast inadmissible; fallback exact but slower | RTX component | no same-root-cause inference |
| Arc B570 / Vulkan | correctness-blocked | 1.2426 / 1.6373 at 512/2048 | not admissible; fallback cells remote-contaminated | 45/90 exact pairs; fallback gate 18/18 exact | all-pair diagnostic; exact subset post-hoc | Arc B570 GPU board | original six-prompt gate remains FAIL |

Bounded interpretation: multiple discrete-GPU backend paths can be correctness-blocked under strict token-exact evaluation. This does **not** establish a shared CUDA/Vulkan root cause.
