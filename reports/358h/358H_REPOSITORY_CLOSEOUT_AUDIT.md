# 358H repository-closeout audit

Audit date: 2026-09-18

## Scientific record

The Phase-3 scientific record is complete: 270 full observations, 90 paired CPU
comparisons, 90 paired NPU comparisons, and no errors or warnings. Independent
recomputation reproduced the published aggregates and exactness counts.

## Git transport incident and recovery

Six large text paths in the initial PR upload were truncated to approximately
80 KiB by an intermediate text-transfer path. The complete local files were not
damaged. The affected content comprises the full and small-gate JSONL records,
their resolved JSON forms, and the per-round CSV (including its top-level copy).

The recovery artifact is:

- `artifacts/358h_threshold_validation/phase3-final-20260918-144458/358h_phase3_complete_evidence.tar.gz`
- bytes: `694239`
- Git blob SHA1: `efa399823049ee57968b0bfa00b0ea41cca9c975`
- SHA256: `2fa6197864b1c6fc7af1c6da31f24ccf224e3dc0933bc1534840117eaee08511`

The gzip-compressed tar contains the complete 34-entry archive manifest and all
34 byte-complete files. A clean extraction was validated against every manifest
size and SHA256 with zero failures. Until the convenient text paths are replaced,
the compressed bundle is the authoritative committed Git representation and the
approximately-80-KiB text objects are non-authoritative previews only.

## Merge gate

The PR must remain a draft until all of the following are true:

1. the recovery bundle Git blob identity and byte count are verified remotely;
2. repository-wide status and mechanism documents no longer say 358H is pending;
3. this audit and the formal-execution amendment are committed;
4. the PR branch is reconciled with the current `main` branch;
5. the PR description names the compressed bundle as authoritative and does not
   claim that the truncated text blobs match the original manifest.

The transport incident does not invalidate the scientific result because the
complete source files, hashes, and independently verified compressed recovery
artifact survive. It is nevertheless a repository reproducibility blocker until
the recovery representation is committed and documented.

