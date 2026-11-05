"""Paired natural-service analysis. Complete panels only, root-cluster uncertainty."""
from __future__ import annotations
import argparse,math,random,statistics
from pathlib import Path
from common import need,read,digest,positive,write_new
from design import schedule

def quantile(xs,p):
    ys=sorted(xs);a=(len(ys)-1)*p;i=int(a);f=a-i
    return ys[i]*(1-f)+ys[min(i+1,len(ys)-1)]*f

def analyze(panel:dict,lane:str,records:dict,draws:int=10000)->dict:
    need(type(draws) is int and 100<=draws<=1000000,'bootstrap draws')
    sched=schedule(panel,lane);expected={s['slot']:s for s in sched['slots']}
    need(records['panel_sha256']==digest(panel),'panel drift')
    need(records['lane']==lane,'lane drift')
    need(records['frozen_before_test'] is True,'not prospective')
    need(records['qualification_status']=='FINITE_NATIVE_CAPTURE_MATCH','missing numerical qualification')
    rows=records['records'];need(len(rows)==len(expected),'incomplete or duplicate slots')
    found={}
    for r in rows:
        sid=r['slot'];need(sid in expected and sid not in found,'unknown or repeated slot')
        e=expected[sid]
        for k in ('root_id','input_id','session','period','arm','kind'):need(r[k]==e[k],'schedule drift: '+k)
        need(r['status']=='COMPLETE' and r['endpoint_equal'] is True,'failed/incompatible slot; no qualified aggregate')
        need(r.get('fallback_count')==0,'fallback in measured method')
        need(r['source_freeze_sha256']==records['source_freeze_sha256'],'code changed within panel')
        need(r['numeric_profile_sha256']==records['numeric_profile_sha256'],'target profile drift')
        positive(r['service_s'],'invalid service time')
        for k in ('setup_s','guard_s','restore_s','verification_s','draft_prefill_s','state_commit_s'):
            if k in r and r[k] is not None:
                need(type(r[k]) in (int,float) and math.isfinite(r[k]) and r[k]>=0,'invalid measured component')
        found[sid]=r
    need(set(found)==set(expected),'missing slots')
    arms=sched['arms'];roots=[x['root_id'] for x in panel['test']];sessions=sched['sessions']
    index={(r['root_id'],r['session'],r['arm'],r['kind']):r for r in rows}
    # All arms must produce the same autonomous reference endpoint on each input.
    for root in roots:
        outputs={index[(root,s,a,k)]['endpoint_sha256'] for s in range(sessions) for a in arms for k in ('warmup','measure')}
        need(len(outputs)==1,'endpoint differs across arms/repetitions')
    primary='paired_geometric_ratio' if lane=='rtx-operator' else 'total_service_ratio'
    contrasts=[];m=len(arms)*(len(arms)-1)//2;alpha=.05/m
    rng=random.Random(20261105);indices=[[rng.randrange(len(roots)) for _ in roots] for _ in range(draws)]
    for ai,a in enumerate(arms):
        for b in arms[ai+1:]:
            at=[];bt=[];logs=[];diff=[]
            for root in roots:
                av=[index[(root,s,a,'measure')]['service_s'] for s in range(sessions)]
                bv=[index[(root,s,b,'measure')]['service_s'] for s in range(sessions)]
                at.append(sum(av));bt.append(sum(bv));logs.append(statistics.mean(math.log(x/y) for x,y in zip(av,bv)))
                diff.append(statistics.mean(x-y for x,y in zip(av,bv)))
            g=math.exp(statistics.mean(logs));t=sum(at)/sum(bt)
            gb=[math.exp(sum(logs[j] for j in ix)/len(ix)) for ix in indices]
            tb=[sum(at[j] for j in ix)/sum(bt[j] for j in ix) for ix in indices]
            sb=[sum(diff[j] for j in ix)/len(ix) for ix in indices]
            contrasts.append({'numerator':a,'denominator':b,'ratio_gt_1_favors':b,
                'paired_geometric_ratio':g,'total_service_ratio':t,
                'geometric_family95':[quantile(gb,alpha/2),quantile(gb,1-alpha/2)],
                'total_family95':[quantile(tb,alpha/2),quantile(tb,1-alpha/2)],
                'mean_paired_seconds_a_minus_b':statistics.mean(diff),
                'paired_seconds95':[quantile(sb,.025),quantile(sb,.975)],
                'roots_favoring_denominator':sum(x>0 for x in logs),
                'root_ratios':[{'root_id':k,'ratio':math.exp(v)} for k,v in zip(roots,logs)],
                'session_ratios':[math.exp(statistics.mean(math.log(index[(root,s,a,'measure')]['service_s']/index[(root,s,b,'measure')]['service_s']) for root in roots)) for s in range(sessions)]})
    costs=records.get('campaign_costs',{})
    return {'status':'COMPLETE_PAIRED_PANEL','lane':lane,'primary':primary,'contrasts':contrasts,
            'independent_roots':len(roots),'sessions':sessions,'measurements':len(rows)//2,'warmups':len(rows)//2,
            'all_contrasts_family_alpha':.05,'bootstrap_draws':draws,'cluster':'root; all paired sessions retained',
            'best_fixed_by_primary':min(arms,key=lambda a:sum(index[(r,s,a,'measure')]['service_s'] for r in roots for s in range(sessions))) if primary=='total_service_ratio' else min(arms,key=lambda a:sum(math.log(index[(r,s,a,'measure')]['service_s']) for r in roots for s in range(sessions))),
            'campaign_costs':costs,'no_equivalence_claim':True,'cross_platform_pooling':False,
            'interpretation':'No automatic accept or speedup decision. Negative results and practical cost remain material.'}

def threshold(C,P,B,epsilon=0.0,overhead=0.0):
    positive(C,'C');positive(P,'P');positive(B,'B')
    need(P<=C and 0<=epsilon<1 and overhead>=0,'counterfactual domain')
    den=P+(1-epsilon)*B-C-overhead
    return None if den<=0 else P/den

def main():
    p=argparse.ArgumentParser();p.add_argument('panel',type=Path);p.add_argument('records',type=Path);p.add_argument('out',type=Path);p.add_argument('--draws',type=int,default=10000);a=p.parse_args()
    r=read(a.records);write_new(a.out,analyze(read(a.panel),r['lane'],r,a.draws))
if __name__=='__main__':main()
