autoreview findings: 2
[P2] P2: Include nested-debugger children in resource accounting
benchmarks/b570_entry_repair_v3/source/observe.py:46
Resource decisions use only `live`, which is populated from this observer's debug events. Windows stops propagating descendant debug events when a descendant creates a process with `DEBUG_PROCESS` ([Microsoft documentation](https://learn.microsoft.com/en-us/windows/win32/debug/process-functions-for-debugging)). The supplied supervisors do exactly that when launching actors. Those actors remain in the observer's Job but disappear from its process-count and RSS calculations, allowing an over-budget command tree to pass these checks. Build the resource census from Job membership, retaining debug events for the processes this observer actually debugs.

[P2] P2: Check operational import dependencies before reporting readiness
benchmarks/b570_entry_repair_v3/source/entry_bootstrap.py:26
`--startup-check` exits inside `bootstrap`, before the entry executes its remaining imports. Consequently, a deployment with a missing or broken `observer_policy` or `source_guard` can receive `STARTUP_PREFLIGHT_PASS`, then immediately fail its operational observer/watchdog launch. Authenticating an inventory does not detect this when the manifest was generated from that incomplete deployment. The fixture tests currently demonstrate this gap by successfully probing entries without those dependencies. Move readiness reporting after each entry's required imports, while keeping argument parsing and operational side effects after the check.

overall: patch is incorrect (0.92)
The supplied change has two actionable gaps: nested debugger children evade observer resource accounting, and startup preflight can report readiness before required operational imports execute. Review completed from the supplied patch and Windows API documentation without executing project code. Native Windows behavior was not tested, and the omitted legacy CPU8 adapter is not certified.
