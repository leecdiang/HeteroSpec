# PR119 PID repair delivery

Status: SOURCE_REPAIR_REVIEW_PASS, scoped to this additive overlay and protocol.
No B570 execution or Windows acceptance occurred in this delivery.

- 92 portable regressions passed: 56 source tests and 36 runtime tests.
- The actual short-lived subprocess fixture completed 200 workers on macOS;
  this verifies the fixture only, not Windows debug observation.
- Historical 4cb0e0f archive: 782 members, all 781 manifest-bound files verified
  for byte length and SHA256. Historical reports and missing evidence unchanged.
- Independent P0–P2 full-overlay review first found one P1 (ctypes handles are
  unhashable) and one P2 (receipt/root OS exit contradiction). Both were fixed,
  with actual ctypes-type and contradictory-exit regressions. A second full review
  found swallowed application breakpoint exceptions (P2); all three debugger
  loops now use a shared one-loader-breakpoint policy, with policy regressions
  and a native negative fixture in the handoff. The final full
  review returned scoped-clean. All three original reports are retained.
- History and retained handles now use PID plus creation FILETIME; live PID
  lookup is separate. Both normal observation and failure cleanup use Registry.
  Raw creation identity is saved before admission. Missing identity remains a
  coverage failure, even when the Job is physically empty.
- New independent identity reconstruction checks root actual exit, each paired
  exit and retained handle close, lifetimes, raw creation coverage and receipt
  totals. It does not certify review contents or outer process lifecycles.

B570 next: new root, bound source, real startup preflight, existing native gates,
200-child churn, application-breakpoint rejection, completed full deployed-candidate independent review, identity
reconstruction, then original CPU8 only if all prerequisites pass. Native PID
reuse is optional observation and must never be inferred from churn alone.
See B570_PROMPT.md for the full handoff, unchanged limits and delivery steps.

The historical failure's exact triggering creation was not captured, so this
repair does not retroactively prove its unique cause. No ENGINEERING_READY,
complete-task accounting, GPU/model/scientific result or paper claim is made.
