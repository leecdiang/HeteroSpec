# M4 runtime profitability-control closeout

**Final scientific status: CORRECTNESS-ADMISSIBLE / PROSPECTIVELY PROFITABLE — RUNTIME STUDY CLOSED.**

The final prospective attempt is `unattended-20260924t125921z`. The measured generation window is post-prefill; model load and shared prompt prefill are excluded. The fixed protocol, calibration, qualification, and formal held-out stages are complete. **No additional timing and no post-hoc policy tuning are authorized as part of this study.** Energy is `NOT_CLAIMED`.

## Frozen result

| Item | Final value |
| --- | ---: |
| Selected policy | `E8_M000` (decision after 8 speculative rounds; margin 0) |
| Qualification direct-ID exactness | Always-Spec 48/48; Guard 48/48 |
| Formal direct-ID exactness | Always-Spec 180/180; Guard 180/180 |
| Held-out workload | 60 prompts, 3 repetitions, 3 conditions; 540 observations |
| Target/Guard geometric-mean speedup | **1.3114×**; 95% prompt-bootstrap CI **[1.2487, 1.3787]** |
| Target/Always-Spec geometric-mean speedup | **1.3469×**; 95% prompt-bootstrap CI **[1.2867, 1.4088]** |
| Guard/offline-oracle geometric-mean regret | **1.0278×**; 95% prompt-bootstrap CI **[1.0137, 1.0446]** |
| Guard fallback requests | **30.6%** |
| Energy | `NOT_CLAIMED` |

The Guard is profitable relative to target-only on this held-out workload and is direct-token exact. Fixed k=2 speculation has a better aggregate point estimate than the Guard. The offline oracle is descriptive and was never available to the online policy. These data do not establish that the Guard improves on fixed k=2, and the small individual Spec-Bench strata should not be read as stable subgroup estimates. Full formulas, per-prompt results, control trace, and uncertainty are in [FORMAL_REPORT.md](FORMAL_REPORT.md) and [FORMAL_ANALYSIS.json](FORMAL_ANALYSIS.json).

## Evidence archive and offline verification

The immutable Git evidence bundle is [m4_runtime_complete_evidence.tar.gz](../../artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz). It contains the final baseline (240 rows), candidate (1,080 rows), qualification (144 rows), and formal (540 rows) `observations.jsonl`, manifests, completion records, warmups, runner stderr, pipeline and launcher logs, formal-start markers, build manifest and binary, frozen policy/protocol/data/source files, recovery analyzer, analysis output, and a per-file `bundle_manifest.json`.

Archive SHA-256: `af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab`. Compressed size: 1,298,101 bytes. The [archive descriptor](../../artifacts/m4_runtime/runtime-profitability-control-20260925/archive_descriptor.json) records **62/62** extracted payload files with matching byte sizes and SHA-256 values, zero failures. The same clean extraction ran an independent, standard-library-only recomputation of calibration policy selection, direct-ID equality, 60-prompt medians, 10,000 prompt-bootstrap resamples, and fallback fraction; every recorded core result matched.

An evaluator can repeat this without an M4 machine or model files:

```bash
python3 scripts/platform/m4_runtime/recompute_evidence_bundle.py \
  artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz \
  --expected-sha256 af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab
```

The archive includes a copy of that verifier under `tools/`. The sidecar [bundle_manifest.json](../../artifacts/m4_runtime/runtime-profitability-control-20260925/bundle_manifest.json) lists each archived payload file's byte size and SHA-256. The archive is content-addressed and the builder refuses to overwrite its destination. Original ignored raw files remain on the measurement machine; the archive is the portable review copy.

## Freeze-hash metadata closure

The formal-start commit is `202109717754bc62f889d19b5fbb141bfc3cc529`. The actual calibration-freeze SHA-256 is `3c179a35f046b57edb4ddc8772a1aba609b496878efc2b7849a66947c8b7830b`. The digest recorded in the qualification report, global and per-attempt formal-start markers, and formal manifest is `21592be38c0c477f63cea819b96b5b12cfea4529c131f6914b761a06ae5e518b`—the SHA-256 of `build/manifest.json`.

The cause is a local variable shadowing bug in the frozen `frozen()` function: it returned the last artifact-loop path (the build manifest) instead of the calibration-freeze path. This is a **metadata-recording defect, not a measurement mutation**. The freeze file was byte-identical to the file committed at formal start. The original raw observations and markers were not modified. The versioned recovery analyzer verified that committed freeze and qualification report, all frozen source/model/calibration/policy hashes, and every complete attempt before applying the originally frozen analysis formulas. Its output and `provenance/provenance_closure.json` are in the archive. The original pipeline `STOPPED` status is retained as evidence of the analysis gate failure; this closeout records the separately audited recovery.

The defect should be fixed in a later maintenance PR with a regression test asserting that `frozen()` returns the calibration-freeze path and that its SHA-256 equals the actual freeze file. That maintenance code must be identified as **post-measurement** and must not be presented as the source used for this formal experiment. PR #26 contains the exact formal source plus the archived recovery evidence. Paper Section 7 integration belongs in a separate PR after this study PR is reviewed and merged.
