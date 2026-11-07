"""Exploratory factor consistency and alternate-QB sensitivity, CPU only.

Rule fixed before confirmation: show both value modes and both sessions; no p-value
selection. A/A-adjusted edge screen is descriptive, not a calibrated inference.
"""
import argparse,math,statistics
from common import load,save
from analyze import summarize
from export_rtx import rows_csv

def review(plan,result,out):
    plan=load(plan);a=load(result);geoms={(x['stage'],x['geometry_id']):x for x in a['geometry_summaries']};cases={(x['stage'],x['case_id']):x for x in a['case_summaries']};rows=[]
    for edge in plan['factor_edges']:
        if ('confirm',edge['base']) not in geoms or ('confirm',edge['changed']) not in geoms:continue
        effects={}
        for label in ['AA','QB_QH','QB_QH_alt','PQ_QB','PQ_QB_alt']:
            x={p['block']:p for p in geoms['confirm',edge['base']]['comparisons'][label]['pairs']};y={p['block']:p for p in geoms['confirm',edge['changed']]['comparisons'][label]['pairs']};pairs=[dict(block=b,session=y[b]['session'],log_ratio=y[b]['log_ratio']-x[b]['log_ratio'],difference_us=y[b]['difference_us']-x[b]['difference_us']) for b in sorted(x.keys()&y.keys())];effects[label]=summarize(pairs)
        for label,alt in [('QB_QH','QB_QH_alt'),('PQ_QB','PQ_QB_alt')]:
            directions=[];values=[]
            for mode in [0,1]:
                x={p['block']:p for p in cases['confirm',edge['base']+f'-v{mode}']['comparisons'][label]['pairs']};y={p['block']:p for p in cases['confirm',edge['changed']+f'-v{mode}']['comparisons'][label]['pairs']}
                for cycle in [0,1]:
                    zz=[y[b]['log_ratio']-x[b]['log_ratio'] for b in sorted(x.keys()&y.keys()) if b//4==cycle]
                    value=statistics.mean(zz) if len(zz)==4 else None;values.append(dict(realization=mode,cycle=cycle,log_effect=value));directions.append(1 if value is not None and value>0 else -1 if value is not None and value<0 else 0)
            effect,alternate,aa=effects[label],effects[alt],effects['AA'];complete=all(x['n_blocks']==8 and x['sessions']==2 for x in [effect,alternate,aa]);consistent=complete and len(set(directions))==1 and directions[0]!=0
            noise=max(abs(x) for x in aa['log_interval']) if aa['log_interval'] else None;cut=math.log(1.02)+noise if noise is not None else None
            larger=complete and ((all(x['log_interval'][0]>cut for x in [effect,alternate])) or (all(x['log_interval'][1]<-cut for x in [effect,alternate])))
            rows.append(dict(**edge,comparison=label,geometry_log_effect_ratio=effect['ratio'],log_interval=effect['log_interval'],alternate_QB_effect_ratio=alternate['ratio'],AA_effect_ratio=aa['ratio'],AA_log_interval=aa['log_interval'],consistent_all_value_modes_sessions=consistent,mode_cycle_effects=values,larger_than_AA_plus2percent_heuristic=bool(larger),exploratory_multiple_comparisons=True))
    rows_csv(out,rows);return rows
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--analysis',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();review(a.plan,a.analysis,a.out)
