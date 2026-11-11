# Direct-ID qualification scope v0.7

Starting main: `bab0e44c74f7fa59d2ea42faf4dcf4c51a78e674`. Integration branch:
`paper/mlsys2027-direct-id-integration-v0.7`. The v0.5 comparator record is
historical and remains unchanged. This record adds prospective evidence.

| Layer | Source | Allowed use |
|---|---|---|
| Historical physical/performance | Frozen M4/RTX/B570 micro cells and post-prefill controls | Recorded mechanism proxies and timing under original comparators |
| Prospective qualification | `benchmarks/rtx_direct_id_v2/FORMAL_ANALYSIS.json`; `benchmarks/b570_direct_id_v1/FORMAL_ANALYSIS.json` | Direct committed/generated-ID contract for separately frozen tested paths |
| Historical mechanism diagnostic | RTX HumanEval/106 separate same-commit instrumented capture | Bounded argmax margin sign change; no shared CUDA/Vulkan root cause |

RTX: batched 75/90 exact pairs, 25/30 wholly exact prompts, BLOCKED;
serialized 90/90, 30/30, QUALIFIED. B570: fast 60/90, 20/30, BLOCKED;
serialized 78/90, 26/30, BLOCKED. Each study completes 270 executions and
180 comparisons. Both require exactly 90/90; no subset qualification.

Common protocol family: the same 30 HumanEval IDs, three repetitions,
greedy k=2, Qwen3-8B/Qwen3-0.6B Q8_0, and sequence equality. RTX uses the
original embedded-server CLI, context 4096, native debug commit events and
reference micro-batch one. B570 uses instrumented completion/speculative
front-ends, context 1024, sidecars, and reference micro-batch 128. B570 retains
raw overshoot and compares the semantic 128-ID/EOG endpoint. These differences
prevent a causal hardware ranking. Deterministic frozen counts have no
sampling confidence intervals and do not estimate population failure rates.

Historical RTX CPU-to-GPU ~0.404x and GPU-to-GPU ~0.650x remain historical
text-path controls. Fresh RTX qualification does not authorize them as
strict-ID performance. Fresh RTX driver 616.92 differs from historical
616.56. Historical B570 45/90 and 60/90 text-path counts and ~0.538x/~0.309x
diagnostic timings remain untouched and are not numerically commensurate
with the new 60/90 and 78/90 direct-ID counts. Historical M4 remains text-path
evidence; prospective M4 runtime direct-ID evidence is a separate campaign.

RTX archive SHA-256:
`fc3676adae93c4f21bf6e29d9787d95d1e60d08c2d7223de30fc58c46c3e0822`.
B570 archive SHA-256:
`58daa4159de12042c73194bbd99abc5e5e23c171578ea873675f07901582db20`.
Portable validators replay included records and check external frozen
identities; omitted model/runtime bytes are not independently rehashed here.

B570 scheduled launch failed during CP936/UTF-8 metadata decoding before
inference with zero formal executions. The first data-producing direct
launch used the unchanged frozen runner. No model, source, binary, driver,
sampling or parameter change occurred. RTX incomplete v1 is preserved and
contributes no completed-v2 formal pair. No inference, parameter search,
performance rerun or reopened campaign is authorized by this integration.

The historical comparator weakness is partially addressed prospectively,
not retroactively repaired. Figure 3 deliberately separates the two study
families; it is not a same-run cost-versus-correctness experiment.
