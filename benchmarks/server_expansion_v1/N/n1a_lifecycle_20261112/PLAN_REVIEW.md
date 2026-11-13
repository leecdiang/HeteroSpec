# N1a lifecycle qualification proposal and CPU raw-state comparison preparation

Status: CPU_PREPARATION_NOT_ADMITTED. These files executed no model forward, native context, GPU query or placement action. They do not implement a native runner or issue permission to run one. N1b, LOCAL/packed comparisons, N2 and performance measurements are excluded from this proposal. Existing N0/PR224/PR225 results, reference sources, STATE, ledgers and failures remain unchanged.

N1a asks whether one real producer can preserve the exact canonical request and reference semantics while retaining a legal resident prefix. It does not ask whether LOCAL is faster. The three necessary comparisons are repeated independent resident R, a cold canonical oracle using the same unmodified reference arithmetic, and strong whole-rechunk+loop4. A token-only check cannot admit any of them.

## Producer and reference contract

The proposed natural producer is the actual pinned modern-server message parser and template renderer, the exact GGUF chat template, enable_thinking=false, greedy generation and unchanged cap128. The full parser/render/effective-stop/cache/slot policy and exact source/binary/tokenizer bindings must be supplied by the genuine CPU producer bridge. N0's Python Jinja output is a saved-token cross-check, not assumed identical to minja. A bridge conflict blocks GPU admission; do not switch templates, parse modes, supplied assistant histories or flags to obtain a prefix match.

The four development episodes are the independently reviewed frozen two predicted-no-difference and two predicted-difference source episodes. Their source rank/leaf selection and all rejected candidates remain recorded. Each contributes its first two user messages. Future R generates its own assistant responses; supplied OASST assistant bodies are not replayed as free output. The predicted stratum does not guarantee the future head or partition. Do not reselect episodes when real generation changes the geometry.

Independent resident R uses the original sequential q1 reference arithmetic in a separately versioned C4096 adapter. The old C1024-only frontend and its results are preserved. It needs a real same-context two-turn lifecycle, actual materialized-head/pending receipts and full state capture; allocating resident buffers while resetting KV on every turn does not satisfy this contract. Repeat R uses a new independent context/worker and the same source user messages. Both R runs and the strong candidate produce their own greedy tokens. Reference outputs are expected values, never forced candidate tokens.

The cold canonical oracle starts with empty sequence KV/pending/frontier for every turn, computes its own q1 state from the exact canonical token IDs produced by R, and never restores R captures. Its q1 operation arithmetic and token order are unchanged. It may stop at the registered retained-prefix position for capture, then continue q1 through the remaining canonical input. This introduces no extra token row or new arithmetic grouping. Model/context allocation may remain within its worker, but the sequence is explicitly empty before each turn; this oracle is not called a resident multi-turn service. Oracle replay has a separate budget and is not pooled as free generation.

At a turn boundary all resident paths compare complete token IDs before mutation, keep at most the actual materialized matching prefix, trim the tail, invalidate the old frontier, reconcile pending exactly once, then decode the exact canonical suffix. A wholly cached next prompt backs up and decodes its final token to obtain a fresh owned frontier. Unsupported trim or the named no-mutation caller failure uses the same full canonical reset/rebuild policy. Unexpected native errors or any error after decoding has begun STOP the attempt; there is no second uncharged forward or automatic retry. Every fallback/reject/failed request and actual row remains in the ledger.

## Mandatory phase order and stop gates

The operation graph is ordered by path, with eight natural and ten scripted-control requests per path:

1. Resident R: all18 requests, source/config identity and independent reference freeze.
2. Repeat resident R: all18 requests; full vectors, active K/V, pending, frontier/ownership and reset must pass against R.
3. Cold canonical oracle: all18 requests; exact input semantics and strict raw vector/KV bridge to resident R must pass.
4. Strong whole-rechunk+loop4: only after the entire cold bridge passes;18 requests, same contract and append, actual ordered native calls recorded.

If the cold bridge first differs, preserve the actual raw bytes, coordinate and ledger, halt, and mark all18 strong-candidate requests unexecuted. A producer/canonical-input/alignment conflict is CONTRACT_CONFLICT, distinct from a numerical byte difference. This gate must not be bypassed because repeated R matched or the final tokens agree. No native stage is presently implemented or approved by this CPU plan.

## Request and row budget

The suggested60 requests cannot cover this complete graph. Five separate controls are required to avoid treating unsupported capability and a failed trim as the same event.

| Class | Requests | Rows reserved |
|---|---:|---:|
| Natural free resident R, repeat R and strong candidate |24|51,546|
| Natural cold canonical oracle |8|17,182|
| Scripted resident controls, all three resident paths |30|444|
| Scripted cold control oracle |10|182|
| Planned total |72|69,354|
| Unallocated failure-consumption ceiling |4|16,384|
| Proposed hard ceiling |76|85,738|

Every model request has a unique ID and charged setup/continuation role in `plan/manifest.js`. No class quota transfer or automatic retry is allowed. Four failure slots are not four extra trials or diagnostics; they do not authorize replacement results. Before any later execution, the approving operation manifest must identify what consumption can use that reserve.

The four first natural prompts contain92,63,27 and108 saved native-tokenizer IDs. Each first-turn allowance is that length+127, including the unchanged maximum128-token response whose final token remains pending. Across four paths these initial turns reserve3,192 rows. Each of the16 later natural requests reserves4,096 rows because the new canonical history and retained head depend on future free R. Capacity admission requires prompt length+127<=4,096 before mutation; an over-cap request is a charged zero-row rejection, never truncated to fit. These tighter initial allowances are conditional on the actual pinned producer CPU bridge matching the exact saved ID hashes; a different first prompt is a contract/budget conflict, not permission to enlarge silently.

Five control setups use13 rows each on four paths:260 rows. Resident continuations use16,16,1,25,25 rows on each of three paths:249 rows. Cold continuations build29,25,13,25,25 rows from empty:117 rows. Controls therefore reserve626 rows. Rows here mean decoded token rows in actual forward calls; physical dispatch/padded work is recorded separately and must not be presented as a measured value from these plans. A changed native accounting metric requires a new bound.

## Concrete raw-token controls

`plan/control_fixtures.js` contains the actual arrays and two operation instructions, using IDs from the saved tokenizer stream. These are SCRIPTED_RAW_TOKEN_CALLER_CONTRACT fixtures, not natural canonical chats or greedy responses. Their forced terminal tokens are non-EOG and remain pending at cap1; zero generated rows are decoded within each cap1 setup/continuation request. All prompt/setup work is charged.

| Control | Setup prompt rows | Resident keep | Resident continuation rows | Cold continuation rows |
|---|---:|---:|---:|---:|
| Pending CAP direct append |13|13|16|29|
| Empty-think LCP suffix rebuild |13|9|16|25|
| Fully cached last-token replay/ownership |13|12|1|13|
| Trim unsupported, common full rebuild |13|0|25|25|
| Caller-injected pre-mutation trim failure, common full rebuild |13|0|25|25|

The pending direct-append control proves a low-level caller lifecycle if qualified. It cannot show that the rewriting nonthinking canonical template naturally produces that direct append. The empty-think case drops the obsolete four-token suffix and old pending ownership; the same body token can appear at a different canonical position and is decoded there exactly once. The failure injection exercises wrapper policy before native mutation; it does not claim arbitrary native faults are safely recoverable. Every session performs an explicit final empty reset checkpoint after both requests, without an extra forward.

## Raw-state capture and CPU comparator

`plan/raw_compare.js` reads full raw files in bounded chunks. SHA-256 checks file transport/provenance; passing requires actual byte comparisons and finite scalar values. Strict bytes are used, with no newly chosen tolerance: signed zero differences fail; identical NaN or infinity also fails. Diagnostics name the first scalar/byte and coordinates, plus full compared-byte counts and numeric differences. F32 vectors contain all151,936 vocabulary elements for every declared sampling position. F16 K/V is extracted in canonical `[layer,kv_head,position,dimension]` order for all36 layers,8KV heads, all active prefix positions and128 dimensions, with explicit little endian and no padded/dead KV counted as active state.

Each request has at most three nonempty-capable snapshots: POST_RECONCILE, POST_APPEND and TERMINAL. A later reset adds an empty metadata/checkpoint with zero active-KV/vector bytes. A terminal sampled token is pending and is never silently counted as decoded KV. Snapshot validation binds exact token IDs, capacity, output masks, pending positions, EOG/cap precedence, full tensor coordinates, source/writer/executable identities and caller-owned vector IDs. Natural, scripted-control and cold-oracle modes remain explicitly separated.

There are four comparison scopes:

- ALIGNED_STATE: repeated R, cold oracle and strong candidate against R. POST_APPEND/TERMINAL require all active K/V and complete requested vocabulary rows. POST_RECONCILE compares only the exact aligned active K/V: resident trim invalidates the old frontier, while cold q1 prefix construction may have a valid new frontier. This scoped exception must never become a logits-equivalence claim.
- PREFIX_RETENTION: previous TERMINAL -> next POST_RECONCILE in the same actual resident context. The checker recomputes LCP/keep/pending policy and compares all retained KV bytes using the original source-head stride, rather than comparing only two final states.
- OWNED_VECTOR_STABILITY: bind exactly the last requested frontier row of the setup TERMINAL snapshot, run/context/operation and ownership ID to before/decode/after receipts. Compare that entire original row to the before-copy and the before-copy to the after-copy, around a recorded positive-row continuation decode. This adds two owned row captures, not two copies of the complete128-row history matrix; all sampling rows remain captured in the terminal matrix. The named test cannot pass using an arbitrary unbound tensor twice.
- RESET_EMPTY_CHECK: empty native-state metadata and zero-length active raw files, without any model request.

A complete future comparison graph needs162 aligned-state pairs (18 operations x3 snapshot phases x3 comparisons),27 same-resident prefix-retention checks (nine two-turn sessions x3 resident paths),36 output-ownership checks and36 individual empty-reset checks. `plan/coverage.js` freezes these261 exact IDs, scopes, operations, phases and source/mutation bindings from the operation manifest. It rejects omissions, duplicates, changed paths/phases/scopes, alternate source captures for the same operation/phase and missing/relabelled results. Its optional raw replay wrapper verifies actual header bindings and the last ownership row before invoking the byte comparator. It does not claim cold contexts retain their prior KV; the nine cold sessions are excluded from PREFIX_RETENTION. Cold fresh-prefix construction still needs truthful native work/empty-start receipts and source audit.

The generic raw comparator reports only its listed provided pairs. The coverage wrapper adds finite completeness of provided bindings/raw records, not proof that a writer truthfully captured native memory or any GPU admission. Reset checks verify empty metadata and actual zero-length raw files directly, rather than declaring a self-pair a numerical proof. No actual native raw captures are available in this CPU preparation.

## Placement, RAM, VRAM, storage and bounded window

The proposal registers ten deployment placements: two zero-forward preflight probes (independent R and strong loop4) plus eight native-worker model/context deployments (natural/control workers for each of four paths). There is one native worker/model at a time. Reusing an allocated oracle worker requires clearing its sequence per turn, not recreating an uncounted context. Capture copies, trim, reset and fences are separately logged native actions; no hidden calibration forward is allowed.

Proposed host memory gates are a24GiB per-worker RSS hard cap plus24GiB protected system-available memory, hence48GiB available before admission. Model mmap8,709,518,112 bytes and F16C4096KV603,979,776 bytes do not account for all host workspace; the cap must be measured/enforced, not claimed as predicted usage. The enforcement mechanism remains an admission gap: sampled RSS monitoring or an ineffective RSS limit must not be called a proven hard cap. Capture streams at most one layer/chunk, at most32MiB per GPU-to-CPU copy, without multiple full-KV captures in RAM. The raw comparator uses1MiB chunks. Keep at least2GiB free VRAM; actual placement/peak workspace remains unmeasured and blocks admission.

The conservative conditional storage profile is three active-prefix snapshots per request, each bounded by fullC4096KV603,979,776+1MiB header bytes;132 total F32 vocabulary rows;2MiB text. This is1,897,404,416 bytes/request and144,202,735,616 raw bytes at76 requests. Requested vectors comprise POST_APPEND1 +TERMINAL<=128 +cold-prefix alignment<=1 +ownership copies<=2. The actual writer must prove those bounds and stop if exceeded.

Keep the raw originals, an archive capped at ceil(1.02xraw)+16MiB headers, a full strict restore,8GiB build/text allowance and100GiB protected free space concurrently: **551,473,155,769 bytes** required. At most32 payload files/request (2,432 total) fits the declared16MiB archive-header allowance. This is an upper bound, not a measured writer size; active-prefix extraction often writes less, but that is not presumed. The old250GiB floor and prior1.676TB larger-proposal calculation are not this profile. No historical data may be deleted to obtain space.

A proposed five-hour quiet-window watchdog contains two hours for eight10-minute worker caps, two2-minute probes and30minutes of checks/gaps; one hour for CPU comparison;90minutes for archive and strict readback;30minutes closeout contingency. Bind explicit start/end timestamps and last-worker-start at least10minutes before native-end. The watchdog is not a measured completion estimate. If a worker/comparison/export cannot finish its allowance, stop partial and preserve evidence. CPU builds must finish before the GPU window. GPU UUID, real start/end, approval, runtime peak memory and archive destination remain unset; historical availability is not allocation.

## Go/NoGo and reproducible CPU preparation

Run `node --test plan/test_*.js` for synthetic CPU tests. Create a fresh proposal with `node plan/manifest.js create FOUR_EPISODES.json FRESH_PROPOSAL.json`; validate it with `node plan/manifest.js validate FRESH_PROPOSAL.json`. Freeze the required graph with `node plan/coverage.js expected PROPOSAL.json FRESH_GRAPH.json`. The `--require-admission` switch always rejects: a later independently audited admission/controller implementation is required, and a forged true flag cannot authorize native work here. The generic raw-file replay CLI is `node plan/raw_compare.js CAPTURE_COMPARISONS.json FRESH_REPORT.json`; the complete provided-pair wrapper is `node plan/coverage.js verify PROPOSAL.json CAPTURE_COMPARISONS.json FRESH_REPLAY.json`. Both require actual files and never start a model. Synthetic metadata tests cannot pass actual-header/raw verification without real capture files.

Go requires genuine producer/tokenizer parity, original independent arithmetic and C4096 implementation, exact native operation/placement identity, complete writer/coverage proof, a finite separately approved allowance and current quiet resource window. NoGo includes producer conflict, any strict vector/KV/state difference, wrong pending/reset/ownership, unbounded resource use, missing raw bytes, lost lock or unknown state. Preserve failures and mark unexecuted operations. A negative or blocked N1a does not invalidate old experiments; it narrows the deployability claim. A passing N1a would establish only the limited lifecycle/reference bridge, not LOCAL value or a performance gain.

CPU development failures are retained privately: the first test run had a frozen-array test-harness mutation error and an overbroad frontier-mask comparison; both were corrected. Independent review then prompted dense-array validation, bound ownership-source receipts, exact operation-path/mode checks and explicit placement accounting. No native result is being relabeled by those CPU fixes.
