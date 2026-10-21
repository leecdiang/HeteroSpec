# B570 final partition, operator, KV-state and timeline closeout

Read [RESULTS.md](RESULTS.md) for audited results and limitations. This directory is the independent result of PR #100 and does not modify historical studies or the paper.

Evidence: COMPLETE_CAS.json and ARCHIVE_MANIFEST.json pin the archive. Concatenate archive/part-*.bin in lexical order, check bytes and SHA256, then run code/restore98.py --cas COMPLETE_CAS.zip --dest <fresh-folder>. Run the restored code/verify100.py --root <fresh-folder> --output <fresh-analysis>, code/test_verify100.py <fresh-folder>, and baseline/pr99/code/verify98.py for inherited audit. code/historical_capsule100.py verifies every object of the complete inherited PR97/PR92 capsule. Actual target GGUF remains an external byte-pinned prerequisite and is fully rehashed by the auditor. No model forwards are needed for CPU audit.

F0 authentication and dataflow amendments are immutable prospective evidence. LOCAL_RESTORE.json and REMOTE_RESTORE.json are separate post-seal receipts; exact complete-output and restoration failures are retained. New paid cost ratios remain NULL and original R_stock failure remains unchanged.
