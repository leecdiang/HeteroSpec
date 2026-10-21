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
