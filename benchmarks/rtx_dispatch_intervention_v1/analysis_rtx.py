"""CPU paired analysis. No GPU entrypoints; blocks, not inner calls, are resampled."""
import math,statistics as st,random
from collections import defaultdict
def summary(pairs, draws):
    if not pairs:
        return dict(blocks=0,sessions=0,ratio=None,difference_us=None,interval=None,pairs=[])
    blocks=[x['block'] for x in pairs]
    if len(blocks)!=len(set(blocks)):raise ValueError('duplicate statistical block')
    strata=defaultdict(list)
    for x in pairs:strata[x['session']].append(x)
    logs=[x['log_ratio'] for x in pairs]
    out=dict(blocks=len(pairs),sessions=len(strata),ratio=math.exp(st.mean(logs)),
             difference_us=st.mean(x['difference_us'] for x in pairs),interval=None,pairs=pairs,
             leave_one_block_out=[math.exp(st.mean(logs[:i]+logs[i+1:])) for i in range(len(logs))] if len(logs)>1 else [])
    if len(pairs)>=4:
        rng=random.Random(20261018); boot=[]
        for _ in range(draws):
            picked=[x for key in sorted(strata) for x in rng.choices(strata[key],k=len(strata[key]))]
            boot.append(math.exp(st.mean(x['log_ratio'] for x in picked)))
        boot.sort();out['interval']=[boot[math.ceil(.025*draws)-1],boot[math.ceil(.975*draws)-1]]
    out['scope']='complete two-session descriptive' if len(pairs)==8 and len(strata)==2 else 'partial/single-session descriptive'
    return out


def average(groups):
    if not groups:return []
    maps=[{p['block']:p for p in group} for group in groups]
    common=set.intersection(*(set(m) for m in maps)); result=[]
    for b in sorted(common):
        pp=[m[b] for m in maps]
        if len({p['session'] for p in pp})!=1:raise ValueError('unpaired sessions')
        result.append(dict(block=b,session=pp[0]['session'],log_ratio=st.mean(p['log_ratio'] for p in pp),
                           difference_us=st.mean(p['difference_us'] for p in pp)))
    return result



def analyze(plan,hosts,draws=4000):
    tasks={t['task_id']:t for t in plan['timed_jobs']};seen=set();groups=defaultdict(dict);coverage=[]
    for h in hosts:
        tid=h['task_id'];assert tid in tasks and tid not in seen,'unknown/duplicate timing';seen.add(tid);t=tasks[tid]
        assert h['arm']==t['arm'] and h['cell']==t['cell'] and h['block']==t['block'] and h['planned_session']==t['session'],'treatment/order drift'
        v=h['values_us'];assert all(type(x) in (float,int) and math.isfinite(x) and x>0 for x in v),'invalid timings'
        if h['eligible']:
            assert len(v)==30 and h['actual_session'],'count/session'
            groups[t['cell'],t['block']][t['arm']]=(st.mean(v),h['actual_session'])
    for tid,t in tasks.items():coverage.append(dict(task_id=tid,cell=t['cell'],arm=t['arm'],block=t['block'],started=tid in seen))
    pairs=defaultdict(list);baseline_means=defaultdict(list)
    for c in plan['cells']:
        names=[a['name'] for a in c['arms']];contrasts=[('AA',names[0],names[1])]+[(x+'/'+z,x,z) for x in names[2:] for z in names[:2]]
        if c['panel']=='T0':contrasts.append(('QH_compact/QH_permuted','QH_compact','QH_permuted'))
        for b in range(8):
            g=groups.get((c['id'],b),{})
            for label,a,z in contrasts:
                if a in g and z in g:
                    x,y=g[a],g[z];assert x[1]==y[1],'unpaired session'
                    pairs[c['id'],label].append(dict(block=b,session=x[1],log_ratio=math.log(x[0]/y[0]),difference_us=x[0]-y[0]))
                    baseline_means[c['id'],label].append(y[0])
    cell={cid+'|'+label:summary(pp,draws) for (cid,label),pp in pairs.items()}
    geometries={}
    for panel in ['B0','T0']:
        for extent in sorted({c['logical'] if panel=='B0' else c['q'] for c in plan['cells'] if c['panel']==panel}):
            cs=[c for c in plan['cells'] if c['panel']==panel and (c['logical'] if panel=='B0' else c['q'])==extent];assert len(cs)==2
            labels={k[1] for k in pairs if k[0] in [c['id'] for c in cs]};aap=average([pairs.get((c['id'],'AA'),[]) for c in cs]);aa=st.median(abs(p['difference_us']) for p in aap) if aap else None
            comparisons={}
            for label in sorted(labels):
                pp=average([pairs.get((c['id'],label),[]) for c in cs]);row=summary(pp,draws);row['AA_scale_us']=aa
                per_session={}
                for c in cs:
                    for sess in sorted({x['session'] for x in pairs.get((c['id'],label),[])}):
                        rr=[x for x in pairs[c['id'],label] if x['session']==sess];per_session[c['id']+'|'+sess]=dict(ratio=math.exp(st.mean(x['log_ratio'] for x in rr)),difference_us=st.mean(x['difference_us'] for x in rr))
                row['per_value_session']=per_session
                row['baseline_mean_us']=st.mean([x for c in cs for x in baseline_means.get((c['id'],label),[])]) if pp else None
                row['threshold_us']=max(1.,.02*row['baseline_mean_us'],aa) if pp and aa is not None else None
                row['screen_pass']=bool(len(pp)==8 and len(per_session)==4 and all(x['difference_us']<0 for x in per_session.values()) and row['interval'] and row['interval'][1]<1 and -row['difference_us']>row['threshold_us'])
                comparisons[label]=row
            controls=[a['name'] for a in cs[0]['arms'][:2]];candidates={a['name']:('PRACTICAL_CANDIDATE' if all(comparisons.get(a['name']+'/'+z,{}).get('screen_pass',False) for z in controls) else 'NOT_ESTABLISHED') for a in cs[0]['arms'][2:]}
            geometries[panel+'-'+str(extent)]=dict(comparisons=comparisons,candidates=candidates)
    return dict(cells=cell,geometries=geometries,coverage=coverage,statistical_unit='whole block stratified by actual session;two values averaged equally;30 inner calls technical repeats',draws=draws)
