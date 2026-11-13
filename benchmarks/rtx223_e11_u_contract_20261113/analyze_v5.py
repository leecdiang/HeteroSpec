"""Pre-registered complete-pair analysis; no CUDA, filtering or synthetic samples."""
from pathlib import Path
import json,csv,math,statistics,random,datetime
p=Path(__file__).resolve().parent
stage=json.loads((p/'STAGING_V3.json').read_bytes());out=Path(stage['profile'])/'Temp/e11-timing-003'
native=json.loads((out/'result.json').read_bytes());assert native['status']=='PASS_E11_TWO_CONTRACTS'
assert native['explicit_prelaunch_charged']==392 and native['explicit_by_operation']==dict(B_quantizer=74,B_projection=122,U_quantizer=74,U_projection=122)
receipt=Path('D:/HeteroSpec-PC/rtx223-e11-u-contract/timing-003/attempt.jsonl')
assert json.loads(receipt.read_bytes().splitlines()[-1])['event']['kind']=='PASS'
assert len(native['post_batch_bitwise'])==48 and all(x['activation_exact'] and x['output_exact'] for x in native['post_batch_bitwise'])
samples=native['paired_timings'];assert len(samples)==48
with (p/'ALL_SAMPLES.csv').open('x',newline='',encoding='utf8') as f:
 writer=csv.DictWriter(f,fieldnames=list(samples[0]));writer.writeheader();writer.writerows(samples)
geomean=lambda v:math.exp(statistics.mean(math.log(x) for x in v))
def percentile(v,f):
 z=(len(v)-1)*f;a=int(z);b=min(a+1,len(v)-1);return v[a]*(b-z)+v[b]*(z-a) if a!=b else v[a]
def ci(ratios):
 rng=random.Random(20261113);logs=list(map(math.log,ratios));v=sorted(math.exp(sum(rng.choice(logs) for _ in logs)/len(logs)) for _ in range(10000));return [percentile(v,.025),percentile(v,.975)]
summary={};allpairs=[]
for mode in ['kernel-only','complete-operator']:
 pairs=[]
 for block in range(12):
  rows=[x for x in samples if x['mode']==mode and x['block']==block];assert len(rows)==2
  assert [x['arm'] for x in rows]==(['B','U'] if block%2==0 else ['U','B'])
  arms={x['arm']:x for x in rows};assert set(arms)=={'B','U'} and all(x['batch_repetitions']==5 and x['event_ms']>0 for x in rows)
  pair=dict(mode=mode,block=block,order=''.join(x['arm'] for x in rows),B_ms_per_operator=arms['B']['event_ms']/5,U_ms_per_operator=arms['U']['event_ms']/5,U_over_B=arms['U']['event_ms']/arms['B']['event_ms']);pairs.append(pair);allpairs.append(pair)
 ratios=[x['U_over_B'] for x in pairs];interval=ci(ratios);orders={order:geomean([x['U_over_B'] for x in pairs if x['order']==order]) for order in ['BU','UB']}
 byarm={}
 for arm in ['B','U']:
  v=[x[arm+'_ms_per_operator']*1000 for x in pairs];byarm[arm]=dict(all_microseconds=v,mean_microseconds=statistics.mean(v),median_microseconds=statistics.median(v),range_microseconds=[min(v),max(v)],sample_CV=statistics.stdev(v)/statistics.mean(v))
 stable=geomean(ratios)<1 and interval[1]<1 and sum(x<1 for x in ratios)>=10 and all(x<1 for x in orders.values())
 summary[mode]=dict(arms=byarm,pairs=pairs,U_over_B_geomean=geomean(ratios),U_time_change_percent=100*(geomean(ratios)-1),paired_log_bootstrap_95pct=interval,order_strata_geomeans=orders,U_faster_pairs=sum(x<1 for x in ratios),stable_exploratory_advantage=stable)
with (p/'ALL_PAIRS.csv').open('x',newline='',encoding='utf8') as f:
 writer=csv.DictWriter(f,fieldnames=list(allpairs[0]));writer.writeheader();writer.writerows(allpairs)
r=summary['complete-operator']['U_over_B_geomean'];lower,upper=summary['complete-operator']['paired_log_bootstrap_95pct']
required=lambda value,h=0:(.05+h)/(1-value) if value<1 else None
sensitivity=[]
for value in [.25,.5,.75,.8,.9,.95,.98,1.0]:
 for h in [0,.005,.01]:sensitivity.append(dict(assumed_r=value,assumed_h=h,required_f_for_5pct=required(value,h),feasible_with_f_at_most_1=required(value,h) is not None and required(value,h)<=1))
amdahl=dict(measured_r_different_contract=r,conditional_f_min_point=required(r),conditional_f_min_optimistic=required(lower),conditional_f_min_conservative=required(upper),same_request_f='NOT_MEASURED',same_request_h='NOT_MEASURED',actual_service_speedup='NOT_MEASURED',formula='new/old=1-f+f*r+h',sensitivity=sensitivity,coverage_examples=[dict(assumed_f=f,assumed_h=h,conditional_service_reduction_percent=100*(f*(1-r)-h)) for f in [.05,.1,.2,.33,.5,.75,1] for h in [0,.005,.01]],not_an_actual_cost_stack=True,legacy_preserving_candidate_speedup_not_established=True)
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS_EXTRACTED_DIFFERENT_CONTRACT_TIMING',summary=summary,amdahl=amdahl,resources=native['resources'],post_batch_checks=48,all_samples=48,actual_occupancy='NOT_MEASURED',L2_DRAM='NOT_MEASURED',full_backend_run='NOT_RUN',stable_in_both_boundaries=all(x['stable_exploratory_advantage'] for x in summary.values()),model_or_service=0,limits='single real first-layerq8 operand;PDL0,graphsOFF,resident arrays;events include possible host submission gaps;no full backend/defaultPDL/defaultgraph or service conclusion')
with (p/'ANALYSIS.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
with (p/'AMDAHL.json').open('x',encoding='utf8') as f:json.dump(amdahl,f,indent=2)
print(json.dumps(dict(stable=report['stable_in_both_boundaries'],ratios={k:v['U_over_B_geomean'] for k,v in summary.items()},full_r=r,conditional_required_f=required(r))))
