# Reference-batching implementation status

## Completed native evidence

RTX PR162 (`e11d2b75d82422409ba2b701aa38c59f36acc50b`) and B570 PR163 (`10a70566ce01ab707dbdcc57d8270c1434088f07`) contain the completed Llama mechanism, repair, unseen-input and cost results. These measurements belong to their frozen native implementations. CUDA also has combined-policy Qwen8B/14B regressions; the Vulkan legacy Qwen regression kept the new precision and prefix switches off.

## Shared candidate delivered here

`src/reference_batching/reference_batching.hpp` supplies shared physical-prefix extraction, adjacent grouping and policy identity. `src/reference_batching/integrate_llama_cpp.py` stages the prefix planner and graph-reuse identity in the repaired CUDA/Vulkan source trees. CPU and source-integration checks support this candidate; the historical native results do not qualify the new candidate automatically.

## Remaining host implementation and transfer

The hosts must connect actual graph/backend arithmetic and dispatch descriptors to the shared interfaces, compile the candidate and demonstrate active Qwen rule triggers. Placeholder structural IDs or unused helpers are not automatic requirement extraction. The focused transfer tasks preserve the original numerical references and repair retained failures before a small frozen confirmation and one fixed cost panel.

- [Shared plan](../../../benchmarks/reference_batching_transfer_20261103/PLAN.md)
- [RTX execution entry](../../../benchmarks/reference_batching_transfer_20261103/RTX_PROMPT.md): Qwen8B/14B boundary and normalization-placement transfer.
- [B570 execution entry](../../../benchmarks/reference_batching_transfer_20261103/B570_PROMPT.md): active-policy repair of the original Qwen P1 counterexamples.

These host tasks produce separate result PRs. The current change supplies the shared candidate and executable handoff, without claiming new GPU measurements or completed automatic cross-family transfer.
