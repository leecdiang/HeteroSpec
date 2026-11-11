# B570 shared-rule transfer

The native mapping starts with the frozen PR163 candidate-combined-02 llama.cpp tree. PR164's integrator stages a new tree. The B570 mapping then connects the shared projection decision to the live Vulkan matvec selector. For scoped Q8/F32 projection it queries the existing MMVQ predicate using scalar and actual batch dimensions, device capability and contiguity. When F32 preservation is required, the batched F32 shader receives the original activations. The target policy covers prefill, ordinary generation and verification. Draft calls clear the target scope.

The attention planner reads the native allocator's slot head, occupancy, capacity and padding. Row requirements include extent, tensor types, head structure, strides and layout. Reuse checks include policy identity, scalar extent vector and the same logical ordering guard used when constructing the graph. The teacher-forced probe records the native reuse counter across a same-shape precision change.

The original reference uses the PR152 all-GPU Qwen target/draft Q8 weights, eight threads, F16 KV and scalar target schedule. The speculative arms use the original k1 contract. The PR152 executable accepts a panel and job. Its adapter adds recording, clean timing and structural probes and links the original numerical DLLs. The historical P1 donor uses UB4 with one-token calls. Its state and initial logits are checked against the original before interpreting resumed PQ/QB results.

## Native reproduction

Use a fresh PR164 worktree on the original host. Host paths are bound in `scripts/b570_qwen_transfer/build_driver.py` and `execute.py`. The required inputs are the authenticated PR152 source, models and raw captures plus PR163's frozen tree and supervisor. Each attempt uses a fresh output path.

1. Stage the frozen tree with `src/reference_batching/integrate_llama_cpp.py --backend vulkan --source <PR163-final-tree> --out <new-root>/source-01`. Apply `map_vulkan.py <new-root>/source-01` and `final_mapping.py <new-root>/source-01`. The initial development build used the first mapping alone.
2. Configure the PR163 companion CMake project with Visual Studio 17 2022, x64, the pinned Vulkan SDK 1.4.357.0, `LLAMA_SOURCE=<new-root>/source-01`, `HS_COMPANION_ORACLE=OFF`, `LLAMA_BUILD_NUMBER=10839` and `LLAMA_BUILD_COMMIT=0cae43063`. Build Release into `build-01`. Configure/build logs and runtime binaries are retained.
3. Run `build_driver.py original-final` and `build_driver.py shared-01 --candidate --version 01`. Run `execute.py admit` for each role. Run `execute.py original original-final`, `execute.py known shared-01` and `audit.py shared-01 <4|6|2>`. The initial original adapter produced `original-4`, `original-6` and `original-2`, which the auditor uses as retained scalar records. The final original adapter independently repeats all three fixtures.
4. Run `controls.py probe` on the original teacher-forced role (`original-probe-01`) and on `shared-01`, then `controls.py check shared-01`, `controls.py reversal shared-01` and `llama_controls.py 01`.
5. `prepare_pool.py` tokenizes pinned natural texts with the exact Qwen vocabulary and validates all three historical prompt-ID sequences. It applies the authenticated exposure inventory and subsequent PR163 exposures. Run `confirmation.py freeze`, then `select`, `qualify`, `time` and `phases` in order. Run `cost_report.py` to reconstruct the one registered cost panel.

The integrated target prefill schedule is uniformly P4T. Three sessions use immediate same-arm warmups. Phase clocks use one separately designated input. Model loading, reference preparation and all failed attempts remain identifiable in the raw evidence.


The completed tables are in [RESULTS.md](RESULTS.md). For independent CPU reconstruction from the [published evidence](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-qwen-shared-transfer-v1-evidence-20261103), use the release [README](https://github.com/leecdiang/HeteroSpec/releases/download/b570-qwen-shared-transfer-v1-evidence-20261103/README.md) and [standalone auditor](https://github.com/leecdiang/HeteroSpec/releases/download/b570-qwen-shared-transfer-v1-evidence-20261103/recompute.py).
