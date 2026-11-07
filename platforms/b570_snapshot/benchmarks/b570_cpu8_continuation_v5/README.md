# PR119 CPU8 continuation v5

This additive delivery repairs the two final B570 review findings and changes the
engineering workflow from count-limited attempts to repair-until-verified within
one six-hour task budget. The user explicitly authorized autonomous repairs and
continuation. All historical source/results remain unchanged; historical_context
is read-only provenance, never fresh task registration or PASS evidence.

runtime is the complete source snapshot from fb20a198, including the legacy CPU8
adapter, with the new fixes. It is not just the earlier observer overlay.

Evidence audit now requires exact coverage of the sealed task tree, rejecting
omissions, extras, aliases and duplicate paths; only the manifest itself is outside
its own inventory. The completion receipt and post-seal export/recovery records
must stay outside that sealed root and bind its manifest. Watchdog receipt bytes
must agree with the original WATCHDOG_END receipt and actual supervisor identity,
OS times, return code and monotonic lifecycle bounds.

CONTINUATION_POLICY.json explicitly enables v5 in a fresh root. Roots without it
retain their historical rules. V5 removes arbitrary review-ID/revision/attempt
counts while keeping unique prospective registrations, raw failure accounting,
per-command deadlines and resource ceilings. D0 may use up to five hours from the
first preparation; the task remains six hours including recovery/delivery. The
last hour is reserved for formal validation and closure; the watchdog still
reserves thirty minutes of the total for delivery. No new work starts after its
remaining budget is insufficient. The clock is never reset by revision or root.

No GPU/model/science/paper changes. No repeated three-hour soak. Formal CPU8
control points, raw evidence, one-second inner coverage and truthful outcomes are
unchanged. A failed formal batch may be sealed and followed by development repairs
and a new frozen batch, never overwritten or combined into a retrospective PASS.
See B570_PROMPT.md for the complete execution handoff.
