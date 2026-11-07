# Representation, backend and evidence

All statements below bind to the source hashes and line/symbol anchors in
BACKEND_MAP.json. Dimensions below are dim0-first. D=128, H=Hq, G=Hkv,
q=2 and K is the declared key extent. Actual synthetic graph ne/nb/dtype and
precision flags for 36 graph exports are retained there; native operand nb
and actual per-op assignment are UNKNOWN.

| Representation | Same logical object / required mapping | Frozen backend mapping | Evidence / unknown |
|---|---|---|---|
| MQ | Q[D,2,H,1], scores[K,2,H,1], AV[D,2,H,1], permute[D,H,2,1], cont[D*H,2]. Head g=floor(h/(H/G)); mask column=query. | Source batch3 matches. With contiguous fixture K/V and H>1, vector small-column predicate is false; matmul path predicted. Device/pipeline/split choice unknown. | Exact address checks and independent FP64 stage diagnostics on CPU. SOURCE_PREDICTED_PATH for GPU dispatch; no observed GPU branch. |
| PQ | Two Q[D,1,H,1] views at j*Q.nb1; two mask[K,1,1,1] views at j*mask.nb1; two complete attention chains, cont[D*H,1] then concat dimension1. | Source batch3 matches; one-column vector predicate reachable. Native permuted K/Q can meet p021 only when both batch3=1, stride ordering and device limits also hold. Fixture contiguous K/V uses general vector path prediction. | Strong software organization keeps per-query chains. It adds graph outputs/concat storage and scheduling; these are not free or measured here. Four full P1 endpoints match R, but no full-P1 or unseen-input qualification. |
| QB | Q[D,1,H,2] has nb3=original Q.nb1; K/V batch3 remains1; mask[K,1,1,2] nb3=mask.nb1. AV[D,1,H,2], permute[D,H,1,2], cont[D*H,2]. | Both MUL_MAT fail frozen Vulkan supports_op source-batch equality. CPU broadcasting uses division factors and is mathematically valid. Scheduler fallback/copies predicted, actual assignments unknown. | SOURCE_PROVEN_PROPERTY: support predicate false. CPU semantics are not native GPU arithmetic evidence. QB cannot be called a validated GPU batched kernel from graph names. |
| q1 common path | Hook delegates; actual CPU original nonflash QK/softmax/AV/permute/cont chain executed. | No batch lift; no multiquery-QB validation. | 648 CPU common-path graph computations. Native M_R_QB 4/4 is q1 endpoint evidence only. |
| Context/cache | Per-context role:phase:layout:ub:capacity; active layout thread-local. Synchronize/invalidate on key changes; upstream reuse requires equal n_tokens/sequences/outputs and input compatibility. Buffer owners live through compute. | Source guards + pure per-context state model. | No actual binder/GPU-context creation. Native KV equality, async lifetime and real cache hit costs remain UNKNOWN. |

An actionable hardware question remains whether independent queries can change
issue grouping and share supply while preserving each query's declared
numerical computation. PQ is the software baseline to beat, including its
concat, ownership and scheduling costs. A CPU model would first need an explicit
mechanism and equal-resource strong baselines; none is calibrated by these data.

This is not the first discussion of batch invariance. Thinking Machines' primary
[batch-invariance article](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
describes fixed reduction configuration for matmul, consistent KV treatment and
fixed split-size (rather than fixed split-count) attention. Our finding is a
specific representation/capability boundary in a frozen implementation, plus
address/state checks; it neither implements their kernels nor establishes
invariance for GPU reductions.

Index/state preservation is required. Mathematical freedom to regroup queries
does not license finite-precision branch changes. Graph node counts are not
shader counts; logical tile bytes are not DRAM traffic; source branches are not
XMX usage or proprietary arithmetic DAGs. Sharing, ports, contexts and sync
have costs. No hardware necessity, RTL, GPU simulator, cycle model or PPA claim.
