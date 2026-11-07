# PR119 PID identity repair v4

Scope: CPU observer identity bookkeeping only. Historical PR115/117, all PR119
results including the three-hour run and 4cb0e0f are immutable. No GPU, model,
scientific execution or paper changes. This is an additive source overlay.

The previous observer used PID as the permanent identity and rejected any later
CREATE for that PID, including after OS exit. That is a demonstrated code defect.
The 4cb0e0f triggering creation identity was not recorded; PID reuse is a supported
risk, not a uniquely established explanation for that historical event.

Registry now retains history and handles by (PID, OS creation FILETIME), with a
PID index only for active processes. Normal and failure paths use the same code.
A received-create record precedes identity reads; a complete raw identity record
precedes admission checks. Active collisions, exact identity replay and unmatched
exits remain failures. Rejected retained handles are disposed without certifying
coverage. Root recognition uses full identity. Closed identities require actual
OS times, exit code and handle release. Failure disposal does not manufacture exit.

Acceptance: portable deterministic normal/cleanup PID reuse, active collision,
replay, missing exit, wrong identity/code, root PID reuse and 600-identity churn;
actual Windows startup preflight and bounded 200-child process churn; then a
completed independent full-candidate review under the observer plus independent
identity-stream reconstruction. Native reuse is reported only if observed.
The source review here does not certify Windows or the deployed legacy adapter.
Original CPU8 gates and unchanged scientific boundary still apply.

Use B570_PROMPT.md end to end. The current full source and src/rev2 overlay includes
prior entry/budget fixes. Old evidence remains evidence, never a reused PASS.

Additional review correction: only one initial first-chance loader breakpoint per
process identity is continued. Later breakpoint/single-step/application exceptions
are passed to application handling in all three debugger loops. The native handoff
includes a post-loader DebugBreak negative fixture; normal review still requires
zero exit. The exception policy is included in startup and freeze bindings.
