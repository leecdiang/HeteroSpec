# Evidence delivery

Native execution, independent raw reconstruction and remote delivery are complete.
The [published evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-reference-repair-v1-evidence-20261102) accompanies
[Draft result PR159](https://github.com/leecdiang/HeteroSpec/pull/159).
There are 133 raw ZIP shards containing 51496 files
(68271459792 uncompressed bytes;
55892670590 archive bytes). Every shard was freshly
downloaded; archive size/SHA256, exact inventory and every decompressed member's
size/SHA256 passed. All separate transport metadata assets and ZIP members also
passed fresh remote readback. After publication the raw index was additionally
downloaded with repository authorization and normal HTTPS certificate verification.
The repository is private: authorized readers are required, and its permissions
were not changed. Anonymous availability is not claimed.

[RAW_ACCESS.json](RAW_ACCESS.json) pins the full remote index and every shard.
Full index SHA256: `80abc43b9d68dd9fa61effb93d7ce9e0172ff0645c65051a96a9e10fb69156f0`.
The immutable full index retains its packaging-time `remote_uploaded=false`;
[UPLOAD.json](delivery/UPLOAD.json) and
[REMOTE_READBACK.json](delivery/REMOTE_READBACK.json) establish subsequent success.
See [metadata readback](delivery/DELIVERY_METADATA_READBACK.json),
[receipt readback](delivery/RECEIPT_ASSET_READBACK.json), and
[published access verification](delivery/PUBLISHED_ACCESS_READBACK.json).
TRANSPORT_METADATA.zip, METADATA_MEMBERS.json and DELIVERY_ASSETS.json on the release
retain and pin the transfer sources, handoff and per-part receipts. The native/source
archive is pinned to commit `0ccedc064214c7a758564bd6be1aa9a0c81bcb99`; later transport
code and delivery reports are separate commits in the result PR. No native request
was added during transport.

Two closeout failures are retained: publication succeeded, but the first checker
asserted against a cached draft asset URL; the next anonymous download returned404
because the repository is private. A fresh post-publication authenticated index
download passed. These are access/reporting corrections, not missing raw evidence
or scientific retries. Logs, receipts and corrected closeout source accompany this PR.

The raw bundle retains every new epoch, failed attempt, full vector/state artifact,
schedule, native receipt and cumulative ledger. The closeout snapshot also preserves
build adaptations, source, operations logs and reports. Runtime/weight binaries are
not distributed. Local configuration-only files named CONFIG.json or LOCAL_PATHS.json
are excluded by the supplied archiver; native logs retain host paths.

Packaging uses the supplied archiver with 512MiB uncompressed shard groups. Every
local ZIP is reopened and every member's size/SHA256 is verified. Remote transport
then downloads a new copy of every shard and repeats archive/member checks. Only a
successfully verified temporary remote duplicate may be removed after a durable
receipt; original raw data, local archives and failed downloads remain.

Upload to the unpublished draft overlaps packaging. The supplied packer creates
the next ZIP only after the preceding ZIP's complete local readback and hash; this
is the upload readiness barrier. The final immutable index must match every
uploaded shard's size/SHA256. `diagnostics/stream_upload.py` records each transfer,
uses no clobber or silent retry, and does not replace the subsequent fresh remote
download and all-member verification.

After four successful sequential transfers, a quiescent handoff switched to
`diagnostics/parallel_upload.py` (at most five concurrent transfers). Existing
assets are adopted only when prior success receipts, local size/SHA256 and GitHub's
uploaded-state SHA256 digest agree. The original uploader's intentional stop and
the temporary readiness-barrier hold/restoration are retained in transport records;
no active transfer was interrupted and no remote asset was deleted or overwritten.
`diagnostics/parallel_verify.py` performs the fresh index/archive/member readback,
with at most five temporary shards and durable per-part receipts before cleanup.

The native/source snapshot necessarily predates its own transport receipts. Final
upload/readback receipts are separate release assets and files in the result PR;
this avoids a self-referential archive manifest. It does not change native data or
the frozen candidate. Same-host remote readback proves transport integrity, not
third-party scientific replication.

Original PR156 evidence remains at the
[unchanged prior release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-dense14b-transfer-v1-evidence-20261101).
Its forty requests and placement correction v2 remain separate. Pinned original
delivery indices and correction/readback metadata are also retained under
`provenance/pr156_original_delivery` in the new raw bundle. Those are historical
readback receipts, not a new download of the original release in this run.
