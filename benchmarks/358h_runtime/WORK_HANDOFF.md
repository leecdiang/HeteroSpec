# GPT-6 Work Handoff: 358H Runtime Study

Branch: `runtime/358h-codesign-v0.1`

Purpose: finish local API qualification and execute the new prospective Section 7 runtime study on the Core Ultra X7 358H machine without reopening the closed hardware campaign.

## Non-negotiable boundaries

1. Do **not** edit `scripts/platform/358h/`, old `runs/358h/...`, closed reports, or old analysis outputs.
2. Do **not** use old Phase-3 timings as formal R2 observations.
3. R0 is the only stage where API-compatibility repairs to the new runtime implementation are allowed.
4. Once `runtime_freeze_manifest.json` is generated, do not change HEAD, frozen source files, model/data artifacts, Python version, or frozen package versions through the end of R2.
5. Never replace explicit NPU/CPU execution with `AUTO`, `MULTI`, `HETERO`, or a silent fallback.
6. Never promote a path because its R0/R1 diagnostic timing looks fast.
7. One generated-token mismatch blocks that complete path from admissible performance claims.
8. Do not enable `runtime_policy.py` profitability adaptation during R2.
9. Energy is out of scope.

## Stage A — checkout and static validation

```powershell
git fetch origin
git checkout runtime/358h-codesign-v0.1
git status
python -m compileall scripts/platform/358h_runtime
```

Confirm the branch contains only new runtime-study files relative to main. Confirm the old Phase-3 runner hash is still accepted by `runtime_target.py`.

Inspect the active environment before changing anything:

```powershell
python --version
python -m pip freeze
python -c "import openvino as ov; print(ov.get_version()); print(ov.Core().available_devices)"
python -c "import openvino_genai as g; print(getattr(g,'__version__','unknown'))"
python -c "import importlib.metadata as m; print(m.version('optimum-intel'))"
```

If `optimum-intel` or a required dependency is missing/incompatible, repair the environment only during R0. Prefer an isolated runtime-study environment. Do not change the frozen model artifacts to make an API easier to use.

## Stage B — R0 capability discovery

Create a new run root, for example:

```powershell
$R = "runs/358h/runtime_codesign_20260923"
New-Item -ItemType Directory -Force $R | Out-Null
```

Run the descriptive state/API probe:

```powershell
python scripts/platform/358h_runtime/probe_openvino_state.py `
  --devices CPU NPU `
  --output "$R/r0_capability.json"
```

Then run forced state-machine tests:

```powershell
python scripts/platform/358h_runtime/runtime_state_tests.py `
  --devices CPU NPU `
  --output "$R/r0_state_tests.json"
```

The state-test command may return a non-zero exit code because one device is implementation-unavailable. Treat the JSON, not the shell code alone, as the diagnosis.

### What R0 must establish

For `TARGET_UB1` and `TARGET_UB2`:

- forced zero/one/two accepted-token cases reconcile correctly;
- repeated rejection is correct;
- reset is exact;
- target KV max position agrees with logical history.

For each persistent draft device:

- requested execution device equals actual execution device;
- persistent proposal tokens equal the same-frontend full-prefix replay oracle;
- forced acceptance/rejection sequences remain equal after reconcile;
- request reset has no cross-request leakage;
- the output-cap-one test never calls the proposal API;
- state transfer/checkpoint behavior is observable rather than hidden.

### NPU-specific decision rule

Current OpenVINO NPU implements state variables and Query State through plugin-managed state buffers, but its LLM execution has special shape/static-profile constraints. Therefore:

- do not assume `OVModelForCausalLM` direct NPU compilation will work merely because GenAI LLMPipeline worked in the closed campaign;
- if direct NPU state compilation fails, first determine whether this is a frontend/API compatibility issue that can be repaired without changing the frozen model semantics;
- do not use `AUTO`, CPU fallback, or GenAI chat history and label it `PERSIST_NPU`;
- do not treat `start_chat()` as evidence of arbitrary speculative rollback;
- if safe exact NPU reconcile remains unavailable, record `PERSIST_NPU = IMPLEMENTATION_UNAVAILABLE` for v0.1.

If NPU persistence is unavailable and the team wants to engineer a new static/state-exposed NPU backend, **stop before the freeze and before all R1 data**. Create a new protocol/branch revision (v0.2), add a same-frontend replay control for that backend, repeat R0, and only then freeze. Do not retrofit such a backend after seeing R1/R2 timings.

## Stage C — commit final R0/API repairs, then freeze

If R0 required code or dependency changes, finish them now, rerun R0, and commit the final implementation. The tracked working tree must be clean.

Generate the source/environment freeze manifest:

```powershell
python scripts/platform/358h_runtime/create_runtime_freeze.py `
  --r0-capability "$R/r0_capability.json" `
  --r0-state-tests "$R/r0_state_tests.json" `
  --output "$R/runtime_freeze_manifest.json"
```

After this command succeeds:

- do not commit anything;
- do not install/update/remove frozen Python packages;
- do not modify any frozen runtime source or protocol file;
- do not change model/data files;
- do not switch branches.

Untracked run outputs are allowed.

## Stage D — construct R1 candidate groups from R0 only

Use no timing information.

Recommended process-separated groups avoid unnecessary simultaneous CPU/NPU model residency.

### CPU group

Include only paths that R0 can actually instantiate:

```text
LEGACY_CPU_UB1
OPTIMUM_REPLAY_CPU_UB1   # only if Optimum CPU binding works
PERSIST_CPU_UB1          # only if CPU forced state test passes
```

### NPU legacy/target group

```text
TARGET_UB2               # only if R0 target UB2 state test passes
LEGACY_NPU_UB1
LEGACY_NPU_UB2           # predeclared UB2 fallback candidate
```

### NPU state-capable group

Only if the Optimum/state backend passed R0:

```text
OPTIMUM_REPLAY_NPU_UB1
PERSIST_NPU_UB1
PERSIST_NPU_UB2
```

Do not add CPU UB2, k sweeps, model variants, concurrency, or any newly discovered fast path.

## Stage E — R1 small correctness gate

Example CPU invocation:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage small `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths LEGACY_CPU_UB1 OPTIMUM_REPLAY_CPU_UB1 PERSIST_CPU_UB1 `
  --output-dir "$R/r1_small_cpu"
```

Example NPU legacy/target invocation:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage small `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths TARGET_UB2 LEGACY_NPU_UB1 LEGACY_NPU_UB2 `
  --output-dir "$R/r1_small_npu_legacy"
```

If NPU persistent is R0-feasible:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage small `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths OPTIMUM_REPLAY_NPU_UB1 PERSIST_NPU_UB1 PERSIST_NPU_UB2 `
  --output-dir "$R/r1_small_npu_state"
```

A return code of 2 means at least one requested path is blocked by exactness. Preserve the complete output. Do not repair a numerical mismatch after looking at its timing and then reuse earlier qualification results.

## Stage F — R1 full correctness gate

Run HumanEval30 x 3 only for paths that passed their R1 small gate. Use the **same freeze manifest**.

Example:

```powershell
python scripts/platform/358h_runtime/run_runtime_qualification.py `
  --stage full `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --paths <SMALL_GATE_SURVIVORS> `
  --output-dir "$R/r1_full_<group>"
```

Full promotion rule is exactly 90/90 token-ID equality against the shared `TARGET_UB1` reference. 89/90 is blocked.

R1 timing is qualification diagnostic only. Do not use it to choose the formal condition set.

## Stage G — freeze the R2 qualification registry

Pass all small summary files and all corresponding full summary files. Missing full results remain blocked.

Example shape:

```powershell
python scripts/platform/358h_runtime/freeze_runtime_registry.py `
  --small "$R/r1_small_cpu/qualification_summary.json" "$R/r1_small_npu_legacy/qualification_summary.json" <optional-state-summary> `
  --full  "$R/r1_full_cpu/qualification_summary.json"  "$R/r1_full_npu_legacy/qualification_summary.json"  <optional-state-summary> `
  --r0-state-tests "$R/r0_state_tests.json" `
  --r0-capability "$R/r0_capability.json" `
  --output "$R/runtime_qualification_registry.json"
```

The registry must state:

```json
"selection_uses_performance_timing": false
```

It should select UB2 in this predeclared order:

1. qualified `PERSIST_NPU_UB1` / `PERSIST_NPU_UB2` pair;
2. otherwise qualified `LEGACY_NPU_UB1` / `LEGACY_NPU_UB2` pair;
3. otherwise no formal UB2 timing.

`TARGET_UB2` is a gate for either UB2 branch but is not itself an R2 timing condition.

## Stage H — R2 formal prospective campaign

Before starting:

- AC power positively online;
- no RDP session;
- no package/source changes since freeze;
- no background benchmark/tuning activity;
- use the registry exactly as generated.

Run:

```powershell
python scripts/platform/358h_runtime/run_runtime_campaign.py `
  --registry "$R/runtime_qualification_registry.json" `
  --freeze-manifest "$R/runtime_freeze_manifest.json" `
  --output-dir "$R/r2_formal"
```

R2 fixes one process-affinity mask at session start and uses it for every condition. Do not restore the old CPU-only 0-11 affinity asymmetry.

Do not restart a slow-looking condition selectively. If a machine-level interruption invalidates the campaign, retain the failed run directory, document the reason, and restart the complete formal campaign in a new directory under the same frozen source/environment.

## Stage I — deterministic analysis

Only after R2 is complete:

```powershell
python scripts/platform/358h_runtime/analyze_runtime_campaign.py `
  --campaign-dir "$R/r2_formal" `
  --output-dir "$R/r2_analysis"
```

Primary outputs:

1. **System:** per-prompt median of `TARGET_UB1 / runtime end_to_end`, then geometric mean over 30 prompts with prompt bootstrap CI.
2. **State reuse:** same-frontend replay complete draft-subsystem time / persistent complete draft-subsystem time.
3. **Target path:** same-policy NPU UB1 target-verification time / UB2 target-verification time.

The bootstrap unit is the HumanEval prompt, not each repetition.

## Stage J — scientific interpretation before paper edits

Use these categories without forcing a positive story:

- `persistent draft ratio > 1`, system `<= 1`: state intervention works, system still not profitable;
- UB2 ratio `> 1` but system `<= 1`: target intervention reduces its component but not enough overall;
- both components improve and system `> 1`: measured combined runtime benefit;
- NPU persistent unavailable: implementation boundary, not NPU intrinsic weakness;
- UB2 exactness failure: blocked path, timing diagnostic only;
- R2 correctness regression after R1: that path loses performance admissibility.

Only after this classification should Section 7 text/figures be rewritten. Do not edit the manuscript while R0/R1/R2 is in progress.

## Local fixes Work may make before freeze

Allowed in R0:

- import/API compatibility for the locally installed Optimum/OpenVINO versions;
- correct extraction/restoration of the exact state representation exposed by the frozen IR;
- additional assertions/logging/provenance;
- Windows path/process-affinity compatibility;
- compilation/cache configuration needed to instantiate the same frozen model on the requested physical device.

Not allowed without protocol revision:

- changing model weights/quantization;
- changing k from 2;
- changing the target/draft model pair;
- changing the output cap/workload because results look unfavorable;
- approximate token acceptance;
- changing the target reference contract;
- silently replaying full prefix while reporting a persistent-state path;
- choosing formal candidates from observed speed.

## Deliverables to return to the research chat

Return, at minimum:

- final source commit used by `runtime_freeze_manifest.json`;
- R0 capability and state-test JSONs;
- freeze manifest;
- all R1 small/full status + qualification summaries;
- frozen qualification registry;
- R2 status/session/resolved observations;
- deterministic R2 analysis outputs;
- stderr/session logs proving Vulkan0 target placement and explicit draft device binding;
- concise list of any R0 code/API repairs made before freeze;
- no manuscript edits unless requested after the experiment is reviewed.
