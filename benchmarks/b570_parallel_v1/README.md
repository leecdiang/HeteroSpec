# B570 physical-prefix parallelism

The study starts at PR165 commit `5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f`. Its Vulkan runtime consumes the same shared rule bytes as RTX commit `9c79594f679ea4aad1956d8a385fdf6a7352d892`. The file has Git blob `a0baff824a1b54fb3867845372939b9a97c11115` and SHA-256 `7c1e2ee97e0af5b306ec9ba3cf7e2fb55c37749da07891f46cccd88041530809`.

| Arm | Whole target calls on one known query | Attention |
|---|---|---|
| S1 | One call per row | Original scalar arithmetic |
| PQ-ext | One call | Per-row attention, retaining physical prefixes |
| QB-local | One call | Adjacent compatible rows share a prefix group |
| WB-cut | One call per physical prefix group | Batched compatible attention inside each call |
| FAST | One native call | Original unscoped native dispatch |

WB-cut reads the actual KV allocator and fast-paths a query contained in one physical extent. The native caller submits each predicted group through the normal target decode API. All arms hold the same target and draft weights on Vulkan. Target-only service constructs only the target context. Speculative admission separately constructs both contexts.

The original scalar process creates checkpoints, independently for each context and model. Each heavy comparison restores and verifies identical state bytes, consumes identical tokens, and captures full-vocabulary F32 bytes for every row. The fixed-work timer excludes checkpoint restoration. The natural service timer includes fresh context creation, prefill, continuation and destruction. Diagnostic runs can capture graph nodes, GPU dispatch dimensions and device timestamps. Production timings keep these probes off.

## Reproduction on the original host

The path bindings in `paths.py` identify the original PR152 numeric libraries, the PR165 source tree and the PR163 build kit. Use a fresh evidence root when replaying. `stage.py` builds the native libraries, `host.py` links original and candidate workers, and `register.py` binds the weights, historical P1 anchor and prospective coordinates. `structure.py` produces context-specific scalar checkpoints. `experiment.py` runs controlled qualification and the three fixed repetitions. `service.py` consumes the frozen role and the preregistered input ranges. `recompute.py EVIDENCE_ROOT --verify-objects` reads the saved vectors and reconstructs paired estimates.

## Development evidence

`evidence/first-pilots.json` reports all cells from the first B=256 experiments, including unmeasured cells and process failures. Qwen C1024 used the preliminary mapping. SmolLM2-1.7B C4096 used the stronger balanced PQ join. Their development measurements cannot establish final service performance.
