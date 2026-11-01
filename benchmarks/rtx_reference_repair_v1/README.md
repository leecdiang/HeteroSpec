# Reference repair after the 14B counterexamples

**Implemented development and confirmation workflow, not an observed repair result.**
Base: PR156, `47c93985010d0f3c0c55f975f4cd7761e64bcae2`. Historical source, numerical libraries, failures, two mathematical counterexamples and the original 40 requests remain unchanged. The new work has its own roots and cumulative ledger. No model was run while authoring this PR.

The objective is a structural repair that preserves the frozen UB1 reference on unseen inputs, with its entire cost charged. A diagnostic matrix or a rewrite of the paper is not the finish condition. Read `PROTOCOL.md`, `ENGINEERING_POLICY.md` and `HOST_PROMPT.md` before native execution. Source entry: `scripts/experiments/rtx_reference_repair_v1/`.

## What is implemented

- A hash-checked adapter for the exact PR156 worker, retaining its native acceptance/correction/bonus/KV reconciliation loop.
- Actual QK/node **scheduler assignment** through `context->get_sched()` and `ggml_backend_sched_get_tensor_backend`, recorded separately from memory ownership. This corrects the PR156 observation error; a buffer label is never accepted as compute-placement evidence.
- Native prefill snapshots, initial full logits, imported-state readback and optional post-reconciliation checkpoints, including consumed IDs and pending ownership.
- `NATIVE`, `P1`, `RSEED`, `SELF` and reverse `BSEED` interventions. `RSEED` executes original UB1 prefill in a separate reference context and transfers actual state and initial logits. `BSEED` sends candidate-prefill state to a reference consumer. All real producer/copy/restore/readback work is inside the service timer.
- Process-fixed row lowering for selected dense projection families (`qkv`, `attn_out`, `ffn`, `lm_head`), with original single-row MUL_MAT, original numerical DLLs, precision forwarding and explicit supported-shape guards. This is a candidate implementation, not a proof or already-validated kernel.
- Selected post-compute tensor OUTPUT captures, exact logical-prefix records and a strided F32/F16 comparator. Source-reviewed token-axis/microbatch alignment is mandatory. Sparse output capture is not an automatic first-causal-operator certificate or a fixed-operand replay engine.
- Development, raw audits, candidate sealing, independent old/new R comparison, 14B untouched confirmation, original-Qwen8B regression, paid timing, A/A analysis and local evidence packaging.
- Windows kill-on-close Jobs, startup/request handshakes, exclusive GPU lock, cleanup receipts, immutable code/assets and budgets shared across repair epochs.

## CPU check

From `scripts/experiments/rtx_reference_repair_v1`:

```powershell
python -B -m unittest test_repair test_row_helper -v
```

The C++ helper tests use a tiny synthetic graph API; they are not real ggml/CUDA/Windows model tests. Python 3.11+ is sufficient. A missing local C++ compiler skips only the compiled helper tests; report this, never call it native acceptance.

## Host workflow

1. Check out this branch. Recover PR156's actual source archive, model paths, old worker, 21-DLL manifest, calibration tokens, untouched selected panel and complete evidence. Read the v2 correction. Do not download weights again if existing hashes match. Keep the original worker and model bytes untouched.
2. Generate the new worker into a fresh path:

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/stage.py --repo D:/HeteroSpec --out D:/rtx_repair/stage001
```

3. Use `stage001/build_native.py` with the same real tools/source archive and DLL assets as PR156, a new build directory, and `--variant original`. Its options remain `--archive --out --dll-manifest --dll-dir --zig --cmake --ninja`. The DLL manifest expects the original `numerical_DLL_sha256` mapping. Reuse validated tool paths from PR156's BUILD receipt; do not invent paths. The script builds the new core/worker and retains the numerical DLL cohort. Run source review and CPU tests after any anchor/API repair.
4. Fill `CONFIG.example.json` with actual paths and conservative resource reservations. `reference_binding` is the original PR156 frozen binding; `original_raw_root` must contain the restored original request records, not just the compact report. `development_panel` has the four exact old inputs; `confirmation_panel` is the original twelve still-unexposed natural inputs. Preserve its 2-domain × 2-length strata. Fill missing provenance from real prior receipts without changing tokens.
5. Prepare and advance:

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/host.py prepare --config D:/rtx_repair/config.json --out D:/rtx_repair/epoch001
python -B scripts/experiments/rtx_reference_repair_v1/host.py advance --bundle D:/rtx_repair/epoch001
```

This performs the baseline, own-path state sham, P1, RSEED and reverse cross (120 development requests when all execute), then stops for the **agent's mechanism decision**, not renewed user permission. Inspect every `.audit.json`; a scientific counterexample is retained and does not automatically abandon development. An execution/ownership failure stops immediately and must be repaired before continuation.

6. Diagnose the first observed divergence and choose a uniform structural rule. For original-path tensor tracing:

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/host.py run --bundle D:/rtx_repair/epoch001 --phase trace --producer NATIVE --rows off --trace D:/rtx_repair/trace.json --tag trace01
```

Use selected layers/positions before broad capture. A separate diagnostic-only epoch can add a complete historical `teacher_ids` endpoint to the development inputs to align token prefixes. Teacher forcing is rejected from qualification/timing and speculative requests. Serialized KV inequality alone is not a causal result. If the snapshots are inadequate, the agent may add a narrowly targeted fixed-operand replay with original input-lifetime/own-path controls; it is not claimed to be preimplemented here.

7. Example development candidate (only after evidence motivates the families):

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/host.py run --bundle D:/rtx_repair/epoch001 --phase candidate --producer RSEED --rows qkv,ffn --tag repair01
```

This is an example of flags, not a prescription that qkv/ffn causes the failure. `P1` or `NATIVE` is also accepted for candidate runs. No brute-force timing search. Preserve each candidate and its ablation. Changes to code create a new epoch with the same shared ledger; do not overwrite failed evidence.

8. Write a concrete mechanism report using the example fields. Seal only a complete passing development matrix. `seal` independently rereads all raw files, baseline and sham; a caller-supplied PASS string is insufficient:

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/host.py seal --bundle D:/rtx_repair/epoch001 --producer RSEED --rows qkv,ffn --mechanism D:/rtx_repair/mechanism.json --audit D:/rtx_repair/epoch001/RUN_candidate_repair01.audit.json
python -B scripts/experiments/rtx_reference_repair_v1/host.py advance --bundle D:/rtx_repair/epoch001
```

9. Confirmation runs 144 requests against the **original** R executable, not merely the rebuilt core. If it passes, make a separate `regression_only: true` configuration using original Qwen3-8B target (`408b9555…`), its PR151 R worker/binding, full-offload999, exact old regression inputs and the **same repair executable/rule**. Set `primary_bundle` to epoch001 and `reference_compatibility_study` to `rtx_scope_transfer_v1`. The native binding admits the actual 36-layer/4096 geometry. Prepare a fresh regression root; run `--phase regression --producer ... --rows ...`, then attach its completed run:

```powershell
python -B scripts/experiments/rtx_reference_repair_v1/host.py attach-regression --bundle D:/rtx_repair/epoch001 --run D:/rtx_repair/regression001/RUN_regression_v00.json
python -B scripts/experiments/rtx_reference_repair_v1/host.py advance --bundle D:/rtx_repair/epoch001
```

Four timing sessions then run automatically if all gates hold. No requirement to spread them over three dates; log actual dates and do not claim independent dates if there are fewer.

## Recovery, results and delivery

`host.py audit-existing --run <RUN_*.json>` reconstructs an existing completed matrix without new forwards. No failed attempt is automatically overwritten or retried. Ordinary engineering fixes are authorized under `ENGINEERING_POLICY.md`; unresolved cleanup retains ownership/lock. Do not manually delete a live lock.

`archive.py --root <evidence-root> --out <new-delivery-root>` packages and reopens every member, excluding weights/DLLs/executables. A GitHub release upload and fresh remote download must be performed separately; local packaging never claims remote verification. Deliver a separate result PR including actual fix, complete matrices, raw access, remaining failures, unstarted slots and old evidence links. Do not merge the paper or submit arXiv automatically.
