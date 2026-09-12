# B570 Fallback V2 Remote-Reconnect Deviation

Run `diagnostic-v1-20260912-170834` completed fast-path V2_raw, frozen HumanEval30, and the six-prompt serialized fallback correctness probe while ToDesk was disconnected. The fallback probe was exact in all 18 paired repetitions.

During the later fallback V2_exact stage, the user reconnected and queried status while the 512-context cell was still running. This violates the frozen remote-session policy for authoritative timing and power. The recorded 512 ratio (`2.0351502644`) is therefore **INVALID / REMOTE-INTERFERENCE**. The immediately following 2048 ratio (`2.0176987408`) is **NOT ADMISSIBLE / REMOTE STATE NOT PROVEN CLEAN**, because no automated clean-disconnect boundary was re-established between the query and that cell.

Both raw observations and telemetry are preserved for audit. They are not promoted as admissible V2_exact, are excluded from cross-platform conclusions, and were not rerun. The fallback correctness finding remains valid because it completed before the reconnection.
