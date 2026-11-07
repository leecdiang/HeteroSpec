# Evidence interpretation notes

- `RUN_SPEC.start_epoch` is a deliberately conservative budget epoch preceding
  the first observed preparation timestamp; it is not an independently certified
  author-message receive timestamp. Every actual controller/host UTC is retained.
- Legacy native `failed_call` names the next unread record slot when a completed
  readback mismatches. Its default -1 statuses do not describe a second graph
  call. The actual mismatch is `calls[0].ordinary_exact=false`, with completed
  graph/sync and full finite output. All twelve affected hosts executed one graph,
  independently supported by their output/trace records; no slot was retried.
- Signed-ULP zero crossings are calculated by `audit_final_rtx.py`, which wraps
  the frozen auditor's byte checks and corrects only its diagnostic integer
  ordering. Four deterministic CPU edge cases pass. Admission and timing rules
  remain the frozen exact-byte rules.
- The closure inventory's first empty PowerShell pipeline did not create a file;
  the CPU refusal is retained. An explicit empty process-array inventory then
  verified that no native collector remained. No GPU rerun or extra probe.
- A short CPU fault-injection audit overlapped session0. All observations stay in
  the analysis; it did not change gates, remove outliers or alter the schedule.
- Raw member verification and new-interpreter recomputation are local, on the
  same laptop. Git remote-byte authentication is a different operation and does
  not imply the large raw ZIP was uploaded or externally reviewed.
