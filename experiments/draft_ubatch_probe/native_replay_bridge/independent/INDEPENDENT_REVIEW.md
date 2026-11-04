# Independent review: native CPU capture and fresh replay bridge

## Conclusion

No remaining blocker was found for the stated bounded evidence experiment. The final native bridge, parser and controller were inspected, independently rebuilt/re-executed, and challenged with malformed input and real payload mutations. This is not approval of a production transaction, GPU route, historical resident reference, or resumable checkpoint.

The exact reviewed source and script hashes are in REVIEWED_ARTIFACTS.json. Main pins:
- Native bridge: b422e58ff0f4005f0259c811dd1fa12f237c5599a4d7c7c06e194e0b398b61f3.
- Native binary, identical after independent rebuild: 03f803ad1451d537563a51882307ead7fb910a10f90ccede8e38892d2c3233a1.
- Controller: 52674118d0fd8c61f5420443dfa191a3ac3516ce27d0f3b33d6480915acde6ee.
- Parser: ccad8e938f78ed35e7b7f73e048e1531287dad4a8304282b2fad4081602df2e0.
- Offline auditor: 6fd522df4690e0ee718587dd306298addd2b076352e0e85df2264b95d75bf2d1.

## Independent evidence

1. Rebuilt the bridge against the pinned existing CPU libraries. The resulting executable hash exactly matched build-v3. This rebuilt the bridge, not the complete dependency libraries.
2. Re-ran the 16-case matrix with that rebuilt executable and the final controller, plus two cap-9/reject-0 cases. All 18 cases completed across 54 candidate/reference/free processes: 178 full-vector uses, 178 required queries summed per case, and 58 committed target boundaries. Re-auditing every case with Python -O reproduced its report. All outcomes keep qualification false.
3. Independently started one new reference process for every required prefix of the Q8 and F32 reject-0 cases. All 34 full vectors and 10 state-required active K/V captures equaled the corresponding maximal-path observations byte for byte. Thus path reuse matched separate-process, separate-context prefix replay in these observed cases. This is not a general determinism proof.
4. Twelve independent serializer sentinels cover 1/2/3/7/17/128 tokens and both V layouts. All 512 token/layer/K-or-V rows in the maximum geometry are distinct. Explicit nonfinite and signed-zero raw bits survive extraction; no floating-point arithmetic is performed. Twenty-one malformed headers/layouts/truncations/trailing-data cases reject. A payload bit mutation survives in the extracted bytes.
5. Thirty-one native configuration negatives reject before creating capture output, including unsigned overflow, invalid widths, float/bool integers, invalid token IDs, duplicate jobs/queries, invalid query extents, and forbidden candidate-derived fields in autonomous free input.
6. Twenty-five mutations of actual native evidence reject under Python -O. They include K/V exchange, F16 byte swapping, a changed active bit, a missing token, altered complete vectors including rejected tails, wrong pending/unmaterialized suffix/frontier, shifted positions, wrong producer masks/row indices, missing jobs/queries, a dirty reference origin, and a teacher-forced or altered free trajectory. Payload mutation tests recompute content hashes, so they test byte/semantic comparison rather than merely stale hash detection.
7. Existing output receipts remain byte-for-byte unchanged after a rejected reuse attempt. A new preflight failure receives its own FAILED receipt.

## Defects found and corrected

The initial bridge attempted token text lookup on a vocabulary-NONE model and aborted. That failure remains a failure. The final bridge explicitly supports only the pinned synthetic NONE/128 ID namespace and does not claim tokenizer or natural EOG coverage.

Autonomous free execution originally shared a process/configuration with candidate-derived forced jobs. The final free role uses a third OS process and accepts only prompt/cap/synthetic-stop input. Context requests of 128 were observed as native n_ctx/n_ctx_seq 256; final evidence records both requested and actual geometry.

An unsigned integer conversion accepted 18446744073709551615 as forced_reject_index -1. The final bridge checks unsigned bounds before narrowing. The old binary's accepted input and exact old source are retained separately.

The controller's old exception handler overwrote an existing successful receipt when fresh-directory creation failed. It also omitted receipts for early preflight failures. The final controller records ownership only after successful directory creation, initializes a preflight receipt immediately, and writes failures only in that owned directory. Exact before/after reproductions are retained.

## Source and semantic boundaries

The inspected seq_get_data format is not the GGSQ saved-file container. It contains native magic/sequence, stream and cell metadata, all K layers, then all V layers. It contains positions and sequence IDs, not token IDs or explicit layer labels. Token-to-position identity therefore depends on the separately recorded executed calls and the pinned implementation/model. Supplying different token IDs of the same length to the raw parser intentionally cannot change or authenticate the extracted bytes.

For the admitted no-extension, one-stream, seq-0, two-layer F16 geometry, raw size is 72 + 2060*n bytes and complete active K/V is 2048*n bytes. Transposed V is component-major in the source and is mapped to token/layer/K-then-V/component order without float conversion. Unknown geometry, sparse/reordered positions, other sequences, extensions, trailing data and wrong layouts are outside this admission. The byte-preserving parser is not a general llama state reader.

All reference contexts begin empty and use one whole-prompt, last-output-only caller followed by singleton callers. They preserve the same context/output-capacity settings during a path and capture vectors/state before later suffix execution. There is no reference trimming/backtracking or candidate-KV import. Actual physical capacity 1 plus the pinned implementation establishes the scalar microbatch inference; this is not independent instrumentation of an internal scheduler.

Controlled rejection cases deliberately use extra oracle contexts to choose proposals. They are protocol probes, not native-draft speed or acceptance-rate measurements. Native-draft cases are separately labeled. Synthetic stop positions do not establish natural EOG behavior.

## Limits that remain

- Only cloud CPU, two synthetic untrained dense-Llama models (F32 or Q8_0 weights), two layers, 128 synthetic IDs, one sequence, F16 KV, one thread and disabled flash attention were exercised. No user hardware or GPU was used.
- Target physical ubatch is 1 and output reservation 4; draft ubatch is 1/2/4 and reservation 1. Whole-prompt producer similarity does not reproduce PR151 target ubatch4, output allocation, complete prior history, or resident-reset lifecycle.
- State equality means complete active **target** K/V plus the separately tested semantic frontier and copied logits. It excludes inactive padding, complete draft state, graph/allocator/backend state, RNG/sampler state and import/resume behavior. It is not a complete machine-state checkpoint.
- Model/library/executable/source/module hashes are trusted local provenance records. Three parser-related source pins are not the entire transitive library build. Loaded-file hashes, reported traces and binding_complete do not provide hostile-host attestation, race-free TOCTOU guarantees, or complete numerical deployment identity. OS/global allocator effects and observer effects remain outside a universal proof.
- Finite runs and extraction sentinels do not prove arbitrary-value attention, future models, all caller shapes, concurrency, transaction rollback, reader leases, or a safe fast path.

The README provides portable reproduction commands. Results and historical failures are kept distinct; no mismatch or aborted attempt is relabeled successful.
