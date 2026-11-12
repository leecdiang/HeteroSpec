# E03: C is linked into the numerical CUDA backend

The final numerical module is `build-v3/bin/ggml-cuda.dll`, SHA-256
`bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b`.
It links the original CUDA operator implementations, the new same-CTA pair4
kernel and explicit runtime A/B/C selection. This is an actual numerical DLL,
not a metadata stand-in or an isolated MMVQ object. It has **not** been normally
loaded, initialized, used for a model, or numerically qualified.

A requires the existing loop4 graph-building core. B and C require the packed
graph-building core. C dispatches only the admitted Q8_0/F32 physical `[K,4,2]`
node with eight rows, contiguous same-device allocations, no K padding, no IDs
or fusion, default precision and SM120 warp32 case4 geometry. The kernel keeps
two independent four-column accumulator groups and the original K/lane/reduce
organization. Checks occur before that operator's original quantizer.
Ordinary packed paths outside C's subdomain remain explicitly unqualified in
the new module; their source existence is not an approved fallback.

`hs_e03_select_arm(0/1/2)` selects A/B/C once per process and returns 0 on
success, 2 on an invalid value and 3 for a conflicting later selection. Metadata
and selector exports contain no explicit CUDA calls. However normal loading of
a CUDA-containing DLL may execute CUDA runtime/fatbinary registration, so
metadata-only function bodies do not establish a zero-CUDA loader path.
`RUNTIME_METADATA_EXPECTED.json` binds the intended pure metadata values.

Dispatch counters and their `*_dispatch_attempts` aliases observe branch
attempts before the launch guard. They are not submitted/completed kernels.
`hs_e03_failure_code/message` retain the first C++ failure caught inside this
DLL's graph callback, which returns `GGML_STATUS_FAILED` across the C ABI.
This avoids relying on a MSVC C++ exception crossing into the GNU/libc++ worker.
Other allocator/model-transfer failures are not generally recoverable. The
final launch-budget denial exports use explicit own-process failstop instead
of throwing through a C ABI.

The launch provider is process-shared across all translation units and is
compiled exactly once from the final canonical implementation. Native arming
still returns `-6`: all physical work, including runtime/library internal work,
has not been qualified within the 4096-launch family cap. CUDA graphs, NCCL and
PDL are disabled in the supported profile; NO_VMM is enabled consistently.
No GPU/model/context/kernel execution occurred in this continuation.

## Build and source identities

`build-v1/` preserves a complete 145-unit batch: 144 compilations succeeded;
the MMVQ guard failed because it accessed an incomplete private buffer type.
`build-v2/` preserves the staged include-path failure. `build-v3/` fixes the
public buffer accessor and include search, adds the DLL-local error boundary,
and links 141 hash-bound successful objects with four freshly compiled objects.
The final provider is canonical SHA-256
`07f4b16222dc260491592a1f9369ecd829fdb393a1f6991f40eb17647882439c`,
without `HS_LB_CPU_TEST_ONLY`.

The old provider copy was synchronized during the first batch. Its exact sync
time was not recorded; the catalog time is only an approximate bound. The old
body is preserved and its first-batch object is not linked into the final DLL.
The 141 reused object bytes and the recorded 283-member CUDA source/header
catalog remain bound, apart from the superseded provider body. The original
and current full-tree manifests also cover non-CUDA `.h` files, but there is no
exhaustive per-compiler dependency transcript or independent compile-start
rehash of every such target header. `AS_BUILT_BINDINGS_FINAL.json` records
this limit and the two declaration-only budget
header versions and the source-sync deviation; it does not claim a globally
frozen first batch or universally byte-identical compiler output.

`delta-v2/OVERRIDES.json` maps the 66 changed/new source files onto the exact
3540-member original core. The delta is about 1.2 MB. The complete original
source tree need not be duplicated in Git. Reconstruct a fresh source directory:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' runtime/materialize_final_source.py --old-core 'D:/rtx192-review-v2/native-v2/cores/packed' --delta runtime/delta-v2 --out runtime/reconstructed-review
```

The helper hashes every original member and delta before writing and hashes
the resulting tree. It never changes the old core. `final-source/` is the
consistent source for a fresh rebuild, including one current budget provider
and one runtime C++ source-list entry. The supported direct compiler entry is:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' runtime/build_runtime.py --source reconstructed-review --out rebuild-review --jobs 2
```

This compiles and links but never loads the DLL. The exact compiler/link flags,
recorded source/member hashes, object bindings, old import-library hashes and failure
logs are retained. Ordinary DLL loading, native qualification, the 66-case
matrix, the real request chain and all GPU performance remain `NOT_RUN`.
