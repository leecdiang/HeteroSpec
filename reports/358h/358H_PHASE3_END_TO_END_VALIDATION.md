# 358H Phase-3 end-to-end validation

## Status

`358H BLOCKED — qualified heterogeneous OpenVINO-draft/Vulkan-target runner is unavailable`

No formal Phase-3 model generation or timing was performed. Formal Phase-3 data seen: **false**.

## Protocol freeze

- Phase-1/2 source commit: `4b655522225f73aa3aba64e7ae6141081d8270af`
- Phase-3 execution addendum commit: `011ebe967fdf0d49f037a80f825951cb6bbfacbd`
- Addendum SHA256: `6469ea89c21070206d9751b554ff73bde5a208944e0d61f19a2673ad4fdeeede`
- The addendum was frozen with zero Phase-3 formal runs and clarifies only execution details.

## MEASURED

No Phase-3 scientific quantity was measured.

Preflight reconfirmed AC online, Windows Balanced mode, no RDP session, and the frozen target GGUF, canonical draft GGUF, and OpenVINO IR hashes.

## DIAGNOSTIC

The frozen llama.cpp b10839 frontend implements `draft-simple` only with a draft model loaded by llama.cpp (`--spec-draft-model`). Its device option selects llama.cpp backends and cannot compile or execute the frozen OpenVINO IR on Intel NPU.

The qualified OpenVINO GenAI LLMPipeline executes the IR on CPU or NPU, but does not expose the stepwise draft KV state and external target-verification interface needed to connect it to the frozen llama.cpp Vulkan0 Qwen3-8B target. The direct lower-level NPU IR path also has the already-preserved empty-KV shape-inference failure. Consequently, no existing repository runner satisfies all frozen runtime, binding, algorithm, correctness, and instrumentation requirements.

## DERIVED

None. Acceptance, committed progress, speedup, verification cost, and handoff residual remain uncomputed.

## NOT_ADMISSIBLE

- Replacing the OpenVINO CPU/NPU draft with the GGUF draft accepted by llama.cpp.
- Moving the target to OpenVINO or another backend.
- Treating CPU fallback or a different NPU-compatible model as NPU execution.
- Starting formal timing before a heterogeneous non-formal dry run and independent CPU/NPU exactness validation.
- End-to-end energy claims: CPU whole-system energy was never qualified; NPU energy remains `NOT_ADMISSIBLE`.

## Required unblock

Implement and freeze a runner adapter that preserves the repository/llama.cpp greedy k=2 semantics while connecting the frozen stateful OpenVINO draft IR (explicit CPU or NPU) to the frozen llama.cpp Vulkan0 target. It must expose exact token IDs and acceptance counters, reset/rollback both KV states correctly, prove `EXECUTION_DEVICES` per draft path, retain explicit Vulkan0 offload evidence, and pass a NON_FORMAL task outside both frozen task sets before any formal gate is launched.

No tuning, model substitution, k change, or follow-up sweep was started.

