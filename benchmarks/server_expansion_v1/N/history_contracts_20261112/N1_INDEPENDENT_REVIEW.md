# Optional N1 proposal review — CPU planning only

Status: NOT_ADMITTED. No model, tokenizer, native adapter, context, placement or GPU action was executed by this review. The source-backed C path is an integration question; it is not a deployed HeteroSpec conversation producer. The 38 necessary-cap-compatible distinct supplied-history turns across 27 roots do not establish a useful latency effect. They justify at most lifecycle qualification, not a performance panel.

## Producer and semantics gates

Freeze one FREE_SEQUENTIAL_R producer before native work. Source-only development user turns come from the four previously selected conversations, without using supplied assistant bodies as generated outputs. R and each arm must generate its own greedy response, construct its own next message history using the same frozen codec, and check its prompt IDs against the R expectation; an R tape is an oracle, not a forced candidate output. A mismatch is a failure, not permission to substitute R's token.

The modern upstream server/CLI supplies a real source basis for full JSON messages -> canonical template -> token-LCP trim/replay. Its message/content/reasoning parser, text decode, treatment of EOG/CAP/partial markup, all template flags, effective stop strings, slot/cache policy and capacity behavior must be bound to exact source and fixtures. N0's Jinja3.0.3 pipeline must not be silently called identical to the upstream minja/template implementation. A CPU token-exact producer bridge is a prerequisite; if it cannot be established, either explicitly freeze a distinct producer study or stop. Legacy completion's real incremental-KV machinery does not establish nonthinking canonical-A equivalence.

For C, declare the mismatch rule as the same canonical suffix rebuild for independent R and every candidate: compare complete IDs before mutation, keep at most the materialized matching prefix, trim the tail, invalidate the old frontier, reconcile pending ownership, and decode the exact remaining canonical suffix once. If the trim capability or state is invalid, perform the same full canonical reset/rebuild rule. Frozen A retains its old full-rebuild rule and result. A wholly cached prompt requires a billed last-token replay. A zero-length suffix must not sample stale logits. Prefix token equality alone does not qualify numerical/KV equivalence.

Any native error after work has begun stops the attempt. It must not trigger an unaccounted second decode/full rebuild. A zero-forward capability/trim failure may choose the predeclared single full rebuild if all arms share that policy. Requests and rows consumed before failure remain charged. The 4,096-row ceiling below depends on this one-pass rule.

## Request envelope

| Class | Derivation | Requests | Purpose |
|---|---|---:|---|
| FREE sequential reference | 4 episodes x 2 user turns x 2 independent R runs | 16 | Freeze/repeatability of true resident sequential R |
| FREE candidate qualification | 4 episodes x 2 turns x 4 arms x heavy/clean | 64 | Heavy state/vector qualification and clean semantic/ownership bridge |
| CANONICAL oracle semantic replay | 8 frozen R-produced canonical inputs x 1 independent full-rebuild run | 8 | Exact canonical-rebuild versus resident-trim reference bridge; separate allowance, no free-session or performance pooling |
| CONTROL lifecycle | 8 predeclared fixtures x 2 charged setup/transition turns x (R twice + 4 heavy arms) | 96 | Boundary/state qualification, separate synthetic-control allowance |
| Planned total |  | 184 | Qualification only |
| Failure reserve | Aggregate maximum; not retries or replacement cohort | 8 | Preserve failed consumption and stop/checkpoint |
| Hard ceiling | No class quota transfers or automatic retries | 192 | 786,432 decoded rows at 4,096 rows/request maximum |

R and all four arms keep one context through each two-user-turn episode. They may reset between independent episodes, never use per-turn cold rebuild as a resident reference. Full canonical rebuilds necessitated by the common rule are explicit operations with full costs. Four arms remain whole-rechunk+loop4, whole-rechunk+packed, LOCAL+loop4, LOCAL+packed, with the same legal append and equally optimized state management. All capture/restore/warm/failed model requests belong to the operation manifest; there are no extra uncounted calibration calls.

There are three proposed zero-forward placement actions, separately budgeted and not presently authorized: independent R, loop4 module and packed module. Placement actions may not issue a hidden forward. The current arbitrary 192-request ceiling is a proposed envelope, not authority; the per-operation fixture/source/configuration freeze is still missing. It does not reuse the old 256/3,072-request proposals, the 12M-row ceiling, S3 allowance or any other ledger.

## Eight control categories and gaps

1. A true token-prefix match with a pending CAP token; materialize that pending token exactly once on append.
2. A canonical-template think-stub mismatch requiring LCP suffix rebuild; refresh and own the frontier before any sample.
3. Actual EOG termination and next assistant/user boundary; do not synthesize EOG for CAP. The native receipt must report the actual vocabulary predicate across all six EOG IDs. CPU EOG-ID tests are not evidence that every ID is naturally generated.
4. Predeclared unsupported/failed trim -> common full reset/rebuild. Controlled failure must occur before a second decode and not alter R's sampling semantics.
5. Fully cached/shortened next input and empty tail -> charged last-token replay, never stale frontier.
6. Capacity tail with cap1/cap128 accounting and an overflow rejected before mutation; no context shifting or favorable truncation.
7. Explicit end-of-session reset and next-session empty state, with no leakage of pending/frontier or KV positions.
8. Output vector ownership across the next append/trim/decode: retained copies must not alias mutable native storage.

Each category needs an exact two-operation fixture and expected behavior before approval. If multiple terminal conditions cannot be covered within those fixtures, stop and revise the manifest rather than imply coverage. Controlled fixtures are qualification inputs, not new natural observations or a speed-selected cohort. The cap1 exception is confined to named controls; the natural free producer keeps cap128. The clean bridge checks token/stop/config/context/ownership plus declared boundary snapshots; it must not be represented as all heavy intermediate checks. Exact full vectors, all active per-layer K/V, frontier validity, pending IDs/positions and resets are checked in heavy qualification with predeclared inherited tolerances, never argmax alone.

## Conditional storage bound

This calculation is valid only if a writer audit proves the named capture profile and caps. It is not a measurement of a newly built N writer.

- Actual Qwen8B C4096 F16 K+V: 603,979,776 bytes; assume at most 1 MiB extra per snapshot = 605,028,352 bytes.
- One F32 vocabulary row: 151,936 x 4 = 607,744 bytes.
- Heavy request upper bound: 5 full snapshots + 132 requested full-vector rows + 2 MiB text = 3,107,461,120 bytes.
- Clean request upper bound: 1 full snapshot + 2 persisted boundary rows + 2 MiB text = 608,340,992 bytes. Clean still needs owned transient outputs for every sample; two persisted rows do not mean every row is revalidated as heavy.
- Planned heavy count: 152 (R16 + candidate-heavy32 + oracle8 + control96). With all eight failed requests charged at the heavy maximum, heavy ceiling160; clean32.
- Raw maximum: 516,660,690,944 bytes (481.177765 GiB).
- Archive maximum: ceil(1.02 x raw) + 16 MiB headers = 527,010,681,979 bytes. Freeze at most eight packed payload files per request (1,536 total); store requested vectors contiguously, not one file per row. Header/file-count changes require recalculation. The 16 MiB allowance covers this bounded tar layout; an unspecified archive layout cannot inherit it.
- Full strict restore: another 516,660,690,944 bytes.
- Additional build/text allowance8 GiB and protected remaining free space100 GiB.
- Required free space with all of the above coexisting: **1,676,296,180,859 bytes (1,561.172475 GiB)**.

The OS-only snapshot at 09:17 UTC showed1,682,239,500,288 free bytes. That is only5,943,319,429 bytes (5.535148 GiB) beyond the complete bound including the100GiB protected reserve. This is too narrow to assume prospective admission on a shared changing disk. Re-read before approval/start, establish output-space ownership, prove snapshot serializer/row/file/header bounds, and reserve a known safe archive/restore destination. Do not claim the historical250GiB floor is sufficient; do not delete earlier data. Any observed writer output larger than its cap stops safely. Existing historical disk use is not charged as newly written data but remains physically occupied.

The source metadata estimates model weights8,709,518,112 bytes + KV603,979,776 + reserve32F32 outputs19,447,808 =9,332,945,696 bytes before compute/workspace/driver/embedding/allocator overhead. File bytes are not actual VRAM allocation. Placement must measure and echo actual CPU/GPU location, peak VRAM and safety margin; no admission follows from these sums. The OS RAM-available snapshot60,586,598,400 bytes is likewise not a current allocation or a runtime peak-memory measurement.

## Time and stop contract

Ten hours can be proposed as a hard quiet-window envelope only, not a measured completion forecast. The controller must enforce an absolute wall deadline, an earlier final-worker-start cutoff, bounded per-worker timeouts, explicit per-stage compare/export budgets and sufficient closeout time. A possible cap is17 native workers at15 minutes each (4h15), three placement probes at2 minutes (6m),2h CPU comparisons,2h export/strict readback, and45m resource checks/gaps (total9h6). The last54m is contingency within10h. All of these are proposed watchdogs, not observed performance; timeout means PARTIAL/FAILED and no retry. A worker which cannot finish its declared fixture set in its cap stops at the safe checkpoint and preserves all requests, rows and captures. Build work should finish before the reserved GPU window; if capture comparisons need more than2h or export more than2h, revise the window before running rather than compress checks.

Before approval, bind actual start/end/cutoff/closeout timestamps and one explicitly allocated GPU UUID; all currently remain unset. Obtain a finite per-class request/row/placement allowance, current quiet resources, executable hashes, independent sequential-reference freeze, producer token bridge, capture-profile proof and an exact operation manifest. A second card, teacher-forced performance, free-session performance/N2, repeated cohort expansion and reruns are excluded. If the CPU producer bridge fails or free development states reveal no distinct strong/LOCAL geometry, stop this line and report that negative result; do not choose favorable offsets, templates, roots or accept rates.
