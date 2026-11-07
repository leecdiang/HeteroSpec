# Audit of PR119 and closure hypothesis

Audit anchor: [aa7d64b5](https://github.com/leecdiang/HeteroSpec/tree/aa7d64b5e4c198699a2f1fcc52c8ff2e31103fa7). Implementation inspected: `benchmarks/b570_cpu8_continuation_v5/implementations/647fc68d-b3ad-43da-82e2-74037e7f2f35/`. This is a source/evidence review, not an independent native rerun.

## What is established

The recorded campaign is ENGINEERING_BLOCKED, formal CPU8 0/8, no F0. Native gates, limited D0 normal/journal bridges, and 53 regressions are engineering evidence; none is a substitute for the frozen eight-case campaign. Remote restoration of 5,438 data members and byte-identical recomputation supports artifact recoverability. It does not establish live acceptance. The 810 identified identities are closed; the full-task OS ledger remains UNKNOWN. No GPU, workload-model, or scientific execution occurred.

## Current source findings

| Finding | Actual inspected path/function | Consequence | Required intervention |
|---|---|---|---|
| Relocation can skip current resource admission | `source/verify_cpu8.py`, `campaign_snapshot`: current process/storage checks occur only when `not relocated`; CLI admits `--relocated` | Historical reconstruction and live qualification are not sufficiently separated | Two verifier roles with disjoint terminal states; live always checks current resources at original identity; reconstruction can never emit CPU8_INTEGRATION_PASS |
| Delivery receipts overstate execution provenance | `source/delivery_audit.py`: checks hashes, declared command, exit code and isolated-import fields, downloaded chunks and recomputed bytes | Correct bytes and declared metadata do not by themselves prove the named tool returned those bytes or executed that restore | Bind actual provider request/response exports and terminal execution chain to frozen intent, downloaded objects and output bytes |
| Review consumes execution headroom | `source/campaign_budget.py` enforces cumulative limits but does not reserve future formal/delivery lifetime | Another useful repair can still end at formal 0/8 | Prospective stage admission with protected formal and delivery allowances, using the same cumulative clock/ledger |

Existing `source/tool_binding.py` already binds watchdog launch intent, actual request/session chain and terminal output. Extend that pattern for delivery instead of replacing supervision. Existing `source/freeze_cpu8.py` already requires scoped clean review, native gates and source hashes. Preserve those requirements and bind all new modules/entry points. Do not introduce a new boolean-only bypass.

The earlier `review/FINAL_REVIEW.json` describes four findings at an earlier snapshot. Later code addresses significant portions of accounting, archive admission and link handling; this audit does not assert all four remain unresolved. The final interrupted review is not a clean verdict.

## Research interpretation

This campaign tests whether an evidence-producing supervisor can close its CPU integration contract. It measures neither B570 kernel cost nor a hardware acceleration opportunity. Its useful outcome is a trustworthy prerequisite and a bounded failure classification. RTX's closed mapping experiments remain the software baseline; B570 cannot yet supply a cross-platform performance comparison. The next GPU experiment must be separately designed after CPU8 closure, with numeric reference qualification, a strong baseline and an explicit cost boundary.
