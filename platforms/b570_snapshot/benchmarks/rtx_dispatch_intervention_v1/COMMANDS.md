# Actual execution commands and closed-run boundary

Worktree: D:/hs123. Python: the registered Codex dependency interpreter.
Run root: D:/hs123-57d3eed0-c107-4358-bc4a-ac1008a06e28.

CPU preparation: bootstrap_rtx.py (one-time, isolated paths), inputs_rtx.py,
prepare_rtx.py build, prepare_rtx.py graphs, source_notes.py and unittest discover.
Initial implementation committed4ade6799 before freeze. Pre-GPU path verifier
correction committeded9b2ed4; initial and repair freezes retained separately.

The new runner.py entry executed reference, qualification, capability, admission,
collect0, collect1 in that order. The admission manifest was committed85ccd59c
before any clean measurement. All GPU stage ledgers are terminal and the UUID
is PERMANENTLY_CLOSED. These commands must not be rerun to fill rejected slots.

CPU closure used audit_final_rtx.py, trace_summary.py, identity_audit.py,
verify_archival.py, resources_rtx.py, final unittest, close_rtx.py snapshot/package/
restore/replay, report_rtx.py and publish_rtx.py. The report format correction is
retained outside the immutable main ZIP with the original formatter/draft outputs.

CPU-only fresh audit can target another NEW output directory with the environment
HETEROSPEC_RUN_ROOT pointing to the restored raw directory, using:

    python -B audit_final_rtx.py --out <new-output-directory>

Raw member inventory and ZIP descriptor are at the sibling -archive directory;
fresh restored data and replay receipts are at the sibling -fresh directory.
verify_delivery.py downloads every scoped Git blob and checks actual bytes and
all execution-artifact hashes; it never uploads raw or invokes a GPU tool.
