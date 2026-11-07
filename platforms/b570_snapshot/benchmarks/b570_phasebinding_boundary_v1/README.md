# B570 Phase Binding / Reference Boundary / Physical Work Closeout

Result of PR #96 on the actual Intel Arc B570 / Vulkan host, inheriting the immutable PR #92 evidence and PR #93 audit. The new Draft targets the PR96 design branch; no main/manuscript/release/older PR changes.

Start with [RESULTS.md](RESULTS.md). The four conclusions are separately reported: prefill causality UNRESOLVED, state/continuation interaction UNRESOLVED, native physical-work geometry SUPPORTED, immutable same-output negative request cost SUPPORTED. Original stock-relative failures and null qualified ratios remain unchanged.

All 108 original requests were attempted exactly once: 107 complete and one failed API-observer scope; P1 72/72, P2 35/36; two zero-forward load probes, zero warmups/retries/forks. Partial API metadata has no complete native endpoint and is explicitly failed with sampled stop-threshold overshoot. Continuous physical residency UNKNOWN; exclusive stage cost MODEL_TIMING_UNAVAILABLE.

## Evidence map

- PLAN.json / INPUTS.json / F0A.json / F0A_AUTHENTICATED.json: prospective actor, exact native prompts, recipes, gates and actual authenticated source bytes before first forward.
- REMAINING_EXECUTION.json / REMAINING_AUTHENTICATED.json: prospectively sealed continuation of only23 unstarted slots after the one observer failure. Actor/plan unchanged, failed start not replayed.
- STATE_RECIPE_INVENTORY.md: actual phases, sampler/pending/KV ownership, capacity, synchronization, physical occupancy and unavailable full-state fork.
- PHASE_INTERVENTION.json / FORK_SHAMS.json: full-trajectory comparisons, natural boundaries, captured top2 and state/logit hashes, capture/own-binding guards, explicit causal/fork limits.
- WORK_WITNESSES.json: actual native graph/row/cycle counters from35 successful new P2 requests; separate partial Vulkan API recording metadata.
- QUALIFICATION.json: entire immutable original qualification, nulls, separate post-hoc complete-output pairs and exposed-diagnostic scope.
- RESULTS.json / INDEPENDENT_VERIFICATION.json / SYNTHETIC_REJECTION.json: independently rederived conclusions and rejection checks.
- STUDY_RECORDS.json / FAILED_REQUESTS.json / LEDGER.jsonl / STUDY_COMPLETION.json: every unique start and outcome, owned native lifetimes, failure without replay.
- raw/ contains direct new native RESULT/REQUEST and failed-scope evidence; all traces, memory samples, module/weight/KV records and partial Vulkan API dump are in the CAS.
- ARCHIVE_MANIFEST.json / COMPLETE_CAS.json / COMPLETE_CAS.chunk*: complete de-duplicated source/raw/failure evidence including all7379 inherited logical files.
- LOCAL_RESTORE.json / REMOTE_RESTORE.json / RECEIPT_PUBLICATION.json: fresh complete byte restoration and independently rederived output equality, with actual authenticated remote GitHub bytes and final receipt readback.

## CPU-only independent restoration

Read COMPLETE_CAS.json. Concatenate its parts in declared order using the downloaded raw binary file bytes (do not concatenate GitHub HTML). Verify every size/SHA256/Git blob SHA and the whole archive SHA256. The exact ARCHIVE_MANIFEST.json also lives inside the authenticated archive as MANIFEST.json; its byte SHA256 and Git blob SHA bind the public manifest. All code is in the CAS under code/.

Restore into a new destination:

    python -B restore96.py --archive COMPLETE_CAS.zip --manifest ARCHIVE_MANIFEST.json --destination restored --sha256 <COMPLETE_CAS.json archive_sha256> --receipt restore-receipt.json
    python -B restored/code/verify96.py --root restored --output rederived
    python -B -m unittest discover -s restored/code -p test_verify96.py

The independent auditor never imports an executor or launches native code. On the experiment host it fully rehashes both pinned external GGUF files again. Without those exact external model paths, the explicit --skip-external-model-rehash option supports CPU archive/output/work/fee verification while honestly recording models_rehashed=false; it does not reproduce the full model-check receipt. RESULTS.json and the other derived evidence remain comparable. Full model weights are external and excluded from the CAS.

Preserved state/logit digests are native live witnesses. Full serialized KV and FP32 vector payloads are absent, so independent CPU verification cannot redo those tensor byte comparisons. Own same-UB binding no-ops are not donor clone/restore shams. No output cropping, forced future tokens, numeric fallback, fitting of seen fees or broad tuning sweep was used.
