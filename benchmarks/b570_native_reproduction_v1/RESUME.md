# Resume / review

No required native work remains for the PR146 B570 scope. Review the result PR; do not launch another optimization or timing campaign as a continuation of this package.

The final run root is `C:/hs/b570-native-reproduction-20261026`. Read `RESULT.md`, `SUMMARY.json`, `TECHNICAL_AMENDMENT_A2.json` and `LOCAL_DELIVERY.json` first. Original `capture-a1` evidence is preserved. All successful later receipts use the A2 diagnostic correction. Existing receipt/output paths are never reused.

Reverify the complete lossless archive offline, writing a new receipt:

```powershell
python -X utf8 benchmarks/b570_native_reproduction_v1/verify_delivery.py --archive C:/hs/b570-native-reproduction-20261026/B570_NATIVE_DELIVERY.zip --out C:/hs/b570-native-reproduction-20261026/REVIEW_ARCHIVE_NEW.json
```

To independently repeat the numerical audit without launching a model, use `audit_request.py` with an archived `evidence/smoke-N-a1` directory and `references/qual-N`; use `audit_stage.py` with `fixture`, `evidence/capture-a2` and `evidence/stage-a1`. Set a new output receipt for each call. `collect_results.py` reproduces the original run-root accounting summary and verifies loaded-module identities; an archive relocated to another machine requires mapping the explicitly recorded runtime paths first.

To perform a new native reproduction on another B570 host, obtain the model-free archive plus the two externally supplied exact model hashes. Follow `README.md` in a new source/build/run directory and seal a new runtime manifest. Native runs are not needed to review the archived evidence and are not scheduled by this closeout. A different driver/toolchain is a new qualification identity.

If local evidence is unavailable, the concrete missing item is `B570_NATIVE_DELIVERY.zip` with the checksum in `ARCHIVE_RECEIPT.json`; small Git fixtures alone do not replace its complete request vectors. No user credential or model weight is included in that archive.
