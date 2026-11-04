#!/usr/bin/env python3
"""CPU-only QB sensitivity. No inference, GPU, network, writes to source, or causal claim.

Input is PR179 draft_reuse_research/source_projection.json at 224d928...,
whose bytes are pinned. Target savings are removed on BOTH sides. Fractions
are assumed removable elapsed-time fractions, not token-LCP or cache hit rates.
"""
import argparse, collections, hashlib, json, math
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)

PIN = '22e622cf1f69abe953a810069ebaf48b8bdadd90747225ac923e260ab8c3e340'

def costs(r, target_removed=0., draft_removed=0., delta_h=0.):
    # delta_h is added candidate cost minus baseline overhead; negative allowed.
    require(0 <= target_removed <= 1 and 0 <= draft_removed <= 1, "Removal fraction outside [0,1]")
    m = r['M'] - target_removed*r['M_target_prefill']
    c = r['C'] - target_removed*r['C_target_prefill'] - draft_removed*r['C_draft_prefill'] + delta_h
    require(m > 0 and c > 0, "Nonpositive counterfactual duration")
    return m, c

def aggregate(rows, s, f, h=0.):
    pairs=[costs(r,s,f,h) for r in rows]
    m=sum(x for x,y in pairs); c=sum(y for x,y in pairs)
    return {'target_phase_removed_fraction':s, 'draft_phase_removed_fraction':f,
            'candidate_minus_baseline_extra_seconds_per_request':h,
            'M_sum_s':m, 'C_counterfactual_sum_s':c, 'C_over_M_ratio_of_sums':c/m,
            'strict_winning_blocks':sum(y<x for x,y in pairs),
            'blocks':len(rows), 'saving_seconds_per_request':(m-c)/len(rows)}

def thresholds(rows,s,desired_reduction=0.,h=0.):
    pairs=[costs(r,s,0) for r in rows]
    m=sum(x for x,y in pairs); c=sum(y for x,y in pairs)
    p=sum(r['C_draft_prefill'] for r in rows)
    f=(c-(1-desired_reduction)*m+len(rows)*h)/p
    return {'target_phase_removed_fraction':s, 'desired_reduction_vs_M':desired_reduction,
            'candidate_minus_baseline_extra_seconds_per_request':h,
            'required_draft_phase_removal_fraction_strictly_greater_than':f,
            'feasible_under_fixed_components':f<1,
            'extra_overhead_budget_after_full_removal_seconds_per_request':((1-desired_reduction)*m-c+p)/len(rows)}

def overlap(rows,s):
    mm=[]; cc=[]; savings=[]
    for r in rows:
        m,c=costs(r,s,0)
        # Hypothetical perfect overlap of remaining phases, no contention.
        save=min((1-s)*r['C_target_prefill'],r['C_draft_prefill'])
        mm.append(m);cc.append(c-save);savings.append(save)
    return {'target_phase_removed_fraction':s,'M_sum_s':sum(mm),
            'C_ideal_overlap_sum_s':sum(cc),'C_over_M_ratio_of_sums':sum(cc)/sum(mm),
            'maximum_hidden_startup_s':sum(savings),
            'strict_winning_blocks':sum(c<m for c,m in zip(cc,mm))}

def test():
    r={'M':10.,'C':12.,'M_target_prefill':4.,'C_target_prefill':4.,'C_draft_prefill':3.}
    require(costs(r,1,0)==(6.,8.), "Accounting self-check failed")
    require(costs(r,1,1)==(6.,5.), "Accounting self-check failed")
    require(math.isclose(thresholds([r],0)['required_draft_phase_removal_fraction_strictly_greater_than'],2/3), "Accounting self-check failed")
    require(overlap([r],1)['maximum_hidden_startup_s']==0, "Accounting self-check failed")
    require(math.isclose(overlap([r],0)['C_ideal_overlap_sum_s'],9.), "Accounting self-check failed")
    require(math.isclose(thresholds([r],1,.1)['required_draft_phase_removal_fraction_strictly_greater_than'],2.6/3), "Accounting self-check failed")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('projection',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); test()
    raw=args.projection.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN, 'Input differs from pinned projection')
    p=json.loads(raw);rows=[r for r in p['rows'] if r['scope']=='QB']
    require(len(rows)==96 and len({tuple(r['key']) for r in rows})==96, 'QB coverage mismatch')
    result={'warning':'Descriptive accounting counterfactual only. All other costs held fixed; not a deployment measurement or causal prediction. Equal target phase removal is an assumption, not evidence of natural cache hits. Repeated inputs are not independent workloads.',
            'projection_sha256':PIN,'reproduction_self_tests':'PASS','family':{}}
    for family in ('Qwen','SmolLM2'):
        rr=[r for r in rows if r['key'][0]==family]
        result['family'][family]={'blocks':len(rr),'unique_exposed_inputs':len({r['key'][3] for r in rr}),
            'grid':[aggregate(rr,s,f,h) for s in (0.,.5,1.) for f in (0.,.5,.75,1.) for h in (0.,.01)],
            'thresholds':[thresholds(rr,s,d,h) for s in (0.,1.) for d in (0.,.03) for h in (0.,.01)],
            'ideal_overlap':[overlap(rr,s) for s in (0.,.5,1.)],
            'session_thresholds':[dict(date_slot=ds,session_slot=ss,**thresholds([r for r in rr if r['key'][1:3]==[ds,ss]],0.,d)) for ds,ss in ((1,0),(1,1),(2,0),(2,1)) for d in (0.,.03)]}
    require(args.output.resolve()!=args.projection.resolve(), 'Do not overwrite source')
    with args.output.open('x') as f: json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
