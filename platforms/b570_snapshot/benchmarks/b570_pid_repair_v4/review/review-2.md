autoreview findings: 1
[P2] [P2] Distinguish loader breakpoints from application exceptions
benchmarks/b570_pid_repair_v4/source/observe.py:71
Every breakpoint and single-step exception is silently continued with DBG_CONTINUE. This also consumes application-generated exceptions after startup: a command that calls DebugBreak() and then returns zero can receive a successful CLOSED receipt and IDENTITY_STREAM_PASS, even though its breakpoint would otherwise reach its exception handler or terminate it. Microsoft documents that reporting an exception as handled bypasses the application's handler search ([exception handling](https://learn.microsoft.com/en-us/windows/win32/debug/debugger-exception-handling)). Track the expected initial loader breakpoint per process identity and pass subsequent application exceptions through with DBG_EXCEPTION_NOT_HANDLED, preserving their evidence. Apply the same correction to the duplicated exception branches in both supervisors.

overall: patch is incorrect (0.9)
Completed the supplied overlay and protocol review. The handle-key and root-exit reconciliation fixes are present, but exception handling can suppress application faults and produce misleading success evidence. No project code was executed. Native Windows behavior and the unavailable deployed legacy layers remain subject to the separate B570 validation and review.
