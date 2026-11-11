"""Analyze complete checked Linux worker records. Never pool Windows timings.

Input CHECKED records must be created by the host's independent endpoint/trace
adapter against the new Linux oracle; returncode zero alone is not qualification.
"""
import argparse, math
from pathlib import Path
import numpy as np
from common import need, read, save

def analyze(plan,records):
    workers={w['id']:w for w in plan['workers']};need(len(workers)==24,'24 fixed workers required')
    roots=plan['roots'];arms=plan['arms'];x=np.full((16,4,6),np.nan);seen=set();references=set();windows=[]
    for r in records:
        need(r['id'] in workers and r['id'] not in seen,'Unknown/duplicate worker');seen.add(r['id']);w=workers[r['id']]
        need(r['status']=='COMPLETE' and r['native_checks_passed'] is True,'Failed panel retained, no qualified-subset ranking')
        need(r['job_sha256']==w['job_sha256'],'Job differs from freeze');calls=r['requests'];need(len(calls)==18,'Two primers plus16 roots')
        wanted=w['primers']+w['roots'];need([q['root'] for q in calls]==wanted,'Request order changed')
        for q in calls:
            need(q['reference_compatible'] is True and q['trace_valid'] is True,'Missing independent native check')
            need(isinstance(q['service_s'],(int,float)) and math.isfinite(q['service_s']) and q['service_s']>0,'Invalid service clock')
            need(isinstance(q['reference_id'],str) and q['reference_id'],'Missing reference identity')
            references.add(q['reference_id'])
        for q in calls[2:]:x[roots.index(q['root']),w['session'],arms.index(w['arm'])]=q['service_s']
        clocks=r['actual_host_clocks']
        for key in ('launch_to_first_result_s','launch_to_first_test_result_s','test_burst_wall_s','worker_wall_s'):
            v=clocks.get(key);need(type(v) in (int,float) and math.isfinite(v) and v>0,'Missing actual host clock: '+key)
        need(clocks['launch_to_first_result_s']<=clocks['launch_to_first_test_result_s']<=clocks['worker_wall_s'] and clocks['test_burst_wall_s']<=clocks['worker_wall_s'],'Inconsistent host windows')
        windows.append({'id':r['id'],'clocks':clocks})
    need(seen==set(workers) and np.isfinite(x).all() and len(references)==1,'Incomplete or mixed-reference panel')
    y=x.sum(axis=1);idx=np.random.Generator(np.random.PCG64(plan['bootstrap_seed'])).integers(0,16,(plan['bootstrap_draws'],16));boot=y[idx].sum(axis=1)
    contrasts=[];alpha=.05/len(plan['primary'])
    for a,b in plan['primary']:
        i,j=arms.index(a),arms.index(b);rr=y[:,i]/y[:,j]
        contrasts.append({'numerator':a,'denominator':b,'total_ratio':float(y[:,i].sum()/y[:,j].sum()),
             'adjusted_interval':np.quantile(boot[:,i]/boot[:,j],[alpha/2,1-alpha/2]).tolist(),
             'per_root':rr.tolist(),'per_session':(x[:,:,i].sum(axis=0)/x[:,:,j].sum(axis=0)).tolist(),
             'equal_root_geometric':float(np.exp(np.log(rr).mean()))})
    return {'scope':'Independent Linux deployment; fixed exposed transfer inputs; root intervals conditional on4 shared sessions',
            'totals_s':dict(zip(arms,y.sum(axis=0).tolist())),'contrasts':contrasts,'host_windows':windows,'no_historical_timing_pooling':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('checked',type=Path);p.add_argument('out',type=Path);a=p.parse_args();save(a.out,analyze(read(a.plan),read(a.checked)))
