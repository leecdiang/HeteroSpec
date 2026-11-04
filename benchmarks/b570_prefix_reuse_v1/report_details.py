"""Supplementary, prespecified-cost reporting from completed raw slots only."""
from pathlib import Path
import collections, datetime, json, math, random, statistics, sys
from verify_raw import read, require

def percentile(v,p):
 v=sorted(v);x=(len(v)-1)*p;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)

def report(root):
 root=Path(root);panel=read(root/'panel.json');result=read(root/'results.json');policy=read(root/'policy.json')
 require(len(result['records'])==1024,'Complete main timing required')
 measured={(r['id'],r['session'],r['arm']):r['seconds'] for r in result['records'] if r['kind']=='measure'}
 arms=('QB','WB-cut','WB-rechunk','AUTO');fixed=arms[:3]
 byroot={a:[statistics.mean(measured[z['id'],s,a] for s in range(4)) for z in panel['test']] for a in arms}
 rng=random.Random(20261104);samples=[tuple(rng.randrange(32) for _ in range(32)) for _ in range(10000)]
 costs={};total=collections.Counter();dates=set();main=[]
 for u in sorted((root/'units').iterdir()):
  b=read(u/'BUDGET.json');n=read(u/'native/result.json');r=read(u/'RECEIPT.json');g=costs.setdefault(b['stage'],collections.Counter())
  vals=dict(reserved_requests=b['requests'],completed_records=len(n['records']),owned_seconds=r['owned_seconds'],model_load_seconds=n.get('load_seconds',0),cache_preload_seconds=n.get('cache_preload_seconds',0))
  for v in n['records']:
   vals['prefix_construction_seconds']=vals.get('prefix_construction_seconds',0)+v.get('prefix_construction_seconds',0)
   if 'slot' in v:
    k=v['slot'].get('schedule',{}).get('kind','qualification_or_development')
    vals[k+'_service_seconds']=vals.get(k+'_service_seconds',0)+v['seconds']
    vals['import_bytes']=vals.get('import_bytes',0)+v.get('import_bytes',0)
    vals['cache_hit_requests']=vals.get('cache_hit_requests',0)+(v['slot']['cache_key']!='empty')
    vals['cache_miss_requests']=vals.get('cache_miss_requests',0)+(v['slot']['cache_key']=='empty')
    if u.name.startswith('main-timing-session-'):main.append(v)
  g.update(vals);total.update(vals)
  if u.name.startswith('main-timing-session-'):dates.add(datetime.datetime.fromisoformat(b['utc']).astimezone(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat())
 ccal=policy['calibration_total_seconds'];break_even=[]
 for a in fixed:
  delta=[b-t for b,t in zip(byroot[a],byroot['AUTO'])];mean=statistics.mean(delta)
  boot=[sum(delta[i] for i in idx)/32 for idx in samples];lo,hi=percentile(boot,.025),percentile(boot,.975)
  break_even.append(dict(baseline=a,observed_mean_service_saving_seconds=mean,secondary_root_bootstrap95_saving_seconds=[lo,hi],calibration_seconds=ccal,break_even_cache_hits=ccal/mean if mean>0 else None,secondary95_break_even_range=[ccal/hi,ccal/lo if lo>0 else None] if hi>0 else None,uncertainty_includes_nonpositive_savings=lo<=0,actual_AUTO_measurements=128,actual_AUTO_service_requests_including_warmups=256,unlimited_future_reuse_assumed=False))
 fixed_contrasts=[]
 for a in fixed[1:]:
  logs=[statistics.mean(math.log(measured[z['id'],s,'QB']/measured[z['id'],s,a]) for s in range(4)) for z in panel['test']]
  fixed_contrasts.append(dict(arm=a,QB_over_arm=math.exp(statistics.mean(logs)),session_QB_over_arm=[math.exp(statistics.mean(math.log(measured[z['id'],s,'QB']/measured[z['id'],s,a]) for z in panel['test'])) for s in range(4)],descriptive_only=True))
 aligned=[]
 for a in fixed:
  ts=[r['seconds'] for r in read(root/'ALIGNED_TIMING.json') if r['slot']['arm']==a and r['slot']['schedule']['kind']=='measure']
  require(len(ts)==16,'Aligned control incomplete')
  aligned.append(dict(arm=a,measurements=len(ts),geometric_seconds=math.exp(statistics.mean(map(math.log,ts))),median_seconds=statistics.median(ts),descriptive_p95_seconds=percentile(ts,.95)))
 return dict(costs_by_stage=costs,total_costs=total,calibration_window_seconds=ccal,cost_warning='Native service/load/preload/producer are components of owned wall time, not additional independent totals. Calibration window overlaps owned costs and includes orchestration and earlier epochs.',primary_cache_hit_requests=sum(r['slot']['cache_key']!='empty' for r in main),primary_service_requests=len(main),primary_import_bytes=sum(r['import_bytes'] for r in main),main_session_dates_Asia_Shanghai=sorted(dates),cross_date_inference=len(dates)>1,break_even=break_even,descriptive_fixed_contrasts=fixed_contrasts,aligned_empty_cache_control=aligned,phase_timing='Clean main slots do not activate phase observers; zero-valued phase fields mean unmeasured, not zero overhead. Separate development phase controls are retained.',dispatch_mask_join_costs='Not independently timed in clean main; native graph-call counts and separate development traces retained. No zero-cost or general graph-cache-reuse claim.')

if __name__=='__main__':print(json.dumps(report(sys.argv[1]),indent=2))
