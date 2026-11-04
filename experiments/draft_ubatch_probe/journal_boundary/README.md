# Additive terminal-journal interpretation proposal

This directory is a read-only sidecar proposal for the fixed PR183 native CPU
fixture journals. It does not modify the frozen worker, old fields, old output
artifacts, execution, or stop behavior. It is not a fix to runtime recovery.

`pending: null` in a terminal cycle means **there is no next loop iteration**.
It does not say every emitted output token has been materialized into KV.
For each of the75 recorded fixture cases, the terminal branches are:

- 18 initial stops: final emitted token is outside the logical committed prefix.
- 15 corrections and15 bonuses: final emitted token is likewise unconsumed.
- 27 accepted stops: all emitted tokens are in the logical committed prefix.

These are source-derived logical frontiers, not independent KV measurements.
Token position matters: the same integer token ID can appear elsewhere in KV.
The sidecar uses a positioned `emitted_unconsumed_suffix`, never token membership.
It rebuilds the endpoint from the original decisions/proposals and validates
base, keep, branch and old loop-pending fields. Unknown/inconsistent inputs reject.
An incomplete STARTED attempt remains incomplete and has no inferred frontier.

## Logits and recovery remain unproven

The boundary's logical verification row is `accepted`, not necessarily the
last verification row3. An initial stop's source is the prefill output. Merely
trimming KV does not repair the cached last-logit output. Even where row3 is the
right row, the journal only records argmax decisions, not the full vector.

`source_row_index` identifies a source within the original live decode. It does
not imply that the vector is persisted, valid after another decode/context reset,
or available after process restart. No new checkpoint, restore operation, saved
logits, reader lease or runtime-admission permission is implemented. Every
annotation is explicitly `recovery.status = UNPROVEN` and `resume_authorized =
false`, including records with successful old serialized-state checks.

This adapter intentionally supports only the PR183 fixed-k3 synthetic fixture.
It does not treat all empty-cycle worker records as initial stops: original
PR151 ordinary/no-draft requests can have no speculative cycles but many decoded
outputs. A worker adapter would require explicit draft mode and actual KV bounds,
plus separate handling of persisted vectors and state provenance.

## Use without changing evidence

From the enclosing experiment directory:

```sh
python journal_boundary/test_inspect.py
python journal_boundary/inspect_journal.py \
 --journal evidence/stress-q8-attempts.jsonl \
 --prompt-ids 1,2,3,4,5,6,7 --output /fresh/boundary-sidecar.json
```

Prompt IDs are supplied explicitly, not invented from final keep/base. The
example prompt is from the pinned fixture source, not a production assumption. The journal itself omits the prompt, so binding is explicitly CALLER_SUPPLIED_NOT_VERIFIED_BY_JOURNAL. A different same-length prompt is not distinguishable by these old records; all derived prefixes are conditional on the supplied prompt.
Output uses exclusive creation: existing files, including the input journal,
are never overwritten. Source bytes and each completed source line are hashed.
The9 unit tests check all four legacy journal sets, input immutability,
initial/accepted terminal cases, malformed frontiers/branches/endpoints, partial
attempts, unknown event types and overwrite refusal. This is compatibility and
source-interpretation testing, not a numerical recovery proof.

## Independent native observations, not recovery

`independent_native/` contains the unchanged reviewed probe, generator, runner,
full75-case result and hashes. It adds read-only observations and separate fresh
scalar diagnostic replay to the pinned CPU fixture. Old result fields remain
unchanged. In this stress-Q8 run, the default last logits differ from the retained
prefix in36 cases (21accepted,15correction). The selected frontier row matches
fresh scalar replay in75/75 cases. These facts do not persist that vector or
implement resume. The initial prefill selection uses API row-1; the sidecar
marks its phase as prefill rather than assigning a verification-row index.

All evidence remains cloud CPU, one synthetic model used as both target and
draft, ordinary target ubatch1/output reserve4. No Windows worker, GPU target
contract, trained-model generalization or new performance result is established.
