# N1a CPU contract corrections

This successor copies the #225 CPU contracts, tests, comparison and independent checker into `N/n1a_lifecycle_20261112/`. It does not edit the ancestor source, frozen N0 tokenization, comparison files, results or baseline. All four copied ancestor source files were rehashed and remain unchanged.

The independent checker's B positive branch previously counted append rows from the length of logical history. A logical history may include one pending token that has not been materialized. The corrected real checker imports its pure independent `appendOnlyRepair` helper and counts from the materialized head. For old `[10,11]`, materialized head `1`, next `[10,11,12]`, the exact replay is `[11,12]`, two rows. The helper is directly tested on initial, full-prefix, partial-prefix, pending and no-pending inputs. It never lends B a repaired partial prefix. Fully cached B has zero new append rows but explicitly requires a fresh frontier; independent C instead plans the required trim and final-token replay.

Both the candidate and independent helper now validate every indexed own token property. Sparse arrays, inherited-index placeholders, undefined, null, negative, fractional, nonfinite, nonnumeric and unsafe integer token IDs are rejected. Every token may additionally be bound to `0 <= id < n_vocab`; the saved replay binds the vocabulary metadata at 151,936 entries. Prefix validation checks both full arrays before comparing them, including IDs after the first mismatch. Candidate reconciliation, terminal classification and declared pending IDs use the same bound validation. The producer bridge can use exported `validateTokenIDs(ids,{n_vocab,label})` without creating a context.

Validation completed:

- Candidate contract tests: 19/19, including 8,960 dense geometry cases.
- Actual independent-helper branch tests: 6/6, including independent expected values and candidate cross-checks.
- New independent checker on original frozen comparison: 118,207 checks, zero failures.
- New copied comparison on saved N0 inputs, then new independent checker: 118,207 checks, zero failures.
- Replayed FREEZE, TURN_COMPARISON, REPORT and PER_ROOT are byte-identical to the original four frozen files.

The original 1,127 later supplied-history turns all failed the whole-logical-prefix test, so the defective positive B row-count branch was unexercised. No original geometry, denominator, opportunity count or result changed. Tests use synthetic token IDs or already saved token receipts; they do not retokenize N0 or observe a native producer.

Fresh logs, replay artifacts, identities and evidence are in this run directory. `CPU_FIX_EVIDENCE.json` records final source hashes and `SAVED_COMPARISON_IDENTICAL.json` records output hashes. `INDEPENDENT_OLD_COMPARISON/` and `INDEPENDENT_NEW_COMPARISON/` contain the two independent reports. The standalone checker requires its sibling `independent/token_contracts.js`; both belong in any reproduction packet.

No tokenizer, native adapter, model forward, context creation, placement or GPU action was executed. Passing these CPU checks does not establish native lifecycle, numerical/KV/frontier, producer or performance qualification.
