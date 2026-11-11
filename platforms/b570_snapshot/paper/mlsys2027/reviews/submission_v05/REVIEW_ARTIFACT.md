# Reviewer I — artifact and reproducibility review

Reviewed source: PR #27, `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`.

## Verdict

**The core M4 runtime result is reproducible from the portable bundle without model execution.** I ran the documented offline verifier successfully against the archive with its expected SHA-256. The archive retains the four final raw-data stages, token arrays, attempt records, frozen sources, original erroneous hash fields, and the original analysis-stop state. The remaining actionable issue is evaluator guidance, especially the Git-history prerequisite of the broader manuscript check. The 358H runtime material supports a compact diagnostic audit, not independent raw-trace replay; the manuscript already discloses that boundary.

This review used existing data only. I did not run timing, search policies, change experimental files, or read other reviewers' reports. I inspected the manuscript README/Makefile, runtime appendix and ledger, M4 closeout/preregistration/freeze/analysis, archive builder and replay/recovery code, sidecars, and the six pinned 358H snapshots. No full paper-build pass or independent Git-chronology verification is claimed here.

## Checks actually performed

The following command completed with `status: PASS`:

```sh
python3 scripts/platform/m4_runtime/recompute_evidence_bundle.py \
  artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz \
  --expected-sha256 af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab
```

| Check | Observed result |
|---|---|
| Archive size and digest | 1,298,101 bytes; expected SHA-256 matched |
| Extracted payload integrity | 62 files verified against sizes and hashes |
| Complete observations | Baseline 240; candidates 1,080; qualification 144; formal 540 |
| Recomputed calibration selection | `E8_M000` |
| Direct generated-ID equality | Qualification 48/48 and formal 180/180 for each speculative condition |
| Held-out estimator | 60 prompts; three repetitions reduced to condition medians |
| Target/Guard | 1.3113869084; CI [1.2486784089, 1.3786628977] |
| Target/Always-Spec | 1.3468940492; CI [1.2867003677, 1.4088049231] |
| Guard/offline oracle | 1.0277867248; CI [1.0136781576, 1.0445879575] |
| Fallback requests | 0.3055555556 |
| Preserved pipeline state | `STOPPED`, with formal stage `COMPLETE` |

I additionally ran an independent read-only script verifying the sidecar manifest digest, 34 corresponding locally available payload hashes, all six 358H snapshot hashes, and all 116 split identities for counts, disjointness, inventory digest, and exact preregistered rank. That script also reconstructed the three geometric means and their 10,000-resample intervals from `FORMAL_ANALYSIS.json:per_prompt` using the specified random-stream order. All checks passed. This latter calculation validates processed-summary arithmetic; raw-data reconstruction is provided by the separately executed bundle verifier.

The archive was initially unavailable in this downloaded sparse snapshot because the connector did not return its large-file body. The coordinator subsequently retrieved it through the download URL, after which the checks above ran. This was a resolved retrieval limitation, not evidence that the upstream artifact was absent.

## Findings and justified changes

### I-1. Document the two reproducibility entry points and Git prerequisite

**Artifact issue; medium priority; documentation change.** `benchmarks/m4_runtime/M4_RUNTIME_CLOSEOUT.md` already gives a sufficient, exact, standard-library-only command for M4 numerical replay. However, `paper/mlsys2027/manuscript/README.md` leads evaluators to `make check` and lists TeX/Python dependencies without stating that `scripts/validate_runtime.py` executes `git show` for commit `12f387d117fb52cc0ecc688931b9925abb29e71e`. The ledger describes this 358H source as a separately pinned, unmerged branch. A source ZIP or checkout lacking that object cannot complete the broader check, even with every compact snapshot present and correctly hashed.

Add a short README subsection linking the M4 closeout command and distinguish:

- **Portable M4 replay:** Python standard library, archive, verifier, expected digest; no models, M4 hardware, or Git history required.
- **Full manuscript validation:** listed packages and build assets, plus the historical Git objects used by validators. State the required source/ref acquisition procedure for the pinned 358H object and other history-dependent checks, and make the working directory for `make` explicit.

Document the requirement rather than silently skipping Git checks or changing frozen records. This recommendation does not require a new experiment or an expanded artifact.

### I-2. Repair the stale paper-workspace entry point

**Artifact/documentation issue; low priority.** `paper/mlsys2027/README.md` still says runtime/software co-design is future work and not a measured contribution, and tells readers that pursuing it would require a separate study. The manuscript README, runtime ledger, closeout, and current paper describe the completed M4 runtime study and qualification-closed 358H outcome. The paper-root README is presented as a current entry point rather than a clearly historical record.

Update only its current-status/navigation text to direct evaluators to the runtime supplement and current manuscript. Preserve historical preregistration and experiment records. This reduces authority ambiguity without changing claims or numbers.

### I-3. Keep numerical replay distinct from historical provenance verification

**No demonstrated paper defect; guidance clarification.** The archive replay reconciles the actual calibration-freeze digest (`3c179a…830b`) with the erroneous build-manifest digest (`21592b…18b`) in original records. The recovery analyzer and archive builder additionally contain explicit comparisons against the formal-start Git commit `202109717754bc62f889d19b5fbb141bfc3cc529`. The portable verifier itself does not fetch or authenticate that historical Git object; it checks the archived closure and mutually consistent payloads. Its PASS is therefore numerical/data-integrity reproduction, not a new independent proof of temporal precedence.

The existing appendix correctly describes the versioned recovery and retains the exception. A sentence in evaluator guidance explaining the two verification layers is sufficient. Do not fix the frozen helper or replace erroneous original metadata as part of paper cleanup. The recorded source and post-measurement recovery must remain distinguishable.

### I-4. Retain the explicit 358H audit boundary

**Disclosed artifact limitation, not an undisclosed paper issue.** The six snapshots match the recorded hashes. They explicitly mark the evidence diagnostic and invalid for performance claims, state that no formal R2 data exist, disable R2 authorization, and do not establish a particular rollback bug or changed target semantics. The compact record contains raw-trace hashes and token-level findings, but hashes cannot replace the unavailable local raw traces for independent replay. The README, runtime ledger, and appendix already state this limitation.

Keep those qualifications adjacent to the diagnostic claim. Describe the current checks as snapshot-integrity and compact-record consistency checks, not raw 358H reproduction. Portable raw diagnostic traces could be a later artifact enhancement, but adding them is **nice-to-have outside this review's necessary scope**, not grounds to reopen qualification or infer a runtime speedup.

## Raw retention and scope assessment

The M4 bundle contains `observations.jsonl`, manifests, completion records, warmups, and stderr for each of the four final stages. Inspected formal observations retain generated token IDs, post-prefill latency, control costs, fallback state, and round traces. Formal-start markers, build manifest/binary, frozen source/data, pipeline/launcher logs, and recovery output are present. Thus the headline M4 estimates and exactness counts are not supported solely by derived tables.

The bundle is explicitly a portable copy of the final attempt. R0 and any other measurement-machine-local history are not established as portable by this manifest. Do not expand “complete evidence bundle” into a claim that every historical exploratory or abandoned run has been distributed. The closeout's final-stage wording is appropriately bounded.

No new timing, policy tuning, raw-record modification, or additional performance comparison is warranted by this artifact review. The necessary changes are limited to accurate entry-point guidance and disclosed verification prerequisites.
