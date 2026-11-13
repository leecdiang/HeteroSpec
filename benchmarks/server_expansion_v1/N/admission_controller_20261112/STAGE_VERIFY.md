# Python staged provided-byte verifier — CPU only

`StageVerifier(repo_root, capture_root, manifest)` reads files only. It imports no
native library and invokes no executable, tokenizer, producer, model, context,
placement or GPU API. The original A5000 host has Python3.10 but no Node in its
PATH; this separately named port keeps the frozen PR226 contracts unchanged.
The parent controller still has a permanently closed native admission boundary.

The source pins the full bytes of `N1A_PROPOSAL_NOT_ADMITTED.json`,
`REQUIRED_COVERAGE.json` and the original exact-token `NATIVE_JOB_TEMPLATE.json`.
It derives check IDs from that graph rather than accepting a chosen pair list.
Old sources and data are never rewritten.

| `verify(stage)` | Exact checks in this stage | Completed-role-prefix inventory |
| --- | --- | --- |
| `RESIDENT_R` / `R` | 27 self checks | 63 states, 18 owned events, 8 producer receipts, 2 contexts |
| `REPEAT_RESIDENT_R` / `REPEAT` | 27 self + 54 aligned = 81 | 126 states, 36 events, 16 producer receipts, 4 contexts |
| `COLD_CANONICAL_ORACLE` / `COLD` | 18 self + 54 aligned = 72 | 189 states, 54 events, 16 producer receipts, 6 contexts |
| `STRONG_WHOLE_RECHUNK_LOOP4` / `STRONG` | 27 self + 54 aligned = 81 | 252 states, 72 events, 24 producer receipts, 8 contexts |

These disjoint lists cover the original 261 IDs. Cold has no prior-KV retention
or own producer receipt. No future-role capture is permitted in an earlier
stage. A stage verifies all required already completed worker files, not an
arbitrary caller-supplied partial manifest.

The admission manifest must independently bind `run_id`, `stage_check_ids`
(keyed by the full role names), and `worker_bindings`. The latter is keyed by
`ROLE/NATURAL` and `ROLE/CONTROL`; each value contains `source_sha256`,
`executable_sha256`, `writer_sha256` and the complete `identity` object with
contract/model/tokenizer/template/producer digests. Absent bindings BLOCK the
verifier. Source identities are not inferred from the captures themselves.
The constructor deep-copies this manifest and binds its normalized digest;
verification and seal replay reject any mutation of that internal binding.
Changing the caller's original dictionary cannot change the verifier's inputs.

Inventory rejects unplanned, duplicate, partial, symlinked, uncertain or poisoned
files; it never chooses a favorable duplicate. It binds deterministic actual
writer filenames, COMPLETE/pending/snapshot bytes, full tensor descriptors,
eight distinct resident worker contexts and same-run identity. Control token
inputs and forced terminal IDs are checked against their unchanged exact frozen
fixtures. All provided active F16/F32 scalars are streamed and checked finite.
Every raw digest is re-read; hashes only check transport, not numerical equality.

Comparisons read every declared scalar bit with no tolerance, including signed
zero. They check complete requested vocabulary rows, all active KV positions,
logical/materialized/pending/stop state and output ownership. Prefix retention
uses each old and new head's own tensor stride. An actual failed native trim
cannot become an automatic rebuild. Ownership compares the actual source's last
requested row to the before copy and compares before/after around a bound,
ordered, positive-decode mutation receipt. Reset requires actual zero-length
raw files. Only at POST_RECONCILE are the freshly computed cold frontier and the
invalidated resident frontier deliberately excluded from numerical comparison;
their aligned active KV still undergoes full comparison.

File reads use component-wise openat/O_NOFOLLOW, bounded buffers, transport SHA
and pre/post descriptor plus linked-path device/inode/size/mtime checks. A file
changing between a retained-prefix transport check and comparison blocks, even
if compared bytes would otherwise match. A successful result includes the
relative `capture_file_sha256` map. The controller must durably seal it and call
`verify_sealed(files)` before every later worker and before every later stage
verification. Sealing permits additional future files but rejects any changed,
missing, unsafe or oversized old entry. A changing whole-root digest alone
cannot express this subset rule. The controlled writer's exclusive creation
and directory bounds are complementary protections.

Results have `status` PASS/FAIL/BLOCKED/NOT_RUN, exact IDs, per-check results and
the first difference. A failure stops at its first check; unperformed checks
remain NOT_RUN. A PASS always has `scope=PROVISIONAL_PROVIDED_BYTES_ONLY`,
`native_qualified=false` and `admission_authorized=false`. It cannot establish
that headers or work receipts truthfully came from native execution. A JSON
report is never permission to launch a model. R's 27 self checks alone do not
prove reference arithmetic repeatability; the repeat and cold stages remain
separate required gates.

Only after R's complete 27-check provided-file pass, the report contains the 18
`reference_inputs` entries extracted from those same inventoried POST_RECONCILE
and TERMINAL snapshots: canonical IDs, actual declared retained head, emitted
IDs, stop/cap and immutable snapshot descriptors. The controller must persist
this mapping independently before preparing any later-role job. Repeat/strong
use it as an assertion and cold as its independently recomputed input; it is not
a forced live-generation tape. Its scope is explicitly
`PROVIDED_R_SELF_NOT_COLD_EQUIVALENCE`, not permission or a cold-arithmetic pass.

CPU tests use artificial files and fake source identities only. The full-prefix
fixtures are intentionally zero tensors, not producer/sampling/model output;
their PASS tests the consumer, not N1a. Ordinary unit temporary directories are
cleaned by unittest. Retained differential cases are explicitly artificial and
are stored separately with source-bound logs. Public receipts identify the exact
source epoch tested; a later source change requires its own receipt.

The final differential replay in audit/DIFFERENTIAL_FINAL_01.json compares the
unchanged Node checker with Python on twelve retained artificial cases. All
twelve agree on decisions, compared byte/scalar counts, first raw coordinates
and hex, ownership-source byte counts and reset file evidence. Diagnostic reason
wording, decoded-value formatting and maximum absolute difference are not used
as parity criteria. The first replay exposed two omitted diagnostic fields;
audit/DIFFERENTIAL_INITIAL_01.json preserves that mismatch and its correction.

The expanded integration test appends one artificial role at a time and runs
R27 → repeat81 → cold72 → strong81, rechecking earlier sealed entries before
advancing and asserting the exact disjoint 261-ID union. This is CPU consumer
coverage only, not 261 native passes. Streaming the complete synthetic vectors
and KV takes several minutes even though no model is run.

Reproduce on Linux with Python3.10+ from the repository root:

```
python3 -m unittest discover -s benchmarks/server_expansion_v1/N/admission_controller_20261112 -p test_stage_verify.py -v
```

To export small retained synthetic cases for the unchanged Node comparator:

```
python3 benchmarks/server_expansion_v1/N/admission_controller_20261112/differential_fixture.py --out /absolute/fresh/CPU_DIFFERENTIAL_FIXTURES
```

No native capture set currently exists. Actual loaded identity, real producer
continuation, reference repeat/cold arithmetic, actual retained KV and all 261
native checks remain NOT_RUN; a live approved controller/preflight and separate
finite GPU authorization are still required.
