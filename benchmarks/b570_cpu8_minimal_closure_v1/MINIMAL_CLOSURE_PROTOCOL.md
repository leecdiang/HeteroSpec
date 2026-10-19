# B570 CPU8 minimal closure: prospective split protocol (DESIGN ONLY)

Status: DRAFT / NOT EXECUTED. Parent evidence: PR119 `aa7d64b5e4c198699a2f1fcc52c8ff2e31103fa7`; PR125 `c86ed78a8c6b8093205c34c1ab66b7f1bfcdc0ae`. Historical UUIDs `647fc68d-b3ad-43da-82e2-74037e7f2f35` and `48d45054-1838-4d55-9f3a-e15476dc4423` remain closed/blocked. This document neither reclassifies prior failures nor transfers their budget. No GPU, workload model, actor, graph, RTL, or formal CPU8 task is authorized by this proposal.

## Decision and boundaries

The scientific target is reference semantics -> qualified mapping -> strong software baseline -> full cost boundary -> residual hardware opportunity. CPU8 is an **engineering integration prerequisite**, not B570 numeric qualification or cross-platform performance evidence.

Retain: exact-source and compiled-binary identity, frozen real entrypoint, native checks, fault detectors, eight actual cases, trusted response/exit evidence, operation containment and cleanup, prospective resource budget, byte-accurate archive/restore/recompute, negative controls, and explicit UNKNOWN fields. Move general-purpose reviewer/CUA/REPL lifecycle proof outside the *formal-case* critical path; do not pretend an unsupervised external service is bounded or authenticated. A software monitor's over-cap rejection is not evidence of a hard pre-start cap.

There are **three separately authorized tasks**, not three stages that can silently share an origin. Each task has its own immutable start, ledger, budget, closed status and handoff manifest. The old origins, failures and balances remain unchanged.

### A — source repair and final independent review, no formal CPU8

Input: pinned PR125 head, source and binary manifests from the closed v6 evidence; inspect `implementation/operation_guard.py`, `budget_v6.py`, inherited `observe.py`, `process_registry.py`, `job_census.py`, live `verify_cpu8.py`, `delivery_audit.py`, `tool_binding.py`, and actual 037/039 launch argv and raw logs. Archived `implementation/` snapshots are **not** yet established as a reviewed deployable module.

Fix only (1) verifier role separation: live original canonical root always performs fresh native/process/storage checks, while relocate/restore is RECONSTRUCTION_ONLY; (2) delivery tool binding: frozen intent to real request, provider response, session termination and output bytes, with missing provider IDs labeled UNKNOWN; (3) a proven execution boundary and budget admission for the **chosen** launch, including unobserved wrappers conservatively charged or excluded by eliminating them. Review source, helper imports and exact deployed entrypoint at immutable hashes; do not accept an eight-test portable prototype as Windows native certification. Execute impact-directed development tests and one complete independent review once, with an explicit stop if not clean. Compiler outputs have separate reproducible manifest and hashes; static review alone never certifies native execution.

A's exit: `SOURCE_REVIEW_PASS` with review transcript, corrected source, source/import/binary manifest, exact runner CLI, enumerated required native gates and gate mapping; or `SOURCE_BLOCKED`. No formal slots or F0.

### B — narrow native entry admission, no formal CPU8

Consume A's exact reviewed bytes. Prefer direct isolated interpreter/launcher over Codex -> CUA -> node_repl debug stack **only if** the simplified entry preserves: real request/session/terminal capture, PID+creation identities for owned process tree, native Job membership and limits, exit identity/close evidence, detector triggers, trusted output digests, cleanup and no prohibited imports. Disabling `--ignore-user-config`, CUA, REPL or correcting argv quoting is a hypothesis, not proof. Never remove DEBUG_PROCESS without equivalent documented native provenance.

Freeze the actual startup/exit process tree, including conhost, shell and helpers when present; establish a **pre-admission enforceable** process-lifetime/peak-resource envelope on the new entry. Test normal, expected-cap-rejection, timeout and forced cleanup. Do not rely solely on `ActiveProcesses` or a four-member parent Job flag. Reject if observed descendants exceed predicted bound or are outside the controlled boundary. External provider/service workers must either be eliminated, covered by an independently enforceable bound, or disclosed UNKNOWN and conservatively reserved: if their unknown cost could invalidate the mandatory cap, B fails. Check that no process survives. The Windows root/OS mechanism of the v6 4->6 anomaly need not be universally explained, but the **selected** entry must be qualified without that anomaly.

B's exit: `ENTRY_ADMITTED` plus exact machine/OS/native runner identity, test transcripts, limits/readback, peak census, child identities and exits, real tool/terminal records, observed overheads and defensible conservative bounds; else `ENTRY_BLOCKED`. Neither exit counts toward formal eight.

### C — independent native CPU8 integration and delivery

**Only after A and B pass**, propose and approve a new UUID/task with new origin and **separately frozen forward-looking** resource limits. Consume A/B immutable manifests. C contains only deployment/hash/native prerequisite checks; final freeze; formal eight in original order exactly once; then real remote delivery with isolated byte recomputation and terminal receipt binding. C has no development/reviewer/agent subprocess construction in its critical path. Any source change invalidates the freeze and requires new A/B reviews and a new C campaign; do not resume a failed frozen slot.

Formal order and detectors (preserve old protocol exactly):
1. `normal_single` -> `NORMAL_COMPLETE`
2. `normal_transition` (8 pairs, 16 unique slots) -> `TRANSITIONS_COMPLETE`
3. `terminal_pending_completion` / `SEALED_WRITE_DURING_CLOSE` -> `SEALED_WRITE_REJECTED`
4. `frozen_input` / `WRITE_FROZEN_INPUT` -> `SEALED_WRITE_REJECTED`
5. `late_closed_slot_write` / `WRITE_CLOSED_SLOT_A` -> `SEALED_WRITE_REJECTED`
6. `resource_read_failure` / `FAIL_RESOURCE_READ` -> `RESOURCE_READ_REJECTED`
7. `directory_read_timeout` / `STALL_DIRECTORY_READ` -> `COVERAGE_GAP_REJECTED`
8. `journal_write_failure` / `FAIL_JOURNAL_WRITE` -> `JOURNAL_FAILURE_REJECTED`

Require both correct fault classification and trustworthy native cleanup. A deliberate fault counts PASS only if the frozen detector catches **the intended fault** with authentic raw evidence. Failure/timeout => stop and retain raw data; no scientific retry. At 8/8 with incomplete delivery use `CPU8_CASES_PASS_DELIVERY_PENDING`; only full live/freeze/native/case/delivery checks allow `CPU8_INTEGRATION_PASS`. Reconstruction can *never* issue that verdict.

## Budget derivation and decision gate

The historical `13,600 process-seconds + 1,800 wall-seconds` formal reserve is an **old task allocation**, not a measured per-case upper bound. Historical review 3030 process-seconds is likewise invalid as a new review quote because the assumed four-process envelope was falsified. Do NOT mechanically copy or silently shrink either.

For each independently authorized task calculate a declared ledger:
`E_i = ceil(P_i * (T_i + L_i) + U_i)` process-seconds, where `P_i` is the **enforceable** maximum concurrent charged process count across the chosen operation and its owned descendants, `T_i` wall-time cutoff, `L_i` bounded termination/cleanup grace, and `U_i` conservatively billed process-seconds for services outside that process boundary. This simplified ceiling is valid only if the operating envelope actually enforces P_i throughout; otherwise use per-subtree bounds and sum them, or STOP. Record caps and upper bounds separately for wall, starts, bytes/links/storage, capture/export, and delivery acknowledgments. No UNKNOWN cost is zero. Pre-admit the next whole operation and cleanup using unused **same-task** budget; monitor during run. Distinguish actual bounded job data from uncovered whole-machine OS costs.

A budget = one bounded development+review pass with bounded possible repair loop; quote from the real simplified review entry rather than the old 3030 estimate. B budget = fixed startup matrix, negative rejection, timeout, cleanup, captured provider intervals. Neither has permission to consume C's budget. C budget derived from **eight case-specific** `E_i` plus native admission, frozen deployment and independently priced delivery, one-time capture, and a safety margin justified by measured A/B calibration. Supply an eight-row table with P_i,T_i,L_i,U_i,starts,storage and evidence-volume forecasts before authorizing C; no proposal to spend the former 13,600 without that table. A target may be lower than 13,600 only if the newly proven bounds justify it. Before cases begin ensure the entire sequence + restore + final upload+cleanup fits. If not, STOP prior to formal first slot.

Legacy all-campaign rules such as 21,600 cumulative wall/process-seconds and 3,000 starts apply **within old tasks unchanged**. New task caps must be prospectively approved, recorded and at least as strict as all mandatory inherited physical limits applicable to their respective execution scope. Different-task ledgers cannot be added as if they formed one continuous native acceptance; separately report A/B/C costs and provenance.

## Honest evidence and stopping conditions

Old v6 facts: 0/8, no freeze, insufficient full review; old archives were genuinely restored and byte-recomputed; stable provider call IDs not exposed; original failed upload responses 21-25 and download responses 0-1 missing; whole-task service-host OS coverage UNKNOWN. No backfill, no proof of external certification. Preserve all PR115/117/119/125 raw evidence verbatim. Use immutable refs and additive artifacts only.

Stop A if complete review cannot be finished within a genuine hard bound. Stop B if startup has unbounded/untracked descendants, inconsistent census, cap mismatch, or missing native exits; never confuse post-hoc software rejection with kernel admission. Stop C if immutable manifest mismatches, live-resource gate can be bypassed, receipt provenance is unbound, case fails, cleanup incomplete, or worst-case remaining budget cannot cover all mandatory remaining work. Publish precise blocker and closed ledger, not a fabricated PASS.

## Post-CPU8 science gate: first B570 experiment (separate permission)

After C passes, design a **B570 reference-preserving mapping/dispatch crossover study**: ask whether B570's qualified QB vs compact/permuted QH_C cost boundary changes near 1023/1024/1025 visible keys and GQA q=1/2/4 when reference bytes, conversion, real replay and readback are accounted for. Freeze independent per-device numerical qualification and no input aliasing before cost. Include paired A/A QB controls, original and reverse execution order, independently restarted blocks, strong resident and full-input software baselines, OFF and **actual replay ON** as applicable, and explicit source, profiler/clock reliability checks. Do not pad 1023 to 1024 unless exact output-byte equivalence is freshly established on B570. Distinguish observed kernel-path evidence from causal bottleneck claims. Separate mechanistic profiling from clean timing and preserve local reversals.

Primary scientific question: after real replay and input conversion cost, is there any statistically resolvable, practically useful **qualified B570 region** where a different mapping outperforms QB, and does the RTX-discovered boundary generalize? Null results are informative and do not justify RTL. Only when physical bottleneck + cost dominance + system critical-path evidence survive should a small FPGA architecture probe be designed; not full model deployment.
