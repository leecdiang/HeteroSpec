# Evidence delivery

Native execution and independent raw reconstruction are complete. Transport
verification is pending at this source snapshot. The final result PR will replace
this status with the actual release, access index and fresh remote readback receipts.

The raw bundle retains every new epoch, failed attempt, full vector/state artifact,
schedule, native receipt and cumulative ledger. The closeout snapshot also preserves
build adaptations, source, operations logs and reports. Runtime/weight binaries are
not distributed. Local configuration-only files named CONFIG.json or LOCAL_PATHS.json
are excluded by the supplied archiver; native logs retain host paths.

Packaging uses the supplied archiver with512MiB uncompressed shard groups. Every
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
