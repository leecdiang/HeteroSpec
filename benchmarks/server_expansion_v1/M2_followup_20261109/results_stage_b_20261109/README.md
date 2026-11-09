# Stage B: qualified equal-work q4pair/q8; startup and order remain aliased

All native work completed at 2026-11-09 18:37:03 Asia/Shanghai. The 32 finite
qualification cells, 16 descriptive measurements and 8 primers completed. This
is a target-operation diagnostic on the four previously exposed M2 roots, with
only the prespecified first root timed. It is not live speculative service,
a new blind sample, population inference, or a change to the previous M2 result.

The timing sign reverses between rounds. Round0 has one primer per cell and
q4pair then q8. Round1 starts fresh block processes, has no additional primer,
and runs q8 first. Thus batching width, request order and first-use state are
not separated by the pooled statistic. Preserve all data; do not report either
the pooled slowdown or the first-round saving as steady-state q8 efficiency.

| Projection | Start position | Round | q4pair ms | q8 ms | q8/q4pair |
|---|---:|---:|---:|---:|---:|
| loop4 | 248 | 0 | 36.546 | 34.504 | 0.9441 |
| loop4 | 248 | 1 | 37.373 | 60.345 | 1.6147 |
| loop4 | 252 | 0 | 39.481 | 37.345 | 0.9459 |
| loop4 | 252 | 1 | 38.081 | 72.683 | 1.9086 |
| packed | 248 | 0 | 36.562 | 33.773 | 0.9237 |
| packed | 248 | 1 | 37.578 | 61.088 | 1.6256 |
| packed | 252 | 0 | 38.579 | 35.903 | 0.9306 |
| packed | 252 | 1 | 37.997 | 63.223 | 1.6639 |

The registered two-round rollups are retained unchanged in RESULTS.json:
q8/q4pair = 1.2831/1.4186 for loop4 within/crossing and 1.2795/1.2945 for packed.
Graph build/reuse counts and nested phase clocks are in every receipt. A graph
counter is not a kernel launch count; VERIFY clocks are not kernel timings.
These fields do not prove which internal first-use cost causes the difference.

## Reference and numerical eligibility

Original R is unchanged: pristine Linux UB1/reserve1, frozen SHA
`fa8ceec6d54f98730d63880436a6bf088c119232c0f091406725e724a4665731`.
The target is the original Qwen3-8B Q8_0 file; q8 here means physical width8.
Candidate arithmetic archives are the unchanged hash-checked M2 loop4/packed
archives. The diagnostic adds a frontend, not a numerical optimization.
Use C1024, F16 KV, noFA, UB32/reserve8, LOCAL, two threads and the assigned single
A5000. Allocation identity is private. No draft is loaded or executed.

Historical formal R receipts retained token endpoints but no required
intermediate vectors/KV. The admitted remedy charges four autonomous R128
replays, three same-R extensions and four forced scalar trunks. All replayed
128-token endpoints equal the old frozen endpoints. Extension pending tokens,
full frontier and active KV match the independent replays; full autonomous and
forced scalar vectors agree. Old roots, original128-token records and baseline
files are unchanged. No padding, origin substitution or tolerance relaxation.

All32 qualification cells compare all8 full vocabulary vectors plus initial
frontier and initial/final active KV, using the unchanged strict readers. Actual
q4pair is two physical width4 calls; q8 is one physical width8 call, including
the crossing case. Requested masks are complete and final bounds match.
Within/crossing extents are256/512 as recorded. q8 loop4 and packed expose their
actual marked projection descriptors; q4 has no wide-packing claim. These are
scheduled tensor descriptors and core counters, not CUDA-symbol profiling.
Timing/primers verify all8 output hashes and bounds, with zero online heavy
captures/state transfer. They do not redo full KV export/comparison during the
operation timer. This is not new live EOG/cap/pending/rollback qualification.

## Complete recorded cost and failures

Stage B charges67 requests:11 R,32 qualification,8 primers and16 measurements.
There are27 unique complete native worker processes and no failed native worker
event. One earlier completed extension and one completed timing block were
commitment-checked and reused once, never rerun or refunded. Source/record
failures remain retained: pause-directory collision, missing prompt hash field,
missing historical captures, duplicate table kwargs, the first adapter's narrow
whitelist refusal, and the supervisor's archive-log name collision. Closeout03
uses new output/log paths and runs no model. See EXTRA_FAILURES.json as well as
the original traces in the archive. Retrospective preparation annotations are
explicitly labelled; they are not reconstructed original stderr logs.

| Worker group | Processes | Adapter-inclusive wall s | Native-process wall s |
|---|---:|---:|---:|
| Independent R | 11 | 256.133 | 110.155 |
| Qualification | 8 | 562.068 | 472.040 |
| Timing, including primers | 8 | 490.298 | 402.646 |

The adapter-inclusive sum is1308.499s (21.81min), not GPU kernel time. Build
compile/link records total19.270s. Clocks overlap: do not add process, setup,
restore and operation fields. The16 measured operation timers total0.701060s;
their separate snapshot reads total2.113937s and restore/frontier copies total
3.739152s. Output-copy0.013024s and planning0.000043s are already nested in the
operation total. Startup, hash/load, complete request strings and resource
receipts are retained. CPU preparation/energy/kernel time has no separate total.

Actual recorded target work is3151 rows (2703 R,256 qualification,192 primer/
timing), with zero draft rows. Conservative reservations are28695 rows. Final
cumulative budget is1893/2048 requests and3049826/8000000 reserved rows, leaving
155 requests and4950174 rows; unused stage quota is not automatically transferred.
The selected-device sampled total-minus-free maximum is8518MiB, with16046MiB
minimum sampled free. This2s-sampled value is not an exact per-process peak.
The371 resource-observer samples report no selected-GPU foreign process or
interference event; short/shared-interconnect interference is not excluded.

## Archive and decision at the B completion cut

The public bundle has562 sanitized text records,1948580 compressed bytes, SHA
`8d18fc21bc25bd81a288b9c7610860660fa2fe74c266216540c7ddf9d05eeae6`.
PARTS.json commits8 ordered parts. TEXT_INDEX.json binds original and exported
text. BINARY_CAPTURE_INDEX.json commits1728 retained private captures totaling
7626948252 bytes. Weights, executables, credentials, allocation UUID and unrelated
foreign-job identifiers are not published. Public commitments do not allow an
independent reader to requalify unavailable private numerical payloads.

Local byte/statistic replay passed, including original native receipts, frozen
oracle commitments, all32 qualification records and physical/cost reconciliation.
Public readback status is separately committed after upload; local replay alone
does not establish public delivery or new numerical correctness.

At this cut C–E, optimization and32B are NOT RUN. B establishes numerical
eligibility and a startup/order limitation, not an attributed removable hotspot
or a reason to change the finite old k3 recommendation. Any further controlled
profiling must be registered separately against the remaining original budget.
Preserve these completed data; do not repair the design by selectively repeating
or replacing them. No manuscript edit, merge, Release or data deletion.

Reproduction: see REPRODUCE.md, DIAGNOSIS.json, the source epochs in the archive
and the immutable admission/build bindings in ../stage_b/.
