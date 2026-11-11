# PR108 P1 — stopped on execution-contract error; NO-GO

Design8d7b85d8aac6e546ca23e1f8a6ad353ea7ed2e02. Native implementationbb803c94f23af0e5ab4e250c52f74e0b60621a66. Execution authorization was published at17f942e5 before the first start. Exact approved F0 SHA256 remains29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8. This F0 and all original artifacts are unchanged.

## Why execution stopped

The independent post-start semantic audit found that F0's universal every100ms request VRAM-sampling declaration does not describe original R. Its unchanged native counts runtime records requested_period_ms=null and only REQUEST_BEGIN / TARGET_PREFILL / REQUEST_COMPLETE / ENGINEERING_END checkpoints. The eight R receipts show maximum gaps2874.172–3032.6884ms. The rebuilt actor uses the declared100ms sampler.

This was a P0 review omission: byte hashes, build success and CPU tests did not establish the field's meaning. The current independent raw auditor did not enforce the F0 cadence declaration before allowing later stages. Detection occurred after48 completed requests while the49th request was active. The active owned worker PID12836 was checked against its frozen executable path and terminated with exit99. The runner then closed normally through its failure path and stopped. No other task/process was terminated.

There was no observed sampled-memory threshold failure, but adequate sampled headroom does not repair the declared sampling contract. The discrepancy is not silently reinterpreted, relaxed or retroactively amended. All observations below are retained exploratory native evidence with this protocol limitation, not a completed compliant P1 panel. No remaining slot was resumed or replayed. The original R binary was not replaced.

## Actual accounting

| Item | Actual |
|---|---:|
| Native process attempts |49|
| Model request starts |49|
| Complete endpoint/raw-audited requests |48|
| Incomplete request retained |1|
| Unstarted coordinates |31|
| Actual model forward caller starts/returns |8,110 /8,110|
| Forward callers in completed requests |8,109|
| Forward in the terminated request |1 successful target PREFILL caller; no VERIFY observed|
| Operator starts / warmups / probes / scientific retries |0 /0 /0 /0|
| Exact owned native PID lifetime |442.8113613s|
| Conservative charged owned interval |444.416s|
| Immutable raw run output |23,073,242bytes|
| Completed-request target/draft micrographs |4,791 /3,374|
| Completed-request target/draft occupied rows |14,138 /7,208|

The old R has no per-forward stdout events: its1,024 actual forward callers are reconstructed from eight complete native RESULT counters. The new actor has7,086 observed FORWARD_START and matching successful FORWARD_RETURN events, including the partial request's prefill. They sum to8,110 without mixing requests and forwards. Partial-request physical micrographs are not filled from planned widths.

Minimum sampled same-PID signed B570 dedicated headroom1,627,435,008bytes; minimum sampled available host RAM10,406,928,384bytes. These are sampled observations, not continuous residency. All source/runtime/model/driver hashes rechecked unchanged after stopping. Original PR105's failed request/process,127 decodes,12.438s and167 unstarted slots are untouched.

Failed coordinate: candidate_diagnostic / GSM8K/test/1249 / C_R_QB / session0 / slotff67f74a6a86f5d1346b7d1b. All31 unstarted coordinates are in ANALYSIS_P1.json and the immutable native CLOSEOUT.json inside the archive. The native CLOSEOUT error is EOF; the ledger's INDEPENDENT_CONTRACT_STOP and OWNED_CONTROL_TERMINATION events record the substantive cause. It is not mislabeled as a model crash or an out-of-memory event.

## Complete outputs observed before stopping

All four original-R pairs were stable; R_SHADOW's four counts and four diagnostic endpoints matched original R, with no endpoint observation drift on those controls. Candidate diagnostic endpoint comparisons were not completed.

| Arm | Counts endpoints equal to R | Complete-output differences, zero-based first index |
|---|---:|---|
|R|8/8, including both repeats|None; cadence contract failed|
|R_SHADOW|4/4 counts +4/4 diagnostic|None observed; not a replacement R|
|M_B_QB|2/4|/1248:47; /831:81|
|M_R_QB|4/4|None in counts; candidate diagnostic missing|
|C_B_MQ|1/4|/1248:47; /831:40; /1011:10|
|C_B_PQ|2/4|/1248:47; /831:81|
|C_B_QB|1/4|/1248:47; /831:40; /1011:10|
|C_R_MQ|2/4|/831:40; /1011:10|
|C_R_PQ|4/4|None in counts; candidate diagnostic missing|
|C_R_QB|2/4|/831:81; /1011:10|

All14 candidate endpoint counterexamples are retained with complete IDs, EOG flags, length, terminal token, stop and cost. These14 endpoints and their references all reached CAP128, so no shorter incorrect output is used to claim speed. Every arm remains in the evidence. Full P1 qualification is NOT_ESTABLISHED for every candidate because diagnostic controls are missing and the execution contract failed. No single matching pair is promoted to panel qualification.

Independently of the contract stop, C_R_QB's two valid counts mismatches already fail the frozen requirement to match original R on all four sentinels. P1-to-P2 is NO-GO. There is no new input selection, third search, altered k or shader/precision intervention.

## Geometry, costs and what can be inferred

Counts retain actual successful continuation-width histograms and observed VERIFY caller events. CALLER_OBSERVATIONS.json binds actual caller widths to raw stdout lines/hashes, separately from the missing physical transaction witness; a llama_decode return is not a completed GPU kernel timestamp. A phase-bound ordered micrograph trace is unavailable: the only started candidate diagnostic was stopped after prefill. VERIFY_WITNESSES.json is empty. Therefore no qualified genuine multirow VERIFY witness is claimed, even where a continuation histogram contains width2. Backend dispatch, compute-array concurrency and numerical DAG remain separate unknowns.

Descriptive counts native request ranges, seconds: R2.967–5.643; R_SHADOW3.112–5.623; M_B_QB3.112–3.115; M_R_QB3.013–3.214; C_B_MQ3.114–4.018; C_B_PQ3.216–3.415; C_B_QB5.120–5.724; C_R_MQ3.012–3.214; C_R_PQ3.212–3.323; C_R_QB5.020–5.222. Every individual timer is preserved in ENDPOINTS_P1.json. Native windows include reset, natural prefill, decode/verify, draft/reconciliation, end synchronization and the applicable safety lifecycle. Loading remains outside that timer. LOAD_ADMISSION_WINDOWS.json independently reconstructs49 native BEFORE_LOAD→LOADED civil-clock admission windows of3.582–4.911s; these include backend/model/context/vocabulary admission and are not exclusive pure-I/O or GPU-stage fees. No global speedup, qualified ratio or cross-time conclusion is reported; performance aggregates remain WITHHELD.

Producer constraints correspond to4/4 counts matches for M_R_QB versus2/4 for M_B_QB, but do not establish internal state equality. With reference128, PQ has4/4 counts matches while MQ and QB have2/4 each. Adding draft/VERIFY changes the M_R_QB4/4 pattern to C_R_QB2/4. C_B_QB1/4 versus C_R_QB2/4 shows an endpoint-domain change on this finite exposed set, not a universally reference-preserving combination. Missing candidate initial-state diagnostics prevent a stronger causal state/numerics interpretation. All inputs are previously exposed; no unseen-input claim is made.

## Recovery and hardware handoff

The immutable P1 CAS contains560 logical files /559 unique objects; SHA256245f6194161ec573f074c9738495951c68da91a2f09e10d719d753af36248fce,4,062,125bytes. Fresh sequential restoration independently re-audited all48 complete slots and retained the incomplete49th slot. Authenticated remote readback matched all72 committed P1 files; the remote CAS was freshly reconstructed and all48 complete slots independently re-audited again. The eight cadence failures were then independently rederived from the remote raw memory receipts, rather than accepting the saved conclusion. Both contract-regression CPU tests passed. The original schema-2 exporter produced48 records with the required plan/runtime/raw-root and same-task/session original R where available. Its individual MATCH/MISMATCH statuses do not override this execution-contract failure or qualify a panel. Old R raw paths were rebased explicitly; payloads were unchanged.

Hardware first-stage conclusion: HOLD_MISSING_EVIDENCE. H-L: phase/cache/synchronization source paths exist, but effective new graph-invalidation/dispatch time is not measured; the old phase_binding_calls counter only covers the legacy repair branch and must not be treated as a new universal count. H-M: shared KV views do not establish measured DRAM/cache savings. H-A: endpoint divergence may involve representation/backend numerical or layout behavior; the opaque GPU arithmetic DAG and operator data are insufficient to separate these explanations. H-S: natural producer/consumer contrasts provide finite endpoint observations, but candidate diagnostic state evidence is missing. Strong software PQ remains an alternative to examine within a separately approved study, not evidence that new hardware is necessary.

DRAM, cache hits, XMX utilization, completed kernel times, continuous physical residency, resource concurrency, complete operator metadata, area and power stay UNKNOWN/null. No hardware model, RTL or PPA was developed. P2 and P3 were not started and are not authorized by this stopped run. This branch closes without another scientific retry.
