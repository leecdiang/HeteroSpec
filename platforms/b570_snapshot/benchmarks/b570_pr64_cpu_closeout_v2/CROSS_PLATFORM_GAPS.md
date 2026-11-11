# RTX ordinary-reference cost handoff

Status: **DEFERRED_RTX_RAW_ACCESS**. B570 local known study archive roots and PR62 public catalog were inspected; no identity-bound RTX PR62 archive or complete B raw records were found. Public B_RESULTS contains qualification arrays, derived task ratios, aggregate/repeat results and a records hash, but no four-repeat absolute scalar_reference costs and full request IDs. It cannot reconstruct the missing pairs. No RTX bulk restore or GPU work was initiated.

Exact dependency: PR62 `8dfa60a2492e0639a0774f7bac842273485ca26a`, `benchmarks/rtx_closeout_bcd/`. Expected immutable archive SHA256 `88ff7d52da4815dee11d7232e36b292fd77fe18a414e01aca41e860cdd4cade5`,122395102bytes,10151logical files. Verify archive and internal index before accessing records; do not substitute another campaign's R.

Future CPU executor: use original B_MANIFEST/B_INPUTS/SOURCE_BINDINGS and the exact B records file whose SHA256 is given in public results/B_RESULTS.json. Read task/request ID, condition, repeat1–4, warm flag, input identity, full generated IDs/runtime-EOG/endpoint, absolute generation and whole-request/wall durations, timer units and source/session identity. Retain all failures and duplicates as audit errors. The B session paid384 measured requests (four conditions ×24tasks ×4repeats) plus16 excluded warmups; only qualified costs enter comparisons.

Compute `R_ms / matched_ms`, `R_ms / target_scopes_ms`, `matched_ms / target_scopes_ms`, >1candidate faster. For each timer and task: median of four absolute durations for each condition, divide, then unweighted task GM. Report each task and repeat, direction exceptions, and deterministic task bootstrap (resample the24 task ratios as clustered units, fixed seed and sufficient repetitions; descriptive interval for this exposed finite panel). Include raw/endpoints separately and no timer pooling.

CPU verification command contract for that future executor:

```
sha256(archive) == expected archive hash
sha256(B records bytes) == public B_RESULTS.records_sha256
assert unique(task,condition,repeat); assert full qualified 24*4 per included condition
assert warm excluded and source/session/input identities bound
median(per-task costs) -> baseline/candidate -> task GM -> task bootstrap
validate negative fixtures: missing repeat, duplicate key, inverted speed, unqualified cost
```

This is an explicit calculation specification, not a claimed executed RTX command or a hidden request for another GPU campaign. Public1.1692379705484377generation/1.035071366196948whole refers to **matched_target / target_scopes** elapsed time despite the historical table's numerator/denominator naming. It must not be upgraded to a win over scalar_reference.

PR62 C4 source boundaries remain separate: diagnostic call/graph counts include warmup; formal drafted/accepted counts come from a different performance session. Never divide across those sessions. No kernel launches are inferred from graph observations. Closing this transfer item later does not reopen B570 GPU work or block this CPU evidence delivery.
