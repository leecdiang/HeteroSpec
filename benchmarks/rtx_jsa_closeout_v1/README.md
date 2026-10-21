# PR140 RTX S0 result package

Result: **S0_BLOCKED_MISSING_COVERAGE**, with zero scientific model requests. Read [RESULT.md](RESULT.md) and [PAPER_ADDENDUM.md](PAPER_ADDENDUM.md).

`audit_pool.py` produced the unregistered, bounded vocabulary-only census. `verify_s0.py` independently reconstructs it without importing the producer or starting native processes. Source hashes, model/runtime identities, static process receipts, the raw archive and complete unstarted scientific slot inventory accompany the result. `RAW_ACCESS_MANIFEST.json` binds the archive bytes. Model weights, numerical DLL bytes, credentials and telemetry are excluded.

To verify without loading any model:

```powershell
python -B -m zipfile -e STATIC_CENSUS.zip fresh-s0
python -B verify_s0.py fresh-s0 --out fresh-reconstruction.json
```

Use a fresh output directory/file. The archive is a static-input/tokenization artifact, not model-output raw data. The original PR140 design files are unchanged. The resource and exposure gaps are not repaired or authorized by passing this verifier.
