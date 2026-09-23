# HeteroSpec 358H Runtime Architecture v0.1

Status: **pre-execution design**. No runtime performance result is implied by this document.

## 1. Design objective

The runtime is intentionally smaller than a general speculative-decoding scheduler. It addresses two measured failure modes with separable mechanisms:

1. **State realization:** avoid reconstructing the entire committed draft prefix on every speculative round when the backend exposes a safe, reconcilable state representation.
2. **Verification realization:** permit a physically different target verification path only after that exact execution setting satisfies the active token-output contract.

A third component, the profitability guard, is an architectural policy hook only. It is not enabled by the formal R2 mechanism study.

## 2. Evidence boundary

The closed 358H Phase-3 campaign is immutable. The prospective runtime imports its target tokenization/verification semantics and validates the legacy runner SHA, but does not modify any old script, raw observation, analysis product, or conclusion.

New runtime artifacts live under:

- `scripts/platform/358h_runtime/`
- `benchmarks/358h_runtime/`
- a new runtime-specific `runs/358h/...` directory during local execution.

## 3. Layered architecture

### 3.1 Qualification registry

`freeze_runtime_registry.py` is the admission controller. A complete path is usable only if:

- its R0 implementation/device gate passes,
- the R1 small exactness gate passes,
- the R1 full exactness gate passes,
- the path was built under the same frozen source/environment manifest.

Timing is never read when constructing the registry.

The registry is therefore upstream of policy:

```text
candidate execution path
        |
        v
R0 feasible? -------- no --> BLOCKED / IMPLEMENTATION_UNAVAILABLE
        |
       yes
        v
R1 exact under contract? - no --> BLOCKED / diagnostic only
        |
       yes
        v
QUALIFIED PATH
        |
        +--> R2 fixed-policy measurement
        |
        `--> future profitability policy (R3, not R2)
```

### 3.2 TargetPath

`runtime_target.py` loads the pinned Qwen3-8B target once and creates independent llama.cpp contexts for:

- `TARGET_UB1`: frozen serialized reference path;
- `TARGET_UB2`: prospective two-token physical verification context.

The two contexts share model weights but never KV/history state. Tokenization, ordered acceptance, correction, bonus, and rejected-suffix removal are inherited from the frozen Phase-3 implementation. Only `n_ubatch` is prospective.

`TARGET_UB2` is a correctness gate, not a useful target-only R2 timing condition: target-only decoding submits one token per `llama_decode`, so a target-only UB2 context does not exercise the intended two-token verification shape. The target-path timing effect is instead identified with the same speculative policy at UB1 and UB2.

### 3.3 DraftStateAdapter

The request-scoped interface is:

```text
begin(committed_prompt)
checkpoint [inside propose when required]
propose(committed_prefix, width)
reconcile(committed_prefix_before, proposals, accepted, committed_this_round)
finish()
```

Every implementation also exposes its logical committed-state length and execution capabilities.

Three policy families are implemented:

#### Legacy GenAI replay

`LEGACY_*`

- frozen OpenVINO GenAI LLMPipeline frontend;
- complete committed prefix is replayed for every proposal;
- provides the contemporaneous bridge to closed Phase-3 behavior.

#### Same-frontend replay control

`OPTIMUM_REPLAY_*`

- uses the same state-capable frontend/engine as the persistent candidate;
- deliberately reconstructs state from the complete committed prefix every round;
- isolates persistence benefit from frontend/runtime changes.

#### Persistent/reconcilable state

`PERSIST_*`

Two state representations are supported by the adapter contract:

1. **Explicit past-key-values:** retain the committed cache object, speculate from it, then retain proposal state only when valid or advance from the committed checkpoint after rejection.
2. **OpenVINO VariableState:** snapshot the committed backend state before speculation, restore on partial rejection, and advance only the actually committed sequence.

No state copy is considered free. Checkpoint creation, host/device transfer, restoration, correction/bonus incorporation, reset, and fallback are charged to the measured draft subsystem.

If a backend cannot expose a correct reconcilable state without hidden full-prefix replay, that device/path is `IMPLEMENTATION_UNAVAILABLE` for the persistent intervention. It is not silently replaced by AUTO, CPU, or a replay implementation.

## 4. Request state machine

```text
UNINITIALIZED
    |
    | begin(prompt)  [charged]
    v
COMMITTED(prompt)
    |
    | target-only initial token + draft reconcile
    v
COMMITTED(prompt + output)
    |
    | checkpoint/propose k<=2
    v
SPECULATIVE(candidate state)
    |
    | target verify
    v
+--------------------------+
| accepted all candidates? |
+--------------------------+
    | yes                         | no
    |                             |
    | retain candidate state      | restore committed checkpoint
    | + advance target bonus      | + accepted prefix + correction
    |                             |
    +-------------+---------------+
                  v
             COMMITTED
                  |
          output budget done?
             |          |
            no         yes
             |          |
             +----------+--> finish/reset [charged] --> TERMINATED
```

A one-token remaining output budget is a strict zero-width draft boundary: the draft proposal API is not called.

## 5. Cross-layer invariants

After every target round:

1. target logical history equals the orchestrator committed ledger;
2. target KV max position equals `len(committed_history)-1`;
3. draft logical state length equals prompt tokens plus committed output tokens;
4. rejected proposal suffix is never treated as committed draft state;
5. each speculative round commits `C = accepted draft prefix + correction/bonus` tokens;
6. complete output never exceeds the frozen output cap;
7. request termination invalidates draft state before the next request;
8. every fallback/recovery event is surfaced and charged;
9. physical execution device equals the requested single device.

## 6. Accounting boundary

Target prompt prefill remains outside the primary post-prefill decode boundary, matching the hardware study's principal timing contract.

For a speculative request, the enclosing timer includes:

- draft begin/prompt initialization;
- checkpoint creation;
- draft proposal execution;
- target verification;
- state restoration/reconciliation;
- correction/bonus incorporation;
- fallback/recovery;
- draft finish/reset;
- orchestration residual.

The components must reconcile to the enclosing request time. Moving prompt/state work outside a narrow proposal timer is not an optimization.

## 7. Engine topology

Within a process:

- target Qwen3-8B weights are loaded once; UB1/UB2 have separate contexts;
- at most one legacy GenAI draft engine is resident per device;
- at most one Optimum/OpenVINO compiled draft engine is resident per device;
- replay and persistent policies are wrappers over that same Optimum engine;
- requests using a shared engine are serial and fully reset between observations.

This avoids treating duplicate model compilation, cache residency, or NPU resource pressure as a policy difference.

## 8. Formal path decomposition

Minimum UB1 controls, when individually qualified:

```text
TARGET_UB1
LEGACY_CPU_UB1
OPTIMUM_REPLAY_CPU_UB1
PERSIST_CPU_UB1
LEGACY_NPU_UB1
OPTIMUM_REPLAY_NPU_UB1
PERSIST_NPU_UB1
```

NPU UB2 has one predeclared promotion branch:

```text
preferred: PERSIST_NPU_UB1  <-> PERSIST_NPU_UB2
fallback : LEGACY_NPU_UB1   <-> LEGACY_NPU_UB2
```

The preferred pair is used only if NPU persistent state is feasible and both complete paths qualify. Otherwise the legacy pair may isolate the target verification intervention. Selection never uses timing.

## 9. Profitability policy hook

`runtime_policy.py` implements two concepts:

- `QualificationRegistry`: correctness admission always precedes cost policy;
- `RealizedProfitabilityGuard`: consumes complete realized request cost per committed token and can decline speculation when observed runtime cost does not clear a safety margin against target-only.

The guard intentionally ignores isolated draft throughput and draft acceptance by themselves. It is disabled in R2 because a measured adaptive-policy claim requires calibration/holdout design, exploration rules, and guard-overhead accounting. Those belong to a separately frozen R3 study if later justified.

## 10. Interpretation

The architecture supports four scientifically distinct outcomes:

- persistent state reduces draft cost and the complete runtime becomes faster than target-only;
- persistent state reduces draft cost but target verification still prevents profitability;
- UB2 reduces target-side cost but state realization remains the bottleneck;
- an intervention is unavailable or fails exactness and is blocked.

All four are valid outcomes. None reopens or changes the closed 358H hardware campaign.
