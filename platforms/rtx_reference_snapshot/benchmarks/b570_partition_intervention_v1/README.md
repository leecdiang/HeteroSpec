# B570 live partition intervention V1

This independent additive study measures a prospective sampled same-state target partition intervention. Read ENGINEERING_PLAN.md, ANALYSIS_FREEZE.md and the preserved STUDY_PROTOCOL.md. Existing B570 results and the manuscript are read-only.

The original engineering frontend/runner/core checker were committed before R0. The complete endpoint characterization and validator supplement are frozen before any reserved inference. They do not change execution semantics, technical qualification criteria, the physical partition intervention, the sampled checkpoint rule or dataset selection.

Authorized stage order:

1. Generate the separate frontend with build_source.py and build CMakeLists.txt against read-only pinned libraries. Run audit.py and `study.py prepare`; commit and push the engineering plan.
2. Run `study.py qualify`. The first failure closes INTERVENTION_NOT_FEASIBLE, with zero reserved inference. Never repair/requalify V1 to rescue a failure.
3. Only on PASS, run `study.py freeze`; commit and push every identity/qualification/selection/schedule/analysis file. Run `study.py formal` exactly once.
4. Run `deliver_complete.py closeout`; commit execution/closeout records. Run `deliver_complete.py archive`; its clean extraction invokes the official hardware-free verifier, `verify_complete.py`. Commit content-addressed parts and ARCHIVE.json, push and open a draft PR against main. Do not merge.

Offline: reconstruct the ordered SHA256-addressed parts using ARCHIVE.json, extract the archive, and run `python scripts/platform/b570_partition_intervention_v1/verify_complete.py --root .`. Alternatively run `verify_archive_complete.py --archive artifacts/b570_partition_intervention_v1/ARCHIVE.json` from the source checkout. No GPU or model weights are required for offline checks.

Formal reports separate complete raw score records, immediate target decisions at a common proposal-conditioned prefix, and downstream continuation trajectories. The raw-core checker is retained unchanged for source identity; verify_complete.py is the official validator and supplies the joined endpoint classification. Full NO_EFFECT requires unchanged scores, immediate decisions and downstream trajectories. R0 observations are exposed diagnostics and never join the reserved 24 x 3 denominator.
