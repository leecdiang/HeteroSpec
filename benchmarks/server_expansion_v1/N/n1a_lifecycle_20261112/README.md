# N1a preparation: CPU fixes, genuine serialization fixtures, no native qualification

Independent successor of PR225 head
`a996df95c1578c47a791ebcf91d55d0148264a38`, with PR224 frozen at
`8be5f9acf3139356ecd95f065964373c7c83ffde`. The latest PR225 discussion was empty
at start. Original protocols, reference, source, STATE, negative results, failures
and GPU ledgers are preserved. No applicable AGENTS.md was found. Neither N0
census nor completed GPU panels were rerun. Saved-data reconstruction is distinct
from the old census execution. No192-request N1 or N2 runner was launched.

This work asks whether exact canonical-token LCP retention, tail trim and suffix
recomputation can preserve full reference outputs and active state. The CPU work
prepares that question; it does not answer its native numerical part.

## Corrections and unchanged frozen conclusions

The actual independent checker now derives B's replay from the materialized head,
not the length of logical history. The specified positive case
`old=[10,11], materializedHead=1, next=[10,11,12]` replays `[11,12]`, two rows.
The checker imports its separately implemented independent helpers; positive and
negative tests execute those same helpers. Full/partial prefixes and pending/no
pending cases have independently specified expected answers. A fully cached raw
append of zero rows still requires a fresh frontier; C explicitly replays the
last token. No test was changed merely to accept an old wrong output.

Candidate and independent token interfaces now inspect every own index before
copying/comparing. Holes, inherited-index placeholders, undefined, null, negative,
fractional, nonfinite, unsafe and nonnumeric IDs are rejected. Validation examines
the entire input, including IDs after the first mismatch. Once vocabulary is
bound, `0 <= id < n_vocab` is enforced; the native CPU bridge also validates its
JSON integer IDs against the vocabulary actually loaded from the exact GGUF.

19 candidate tests,6 independent-helper tests and8,960 geometry cases pass.
Two independent saved-data replays each pass118,207 checks. FREEZE, REPORT,
PER_ROOT and TURN_COMPARISON are byte-identical to the four PR225 artifacts.
All1,127 original later turns failed the full-prefix test, so the faulty positive
B branch was not exercised by that census. Its correction changes no denominator,
token vector, geometry result or prior negative conclusion. See CPU_FIX_REPORT,
CPU_FIX_EVIDENCE and SAVED_COMPARISON_IDENTICAL; old code/data are not overwritten.

## Actual producer components versus observations

The producer preparation builds the fixed upstream common/minja/parser code for
CPU only and calls actual runtime serialization components with the exact GGUF
vocabulary/template, instead of substituting a hand-written parser. All GPU
backends are disabled; no model tensor execution or llama_context is created.
The exact source/build/wrapper epochs, flags, binary identity, raw receipts and
failure explanations are bound by the producer evidence.

The template-engine check renders all1,645 saved canonical prompts and compares
**bytes** with the saved Jinja inputs. All match. It does not retokenize or rerun
the identity-matching N0 census. Four frozen provided-body cases additionally
exercise actual token pieces, parser initialization, message construction, next
template and tokenization. Boundary fixtures exercise EOG/cap, empty thinking,
special pieces and invalid input. A final wire-response route is necessary:
actual server result formatting and safe JSON serialization, followed by client
history parsing, can differ from directly serializing an intermediate parser
message. Earlier ABI/UTF8/fallback wrapper epochs are retained as preparation
failures; none is represented as a model or server performance failure.

These are genuine CPU calls on **provided or scripted IDs**, not sampled model
responses, teacher-forced native execution or observed free generation. Exact
fixture results, stop/profile restrictions and remaining unsupported paths are
reported by the producer materials. Source evidence of server EOG/cap handling
does not certify a new native sampler/context. The original N worker still lacks
the required source-bound multi-turn adapter and independent C4096 R.

## Four exposed development episodes

The original four N0 development episodes are unchanged and all predicted no
partition difference. New N1a coverage therefore has a separately frozen rule:
within each root choose one two-user-turn-capable leaf by source-only hash,
**before** consulting geometry; keep its first two user messages exactly. Do not
replace an incompatible chosen path. Then select two roots by root hash in each
of the explicitly requested predicted-difference/no-difference strata.

All518 roots remain in the denominator:218 lack a two-user path,145 fixed paths
fail the necessary supplied-history cap/stop diagnostic, and155 remain:4 predicted
difference/151 no difference. The frozen2+2 episodes predict later `(head,append)`
of `(23,516)`, `(104,172)`, `(88,128)`, `(59,94)`. No offset, padding, template,
latency or acceptance is searched or altered. Independent raw-tree selection
review passes27,386 checks. See episodes/ and the independent selection review.

This is geometry-stratified **development coverage**, not a representative cohort
or frequency estimate. The user texts are fixed public source continuations; a
future R generates its own assistant responses. Actual free heads, stopping and
partitions are unknown and cannot trigger reselection. Provided-body eligibility
does not establish future native/free eligibility. No unfavorable source row is
deleted from the complete source accounting.

## Minimal native proposal and reference conflict gate

Read REFERENCE_CONTRACT.md and PLAN_REVIEW.md. The fixed order is resident R,
independent repeated R, cold canonical oracle, then strong whole-rechunk+loop4.
Each path keeps one context allocation across an episode; resident paths preserve
their own true state between turns. The cold oracle clears KV each turn and
computes its own full canonical input, never restoring resident captures. It is
a separately charged input replay, not a resident free episode.

R repeatability is insufficient: resident/cold exact canonical input and temporal
state alignments must be valid before numerical comparison. At POST_RECONCILE,
only aligned active KV is comparable because resident frontier is invalid and cold
prefix frontier may be fresh. After the common suffix, compare full requested
vectors and all active KV/frontier/pending. An ineligible semantic alignment is
CONTRACT_CONFLICT, not a numeric pass/failure. An eligible strict difference stops
the study with its first raw coordinate. No reference switching, argmax shortcut,
tolerance relaxation or timing continuation is allowed.

There are32 natural/input-oracle turn requests and40 explicitly scripted token
control requests: five2-request fixtures across four paths. Splitting trim
unavailable and injected pre-mutation failure gives five controls, rather than
hiding both behind one nominal case. Setup, continuation, oracle, output ownership
and zero-forward reset are specified. The raw-token controls do not claim to be
canonical natural chats or actual greedy/EOG observations.

The proposal has72 planned/76 maximum requests, with four consumption-reserve
slots and no automatic retry or quota transfer. Tight row reservations total69,354
planned/85,738 including reserve: fixed first prompts plus cap, C4096-limited
unknown continuations, and626 exact control rows. The suggested60/245,760 was an
estimate, not authority or a manifest to force the experiment into. Ten deployment
placements (two probes plus eight workers) are separately proposed and unapproved.
See the machine-readable operation graph and exact per-fixture instructions.

## Raw evidence, resources and Go/No-Go

The streamed comparator reads complete raw F16/F32 values, checks metadata and
coordinates, and preserves first differences, retained-prefix bytes and owned
output transition evidence. Matching hashes are transport checks, never a numeric
pass. Synthetic tests include nonargmax differences, all-layer/head KV tails,
nonfinite values, bad transport, holes, mode/path substitution and ownership
provenance. CPU tests do not establish a truthful native capture writer, complete
execution coverage or retained live contexts.

The conditional capture profile uses three active-prefix snapshots, complete
requested output rows and bounded streaming; reset has zero active bytes. It
requires at most144,202,735,616 raw bytes and551,473,155,769 bytes including archive,
strict restore, build/header and100GiB protected reserve. This replaces the larger
unexecuted N1 profile; no old data is deleted. The writer/profile bounds must still
be proven. Proposed one-worker RSS24GiB plus24GiB system reserve and2GiB free VRAM
are caps, not measurements; enforcement is not established by a JSON field.

The5-hour window is a watchdog envelope, not a measured completion forecast:
bounded initialization/placement/native workers, checks, comparisons, export and
strict readback are all included. Current OS snapshot is not GPU allocation or a
quiet window. No UUID or absolute start/end/last-worker deadline is approved.

**Go:** CPU bug fixes and bounded test/fixture planning. **No-Go for GPU:** native
R/adapter/modules/writer and independently bound execution receipts remain absent;
finite request/row/placement approval, effective resource enforcement and a current
quiet allocation are missing. No N1a numeric pass/failure is claimed. Native EOG,
capacity extremes, remaining lifecycle cases and four arms require N1b. N2 needs
a separate new-root, episode-paired service protocol only after qualification and
an attributable real execution difference; no5% target or sample expansion.

The paper may describe the corrected CPU checks, unchanged supplied-history
negative result and source-bound serialization fixtures. It may not claim native
resident/cold equivalence, active-KV qualification, LOCAL's unique advantage or
natural service speed. A real producer path benefits all LCP-capable strong arms;
shared cache reuse is never attributed to LOCAL.

The final plan tests pass30/30 and independent challenges pass14/14. The required
261-check graph is162 aligned-state pairs,27 resident-only prefix-retention,
36 ownership and36 individual reset checks. It does not claim cold retention.

The public evidence packet, reproduction instructions, accounting and final
readback receipt record actual execution and publication separately. No model
forward, GPU context or placement was run. No model task is queued. No merge,
Release, paper/baseline edit, rental, second card or data deletion occurred.
