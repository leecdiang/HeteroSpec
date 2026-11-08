# Completed-scope export and readback

`transfer_export.py` extends the allowlisted exporter/readback interface from
qualified Linux result commit `592abdfe9267fd97ecbde18cd0ee9a1bfc319e20`.
It does not modify frozen run trees or grant native qualification.

Use the exact runtime modules from that result, the actual lane build directory,
and a terminal completion receipt. Accepted statuses are `COMPLETE` or
`QUALIFIED_FORMAL_NOT_RUN`; the latter explicitly grants no formal performance
result. The original failure epochs and incomplete captures remain included.

The exporter holds the same `STUDY_SCHEDULING.lock` as the GPU pipelines while
reading all bytes, compressing, and independently reading back the bundle and
every indexed private capture. Export/readback cost is recorded separately from
native service. It cannot overlap another pipeline's formal timing.

Example arguments, using user-defined paths without credentials:

```sh
python -B benchmarks/server_expansion_v1/transfer_export.py \
  --work "$HS_WORK" --runtime "$HS_RUNTIME" --builds "$HS_BUILDS" \
  --completion "$HS_COMPLETION" --support-manifest "$HS_SUPPORT_MANIFEST" \
  --out "$HS_FRESH_EXPORT"
```

The support manifest lists exact reviewed external scientific files, each with
`name`, `source` (private local path) and original `sha256`:

```json
{"schema":"linux-transfer.exact-support-files.v1","files":[]}
```

Include the actual completion receipt in this manifest when it is outside the
run tree. Other support records include retained coordinator failure/status/log
files, exact asset-check and rule-freeze summaries, admission evidence, and
source/build binding receipts. Full vocabulary dumps, model weights, download
redirects/headers and machine inventories are excluded. Never use broad external
directory globs. The manifest's private-byte hash is recorded in `EXPORT_SCOPE`;
public records use stable `support/` names.

`TEXT_INDEX.json` binds original private text bytes and sanitized public bytes
separately. Paths/allocated UUID/authorization labels become placeholders;
original hash fields are preserved. All launch/request JSON, selected-device
resource samples, native service/physical receipts and available scientific logs
under reference, qualification, negatives and panel are included. Network or
credential patterns cause failure, requiring review before publication.

`BINARY_CAPTURE_INDEX.json` includes every `.f32`/`.bin` under this lane's
reference, all retained qualification epochs and panel, including failed partial
captures. Every byte is hashed and then independently read back. Raw captures
remain private; neither this index nor `LOCAL_READBACK.json` asserts public raw
archive availability or third-party reproduction. Source builds and model
identities remain separately pinned for reconstruction.

`scientific-records.json.gz` uses the predecessor bundle schema and deterministic
gzip metadata. After upload, fetch the exact public commit's parts and verify
their concatenation/hash plus every indexed public text record with the same
`readback_export.py`. Public text readback and local private capture readback are
separate claims and must be reported separately.

`TRANSFER_EXPORT_SELF_CHECK.json` records a zero-forward integration check of
the exact exporter bytes: bundle roundtrip, complete failed-partial binary
readback, UUID/path sanitization, inventory exclusion, and rejection of a test
credential pattern. It is an exporter check, never model qualification.
