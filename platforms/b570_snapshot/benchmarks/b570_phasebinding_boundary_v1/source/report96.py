"""Readable result report built only from independently verified evidence."""
import pathlib,json
R=pathlib.Path(__file__).resolve().parent.parent
j=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
r=j(R/'analysis/RESULTS.json');p=j(R/'analysis/PHASE_INTERVENTION.json');s=j(R/'analysis/FORK_SHAMS.json');w=j(R/'analysis/WORK_WITNESSES.json')
L=['# B570 phase-binding, reference-boundary and physical-work result','',
'The admitted PR96 whole-recipe fallback reproduces the complete stock/production output boundary. Native C512 verification remains two occupied width1 micrographs per logical k1 cycle, with separate draft proposal and catch-up work. The immutable post-hoc same-output cost remains negative. Isolated prefill causality and donor-state interaction remain UNRESOLVED.','',
'B570 does not implement RTX query-batch. These findings apply to this frozen actor, not a universal GPU/Vulkan limit or model-answer accuracy.','',
'## Four questions','','| Question | Conclusion | Evidence / boundary |','|---|---|---|']
for k,v in r['questions'].items():L.append('| '+k+' | '+v['status']+' | '+v.get('reason',v.get('scope',''))+' |')
e=r['execution']
L+=['','## Execution and immutable provenance','',
f"- Started {e['requests_started']} requests: {e['requests_completed']} complete, {e['requests_failed']} failed; P1={e['P1']}, P2={e['P2']}/{e['P2_planned']} complete; two zero-forward load probes; {e['charged_units']} charged units; zero warmups, retries or donor-fork forwards.",
f"- {e['owned_native_workers']} actual owned native worker lifetimes; {e['owned_gpu_seconds']:.3f} owned GPU-process seconds (<18,000).",
f"- Minimum sampled same-PID dedicated headroom: {e['minimum_sampled_owned_dedicated_headroom_bytes']:,} bytes (gate 536,870,912). Native weights and F16 KV placed on Vulkan0. Physical residency remains UNKNOWN; sampled headroom/placement are not continuous residence proof.",
"- Existing 1,200 paid PR92 counts requests and 50 warmups were not rerun. All 7,379 inherited logical files were restored unchanged and hash-verified.",
f"- Design head: {r['design_head']}; PR92: {r['parents']['PR92']}; PR93: {r['parents']['PR93']}.",
f"- Prospective execution source seal: {r['source_commit']}, pushed and authenticated by actual GitHub bytes before the first new forward. See F0A.json, F0A_AUTHENTICATED.json, PLAN.json, INPUTS.json and LEDGER.jsonl.",
"- Original source seal b8b0f4feb1a142b112200a48e9903f4bd1384a66; small raw download-chunk supplement 8bc0d9e8d53af54a967c98c12714349d577565a1. All 306 original capsule files were freshly restored from actual authenticated GitHub bytes before execution.",
"- A UTC logging exception followed the first successful zero-forward O128 probe, before any request start. The traceback/source/receipt and successful native probe remain under versions/pre-forward-log-amendment/. The correction was separately sealed/authenticated before forward. The completed probe was not replayed; numerical binaries, model inputs, sampler, plan and request slots did not change.",
"- Initial Hostx86 build failed LNK1101 / incorrect MSPDB140.DLL version. A separate Hostx64 Release build succeeded. Build failures and a counter-hash finishing error remain in versions/, receipts/ and logs. All five numerical DLLs are byte-identical to PR92.",
'','## Whole recipes and complete reference outputs','',
'Clean 2x2 admission: PHASE_FACTOR_NOT_ISOLATABLE. Target-only ordinary UB128/512 and bound UB1 each submit one continuation ID and execute occupied width1. Binding also couples capacity4, synchronization and scheduler reservation; ordinary capacity is1. These are entire recipes, not independent physical continuation treatments.','',
'| Arm | Prefill UB | Continuation UB | Occupied continuation width | Capacity | Path |',
'|---|---:|---:|---:|---:|---|',
'| O128 |128|128|1|1|Original stock-compatible ordinary|',
'| O512 |512|512|1|1|Original production ordinary|',
'| B128 |128|1|1|4|Existing binding ABI/capacity4 with UB128 prefill|',
'| B512 |512|1|1|4|Original matched binding path|',
'| C512 (P2) |512|1|1|4|Original k1 binding candidate + Q4 draft|','',
'Fixed Q6_K target/Q4_K_M draft, greedy sampler, exact prompt token arrays, F16 KV, cap128, logical batch512, context1024, threads10, FA off and old binding ABI. STATE_RECIPE_INVENTORY.md records actual phase ownership, pending consumption, sampler, KV positions, output/graph reservation and synchronization. Binding synchronizes and may reserve scheduler work; capture adds separate observer synchronizations/readbacks. Neither is CPU-only.','',
'P1 repeats are fresh owned-worker counts/capture-off, heavy/capture-on, and heavy plus own same-context same-UB binding no-op. All 24 task/arm complete-output guards pass across three repeats. Controls were prospectively selected by ascending original integer task ID from stable PR92 tasks; the two GSM8K probes are exposed known divergences. No task substitution or fee-based selection occurred.','',
'| Task | O128/O512 first difference | O128=B128 full output | O512=B512 full output | B128/B512 first difference |',
'|---|---|---|---|---|']
tasks=[c['id'] for c in j(R/'INPUTS.json')['cases']]
def cmp(t,a,b):return next(x for x in r['recipe_comparisons'] if (x['task'],x['left'],x['right'])==(t,a,b))
def ds(x):
 d=x['first_difference'];return 'none (full equality)' if d is None else f"index {d['index']}: {d['left_id']} to {d['right_id']}"
for t in tasks:L.append(f"|{t}|{ds(cmp(t,'O128','O512'))}|{cmp(t,'O128','B128')['complete_output_equal']}|{cmp(t,'O512','B512')['complete_output_equal']}|{ds(cmp(t,'B128','B512'))}|")
L+=['',
'Every O128/O512/B512 endpoint reproduces its pinned old own-path complete output. B128 is compared to the entire O128 trajectory. These checks include all native IDs, EOG flags, length, terminal and stop reason; matching only the first differing ID or a cropped suffix is insufficient. Four controls remain invariant, including MBPP EOG and GSM8K CAP boundaries. PHASE_INTERVENTION.json retains all six arm pairs per task, repeats and no-trigger cases.','',
'### Natural boundary diagnostics','','| Task / cut | O128 top1 / margin | O512 top1 / margin | Natural prefix equal | FP32 vector hash equal | KV hash equal |','|---|---|---|---|---|---|']
for q in p['boundary_pairs']:
 if q['left']=='O128' and q['right']=='O512' and q['task'] in tasks[:2]:
  L.append(f"|{q['task']} / {q['index']}|{q['top1_left']} / {q['margin_left']:.9g}|{q['top1_right']} / {q['margin_right']:.9g}|{q['natural_prefix_equal']}|{q['full_logits_hash_equal']}|{q['sequence_KV_hash_equal']}|")
L+=['',
'Boundary records retain actual consumed IDs/positions, naturally committed prefix, native greedy top1, runner-up ID/logit/margin, current UB/capacity, KV positions/state sizes/digests and source-owned sampler. Equal tokens do not imply equal KV/logits. Bounded witnesses retain top2 values and whole-vector/state digests; full FP32 and serialized KV payloads are absent. Independent verification checks full outputs, pins, finite values and provenance, but cannot independently rehash absent tensors.',
f"Own-binding no-op guards: {s['own_binding_guard_calls']} live same-context full-context and sequence-KV byte comparisons. They are not clone/restore shams. Donor forks and clone/restore shams=0: FORK_NOT_IMPLEMENTABLE. No validated full target/pending/sampler/scheduler/reservation restoration contract exists in this actor. The actual core state_write_data writes architecture plus memory-module state; sequence serialization writes memory state. It does not serialize dynamic logits/output buffers, frontend pending, sampler ownership or scheduler/reservation. Logits are captured separately. Frozen PLAN/F0A wording KV/logits is preserved but corrected here and in SOURCE_SERIALIZATION_SCOPE.json; fork admission is unchanged. Partial KV state was not promoted to full retained-state causality. Prefill-only and state/continuation causes remain UNRESOLVED.",
'','## Physical work, dispatch metadata and actual costs','',
'P2 registered and attempted six exposed inputs x three arms x two capture sessions=36:35 completed,1 API-observer scope failed without replay. New elapsed fields are diagnostic only, excluded from paid prices. Each C512 VERIFY caller submits two IDs at UB1 and executes two successful occupied width1 native micrographs. Native caller IDs, occupied rows, graphs, KV positions, cycle decisions and complete committed arrays are independently reconciled. O512/B512 each execute one occupied width1 graph per ordinary continuation call.','',
'| Domain / arm |Requests|Full output IDs|Acceptance|Target verify rows/output|Target total graphs/output (prefill included)|Draft proposal rows|Draft catch-up rows|',
'|---|---:|---:|---:|---:|---:|---:|---:|']
for a in w['aggregates']:
 t=a['totals'];acc='n/a' if a['acceptance'] is None else f"{a['acceptance']*100:.3f}%"
 L.append(f"|{a['domain']} / {a['arm']}|{a['requests']}|{t['output_ids_count']}|{acc}|{a['per_output']['target_verification_rows']:.6f}|{a['per_output']['target_micrographs']:.6f}|{t['draft_proposal_rows']}|{t['draft_catchup_rows']}|")
d=w['dispatch']
L+=['',
f"One predeclared C512 GSM8K/test/1248 session0 API-dump request failed the sampled log stop threshold and has no complete native endpoint: {d['vkCmdDispatch_calls']:,} vkCmdDispatch API calls, {d['group_count_metadata_values']:,} group-count metadata values, {d['bytes']:,} bytes; SHA256 {d['sha256']}. Loaded layer SHA matches the prospective pin. The raw trace is PARTIAL_FAILED_OBSERVER_SCOPE. Watcher sampled171,123,559 bytes at a134,217,728-byte stop threshold; final file171,281,419 bytes. The0.5-second sampled watcher has an overshoot: the hard byte-size cap was not met and this gate is failed, not PASS. It killed only owned PID24252. No completed counters, output arrays or timing are fabricated for this slot, and it was not replayed. Actual partial CPU API metadata is not GPU completion/kernel timing. The original unstarted23 slots were separately sealed/authenticated at b81e1b1835e3db7ee8ef0cb9ad63503116c9a816, then continued with the original actor/plan. The remaining five session0 candidate inputs used their predeclared separate worker without this layer. All11 completed C512 witnesses preserve complete old own-path output; GSM8K/test/1248 has only its session1 successful witness.",
'',
'Successful native process_ubatch graph/occupied-row counters are separate from shader kernels, continuous residency and GPU completion. They support the observed extra-work geometry: no two-row physical micrograph amortization plus proposal/catch-up/reconciliation. They do not quantify the fraction of request cost due to draft, binding or GPU stages. No completed non-invasive stage marker was available: MODEL_TIMING_UNAVAILABLE. No coefficients or break-even threshold were fitted.','',
'### Immutable paid same-output costs','',
'Use five-round arm medians per task/session, left/right fee ratio, then average logs across two consecutive sessions and 24 tasks. Each domain has12 tasks and120 paid requests per arm. Full EOG IDs and CAP endpoints are included. Every pair has240 complete equal native outputs. No new formal paid or cross-date interval was added.','',
'| Post-hoc pair |Left fee/right fee|MBPP|GSM8K|Right fee increase|Regressions|','|---|---:|---:|---:|---:|---:|']
for a in r['paid_posthoc_pairs']:L.append(f"|{a['pair']}|{a['left_fee_over_right_fee']:.12f}|{a['domain_ratios']['MBPP']:.12f}|{a['domain_ratios']['GSM8K']:.12f}|{a['right_cost_increase_pct']:.3f}%|{a['negative_tasks']}/24|")
L+=['',
'Historical C_k1 acceptance is88.8218% MBPP (2940/3310) and87.4847% GSM8K (7130/8150). High acceptance did not reduce measured whole-request fees. All original domain/task totals, native arrays and per-task effects remain archived and independently audited.','',
'### Original qualification unchanged','',
'R_prod/M_match/C_k1 each mismatch R_stock on both GSM8K probes in every original ten-repeat task set (20/240 per arm). N_k1 mismatches80/240 on eight tasks. Original request_qualified_ratio and qualified_ratio remain null. Original RESULTS.json is retained byte-for-byte in the inherited CAS, and its entire structure is also carried in QUALIFICATION.json.',
'',
'stock_ref_qualified, posthoc_pairwise_output_equal, physical_residency_qualified and request_cost_qualified remain separate. Post-hoc R_prod=M_match=C_k1 supports descriptive negative whole-request economics only; it does not pass the stock gate or certify deployment/residency.','',
'## Independent audit and restoration','',
'verify96.py is a separate standard-library auditor; it never imports an executor or calls native code. It checks full prospective grids, unique charged starts/closures, complete arrays/raw hashes, owned PID/adapter/heap scope, frozen model/runtime hashes, actual recipes, graph/row/cycle conservation, natural cuts, own binding guards and historical pairwise fees/qualification. Ten synthetic cases reject missing/duplicate coordinates, fake widths, cropped/suffix-lost outputs, observer drift, diagnostic fee promotion, borrowed PID, invalid signed headroom, nonfinite top2 and forced prefixes. The six original PR93 rejection tests are retained too.',
'',
'ARCHIVE_MANIFEST.json indexes a de-duplicated CAS including all7379 old logical files and new raw RESULT/REQUEST/trace/memory/API/module evidence, source/binary/model pins, diagnostics failures and chronological ledger. External GGUF weights are not archived; their full SHA256 is rechecked. COMPLETE_CAS.json lists exact sizes/SHA256/Git blob SHA for512KiB byte-preserving download chunks.',
'',
'LOCAL_RESTORE.json and REMOTE_RESTORE.json record fresh full-byte restoration and rederived result equality. Remote restoration reads actual authenticated GitHub bytes from a pinned commit, validates chunks/archive, restores every object/path and reruns the independent auditor without native execution. Metadata-only or local substitute evidence is not accepted. Final receipt publication is separately authenticated to avoid self-referential archive hashes.',
'',
'No main branch, manuscript, release or earlier PR was modified or merged. The separate Draft result PR targets the PR96 design branch.','']
(R/'analysis/RESULTS.md').write_bytes('\n'.join(L).encode());print('RESULTS_MD_GENERATED',len(L))
