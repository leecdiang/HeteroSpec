# RTX prefix reuse v1: completed native negative result

Result PR: https://github.com/leecdiang/HeteroSpec/pull/174

The original RTX5070 Ti Laptop host completed 12 calibration roots, all 32 held-out roots, four paired sessions (512 measurements plus 512 immediate warmups), and the eight-root aligned control. Full native qualification passed. Frozen AUTO selected WB-cut for every bin and did not meet the registered usefulness screen: its geometric service time was 3.021310s versus 3.002246s for WB-cut, a 0.635% point slowdown. The baseline/AUTO family-adjusted interval was [0.974813, 1.012617]; all three primary intervals crossed one. No extra rounds or policy retuning were performed.

The exact-token deployment retained natural crossings in four of 32 test roots. Predeclared 32/64-token rounding scenarios eliminated crossings, with some loss of reusable prefixes. This file-backed RTX lifecycle is separate from B570's host-memory lifecycle; no pooled hardware estimate is claimed.

Calibration campaign cost was 2038.781179s. All 2026 conservative reservations, 1957 completed receipts and 69 reserved units without complete receipts remain accounted for. Prior source epochs, incomplete attempts and original references remain preserved.

## Assets and SHA256

| Asset | SHA256 |
|---|---|
| Frozen runtime | `24d647dbf7bedb1003e766363d24cad04d55094290f1b06d6e17a342cb328d12` |
| Complete native source kit | `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac` |
| Pre-test calibration archive, reconstructed | `cc9a004e1e6af7d324cad2dcf27ed987222153414955789c5614d8c4c32f7d7c` |
| Final raw archive, reconstructed | `5850cd9e839f099c6105ae54ce144494d32ee6e058b32cb3701e8f2272de5570` |

The final archive is 7,763,135,840 bytes and retains 56,588 original paths through 8,988 content-addressed blobs. Download all 58 `raw-evidence.zip.partNNN` files and `raw-evidence.zip.parts.json`. The calibration checkpoint has its own nine parts and manifest. Part sizes and individual hashes are in each manifest; neither archive can be reconstructed from a subset.

From a checkout of the result branch, in `benchmarks/rtx_prefix_reuse_v1/execution`:

```text
python parts.py join <download-dir>/raw-evidence.zip.parts.json <download-dir>/raw-evidence.zip
python archive.py verify <download-dir>/raw-evidence.zip
```

`download_parts.py raw-evidence.zip <fresh-directory>` automates download, hash checks, joining and reconstruction through authenticated GitHub CLI access. The archive verifier reconstructs vector/state qualification, all formal slots, aligned controls, separate restore diagnostics and the root bootstrap. It does not execute a model.

For original-deployment replay, follow `README.md` and `reproduce.py`. The frozen worker requires a supported Windows NVIDIA device description containing5070 and the exact Qwen3-8B Q8_0 model hash `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`. Model weights are excluded. Use `--prepare-only` to verify and rebase a manifest without new model requests. Any actual replay is a separately charged experiment.

Restored-download checks and preparation checks are distinct from third-party native replication. See the result PR's final delivery receipts and `RESULTS.md` for completed verification and limitations. No merge or manuscript update accompanies this release.
