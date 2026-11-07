# B570 PR81 delivery closure

Delivery status: **COMPLETE**. The scientific matrix, independent CPU verification, local fresh restoration and actual GitHub fresh restoration/readback all passed.

Executed plan head: `0a95a64805536323b0e8ae11784eaab150f91dcf` (PR #81).
Verified scientific/CAS source head: `33cb8bfddb4f080526dba82bc1c099be29b58860` (result Draft PR #82).
Actual remote restoration/readback passed at **2026-10-10 23:32:40 Asia/Shanghai** (`2026-10-10T15:32:40Z`). This transport receipt is being published in a subsequent metadata-only commit; its final remote head is checked separately, avoiding a self-referential commit hash.

All **560/560** requests completed: 32 Qwen bridge, 128 SmolLM2 discovery/capture controls, 384 formal requests and 16 warmups. Forty owned sessions closed; zero failures, missing records, scientific retries or auxiliary decodes. The actual owned-session GPU upper bound was 0.5672310697 hours, within the frozen budgets.

Independent CPU verification passed **12,042 checks**, including actual KV/F32 arrays and five negative contract tests. All four arms passed the fixed first-runtime-EOG-inclusive-or128 endpoint contract on all24 tasks/four rounds. N and C had complete-raw suffix differences; endpoint qualification does not certify raw losslessness or functional code accuracy.

Host whole-request ratios (baseline/C, per-task four-round median then all24-task geometric mean): R/C **0.5461389079**, M/C **0.5615619464**, N/C **12.9058341610**. C cost about **1.83 times ordinary R**; all24 tasks were slower than R in every round. Natural-state discovery was **NO_TRIGGER**. No cross-date robustness, unique operator cause, production or energy claim follows.

The392,608,205-byte CAS archive has SHA256 `fb05dcb8381b012f8e97de4312240679523d6c27446097332f348eb9af6c6850`. Eight Git-hosted SHA-addressed parts restore **3,319 logical files /2,603 objects**. Both local and actual fresh remote restorations checked every part, archive CRC/SHA, object and logical file, then independently rederived the scientific outputs identically. Eighty-two source/CAS files also matched local checkout, fresh GitHub checkout and Git blob bytes. No model forward was launched during closure/restoration.

[Remote receipt](REMOTE_READBACK.json), [local receipt](LOCAL_CAS_RESTORE.json), [CAS index](CAS_INDEX.json), [restoration procedure and host dependencies](RESTORE.md), [scientific report](REPORT.zh-CN.md), [complete formal matrix](D_VERIFICATION.json).

`DECISION.json` preserves its pre-transport `PENDING_CAS_AND_REMOTE_READBACK` field as sealed evidence; this report and the separate transport receipt record its now-complete delivery. Original Qwen/Smol model weights and installed recorded module paths remain hash-bound host dependencies. The result PR remains Draft/unmerged.
