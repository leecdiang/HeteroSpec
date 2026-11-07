"""Post-timing coverage, physical census and complete raw cost accounting."""
from pathlib import Path
from collections import Counter
import argparse, csv, json, sys

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    w=a.work.resolve();out=a.out.resolve();need(read(w/'PIPELINE_STATUS.json')['status']=='COMPLETE','Only complete fixed panel');need(not out.exists(),'Fresh derived report');out.mkdir(parents=True)
    plan=read(w/'panel-01/PLAN.json');checked=read(w/'panel-01/CHECKED.json');workers={x['id']:x for x in plan['workers']};records=[];clocks=[];physical={}
    for c in checked:
        worker=workers[c['id']];clocks.append(dict(id=c['id'],session=worker['session'],arm=worker['arm'],**c['actual_host_clocks']))
        for i,call in enumerate(c['requests']):
            r=read(call['native_receipt']);group='primer' if i<2 else 'measurement';arm=worker['arm'];table=physical.setdefault(group,{}).setdefault(arm,dict(target_rows=0,draft_rows=0,verify_physical_width_hist={},prefill_physical_width_hist={},graphs_reused=0,graphs_built=0,cycles=0,accepted=0,rejected_cycles=0,stops={}))
            for e in r['executions']:
                key='prefill_physical_width_hist' if e['phase']=='PREFILL' else 'verify_physical_width_hist';hist=table[key];hist[str(e['width'])]=hist.get(str(e['width']),0)+1;table['target_rows']+=e['width']
            table['draft_rows']+=sum(int(k)*v for k,v in r['draft_physical_width_hist'].items());table['graphs_reused']+=r['graphs_reused'];table['graphs_built']+=r['graphs_built'];table['cycles']+=len(r['cycles']);table['accepted']+=sum(x['accepted'] for x in r['cycles']);table['rejected_cycles']+=sum(x['rejected'] for x in r['cycles']);table['stops'][r['stop_reason']]=table['stops'].get(r['stop_reason'],0)+1
            records.append(dict(kind=group,root=call['root'],session=worker['session'],arm=arm,service_s=r['service_seconds'],request_s=r['request_seconds'],reset_s=r['setup_seconds'],teardown_s=r['teardown_seconds'],
                planning_s=r['planning_s'],output_copy_s=r['output_copy_s'],prompt_tokens=r['prompt_tokens'],generated_tokens=len(r['ids']),terminal_kind=r['stop_reason'],cycles=len(r['cycles']),
                accepted_proposals=sum(x['accepted'] for x in r['cycles']),target_rows=call['physical']['target_rows'],native_receipt_sha256=call['native_receipt_sha256'],reference_id=call['reference_id']))
    need(len(records)==288 and sum(r['kind']=='measurement' for r in records)==256,'Full unchanged M1 budget')
    with (out/'REQUESTS.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    ledger=[json.loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE'];prior=read(w/'PRIOR_ACCOUNTING.json')['original_reservations']
    byphase={}
    for r in reserved:
        d=byphase.setdefault(r['phase'],dict(requests=0,reserved_rows=0,workers=0,host_statuses={},worker_wall_observed_s=0,wrapper_wall_observed_s=0,unmeasured_workers=0))
        d['requests']+=r['requests'];d['reserved_rows']+=r['rows'];d['workers']+=1;h=read(Path(r['out'])/'HOST.json');d['host_statuses'][h['status']]=d['host_statuses'].get(h['status'],0)+1
        if h['worker_wall_s'] is None or h['wrapper_wall_s'] is None:d['unmeasured_workers']+=1
        else:d['worker_wall_observed_s']+=h['worker_wall_s'];d['wrapper_wall_observed_s']+=h['wrapper_wall_s']
    totals=lambda rows:dict(requests=sum(x['requests'] for x in rows),reserved_rows=sum(x['rows'] for x in rows),workers=len(rows))
    save(out/'ACCOUNTING.json',dict(M1=totals(reserved),prior_immutable_A5000=totals(prior),cumulative=totals(prior+reserved),byphase=byphase,
        negative_admissions_charged=True,no_refunds=True,M2='NOT_RUN',all_engineering_cost_s=None,
        engineering_cost_limitation='Native worker/wrapper and formal adapter invocation clocks retained; uncaptured total acquisition/preparation and reference-bank validation overhead is not invented or added to overlapping clocks'))
    reports=[read(x) for x in sorted((w/'qualification-01').glob('*-CHECKED.json'))];need(len(reports)==8 and all(x['passed'] for x in reports),'Eight finite native reports')
    dispatch=[read(w/'qualification-dispatch-01'/(arm+'-CHECKED.json')) for arm in plan['arms']]
    need(all(x['passed'] for x in dispatch),'All four native projection witnesses')
    save(out/'QUALIFICATION.json',dict(passed=True,scope='Four D4 paths x Qwen/Smol fixed development cases; cap1, cap128/native EOG, heavy/clean; immutable predecessor geometry reused',
        reports=len(reports),root_arm_cases=sum(len(x['roots']) for x in reports),
        original_requested_vectors=sum(len(r['vectors']) for x in reports for r in x['roots'])+len(reports),
        committed_states=sum(len(r['states']) for x in reports for r in x['roots']),terminal_states=sum(len(x['roots']) for x in reports),cap1_states=len(reports),
        all_raw_serialized_states_equal=all(r['active_KV']['raw_equal'] for x in reports for root in x['roots'] for r in root['states']) and all(root['terminal_active_KV']['raw_equal'] for x in reports for root in x['roots']) and all(x['cap1']['active_state']['raw_equal'] for x in reports),
        all_requested_vectors_equal=all(v['equal'] for x in reports for r in x['roots'] for v in r['vectors']) and all(x['cap1']['full_vector']['equal'] for x in reports),
        all_committed_frontier_vectors_equal=all(s['frontier']['equal'] for x in reports for r in x['roots'] for s in r['states']) and all(r['terminal_frontier']['equal'] for x in reports for r in x['roots']),
        actual_EOG=[dict(arm=x['arm'],family=x['family'],root=r['root']) for x in reports for r in x['roots'] if r['terminal_kind']=='EOG'],
        native_negatives=read(w/'capability-negatives-01/CHECKED.json'),finite_only=True,formal_deep_state_checks=False))
    save(out/'PROJECTION_DISPATCH.json',dict(passed=True,formal_binaries_replaced=False,M2='NOT_RUN',
        scope='Supplemental fixed generation-cap8, k3/reserve4/q4 observer and clean formal-executable bridges, separate from primary timing',
        arms=[{k:x[k] for k in ('arm','projection_graph_nodes','packed_nodes','marked_loop4_nodes','q4_verify_projection_nodes','q4_wide_packing_active','independent_natural_qualification_verify_width_hist','aligned_short_diagnostic_may_coalesce_across_cuts','actual_graph_evidence_sha256','formal_bridge_receipt_sha256','observer_build_sha256','formal_build_sha256','observation_scope')} for x in dispatch],
        supplemental_requested_vectors=sum(len(x['numerical_bridge']['vectors']) for x in dispatch),supplemental_committed_states=sum(len(x['numerical_bridge']['states']) for x in dispatch)))
    save(out/'CLOCK_SUMMARY.json',dict(workers=clocks,window_overlap='Inclusive worker, wrapper, adapter, startup and burst windows overlap; never add them',
        per_arm={a:{k:sum(c[k] for c in clocks if c['arm']==a) for k in ('worker_wall_s','wrapper_wall_s','adapter_run_inclusive_s','test_burst_wall_s','launch_to_first_result_s','launch_to_first_test_result_s','model_load_s','pool_setup_s')} for a in plan['arms']},
        maximum_sampled_device_bytes=max(c['peak_observed_device_bytes'] for c in clocks)))
    save(out/'PHYSICAL_CENSUS.json',physical)
    for name in ('RESULTS.json','ALL_SLOT_STATUS.json','MEASUREMENT-COST-COVERAGE.json','PRIMER-COST-COVERAGE.json'):
        save(out/name,read(w/'panel-01'/name))
    print(json.dumps(dict(records=len(records),M1=totals(reserved),formal_totals=read(w/'panel-01/RESULTS.json')['totals'])),flush=True)

if __name__=='__main__':main()
