# 358H Runtime R0 API Decision Table

This note is an execution aid for the local 358H machine. It does not change the frozen scientific protocol and must not be used to select paths from timing.

## Current API facts to verify locally

OpenVINO 2026 exposes `InferRequest.query_state()` / `reset_state()` and `VariableState.get_state()` / `set_state()` / `reset()`. Optimum/OpenVINO causal-LM exports may be either stateful (KV hidden behind OpenVINO state) or stateless (explicit past/present KV). The frozen INT4 IR, the installed Optimum version, and the requested physical device determine which path is actually available.

Authoritative API references at protocol-design time:

- https://docs.openvino.ai/2026/api/c_cpp_api/group__ov__runtime__cpp__api.html
- https://docs.openvino.ai/2026/documentation/openvino-extensibility/openvino-plugin-library/synch-inference-request.html
- https://huggingface.co/docs/optimum-intel/openvino/export

The local R0 probe remains authoritative for this experiment.

## Decision table

| R0 observation | Classification | Allowed implementation | R1 candidates | Forbidden interpretation |
|---|---|---|---|---|
| Optimum loads on requested device; explicit PKV inputs/outputs or returned `past_key_values`; no internal state needed | `EXPLICIT_PKV` | Keep committed PKV object; generate candidates from it; on rejection discard speculative PKV and advance only committed suffix | `OPTIMUM_REPLAY_<DEV>_UB1`, `PERSIST_<DEV>_UB1`; NPU may also predeclared UB2 | Do not claim zero-copy unless measured/verified; Python/frontend tensor copies remain charged |
| Optimum loads; `query_state()` returns state; lossless host snapshot + `set_state()` restore works | `VARIABLE_STATE_RESTORABLE` | Snapshot committed state before proposal; restore only when rejected candidate is already materialized; charge copy/restore bytes and time | same as above | Do not hide snapshot cost; do not call chat history arbitrary rollback |
| Stateful model works but VariableState cannot be read/write-restored exactly | `STATEFUL_NON_RECONCILABLE` | No persistent speculative adapter in v0.1 | replay only | Do not label sequential generation or `start_chat()` as persistent speculative state |
| Requested NPU compile fails in Optimum but frozen GenAI LLMPipeline still works | `OPTIMUM_NPU_UNAVAILABLE` | Keep legacy NPU replay control only | `LEGACY_NPU_UB1`, predeclared `LEGACY_NPU_UB2` after target UB2 gate | No CPU/AUTO/MULTI fallback under an NPU label |
| Execution device property is not exactly `[CPU]` or `[NPU]` as requested | `BINDING_FAIL` | stop that path | none for that frontend/device | Never accept implicit fallback |
| Snapshot/restore changes next-token ID in forced tests | `RECONCILE_FAIL` | block persistence | replay only | Timing is diagnostic only |
| TARGET UB2 forced state tests pass, but HumanEval exactness is < 90/90 | `TARGET_UB2_BLOCKED` | retain UB1 | no UB2 formal timing | 89/90 is not approximate qualification |
| TARGET UB2 is 90/90 exact and a same-policy NPU UB1/UB2 pair is 90/90 exact | `TARGET_UB2_QUALIFIED` | registry may promote predeclared pair | selected automatically by registry | Do not choose pair from timing |

## Required local checks before freeze

1. Record raw IR input/output names and shapes.
2. Record `stateful`, `use_cache`, `query_state()` count, state names/shapes/dtypes/bytes.
3. Record `EXECUTION_DEVICES` after compilation.
4. Prove reset repeatability and no cross-request state leakage.
5. Prove same-frontend replay and persistent proposal IDs agree at matched committed prefixes.
6. Force 0/1/2 accepted-token branches and repeated rejection.
7. For explicit PKV, verify proposal inference does not mutate the committed checkpoint object in place.
8. For VariableState, verify snapshot -> speculative advance -> restore reproduces the exact next-token logits/token IDs.
9. Treat all R0 timing as `NON_FORMAL / INVALID_FOR_PERFORMANCE_CLAIMS`.

## Escalation rule

If the frozen NPU IR cannot expose a safe reconcilable state through the installed OpenVINO/Optimum path, v0.1 records `PERSIST_NPU = IMPLEMENTATION_UNAVAILABLE`. Engineering a new converted/static/state-exposed IR is a new backend and requires a new protocol revision before R1; it must not be introduced after observing R1/R2 performance.
