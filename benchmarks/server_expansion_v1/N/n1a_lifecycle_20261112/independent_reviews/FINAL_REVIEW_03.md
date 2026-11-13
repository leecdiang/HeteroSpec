# Final independent N1a CPU review, revision 03

`FINAL_REVIEW_03/FINAL_REVIEW_03.json` passes all 14 independent synthetic test groups against the final source hashes recorded below. The older reviews remain preserved. Their 311,296-row conservative figure and missing-coverage observation are historical; the current proposal has a tighter row reservation and a required-coverage validator.

Current accounting is **72 planned requests plus four consumption-reserve requests, 69,354 planned decoded rows plus 16,384 reserve rows, at most 85,738 rows, and ten placement actions**. No automatic retry or quota transfer is allowed. Independent replay of saved first-prompt token IDs verifies the bound counts 92, 63, 27 and 108 and their exact ID hashes. Four paths contribute 68,728 natural-session rows; direct arithmetic on the five concrete scripted controls contributes 626 rows. This agrees with the tighter reservation without using the manifest's declared row totals as the calculation source.

The exact required graph contains **261 checks: 162 aligned-state pairs, 27 resident prefix-retention transitions, 36 ownership transitions and 36 individual empty-reset checks**. Independent reconstruction matches every required ID, scope, operation and phase binding. Cold-oracle sessions contribute no prefix-retention checks: their fresh q1 prefix is compared to R at the aligned phases, while resident retention compares prior TERMINAL to next POST_RECONCILE in the same context. Fresh empty cold construction and actual work still require truthful native writer/work receipts.

The independent challenges reject missing, duplicate, relabeled and cross-path comparison bindings, and missing, duplicate and cross-pair result records. Forged native/admission labels in a supplied result cannot grant authorization; the returned status remains provided-bytes/receipts only, and a proposal with native execution enabled is rejected. The comparator's full-byte, finite-value, tail-vocabulary, final-KV-coordinate, transport-integrity and post-reconcile KV-only tests continue to pass. An unbound ownership string cannot establish ownership. The new RESET check requires actual zero-length files and empty metadata rather than a numerical self-pair.

The path order is R, repeat R, cold canonical oracle, then the strong whole-rechunk candidate. Every preceding path must complete its 18 requests and full qualification before the next path starts. In particular, the candidate cannot begin before the cold canonical bridge passes. All current gates remain preparation only; none was exercised on a native R context here.

The complete-binding validator closes the earlier missing-pair preparation gap. It does not prove that receipts are truthful, a native context persisted, a cold oracle genuinely rebuilt from empty state, or a GPU request executed. Those remain native implementation/integration and admission requirements. Storage remains a conservative capacity-based capture bound: 551,473,155,769 bytes (about 513.60 GiB) available space including raw captures, archive, restoration, build/text allowance and protected space. It is not an observation of current resources.

The prior episode-selection review remains applicable: two predicted-difference and two predicted-no-difference roots provide deliberate development coverage, not a representative cohort; actual free-generation outputs and heads remain unobserved. No N0 retokenization, tokenizer invocation, model forward, native context, GPU context or placement action occurred in this review.

Final reviewed code identities:

| File | SHA-256 |
|---|---|
| `raw_compare.js` | `561fc44696b6ba9993033798035e1b6670832fce497219388ed845f4b4d6265b` |
| `manifest.js` | `352ec0ec31e6a08e78af09105253fc6dff2ddb954b8e619d186ba7bf47d3d5de` |
| `control_fixtures.js` | `9e2e74cb634adb4faec8d7a2dbfbf664f008c76f5f7c20cadfb0751389dede3e` |
| `coverage.js` | `6ce67475d0636daa9a7d9d66ec7b4f8f2f39fb80bb76b7ec86dcbfb210864d2b` |

`final_check_03.js` reproduces this review using an explicit plan directory, frozen episode JSON, fresh output directory and saved N0 directory. Its synthetic complete-binding manifest is never presented as actual native capture data.
