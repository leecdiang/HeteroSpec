# History serialization successor: partial canonical cache reuse, no native qualification

This independent successor starts at PR224 head
`8be5f9acf3139356ecd95f065964373c7c83ffde`. PR200 remains at
`fb56140a4aa33ba4eca24af680c5a0d844563b96`; both latest discussion timelines
were empty when checked on 2026-11-12. No applicable AGENTS.md was found in the
checkout or its ancestors. The original protocol, shared coordination/adapter,
PR224 README, NATIVE_HANDOFF, PREFIX_FIRST_DIFFERENCE, STATUS and public readback
were read. Original source, STATE, reference, negative data and ledgers are unchanged.
There is no duplicate N native job to resume. No completed205/206/208/218 work was
rerun; RTX223 and new kernels are outside this study.

**Executed:** read-only source/identity audit, pure CPU contract tests and a
saved-token comparison with independent reconstruction. **Not executed:** new
tokenization, N0 rerun, model forward, native adapter, model/GPU context, placement,
teacher-forced native replay, free generation, N1/N2 or performance measurement.

## The producer finding

The current HeteroSpec worker keeps model/context allocations but resets KV for
each complete pretokenized request. It has no implemented natural conversation
producer. The original reference also hard-rejects C4096. These are engineering
gaps, not numerical failures or evidence that resident service is impossible.

Pinned upstream llama.cpp source provides two different real mechanisms:

* Legacy completion retains actual generated IDs/KV and appends a newly formatted
  message suffix. Its inspected helper defaults thinking=true; it does not match
  the fixed nonthinking N0 flags or prove token-equivalence to canonical history.
* Modern CLI posts full parsed message history; the server renders the whole
  prompt, keeps a token longest common prefix and removes the changed KV suffix.
  This supports a canonical-token repair proposal. It is not deployed or qualified
  HeteroSpec N behavior. A JSON history does not itself imply KV is discarded.

[CONTRACTS.md](CONTRACTS.md) traces output, history, next input, pending tokens and
frontier ownership. [The source audit](evidence/SOURCE_STATUS.md) binds17 source
objects,58 exact fragments,4 existing ELF/BUILD identities and direct fixed-version
links. Hashing ELFs as data did not execute them. The official upstream raw bytes
were not independently re-downloaded; full cached-source and excerpt digests are
clearly distinguished. Do not promote source existence or defaults to deployment.

## Complete saved-token comparison

Exactly the original OASST1 validation subset is reused:4,401 messages,518 roots,
2,241 paths and1,645 unique user turns (518 initial/1,127 later). Original raw
messages, saved actual-tokenizer outputs, model/template identity and all original
rows remain bound. No favorable template, offset, padding, speed, acceptance or
sample search was performed. All heads below are hypothetical supplied-history
predictions, not actual native heads or true free-generated histories.

| Quantity | All supplied histories | Necessary cap/stop-compatible diagnostic |
|---|---:|---:|
| Turns, including initial |1,645|1,029|
| Later turns |1,127|511|
| A full old-history prefix retained |0|0|
| B append-only, same canonical input compatible later turns |0|0|
| C later turns with nonempty partial prefix |1,127|511|
| C exact canonical token reconstructions |1,645|1,029|
| Different strong-rechunk/LOCAL outer partitions |512|38|
| Roots with a partition difference |212|27|
| Strong whole-rechunk calls / LOCAL outer calls |9,644 /9,373|2,909 /2,889|
| LOCAL inner attention groups |10,054|2,946|
| Canonical rebuild rows / C suffix rows |399,786 /274,923|103,636 /77,473|

A is the frozen canonical supplied-history/full-common-rebuild negative control;
its old result was read, not recomputed or rewritten. All1,127 full-prefix failures
still begin at the previous four-token empty-think suffix. Keeping that suffix for
B changes the next canonical input and cannot establish unchanged reference results.

C is a **new, source-supported but unimplemented policy**: keep at most the
materialized token LCP, trim the old suffix and replay the exact new canonical
suffix. Shared fallback is full canonical reset/rebuild. A fully cached input must
still refresh one token's output. Every CPU reconstruction equals the original
canonical token vector; no numerical or KV equality follows from that fact.

616 supplied-history turns fail even necessary prior-body-plus-EOG/cap128
compatibility. The original body-only flag was614; the two boundary omissions were
already disclosed in PR224 and remain preserved. The1,029-turn diagnostic retains
518 initial and511 later turns; it is not a selected replacement cohort. Supplied
length/EOG compatibility is still insufficient to establish greedy compatibility.
The complete raw denominator remains primary.

The more relevant diagnostic leaves38 distinct turns in27 roots and only20 extra
whole-rechunk outer calls. All predicted per-token padded attention work is equal;
LOCAL has more inner attention groups. Common cache reuse saves predicted replay
rows for **all** C arms; it is not a LOCAL benefit. Counts are not kernel dispatches,
actual rows executed, service timings, confidence intervals or speedups. Branches
share roots. There are zero observed native/free histories, not an estimated zero
real-world compatibility rate.

## Decision and paper-facing scope

Narrow the question to whether a source-backed canonical LCP/trim integration can
preserve full reference/state semantics and whether the remaining graph grouping
matters. There is no basis for a large GPU timing panel, a natural multi-round
speedup claim or a universal claim that LOCAL has no value. The narrow geometric
difference permits an optional engineering qualification design, not admission.

[N1_DESIGN_NOT_ADMITTED.md](N1_DESIGN_NOT_ADMITTED.md) proposes one free sequential
producer, four equal strong arms, an independent C4096 R, separately accounted
semantic replay and controls. It has no executable native runner and does not spend
the old256 proposal,3072/12M historical cap or S3 allowance. Its192-request ceiling,
rows,3 separate placement actions and complete capture/closeout estimate are new,
unapproved proposals. Current disk/RAM observations do not satisfy its conservative
resource gate; producer/code/build/fixtures and explicit approval are also missing.
N2 and a timing budget are not proposed here.

The paper may report the fixed canonical-prefix obstacle, the existence of an
upstream partial-repair mechanism and this descriptive supplied-token geometry,
with the stated scope. It may not claim deployed N support, canonical B equivalence,
numerical/active-KV qualification, measured free history, natural service gains,
LOCAL-specific cache savings or a reproduction of RTX kernels. No paper was edited.

## Reproduction and delivery

17 CPU tests passed, including8,960 ordered-geometry cases and terminal/trim/capacity/
pending/ownership invariants. The standalone independent implementation passed
118,207 checks, reconstructing raw ancestry, all1,645 canonical vectors, every
ordered group,518 root aggregates, first differences and immutable hashes. It
imports neither the comparison nor its contract/geometry implementation.

The reviewed text packet contains every new per-turn prediction, independent raw
replay and exact source fragment. The unchanged PR224 packet separately supplies
all original messages/tokenizer IDs; weights/ELFs are external identities and are
not needed for saved-data replay. No native numeric captures exist for this study.
See REPRODUCE.md, PACKET.json and PUBLIC_READBACK.json for byte identities and the
actual scope of anonymous immutable public verification. CPU replay is not a GPU
rerun or an independent validation of model weight bytes.

ACCOUNTING.json records zero new GPU requests/rows/actions and unchanged old ledger
identities. CPU total wall time and full network/read byte costs were not metered;
no preparation cost is represented as model latency. STATUS.json and HANDOVER.md
give the terminal checkpoint and missing admission items. No merge, Release,
baseline change, data deletion, rental or second GPU was performed.
