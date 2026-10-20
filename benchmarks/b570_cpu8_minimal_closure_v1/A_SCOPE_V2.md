# A2 prospective source-only closeout: execution split and migration

**Status: CODE CANDIDATE / SOURCE_BLOCKED.** Parent: PR126 `b4cd53d3`, original PR125 evidence `c86ed78a`. No native execution, no scoped-clean, no F0, no CPU8 case.

## Decisions implemented as candidate code

- `finalize_review_v6.py` is rewritten as **source-only evidence consistency**. No `win`, `audit_identity_stream`, `processes/full-review`, compiler or historical writes. It requires actual complete P0/P1/P2 coverage for an exact manifest, source bytes, commit, reviewer identity and transcript SHA. It outputs `SOURCE_REVIEW_EVIDENCE_CONSISTENT`, **not SOURCE_REVIEW_PASS**. The actual independent reviewer/service attribution must be verified externally.
- `integration_gates.py` no longer includes the reviewer's Windows process in native gates; it still requires current B/C-native observer smokes, churn, breakpoint, native prerequisite and D0 reconstruction. The C gate requires an A source approval record pinned to the actual report; its external authenticity is a separate required admission action.
- `native_gate_audit.py` consumes existing `NATIVE_GATE_PATHS.json`. `operation_roles_v7.py` maps B/C operation IDs only and rejects historical IDs and mismatched UUID/stage/digest. No competing native gate-path map is created.
- `operation_pricing_v7.py`, `operation_guard.py` and `budget_v6.py` use explicit bounded **cumulative owned starts + wrapper starts + separately reserved provider process-seconds**; no magic `cap+2`. The price formula is conservative; **it does not by itself prove hard process containment or unknown service overhead**. Job readback and actual cumulative starts remain mandatory. Missing/unauthenticated external proof blocks B.
- `tool_binding.py` consumes a future exact C execution envelope and role instead of hard-coded 1120/1125/cap10. `engineering_gates_v6.py` binds a current C native compiled identity, not old 036/026/025/compile IDs. These B/C dependencies are not yet executed and must be reviewed together in A.
- `b_negative_binding_v7.py` is a separate B02/B03/B04 fixed-negative evidence checker, so success-path `delivery_binding_v6.invocation` still **requires exit 0/CLOSED**. No generic allow-failure switch. Expected failure detector, provider exit, real native events and outside-owner exit/cleanup must match the frozen B contract. Event names and provider outcomes are prospective interface requirements, not observed results.

## Legacy operation migration (no old PASS transfer)

| Previous source dependency | Prospective role | New authority |
|---|---|---|
| 037-final-review; processes/full-review | A01-independent-source-review | External P0–P2 provider/human review with recorded real request/response, no Windows PID requirement |
| 036-final-regressions; 026-budget-negatives; 025-bridge-negatives | A00-source-checks | Fresh fixed tests and real results, never old 91/11/7 counts |
| 021-build-launcher-windows-path; compile-v6-2 | C-compiled-identity / B build-load evidence | Actual native build/load identity; archived DLL remains historical until qualified |
| 038-final-startup | B00-entry-imports | Must **not** alias historical 038-job-cap-diagnostic |
| probe-download-01; 030-isolated-probe-recompute | C delivery download / C isolated recompute | Actual session/tool/blob and output byte bindings |
| healthy-r0-a2; freeze-r1; stall-r2-a2; stall_harness_r2_a2 | native_gate_paths healthy/freeze/stall/stall_harness | `NATIVE_GATE_PATHS.json` with fresh task UUID |
| review-smoke-*; review-churn*; review-breakpoint | native observer/smoke/churn/breakpoint roles | Actual B/C native artifacts, no reviewer OS identity |
| 1120/1125; cap10; (cap+2) | C execution plan & per-op prospective_envelope | Independent pre-start proof, no guessed service costs |

A approval must also pass the new `source_review_origin_v7.py` binding against the independent provider request, response, actual capture index and reviewer identity outside candidate-owned root. A candidate-authored approval or matching hashes alone **cannot** prove an independent reviewer. The platform must authenticate the provider identity separately; no new native reviewer PID requirement is introduced.

## A review request and cost ledger

One complete independent source-only review of the **new fully composed code and configs**, not just patch. Candidate preparation is tracked separately. No B570 native/GPU/model/actor/RTL process is authorized in A.

Prospective review-request controls: ≤1 review request, ≤60min wait, ≤160 read-only file retrievals, ≤1MiB final report. These are *API/operational* bounds, not hidden service worker OS limits; actual usage and unknown provider cost are recorded as separate fields. A clean requires every manifest entry, real provider provenance, complete findings and no unresolved P0–P2. Missing evidence => SOURCE_BLOCKED, not auto clean. Do not invoke full review automatically from a candidate file or spawn Codex/CUA/REPL inside the Windows Job.

The current working source-only overlays are NOT A approval. The previous 119-file list is a historical base and must be regenerated with **all** added helpers, native role policy and config templates in a new full composition before external review. A's scope is *source qualification*, not B hard-cap qualification.

## B and C hard stops

- B is four native rows B01–B04 **only after separately authorized A pass** and actual pre-start owned-tree + provider bound. Proposed P=7, total 1200 process-seconds/32 starts, 240s native wall, 300s separate remote wait and 528MiB storage are **conditional targets**, not proven values. In particular U≤360 is UNKNOWN.
- C first slot remains 0/8 and NOT AUTHORIZED until B ENTRY_ADMITTED and independently priced eight-case+delivery budget. Its A evidence is externally authenticated and exact-byte frozen, but no reviewer OS PID is required inside C.
- Archived old UUIDs, raw failures, missing provider stable IDs, spent budgets and 117.236s delivery-tail deviation remain unchanged.

## Minimal next handoff

Review this A2 delta and exact source composition; resolve broken imports/schema/approval flow through source-only checks; then request a single independent P0–P2 review against a frozen source commit. Do **not** start B native entry or C. Report only: current PR head, source digest, scope completeness, unresolved P0–P2, provider provenance and explicit A status.

## Additive recovery fixes — independent source candidate, not native admission

A subsequent source-only recovery identified and repaired an actual indentation/syntax defect in `operation_guard.py` and a settlement path that reduced a previously higher conservative charge. The guard now requires that its own task/phase operation already be reserved as **unsettled** in `snapshot` before creating a Job. As before, a reserved JSON ceiling does **not** prove the provider's hard outer process boundary; B still requires independent pre-start admission and an authenticated whole-operation resource envelope.

The three fixed B negatives have distinct event authorities: B02 records the native `CreateProcess` refusal (Windows error 1816) in `operations/<op>/FIXTURE_NATIVE_EVENTS.jsonl` from a frozen, reviewed B fixture, and an external owner cross-checks its SHA256 and writer identity; B03 records `OPERATION_DEADLINE` and `OPERATION_FAILURE` from the guard's monotonic check with an independent termination witness; B04's `OWNER_ABORT_CLEANUP` is **only** emitted by the surviving external native owner after abnormal guard-owner exit. No candidate-owned aborted process can certify its own cleanup. The outside witness contains `frozen_contract_sha256`, complete Job starts and exits, and post-run external byte identities. Its SHA256 cannot appear in the **pre-execution frozen** B contract; the post-run result binds those bytes instead.

This is an **interface contract**, not an assertion that the B02 fixture/witness writer or provider OS boundary is currently deployed or native-qualified. B02's dedicated native-error writer and B04's independent surviving outside-owner capture remain explicit platform implementation/verification prerequisites. Source-only tests and byte inventories must be rerun on the exact new composition before a separate P0–P2 independent review. Any test not actually run remains NOT_RUN.

## e9667 source-only A3 local closure (prospective, no native qualification)

Three scoped implementation repairs were made after the immutable `e9667eb7` starting point, without changing A2's old-operation mapping or any historical PASS/UUID/ledger:

1. **Deadline provenance:** `operation_guard.py` now derives B03's fixed `OPERATION_DEADLINE` detector from monotonic time or an actual rescue signal; a forged exception text alone cannot create timeout evidence. `b_negative_binding_v7.py` requires the detector's monotonic cutoff/observation and rescue flag.
2. **Fast-child census:** every Job cumulative process start must match a unique captured native identity (root plus retained descendants). A missed short-lived descendant yields `OPERATION_MEMBER_CENSUS_GAP`, preventing a qualified `CLOSED` verdict. This is fail-closed detection, **not** a claim that 100ms polling captures every child; B may still need a reviewed non-sampling creation feed.
3. **Budget-input integrity:** `budget_v6.snapshot` rejects a foreign UUID, wrong native phase, wrong operation filename, malformed/underpriced unsettled operation and missing explicit provider reserve before prospective admission. C's separate `delivery` reservation can read C operations without transferring an A/B ledger.

Targeted regressions cover both accepted controls and adverse inputs using isolated pure-function extraction and synthetic no-child budget operations. These are CPU-only source checks, not B native gate results. The previously required A2 full source review must cover every currently pinned source/import and auxiliary byte; **no independent scoped-clean is implied by hash consistency or by these tests**.

**Review sequence:** materialize the exact newly re-pinned full composition, run AST and source-only negative tests, then request exactly one externally attributable P0-P2 review of the complete frozen candidate (not only this delta). Preserve separate, UNKNOWN reviewer-service process/cost accounting. Remain `SOURCE_BLOCKED` until that independent review is clean, complete and authentic; B/C retain their native resource and execution stops.

## Three P1 source repairs after dfc6a8 (candidate only; no Windows qualification)

1. `operation_guard.py` retains the suspended root handle and tracks successful Job assignment separately. An unassigned, still-alive root is explicitly terminated via `TerminateProcess` and then waited on with real exit/FILETIME evidence; terminating the empty Job alone is not sufficient. The four combinations (unassigned/assigned × live/already exited) have pure-function source negatives. A failed direct termination must remain a failed cleanup, not a PASS; B must still prove the actual Windows call and exit.
2. `b_negative_binding_v7.py` now applies the existing `delivery_binding_v6.request_check` to the **exact frozen guard request** and its actual native command, then checks child argv, command, parent PID and creation time. The outside witness must identify the same real guard PID+creation, child PID+creation, operation hash, guard command hash and actual provider terminal hash, with a distinct external owner. Source-only positives and malicious argv/parent/witness/terminal substitutions do not replace real native evidence or independently authenticate the service.
3. **Non-circular F0:** A2's existing `OPERATION_ROLE_MAP.json` pins an immutable `tools/<op>.operation.template.json` with only the `--freeze-sha256 __F0_SHA256__` placeholder. This role map, the template and all frozen source/config bytes enter F0. The actual `tools/<op>.operation.json` does **not** exist at F0 and is never in F0's file inventory. After F0, the reviewed `operation_roles_v7.py --root <ROOT>` entry generates the runtime operation exactly once, substituting only the actual F0 SHA256. `operation_roles_v7.operation()`, the guard and tool binder reject any additional runtime drift; `budget_v6.snapshot()` accounts for the pre-F0 template until the runtime file replaces it, never both. F0/self-hash, template drift, modified actual argv, mutated F0 and double-billing negative tests are source-only. The static `OPERATION_ROLE_MAP_C.template.json` uses `template_sha256` and `post_freeze_template=true` rather than a runtime `sha256`.

This is a forward-looking interface repair, **not F0 creation**. The immutable A review still requires the entire new source/config/test composition, full AST/source tests, real external reviewer provenance and no P0-P2 unresolved. No old PASS, UUID, budget, hardware qualification or B/C authorization transfers.

### Current A review input scope after three P1 fixes

The current immutable `SOURCE_COMPOSITION.json` contains **123 source/import files and 14 auxiliary inputs** (including `NATIVE_ENTRY_PLAN.md` and `CPU8_ACCEPTANCE_PLAN.md`). Earlier 12-input statements are previous candidate snapshots and must never be used for final scoped-clean. The C execution protocol uses a single frozen pre-F0 template, not a circular runtime hash. B00 failed-Job-assignment cleanup requires a separately priced native negative, not a source-only PASS.

## 2026-10-20 independent review six-finding source remediation (candidate, not independently clean)

The external independent review of pinned `8dddac29` reported **COMPLETE_NOT_CLEAN, 2 P1 + 4 P2** over all 123 source/import and 14 auxiliary files. These were real independent findings and are not superseded by passing 59+29 CI. This additive **six-issue** patch must itself be fully re-reviewed; it does not inherit SOURCE_REVIEW_PASS.

- **P1 / guard failed journal:** cleanup events are best-effort only; a persistent disk/journal exception cannot preempt direct termination of an unassigned suspended root, retained-handle wait or handle closure. A logging failure must mark the operation FAILED; independent native B00a/B00b cleanup evidence remains required.
- **P1 / seal versus postseal delivery:** `delivery_binding_v6.postseal_capture()` and `restore_postseal_invocation()` read provider returns, registered restore intent, native OS exits and full stdout **only from the registered external_root/postseal area**. Downloads and isolated restoration no longer need to append `tools/*` or `operations/*` under the sealed original root. `delivery_audit.py` calls the fixed postseal binder. These are source evidence rules, **not** a claim the platform has already implemented the outside owner or authenticated its provider.
- **P2 / sacrifice freeze:** native freeze negative fixtures copy the existing preflight/TOOLS.json before computing their sacrificial freeze inventory, so the initial baseline can pass and the intended mutation detector is reached.
- **P2 / PID reuse:** after opening each sampled PID handle, guard queries `IsProcessInJob(handle,job)` and refuses a foreign/reused PID before retaining its identity; completeness of cumulative Job starts is still mandatory.
- **P2 / outside owner:** reject nonpositive owner PID, invalid birth time, guard/child/Job-member PID and a witness claiming job membership, even if other field hashes are consistent.
- **P2 / frozen C clock:** new A2 C freezes bind task and delivery elapsed-frontier limits from `freeze['budget']`; historical v6 budgets retain historical constants for reconstruction only.

All six changes have new pure-source mocks/counterfactuals and explicit negative cases. A source-only GitHub Actions check may pass without proving Windows native behavior, external provider authenticity, disk hard quota, or complete independent review. Do not merge or launch any B or C process until authorized; old terminal UUIDs, UNKNOWN accounting and archived source bytes remain unchanged.
