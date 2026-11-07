# Bounded exploratory diagnostics

The full 171-run matrix completed before exploratory selection. The frozen rule selected /15, /25, /18 and /31; no new U2/N1 mismatch or instability took priority. Additional diagnostic generations: 0/12. Existing formal N captures already contain the available detailed state witnesses; repeating the same paths would not provide richer U2 state.

| Path / phase | Observed caller lengths | Callback occupied tokens |
|---|---|---|
| N0 target continuation | 1, 3 | 1, 2 |
| N1 target continuation | 1, 3 | 1 |
| N0/N1 draft continuation | 1, 3 | 1, 2 |
| U2 after first commit | logged batch dumps: 1 | unavailable |

U2's UB2 capacity is not an observation of two occupied graph tokens. Its logger includes caller and split-batch dumps; those counts are distinct from N tensor callback dimensions. For all four selected cases, the first U2 prefill dump spans the complete input (91, 151, 111, 129 tokens respectively), with additional split dumps of sizes 1/2. Grouping was not replaced or forced to match N.

## HumanEval/15

N0/N1 lengths: 25 / 28; endpoints: EOS / EOS. U2=N1: True. Original first-pending source KV equality: True; full pending-logit equality: True. These are captured live initial states, not a new prefill of a later shared prefix.

First divergence: zero-based index 15, IDs 9147 / 4199.

| Condition | Selected ID | Top 1 (score) | Top 2 (score) | Caller length / UB | Positions / logits index |
|---|---:|---|---|---|---|
| N0 | 9147 | 9147 (50.415562) | 4199 (50.238899) | 3 / 2 | [103, 104, 105] / 2 |
| N1 | 4199 | 4199 (50.456791) | 9147 (50.248737) | 3 / 1 | [103, 104, 105] / 2 |

Both native paths have the same committed prefix at this sampled decision ordinal. The original caller tokens, positions/masks, actual proposals, rollback endpoints and selected scores remain in DIAGNOSTIC_FACTS.json and raw traces. Full live KV at this later point was not serialized. Speculative lookahead must not be conflated with the committed-prefix state. A correlated score/shape difference is not unique causal identification.

## HumanEval/25

N0/N1 lengths: 75 / 75; endpoints: EOS / EOS. U2=N1: True. Original first-pending source KV equality: True; full pending-logit equality: True. These are captured live initial states, not a new prefill of a later shared prefix.

First divergence: zero-based index 4, IDs 1406 / 271.

| Condition | Selected ID | Top 1 (score) | Top 2 (score) | Caller length / UB | Positions / logits index |
|---|---:|---|---|---|---|
| N0 | 1406 | 1406 (44.883926) | 271 (44.487068) | 3 / 2 | [154, 155, 156] / 0 |
| N1 | 271 | 271 (44.887604) | 1406 (44.698635) | 3 / 1 | [154, 155, 156] / 0 |

Both native paths have the same committed prefix at this sampled decision ordinal. The original caller tokens, positions/masks, actual proposals, rollback endpoints and selected scores remain in DIAGNOSTIC_FACTS.json and raw traces. Full live KV at this later point was not serialized. Speculative lookahead must not be conflated with the committed-prefix state. A correlated score/shape difference is not unique causal identification.

## HumanEval/18

N0/N1 lengths: 69 / 69; endpoints: EOS / EOS. U2=N1: True. Original first-pending source KV equality: True; full pending-logit equality: True. These are captured live initial states, not a new prefill of a later shared prefix.

No divergent committed decision exists. /18 remains different from the old reference; /31 is the unchanged cap-128 control. Equal outputs do not prove equal internal continuation states.

## HumanEval/31

N0/N1 lengths: 128 / 128; endpoints: limit / limit. U2=N1: True. Original first-pending source KV equality: True; full pending-logit equality: True. These are captured live initial states, not a new prefill of a later shared prefix.

No divergent committed decision exists. /18 remains different from the old reference; /31 is the unchanged cap-128 control. Equal outputs do not prove equal internal continuation states.

## Interpretation and unavailable state

N0/N1 preserve initial handoff state while changing observed target continuation capacity/graph shape. The first output divergences associate with different target top candidates. U2's ordinary single-token continuation agrees with N1 at every formal endpoint; shared greedy numerical execution and occupied shape are plausible explanations. Equal outputs cannot establish identical KV, logits, sampler or kernel execution, and accumulated numerical differences remain an alternative.

Unavailable: live U2 KV/logits/sampler/occupied graph tensors; complete serialized KV at the later divergent N decision; opaque sampler bytes. No fresh prefix was presented as an original live state, and no major runtime intervention was built. The 60 recorded uncommitted target samples in 60 native runs are retained independently of committed arrays. Diagnostic records never replace formal arrays or change the denominator.
