# Dynamic frontend build repair and native evidence hooks

The dynamic loop4 and packed frontends now compile and link. Final sources are
in `hooked_frontend_v7`; final binaries, exact commands, input hashes and logs
are bound by `hooked-build-v5/BUILD.json`. Both binaries pass the early
`--selftest` path, which returns before backend loading, device enumeration or
model initialization. This is a host helper test, not native numerical
qualification. No model request, target/draft row or GPU launch occurred.

## Diagnosed failure and repair

`request/timeline.hpp` is 1,157 bytes of valid UTF-8, begins with `#pragma once`,
has no NUL and matches its inherited SHA-256. Its contents and actual include
paths were inspected. The old `timeline.hpp:1:1: Unexpected` is not a demonstrated
C++ syntax or encoding error: a new minimal `int value(){return 17;}` source
fails with the same `Unexpected` under both file and stdin `zig c++`, whereas
the same binary's `zig clang` compiles it. Direct Clang also compiles the actual
timeline header and dynamic frontend. A subsequent wrapper link attempted to
rebuild CRT/libc++ inputs and failed with the same error across their sources.
The exact internal cause of the Zig wrapper failure remains unproven.

The working path uses the same pinned Zig 0.16.0 binary's Clang driver with
explicit Windows GNU target, libc++ ABI/configuration and include paths, then
its internal `lld-link` with the exact previously compiled CRT/libc++ inputs
from the original successful linker trace. Those archives are read-only and
hash-bound. Neither old caches nor numerical core sources/libraries are
modified. The new compiler invocation is separately identified; old native
qualification is not inherited by the new frontend binary.

Rebuild in a fresh e02 directory:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B continuation/frontend/direct_build.py --frontend continuation/frontend/hooked_frontend_v7 --out continuation/frontend/review-rebuild
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B continuation/frontend/run_selftest.py continuation/frontend/review-rebuild
```

The script rejects frontend/output paths outside this independent workspace.
It snapshots executed build/source inputs, preserves every failed build and
does not invoke a model-bearing job. The original read-only private source
kit, cached runtime archives and toolchain remain dependencies, not packaged
model/runtime redistributions.

## Hooked source behavior

- Capture every originally requested complete target/draft vector immediately
  after decode, including the final draft output that is not sampled.
- Capture native target/draft sequence bytes and actual dense geometry at
  initial, pre-verify, speculative untrimmed, committed and terminal stages.
  `physical_head` is reported only when the native append guard establishes
  equality; its proof basis is explicit.
- Invalidate request owners after failures in decode, reset, sampling, trim,
  snapshot or reconciliation. A request-wide guard covers exceptions outside
  an individual method. Raw pointers are cleared before fresh context teardown.
- Record one enclosing service timeline beginning before reset/admission work,
  with planning, guard, prefill, draft/verify, synchronization, reconciliation,
  state and sampling spans. Capture-heavy partitions remain diagnostic and
  cannot admit clean service comparisons.
- Require a positive capture-byte reservation no larger than 2 GiB before
  backend/model setup. A shared counter reserves before binary and JSON writes,
  including old metadata and actual-q8 operand captures, without refunds on
  failed writes. The parent runner must separately bound stdout and other work.
- Preserve loaded-path inventories and add disk hash inventories for the
  loaded module paths, executable and models. A disk hash is not a memory hash.

`HOOKS_README.md` and `read_hooks.py` define the new offline evidence schema.
The reader requires an independently frozen full row/stage/vocabulary/KV
contract. It does not turn capture observations into always-on clean guards.

## Evidence retained and remaining gates

`diagnostic-v1` retains the minimal wrapper/direct-driver comparison;
`direct-v1` retains the failed wrapper CRT link; `direct-v2` proves the initial
dynamic source builds. Hook source/build versions retain the independent UAF
finding and its fix. The final `HOST_SELFTEST.json` records owner invalidation,
nested timeline and exact byte-cap boundary checks. It also exercises the actual
JSON dump on one fresh file per binary: each contains 109 UTF-8 bytes, 11 LF
and zero CRLF; physical, encoded, reserved and written counts agree, and an
additional byte is refused. Old text-mode and corrected binary-mode source
versions remain separately identified. Two focused diagnostic
cost-reader tests originally passed normally and under `-O`; a third focused
crossing-interval refusal test is retained in the additive v2 test receipt. The inherited 41-test suite
was not rerun here.

Native state/vector replay, geometry/readback on a real request, actual loaded
DLL observations, true q8 operands, always-on actual dispatch qualification,
the C runtime integration and complete service endpoint admission remain
unexecuted. The standalone kernel/quantizer backend hooks prepared by the
native agent are not silently treated as installed in the unchanged DLLs.
