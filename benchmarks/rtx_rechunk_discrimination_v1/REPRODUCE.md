# Reproduce the bounded rechunk result

The [PR177 result release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-rechunk-discrimination-v1-20261104) contains the complete content-addressed raw archive (split into authenticated parts when necessary). `evidence/ARCHIVE.json` records its full SHA256 and size. The archive retains every native manifest, launch/exit/log, qualification vocabulary vector, prefix/final state, timing receipt, build receipt, frozen source bytes and the new candidate executable. `index.json` maps original paths to SHA256-addressed blobs; deduplication preserves all original logical paths.

Reuse `frozen-runtime.zip` and `native-source-kit.zip` from the [PR174 release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-prefix-reuse-v1-20261104). Their SHA256 values are respectively `24d647dbf7bedb1003e766363d24cad04d55094290f1b06d6e17a342cb328d12` and `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`. These retain the original oracle, all 21 numerical/runtime DLLs, static libraries, complete native source trees and inherited adapter. The new executor differs only by the published `timing-only.diff`; all three arms link the same unchanged packed core. No extra runtime download or rented GPU was used for this study.

For offline verification with Python3.11, reassemble the parts in manifest order, checking each size/hash and the final archive hash, then run:

```text
python archive.py verify raw-evidence.zip
```

This verifies every unique raw blob, all frozen inputs/source bytes, 32 full-vector/final-state comparisons, all observed candidate call sequences, all endpoints and additive phase boundaries, and reconstructs the complete paired analysis directly from receipts. It uses no model/GPU. Ordinary Git checkouts may normalize line endings; the archived `source/` bytes are authoritative for pre-output source hashes.

Prepare or replay an existing manifest on a supported Windows RTX host:

```text
python reproduce.py --runtime frozen-runtime.zip --raw raw-evidence.zip --model Qwen3-8B-Q8_0.gguf --slot science-session-0 --out fresh-replay --prepare-only
```

The model SHA256 is `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`. The helper authenticates the model, runtime, executable and modules, extracts exact referenced snapshots and rebases paths into a new directory. `--prepare-only` starts no model. Removing that option runs the original manifest; this is provided for independent reproduction, **not permission to extend the completed source-host campaign**. A different driver/backend/hardware cohort requires its own qualification. Download verification is not independent native replication.

For source rebuilding, extract the inherited source kit/runtime static libraries, use the recorded `candidate01/binding.json` compiler/link arguments, and rebase their include/library paths to the extracted locations. Use the original Zig0.16.0 Windows compiler and DLL hashes. `worker.cpp` includes the unchanged inherited `probe.cpp`; its transitive source trees and adapter are in the source kit. Original R is reused byte-for-byte, never silently rebuilt with candidate arithmetic.

`audit.py` authenticates the saved PR174 exposure inventory and inputs (including unsuccessful reserved slots) before selecting roots. Full census, prior panel, tokenizer rows and older exposure evidence are in the PR174 raw archive. `coverage.py` deterministically reconstructs the new selection from the saved census, prior panel and delivered exclusions. The scientific runner was frozen before outputs and intentionally refuses to resume or overwrite a campaign. No AUTO retraining, replacement root or favorable offset search is a reproduction step.
