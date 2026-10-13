# Delivery-only Windows path recovery

The formal experiment completed all 3456 requests plus144 warmups at 2026-10-11 19:22 China time. Analysis, postchecks and archives completed. Local author-archive extraction then failed because the long checkout prefix plus an upstream UI source path exceeded Windows MAX_PATH. The original traceback and partial restore are retained.

`restore_short_path.py` invokes the **unchanged frozen** restore checker with only its extraction-parent variable redirected to `D:/hsr`. The longest author-archive relative path is188 characters; the shorter root brings it below260. Archive bytes, every indexed file hash, all3530 private source hashes, server hash and independent CPU result reproduction still undergo the original checks. The script neither imports an inference driver nor modifies the frozen code, F0B payload, binaries, models, statistics or results. Its receipt checks the complete request-start count before and after.

Recovery commands from the real study checkout:

```powershell
python benchmarks/jsa_third_family_v1/delivery/restore_short_path.py
python scripts/platform/jsa_third_family_v1/control/autorun.py --resume-post
```

The second command resumes only delivery: commit/push scientific evidence, restore actual authenticated GitHub archive bytes, independently reproduce RESULTS.json, commit completion receipts, and update existing draft PR84. It never replays formal requests. The scientific ZIP's maximum relative path is128 characters, so the original remote restore destination is within MAX_PATH.

The already sealed author/scientific archives remain byte-identical. This recovery helper and its provenance receipt are an additional Git delivery appendix; they are not represented as part of the original ZIP or prospective F0B. The real execution receipts, not this description, determine restoration and publication success.
