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

Closeout repair status:

1. **PASS** — the remote recovery object is 694239 bytes and has Git blob SHA1
   `efa399823049ee57968b0bfa00b0ea41cca9c975`, identical to the local object;
2. **PASS** — repository-wide status and mechanism documents no longer say 358H
   is pending;
3. **PASS** — this audit and the formal-execution amendment are committed;
4. **PASS** — the branch incorporates current `main` through merge commit
   `8d15dbc4c86b6317e626b5a7aa42862c75af7a08` and is zero commits behind;
5. **PASS** — the PR description identifies the compressed bundle as
   authoritative and does not claim that truncated preview blobs match the
   original manifest.

The transport-recovery and documentation gates are complete. The PR may move
from audit hold to ordinary review after its final changed-file/CI check.

The transport incident does not invalidate the scientific result because the
complete source files, hashes, and independently verified compressed recovery
artifact survive. It is nevertheless a repository reproducibility blocker until
the recovery representation is committed and documented.

