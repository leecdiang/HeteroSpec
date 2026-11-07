"""Lead's vectorized check from canonical processed CSV, independent of ZIP helper."""
from pathlib import Path
import hashlib,json,zipfile,math
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
CSV=REPO/'analysis/358h_phase3_prompt_summary.csv'
ZIP=REPO/'paper/mlsys2027/manuscript/output/anonymous-evidence-index-v0.8.8.zip'
csv=pd.read_csv(CSV)
assert len(csv)==180 and not csv.duplicated(['task_id','repetition','condition']).any()
result={'status':'PASS','scope':'Post-study retained-record analysis; no new model execution or interval',
        'canonical_source_SHA256':hashlib.sha256(CSV.read_bytes()).hexdigest(),
        'scientific_ZIP_SHA256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),'358H':{}}
agent=json.loads((HERE/'acceptance_diagnostic.json').read_bytes())
for name in ['CPU','NPU']:
    df=csv[csv.condition.eq(name+'_DRAFT_K2')].copy()
    assert len(df)==90 and df.groupby('task_id').size().eq(3).all()
    for key in ['baseline_end_to_end_ms','verification_ms','end_to_end_ms']:
        assert (df[key]>0).all()
    assert (df[['draft_replay_proposal_ms','orchestration_residual_ms']]>=0).all().all()
    assert np.max(np.abs(df.verification_ms+df.draft_replay_proposal_ms+df.orchestration_residual_ms-df.end_to_end_ms))<.01
    df['ceiling']=df.baseline_end_to_end_ms/df.verification_ms
    df['actual']=df.baseline_end_to_end_ms/df.end_to_end_ms
    g=df.groupby('task_id')[['ceiling','actual']].median()
    assert len(g)==30 and (g.actual<=g.ceiling).all()
    upper=float(np.exp(np.log(g.ceiling).mean()))
    observed=float(np.exp(np.log(g.actual).mean()))
    pooled=float(df.baseline_end_to_end_ms.sum()/df.verification_ms.sum())
    assert abs(upper-agent['358H'][name]['new_prompt_gm_upper_bound'])<1e-14
    assert abs(observed-agent['358H'][name]['original_prompt_gm_recomputed'])<1e-14
    assert abs(pooled-agent['358H'][name]['total_time_bound_recomputed'])<1e-14
    result['358H'][name]={'observed_prompt_GM':observed,'prompt_GM_ceiling':upper,'pooled_total_ceiling':pooled,
       'prompt_medians_at_or_above_one':int(g.ceiling.ge(1).sum()),'individual_runs_at_or_above_one':int(df.ceiling.ge(1).sum()),
       'maximum_prompt_median':float(g.ceiling.max()),'minimum_uniform_target_work_reduction_prompt_GM':1-upper,
       'minimum_target_work_reduction_pooled_total':1-pooled,'all_agent_prompt_bounds_max_absolute_difference':float(max(abs(g.loc[t,'ceiling']-v) for t,v in agent['358H'][name]['prompt_bounds'].items()))}
with zipfile.ZipFile(ZIP) as z:
    b=json.loads(z.read('evidence/B570_original_H1.json'))
    cases=[]
    for r in b['rows']:
        assert r['arrays']['prediction']==r['arrays']['live']
        if r['repetition']!=1:continue
        ref=np.asarray(r['arrays']['reference']);live=np.asarray(r['arrays']['live'])
        assert len(ref)==len(live)==128
        mask=ref!=live
        if mask.any():
            first=int(np.flatnonzero(mask)[0]);assert mask[first:].all()
            cases.append({'task':r['task_id'],'first_index':first,'nonreference_ids_predicted':int(mask.sum()),'after_first_nonreference_ids_predicted':int(mask.sum()-1)})
    assert len(cases)==4
    result['B570']={'prompt_units':24,'distinct_divergent_prompts':4,'cases':cases,'nonreference_ids_predicted':sum(x['nonreference_ids_predicted'] for x in cases),'strictly_after_first':sum(x['after_first_nonreference_ids_predicted'] for x in cases),'not_independent_samples':True}
    v=json.loads(z.read('evidence/RTX_V4.json'))
    case_rows=[];covered_by_either=0
    for r in v['A']:
        if r['repetition']!=1:continue
        c=r['conditions'];ref=c['A_REFERENCE_UB1']['ids'];ub=c['A_TARGET_ONLY_UB2']['ids'];live=c['A_NATIVE_BATCHED_LIVE']['ids']
        assert c['A_H2_P_R']['ids']==c['A_R_ONLY']['ids']==live
        covered_by_either+=int(ref==live or ub==live)
        if ref!=live or ub!=live:
            case_rows.append({'task':r['task_id'],'lengths':{'reference':len(ref),'UB2':len(ub),'live':len(live)},'reference_matches':ref==live,'UB2_matches':ub==live,'reference_equals_UB2':ref==ub,
               'reference_common_extent_differences':int(np.count_nonzero(np.asarray(ref[:min(len(ref),len(live))])!=np.asarray(live[:min(len(ref),len(live))]))),
               'UB2_common_extent_differences':int(np.count_nonzero(np.asarray(ub[:min(len(ub),len(live))])!=np.asarray(live[:min(len(ub),len(live))])))})
    result['RTX']={'tasks':19,'distinguishing_cases':case_rows,'retrospective_selection_of_two_full_target_only_arrays_covers':covered_by_either,'retrospective_selection_is_not_predictor':True}
oracle=agent['M4']['always_over_two_fixed_mode_oracle_gm']
result['M4']={'two_measured_fixed_mode_GM_maximum_relative_latency_reduction':1-1/oracle,'not_arbitrary_switching_bound':True}
(HERE/'LEAD_RECOMPUTATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'358H':result['358H'],'B570_nonreference_ids':result['B570']['nonreference_ids_predicted'],'RTX_retrospective_either_target_only':covered_by_either,'M4':result['M4']}))
