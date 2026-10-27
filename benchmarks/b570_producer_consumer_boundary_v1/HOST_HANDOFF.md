# B570 host handoff

## Status at handoff

This PR provides a fixed scientific protocol and executable **CPU** planner/validators. It has started **0 new native/GPU processes**. `boundary.exe` does not exist in this package. No native compile or qualification has been claimed.

The host has the existing PR148/150 source/runtime/reference delivery. Reuse those assets. A new packaging/reproduction campaign is not required before implementing this bounded experiment.

## 1. Freeze the actual inputs and runtime

Use these exact controls from CONTROL_INPUTS.json:

- HumanEval/38:181 native prompt IDs, cap64, historical `references/qual-0`.
- HumanEval/115:349 native prompt IDs, cap64, historical `references/qual-2`.

New panel:8 natural inputs, cap128, four with64–192 formatted native IDs and four with256–352. Source revision, exact IDs, template hash, candidate inventory, complete exposure exclusion and fixed hash selection must be recorded before any new forward. Domain is a descriptor; do not force missing domain×length cells with artificial truncation/concatenation.

The supplied INPUT_PANEL_TEMPLATE is intentionally invalid for execution. Fill a separate real file, set status=FROZEN_BEFORE_FORWARD, preserve the census/exposure evidence. Eight unique token sequences and exactly four per band are enforced by the planner. If the static census cannot populate the plan, stop before forwards and revise the design visibly; do not silently run a reduced matrix.

RUNTIME_TEMPLATE is also intentionally invalid. After an actual build, bind executable/source/numerical-module hashes, vocabulary size and full native EOG set. The models must match the exact published Qwen hashes in the template. Target and draft remain B570 Vulkan, threads8, F16KV, FAoff.

## 2. Existing verified interfaces

These paths exist at PR150 commit `9f03bead68462326497b03edb0d2d80f8f2fd4c3`:

- `benchmarks/b570_native_reproduction_v1/native/formal.cpp`
- `native/query_head.h`, `native/raw_capture.h`, `patches/03-request-bridge.patch`
- `CMakeLists.txt`, `prepare_source.py`, `freeze.py`, `run_native.py`, `audit_request.py`
- `MODEL_IDENTITY.json`, `INPUT_PANEL.json`, `LOCAL_DELIVERY.json`.
- `benchmarks/b570_native_delivery_v1/ACCESS.json` for existing delivered references/source.

The current native CLI is:
`formal OUTPUT TARGET DRAFT PANEL qual INDEX STUDY_ROOT`, INDEX0..3.
It internally runs the old R/PQ/QB triplet and only serial prefill. It cannot execute producer/resume slots by substituting an index or setting an environment variable.

Existing process supervision syntax, for **the new executable once it exists**, is:
```powershell
python benchmarks/b570_native_reproduction_v1/run_native.py --manifest $freeze --receipt $receipt --limit 900 $boundaryExe $output $target $draft $panel $slots
```
This is the existing supervisor around a proposed new native argument list. Do not run it until the extension is built and the new manifest hashes that actual binary. The old freeze helper may assume the old bin inventory; extend a copied helper for the new executable instead of weakening its checks.

The existing CMake target uses:
`target_link_libraries(... PRIVATE llama ggml ggml-base)`, C++17 and `/O2 /W4 /fp:precise /utf-8`, with include roots `LLAMA_SOURCE/include`, `ggml/include`, `vendor` and the native header directory. Add a new boundary target in a new build wrapper; preserve old kit files. Reuse already prepared upstream/overlays and numerical libraries where the host build supports it. If any numerical DLL changes, record a new runtime identity; never describe it as byte unchanged.

## 3. Native extension: exact implementation obligations

Create a new `native/boundary.cpp` by adapting formal.cpp. Keep original code frozen. Implement:
`boundary OUTPUT TARGET DRAFT PANEL SLOTS`.

Each record carries the frozen slot_id. Only one model worker is active. Models may remain loaded across the slots of one input; use fresh target contexts for each natural/resumed path. Do not hold all donor/consumer contexts simultaneously.

### 3.1 Native context and layout

Use current formal.cpp context parameters:ctx1024/batch512/8threads/F16 K,V/FA disabled.
Strict R uses UB1/output1. All other target paths use UB4/output4; draft uses UB1. Set `HS_REQUEST_LAYOUT` before creating each target context and keep it fixed until that context is destroyed.

- Natural producer and natural C1 use PQ.
- Natural speculative B0 PQ/QB keep their own corresponding layout through P1 and continuation. Their P1 producer bytes must agree with the fixed-PQ donor before they become own-path controls.
- Resumed PQ/QB use their fixed consumer layout in a new context.
- No same-context PQ→QB switch; current graph cache does not establish safe dynamic selector switching.

The request bridge only admits q2/4 and key256/512; q1 is the original path. P4T caller tail3 is2+1 and is a new frozen recipe. Do not add a q3 method silently.

### 3.2 Producer function

Replace fixed serial prefill in the new driver with:
`prefill(prompt_ids, caller_lengths)`.
Require all lengths positive, sum exactlyN, width∈{1,2,4}; use exact contiguous absolute positions.
Set logits=false on every prefill row except the last absolute prompt position. The existing decode helper already has a `last` flag; retain that semantics.

P1 schedule is N ones. P4T is floor(N/4) fours plus tail1/2, or tail3→[2,1]. Exact schedules are present in each bound slot.

Record actual caller IDs/positions. Capture actual attention ne/nb/dtypes/device. If whole-micrograph counters are unavailable, report them null/unknown; do not infer a measured physical histogram solely from a caller label. The causal factor is the specified producer recipe, not a claim of isolated shader scheduling.

### 3.3 Boundary export/import

The public sequence-state API used by the repository's earlier worker is:
```cpp
llama_synchronize(ctx);
size_t n = llama_state_seq_get_size(ctx, 0);
std::vector<uint8_t> state(n);
size_t written = llama_state_seq_get_data(ctx, state.data(), state.size(), 0);
```
Check returned size, save exact bytes, and save the complete final prefill FP32 vector before initial sampling. Record sequence0/min0/maxN-1 and model/runtime identity. Capture does not run a new forward.

On a **new empty context**:
```cpp
size_t consumed = llama_state_seq_set_data(ctx, state.data(), state.size(), 0);
llama_synchronize(ctx);
```
Require consumed==saved size. Read sequence state back through the same get_size/get_data API and require exact bytes and positions. Persist that actual post-import KV readback and the full receiver-owned initial-logit vector that will be consumed, including off-mode resumed requests, as restored_boundary payloads. A restore_roundtrip boolean or a reference to the donor digest is not a substitute for these bytes. This API pattern is present in `benchmarks/b570_final_causal_closeout_v1/native/worker.cpp` at PR145; the old Q6_K worker/binary is not reused.

The reconstructed contract is boundary0 sequence KV+positions, complete initial logits, empty committed output prefix, no pending token before first sample, greedy no RNG history, clean native context/scheduler. It is not a general opaque context clone.

Implement `sample_saved_initial(vector<float>)` with exactly the current formal.cpp first-finite-maximum rule. Save/compare the full vector and consume this initial sample once. Never call an extra teacher-forced forward to rebuild hidden state. `extra_forward_calls_on_restore` must be0.

### 3.4 Natural and resumed consumers

Reuse the original formal.cpp generation loop and keep k=1:

- C1 consumes the pending token one at a time.
- PQ/QB rebuild a separate draft from the same prompt using serial P1. Producer factor never changes the draft producer.
- Draft sync/proposal, target verify [seed,proposal], both decision rows (including the uncommitted row), accept/reject, correction/bonus, trim and stop logic remain the inherited code.
- Preserve old cycle fields exactly and append `committed_ids` for independent reconstruction.
- Export initial producer state before natural C1 continuation; retain full natural endpoint as each donor's reference.
- Off/on observation differences must not change endpoints or cycles.

B0 contains both C1 and layout-specific natural/resumed checks. Only when all32 control slots and the independent historical audit qualify may B1 run. B1 also has a C1 natural/resumed sham for every new producer state.

P4T consumer findings stay conditional on this clean receiver. A negative result does not automatically prove a natural integrated production path fails.

## 4. Record format consumed by the CPU tools

One final JSON object per primary slot in REQUESTS.jsonl. Keep immutable per-request raw files separately. Progress files may exist, but do not append a STARTED and COMPLETE line with the same slot to this final ledger; write a unique final disposition or leave STARTED explicit after interruption.

Required completed record fields:

- slot_id, attempt=0, status (COMPLETE_QUALIFIED / COMPLETE_COUNTEREXAMPLE / COMPLETE_NO_TRIGGER).
- native_started=true, pid, started_utc, finished_utc; UTC offset required.
- runtime_sha256 = canonical JSON SHA256 of FROZEN_PLAN.runtime.
- prompt_ids_sha256 copied from the frozen slot after checking actual submitted IDs.
- endpoint object with ids/eog/length/terminal_id/stop_reason.
- cycles array; C1/R empty. Spec rows contain all legacy fields plus committed_ids.
- target_calls/draft_calls, actual_signatures, geometry_files for natural control comparison.
- checks.module_identity/device_placement/actual_geometry = actual observed booleans.
- performance_eligible=false.
- vectors={} for off; heavy uses the complete logical inventory below.
- resumed paths:checks.restore_roundtrip=true only after byte comparison; extra_forward_calls_on_restore=0; imported_boundary_sha256 = canonical hash of the donor boundary byte signature; **restored_boundary** must identify the actual post-import KV export and actual receiver initial-logit bytes, with kv_min/kv_max/sequence_id.

Logical vector keys:

| Key | Existing formal.cpp raw equivalent |
|---|---|
| target_initial | target/initial.f32 |
| target_ordinary/N | target/ordinary-N.f32 |
| target_verify/C/0 and /1 | target/verify-C-0.f32 and -1.f32 |
| draft_proposal/C | draft/proposal-C.f32 |

For k1 cycles, reconstruct exactly the native commit sequence: always commit decisions[0]; when it matches the proposal and that commit has not reached cap/EOG, decisions[1] is mandatory. Omitting this bonus is legal only at the true terminal boundary. Require target_kv_max and draft_kv_max to equal keep-1 after every trim, preserve seed/base/pending ownership, and reject any cycle after termination.

A heavy C1 has exactly output_length vectors. A heavy k1 request has1+3×cycles vectors. Each vector metadata includes relative path, bytes=4×vocabulary_size and SHA256. Include rejected/unexamined verification rows.

A captured natural boundary is:
`boundary={kv:{path,bytes,sha256},initial_logits:{path,bytes,sha256},kv_min:0,kv_max:N-1,sequence_id:0}`.
The byte signature used for donor matching excludes payload paths, keeping each payload's bytes/hash and those three position fields. Two identical values saved to different directories must compare equal. **restored_boundary has the same structure, but its payloads come from the actual post-import receiver export/initial vector.** The CPU gate requires payload-root, rehashes both donor and restored KV/initial payloads, and compares their complete byte signatures and positions. Missing payload paths fail. In heavy mode, both donor and restored initial_logits identities must equal the actually consumed target_initial vector. Initial logits are the receiver-owned vector consumed by the defined first-greedy step, not a claim of restoring an opaque native output buffer. Content-addressed deduplication is allowed only after actual native readback and hashing; do not substitute donor metadata for the readback operation.

geometry_files maps old relative names such as `target/decode-350.json` to real payload metadata. Preserve their parsed contents for historical natural controls. Do not fabricate old geometry descriptors from requested flags.

Failure/NOT_RUN:

- Failed native record: native_started=true, actual status/reason, all partial raw paths preserved.
- NOT_RUN_DEPENDENCY/NOT_RUN_BUDGET: native_started=false, reason and blocking slot.
- Missing records remain missing in CPU reports; the tool never invents a final status.
- No automatic retry in this152-slot freeze. A technical rerun requires a visible separate amendment and new attempt inventory, keeping all primary records.

## 5. Independent historical control check

The new CPU `audit-controls` command independently reads delivered references and actual payload bytes; it does not trust `historical_reference=true`.

It compares every natural B0 P1 C1/PQ/QB off/on endpoint, complete legacy cycle fields and call counts. For heavy records it additionally compares all vector bytes, actual descriptors, and every per-decode geometry JSON to:
`$referenceRoot/qual-0` and `$referenceRoot/qual-2`.

This is numerical compatibility at the new driver configuration; the P1 C1 UB4 context is deliberately being tested against strict R UB1. Do not relabel its actual configuration as UB1 or rewrite raw files to satisfy the older schema.

```powershell
python "$work/work_package.py" audit-controls --plan $frozen --records $records --reference-root $referenceRoot --payload-root $rawRoot --out $controlAudit
python "$work/work_package.py" validate-records --plan $frozen --records $records --payload-root $rawRoot --control-audit $controlAudit --report $gateReport
```

At the B0 checkpoint, missing120 B1 slots are expected; gateReport.b0_qualified must be true before B1. After execution use a fresh audit filename and `--require-complete`.

## 6. Host sequence and stopping

1. CPU verify-source against PR150 checkout; inspect existing material paths.
2. Complete static input census and exact8-input binding; implement native driver separately.
3. Compile new native target, record actual binary/modules/vocabulary in runtime JSON.
4. Generate FROZEN_PLAN with152 exact slots; verify no null bindings remain.
5. Run the32 B0 slots under the existing bounded Job supervisor. Rehash actual payloads and run both CPU checks. Preserve any failure.
6. Only after B0 qualification, execute each new input's15 slots in frozen order. Own-path C1 sham must precede its donor consumers.
7. Recompute all outcomes. Negative/no-trigger findings are complete endpoints. Do not select only passing inputs to report eligibility.
8. Deliver source/plan/inputs/actual records/needed raw/CPU audits through the existing repository material system. Report native implementation and execution status explicitly.

Bounded defaults:one active GPU worker, totalowned≤10800s, rawpayload≤8GiB; single input worker supervisor≤900s, individual request soft deadline≤180s. Account model-worker lifetimes separately from request timers. A cap stops remaining coordinates; no automatic budget expansion.

No model-weight or numerical-DLL redistribution is added by this PR.

