# PR143 evidence, timing and accounting review

Review date: 2026-10-21. Reviewed result commit: `60b7d6a9301557c9a26c7d89acbe1b9d122bb53d`.

**Disposition: accept the archived finite-panel negative closeout, with the limitations below. Full protocol resource-budget compliance is not certified.** The original QB/thread8 baseline remains in place. No additional model run, repaired reference, retrospective cost entry or optimization is authorized by this review.

The independently implemented [read-only audit](read_only_audit.py) loads no model or backend and imports no experiment analyzer. Its [final receipt](REVIEW_FINAL.json) authenticates all 100 payload-manifest entries and all 102 original package Git blobs against the reviewed commit, 1,044 frozen local files, the two original model files and five numerical DLLs, and the original inputs/order. It rechecks 914 PR134 reference vectors, 78 original bridge vectors, 346 PR135 attempt2 vectors, and all 976 new archived vectors against the committed historical references and their local bytes. Detailed geometry and native results agree across the local root, compact archive and Git package.

All 156 registered slots and nine individual model-worker receipts reconcile. E0/E1 capture/count endpoint and complete speculative-state comparisons pass. Every observed draft layer/physical microbatch has q1; ordered QK, key/mask tensor metadata and prefill KV endpoints agree between BASE and SUBMIT. These are finite-path shape/source and full-logit observations; actual GPU mask values are not independently read back. All 64 immediately paired warmups and 64 measurements match their registered input, arm and order. The prior unreceipted partial time-1 remains unchanged and excluded.

Independent reconstruction from original native request records gives:

| Metric | Recomputed value |
|---|---:|
| SUBMIT / mean(BASE_A, BASE_B), complete service | 0.9991613016897527 |
| Service reduction | 0.0838698310% |
| SUBMIT / contemporary R | 1.2036779934566173 |
| Dual BASE / R | 1.2046883635515024 |
| Largest input-aggregate absolute A/A imbalance | 0.3688690362% |
| Registered practical screen | Fails |

The required reduction exceeds 2%, and session0 is slower rather than faster. The observation establishes no practical benefit and no equivalence. Timing/phase CSVs and both stored estimators agree with the native records. The 16 shared CPU toolkit tests passed again during review. GitHub reported no configured CI checks, statuses or review threads at the reviewed head; this is not a CI-pass claim.

## Timing boundaries

The C++ outer service clock brackets `request(...)`. Target/draft contexts are constructed inside that function and their destructors finish before control returns to the caller. Prefill, generation, sampling, inherited host/state handling, synchronization and teardown therefore remain charged. Arm selection precedes fresh context creation. Shared model loading, reference reads/comparisons and result-file output are outside that clock. Capture callbacks are installed only for capture; all 128 E2 requests have no observers.

The inner `request_seconds` window excludes context creation/teardown and some final record handling. Phase fields sum synchronized decode spans and exclude batch construction and host-loop overhead. A standalone whole-draft-prefill interval was not collected; the phase sums cannot substitute for it or identify GPU time.

The reported 1,389.874 seconds of worker charge is a conservative wrapper stopwatch interval. It includes process launch, exit polling at 0.5-second intervals, result parsing and Job Object cleanup. It is not an exact OS-process lifetime or active CPU/GPU time. Every worker's model-load plus service sums fits inside its supervised charge; all native exits/cleanup and non-overlap are supported by the receipts. Nested service, request, phase, worker and wrapper intervals must not be summed as disjoint costs.

## Auxiliary-process limitation

The registration's `other_processes=128` is a prospective reservation. The archived wrapper neither counts every compiler/control/auditor/helper descendant nor enforces that aggregate ceiling. The one-active-process Job Object applies to the individual native model worker, not every host helper. The continuous owned-wall interval accounts conservatively for elapsed host preparation/coordination time but cannot establish how many helper processes existed.

Accordingly, this review does not infer either compliance or an overrun of the 128-process reservation. It cannot be reconciled retrospectively from model-worker receipts. `fully_protocol_resource_compliant` is explicitly false in the review receipt. This is a protocol-accounting deviation, not a promotion of SUBMIT or proof of a fully audited software ceiling. This qualification also applies when citing the archived `PAPER_ADDENDUM.md` by itself.

## Evidence-preserving reproduction

The archived `audit.py` regenerates derived files. The archived `verify_delivery.py`, despite its read-only description, writes `DELIVERY_CHECK.json` and copies files back into its recorded worktree. They should not be used for a nonmutating review of the sealed package. Their original bytes are preserved; this review adds a separate audit rather than rewriting a previously hashed artifact.

On the original host, from a repository checkout containing the result history, use a fresh output path:

```powershell
python -B reports/b570/prefill_closeout_review_v1/read_only_audit.py --repo . --native-root C:/hs/b570-prefill-closeout-20261021 --out C:/hs/b570-pr143-new-review.json
```

The command refuses an existing output file and writes only the newly selected review receipt. It reads the recorded original reference/model/runtime paths; another host needs the author-supplied assets at those paths or an explicitly reviewed path mapping. The 531,548,285-byte full raw archive remains local with its published SHA-256. Local full-byte authentication and independently implemented computation are supported; third-party raw-data certification and Git-only reproduction are not.
