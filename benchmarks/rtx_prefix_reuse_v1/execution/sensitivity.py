"""Aggregate only the pre-output descriptor scenarios on the fixed leaf cohort."""
from analyze import *

def main():
    old=read(ROOT/'descriptor-census.json');actual=read(ROOT/'common-census.json');panel=read(ROOT/'common-panel.json')
    leaf={x['id'] for x in actual['eligible']};rows=[r for r in old['rows'] if r['id'] in leaf];assert len(rows)==6423
    summaries=[]
    for g in (1,16,32,64):
        eligible=[r for r in rows if r['logical_lcp']//g*g>0];total=sum(r['scenarios'][str(g)]['QB'] for r in eligible);cross=sum(r['scenarios'][str(g)]['crossed_qb_calls'] for r in eligible)
        x=dict(granule=g,scenario_only=g!=1,paths_seen=len(rows),eligible_paths=len(eligible),eligible_roots=len({r['root_id'] for r in eligible}),lost_reuse_paths=len(rows)-len(eligible),crossed_paths=sum(r['scenarios'][str(g)]['crossed_qb_calls']>0 for r in eligible),qb_calls=total,crossed_qb_calls=cross,crossed_call_fraction=cross/total)
        for split in ('calibration','test'):
            ids={r['id'] for r in panel[split]};chosen=[r for r in eligible if r['id'] in ids]
            x[split]=dict(frozen_paths=len(ids),eligible_paths=len(chosen),crossed_paths=sum(r['scenarios'][str(g)]['crossed_qb_calls']>0 for r in chosen),qb_calls=sum(r['scenarios'][str(g)]['QB'] for r in chosen))
        summaries.append(x)
    assert summaries[0]['crossed_paths']==actual['crossed_requests'] and summaries[0]['qb_calls']==actual['qb_calls']
    assert summaries[2]['crossed_paths']==summaries[3]['crossed_paths']==0
    put(ROOT/'SENSITIVITY_REPORT.json',dict(source_descriptor_sha256=sha(ROOT/'descriptor-census.json'),fixed_panel_sha256=sha(ROOT/'common-panel.json'),native_actual_census_sha256=sha(ROOT/'common-census.json'),scope='Predeclared output-free granularity scenarios, aggregated from original pre-output descriptors. Granule1 is the native deployment; others are hypothetical dense floor-LCP policies, not observations of another engine. Same fixed 12/32 panel; no re-ranking, native execution or outcome input.',scenarios=summaries))
    print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
