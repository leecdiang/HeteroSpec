# Request closure and complete service protocol

Status: CPU preparation. No new model request, native worker invocation or GPU
launch has been performed by these request tools. The constructed fixture is
not a model result and its token-list states are not native KV bytes.

The exact Windows parent is
`D:/rtx211-q8-20261109/frontend-v2/worker.cpp`, SHA-256
`0bf9920d135fab66d15c5c2d81d25fcbdb90d525b281ef20b8beea384f181096`.
Its request loop uses `int k=spec.k` for the entire request. Admitting both k3
and k7 jobs does not implement a per-cycle schedule. Its `Context::snapshot`
captures target state only. Draft proposal vectors do not substitute for draft
active-state bytes, and committed states do not substitute for untrimmed ones.

## One request must close the consumer chain

Use one frozen, real prompt and a frozen logical per-cycle schedule for both
the independent reference and each candidate. This first schedule qualifies a
path; it is not an adaptive policy or a claim that changing depth is profitable.
Do not alter proposals to make a result look natural, splice separate runs,
insert token 37, or compare only argmax or KV hashes.

| Transition | Required consumer and state |
| --- | --- |
| k3 all accepted | All four requested full vectors; L3 selects bonus b; accepted=3, keep=B+4; b is emitted and remains unmaterialized |
| Bonus continues | The next actual seed is b at the retained base; retain every requested vector, including all eight if this cycle uses k7 |
| Fifth proposal rejected | L4, produced after input p3, is read to judge p4 and select correction c; accepted=4; keep=B'+5 |
| Correction continues | c is the actual next seed. Compare target and draft untrimmed and trimmed active state, geometry, owned outputs, decisions and continuation |
| Request stops | Compare emitted IDs, EOG flags, CAP/EOG reason and whether the final emitted token is materialized; do not add a decode to make terminal KV match |

At every stage require exact source, executable, loaded numerical DLL, model,
vocabulary, producer, KV arithmetic and graph-policy identities. Capture full
requested F32 rows, not a selected consumer projection. Save target and draft
states before verification, after speculative work before trim, and after trim.
Extract active native K/V bytes and compare full state/geometry under an
independent reader. Record owner identity and generation, mask, dispatch and
placement checks separately from observer captures. Stop on first mismatch and
invalidate the whole reusable request owner, including draft/trim/sample errors.

The source-only adapter `prepare_native.py` adds an explicit `cycle_k` input,
checks that every listed depth is 3 or 7 and that reserve/capacity covers the
maximum, and refuses schedule exhaustion. It leaves a missing per-cycle
schedule equivalent to the historical fixed-k source. It does not integrate
the additional state captures, transaction-wide poison, native guards or
complete timing hooks. Historical host bindings do not authorize this new
source/input policy. Generated sources are deliberately marked unqualified.

## Existing natural ingredients remain separate

`cpu_result/OLD_TRACE_STRUCTURE.json` reads the eight completed #215 receipts
without a model or the historical verifier. In each k3 receipt, cycle 0 emits
bonus 1477 and the next cycle uses seed 1477. In each k7 receipt, cycle 14
rejects the fifth proposal: L4 selects 39143 against proposal 914, keeping
frontier 212. These are already-exposed, separate fixed-k requests. They do not
cover the combined dynamic chain and are not new numerical qualification.

`state_machine.py` separately constructs the full chain. It uses all requested
full vectors to produce the next actual bonus/correction seed. Its counterexample
test changes L4 without changing argmax or token-list state and requires a
full-vector failure. CAP, EOG on an accepted token, EOG on a correction and EOG
on a bonus are distinct fixtures. This checks the state-machine tools, not a
CUDA implementation. The native combined-chain status stays `NOT_RUN`.

## Strong controls and fair common improvements

| Role | Required comparison |
| --- | --- |
| A | Same-contract backend-loop4, same logical policy and inputs |
| B | Current packed, with the same logical policy and full request endpoint |
| C | Two groups of four in one CTA only in its qualified Q8_0/F32 q8/g2 subdomain; exact fallback elsewhere |
| Fixed control S | Strongest eligible fixed policy selected on the finite development set before any held-out timing; no winner is selected in this CPU preparation |
| Application background | A runnable target-only/runtime control with its own complete endpoint; any different numerical semantics are explicitly outside the exact-contract comparison |

Lazy last-draft materialization, cap-tail repairs and buffer reuse must be
given to every applicable arm and independently qualified. Pin the common
implementation by hash. An arm must not retain avoidable tail work merely to
inflate a new-mechanism contrast. If a common change alters requested outputs
or a reference API, qualify that reference separately. The prepared dynamic
adapter does not yet implement these common optimizations.

Do not rerun the old #213 eight-arm live panel or the completed #215 supplement.
The development selection remains `NOT_RUN` until newly authorized, bounded
requests and their exact cost contracts are admitted. Existing k3 performs no
multi-group packed verification; a q8 operator win alone cannot establish a
gain over the strongest k3 service control. A scripted wider cycle that closes
the state chain is not evidence of a beneficial service policy.

## Measure the complete resident request once

The intended deployment keeps models and context pools resident. Begin the
same-request wall timer before reset, per-request planning and guards; end
after final target/draft synchronization, reconciliation/fallback and response
readiness. Model loading and resident provisioning are reported separately,
with their resource/window costs. Cold-start application claims require a
separate endpoint that includes those costs.

`timeline.hpp` supplies a host `steady_clock` recorder. Its compilation was
attempted with the frontend and independently, but the compiler returned
`Unexpected` at line 1 before producing an object. It is not compile-verified
and is not yet inserted at the required hooks. Insert spans
at reset; target/draft prefill; proposal generation; target verification;
synchronization; planning; guards; output sampling/copying; trim/pending
reconciliation; fallback; teardown. Allocation and controller overhead belong
inside the complete request endpoint. Native core guards and DLL/source
admission may also have one-time costs, which must be named and reported.

`costs.py` decomposes one request's host timeline exclusively: nested sync time
is removed from its enclosing verify time, crossing spans are rejected and
unattributed wall time stays visible. CUDA event timings use another clock and
remain separate operator diagnostics. Never add asynchronous kernel spans to
host intervals, sum target/draft spans that overlap, or assemble a cost stack
from different requests/panels. Capture-heavy times cannot become clean
performance prices. A complete elapsed endpoint remains authoritative even
when detailed category attribution is incomplete.

The initial CPU cost reader carried a caller-supplied `complete_endpoint` flag.
Independent review found that it could not prove reset/guard inclusion. The
revised reader names that flag `complete_endpoint_self_declared`, leaves its
endpoint qualification `UNVERIFIED`, and refuses a paired service claim unless
the launcher supplies a separately frozen independent endpoint audit for each
source/request. That proof binds endpoint boundaries and required stage
coverage; missing stages require independent zero-work receipts. No such
native audit is fabricated in this CPU preparation. The initial CPU logs are
retained, and the correction has separate versioned CPU results.

Admit paired service results only after numeric/state qualification and with
the same request, logical policy, producer and contract. Freeze selection and
held-out order before clean timings. Report A→B launch/grid effects and B→C
weight-fragment changes separately. Report a real adverse result without
adding samples to seek a positive sign. First-round advancement requires
qualified exactness, an interpretable paired C-over-B improvement, the actual
consumer chain and complete service costs with plausible net benefit.
