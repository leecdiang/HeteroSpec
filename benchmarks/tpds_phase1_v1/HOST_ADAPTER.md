# Original-host integration map

This document separates implemented portable tools from native work. Do not
interpret synthetic fixtures, stager output or a successful compilation as model
qualification. Do not hand the author another plan instead of original-host work.

## RTX: use the real final PR190 implementation

Pin a28f3474acac793d07b6e6f462cb70bbccfa6ceb. Entry points:
- `benchmarks/rtx_phase_plan_v1/host.py`: source staging/build and original execution.
- `native/resident_context.hpp`: `phase_lowering` chooses whole vs local caller;
  original requested outputs are owned before the next native call overwrites them.
- `native/phase_entry.cpp`: common original request implementation, one provisioned
  model/context pool and ordered `job.inputs`. Sixteen sequential requests therefore
  do not require a new inference engine.
- `qualification.py`, `confirmation_analysis.py`, `host_evidence/confirmation/PLAN.json`:
  independent original-R bridges, finite state/vector scope and exact final sources.
- PR186 e8f1ea5aaa35789216801dd971b17e7d5e9f090f: strong loop4 arithmetic control.

The final core behind SIMPLE is loop4 and behind LOCAL is packed. Decouple that
build choice from the runtime `lowering` job field. W_P is packed core with SIMPLE
caller; L_L4 is loop4 core with LOCAL caller. Keep the same shared frontend,
backend/placement guards, output masks, graph reuse, profiling flag and compilation
options. Audit the complete core diff: if any non-projection numerical difference
remains, normalize it or state that the intended factor separation is not obtained.
Do not assume the independent choice of job/core alone proves a clean factorial.

`stage_native.py` copies only manifest-listed sources to a fresh output directory,
verifies the common final frontends, applies one shared R2 residency overlay and
emits core/job maps. Build using recorded parent toolchain commands adapted to new
paths. Preserve full source manifests including generated headers/CMake inputs.
Do not pair a new static core with an old incompatible ggml DLL. Bind actual loaded
modules, not just filenames. The source helper does not implement a new kernel.

For R2, inspect `provision`/`request` in recovered worker.cpp: a null draft model is
valid only when spec.draft is false. The overlay skips draft weight loading,
vocabulary cross-check and unused draft context construction only in target_only
mode. Ordinary target arithmetic/reset remain unchanged. Capture actual occupancy
and check target equality against the original R before timing. If another actual
call dereferences the absent draft, repair the common frontend before freezing.
All R2 arms receive the same overlay, including marker and metadata code.

Use generated burst worker requests in order: two fixed exposed primers, then
sixteen different measured requests. Provision once; reset per request as before,
no prefix reuse/concurrency. Same input order across arms within a session. Never
invoke the old per-root worker wrapper 16 times and label the sum a burst.

The native marker is emitted after response completion with std::endl. The owned
host supervisor starts a monotonic clock before process launch and timestamps each
marker while draining stdout. Native main-start timing is a separate field, not a
replacement. Track initialization, first-any-result, first-measured-result, actual
burst end, wrapper wall and peak device memory; distinguish inclusive clocks.
Record heavy qualification separately from clean measurements. Preserve original
API/state checks and reuse existing canonical state extraction for offline tests.

## B570: scale the final interface, not an obsolete producer

Pin acc86d9cb07c2afa983f73e28a1048fb99c63e3a. Entry points:
- `benchmarks/b570_economics_v1/parallel_host.py`: common repaired binary,
  HS_ECON_WHOLE selects whole re-aligned micrographs; local uses the same arithmetic.
- `resident_host.py`, `probe_host.py`, `native/known_probe.inc`: admitted phase
  binding and real known-token append probes, including rollback and output rows.
- `reference_resource_host.py`, `evidence/REFERENCE_RESOURCE_SOURCE.json`: observer
  qualification of original producer without changing its numerical implementation.
- `REPRODUCE.md` and delivery manifests: clean source reconstruction dependencies.

Expose context capacity as a native profile parameter, not a Python-only label.
Propagate it through reference/candidate context construction, scheduler reserve,
cache capacity, actual head/extent extraction and the signed budget reader. Verify
reported native capacity. Preserve whole-prompt/512 outer chunks and physical
UB128 producer, final requested-output masks and scalar reference continuation.
Do not globally turn on continuation F32/p021 during the producer phase.

PR191's known_probe.inc hard-codes a 1024 guard, all-output q32 calls and a
reserve32 metadata claim. Do not reuse it unchanged. `stage_b570_probe.py` adds an
actual llama_n_ctx check, q32 last-only mask, copied requested rows and a separate
append interval. It suppresses explicit heavy commits only in declared clean
probes; host integration must additionally verify observer.decode/finish are
non-heavy in those clean runs. Candidate output allocation is bound separately:
remove the old implicit reserve32 intervention, keep the independent R unchanged,
and qualify any required candidate reservation under that declared contract.
Build adapters must propagate capacity through the real contexts before using
this overlay. Header/API source-anchor drift is normal integration work.

The twelve cells come from `design.py b570-struct`. q2/q4 may request the registered
rows; scalar R produces its individual rows separately without reserve expansion.
q32 uses last-only output; never report all 32 vectors observed. Restore/prepare
valid paired state before EVERY warmup and measurement. Preparation is separately
charged, not silently omitted from full-study costs. Measure native append through
sync and requested-row retrieval; traces/diagnostics are separate from clean time.

Reuse existing same-version evidence for overlapping C1024 cells only with exact
input/deployment/source matching. C4096 requires its own frozen R before outputs.
No new speculative economics panel. If M paths remain identical, do bounded
integration/EOG/reset checks only. The two capacities must share residency when
interpreting their difference as a capacity effect.

## Bindings, analysis, and portability

Actual host bindings are intentionally absent at authoring time. Recover manifests
rather than guessing hashes or using a template's nulls as admission. Reuse the
parent supervisor, request ledger, namespace-specific flags and cleanup. All tests
here are local helpers; the executing agent must supply real qualification receipts.

Normalize per-slot records into analyze.py's schema. Cross-reference each record's
reference_id, source/model/module manifests and native receipt. Do not set
qualified=true from endpoint equality alone when a heavy qualification is required.
Structural outputs are per-coordinate descriptive tables; do not bootstrap them
as independent natural roots or average their selected crossing density into a
production speedup. R2 root intervals condition on four shared sessions; retain
actual worker/session directions and host costs separately.

Select independent natural roots by immutable ID and text, before candidate
outputs; reuse existing exposure exclusions and native template/tokenizer checks.
Use domain quota and capacity only, no favorable offsets. If R1 natural is closed,
freeze a Qwen-only panel for R2 with the same selection rule.

Produce a source-only portable recipe with dependency revisions, relative roots,
compiler/build commands, model hash/license references and tiny reproducible input
samples. Never include model weights, tokens, secrets, user home paths in public
instructions. `receipts.py source-bundle` validates explicit source hashes; it is not
a build. Validate a fresh-directory build on the existing host. WSL/Linux tests are
optional only if already installed; no installation or rental without authorization.
