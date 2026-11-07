"""Conditional costs for placement; not a GPU speed prediction or energy model."""
import argparse,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from experiment import read,save,require,coverage

def summarize(rows):
    out=[]
    for r in rows:
        s,p,d=(r.get(k) for k in ('service_s','target_prefill_s','draft_total_s'))
        f=r.get('draft_prefill_s')
        if any(x is None for x in (s,p,d,f)):
            out.append(dict(root=r['root'],status='UNMEASURED_COMPONENT',ideal_service_s=None));continue
        require(all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in (s,p,d,f)) and s>0 and f<=d<=s and p+d<=s+1e-9*max(1.,s),'Invalid disjoint cost inputs')
        overlap=min(p,f);ideal=s-overlap
        out.append(dict(root=r['root'],status='CONDITIONAL_FIXED_WORK',original_s=s,
            ideal_prefill_overlap_s=overlap,ideal_service_s=ideal,
            delete_all_draft_floor_s=s-d,two_dedicated_gpu_capacity_s=2*ideal,
            capacity_time_ratio=2*ideal/s,not_energy_joules=True))
    return dict(rows=out,coverage=coverage([r['ideal_service_s'] for r in out],len(rows)),
        assumptions='Same target/draft work and trajectories; no interference or transport cost; not a hardware measurement')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('costs');p.add_argument('out');a=p.parse_args();save(a.out,summarize(read(a.costs)['rows']))
