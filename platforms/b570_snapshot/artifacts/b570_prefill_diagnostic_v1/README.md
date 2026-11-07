# B570 prefill diagnostic v1 — evidence archive

This is a bounded, content-addressed raw evidence exception for the authorized new study. All 360 formal records and 120 G0 controls are retained. Deduplication stores identical file contents once and restores distinct ordinary files; no generated IDs, endpoints, traces or KV/pending-logit bytes are changed.

The 30 ordered `.part` files form a 1,473,070,703-byte compressed content-addressed archive, SHA256 `29ff8282a2751342c834d5a81c27c76daedab611205889a5a7c6ee8ec4ee45d8`. `ARCHIVE.json` binds every part and the complete restored-file manifest. `REMOTE_MANIFEST.json` lists every restored file and SHA256.

Restore into an empty directory from a checkout containing all parts:

```powershell
python scripts/platform/b570_prefill_delivery_v1/restore.py --archive artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json --dest C:/hs/prefill-restored --receipt restore-receipt.json
```

Restore verifies every part, the concatenated archive, all 4,073 reconstructed files, 360 formal arrays/endpoints, G0 arrays and sham traces, T1-before-N1 order, frozen execution source bytes, and summary comparisons. It uses no model inference. The fixed independent raw verifier is kept byte-identical and runs with a separate temporary report directory.

Original unabridged 18,950,381,810-byte local capsule SHA256 `4ce6f65211c2847088ca4318746d47da369ea7596a88469be11c0e6aaecc5896` remains on persistent local disk. This portable container has different compression/metadata bytes. Model weights and rebuildable runtime binaries remain excluded under docs/data_policy.md; their recorded identities do not authenticate omitted bytes offline. Included pinned upstream source retains its MIT license. This delivery remains in the existing private repository; it grants no new public repository license.

`DELIVERY_SEAL.json` is a post-outcome archival binding, not a retrospective independent timestamp for the original predictions. `REMOTE_DELIVERY.json` and `DELIVERY_REPORT.md` provide the final upload/read-back status; the earlier execution-closeout snapshot remains unchanged.
