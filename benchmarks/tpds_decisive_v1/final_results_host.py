"""Complete-panel analysis with separately accounted full campaign costs."""
from build_host import *
from analyze import analyze,quantile
import statistics

def main():
    here=Path(__file__).resolve().parent;costs=json.loads((here/'host_evidence/UNIFIED_COSTS.json').read_bytes());f=json.loads((ROOT/'O-FREEZE.json').read_bytes());records=json.loads((ROOT/'O-MAIN-RECORDS.json').read_bytes());original=json.loads((ROOT/'O-MAIN-ANALYSIS.json').read_bytes());assert len(records['records'])==432
    def group(prefix):
        rows=[r for r in costs['native'] if r['attempt'].startswith(prefix)]
        return dict(attempts=len(rows),reserved={k:sum(r['reserved'][k] for r in rows) for k in ('requests','token_rows','operators')},actual_work={k:sum(r.get('actual_work',{}).get(k,0) for r in rows) for k in ('requests','token_rows','operators')},host_attempt_wall_s=sum(r.get('host_exit',{}).get('seconds',0) for r in rows),model_load_s=sum(r.get('model_load_seconds_once') or r.get('result.json',{}).get('model_load_seconds',0) for r in rows),pool_setup_s=sum(r.get('pool_setup_seconds_once') or r.get('result.json',{}).get('provision_seconds',0) for r in rows),post_service_state_s=sum(s['seconds'].get('post_service_state_seconds',0) for r in rows for s in r.get('slot_costs',[])))
    campaign=dict(all_stage_reserved_total=costs['reserved_total'],all_stage_known_work_lower_bound=costs['known_work_lower_bound_including_completed_failed_slots'],all_stage_host_attempt_wall_s=costs['host_attempt_wall_seconds'],all_stage_known_service_seconds_lower_bound=costs['known_complete_and_failed_slot_service_seconds_lower_bound'],main_pairs=group('O-main-s'),independent_original_references=group('O-main-original-'),independent_forced_references=group('O-main-forced-'),measurement_service_s=sum(r['service_s'] for r in records['records'] if r['kind']=='measure'),warmup_service_s=sum(r['service_s'] for r in records['records'] if r['kind']=='warmup'),elapsed_stage_spans=json.loads((ROOT/'ELAPSED_STAGE_SPANS.json').read_bytes()),nonadditive_note='Service, loading, pool setup, state diagnostics and attempt wall are nested. Calendar spans include outer CPU checks/archives/repair gaps and may overlap; do not sum them with components.',unknown_failed_work_attempts=costs['actual_work_unresolved_attempts'])
    augmented=dict(records,campaign_costs=campaign);result=analyze(f['panel'],'rtx-operator',augmented)
    assert {k:v for k,v in result.items() if k!='campaign_costs'}=={k:v for k,v in original.items() if k!='campaign_costs'},'CPU accounting must not change frozen statistical results'
    put(ROOT/'O-MAIN-ANALYSIS-WITH-COSTS.json',result)
    arms=[]
    for arm in ('graph_tiles','backend_loop4','packed'):
        rows=[r for r in records['records'] if r['arm']==arm and r['kind']=='measure'];assert len(rows)==72
        arms.append(dict(arm=arm,measurements=len(rows),service_total_s=sum(r['service_s'] for r in rows),service_mean_s=statistics.mean(r['service_s'] for r in rows),service_p95_descriptive_s=quantile([r['service_s'] for r in rows],.95),prefill_total_s=sum(r['prefill_wall_s'] for r in rows),prefill_mean_s=statistics.mean(r['prefill_wall_s'] for r in rows)))
    strong=next(c for c in result['contrasts'] if c['numerator']=='backend_loop4' and c['denominator']=='packed')
    put(ROOT/'FINAL_DISPOSITION.json',dict(D='CLOSED_NEGATIVE_FROZEN_PANEL_INVALIDATED',O='COMPLETE_12_ROOT_6_SESSION_3_ARM_PANEL',O_measurements=216,O_warmups=216,O_all432_final_states_and_frontiers_equal=True,strongest_control=strong,primary_stable_superiority_supported=strong['geometric_family95'][0]>1,total_service_secondary_positive_signal=strong['total_family95'][0]>1,interpretation='Packed has a small favorable point estimate against loop4, but the prespecified primary family-adjusted root-cluster interval includes1. The total-service interval excludes1. Retain this estimator dependence, two unfavorable roots and two unfavorable sessions; no equivalence claim and no stable primary superiority claim. Loop4 explains much of the larger graph-tiles gap.',arms=arms,costs=campaign,prior_AUTO_null_preserved=True,no_WB_rescue_panel=True,no_new_D_cohort_or_target_policy=True,RTX_GPU_work_stopped=True,no_B570_or_manuscript_changes=True))
    print(json.dumps(dict(arms=arms,main_costs=campaign['main_pairs'],warmup_s=campaign['warmup_service_s'],measure_s=campaign['measurement_service_s']),indent=2),flush=True)

if __name__=='__main__':main()
