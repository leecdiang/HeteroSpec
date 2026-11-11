"""Summarize completed gates without changing their estimators or raw evidence."""
import hashlib
import json
from pathlib import Path


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    root=Path('E:/rtx160/research');b=root/'epoch07';out=Path(__file__).parent
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    paths={'cost':b/'INDEPENDENT_COST.json','qualification':b/'INDEPENDENT_QUALIFICATION.json',
           'ledger':root/'LEDGER_AUDIT.json','regression':root/'CROSS_MODEL_REGRESSION.json',
           'freeze':b/'CANDIDATE_FREEZE.json','mechanism':b/'MECHANISM_REVIEW.json'}
    r={k:read(p) for k,p in paths.items()};cost=r['cost'];q=r['qualification'];ledger=r['ledger']
    assert cost['status']=='INDEPENDENT_COST_RECONSTRUCTED' and cost['records']==1728
    assert q['status']=='INDEPENDENT_QUALIFICATION_RECONSTRUCTED' and q['candidate_requests']==240
    assert ledger['status']=='COMPLETE_LEDGER_RECONSTRUCTED'
    assert r['regression']['status']=='CROSS_MODEL_REGRESSION_PASS'
    failures=[x for x in ledger['units'] if not x['success']]
    operation_costs=[]
    for p in sorted(Path('D:/rtx160/operations').glob('*.json')):
        if p.name.startswith(('PACK','ARCHIVE','UPLOAD','REMOTE','DELIVERY','PUBLISH','TRANSPORT')):continue
        receipt=read(p)
        operation_costs.append({'name':p.name,'seconds':receipt.get('seconds'),'exit_code':receipt.get('exit_code'),
          'start':receipt.get('start'),'end':receipt.get('end'),'sha256':sha(p)})
    summary={'status':'SCIENTIFIC_EXECUTION_AND_INDEPENDENT_RECONSTRUCTION_COMPLETE',
      'result_pr':'https://github.com/leecdiang/HeteroSpec/pull/162','confirmation_epoch':'epoch07',
      'historical_requests':54,'historical_complete_vectors':5916,'unseen_inputs':24,
      'original_reference_requests':48,'qualification_requests':240,'measured_requests':864,'warmup_requests':864,
      'qwen_candidate_regressions':336,'successful_qwen_original_controls':56,
      'qualification_complete_vectors':q['complete_vectors'],'qualification_candidate_states':q['candidate_final_states'],
      'means':cost['means'],'AA_max_symmetric_input':cost['AA_max_symmetric_input'],'sessions':cost['sessions'],
      'practical_layout_gain':cost['practical_layout_gain'],
      'reserved_credits':ledger['reserved_credits'],'development_credits':ledger['development_credits'],
      'completed_model_requests':ledger['completed_model_requests'],'completed_operator_replays':ledger['completed_operator_replays'],
      'completed_extra_shadow_decodes':ledger['completed_extra_shadow_decodes'],
      'native_supervised_wall_seconds':ledger['native_supervised_wall_seconds'],
      'pre_transport_operation_costs':operation_costs,
      'operation_cost_scope':'Individual preparation/build/test/audit/native/supervisor wall receipts. Nested and overlapping operations are not summed; null duration is not treated as zero. Transport costs are delivered separately after raw archive sealing.',
      'failed_native_units':failures,'evidence':{str(p):sha(p) for p in paths.values()},
      'delivery_status':'PENDING_REMOTE_ALL_MEMBER_READBACK',
      'scope':'Original reference unchanged. All failures and full reserved credits retained. Finite single-host evidence, no population confidence interval or universal guarantee.'}
    for p in (root/'FINAL_EXECUTION_SUMMARY.json',out/'FINAL_EXECUTION_SUMMARY.json'):
        with p.open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
    source=out/'RESULTS.md';text=source.read_text(encoding='utf-8');marker='## Gates still in progress'
    assert text.count(marker)==1
    prior=out/'RESULTS_before_confirmation.md'
    with prior.open('x',encoding='utf-8') as f:f.write(text)
    gain='passed' if cost['practical_layout_gain'] else 'did not pass'
    ratio=cost['means']['layout'];threshold=max(.02,cost['AA_max_symmetric_input'])
    final=f'''## Frozen confirmation and independent reconstruction

The final host-schema successor, epoch07, uses the unchanged config06 native candidate. Its repeated 36-request development matrix passes. The complete pinned historical exposure union excludes IDs, text hashes and token hashes across all reviewed project history. The selected 24-input code/math × short/long panel remained unchanged through the pre-output host-schema correction and was frozen before any reference or candidate output.

All 48 immutable old-R reference requests and all 240 candidate qualification requests complete. Independent reconstruction checks {q['complete_vectors']:,} complete decision vectors and {q['candidate_final_states']:,} candidate final-state artifacts, all endpoints/transactions/observer pairs, original-R vector preservation and layer/backend coverage. New Qwen8B/14B regressions pass 144/192 requests; the additional 24/32 successful original-R controls preserve complete R vectors. These Qwen inputs are development inputs, not unseen confirmation.

All six timing sessions complete: 864 measured requests and 864 immediately preceding warmups, with no captures, shadow consumers or concurrent archives/profiling. Independent recomputation matches the production report and retains every block. The geometric mean C_QB / arithmetic-dual-C_PQ service ratio is **{ratio:.9f}**. The largest symmetric input-aggregate A/A imbalance is **{100*cost['AA_max_symmetric_input']:.6f}%**; the prospective improvement threshold is **{100*threshold:.6f}%**. The practical layout-gain screen **{gain}**. Session ratios are {', '.join(f'{x:.9f}' for x in cost['sessions'])}. An unfavorable performance result is not repaired by extending or selecting timing blocks.

| Service ratio | Geometric mean |
|---|---:|
'''
    for key in ('layout','D_QB','D_PQ','CQB_R','MQB_R','MPQ_R','CPQ_R','AA'):
        final+=f"| {key} | {cost['means'][key]:.9f} |\n"
    final+=f'''
`layout` is C_QB / dual-C_PQ; `D_QB` and `D_PQ` are same-layout M/C ratios. The `_R` columns divide each arm's service time by R. Service includes fresh context setup, prefill/decode, state transfer/reconciliation, synchronization and teardown. Model load is reported separately: {cost['reported_model_load_seconds']:.6f} seconds across six sessions. All measured and warmup service totals and component totals are in INDEPENDENT_COST.json. These ratios are paired finite-panel summaries, without a population confidence interval.

## Complete accounting and retained failures

The append-only new study ledger reserves **{ledger['reserved_credits']} work credits**, including {ledger['development_credits']} development credits. It records {ledger['completed_model_requests']} audited complete model requests, {ledger['completed_operator_replays']} standalone operator replays and {ledger['completed_extra_shadow_decodes']} extra shadow decodes. Supervised wall time is {ledger['native_supervised_wall_seconds']:.3f} seconds, including host auditing and protocol waits. Reservations and actual calls are different quantities. Failed processes may have additional partial work; missing telemetry is not treated as zero. Historical PR151/PR156/PR159 records remain separately retained and are not reset or credited back.

FINAL_EXECUTION_SUMMARY.json additionally indexes every retained pre-transport preparation, build, test, audit and supervisor operation receipt with its elapsed time and exit code. Nested/overlapping operations are not summed into a misleading wall total. Archive/upload/download costs are preserved in the separate delivery metadata produced after scientific timing finishes.

There are {len(failures)} failed native execution units. Complete per-slot dispositions distinguish audited completion, worker completion rejected by host audit, possible partial starts, and unstarted slots. The baseline numerical failures, build-only candidates, host freeze/schema corrections and failed preparation/transport operations are also preserved even where they did not create a failed native unit. See LEDGER_AUDIT.json, ENGINEERING_CHANGES.jsonl, operation receipts and all source versions.

## Delivery

Independent result PR: https://github.com/leecdiang/HeteroSpec/pull/162. Full archive upload and fresh all-member download verification are pending; no remote delivery PASS is claimed until their receipts are added. No merge or manuscript edit is performed. PAPER_ADDENDUM.md states the supported scope and limitations.
'''
    source.write_text(text.split(marker)[0]+final,encoding='utf-8')
    print(summary['status'],flush=True)


if __name__=='__main__':main()
