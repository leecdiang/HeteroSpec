# Native implementation and host execution, 2026-10-28

The registered PLAN/PANEL/SLOTS and historical experiment bytes are unchanged.
This implementation supersedes the original handoff's statement that no new
worker exists. Build success and resident resource admission are not numerical
qualification. See `host_execution/EXECUTION_IDENTITY.json` for the committed
execution cohort, dates and resource limits; results are recorded separately.

The qualification closeout is `host_execution/QUALIFICATION_STATUS.json`:
Qwen 98/98 and SmolLM2 98/98 are numerically qualified. The SmolLM2 CPU audit
needed the source-grounded name correction documented in
[AUDIT_METADATA_CORRECTION.md](AUDIT_METADATA_CORRECTION.md). Its initial refusal
is retained; neither raw bytes nor native requests were changed or repeated.
The qualification closeout and first-unit closeout are historical snapshots.
All four formal date0 units have now completed 28 warmups and 336 measurements
on October 30 under the user-authorized
[calendar amendment](CALENDAR_AMENDMENT.md). Current day0 status is recorded in
`host_execution/day0/DAY0_STATUS.json`; both families ran in two separately
loaded processes and all processes exited normally.
There is no complete three-date performance estimate. The raw bundle is retained
locally with committed payload manifests. The completed main-through-day0 and
54-request diagnostic increment is now remotely archived and download-verified;
see [the archive receipt](sidecar_execution/archives/README.md). Future dates
remain pending and must be archived as separate increments.

## Implemented

- `arm_spec.h` admits exactly the seven registered arms and source-family routes.
- `worker.cpp` provisions independent R/GS/PQ/QB target pools before requests,
  with three scope-specific draft pools. M never calls a draft context. Scope is
  restored on every target/draft decode; M/C share only a cleared same-scope
  target. R uses UB1/output1. GS uses selector2 with UB4/output4 and physical
  serialization in the pinned core. Both model weights stay loaded.
- Observer metadata covers prefill, ordinary generation and verification, with
  phase-specific measured width histograms. Baseline execution uses the source's
  existing callback-off gate. Full vectors, all speculative decision rows and
  canonical transactions remain retained. File serialization and host comparison
  occur outside the resident service clock.
- `build_native.py` verifies every source member against the pinned archive,
  builds all core objects into a fresh directory, changes only the dynamic
  selector header, then links the new worker. It verifies the exact delivered
  21-library inventory. Original and metadata4 are separate build cohorts.
- `admit_host.py` verifies actual assets and loads all pools without generating
  tokens. This is resource admission only. `prepare_host.py` recovers all 24
  historical R records against PR144's committed raw-file manifest and prepares
  the host binding. `host.py` requires a committed identity/source freeze and
  consumes only an exact frozen unit. It checks date and resource limits and
  waits for each retained native record before acknowledging the next request.
- `qualify.py` reuses the public auditor's complete native-row validation, then
  requires all 98 qualification slots, PQ/QB vector/state equality and off/on
  sentinels. Formal execution is blocked without this gate.

## Commands

All commands run from the repository root with Python 3.11+. Build and resource
admission commands print their required paths through `--help`; no legacy bridge
command or guessed native runtime is used.

```text
python -B scripts/experiments/rtx_scope_transfer_v1/test_cpu.py
python -B scripts/experiments/rtx_scope_transfer_v1/test_host.py
python -B scripts/experiments/rtx_scope_transfer_v1/build_native.py --help
python -B scripts/experiments/rtx_scope_transfer_v1/admit_host.py --help
python -B scripts/experiments/rtx_scope_transfer_v1/prepare_host.py --help
python -B scripts/experiments/rtx_scope_transfer_v1/host.py --bundle ABSOLUTE_BUNDLE --unit qualification/Qwen
```

`FREEZE_COMMIT.json` in the retained bundle must identify the committed execution
identity and a map of all runner/worker/scientific-source file hashes. Local asset
paths belong in `LOCAL_PATHS.json`; changing one still requires the original
content hashes. An interrupted attempt cannot be restarted with the same unit
name. The current host command implements attempt0 only: the optional technical
retry reserve is not automatically spent or silently reassigned.

## Remaining boundaries

Three real dates and both daily sessions must finish before performance claims.
The separate registered Llama stream has completed and audited all 54 requests;
see [sidecar_execution/README.md](sidecar_execution/README.md). It remains outside
the factorial auditor. Checkpoint transfer, additional replay, repair searches
and numerical retries remain disabled. The raw native admission records and
build receipts are evidence of resource/build status only. Incremental archive
and downloaded-member readback receipts are maintained with the sidecar evidence.

The initial CPU `check-plan` status describes the unchanged registration package;
it is not a live execution-status endpoint. Use retained attempts, qualification
receipts and the public `audit`/`analyze` outputs for new execution status.
