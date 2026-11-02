# Evidence restoration

The final release index and transport receipts will be linked in RESULTS.md after upload and fresh remote verification. Until then, no remote delivery is claimed.

The immutable `RAW_ACCESS.json` maps each archived member to its shard, byte count and SHA-256. Download every shard through an authenticated account with access to the private repository. Verify each archive's size and SHA-256, its exact member inventory, and each decompressed member's size and SHA-256 before using the evidence. The source map records original host paths for provenance; extracting those paths directly is unnecessary.

Archive directories preserve the complete new shared research ledger, failed and successful epochs, PR151 original diagnostic raw, historical reconstruction, source revisions, build receipts, tokenizer and input-pool preparation, all remote-head/PR exposure coverage, and pre-transport operation logs. The numerical source adaptations are in each configuration's `stage/` and complete patched `source/` trees. Failed versions are retained alongside successors. The original metadata4 and Qwen source capsules are also included.

The earlier PR159 complete raw/source capsule remains at [the original reference-repair evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-reference-repair-v1-evidence-20261102), with its own upload and fresh all-member verification receipts. This new archive includes its unchanged ledger/audit and pinned parent source; it does not claim to duplicate the entire earlier 133-shard capsule. PR151's 54-request original raw is included directly in the new archive. Earlier PRs and release assets are neither merged nor overwritten.

Explicit original and newly compiled worker binaries are archived separately from model weights. For local execution, restore the relevant original numerical DLL cohort alongside a worker and check every DLL hash against that worker's build receipt. The original source and model cohorts must match the archived binding. Model weights are not included; use the immutable model identities from `ORIGINAL_BINDING.json`. The vocab-only helper does not perform model forward calls.

Saved raw records can be independently audited without a GPU. Native reproduction requires a compatible Windows RTX environment, actual resource admission, the finite Job/handshake runner, a fresh prepared epoch and an append-only resource ledger. Historical absolute paths must be mapped explicitly; do not alter an old epoch to make it pass a new host's identity checks. CPU reconstruction is not a substitute for native validation.

For a restored archive rooted at `<evidence>`, use the delivered helper sources:

```text
python -B independent_cost.py --bundle <evidence>/research/epoch07 --out <new-cost-report.json>
python -B independent_qualification.py --bundle <evidence>/research/epoch07 --pool <evidence>/preparation01/POOL.json --exposures <evidence>/exposure04/EXPOSURES.json --out <new-qualification-report.json>
```

The qualification auditor uses NumPy (host version 2.4.6 under Python 3.11.9) for complete little-endian F32 finite/argmax checks. It independently repeats the registered input selection, endpoint/transaction reconstruction, observer pairs, original-R vector identity, state hashes and layer coverage. The optional restored pool/exposure paths must retain the exact pre-output hashes. The cost auditor uses only the Python standard library and includes every warmup and measured record.

Transport creates receipts after the raw archive is sealed. Those receipts and the delivery sources are distributed in a separately indexed metadata asset, also freshly downloaded and checked. Same-host upload/download verification demonstrates byte delivery; it is not third-party scientific replication. The private repository's access controls are retained.
