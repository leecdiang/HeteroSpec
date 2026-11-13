# Controller contract and stopping points

The unchanged PR226 REFERENCE_CONTRACT.md remains authoritative. This controller
does not repair a strict mismatch by changing reference arithmetic, output masks,
token history or tolerances. Tokens/argmax agreement is insufficient.

| Stage | Input and ownership | Required delivered-byte gate | Next action on failure |
| --- | --- | --- | --- |
| Resident R | Independent original R numerical core; own producer, own resident context, exact user inputs; reset only between episodes | All63 state checkpoints,18 owned events, complete receipts and27 self checks | Preserve report/first difference; no repeat |
| Repeat R | Independent process/context and own producer; expected R inputs are assertions | Same contract plus54 aligned comparisons,27 self checks;81 total | No cold and no candidate |
| Cold canonical oracle | Exact provided R canonical IDs and retained-head alignment; empty/reset KV per turn, independently computed prefix and outputs |18 self checks and54 aligned comparisons;72 total; no prior-KV-retention claim | Contract conflict or first full-byte difference stops strong |
| Strong whole-rechunk+loop4 | Same complete legal suffix, producer, trim/rebuild/cap/stop and output obligations; own greedy continuation |27 self checks and54 aligned comparisons;81 total | No timing, reference switch or automatic retry |

At POST_RECONCILE only aligned active KV is compared: resident invalidates its
frontier, while cold independently computes its prefix frontier. At POST_APPEND
and TERMINAL compare every declared full vocabulary row and all active KV.
Retained-prefix checks compare previous terminal bytes using the original head
stride, not matching heads. Ownership checks bind the exact previous final row
to before/decode/after events; reset requires empty actual active ranges.

State transitions are persisted before acknowledgments. One worker stays reserved
through accounting close and owned-exit/log confirmation. No unknown process is
killed to recover a lock. A stopped/in-flight/crashed/uncertain attempt is inspect
only; a successor needs its own reviewed protocol and permission, not a new
directory to evade counters.

The R input certificate is written only by the internal verifier path after its
required file/byte checks. Its snapshot descriptors/run/IDs/head/cap are checked
again before late-binding subsequent jobs. It is explicitly provided-R evidence,
not proof of cold equality. Repeat/strong receive expected canonical assertions,
not a forced natural generation tape. Scripted controls retain their separate
scope and exact fixed token inputs.

Production launch remains impossible in this build. All model/backend/context,
placement and forward counts for this CPU task are zero. Synthetic state
machine PASS and provided-file PASS are separate from native qualification.
All261 native entries remain NOT_RUN, regardless of how many CPU cases pass.
