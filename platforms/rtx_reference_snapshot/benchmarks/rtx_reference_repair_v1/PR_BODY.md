## Goal: repair the mechanism, not redefine success

Successor to PR156 at `47c93985010d0f3c0c55f975f4cd7761e64bcae2`.
This PR contains executable source adapters, diagnostic/repair primitives, host
orchestration, tests and a bounded development/confirmation protocol. It does not
modify old evidence, merge other PRs, submit the paper or claim a working GPU fix.

### Implemented
- Real UB1/unscoped reference producer; complete sequence-state/positions/initial-logit
  handoff into the candidate, with R→R sham and reversed producer controls.
- Scheduler-assigned backends instead of the superseded buffer-owner inference.
- Bounded same-prefix tensor traces, observation controls, stride-aware comparison;
  diagnostics cannot enter qualification or timing.
- Opt-in Q8 row-wise native matmul graph primitive selected by operator class,
  initially disabled. Immutable per-build selection, not task/token-dependent tuning.
- Independent original-binary reference generation for held-out tests, sealed policy,
  complete endpoint/logit/transaction/state checks, dual-PQ cost analysis and evidence packer.
- Fresh Windows Job-managed attempts, shared budget and lock, real exit accounting;
  development may repair and continue without erasing any failure.

### Matrix and freedom
96-request first development matrix; up to480 development/diagnostic/regression/recovery
requests. Only after mechanism review/freeze:24 original-R references +120 qualification
+288 measured +288 warmups. Maximum1200 new requests. Old40 remain separate. No fixed
calendar deadline. Held-out failure cannot be repaired on that same panel and relabelled
blind validation. Original model/reference/precision and the full cost window stay fixed.

The platform agent may fix engineering issues and develop a better structural repair,
including a source-reviewed candidate numerical-kernel successor, with preserved diffs,
new identities, tests and unchanged original R. It need not seek permission for every
build or adapter fix. See ENGINEERING_POLICY.md and Chinese HOST_PROMPT.md.

### Validation scope
Authoring environment runs CPU regression/fault-injection tests and compiles/executes
an API-mock C++ graph/stride test. Exact original worker/adapter blob identities and
unchanged acceptance-loop source are checked. No full Windows native compilation,
real Q8 numerical correspondence, CUDA inference or repair success is claimed.
Read VALIDATION.json for actual counts and tests. Neither generic source equivalence
nor finite endpoint agreement is presented as an all-input guarantee.

Entry: `benchmarks/rtx_reference_repair_v1/README.md`.
New result PRs should retain every version/failure and supply a mechanism-based final
judgment plus raw-access/download verification. Keep this development PR Draft until
host implementation and results have been reviewed.
