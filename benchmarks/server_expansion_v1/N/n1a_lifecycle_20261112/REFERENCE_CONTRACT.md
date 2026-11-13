# N1a reference contract: proposed, not native-qualified

This document defines comparison eligibility before any GPU request. No resident
reference, cold-reference model execution, native state capture or four-arm
qualification is established by the CPU work in this successor. The original
C1024 reference and all old data remain unchanged; JSON cannot turn that binary
into a C4096 reference. A separate source-bound descendant and native adapter are
required. No GPU allowance is inherited from PR224/225 or a different study.

## Four paths and the gate order

1. **RESIDENT_R** is independent of the candidate modules. Bind the original fixed
   Linux reference arithmetic, exact Qwen8B Q8 weights/tokenizer, C4096/F16 and a
   newly frozen sequential caller. It generates its own finite-logit greedy
   responses with the declared tie rule, EOG/cap and actual producer. Use one
   context/seq0 throughout both user turns; reset between independent episodes.
   Do not replace its next turn with a convenient cold full-prefix execution.
2. **REPEAT_RESIDENT_R** repeats the complete same producer/episode in an
   independent process/context, retaining its own KV and generating its own
   responses. This tests repeatability of R, not canonical equivalence. If it
   differs, retain the first difference and stop.
3. **COLD_CANONICAL_ORACLE** uses R's frozen exact canonical input IDs for each
   turn but starts that turn with empty KV/pending/frontier and computes its own
   state with the same reference arithmetic. It never restores a resident capture.
   The context allocation may be reused, but its KV is explicitly cleared each
   turn. This is a separately charged input replay oracle, not a resident free
   episode or independent natural observation. It samples its own response and
   must agree under the strict contract below.
4. **STRONG_WHOLE_RECHUNK_LOOP4** is eligible only after both reference gates pass.
   It receives the same complete legal suffix, producer/stop/cap/trim/rebuild and
   placement opportunities. Its own greedy output determines its own next
   history; an R tape must never be forced into a divergent free candidate.

R and cold deliberately have different cache histories. Their full canonical next
token vector, model arithmetic, sampling contract, logical position, output mask
and compared active ranges must nevertheless match at each declared alignment.
If those semantics cannot be aligned, return CONTRACT_CONFLICT before a numeric
claim. If eligible full vectors or active state differ, return the predeclared
strict failure, preserve raw bytes/first coordinates and stop. Repeating resident
R successfully does not waive this oracle gate. Do not change references, apply
a new tolerance, compare only argmax, or begin timing after an unexplained result.

## Exact temporal alignments

Let Q be the complete next canonical input vector, L the old logical IDs and m
the actual materialized head. Compute k=min(tokenLCP(L,Q),m) before mutation.
If k==len(Q), reduce it by one to obtain a fresh final-token output. The producer
and all resident paths use this same policy. Invalid state, unsupported trim or a
declared no-mutation failure uses a common full reset/rebuild, k=0, fully charged.
Any unexpected native error after decode starts stops; no unbudgeted second pass.

| Alignment | Resident state | Cold oracle state | Eligible comparison |
|---|---|---|---|
| POST_RECONCILE | Keep exact Q[0:k], trim old suffix, discard/reconcile pending; frontier invalid | Starting empty, independently decode Q[0:k] in reference q1 order | All active K/V for positions0..k−1. Its fresh prefix frontier and resident's invalid old frontier are deliberately not equal outputs. |
| POST_APPEND | Decode Q[k:] once; synchronize and own its requested last-token vector | Decode the remaining Q[k:] after its independently computed prefix | Exact Q, head=len(Q), complete last-token vocabulary vector and all active K/V. |
| TERMINAL | Own generated IDs Y, with the last sample pending | Same greedy/stop contract on Q, own generated IDs | Full generated/stop/pending identities, all sampling vocabulary rows, frontier and active K/V at aligned positions. |
| RESET | Clear sequence/pending/frontier after the episode | Same explicit empty checkpoint | Empty active positions and ownership state; no demand to zero inactive allocator bytes. No model request or forward is hidden in reset. |

At terminal, materialized IDs are Q||Y[:-1], logical IDs are Q||Y and pending is
Y[-1] at position len(Q)+len(Y)−1. Capture every actually requested sampling vector
at positions len(Q)−1 through len(Q)+len(Y)−2. An actual EOG remains an EOG; cap
does not append a manufactured EOS. All six model-vocabulary EOG IDs participate
in the predicate. Natural cap remains128; cap1 is explicitly confined to named
scripted controls. Full-cache replay decodes the last token once and cannot sample
an old frontier. Caller-owned output copies must survive the next decode/trim.

The oracle's q1 boundary at k is for a state checkpoint within the same original
q1 arithmetic/call order, not permission to build a faster or numerically different
reference. The strong candidate may batch/rechunk the complete append; requested
outputs, active-state semantics and strict comparator remain fixed. If the actual
reference backend cannot expose this alignment without changing arithmetic,
record that contract conflict and stop before pretending the comparison is valid.

## Raw numerical rule and provenance

N1a proposes strict raw-byte equality for complete requested F32 vocabulary rows
and all active F16 K/V across36 layers,8 KV heads and128 head dimensions, with
explicit little-endian canonical tensor coordinates. Nonfinite captured values
are ineligible under this strict profile. No tolerance, relative error or argmax
substitution is an acceptance rule. If the source reference legitimately requires
another representation/rule, it needs a new prospectively reviewed contract;
do not silently reinterpret an existing capture.

plan/raw_compare.js streams actual bytes in bounded chunks, verifies shapes,
coordinate order, IDs, pending/frontier and transport identities, and records the
first differing scalar and its bits/coordinates. Hash equality never replaces the
byte/numeric comparison. RETAINED_PREFIX checks must compare the previous real
terminal active bytes against the current retained prefix, not only compare two
paths that might share the same corruption. Output-stability pairs require bound
source snapshot, row/run/context and before/after decode transition receipts.

The delivered comparator is CPU preparation. Passing provided synthetic files
cannot prove a truthful native writer, actual memory ownership, source identity or
complete comparison coverage. A future native admission validator must enumerate
every required operation/checkpoint/pair, bind raw captures to actual executable,
producer/model and ordered native work receipts, and reject missing coverage.
That validator/driver is not implemented or authorized by this preparation.

## Controls and limitations

Five concrete two-request token-caller fixtures cover pending CAP append,
empty-think trim, full-cache replay/ownership, trim unavailable and injected
pre-mutation trim failure. Their immutable raw IDs are shared across all paths;
they are **SCRIPTED_RAW_TOKEN_CONTROL**, not canonical natural chats or free
responses. Forcing a control token constructs a state; it is never reported as a
greedy or EOG observation. Their setup, suffix/oracle work and reset are explicit.
The two fallback fixtures test caller policy, not arbitrary native API corruption.

CPU EOG/tokenizer/parser fixtures are separate from native EOG qualification.
Natural EOG may or may not occur in four future episodes; universal EOG behavior,
capacity extremes, additional failure states, packing and LOCAL still require
N1b. N1a includes no LOCAL/packed execution and no service-speed claim. Only a
strict N1a pass can motivate a separately approved four-arm N1b; only qualified
real execution with an attributable difference can motivate new-root N2. N2 must
pair whole episodes/roots and charge history construction, required rebuilds,
controller/state and all service work, separating natural and artificial inputs.
