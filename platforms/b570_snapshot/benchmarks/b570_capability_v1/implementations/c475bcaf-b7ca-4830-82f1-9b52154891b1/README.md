# Frozen B570 CPU capability implementation

Measured UUID: c475bcaf-b7ca-4830-82f1-9b52154891b1. Protocol commit: bdf7095ad9f48a620359978b965cf227acd03984.

These are the exact six revision-2 modules measured under CAPABILITY_FREEZE.json. The raw archive preserves the original src/rev2 layout and supporting scripts, all failed development attempts and measured evidence. No post-freeze fixes or measurement retries were made.

The read-only verifier's frozen production interface is verify.audit(root, relative_run, manifest, tool_binding). Do not use its unused __main__ wrapper: it catches its own SystemExit(0) and prints a misleading failure. This known issue and the audit() entry were disclosed before freezing. No final independent scoped-clean verdict is claimed.

This is evidence of the three-check / three-hour CPU capability lane only. It does not qualify the historical eight cases, complete outer process accounting, GPU execution, scientific results or ENGINEERING_READY.
