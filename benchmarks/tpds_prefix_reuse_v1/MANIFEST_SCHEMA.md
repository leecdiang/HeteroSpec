# Input and normalized-result schema

`manifest.json` has `schema_version:1`, `native_tokenization:true`, `corpus_revision`, `tokenizer_sha256`, `template_sha256`, `deployment_id`, `capacity`, `padding`, `qmax:32`, `output_cap:128`, `cache_granule`, `reuse_policy`, `exposure_audit_sha256`, and `rows`.

Each row includes `id` (terminal message), `root_id`, `cached_ids`, `request_ids`, `effective_head`, `physical_head`, `native_dense_verified:true`, `source_sha256`, `history_exposed:false`. The host derives `effective_head` from the actual cache implementation; the utility only accepts the declared simple policy `floor_lcp` or `exact_lcp`. Both complete token arrays use the same native renderer/template. `exact_lcp` requires granule1. Any more complex cache admission policy needs a named, reviewed schema extension; it cannot be forced into these names.

The `floor_lcp` policy explicitly denotes an implemented whole-granule snapshot service, not vLLM/SGLang execution. `exact_lcp` denotes an actually implemented exact-token snapshot service. `effective_head` must equal the selected policy's token-prefix calculation, and the native observed dense physical head must agree. The source message text is never read by the selector. Paths or data without an authenticated corpus and native tokenization remain preparation-only.

`panel.json` is the full deterministic output of `study.py select`: the input manifest hash, deployment, configuration, calibration roots, held-out roots, all normalized metadata and eligibility/rejection summary. One root supplies one retained path. Native output and timing must never be used to edit it.

`results.json` has `schema_version:1`, `stage:"main"`, `deployment_id`, `panel_sha256`, `source_freeze_sha256`, `oracle_sha256`, `selector_sha256`, `records`. Each record has `id`, `root_id`, `session` (0..3), `arm`, `kind` (`warmup` or `measure`), `seconds`, `qualified`, `actual_output_sha256`, `expected_output_sha256`, `source_freeze_sha256`, and `oracle_sha256`. All scalar hashes are exact64hex strings. Full-vector numerical eligibility remains documented in the separate native qualification; `qualified:true` cannot self-certify unseen raw evidence.

The analyzer requires the exact1024 planned slots, positive finite elapsed times, matching frozen source/oracle identities and qualified output hashes for every slot. A failed/incomplete panel returns a nonzero exit and no qualified aggregate. Preserve its original JSON and generate a separate native disposition, not an edited passing file. Full raw-state verification belongs to the host auditor. `panel_sha256` is the canonical JSON hash produced by `study.digest`, not a hash of pretty-print whitespace; native source/runtime hashes are byte hashes.

The examples constructed in `test_study.py` are labeled synthetic and must not be passed off as native scientific data.

## Calibration JSON for selector.py

Use `stage:"calibration"`, the same canonical `panel_sha256`, `deployment_id`, a byte-bound `source_freeze_sha256`, a positive measured `calibration_total_seconds`, and144 records:12 calibration roots x2 sessions x3 fixed arms x(warmup,measure). Each record has id,root_id,session,arm,kind,seconds,qualified,source_freeze_sha256. Reference/observer qualifications and actual cost-window provenance live in the native evidence, not in a fabricated boolean. The fit function rejects held-out IDs, missing rows and zero/unmeasured calibration cost. `lookup_cost_seconds` remains null in the saved policy until the host measures it; the complete primary service clock already includes every actual lookup.
