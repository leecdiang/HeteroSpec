"""Read-only protocol and raw-to-cost normative review, independent of model runners."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,csv,statistics,math
R=Path(__file__).parent
load=lambda n:json.loads((R/n).read_text(encoding='utf8'))
errors=[];checks=0
def ck(x,m):
 global checks;checks+=1
 if not x:errors.append(m)
assert not (R/'LOCK.json').exists()
counts=load('COUNTS.json');E=load('E_VERIFICATION.json');A=load('A_VERIFICATION.json');B=load('CAUSAL_RESULTS.json');C=load('C_VERIFICATION.json');D=load('D_VERIFICATION.json')
ck(counts['nonwarm_started']==312 and counts['nonwarm_complete']==311,'312 charged starts311 complete')
ck(counts['warm_started']==counts['warm_complete']==37 and counts['aux_started']==counts['aux_complete']==24,'all37 warm and24 auxiliary accounted')
ck(A['nonwarm']==48 and A['status']=='PASS','A historical and capture48 bridge')
ck(len(B['valid_independent_tasks'])==3 and B['cross_case_support'],'3 distinct valid causal cases')
ck(C['scientific_gate']=='PASS' and D['scientific_gate']=='PASS','12/12 development and112/112 exposed gate')
ck(E['complete']==119 and not E['matrix_complete'] and E['missing_units']==['E/FORMAL/1/old_N1/MBPP/400'],'preserved120 positions exactly one documented interruption')
ck(E['decision']=='PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED' and not E['efficiency_gate'],'partial cannot becomeGO')
for label in ['candidate','matched_target','ordinary_R']:
 xs=[x for x in E['rows'] if x['label']==label];ck(len(xs)==30 and all(x['qualified'] for x in xs),'all30 complete qualified '+label)
ck(not E['qualification_errors'],'full raw two-round stability')
manifest=load('E_MANIFEST.json');groups=manifest['formal_sessions'];ck([g['config']['label'] for g in groups[:4]]==list(reversed([g['config']['label'] for g in groups[4:]])),'fixed reversed conditions')
inputs=load('E_INPUTS.json');eligible=load('E_EXPOSURE_AUDIT.json')['eligible_ranked'];ck([i['id'] for i in inputs]==eligible[:15],'prospective15 static-hash tasks unchanged')
for i in inputs:ck(i['selection_hash']==hashlib.sha256((i['id']+'HeteroSpec-B570-mechanism-v1-confirm').encode()).hexdigest(),'fixed hash '+i['id'])
for f in ['native.cpp','target.cpp','phase.h']:
 text=(R/'candidate-front'/f).read_text(encoding='utf8');ck(all(w not in text for w in ['MBPP/','HumanEval/','R_reference','HISTORICAL_PARENTS','future_tape','HISTORICAL_EXPECTED']),'no task/oracle routing '+f)
raws=[json.loads(p.read_text(encoding='utf8')) for p in (R/'raw').glob('*/RESULT.json')];data={(v['task'],v['config']['label'],v['config']['round']):v for v in raws if v['unit_id'].startswith('E/FORMAL/') and not v['warm']}
costs=list(csv.DictReader((R/'E_COSTS.csv').open(encoding='utf8')))
ck(len(costs)==(15+15+14)*3,'full comparator cost rows, no hidden selective rows')
for row in costs:
 def value(label,round):
  r=data[row['task'],label,round];return r['host_seconds']*1000 if row['timer']=='host_end_to_end_ms' else r['metrics'][row['timer']]
 b=[value(row['baseline'],n) for n in [1,2]];c=[value('candidate',n) for n in [1,2]]
 for key,want in dict(baseline_round1_ms=b[0],baseline_round2_ms=b[1],candidate_round1_ms=c[0],candidate_round2_ms=c[1],baseline_median_ms=statistics.median(b),candidate_median_ms=statistics.median(c),speed_ratio=statistics.median(b)/statistics.median(c),round1_ratio=b[0]/c[0],round2_ratio=b[1]/c[1]).items():ck(math.isclose(float(row[key]),want,rel_tol=1e-12),'raw-derived '+row['task']+'/'+row['baseline']+'/'+row['timer']+'/'+key)
for summary in E['cost_summaries']:
 rows=[x for x in costs if x['baseline']==summary['baseline'] and x['timer']==summary['timer']];ck(len(rows)==summary['tasks'],'GM denominator '+summary['baseline']+'/'+summary['timer'])
 for key,col in [('GM','speed_ratio'),('round1_GM','round1_ratio'),('round2_GM','round2_ratio')]:ck(math.isclose(summary[key],math.exp(statistics.mean(math.log(float(x[col])) for x in rows)),rel_tol=1e-12),'independent GM '+key)
ck(load('INDEPENDENT_VERIFICATION.json')['status']=='PASS','main independent audit')
result=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,scientific_matrix='PARTIAL_INFRASTRUCTURE',delivery_closure='pending actual CAS and remote readback',all_authorized_remaining_slots_executed=True,no_model_requests=True,comparator_task_counts=dict(ordinary_R=15,matched_target=15,old_N1=14),phase_and_intervention_scope='complete path recipe and state effects; no unique kernel/attention cause',scope_limits=['frozenB570 Q8 Vulkan ctx1024 cap128 greedy','all56 old tasks exposed','15 accessible-project-unused tasks; not training unseen','rounds separated by overnight interruption; no stationary-environment or statistical claim','one charged incomplete request and unmeasured cleanup duration'])
(R/'NORMATIVE_REVIEW.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(result['status'],checks,errors[:10],flush=True)
if errors:raise SystemExit(1)
