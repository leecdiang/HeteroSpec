# e03 frontend identity and profile preparation

Final prepared frontend source is `source-v4`; both graph-core variants compile
and link in `build-v4`. Normal numerical DLL loading is deliberately blocked
before backend, context or model initialization. There is no authenticated
parent launch intent, and universal physical-kernel launch coverage has not
been qualified. Neither a job boolean nor a claimed metadata kind releases
that gate. This is not a GPU qualification or performance result.

The inherited v7 vector/state/timeline/owner hooks remain unchanged. Their
valid host results are reused without rerunning the old 41/18 suites or v7
selftests. New profile/gate tests invoke only the early `--e03-preflight` and
`--e03-native-gate` branches.

## Fixed entry/profile blockers

The inherited M1 capability allowlist omitted the new evidence capture fields,
while its unconditional real-D4 check also rejected target-only work. The new
entry checks an explicit profile before reading model/draft-dependent fields:

| Profile | Prepared contract |
| --- | --- |
| `m2_dynamic_request` | Retains actual resident draft, D4, k3/7, reserve8 and live request inputs. It does not bypass the original M2 requirements. |
| `target_q8_capture` | Dedicated target-only A/B operand oracle, no unused draft identities, actual q8 requested verification inputs and non-derived capture descriptor. Its capability receipt explicitly excludes M2/service qualification. |

C uses the same admitted A/B operand for replay; it cannot relabel itself as an
A/B capture oracle. A C M2 schema can be checked structurally, but eligibility,
fallback qualification, exactness and service value remain unexecuted.

The future isolated loader checks the frozen DLL directory/hash allowlist,
rejects an already resolved foreign numerical module, verifies actual loaded
paths and disk hashes, reads metadata, selects A/B/C with readback, and looks
up budget Configure/Metadata/Snapshot ABI1. Selector success is 0; budget
success is 1. Native Configure currently returns -6 and must be refused before
backend/context/model work. The current unconditional preload gate prevents
all of these normal numerical loading operations from being reached.

Do not describe the prepared C++ helper as a live parent authorization channel.
Do not describe a selector readback or branch-attempt counter as a submitted
or completed CUDA kernel. Loaded-path disk hashes are not memory hashes.

## Actual DLL disk evidence and load boundary

`NUMERICAL_DLL_PE_IDENTITY.json` reads the actual newly linked DLL from disk
without mapping it:

`runtime/build-v3/bin/ggml-cuda.dll`, 33,850,880 bytes,
SHA-256 `bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b`.

The expected metadata, arm and budget exports exist. Imports include CUDART,
cuBLAS and `__cudaRegisterFatBinary`/Function/Var. Ordinary `LoadLibrary` runs
DLL/CRT initialization; calling only the later literal metadata function is
not sufficient evidence that loading the numerical DLL is CUDA-free. Normal
numerical loading remains `NOT_RUN`; no actual numeric route is claimed.

`pe_identity.py` also records import symbols, exports, sections and TLS presence.
This is offline PE/disk identity only. It does not call the exported functions.

## Focused tests and their limits

- `preflight-tests-v4/RESULT.json`: 22 **CPU schema/gate fixture cases**, including
  nonempty actual-q8 input shape, missing draft, wrong graph core/device,
  unbound fields, invalid budget count types, cap overflow and hard native
  refusal. These are not the 22 native numerical qualification cases.
- `cpu-loader-test-v1/RESULT.json`: one actual Windows load of a separately
  built CPU-only stand-in, metadata/path/hash checks and two pre-load refusals.
- `foreign-resolution-test-v1/RESULT.json`: another own CPU stand-in tests an
  already loaded same-basename foreign path. Only the test's own handle is
  unloaded; no unknown or other-user module is altered.
- `RECEIPT_TESTS_v2.json`: six new adversarial receipt-reader tests pass normally
  and under `-O`. A kind string is recorded as a claim; it cannot independently
  prove an OS numerical-DLL load or numeric route.

The two CPU stand-in DLL loads do not qualify the actual numerical DLL. Model
requests, target/draft rows, CUDA DLL normal loads and GPU launches are all 0.
All original 66 native qualification cells and all performance/request claims
remain `NOT_RUN`.

Rebuild the source without invoking a native job:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B continuation/frontend/direct_build.py --frontend e03/frontend/source-v4 --out e03/frontend/review-rebuild
```

The original private numerical archives and CRT/libc++ inputs remain read-only
hash-bound dependencies. The new numerical backend DLL is separately built;
it was not silently substituted into an old qualified executable or panel.
