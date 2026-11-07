autoreview chunked findings: 2
[P2] [P2] Require tool evidence references to belong to the sealed tree
benchmarks/b570_cpu8_continuation_v5/runtime/source/tool_binding.py:10
chunk 2/2:

The binding and its intent/initial/final references are read with unrestricted `root / path` joins. Absolute paths and `../` therefore allow verification to consume tool evidence outside the root covered by `manifest_check`. A bundle can receive `CPU8_INTEGRATION_PASS` while its terminal tool evidence is absent from the archive, making the claimed restoration dependent on external files. Confine each reference to a canonical member of the sealed evidence tree before reading it.

[P2] [P2] Reconstruct outer Job and handle closure from raw events
benchmarks/b570_cpu8_continuation_v5/runtime/source/verify_cpu8.py:38
chunk 2/2:

CPU8 verification accepts `outer_job_empty` and `owned_handles_closed` from the receipt, but `watchdog_check` only reconciles supervisor creation/exit and the embedded receipt. Neither it nor `cpu8_monitor.check` requires the emitted `OUTER_JOB_EMPTY` or handle-closure events. Removing those records and resequencing the journal therefore leaves successful verification possible despite missing raw cleanup evidence. Require the empty-Job observation and unique supervisor-thread, supervisor-process, and outer-Job closures in lifecycle order, and reconcile them with the receipt.

overall: patch is incorrect (0.72)
Review passes returned. chunk 1/2: 0 finding(s), chunk 2/2: 2 finding(s). See preserved pass reports for provider conclusions.
chunk 1/2 overall: patch is correct (0.72)
No actionable P0–P2 defect is established by this chunk. Historical configurations, reviews and manifests are provenance, not current approval or PASS evidence. This assessment covers the supplied handoff and legacy runtime source; the current continuation-policy, freeze and CPU8 verification implementations are not present in this chunk. No project code was executed, and native Windows behavior remains unverified.
chunk 2/2 overall: patch is incorrect (0.94)
The supplied chunk contains two actionable gaps in sealed evidence membership and raw cleanup reconstruction that can permit unsupported PASS results. Assessment was static; no project code or native Windows code was executed. Omitted context and historical artifacts were not treated as current authorization or execution proof.
