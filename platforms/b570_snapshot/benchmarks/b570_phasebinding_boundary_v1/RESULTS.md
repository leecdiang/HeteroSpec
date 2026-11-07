# B570 phase-binding, reference-boundary and physical-work result

The admitted PR96 whole-recipe fallback reproduces the complete stock/production output boundary. Native C512 verification remains two occupied width1 micrographs per logical k1 cycle, with separate draft proposal and catch-up work. The immutable post-hoc same-output cost remains negative. Isolated prefill causality and donor-state interaction remain UNRESOLVED.

B570 does not implement RTX query-batch. These findings apply to this frozen actor, not a universal GPU/Vulkan limit or model-answer accuracy.

## Four questions

| Question | Conclusion | Evidence / boundary |
|---|---|---|
| prefill_recipe_causality | UNRESOLVED | UNRESOLVED: occupied target-only continuation is width1 for every arm; capacity, synchronization and scheduler reservation are coupled |
| state_continuation_interaction | UNRESOLVED | Actual state_write_data serializes model architecture plus memory module, sequence state serializes memory only. Logits are separately hash-captured; dynamic output/logit buffers, frontend pending, sampler ownership and scheduler/reservation are not restored by these APIs. Current actor lacks a validated full retained-state fork. |
| physical_geometry_explanation | SUPPORTED | C512 native verify caller2 decomposes into two successful occupied width1 graphs; plus separately counted draft proposal/catchup. Does not quantify fraction of request cost. |
| same_output_negative_request_cost | SUPPORTED | PR92/93 full same-output R_prod/M_match/C_k1, 240 pair requests and 24 tasks; original R_stock failures remain. |

## Execution and immutable provenance

- Started 108 requests: 107 complete, 1 failed; P1=72, P2=35/36 complete; two zero-forward load probes; 110 charged units; zero warmups, retries or donor-fork forwards.
- 21 actual owned native worker lifetimes; 1872.000 owned GPU-process seconds (<18,000).
- Minimum sampled same-PID dedicated headroom: 1,412,370,432 bytes (gate 536,870,912). Native weights and F16 KV placed on Vulkan0. Physical residency remains UNKNOWN; sampled headroom/placement are not continuous residence proof.
- Existing 1,200 paid PR92 counts requests and 50 warmups were not rerun. All 7,379 inherited logical files were restored unchanged and hash-verified.
- Design head: 50047214d4e3f97c992c3f07454e29c13449c95b; PR92: 82946adf946491e6cf7fef761bcc1ec0772e914e; PR93: 57da177c3b63a714d6e6b5e5d7a7dc1f1393e662.
- Prospective execution source seal: f0d4df7aa98b342ccecc5c7b60f14799be085af2, pushed and authenticated by actual GitHub bytes before the first new forward. See F0A.json, F0A_AUTHENTICATED.json, PLAN.json, INPUTS.json and LEDGER.jsonl.
- Original source seal b8b0f4feb1a142b112200a48e9903f4bd1384a66; small raw download-chunk supplement 8bc0d9e8d53af54a967c98c12714349d577565a1. All 306 original capsule files were freshly restored from actual authenticated GitHub bytes before execution.
- A UTC logging exception followed the first successful zero-forward O128 probe, before any request start. The traceback/source/receipt and successful native probe remain under versions/pre-forward-log-amendment/. The correction was separately sealed/authenticated before forward. The completed probe was not replayed; numerical binaries, model inputs, sampler, plan and request slots did not change.
- Initial Hostx86 build failed LNK1101 / incorrect MSPDB140.DLL version. A separate Hostx64 Release build succeeded. Build failures and a counter-hash finishing error remain in versions/, receipts/ and logs. All five numerical DLLs are byte-identical to PR92.

## Whole recipes and complete reference outputs

Clean 2x2 admission: PHASE_FACTOR_NOT_ISOLATABLE. Target-only ordinary UB128/512 and bound UB1 each submit one continuation ID and execute occupied width1. Binding also couples capacity4, synchronization and scheduler reservation; ordinary capacity is1. These are entire recipes, not independent physical continuation treatments.

| Arm | Prefill UB | Continuation UB | Occupied continuation width | Capacity | Path |
|---|---:|---:|---:|---:|---|
| O128 |128|128|1|1|Original stock-compatible ordinary|
| O512 |512|512|1|1|Original production ordinary|
| B128 |128|1|1|4|Existing binding ABI/capacity4 with UB128 prefill|
| B512 |512|1|1|4|Original matched binding path|
| C512 (P2) |512|1|1|4|Original k1 binding candidate + Q4 draft|

Fixed Q6_K target/Q4_K_M draft, greedy sampler, exact prompt token arrays, F16 KV, cap128, logical batch512, context1024, threads10, FA off and old binding ABI. STATE_RECIPE_INVENTORY.md records actual phase ownership, pending consumption, sampler, KV positions, output/graph reservation and synchronization. Binding synchronizes and may reserve scheduler work; capture adds separate observer synchronizations/readbacks. Neither is CPU-only.

P1 repeats are fresh owned-worker counts/capture-off, heavy/capture-on, and heavy plus own same-context same-UB binding no-op. All 24 task/arm complete-output guards pass across three repeats. Controls were prospectively selected by ascending original integer task ID from stable PR92 tasks; the two GSM8K probes are exposed known divergences. No task substitution or fee-based selection occurred.

| Task | O128/O512 first difference | O128=B128 full output | O512=B512 full output | B128/B512 first difference |
|---|---|---|---|---|
|GSM8K/test/1248|index 47: 832 to 220|True|True|index 47: 832 to 220|
|GSM8K/test/831|index 81: 1855 to 1521|True|True|index 81: 1855 to 1521|
|GSM8K/test/196|none (full equality)|True|True|none (full equality)|
|GSM8K/test/435|none (full equality)|True|True|none (full equality)|
|MBPP/3|none (full equality)|True|True|none (full equality)|
|MBPP/8|none (full equality)|True|True|none (full equality)|

Every O128/O512/B512 endpoint reproduces its pinned old own-path complete output. B128 is compared to the entire O128 trajectory. These checks include all native IDs, EOG flags, length, terminal and stop reason; matching only the first differing ID or a cropped suffix is insufficient. Four controls remain invariant, including MBPP EOG and GSM8K CAP boundaries. PHASE_INTERVENTION.json retains all six arm pairs per task, repeats and no-trigger cases.

### Natural boundary diagnostics

| Task / cut | O128 top1 / margin | O512 top1 / margin | Natural prefix equal | FP32 vector hash equal | KV hash equal |
|---|---|---|---|---|---|
|GSM8K/test/1248 / 0|1271 / 3.00305557|1271 / 3.0490303|True|False|False|
|GSM8K/test/1248 / 46|11 / 8.05675507|11 / 8.01761436|True|False|False|
|GSM8K/test/1248 / 47|832 / 0.0107059479|220 / 0.0665149689|True|False|False|
|GSM8K/test/831 / 0|1271 / 3.87666512|1271 / 3.82521057|True|False|False|
|GSM8K/test/831 / 80|315 / 0.487922668|315 / 0.411579132|True|False|False|
|GSM8K/test/831 / 81|1855 / 0.067905426|1521 / 0.0130844116|True|False|False|

Boundary records retain actual consumed IDs/positions, naturally committed prefix, native greedy top1, runner-up ID/logit/margin, current UB/capacity, KV positions/state sizes/digests and source-owned sampler. Equal tokens do not imply equal KV/logits. Bounded witnesses retain top2 values and whole-vector/state digests; full FP32 and serialized KV payloads are absent. Independent verification checks full outputs, pins, finite values and provenance, but cannot independently rehash absent tensors.
Own-binding no-op guards: 72 live same-context full-context and sequence-KV byte comparisons. They are not clone/restore shams. Donor forks and clone/restore shams=0: FORK_NOT_IMPLEMENTABLE. No validated full target/pending/sampler/scheduler/reservation restoration contract exists in this actor. The actual core state_write_data writes architecture plus memory-module state; sequence serialization writes memory state. It does not serialize dynamic logits/output buffers, frontend pending, sampler ownership or scheduler/reservation. Logits are captured separately. Frozen PLAN/F0A wording KV/logits is preserved but corrected here and in SOURCE_SERIALIZATION_SCOPE.json; fork admission is unchanged. Partial KV state was not promoted to full retained-state causality. Prefill-only and state/continuation causes remain UNRESOLVED.

## Physical work, dispatch metadata and actual costs

P2 registered and attempted six exposed inputs x three arms x two capture sessions=36:35 completed,1 API-observer scope failed without replay. New elapsed fields are diagnostic only, excluded from paid prices. Each C512 VERIFY caller submits two IDs at UB1 and executes two successful occupied width1 native micrographs. Native caller IDs, occupied rows, graphs, KV positions, cycle decisions and complete committed arrays are independently reconciled. O512/B512 each execute one occupied width1 graph per ordinary continuation call.

| Domain / arm |Requests|Full output IDs|Acceptance|Target verify rows/output|Target total graphs/output (prefill included)|Draft proposal rows|Draft catch-up rows|
|---|---:|---:|---:|---:|---:|---:|---:|
|GSM8K / O512|8|1024|n/a|0.000000|1.000000|0|0|
|GSM8K / B512|8|1024|n/a|0.000000|1.000000|0|0|
|GSM8K / C512|7|896|86.792%|1.064732|1.072545|477|477|
|MBPP / O512|4|168|n/a|0.000000|1.000000|0|0|
|MBPP / B512|4|168|n/a|0.000000|1.000000|0|0|
|MBPP / C512|4|168|90.698%|1.023810|1.047619|86|86|

One predeclared C512 GSM8K/test/1248 session0 API-dump request failed the sampled log stop threshold and has no complete native endpoint: 28,247 vkCmdDispatch API calls, 84,741 group-count metadata values, 171,281,419 bytes; SHA256 fa873dbc4a22a1b2fda9bbd3450736880e16bdae9ed139160b971c7d06e23352. Loaded layer SHA matches the prospective pin. The raw trace is PARTIAL_FAILED_OBSERVER_SCOPE. Watcher sampled171,123,559 bytes at a134,217,728-byte stop threshold; final file171,281,419 bytes. The0.5-second sampled watcher has an overshoot: the hard byte-size cap was not met and this gate is failed, not PASS. It killed only owned PID24252. No completed counters, output arrays or timing are fabricated for this slot, and it was not replayed. Actual partial CPU API metadata is not GPU completion/kernel timing. The original unstarted23 slots were separately sealed/authenticated at b81e1b1835e3db7ee8ef0cb9ad63503116c9a816, then continued with the original actor/plan. The remaining five session0 candidate inputs used their predeclared separate worker without this layer. All11 completed C512 witnesses preserve complete old own-path output; GSM8K/test/1248 has only its session1 successful witness.

Successful native process_ubatch graph/occupied-row counters are separate from shader kernels, continuous residency and GPU completion. They support the observed extra-work geometry: no two-row physical micrograph amortization plus proposal/catch-up/reconciliation. They do not quantify the fraction of request cost due to draft, binding or GPU stages. No completed non-invasive stage marker was available: MODEL_TIMING_UNAVAILABLE. No coefficients or break-even threshold were fitted.

### Immutable paid same-output costs

Use five-round arm medians per task/session, left/right fee ratio, then average logs across two consecutive sessions and 24 tasks. Each domain has12 tasks and120 paid requests per arm. Full EOG IDs and CAP endpoints are included. Every pair has240 complete equal native outputs. No new formal paid or cross-date interval was added.

| Post-hoc pair |Left fee/right fee|MBPP|GSM8K|Right fee increase|Regressions|
|---|---:|---:|---:|---:|---:|
|R_prod/M_match|0.988099025740|0.980665327544|0.995589073302|1.204%|24/24|
|R_prod/C_k1|0.719263759746|0.695351476866|0.743998356653|39.031%|24/24|
|M_match/C_k1|0.727926797830|0.709060937851|0.747294618437|37.376%|24/24|

Historical C_k1 acceptance is88.8218% MBPP (2940/3310) and87.4847% GSM8K (7130/8150). High acceptance did not reduce measured whole-request fees. All original domain/task totals, native arrays and per-task effects remain archived and independently audited.

### Original qualification unchanged

R_prod/M_match/C_k1 each mismatch R_stock on both GSM8K probes in every original ten-repeat task set (20/240 per arm). N_k1 mismatches80/240 on eight tasks. Original request_qualified_ratio and qualified_ratio remain null. Original RESULTS.json is retained byte-for-byte in the inherited CAS, and its entire structure is also carried in QUALIFICATION.json.

stock_ref_qualified, posthoc_pairwise_output_equal, physical_residency_qualified and request_cost_qualified remain separate. Post-hoc R_prod=M_match=C_k1 supports descriptive negative whole-request economics only; it does not pass the stock gate or certify deployment/residency.

## Independent audit and restoration

verify96.py is a separate standard-library auditor; it never imports an executor or calls native code. It checks full prospective grids, unique charged starts/closures, complete arrays/raw hashes, owned PID/adapter/heap scope, frozen model/runtime hashes, actual recipes, graph/row/cycle conservation, natural cuts, own binding guards and historical pairwise fees/qualification. Ten synthetic cases reject missing/duplicate coordinates, fake widths, cropped/suffix-lost outputs, observer drift, diagnostic fee promotion, borrowed PID, invalid signed headroom, nonfinite top2 and forced prefixes. The six original PR93 rejection tests are retained too.

ARCHIVE_MANIFEST.json indexes a de-duplicated CAS including all7379 old logical files and new raw RESULT/REQUEST/trace/memory/API/module evidence, source/binary/model pins, diagnostics failures and chronological ledger. External GGUF weights are not archived; their full SHA256 is rechecked. COMPLETE_CAS.json lists exact sizes/SHA256/Git blob SHA for512KiB byte-preserving download chunks.

LOCAL_RESTORE.json and REMOTE_RESTORE.json record fresh full-byte restoration and rederived result equality. Remote restoration reads actual authenticated GitHub bytes from a pinned commit, validates chunks/archive, restores every object/path and reruns the independent auditor without native execution. Metadata-only or local substitute evidence is not accepted. Final receipt publication is separately authenticated to avoid self-referential archive hashes.

No main branch, manuscript, release or earlier PR was modified or merged. The separate Draft result PR targets the PR96 design branch.
