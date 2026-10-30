# Completed-data incremental archive, batch 1

This batch retains all completed main data through date0 (196 qualification,
336 formal and28 warmup requests) and all54 registered Llama diagnostics,
including A0 historical raw evidence. The source snapshots contain 38,087 files
and 24,655,737,262 bytes. Snapshot member hashes were checked against every
committed request payload pin: 31,936 main pins and5,970 diagnostic pins.

The transport is lossless: 8,541 unique SHA256-addressed objects represent all
38,087 logical paths. Exactly equal contents are stored once; different bytes
are never merged. The mapping preserves each original snapshot/path, length
and SHA256. There are39 object ZIPs totalling3,765,674,413 bytes. The earlier
48 ordinary ZIP parts and both old indices remain retained locally; they were
not substituted for a verified remote delivery claim.

The release is
[RTX scope transfer v1 incremental raw evidence](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-scope-transfer-v1-evidence-20261030).
Use `STATUS.json` and the downloaded-object receipt for actual completion.
An existing release or a successful upload alone is not readback verification.
The receipt verifies every downloaded ZIP, every decompressed object, every
logical path mapping and both freshly downloaded mapping indices.

## Recover original paths without a GPU

Download all assets matching `completed-through-day0.*` from the release to a
fresh directory. Use the committed `OBJECT_PARTS.json` as the trusted index;
its SHA256 is
`ae2fcd4a0333bb2d594a21d6e48b76f8ddb78d4162ccaa090eb72623a50fcbe0`.

```text
python scripts/experiments/rtx_scope_sidecar_v1/restore_objects.py --download DOWNLOAD_DIR --index benchmarks/rtx_scope_transfer_v1/sidecar_execution/archives/OBJECT_PARTS.json --index-sha256 ae2fcd4a0333bb2d594a21d6e48b76f8ddb78d4162ccaa090eb72623a50fcbe0 --out FRESH_RESTORED_DIR
```

The standard-library-only tool validates parts and objects, rejects traversal
and overwrites, restores each original member and checks its bytes and SHA256.
It retains the verified object store under `.objects`; allow at least40 GB of
free space for ordinary copies of the original paths and the object store.
It does not load a model or issue any request. Three CPU tests exercise exact
restoration of duplicate contents, corrupted archives and unsafe paths.

The main restore root is `FRESH_RESTORED_DIR/main-through-day0`; diagnostic data
is under `FRESH_RESTORED_DIR/llama-diagnostic`. External models, native binaries
and numerical DLLs are not redistributed by these raw evidence archives; their
exact pins and existing source/build references remain in the preserved bundles.

Future completed dates must be separate increments and must keep this batch's
indices and payloads. Archive copying, compression, uploads, download verification
and restoration on the experiment host must remain outside formal timing.
