# Prelaunch counter prototype: numeric admission remains blocked

This is a deliberately narrow, source-visible launch guard. It does **not**
prove the original 4,096 ceiling for all physical GPU kernels. The native
`hs_launch_budget_configure_v1` returns `-6` and cannot arm a numeric worker.
No environment flag, JSON receipt or reset API overrides that decision.

One `hs_launch_budget.cpp` implementation object supplies shared atomic state
to every transformed translation unit in the one hash-bound CUDA DLL. The
header contains no private per-TU counter. Compare-and-swap reserves one slot
**before** a visible launch; the first 4,096 mock attempts can be admitted and
the next cannot. Configuration binds the inherited family charge and this
worker's reservation. Failed submissions remain charged; reconfiguration,
reentry and subsequent work after a terminal refusal are rejected.

`transform_launches.py` instrumented the new private CUDA source copy only.
The initial catalog contains 168 raw triple-chevron sites and one actual
`cudaLaunchKernelEx` site. These are **source sites, not a dynamic count or a
minimum physical workload**. A shared helper's PDL API branch and raw fallback
branch receive separate guards; its entry is not additionally charged.

Graph execution/capture, cooperative launches, CUDA host callbacks, cuBLAS
calls (including lazy initialization), NCCL, CUB device-wide operations and
selected opaque memory/driver routes receive a refusal before the original
call. Graphs and NCCL must also be disabled at build time and VMM disabled.
The same graph/opaque-route policy must bind A, B, C, draft and any newly
instrumented reference. It changes the deployment policy and therefore needs
fresh numerical qualification. A denied operation is not a qualified fallback.

The catalog also retains **149 unresolved runtime call sites**. For example,
memory allocation/initialization/copy APIs or driver/vendor internals may
perform GPU work not represented by the source-visible launch syntax. Calls
through unexamined aliases or opaque libraries cannot be certified by this
lexical transform. For this reason all-physical-kernel coverage and actual
model usability are `NOT_QUALIFIED / NOT_RUN`. Some explicit denials, such as
memory-copy refusal, can make the narrow profile unusable at model load. No
full-model support follows from compiling this prototype.

The denial functions use **own-process fail-stop**, not C++ exceptions across
the GNU/MSVC boundary. MSVC `/EHsc` treats C linkage calls as not throwing;
the first CPU mock exposed corrupted unwind state when a C export threw.
That failed source/output is retained in `cpu-checks-v1`. The corrected C APIs
return status for host inspection, while instrumented void guards call
`TerminateProcess(GetCurrentProcess(), reason)` before the denied CUDA call.
The parent supervisor must preserve the reservation and unknown actual cost;
this is not a recoverable reusable-owner API contract.

`cpu-checks-v3` contains 16 independently invoked, CUDA-free C++ scenarios:
unarmed/invalid configuration, exact boundary, multithreaded boundary, two
translation units sharing one provider, inherited reservation, failed submit
without refund, prelaunch ordering, reset/reentry refusal, graph replay,
BLAS/CUB opacity, zero remaining budget and two exact fail-stop exits before
the mock driver body. The individual cases pass. Its original summary flag
incorrectly demanded exit0 even for intentional fail-stop cases;
`CPU_RESULT_RECHECK.json` rechecks the original recorded results and fixes
only the aggregate interpretation, without replay. A subsequent fresh
`cpu-checks-v4/RECEIPT.json` rebuild and 16-case run has `all_pass=true`, with
both intentional nonzero exit statuses checked exactly. The reusable script's
aggregator is corrected. An intermediate
Windows `OPAQUE` macro collision compile failure is retained in v2.

The mock executable imports no CUDA library and executes no GPU kernel.
`native-host-standin-v1` separately compiles the default native-blocked branch
into another CUDA-free host executable; this is not the actual numeric DLL.
Six Python transform tests check masking, config parsing, disjoint wrapper
paths, opaque denial and honest unknown runtime classification.

Reproduce only in fresh output directories:

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B e03/launch_budget/build_cpu_mocks.py cpu-checks-new
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B -m unittest discover -s tests -p test_e03_launch_transform.py -v
```

Exactly one provider object must be linked. The manual runtime build compiles
the canonical `.cpp` once; the generated `runtime/source/.../hs_launch_budget.cu`
is for the alternative CMake glob route and must not also be compiled into
that same DLL. Existing CUDA TUs can use the earlier ABI-identical header;
the canonical header adds an unused nonthrowing test/status helper. Both
header identities and the provider source are recorded separately.
