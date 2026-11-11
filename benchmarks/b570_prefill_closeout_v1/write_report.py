"""Generate reports and tables from the complete frozen native panel."""
from pathlib import Path
import csv, datetime, math
from prepare import ROOT, read

def geo(x):return math.exp(math.fsum(math.log(v) for v in x)/len(x))
def save(name,text):(ROOT/name).write_text(text,encoding='utf-8')
def main():
    a=read(ROOT/'INDEPENDENT_ANALYSIS.json');reg=read(ROOT/'REGISTRATION.json')
    rows=read(ROOT/'TIMING_REQUESTS.json');measured=[x for x in rows if x['category']=='measured']
    blocks=a['blocks'];inputs=read(ROOT/'INPUT_PANEL.json')['inputs'];benefit=a['practical_screen_pass']
    outcome='PRACTICAL_FINITE_PANEL_BENEFIT' if benefit else 'NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT'
    table=['| Input | SUBMIT / dual BASE service | Service reduction | SUBMIT / R | dual BASE / R | A/A imbalance |',
           '|---|---:|---:|---:|---:|---:|']
    for i,inp in enumerate(inputs):
        group=[b for b in blocks if b['input_index']==i];ratio=geo([b['candidate_over_dual_control'] for b in group])
        table.append(f"| {inp['id']} | {ratio:.8f} | {100*(1-ratio):+.4f}% | {geo([b['candidate_over_R'] for b in group]):.6f} | {geo([b['dual_control_over_R'] for b in group]):.6f} | {100*(geo([b['aa'] for b in group])-1):+.4f}% |")
    request_ratios=[]
    for s in range(4):
        for i in range(4):
            c={x['label']:x for x in measured if x['session']==s and x['input_index']==i}
            request_ratios.append(c['SUBMIT']['request_seconds']/((c['BASE_A']['request_seconds']+c['BASE_B']['request_seconds'])/2))
    service_ratio=a['candidate_over_dual_control'];reduction=100*(1-service_ratio)
    economics='SUBMIT remains slower than contemporary target-only R.' if a['candidate_over_R']>=1 else 'SUBMIT is faster than contemporary target-only R within this finite panel; no additional practical screen against R was preregistered.'
    disposition=('Identify SUBMIT as a separately qualified software baseline for these four inputs and this exact runtime. Keep the original PR134 reference and paper values unchanged.' if benefit else 'Retain the original QB/thread8 baseline; this screen does not establish a practical improvement. The small observed effect remains unresolved and does not establish equivalence.')
    text=f'''# B570 final draft-prefill submission closeout

**{outcome}**

On the four exposed PR134 inputs, the complete fresh-context service ratio SUBMIT / mean(BASE_A, BASE_B) is **{service_ratio:.8f}**, a **{reduction:+.4f}% service reduction**. The registered practical screen **{'passes' if benefit else 'does not pass'}**. SUBMIT / contemporary R is **{a['candidate_over_R']:.8f}**; dual BASE / R is **{a['dual_control_over_R']:.8f}**. {economics}

## Frozen intervention and execution

Study UUID `{reg['study_uuid']}`. PR141 design head `03cc11662f0ff21514efd40e9a09d4c7e1d2c672`; source/manifest checkpoint `93ab8d62c24ed7bf60333b8ee196893d1991d868`; first-native registration freeze `a173f09c24e1af815257db350c1d64df87f09c15`; qualification-containing timing freeze `501ee5d46bbc386ca7a0462826126f1d356c5562`. Each process receipt identifies its actual freeze. All commits precede their respective native stages.

Only draft-prefill submission changes: one logical llama_decode instead of one call/synchronization per prompt token. Physical ubatch1, threads8, target QB, original numerical DLLs, models/tokenizer, final-token output flags, positions, KV/pending state and cap64/natural EOG are retained. BASE_A/B invoke exactly the same branch. Both weights remain resident for R. There is no target-prefill change or CPU1 combination. Source and observer changes are separated in SOURCE_AUDIT.md and request_observer_diff.patch.

All **156 registered requests /9 model processes** completed: 4 E0 calibration, 24 E1 qualification, 64 matched warmups and 64 measured requests. Every warmup matches its own input and arm and immediately precedes its measurement. All process exits and normal cleanup were observed. No failed slot, automatic retry, replacement run, outlier deletion, interim subset estimate or success-dependent extension occurred.

## Numerical, observer and physical geometry gates

The original PR134 manifests authenticate 914 historical vectors, including 346 original QB vectors. PR135 attempt2's 346 QB vectors and endpoints/cycles were recovered and rechecked before execution. Original endpoints remain /38 64/CAP, /65 53/EOG, /115 41/EOG, /127 64/CAP.

Fresh E0 compares 62 full vectors with the original /42 bridge. Fresh E1 independently rechecks **914 vectors**: 222 R, 346 BASE and 346 SUBMIT, including rejected verification rows. Capture/count native endpoints and complete cycles match. BASE/SUBMIT's ordered prefill QK and mask/key metadata sequences match, with one observed physical q1 per layer/ubatch and exactly prompt_length *28 draft-layer QK and mask observations in each capture. Consecutive positions, final-token flags and prefill KV endpoints are checked. All timed IDs/EOG/length/terminal/stop and speculative cycles match their original references. Callbacks are absent from all timed requests.

The geometry evidence is shape/source metadata plus complete finite-path full-logit and state equality; actual GPU mask values are not independently read back. Physical microbatch observations occur outside timing. Caller-count reduction is not a measured reduction in GPU operations or a GPU critical-path fraction.

## Complete-service panel

{chr(10).join(table)}

Equal-weight geometric mean over all 16 input/session blocks: `{service_ratio:.12f}`. Per-session ratios: `{a['session_ratios']}`. Largest input-aggregate absolute A/A imbalance: **{100*a['aa_max_input']:.4f}%**. Frozen required reduction: **{100*max(.02,a['aa_max_input']):.4f}%**, together with SUBMIT faster in every session aggregate. Request-only ratio, a secondary window: `{geo(request_ratios):.12f}`.

The primary timer begins before fresh target/draft context creation and graph reservation and ends after context destruction. It includes prefill, generation, native logits/sampling, inherited host/state work, synchronization and teardown. Model loading is separate. Reference comparisons and output-file writes follow the timer. No per-request Python execution or observer is inserted. The outer Python process only supervises the whole native worker and enforces fixed safety reservations. Secondary phase fields sum the inherited decode/synchronize spans; batch construction and loop overhead remain in complete service rather than those sums. No independent whole-prefill interval or GPU critical-path time is inferred. COST_WINDOW_DEFINITIONS.json gives the exact overlapping boundaries.

This is a descriptive, fixed finite panel on one B570/driver/model/runtime configuration. Four exposed inputs support no new-input or length-generalization claim, population confidence interval, equivalence result or fully optimized software ceiling. Machine background exclusivity and cold-driver cache behavior are not established.

## Historical records and cost accounting

PR135 attempt1's failed observer run, CPU-thread negative study and original ledgers are unchanged. The recovered attempt2 time-0 has 3 warmups +6 measured records and a complete 163.5546413-second parent receipt. Time-1 has 3 warmups +2 measured records but no exit/process receipt, with 81.3101785 seconds of recorded service windows. Its full parent cost/exit/cleanup is unknown. Time-2 is absent. These observations remain historical and are never pooled into this study or used to complete its old UUID.

Receipt-backed earlier cumulative cost is 3435.1001972 seconds, with the additional unreceipted process explicitly unknown. New worker wall, model loading, complete service, request-only, synchronized phase windows, wrapper/preflight and conservative owned host wall remain separate in ALL_COST_WINDOWS.csv and CLOSEOUT.json; overlapping windows must not be summed. Preparation/compiler/auditor work is included in conservative owned wall rather than invented isolated active CPU/GPU time. Packaging and final integrity audit costs have separate receipts.

## Disposition and evidence

{disposition} This final bounded study closes the software-policy branch. No additional width sweep, target prefill, persistent-context policy, new shader, k tuning, CPU8, QH, M4/358H, hardware or RTL run follows automatically. No historical paper/reference edit or arXiv submission is performed.

The result PR contains native result JSON, all process receipts, complete slot disposition, phase/cost tables, frozen source/order/asset hashes, raw manifests, independent raw-to-normalized reconstruction and the original PR141 estimator result. COMPACT_EVIDENCE.zip retains detailed native geometry/progress/log files. HISTORICAL_COMPACT.zip preserves recovered prior records. LOCAL_RAW_ARCHIVE.json locates and hashes the complete new raw-vector archive on this machine; original PR134 raw vectors remain separately available at their recorded paths. This is local full-byte authentication and independent computation, not third-party or external raw-data certification. See REPRODUCTION.md and PAPER_ADDENDUM.md.
'''
    save('RESULT.md',text)
    save('PAPER_ADDENDUM.md',f'''# Paper addendum: final B570 draft-prefill submission policy

The final bounded PR141 closeout retains the numerical runtime and physical draft q1/thread8 while changing draft prefill from per-token host submission to one logical prompt submission. All four exposed PR134 inputs pass new capture/count, complete endpoint/state, physical-layer/microbatch and full-logit byte gates. The complete experiment contains156 requests in9 model processes, with64 measurements and64 immediately preceding arm/input-matched warmups. Earlier failed/incomplete studies retain their identities and costs.

Complete fresh-context service SUBMIT/dual-BASE is **{service_ratio:.8f}** ({reduction:+.4f}% reduction); the preregistered 2%-plus-A/A and every-session direction screen **{'passes' if benefit else 'does not pass'}**. SUBMIT/R is **{a['candidate_over_R']:.8f}** and dual-BASE/R is **{a['dual_control_over_R']:.8f}**. {economics} R is contemporary target-only with both weights resident. Request-only and draft-prefill intervals remain secondary windows; fewer logical calls do not establish fewer GPU operations or a GPU critical-path fraction.

{disposition} The evidence is restricted to this four-input/model/runtime/host panel and establishes neither generalization nor a production software ceiling. Preserve PR134/135 and historical manuscript results; this is a separately identified addendum. The software-policy branch is closed after the fixed matrix, without additional search or automatic publication.
''')
    save('REPRODUCTION.md','''# Re-analysis and evidence access

The original native root is `C:/hs/b570-prefill-closeout-20261021`; paths are intentionally retained for exact host provenance. Do not execute prepare/create_driver/register/freeze over this sealed root or restart its UUID. Native execution belongs only to a fresh independently preregistered study and is not authorized by these reproduction commands.

CPU-only re-analysis of the existing root uses `python -B audit.py E0`, `python -B audit.py E1`, `python -B audit.py E2` and `python -B verify_delivery.py`. The first three regenerate deterministic audits from original native records and full raw vectors. The last checks unchanged frozen bytes, raw archives, receipts/nonoverlap, complete slots and ledger sums. They load no model or backend. The original PR141 CPU test command is `python -B -m unittest test_toolkit -v` from `design/`.

COMPACT_EVIDENCE.zip contains detailed geometry/progress/result/receipt/log records. LOCAL_RAW_ARCHIVE.json identifies FULL_RAW_LOCAL.zip by absolute path, size and SHA-256. Original PR134 references remain in `C:/hs/b570-formal-request-20261020` and are individually authenticated by the recorded original manifest. A remote reviewer must obtain these raw archives from the author and verify their hashes; Git alone does not provide external raw-vector access or certify that every local file remains available.

All five numerical DLLs are copied unchanged from PR134/135. Only the C++ host is compiled, using the CMake include/library paths and frozen build identities. Arbitrary current upstream headers, llama libraries or model weights are not substitutes. FROZEN_FILES.json binds the actual executable, DLLs, models, original references and source. No model, executable, DLL or full raw-vector archive is committed. All committed artifact bytes have Git text conversion disabled.

FULL_RAW_LOCAL.zip and HISTORICAL_COMPACT.zip preserve new observations and earlier incomplete/failed studies separately. Historical unreceipted time-1 cost remains unknown; do not infer its complete parent cost from request timers, timestamps or the new matrix. Cost windows in ALL_COST_WINDOWS.csv overlap and must not be added as if disjoint.
''')
    save('COST_WINDOW_DEFINITIONS.json',__import__('json').dumps({
        'service_seconds':'Outer native request call, including environment selection, fresh contexts/graph reservation, prefills, native generation/sampling/state and context destruction; excludes prior reference read and subsequent comparisons/result writes.',
        'request_seconds':'Inherited inner interval after context construction through final synchronization; excludes context teardown and some record finalization.',
        'decode_phase_seconds':'Sum of inherited inner decode spans from immediately before llama_decode through batch free and llama_synchronize. Excludes batch construction and host loop overhead; not an independently timed whole-prefill interval or GPU time.',
        'model_load_seconds':'Native model-load interval, separate from individual fresh-context service.',
        'worker_wall_seconds':'Whole owned native parent lifetime, including load, capture/qualification or warmups/measurements, comparisons, output and cleanup.',
        'wrapper_total_seconds':'Includes preflight hash/resource checks plus native parent supervision; overlaps worker wall.',
        'owned_wall_seconds':'Conservative continuous host preparation/coordination wall; includes compilation/audits, not isolated active CPU or GPU occupancy.',
        'do_not_sum_overlapping_windows':True},indent=2)+'\n')
    fields=['session','input_index','input_id','label','category','slot','service_seconds','request_seconds',
            'draft_prefill_decode_sync_sum_seconds','target_prefill_decode_sync_sum_seconds','target_verify_decode_sync_sum_seconds','draft_prefill_api_calls','length','stop_reason']
    with (ROOT/'TIMING_TABLE.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x in rows:
            row={k:x[k] for k in fields if k in x}
            row.update(draft_prefill_decode_sync_sum_seconds=x['draft_decode_seconds'].get('PREFILL',0),
                       target_prefill_decode_sync_sum_seconds=x['target_decode_seconds'].get('PREFILL',0),
                       target_verify_decode_sync_sum_seconds=x['target_decode_seconds'].get('VERIFY',0));w.writerow(row)
    print(outcome,service_ratio,a['candidate_over_R'])

if __name__=='__main__':main()
