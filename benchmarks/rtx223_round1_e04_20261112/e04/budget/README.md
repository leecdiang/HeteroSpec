# Whole-lifecycle budget planner and CPU-only lease controller

**Native admission remains BLOCKED.** The original ceiling is 4,096 physical
GPU kernels for the same first-round family, not 4,096 per epoch, process,
model, or API. The current implementation proves conditional planning and
mock-controller properties; it is not a GPU interceptor and does not fill
the missing native coverage proof.

`lifecycle_budget.py` has no CUDA import, numerical DLL loader or native
worker launcher. Its production proof registry is empty and has no JSON
registration path. `inspect_native_candidate.py` demonstrates that an
entirely self-issued manifest, including zero-work claims, is refused before
worker/bootstrap or normal numerical DLL loading. The proven full-lifecycle
bound remains `null`; partial source-site counts are not a substitute.

The executable CPU controller is deliberately a separate `CPU_MOCK_ONLY`
capability. Its certificates are scoped to phase, route, kind and artifact
hash. They describe only deterministic fake work, and cannot be transferred
to native admission. No manifest, planner ledger or post-run statistic is
described as real physical-kernel interception.

## What the planner actually does

All 18 phases must appear exactly once, in order: worker bootstrap; numerical
DLL load; CUDA context initialization; library initialization; target/draft
model loads; target/draft KV initialization; transfers; warmup; target/draft
prefill; draft generation; target verification; reconciliation; capture;
error cleanup; teardown. Empty or missing phases are refused. Explicit zero
work still requires a valid phase-specific certificate. Both successful and
failure cleanup capacity is reserved conservatively before any phase entry.

The complete bound is the sum of all certified phase upper bounds, including
initialization, hidden library work and cleanup. That sum must fit the same
family's remaining allowance. The planner does not infer that any API costs
zero kernels or one kernel. A wrapper certificate covers its own overhead
and its explicit child kernel nodes without double counting. A static graph
bound expands its kernel nodes and nested child graphs, then multiplies by
the admitted finite replay count. Each root replay receives a distinct
one-use step identity. Cycles, graph WHILE/conditional/device launches,
host callbacks and unknown external work are rejected by this narrow model.
Current native graphs remain OFF; mock graph support changes no native policy.

`MockFamilyLedger` reserves the full certified lifecycle before the first
simulated bootstrap/load operation. A new epoch reopens the same family
state; it does not renew the allowance. Pending/unclosed leases require a
separate recovery protocol and cannot be cleared by poststats. Failed leases
remain charged, retries are blocked, and no observation refunds unused
reservation. An unexpected observed mock overrun is retained, charged above
the reservation and stops the family; it is not dropped or clamped.

`MockController` checks plan identity, owner PID/thread, step order and
reentry. Its backend calls the quota check **before each simulated kernel
primitive**, including injected library/replay work. Fault injection that
tries to emit an extra primitive is stopped before that fake emission.
Already-reserved error cleanup is used on a failure; no new allowance is
created at that point. This is CPU simulation, not an assertion about a
NVIDIA library's internal execution.

Mock DBs require a dedicated `CPU-MOCK-...` workspace, a bounded resolved
path, no reparse/symlink/hardlink alias and an existing marked mock schema and
family binding before any writable SQLite open. They cannot be pointed at
the canonical GPU ledger through the normal API. These checks protect the
owned fixture paths; they are not a formal defense against a hostile process
of the same Windows account racing filesystem replacement. No production
ledger is opened or changed by this work.

## Four quantities that remain separate

| Quantity | Meaning | Current native status |
| --- | --- | --- |
| Prebound upper limit | Independently justified maximum physical kernels for every route and phase | Unavailable; complete bound is unknown |
| Reservation | Conservative debit from the unchanged first-round family before work | Native reservation not issued |
| Enforcement | A mechanism that refuses every possible physical launch before execution, including opaque/init paths | Not established by this planner or e03 source guards |
| Actual observations | Validated post-run records and their completeness/loss status | Native NOT_RUN; cannot retroactively grant permission or refund reservation |

The former e03 168 raw sites and one Ex API site remain static code facts.
Its 149 unresolved runtime occurrences are not 149 physical kernels or a
minimum workload. A CPU mock count of 4,096 is not a GPU observation.

## Reproduce only the new CPU work

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B e04/budget/run_cpu_checks.py cpu-checks-new
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B e04/budget/inspect_native_candidate.py NATIVE_PREFLIGHT_NEW.json
```

`cpu-checks-v4` is the final producer receipt. Earlier v1/v2/v3 sources,
receipts and own mock ledgers remain. Independent review found and prompted
the dedicated-root/DB-alias checks, pending-lease refusal and SHA grammar
fixes. The alias test uses only a harmless owned sentinel, never the real
canonical ledger. Hardlink refusal was exercised; the symlink creation
fixture was refused by Windows privilege policy and is explicitly noted as
not executed. Old e01/e02/e03 suites were not rerun. Normal numerical
LoadLibrary, CUDA calls, model requests, target/draft rows and GPU launches
are all zero.
