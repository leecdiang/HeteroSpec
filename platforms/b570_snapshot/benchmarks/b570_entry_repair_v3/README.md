# PR119 entry and review-observer repair

Additive overlay for historical implementation
benchmarks/b570_capability_repair_v2/implementations/6214e73d-2da5-455c-b133-b0d246beb6fd
at 3cf5612d6342fff3648a705775ed914c2106fa29. Historical files/results stay unchanged.

## Evidence audit

All 73 published blobs for that UUID were authenticated by Git blob hash.
The downloaded raw ZIP has 367 members; all 366 manifest entries matched size
and SHA256. The stall supervisor failed importing win before its control point.
The actual review command omitted a workload kind and the captured observer
used a combined 8-process/256MiB-per-process/1.5GiB-total predicate. It raised
command resource budget with ten unresolved identities. The triggering sample
was not saved, so the sole failing subcondition cannot be reconstructed.
The published final observer already had an aux/32 option and a cleanup pump;
that later version was not evidence that the aborted review ran successfully.
Ten missing historical OS exits remain missing.

## Fix and exact launch contract

First copy the original b570_supervision_fix_v2 source/dependencies (including root-level check_receipts.py/ACCEPTANCE.json/BUDGET.json) into legacy/repo/benchmarks/b570_supervision_fix_v2. Then copy the historical implementation as an overlay into a NEW UUID task root under
C:/hs/b570-capability-v1, then overlay this source/ and src/rev2/ tree.
The capability runtime retains the existing guards. Its history intake and auditor additionally recognize typed in-process freeze reservations, validate their actual four journals and mutated bytes, and charge all attempts without demanding a nonexistent watchdog journal. Their caller lifetimes remain separately observed. The other capability sources are unchanged.
Never deploy this directory over an old experiment root. Do not copy old runs,
results, freeze, registries or the compiled DLL into an executable position.

Four entrypoints now install their own source/runtime paths before imports.
Their --startup-check imports the actual runtime plus each entry’s operational dependencies and exits BEFORE parsing
operational arguments, opening journals, making Jobs or launching actors.
Every production entry must use the same deployed root. Startup-check is not
an alias for a successful native gate and cannot be mixed with operational args.

Generate ENTRY_SOURCE_MANIFEST.json over every file in source/ and src/rev2/
after overlay, bind its SHA256 in the prospective startup command. Run:
python.exe -I -B <root>/source/startup_preflight.py --root <root>
  --manifest <root>/ENTRY_SOURCE_MANIFEST.json --manifest-sha256 <digest>
  --output <root>/preflight/STARTUP.json
Use actual absolute approved Python and paths, not a shell command template
containing angle placeholders. The checker really launches each entry using
-I -B from a different, empty working directory, checks exit/JSON/module
origins and authenticates the inventory again. It requires Windows in its
production CLI. The local regression uses a fake backend solely to exercise
real process launch, path-with-spaces and missing-import failures on macOS.

## Review supervision

Use source/review_entry.py --root <root> --id review1 --seconds 900 -- <reviewer argv>.
This always selects observe.py --kind review. Experiment actors retain their
original limit 8/256MiB each/1.5GiB aggregate. Review helpers have a separately
bounded profile: 32 processes, 2GiB each, 4GiB aggregate, observer 512MiB,
maximum 900s. This is a NEW explicitly scoped review-process allowance, not
evidence of old compliance and not permission to raise actor limits.
Reserve sufficient host memory before launching; fail rather than enlarge it.
Tool yield/poll time does not enforce the deadline; the observer does.

Resource membership comes from the OS Job, including nested-debugger descendants;
debug-event lifecycle coverage is reported separately. Each sample records members/RSS/profile and the exact violated limits BEFORE
rejection. The observer still kills its Job on a real limit violation and
pumps debug events to collect OS exits. Pending events are continued before
the failure cleanup pump; retained signalled handles are checked afterward.
Cleanup unknown is never a successful review. Even observer exit0 only means
the reviewer command exited0: independently validate the final review report,
its exact source binding and P0-P2 scoped-clean, not stdout presence alone.

Before a real review, run a native synthetic helper fanout with ten concurrent
children through review_entry and prove observed closure. Also run the same
ten children under case profile and prove expected rejection plus cleanup;
run 33+ total processes under review profile and prove bounded rejection.
These are CPU supervision checks, not review clean and not scientific work.
Any resource trigger must have its raw decision sample and actual exits.
If the host cannot support the registered finite profile, stop; do not bypass
the observer or declare a partial review clean.

## Scope and validation

This repair reviews the entrypoints, observer, stall harness and supporting
capability runtime. The historical full CPU8 adapter has NOT acquired a clean
review by association. Its complete candidate must still be independently
reviewed through the repaired entry before CPU8 freeze or execution.
Local checks cover actual subprocess entry loading with a fixture, policy
boundaries, manifest drift and the original 30 capability regressions.
Native Windows import/Jobs/helper trees/stall remain to be verified on B570.
No repeated three-hour soak, GPU/model/science or paper work is authorized.

Native helper-tree fixture: source/helper_tree.py --folder <fresh path> --children 10 (or 32 for the review boundary). Reconstruct each observer directory with source/check_observer_smoke.py --folder <process directory> --kind review (add --expect-rejection for a rejected case/review boundary). No Boolean smoke report replaces OS exit records.

Full D0 reservations include observed_command smoke runs under processes/. source_guard counts their actual OBSERVER_START. The watchdog actor-history REVISION records are the explicit subset of watchdog and in_process_freeze runs; they are not the complete task ledger.
