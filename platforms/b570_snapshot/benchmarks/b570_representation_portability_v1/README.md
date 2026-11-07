# B570 representation portability, CPU only

Read [RESULT.md](RESULT.md), [CPU_PLAN.md](CPU_PLAN.md),
[endpoint table](ENDPOINT_RELATIONS.md), [backend map](BACKEND_MAP.json),
[hardware handoff](HARDWARE_HANDOFF.md) and [no GPU request](NO_GPU_REQUEST.md).

This directory is the only addition to fixed PR109 parent
039a24bf61374042e0dc9f3a3619ea40b218a5ad. Existing restores are read-only
dependencies, not automatically downloaded or re-restored. No models are needed.

Quick read-only condition check (Windows Python standard library):

```powershell
python conditions.py
python conditions.py my-declared-operands.json
```

The no-argument example describes a target VERIFY q2 geometry; the output lists
all representations and evidence levels, with no arm selection. All required
input fields are shown by `conditions.example()`. Nonempty mask/state provenance
are declarations, not observed snapshots. The checker is limited to reviewed
D=128, contiguous singleton-batch F16 K/V and F32 masks. Wider/unbound families
are rejected or remain UNKNOWN. It cannot authorize a model/GPU run.

Final closeout (schema_version=2): every numeric descriptor must be an actual
nonnegative int64, not a boolean or float; shapes/strides are four-element JSON
arrays. Invalid roots, missing fields and malformed JSON return structured
errors (CLI exit2), without a traceback. Q alias checking uses a constant-space
row-interval test, so declared head counts do not allocate an address list.

`vulkan_mul_mat_batch3_equal` reports only the reviewed necessary batch3
condition. `vulkan_mul_mat_support` is **false** for a source-proven rejection,
and **null** otherwise: equality does not certify complete Vulkan support.
The batch3 evidence level and full-support evidence level are separate.
Unbound backends and rejected role/phase bindings leave both predicates null.
Backend assignment, CPU operand correspondence, request qualification and cost
remain separate. Historical CHECKER_TESTS.json keeps the earlier field semantics;
CHECKER_CLOSEOUT_TESTS.json records the current checker hash and 13 regression
test methods. Run `python test_checker_closeout.py` in a fresh result workspace
to reproduce these descriptor-only tests; it executes no attention fixtures.

The committed outputs intentionally refuse overwrite (`common.save` uses
exclusive creation). To independently reproduce, copy the source files (`*.py`,
`native/`, CPU_PLAN.md) into a fresh benchmark workspace in a Git checkout and
commit the unchanged generator/plan before execution. Keep these original
results intact. Set configurable paths to the existing PR109 restore and
frozen ggml source, then run from that fresh source directory:

```powershell
$env:HETEROSPEC_GIT = 'C:/path/to/git.exe'
$old = 'C:/path/to/restored/benchmarks/b570_geometry_state_codesign_v1'
$src = 'C:/path/to/frozen/llama-source'
$identity = 'C:/path/to/benchmarks/b570_partition_intervention_v1/BUILD_IDENTITY.json'
python source_audit.py --old $old --source $src --identity $identity
python endpoints.py --old $old
python build.py --old $old --cmake 'C:/Program Files/CMake/bin/cmake.exe'
python run_cpu.py dev
python test_contracts.py
```

Before holdout, save and commit a new RULE_LOCK.json with current dev raw hash,
executable SHA256 and source hashes, using the committed lock here as a schema;
do not copy its executed-binary claims to a new compiler output. Then:

```powershell
python run_cpu.py holdout
python summarize.py
python backend_map.py --old $old --source $src
python check_controls.py
python state_model.py
python monitor.py --old $old
```

This is a reproduction workflow, not a scheduled continuation. Each group
launches one isolated CPU harness, never a model executable. Build copies only
ggml-base.dll/ggml-cpu.dll and unchanged local_attention.h, then links the
frozen base import library. CMake/MSVC2022, frozen ggml headers and nlohmann
headers from the old restore are needed. There is no GPU backend discovery,
Vulkan/CUDA device query or automatic probe. Stop on a failure and retain first
receipts; do not silently retry or relax the oracle. The original numerical
harness was unchanged across all 432 fixtures.
