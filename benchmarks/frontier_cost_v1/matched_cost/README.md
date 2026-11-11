# Matched LOCAL target-operation diagnostic

This directory provides an executable cost experiment for fixed target histories and fixed candidate IDs. It uses the original numerical core and the exact reconstructed M2 `PhaseContext` headers. Every arm must first agree on full output vectors, active sequence bytes, cache geometry, and a continuation before its operation times become eligible for comparison.

**Current result:** the CPU width experiment stopped at q2 because complete vectors and active sequence bytes differed. No width timing was admitted. A separate q1-only protocol smoke exercised timing, reset, accounting, and artifact replay. CUDA has not been run; the original paper/GPU reference remains unqualified. These results do not establish a speedup.

## What is compared

Each input contains a fixed token history, eight fixed following token IDs, and one fixed continuation token. For q from 1 through 8, the probe uses the first q following IDs and deduplicates three schedules:

| Schedule family | Example at q=8 | Output obligation |
|---|---|---|
| Scalar outer calls | 1+1+1+1+1+1+1+1 | All eight vocabulary vectors |
| Calls of at most four rows | 4+4 | All eight vocabulary vectors |
| One wide call | 8 | All eight vocabulary vectors |

Here q is the number of target input rows. The public q8 example contains one pending seed and seven proposals. It does not mean eight new draft proposals.

Every arm has a fresh context and replays the same history through the same fixed 32-row prefix producer. The probe does not restore a serialized sequence into an already mutated cache. Context configuration is identical across arms: n_ctx=1024, n_batch=1024, actual n_ubatch=32, eight reserved output rows, F16 K/V, and flash attention disabled. The exact original `PhaseContext` invokes LOCAL lowering, layout 0 and active scope, derives per-row append requirements from the native cache, synchronizes the decode, and preserves every requested logit vector. Outer call count and observed physical widths are recorded separately.

The scalar arm is a **new local diagnostic reference** on the newly loaded model/backend. It is not the historical R artifact, a CPU substitute for GPU R, or a certificate of the paper's numerical contract. The public inputs are exposed examples, not a new held-out quality panel or live speculative-decoding rollout.

## Qualification and timing boundaries

For each q and history, the reference and candidates must match bitwise on:

1. Initial active sequence serialization and native cache geometry.
2. Every element of every requested FP32 vocabulary vector, copied before a later native call overwrites its storage.
3. Final active sequence serialization and geometry.
4. The next fixed q1 continuation vector, active sequence serialization, and geometry.

Geometry checks include dense occupied positions, occupied extent, actual n_ubatch, and `phase_append_requirements(next,1)`, whose native guard checks the append head. Serialized active sequence bytes are not a capture of every unused allocator byte or the entire device context. The append guard, geometry, state bytes and continuation are complementary checks.

Any qualification mismatch stops the whole job before the measurement phase. The probe does not select a passing shape, reduce n_ubatch to 1, switch models, loosen equality, or sample again after a failure. During measurement, qualification is repeated against the retained reference and any mismatch also stops execution.

Two measurement modes are available, with two repetitions and reversed schedule order on the second repetition:

- `first_after_fresh_context`: replay the fixed prefix, capture the initial state, then measure the operation.
- `one_shape_warmup_then_reset`: execute the same shape once, clear the sequence, replay the same prefix, check reset state/geometry against the original initial checkpoint, then measure the operation.

The second mode is not a claim of steady-state or hot-graph performance. In the q1 CPU smoke, both modes reported one graph build and zero graph reuses for the measured operation. Reset equality is enforced in the bound C++ source; the reset export is not separately saved as a raw blob.

The timed interval includes the original LOCAL planning and counters, schedule/batch construction, decode synchronization, original output copies, and the common owned materialization of every requested full vector. New budget JSON bookkeeping runs outside the interval. Prefix work, state exports, equality checks, file writes, continuation, draft work and sampling are outside it. Initial state capture can influence cache state. Consequently the result is a **capture-conditioned, instrumented matched operation**, not complete service latency.

For a qualified q8 cell, use the directly observed paired difference

`delta_4plus4_minus_8 = T(history, same eight IDs, [4,4]) - T(history, same eight IDs, [8])`.

The analogous scalar difference uses `[1,1,1,1,1,1,1,1]`. Report mode, repetition, actual physical widths and qualification with each difference. Different q values have different work; this probe does not fit a universal fixed-call constant A from them. A difference here must not be added to draft synchronization as though the terms had independent measured scopes, or inserted into a full-service oracle without a matching service experiment. Two timing repetitions are an integration budget, not sufficient statistical support for a 5% general performance claim.

`summarize_cost.py` replays the raw qualification and computes these two actual differences separately for each history, timing mode and repetition. It refuses incomplete or unqualified q8 groups and reports no admitted cost for failed jobs or q1-only protocol smoke. It makes no regression fit or aggregate speedup claim.

## Inputs and original model binding

`inputs_cpu.json` uses a declared, untrained 128-token F32 fixture with controlled histories at positions 248 and 252. `inputs_cpu_protocol_smoke.json` keeps these histories and requests q1 only. The fixture used by the recorded CPU runs has SHA256:

`e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044`

It is a numerical software fixture, not a trained benchmark model. Model weights are excluded from this repository subtree.

`inputs_public.json` is generated from the authenticated PR213 `LIVE_RECORDS.json` (SHA256 `53d76c43d4b2fa378855b90f76d9bcb60e509d4086fddd630e3c0f51f6197487`). Selection is the first lexicographic `(root,cycle)` in session 0 of `LOCAL-loop4-k7` at each declared base, with no timing-based selection:

| Base | Root | Cycle |
|---|---|---|
| 248 | APPS/train/296 | 11 |
| 255 | APPS/train/603 | 28 |

The token history is reconstructed from the published prompt IDs and prior generated IDs; the pending seed is checked against the cycle record. Inputs are never retokenized or remapped. The continuation is a fixed published decision used as a diagnostic; no claim is made that it is the accepted live continuation after every truncated q.

The runner hard-pins the original Qwen3-8B-Q8_0 GGUF to:

`408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`

All 64 jobs in the authenticated `records/JOB_MANIFEST_LIVE.json` declare that target identity. `MODEL_IDENTITY.json` records the source-member digests. The full GGUF hash also binds its embedded tokenizer. The separate tokenizer metadata receipt has SHA256 `6a5d5b777059e82fb664b418fb59cd2526d1cf65f4b7846892745c84a5124912` and vocabulary size 151936. That receipt hash is not presented as a standalone vocabulary hash. A caller-supplied `--expected-model-sha256` cannot override the original-model pin.

To regenerate public input bytes from the already authenticated raw member:

```bash
python matched_cost/generate_public_inputs.py \
  --records "$HETEROSPEC_PUBLIC_LIVE_RECORDS" \
  --output "$HETEROSPEC_NEW_PUBLIC_INPUTS"
```

The output must be a new path. The checked-in profile SHA256 is `d4ff0a2bf769a322b17a456631d7da5c0813a1f2c82ebd05960a448ed8e3eb0a`.

## Build and execute

Run commands from the experiment directory that contains `matched_cost/`. Use the parent experiment's authenticated preparation workflow to obtain the immutable loop4 core, exact M2 frontend and freshly built native libraries. Set the paths to its prepared outputs:

```bash
export HETEROSPEC_CORE="$HETEROSPEC_PREPARED/sourcekit/native/cores/loop4"
export HETEROSPEC_FRONTEND="$HETEROSPEC_PREPARED/frontend/candidate_frontend"
export HETEROSPEC_LIB_DIR="$HETEROSPEC_PREPARED/numerical_build/bin"
```

Prerequisites are Linux, Python 3.11 or newer, C and C++17 compilers, and the prepared shared libraries. The probe itself has no Python package dependency. Library preparation has its own dependencies described in the parent workflow. There is no hidden dependency on a prior scratch path.

The runner authenticates the numerical source manifest itself, then all 3539 numerical source members and the two exact M2 headers. It compiles only this probe against the existing library; it does not modify the numerical core, frontend headers or old gates. It binds source, inputs, model, compiler invocation, probe executable and native-library hashes in receipts. Dynamic search paths are fixed, preload/audit overrides are rejected, and `/proc/self/maps` checks the actual loaded llama/ggml modules before and after native work. The prepared build receipt provides the numerical library's build provenance.

Inspect the budget without opening a model:

```bash
python matched_cost/run_probe.py \
  --inputs matched_cost/inputs_public.json \
  --output "$HETEROSPEC_FRESH_PLAN_OUTPUT" --plan-only
```

Execute the declared CPU width check with the supplied fixture and a fresh output directory:

```bash
python matched_cost/run_probe.py \
  --core "$HETEROSPEC_CORE" --frontend "$HETEROSPEC_FRONTEND" \
  --lib-dir "$HETEROSPEC_LIB_DIR" --model "$HETEROSPEC_CPU_FIXTURE" \
  --expected-model-sha256 e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044 \
  --inputs matched_cost/inputs_cpu.json \
  --output "$HETEROSPEC_FRESH_CPU_OUTPUT" --backend cpu
```

The recorded CPU width run returned exit 3 at q2. This is a retained scientific qualification failure, not an execution to rerun until it passes. To check only the timing/reset protocol, explicitly substitute `inputs_cpu_protocol_smoke.json` and a different fresh output directory; its success does not qualify a wide action.

For the future original-machine CUDA run, first commit the experiment code and public profile. The runner must live inside that committed experiment subtree. The subtree must be clean, including the tracked runner, C++ source and public profile; unrelated work elsewhere in the repository is permitted. Build outputs and raw outputs should be outside the repository. The actual HEAD and experiment subtree tree SHA are recorded before and after execution.

```bash
python matched_cost/run_probe.py \
  --repo "$HETEROSPEC_REPO" \
  --core "$HETEROSPEC_CORE" --frontend "$HETEROSPEC_FRONTEND" \
  --lib-dir "$HETEROSPEC_LIB_DIR" --model "$HETEROSPEC_TARGET_MODEL" \
  --expected-model-sha256 408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6 \
  --inputs matched_cost/inputs_public.json \
  --output "$HETEROSPEC_FRESH_CUDA_OUTPUT" \
  --backend cuda --gpu-index "$HETEROSPEC_ALLOCATED_GPU_INDEX"
```

The explicit allocated physical GPU index must be greater than zero. GPU0 is excluded. The wrapper queries index, model name, free memory, PCI address, MIG mode and compute PIDs, without querying GPU UUIDs. Physical index and PCI addresses must be unique, and both GPU0 and the requested device must be identifiable. An enabled or unknown selected-device MIG mode is rejected. The requested PCI address must differ from GPU0. The wrapper fixes `CUDA_DEVICE_ORDER=PCI_BUS_ID`, derives the CUDA ordinal from the unique physical PCI ordering, and checks the one visible CUDA driver's PCI address against the requested physical device before loading a model. The mapped CUDA ordinal is recorded separately from the requested physical index; ordinal zero may name a different card, while physical GPU0 remains excluded. The driver identity query does not call context-creation, device-memory-allocation or kernel APIs and has a 15-second timeout. If visibility or ordering does not yield exactly the requested physical device, execution stops; no remapping is guessed. It rejects an already occupied device and requires model-file size plus 4096 MiB free before loading. This is a pre-load screen, not continuous peak-memory measurement. The native probe requires exactly one visible CUDA backend and all model layers/output on that device. No SSH connection, scheduler allocation or automatic remote launch is performed by this directory. The CUDA admission branch itself has not been executed in this CPU-only workspace.

## Finite budget and stopping

| Profile | Phase | Contexts | Native decode calls | Target rows |
|---|---|---:|---:|---:|
| Public, q1..q8 | Qualification | 38 | 444 | 9,789 |
| Public, q1..q8 | Measurement | 152 | 2,588 | 58,658 |
| Public, q1..q8 | Total upper limit | 190 | 3,032 | 68,447 |
| Controlled CPU, q1..q8 | Total upper limit | 190 | 3,032 | 68,048 |
| Controlled CPU, q1 only | Total upper limit | 10 | 136 | 3,524 |

Counts include reference operations, every prefix, continuation, same-shape warmup and reset prefix. They are not merely timed forwards. The C++ ledger distinguishes reserved work from attempted native calls/rows and records stages. Blob output is capped at 2 GiB. Native execution has a fixed **1800-second** deadline, separate from source validation and compilation. At timeout the wrapper kills only its own native child, waits up to five seconds to reap it, preserves partial artifacts, records whether reaping succeeded, exits 124 and does not retry or reset any GPU. A partial result can be absent or malformed and remains evidence of an interrupted run, never a success. Output paths must be new and cannot be symlinks.

## Recorded CPU evidence and software checks

`CPU_WIDTH_FAILURE.json` details the real failure at controlled base248, q2. The initial 510,952 active-sequence bytes and initial geometry match. The actual physical schedules are `[1,1]` and `[2]`. Of 256 operation float words, 242 differ; 43 final active-sequence bytes differ. The continuation differs in 127 of 128 float words and 43 sequence bytes. Initial, final and continuation geometry match. All row argmaxes match, which is insufficient for the declared complete-vector contract. The arithmetic cause was not localized, and this CPU observation does not establish a CUDA failure.

The width attempt consumed 3 contexts, 31 native calls and 752 target rows, with **zero measurement records**. Its 13 unique blobs occupy 3,607,540 bytes. The independent replay verifies the recorded failure; it does not turn it into a qualified action.

The separate q1-only smoke consumed 10 contexts, 136 native calls and 3,524 rows, and produced eight measurement records across the two modes. Its 10 unique blobs occupy 3,104,840 bytes. These CPU durations serve only to exercise software paths and are not GPU evidence or a performance comparison.

The downloadable raw package retains the initial compile failure, the q2 qualification failure, the q1-only smoke, their exact source snapshots, build/run receipts and blobs. The initial compile failure performed zero native work. After the q1 smoke, wrapper-only changes added timeout handling, tracked-profile enforcement, physical-device identity checks and the authenticated original model pin. The final wrapper was checked using host-only tests, including termination of a sleeping owned child and preservation of a truncated result. It has not executed a model or CUDA. The q1 native C++ source is unchanged, and earlier receipts remain bound to their actual executed wrapper snapshots.

`VALIDATION.json` records eight successful host checks and independent blob/accounting replay of both native results. Physical GPU selection is tested with mocked inventory/driver-query outputs; no CUDA driver is executed by those tests. A second reviewer independently checked the raw differences, blob identities, work counts and the q1 protocol modes. To replay supplied raw evidence:

```bash
python matched_cost/verify_run.py "$HETEROSPEC_RAW_ROOT/cpu_f32_attempt02"
python matched_cost/verify_run.py "$HETEROSPEC_RAW_ROOT/cpu_protocol_final"
python matched_cost/summarize_cost.py "$HETEROSPEC_FRESH_CUDA_OUTPUT"
python -B -m unittest discover -s matched_cost -p test_probe_protocol.py -v
```

Use `PR_ALLOWLIST.json` for repository files and `ARTIFACT_ALLOWLIST.json` for retained raw files. Model weights, libraries, executables, caches, raw telemetry and binary captures are excluded from the PR. CUDA qualification and a matched full-service experiment are still required before using any cost difference as evidence for the proposed decoding method.
