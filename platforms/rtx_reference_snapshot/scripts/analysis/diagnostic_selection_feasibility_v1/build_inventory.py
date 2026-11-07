"""Reproducible metadata inventory; this report builder is not a selector."""
import csv
from audit import DOC,load,save,PIN

def main():
    # Exact sources are relative to the pinned repository unless a raw restore is named.
    bridge='benchmarks/rtx_target_only_bridge_v1/'
    b570='benchmarks/b570_prefill_diagnostic_v1/'
    rows=[
    ['Supported action/configuration','PROTOCOL.json in '+bridge+' and '+b570+'; constructor UB capacities, not observed shape','before selection','CPU manifest/source reads; qualification is inherited setup','yes','yes','different actions/settings/cohorts; cross-platform counterparts absent','no'],
    ['Hardware/action support','ASSET_ENVIRONMENT.json / ASSET_MANIFEST.json; loaded device and assets','before selection','CPU existing manifests; future device authentication is setup','yes','yes','capability can constrain actions; name cannot determine remedy','no'],
    ['Declared reference contract','neutral R arrays and protocol endpoint; fixed independently of candidate','before selection if retained, otherwise paid reference acquisition','one full reference workload with required repeats plus storage/CPU checking','yes','yes','different platform references; no new reference run in phase','contains reference answers; evaluator only, hidden from selector'],
    ['Baseline reference disagreement','N0 versus fixed R arrays/boundaries','after paid baseline + reference observations','both workloads acquired through query API; full output comparison','yes','yes','confirms failure, not unique stage; exposed outcomes','answer-derived label; available only after charged acquisition'],
    ['Caller grouping','restored native trace decode.caller_batch/tokens/positions/logits_mask; B570 observer.h trace','after paid baseline/probe','captured forward execution plus logging; metadata parsing CPU','yes raw114','qualified source/receipt; no complete original traces read here','caller length, UB capacity and occupied graph count differ','post-action if candidate trace; no future outcome by itself'],
    ['Occupied graph shape','attn_norm-0.ne[1] on RTX; embd.ne1 on B570','after paid baseline/probe','same captured execution plus graph observer; count by phase','yes raw114','inherited source/review witness','does not identify operation/kernel; U2 actual graph tensors absent','candidate shape is post-intervention, not a free selector input'],
    ['Initial pending KV snapshots','source_before/destination/source_after KV with transfer event; qualified preserved first sample','after paid native/proxy','execute prefill, serialize/copy state; hashes/positions CPU checks','yes initial, inherited blob verification','inherited qualification','initial handoff alignment only; not later divergent decision KV','post-action witness; no repair direction'],
    ['Initial pending logits','trace pending_logits.f32 with first_pending semantic point','after paid prefill/probe','full prefill target work and capture/storage','yes on N paths','inherited qualified pending capture','equal N0/N1 initial state does not prove equal later state','candidate observation is post-intervention acquisition'],
    ['Baseline top-two margin','target sample top scores at its logged decision','after paid baseline','forward logits, top-two extraction and logging; no free model work','yes for captured N0','capture commits scores available by source; not newly reparsed','no fixed reference-repair threshold; known divergence location is outcome-selected','baseline margin can be legitimate paid feature; not used by P2'],
    ['N1 first divergent scores','DIAGNOSTIC_FACTS selected first-divergence decision from native N1','only after intervention outcome and comparison','execute N1 and baseline, align prefixes/decisions','yes selected cases','separate B570 diagnostic outputs','cannot predict N1 cheaply after already running N1','post-intervention answer information; prohibited free feature'],
    ['Live U2 internals','DIAGNOSTIC_FACTS U2_state explicitly unavailable','unavailable','new richer capture would require unsupported work','no','ordinary U2 outcome/capture absent','no live KV/logits/actual graph-tensor access','missing, never filled from N1'],
    ['Later common-prefix KV','complete actual live decision KV at first later divergence','unavailable in bridge','would require additional aligned capture; not authorized here','no','late-fork separate state experiment cannot supply this counterfactual','fresh-prefill shared tokens cannot substitute live KV','missing'],
    ['Opaque sampler bytes','transfer sampler_bytes qualification limit','unavailable','clone/history/seed/behavioral shams checked; byte serialization unavailable','no bytes','no bytes','available metadata does not equal bytewise sampler state','missing'],
    ['Qualified proxy result','old RTX H1 and B570 T1 complete arrays through declared endpoint','after explicitly paid proxy query','RTX two P/R workers/draft+target; B570 full target-only and transfer','yes exposed panel','yes exposed panel','finite closure; false rejection outside measured scope remains possible','post-probe outcome allowed only after charge'],
    ['Actual candidate result','native N1 arrays through contract endpoint','after explicitly paid action/validation query','full native workload including draft/target/transfer/logging then CPU verification','yes','yes','proxy result cannot be relabelled as executed native result','post-intervention label, hidden until requested'],
    ['Unexecuted counterfactual','CANDIDATE_COVERAGE unknown cells','unavailable','no substitute or model execution in this phase','explicit UNKNOWN','explicit UNKNOWN','no synthetic stage factorial or other-task answer substitution','missing'],
    ['Comparable latency/energy','protocol performance_claims=false; instrumentation and old timers differ','unavailable','would need matched qualified boundaries; no such experiment here','no','no','raw elapsed time is not an intervention savings measurement','unmeasured cost'],
    ['Numerical-work counts','RAW_WORK_INVENTORY decode tokens/phase/shapes and transfers','after paid existing execution','CPU parse retained traces; historical forwards already incurred','native114 direct','detailed counts unavailable; path inherited','shape occurrence != kernel dispatch/latency; committed IDs != evaluated tokens','post-run cost accounting only'],
    ['Task/platform identifiers','cohort/matrix keys','before selection','CPU bookkeeping','yes','yes','no remedy lookup; selector receives no platform/task name','may leak exposed remedy if used; prohibited'],
    ['Kernel operands/accumulator bounds','ARITHMETIC_SOURCE_CHECK implementation only; Integer Alibi preconditions absent','unavailable as aligned runtime evidence','needs per-op dispatch/shared operands and overflow checks','not captured','not captured','Q8_0 helper availability does not certify whole-layer exactness','missing'],
    ]
    fields=['feature','exact_source_and_semantics','availability_phase','acquisition_steps_and_cost','RTX_availability','B570_availability','missingness_and_alignment_limits','answer_or_post_intervention_information']
    with (DOC/'FEATURE_INVENTORY.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(fields);w.writerows(rows)
    outcomes=load(DOC/'RECOMPUTED.json')['contexts']
    cells=[]
    for x in outcomes:
        for action in ('N0','N1','U2','R'):
            cells.append({'context':x['context'],'action':action,'eligible_records':x['tasks']*3,**x['actions'][action]})
    unknowns=[
      {'context':'RTX_19','action':'target_prefill_UB128_with_UB2_draft_continuation','status':'UNKNOWN','missing_cells':57,'reason':'No implemented/qualified executed counterpart in this cohort.'},
      {'context':'RTX_19','action':'draft_UB1_only','status':'UNKNOWN','missing_cells':57,'reason':'Draft-policy effect not isolated by existing native candidate.'},
      {'context':'RTX_19','action':'prefill_plus_continuation_joint_change','status':'UNKNOWN','missing_cells':57,'reason':'No joint action matrix; not synthesized from B570.'},
      {'context':'B570_24','action':'late_fork_continuation_UB128','status':'UNKNOWN','missing_cells':72,'reason':'Qualified separate sampled-state study is not this prefill cohort/full-workload reference repair.'},
      {'context':'B570_24','action':'ordinary_global_UB2_target_only','status':'UNKNOWN','missing_cells':72,'reason':'RTX U2 not executed/qualified on this B570 cohort.'},
      {'context':'RTX_MBPP_24_supplement','action':'ordinary_U2','status':'UNKNOWN','missing_cells':72,'reason':'Bridge executed only the old19; no MBPP U2 records.'}]
    save(DOC/'CANDIDATE_COVERAGE.json',{'source_commit':PIN,'separate_cohorts_not_factorial':True,'cells':cells,'unknown_counterfactuals':unknowns,
      'qualified_native_candidates':[{'context':'RTX_19_and_MBPP24','action':'N1 target continuation UB2->UB1; prefill/draft remainUB2','source':'benchmarks/rtx_target_verification_intervention_v1/PROTOCOL.json','proxy':'H1 retains draft+target verification'},
       {'context':'B570_24','action':'N1 target prefillUB128 then continuationUB1; draft staysUB1','source':b570+'PROTOCOL.json','proxy':'T1 target-only prefill intervention'},
       {'context':'B570_partition_reserved24_separate','action':'sampled same-state late verification fork UB1->UB128','source':'benchmarks/b570_partition_intervention_v1/TECHNICAL_QUALIFICATION.json','eligible_for_primary_full_workload_selection':False,'reference_restoration_outcome':'UNKNOWN on prefill panel','reason':'Changes score/downstream trajectory on some separate sampled states; does not supply a certified workload repair action.'}],
      'setup_qualification':'Inherited, not a new engineering/model run; proxy map valid only under declared retained configuration.'})
    save(DOC/'ANALYSIS_HISTORY.json',{'policy_spec_commit':'430ffe4a190fd1615f098543cde584eddd936f40','policy_spec_versions':{'P1':1,'P2':1},'policy_revisions':{'P1':0,'P2':0},
      'development_repairs':[{'kind':'inspection_path','description':'Relative hint paths resolved from bridge cwd were absent; corrected to actual absolute paths before analysis.'},
      {'kind':'inspection_schema_and_encoding','description':'Dictionary/list first-record inspection corrected; UTF8 console mode used to read inherited Chinese text correctly.'},
      {'kind':'arithmetic_byte_check','description':'Initial exact-byte assertion failed; raw hashes retained and CRLF/LF-only difference checked without modifying source.'},
      {'kind':'query_reply_information_boundary','description':'Reference-acquisition reply narrowed to remove unpaid baseline-derived transition fields. Initial9 tests passed; tenth test added; all10 now pass. Rule/order/outcomes/cost ledgers unchanged.'}],
      'new_inference_runs':0,'gpu_forwards':0})
    print('Built20-feature inventory and explicit candidate/unknown coverage')

if __name__=='__main__':main()
