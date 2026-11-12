# What the q4 frontier diagnostic permits a dynamic {4,8} path to consume

**Status: read-only interpretation and a future qualification design.** This note adds no execution or budget allocation. The completed CPU panel is not rerun, and the six frozen guard/architecture files are unchanged. Here q4/q8 denote numbers of token rows, not weight quantization.

## Decision

The new result supports a specific local opportunity: **for the two tested forced histories, an already-known eight-row operation can use q8 or q4+q4 while retaining all eight vectors, active state and the tested forced continuation.** It does not establish that an arbitrary partial frontier with equal KV is a valid replacement for every greedy/speculative continuation.

At frontier5, the unequal fifth vector is exactly the kind of value a real speculative loop may need next. A dynamic path must retain a qualified owned vector for that consumer, or reject that edge. It cannot accept a proposal on the strength of KV equality, substitute equal argmax for the full-vector contract, or discard an output that the original call requested. [Q1–Q3, W1]

There are also two different changes that should not be conflated:

- **Native tiling:** execute the same known k7 verification rows as q8 or q4+q4. This is what the macro diagnostic directly compares.
- **Transaction depth:** choose k3 or k7 across speculative cycles. That changes proposal generation, accepted-prefix processing, bonus behavior and draft lifecycle. The audited worker takes one `k` for its request loop; a dynamic-depth controller is not already implemented by allowing both values at job admission.

The safest initial path investigation retains canonical four-column arithmetic tiles and the complete owned outputs. It does not use a q1 materialization result as an interchangeable frontier vector merely because its resulting KV matches.

## Evidence and its exact limits

Published source commit `ef2766327e7821fe188d1ad788b2c3b05531eb9a` ran one bounded CPU panel: 14 contexts, one model load, 146 native decode calls, 3,612 target rows and four trim calls. The fixture is an untrained two-layer F32 model, vocabulary 128, F16 KV, one CPU thread, non-Flash, context capacity 1024. Histories have lengths 248 and 252. The reference is explicitly the same-deployment q4+q4 diagnostic, **not historical paper R**. [Q1–Q3]

| Comparison | Primary obligations that passed | Important remaining distinction |
|---|---|---|
| q8 versus q4+q4 at frontier8 | All eight full vectors, active state, geometry and one common forced continuation | Known forced inputs on this fixture; no natural acceptance, historical-R, CUDA or production qualification |
| q8 then trim to frontier4 versus q4 | First four full vectors, active state, geometry and common forced continuation | The narrower consumer projection is not a blanket equivalence claim for every requested output of a production q8 call |
| q8 then trim to frontier5 versus q4+q1 materialization | Preregistered first four consumer vectors, active state, geometry and common forced continuation | Fifth vector differs in both histories and was explicitly excluded from the primary consumer set before execution |

The fifth vector has 117 of 128 unequal floats at history 248 and 128 of 128 at history 252; the maximum absolute differences are approximately `3.58e-7` and `3.89e-6`. Its argmax happens to agree in both cases. That is useful diagnostic information, not a full-vector pass or a reason to change the contract. [Q2, Q3]

The continuation test has a particularly important interpretation. Before continuing, the probe calls `owner.plan.clear()` and then decodes the fixed token 37. It therefore **does not read the unequal fifth vector** to decide the next token. Agreement after that forced input is consistent with the fifth-vector mismatch. It tests one action whose input is externally fixed; it does not test the real greedy edge that first reads that vector. [Q1]

The fifth input token itself is fixed by the probe; it has not been shown to be an accepted proposal, correction or bonus produced by an actual reference request. The worker mapping below is a conditional interpretation, not a claim that this forced trace already followed that loop.

The first-four consumer projection was preregistered and is a valid diagnostic. It does not retroactively replace the paper’s full requested-output contract. The probe still requested and saved all operation outputs, and its public result explicitly leaves production full-mask qualification false. [Q1, Q2]

## Exact relationship to the worker’s speculative loop

Let `B` be the first target position that has not yet been materialized. The worker has already emitted a `pending` token `s`; the next cycle uses it as `seed`. With proposals `p0,...,p(k-1)`, verification inputs are:

`[s, p0, p1, ..., p(k-1)]`

Let `L_i` be the full vocabulary vector returned after verification input row `i`. The worker samples every requested row into `decisions[i]`, then compares `decisions[j]` with proposal `p_j`. The alignment is therefore: [W1]

| Output | Input row that produced it | Logical consumer |
|---|---|---|
| `L_0` | seed `s` | Verify first proposal `p0` |
| `L_1` | first proposal `p0` | Verify second proposal `p1` |
| `L_2` | second proposal `p1` | Verify third proposal `p2` |
| `L_3` | third proposal `p2` | Verify fourth proposal `p3` for k7, or produce the bonus after all three proposals are accepted for k3 |
| `L_4` — the fifth operation vector | fourth proposal `p3` | Verify fifth proposal `p4` for k7 |
| `L_7` | seventh proposal `p6` | Produce the k7 bonus if all seven proposals are accepted and the request has not stopped |

“The fifth vector” is not the output after the fifth proposal: it is the vector after the fourth proposal, used to judge the fifth proposal. This indexing matters at the frontier5 cut.

If k7 rejects the fifth proposal, four proposals have been accepted. The worker sets the correction from `L_4`, emits that correction as pending, and trims to `keep=B+1+4=B+5`. The retained KV contains the seed and four accepted proposals; the rejected fifth proposal and later speculative rows are removed. Its owned `L_4` is still needed to select the correction even though the retained KV is identical under another path. **KV equality cannot supply the missing target decision.** [W1]

For k3 with all three proposals accepted, `L_3` yields a bonus. The worker trims to `B+4`; the bonus has been emitted but is not yet materialized in target KV. The next cycle uses that bonus as the new seed. If an optimization materializes the bonus early, reaching frontier5, its resulting `L_4` is what would judge the first new draft proposal. Marking that token “already materialized” does not eliminate this consumer; it changes where the required vector must be obtained. [W1]

## Legal next-action boundary

The tested macro node retains all eight owned vectors. Frontier4 retains the matched first four vectors and state. Frontier5 only establishes equality of state and the first four vectors: it does not supply an interchangeable `L_4`. Its fixed-token continuation is valid as a diagnostic, while a fifth-proposal acceptance/correction or greedy-next-token edge that reads `L_4` has **not passed the stronger contract**.

A useful next candidate can retain `L_4` from a separately qualified q8 or second q4 tile, rather than replacing it with the differing q4+q1 materialization output. This preserves an avenue for {4,8} tiling. It does not justify merging nodes using KV alone. The logical node must include required owned vectors, emitted IDs, pending token identity/materialization status, stop status and relevant draft state.

All `k+1` outputs in the actual worker are requested and sampled before acceptance processing. Even a later terminal branch that does not choose a token from one vector cannot erase its original requested-output obligation. Changing the mask or declaring a new consumer-only API would require a separate reference and qualification; the preregistered diagnostic projection does not relax the paper contract. [W1, M1]

Matching numerical state also does not establish matching future costs: cached graphs, prior call widths and reuse/allocation state may differ. This panel admits no actual controller stage costs. Its wall duration cannot be used as a cost profile or evidence of a service gain.

## Minimal next real-request closure — design only

**This note allocates zero executions or resources.** The completed 14-context panel is finished and is not rerun or extended. The following is a recommendation for a separate, versioned, bounded real-request protocol whose source, inputs, logical policy and resource ceiling must be frozen before execution. It does not replace or silently alter any existing S3, `production_compare`, or other frozen panel. No new model load, context, native call or GPU run is allocated here; absent native access or an independent original reference, its qualification status remains `NOT_RUN`.

Freeze one existing real prompt/proposal trace and its producer identity, reference, cap and path policy. Prefer a trace containing an all-accept bonus followed by fifth-proposal rejection. Do not edit proposals to force these events and call the result natural acceptance; if no available trace contains them, retain the uncovered status instead of adding requests.

| Step in that one request | Real consumer and worker fields to compare | Failure that this closes |
|---|---|---|
| k3 all-accept bonus | Read `L_3`; compare all requested vectors, `accepted=3`, `keep=B+4`, emitted bonus `b`, target/draft state and `pending_after=b` before the next cycle | Treating emitted bonus as already materialized or emitting it twice |
| Next verification consumes bonus | Use actual `seed=b` at the actual `base`; for the known eight rows compare q8 with q4+q4 under the declared reference, retaining all eight full vectors | Replacing a real decision-dependent input with fixed token 37 |
| Reject fifth proposal | Read `L_4`, compare `decisions[4]` against `proposals[4]`, set correction `c`, require `accepted=4`, `keep=B'+5`, matched trimmed target/draft state and owned frontier, `pending_after=c` | Skipping the fifth proposal check because frontier5 KV matches; using a differing materialization vector |
| Next phase consumes correction | Use actual `seed=c` at the retained `base`; compare full originally requested vectors, decisions, state and the request's actual terminal outcome | Dropping or duplicating the correction; incorrectly forcing terminal pending-token materialization |

The comparison must keep the same declared logical policy for reference and candidate. A scripted native tiling schedule is path qualification, not evidence that a controller chose well. If k changes across cycles, the new request-loop implementation must be identified and qualified; the fixed-k worker cannot be silently called dynamic. Historical-R qualification remains a distinct prerequisite: the tiny q4+q4 diagnostic is not that reference.

Retain original cap/EOG behavior. A request that ends immediately after a correction or bonus may leave it emitted but unmaterialized, as the worker specifies. A single case has one actual terminal outcome; CAP coverage does not certify all EOG branches. Do not add a decode just to make terminal KV snapshots look alike.

The closed chain must compare complete original requested vectors, target and draft state/geometry, token decisions, accepted counts, trim positions, pending identity/materialization, emitted IDs, EOG flags and stop reason. Stop at the first mismatch and disallow owner reuse. Until those obligations and separate cost admission pass, the outcome remains a local legality finding with **no qualified dynamic controller, measured service gain or general 5% result**.

## Source and evidence identities

| ID | Artifact / source | SHA-256 |
|---|---|---|
| Q1 | `q4_frontier/frontier_probe.cpp`, source commit `ef2766327e7821fe188d1ad788b2c3b05531eb9a`; `run_arm`, operation capture and fixed continuation | `87a29b58de15e0c7269a37c3e260285c9a569ee3011a8394e8ecdddbbca1b820` |
| Q2 | `q4_frontier/PUBLIC_RESULT.json`; final observed scope, accounting and fifth-vector diagnostics | `5e20c022a553551d177aa6c2848c4cf898c3c1e175a40d2a9b066326531070b1` |
| Q3 | `review/q4_evidence_review.json`; independent raw-blob verification, no native execution by reviewer | `74f90c2d7da3ddb42eb8e3e2859549dcf78d15f66cd41fbc21e0ffc1fbb713e4` |
| W1 | Reconstructed Linux M2 `candidate_frontend/worker.cpp`, request loop: proposal generation, `verify`, decisions, pending/bonus/correction, trim | `05e395aa3082b08229946139c1f0d298bfc1c3064f001ba5c10aefcc9487eecb` |
| M1 | PR #222 method section at `e8a4981ef7db8f05cff7144fd4edc6e5a4109343` | Exact method bytes are bound in the frozen `GUARD_MATRIX.json` |

Native raw result SHA-256: `6aebb51bb96ffa962ee8907ffa03900890414b752e1f021f17382af982e6c967`. The preregistered plan SHA-256 is `9116bb02c0d3553a208abfbd8e7d36ef1eda7571511762f77b277a013ff4c6c2`. No file in the completed panel was modified by this analysis.
