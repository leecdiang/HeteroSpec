"""Separate completed-call and first-input phase-sum views; not relabeled graph data."""
import argparse,collections,csv,math,statistics
from common import load,save
from analyze import summarize,average_pairs
from study import ARMS

def analyze_views(plan_path,host_path,out):
    plan=load(plan_path);cases={c['case_id']:c for c in plan['cases']}
    with open(host_path,newline='',encoding='utf-8') as f:hosts=list(csv.DictReader(f))
    rows=[]
    for stage in ['confirm','holdout']:
        for view,column in [('resident_call','completed_call_mean_us'),('input_inclusive_first_call_phase_sum','input_inclusive_first_call_phase_sum_us')]:
            groups=collections.defaultdict(dict)
            for h in hosts:
                if h['stage']==stage and h['numerical_qualified']=='True' and h.get('environment_qualified')=='True':groups[h['case_id'],int(h['block'])][h['arm']]=h
            pairs=collections.defaultdict(list)
            for (cid,b),arms in groups.items():
                if set(arms)!=set(ARMS):continue
                for label,x,y in [('AA','QB_A','QB_B'),('QB_QH','QB_A','QH_C'),('QB_QH_alt','QB_B','QH_C'),('PQ_QB','PQ','QB_A'),('PQ_QB_alt','PQ','QB_B')]:
                    a,z=float(arms[x][column]),float(arms[y][column]);pairs[cid,label].append(dict(block=b,session=f'{stage}-session{b//4}',log_ratio=math.log(a/z),difference_us=a-z))
            geom={}
            selected=[c for c in plan['cases'] if c['cohort']==('confirmation' if stage=='confirm' else 'holdout')]
            for gid in sorted({c['geometry_id'] for c in selected}):
                cc=[c['case_id'] for c in selected if c['geometry_id']==gid]
                for label in ['AA','QB_QH','QB_QH_alt','PQ_QB','PQ_QB_alt']:
                    pp=average_pairs([pairs.get((cid,label),[]) for cid in cc]);geom[gid,label]=pp
                    rows.append(dict(stage=stage,cost_view=view,scope='geometry',geometry=gid,comparison=label,summary=summarize(pp)))
            for subset in ['q1','q>1']:
                gids=sorted({c['geometry_id'] for c in selected if (c['q']==1 if subset=='q1' else c['q']>1)})
                if not gids:continue
                for label in ['AA','QB_QH','QB_QH_alt','PQ_QB','PQ_QB_alt']:
                    pp=average_pairs([geom.get((gid,label),[]) for gid in gids]);rows.append(dict(stage=stage,cost_view=view,scope='full_panel_'+subset,comparison=label,summary=summarize(pp)))
    save(out,dict(rows=rows,resident_call='host mean over30 completed calls,includes ordinary readback',input_inclusive='one first-warmup phase sum per host;not30 independent inclusive samples;source read/cold init/allocation separate',session_labels='cost aggregation follows actual session grouping already verified by primary raw exporter',inference='descriptive block-stratified bootstrap;no process wall as kernel time'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--hosts',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();analyze_views(a.plan,a.hosts,a.out)
