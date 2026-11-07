# B570 QB batch-broadcast fix and minimal crossover

Result: EXPLORATORY_ALL_PASS on Intel Arc B570, driver 32.0.101.9034. All nine coordinates, each with QB and QH_C, passed actual Vulkan support, independent FP64 numerical checks, then short timing. This is a scoped exploratory result; CPU8 remains unchanged at 0/8, no F0.

## Actual source change

The baseline Vulkan C++ source SHA256 is 04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d. Its mat-vec shader already has broadcast3 indexing, and its backend already stages noncontiguous Q. The old supports_op predicate rejected unequal source batch dimensions before those paths could run.

qb-batch-broadcast-portable.patch changes only that predicate. It admits plain MUL_MAT for contiguous F16 source A, F32 source B with one column, equal head dimension, A.batch=1 and B.batch=2 or 4. Other mismatched batches remain rejected. The existing nc/p021 paths are not selected for this allowance because A must be contiguous.

No shader change, K/V repeat, graph substitution, padding or CPU graph fallback was used. The unchanged query_head.h builds QB and QH_C. The harness asserts the original K and V object identities and rejects any REPEAT graph node. Existing backend Q staging is included in graph timing.

Candidate C++ SHA256: c16de703ff610cb10d4f4b19b64a1f4bb2e36ad57047b1443b718725da939576.
Candidate Vulkan DLL SHA256: 79b0031bea367da64a8f580f1b00fe1108c83cc2ab73e893739d9740e4408423.

The C++ dispatch/support source was compiled anew and linked with 147 unchanged precompiled shader objects from the frozen local build. BUILD_MANIFEST.json records each object hash. This was not a fresh compilation of GLSL.

## Numerical scope and evidence

H=Hkv=8, D=Dv=128, compact F32 Q, F16 K/V, exact key extents 1023/1024/1025, q=1/2/4. Dyadic inputs differ across heads and queries. Query j may attend keys t <= key-q+j; later positions have a negative-infinity mask.

All eighteen graphs passed supports_op before any numerical graph ran. Each graph then passed QK, softmax, AV and final comparisons against serial FP64 loops, plus byte identity of input readbacks. Each coordinate passed QB/QH_C final equivalence before the timing phase began. Tolerance was frozen before execution: abs_error <= 0.0002 + 0.002*abs(reference).

Observed maximum absolute errors across all eighteen mode slots:
- QK: 0
- softmax: 2.842759241981213e-10
- final: 7.691786333297729e-10
- QB versus QH_C final: byte-identical at all nine coordinates

CPU-only verify_raw.py independently loaded the saved raw F16 operands, recomputed with NumPy FP64 einsum, and passed 90 stage checks and 216 input-readback identities. No GPU backend is loaded by that script. CPU_RAW_RECHECK.json and cpu-recheck.log retain its results.

This qualifies only these fixed inputs, geometry, layouts and candidate runtime. It does not establish GQA, permuted-Q, general numerical stability or other hardware support.

## Short timing

All support and numerical gates passed first. Each mode received two warmups and ten measured calls. Paired measurement alternated QB/QH_C and QH_C/QB across rounds. Values below are medians in microseconds.

| key | q | QB | QH_C |
|---|---:|---:|---:|
| 1023 | 1 | 122.05 | 133.95 |
| 1023 | 2 | 125.65 | 145.00 |
| 1023 | 4 | 137.65 | 157.80 |
| 1024 | 1 | 129.50 | 145.60 |
| 1024 | 2 | 118.95 | 133.30 |
| 1024 | 4 | 138.15 | 156.25 |
| 1025 | 1 | 118.95 | 122.15 |
| 1025 | 2 | 130.40 | 133.95 |
| 1025 | 4 | 152.10 | 154.30 |

Timing is host steady-clock graph compute plus explicit synchronization with resident operands, including any backend Q staging. It excludes explicit upload, readback, allocation and CPU reference. It is not GPU timestamp timing or model latency.

QH_C had no lower sample median in this short run. This does not establish a stable ordering: q=1 uses the identical common graph but still exhibits timing differences, and only ten samples were taken. The largest QH_C sample was 1.1913 ms at key=1023,q=4. Every sample is retained in results/result.json.

First-graph initialization was retained separately, including 850.8664 ms for QB at 1023/q1, 171.0923 ms at 1024/q1, and 750.2011 ms at 1025/q1. These cache/initialization costs were charged to the total wall budget and must not be compared as paired cold-start performance.

## Budget and cleanup

PID 42648 started at 2026-10-20T06:17:22.1635806Z and exited at 2026-10-20T06:17:25.1480718Z with exit code 0. The parent observed exit and captured complete stdout/stderr. Normal backend/context cleanup returned.

This attempt charged 3.012652 seconds of entire GPU-program parent wall, including initialization, reference CPU work, raw-file I/O and cleanup. Prior charge remains 1.7474647 seconds. Cumulative charge is 4.7601167 / 300 seconds; 295.2398833 seconds remain. No retry or subsequent GPU execution occurred.

Historical evidence remains at C:/hs/b570-qb-q1-smoke-20261020053419 and C:/hs/b570-qb-qhc-cross-20261020054700. The unsupported original QB result is not rewritten as a PASS. This candidate is a separate runtime.

## Retained artifacts and reproduction

All 451 raw result files (321,408,442 bytes) are retained under C:/hs/b570-qb-broadcast-20261020061400/results. FINAL_MANIFEST.json hashes the raw results and selected source, binary, log and receipt files; compiler intermediates are excluded. BUILD_MANIFEST.json pins pre-start sources, headers, runtime and all reused shader objects. Its recorded files were rechecked after execution.

The repository copy contains the portable patch, harness, frozen local build recipe, preregistration, CPU recheck script, result summary and evidence manifests. It excludes the large raw tensor files and DLLs, which remain at the paths recorded above.

To reconstruct the source candidate without running a GPU program:
1. Check the baseline ggml-vulkan.cpp against the SHA256 above in an isolated source copy.
2. From that source root, apply qb-batch-broadcast-portable.patch with git apply, then copy the resulting ggml-vulkan.cpp beside CMakeLists.txt.
3. The recorded CMakeLists.txt refers to the frozen local headers, import library and 147 shader objects. Recheck BUILD_MANIFEST.json before using those inputs.
4. Configure with Visual Studio 17 2022 x64 and build targets ggml-vulkan and cross in Release. These are CPU compilation steps.

RUN.ps1 is retained as the historical invocation, with the original pre-run charge frozen in its receipt contract. It must not be reused to reset accounting. Any future execution needs a new directory and must carry forward 4.7601167 seconds of cumulative charge.

No models, actor, RTL or CPU8 execution occurred. No framework expansion or merge was made.
