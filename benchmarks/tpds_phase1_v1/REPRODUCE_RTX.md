# Reproducing RTX phase1 review-v2

Use the independent result PR195 and its final commit. The scientific design
input is PR192 head `d730902c62042a8f5f2b93bb6941ca6678dc1a5a`; the numerical
reference remains the immutable original C1024 deployment. Read RESULT.md for
the distinct qualification, structural append and persistent-service scopes.

The authenticated private-repository evidence release is
[`tpds-phase1-rtx-review-v2-evidence-20261107`](https://github.com/leecdiang/HeteroSpec/releases/tag/tpds-phase1-rtx-review-v2-evidence-20261107).
Source, numerical dependencies and raw evidence are separate assets. Building
requires the source/runtime assets and installed pinned tools; historical KV
archives and model weights are unnecessary for compilation. Native execution
uses the exact separate GGUF assets in MODEL_ASSETS.json.

```powershell
gh release download tpds-phase1-rtx-review-v2-evidence-20261107 --repo leecdiang/HeteroSpec --pattern 'rtx-phase1-source.zip' --pattern 'rtx-phase1-runtime.zip' --dir evidence
Expand-Archive evidence/rtx-phase1-source.zip source
Expand-Archive evidence/rtx-phase1-runtime.zip runtime-assets
python source/materialize_runtime.py runtime-assets/RUNTIME_MANIFEST.json runtime
python source/portable_rtx.py --sources source/native --out fresh-build --runtime runtime/candidate/bin --zig tools/zig.exe --cmake tools/cmake.exe --ninja tools/ninja.exe --cuda-headers source/deps/nvidia
```

Supply actual tool paths. The original-host proof uses Zig0.16.0, CMake4.4.3 and
Ninja1.13.2; exact executable hashes and the real commands are retained. Both
cores and common frontend compile in a fresh directory. Numerical CUDA/CPU/base
modules are pinned binary dependencies, shared fairly across candidate paths.
The original reference roles keep their own unchanged modules and observer
executables. The fresh-directory source build received its own actual GPU
boundary/vector/active-KV checks on both model structures; the declared scope is
in `host_evidence/host/CLEAN_BUILD_PROOF.json`. It is same-host evidence.

The source asset contains the final native source trees/frontend, the portable
build entry, transitive SDK header inputs, model/module identities and small
input samples. Upstream licenses are retained. MODEL_ASSETS.json links the
official [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B),
[Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B),
[SmolLM2-1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct) and
[SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) cards,
which identify their base-model license as Apache2.0. Exact quantized-file hashes
remain required independently of those names.

`SOURCE_AND_BUILD.json` binds the complete raw compiler closure, original reports,
configuration/response/generated files, toolchain/static link inputs and actually
loaded modules. The raw source snapshot preserves executed bytes; Git text line
ending normalization is accounted for in the independent publication receipt.
The input, schedule and estimand freeze was published and independently read back
before any formal append slot or new Qwen-root forward.

Raw evidence uses numbered ZIP parts and a file/chunk manifest. The restore entry
verifies part, chunk and complete-file hashes and restores into a fresh directory;
original absolute paths are identifiers. Historical original-R prefix evidence
and costs remain an explicit PR190/186 dependency, with verified consumed legacy
payloads also retained in this result. No historical timing is pooled into the
new panels.

Download the raw parts only when their evidence is needed:

```powershell
gh release download tpds-phase1-rtx-review-v2-evidence-20261107 --repo leecdiang/HeteroSpec --pattern 'raw-evidence.zip.*' --pattern 'restore_delivered_host.py' --dir raw
python raw/restore_delivered_host.py raw/raw-evidence.zip.parts.json 'D:\rtx192-review-v2' restored-rtx
```

The source archive excludes uncompiled binary/key test fixtures; the raw archive
excludes model weights, key fixtures and general compiler caches, while explicitly
retaining every frozen compiler dependency. Consumed historical payloads are
hash-verified in `reference-payloads`. Remaining historical original-R evidence
is an explicit [PR190](https://github.com/leecdiang/HeteroSpec/pull/190) dependency,
with its [evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-resident-phase-v1-evidence-20261106),
rather than a hidden prerequisite for building the new source.

`analyze.py structural` consumes the fixed192 append slots; these chosen
inside/crossing coordinates have descriptive comparisons only. `analyze.py burst`
consumes all24 worker records, including48 primers and384 tests, and reports every
fixed target-only M contrast with root-cluster multiplicity handling. It retains
all four shared sessions per root and all six arms. R1 natural is closed by the
source/actual-dispatch review; its absent samples are not missing timing slots.

Recompute the fixed estimands without any model work from this result checkout:

```powershell
python benchmarks/tpds_phase1_v1/analyze.py structural benchmarks/tpds_phase1_v1/host_evidence/host/R1-STRUCT-SCHEDULE.json benchmarks/tpds_phase1_v1/host_evidence/R1-STRUCT/RECORDS.json structural-recomputed.json
python benchmarks/tpds_phase1_v1/analyze.py burst benchmarks/tpds_phase1_v1/host_evidence/R2/WORKERS.json benchmarks/tpds_phase1_v1/host_evidence/R2/RECORDS.json burst-recomputed.json
```

Native service ends at the request return; response-record writing, later module
verification and process cleanup are retained in actual burst/worker/wrapper
clocks. Those inclusive clocks overlap and are not added together. Llama graph
build/reuse counts, CUDA kernel activities and host launch APIs are distinct;
unmeasured CUDA graph/API clocks remain null. Device memory is the observed
device-global2s-sampled peak, with its sampling scope preserved. Unknown nested
phases and partial cost coverage remain null with observed sums/counts.

Supported deployment is the pinned dense single-sequence C1024, F16 K/V, no-FA,
original masks/reservation/termination contract. New binaries or deployments
require their own independent-R qualification. The delivered experiment's fixed
slots and original raw records are immutable; use fresh output directories and
an explicit new resource ledger for a later native reproduction.
