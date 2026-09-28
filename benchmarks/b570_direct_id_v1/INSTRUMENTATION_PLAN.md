# B570 direct-generated-ID replication: observational instrumentation plan

Starting main: `483c4cbd6cd72ae1cdcdbba4534a62fc1786f885`.

This is a prospectively frozen direct-ID replication with known historical
re-tokenized-text agreement counts (fast 45/90; serialized 60/90). It does not
reopen the historical B570 campaign or provide a blinded discovery.

The only candidate paths are TARGET_REFERENCE, B570_FAST_K2 and
B570_SERIALIZED_K2. Only speculative n_ubatch differs between the two candidate
paths (128 versus 1). No energy collection is part of this study.

## Instrumentation boundary

Use upstream llama.cpp `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, b10839.
The historical completion and speculative frontend sources were verified
byte-identical to the upstream commit archive before instrumentation.

Add an in-memory ordered record immediately after completion samples and accepts
a generated token, and after speculative verification commits its final token.
Do not observe prompt tokens or uncommitted draft candidates. Record the runtime
EOG predicate with each committed ID. Write one JSON sidecar after generation,
using the HETEROSPEC_DIRECT_ID_PATH environment variable. Each execution uses a
fresh process and a unique sidecar. Preserve the entire emitted ID stream even
if the original speculative frontend finishes a verification block beyond its
CLI budget. R0 must resolve the common semantic 128-token contract explicitly
before formal freeze; no text retokenization may establish correctness.

The patch must not change sampling, logits, model placement, KV/cache logic,
verification, acceptance, batching, output, or stop conditions. Auxiliary R0
checks compare original and instrumented stdout bytes for six fixed sanity
prompts and all three paths, record all IDs, and test output cap, EOG termination,
and fresh-process state isolation. R0 is excluded from formal inference.

## Freeze and interpretation

After R0, freeze complete commands, patch hash, binaries/dependencies, driver,
models/dataset, schedule seed, and runner/validator hashes in a committed
protocol. Formal study: 30 frozen prompts x 3 repetitions x 3 conditions = 270
executions and 180 direct-ID pairs. Run through mismatches. A path qualifies
only at 90/90 exact pairs. Any semantic repair after freeze invalidates the
attempt and requires a new protocol version.

Use independent analysis and a portable hash-verified evidence bundle under
artifacts/b570_direct_id_v1/. Preserve all historical materials unchanged.
Open a draft PR; no manuscript, Figure 3, historical CSV, or automatic merge.
