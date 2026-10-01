# Portable evidence packaging

The first packaging attempt stopped at a Windows CopyFile2 path-length error before archive creation. No inference, scientific source, frozen input, raw result, or analysis was changed. The packaging-only `package_windows.py` adapter uses a verified junction at `C:/hs/bpiv1pkg` to this checkout and short temporary paths. It calls the original frozen archiver and clean-extraction validator unchanged. This adapter was added after closeout and is outside the formal inference source freeze.

Reconstruct the archive by concatenating the `.part` files in the order in `artifacts/b570_partition_intervention_v1/ARCHIVE.json`. Verify each part's SHA256 and byte length, the concatenated archive SHA256, and the extracted `MANIFEST.json` SHA256 against that record. Extract into a short path on Windows. From the extracted root run:

```
python scripts/platform/b570_partition_intervention_v1/verify_complete.py --root .
```

The official complete verifier includes the core verifier, serialized KV metadata checks, frozen source and schedule checks, endpoint classification, and retained Git object membership and ancestry proof. `verify.py` alone is the core verifier and omits these supplements. Neither models nor runtime binaries are included; their identities were rehashed on the experimental host before and after formal execution.
