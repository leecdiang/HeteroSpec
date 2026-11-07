"""Held-out prediction and the incremental contrast attributable to crossing a boundary."""
import math,statistics
from recompute import pairs,gmean
def crossing_contrast(times):
    d={}
    for r in times:
        if r['arm'] not in ('WB','QB') or not r['seconds'] or not r['qualified']:continue
        k=(r['family'],r['C'],r['B'],r['q'],r['rep'])
        d.setdefault(k,{})[(len(r['groups'])>1,r['arm'])]=r['seconds']
    matched=[]
    for k,v in d.items():
        if len(v)!=4:continue
        cross=v[True,'WB']/v[True,'QB'];inside=v[False,'WB']/v[False,'QB']
        matched.append(dict(key=k,cross=cross,inside=inside,ratio=cross/inside))
    return matched
def forecast(times):
    # Fixed before measured repetitions. Stratify by width and crossing status.
    def where(r,training,family):
        if family=='smol':return r['family']=='smol' and r['B']==(256 if training else 2048)
        return (r['family']=='qwen' and r['C']==1024) if training else r['family']=='qwen_target' and r['C']==4096
    reports={}
    for family in ('smol','qwen'):
        sub=[r for r in times if where(r,True,family)]
        held=[r for r in times if where(r,False,family)]
        rows=[]
        for q in (2,4,8,16,32):
            for crossing in (False,True):
                def one(data):
                    cells=[r for r in data if r['q']==q and (len(r['groups'])>1)==crossing]
                    return pairs(cells,'WB','QB',['C','B','head','q','rep'])
                fit=one(sub);test=one(held);pred=fit['geometric_ratio']
                for p in test['pairs']:
                    rows.append(dict(q=q,cross=crossing,heldout_key=p['key'],estimate=pred,actual=p['ratio'],absolute_log_error=abs(math.log(pred/p['ratio'])) if pred else None))
        err=[r['absolute_log_error'] for r in rows if r['absolute_log_error'] is not None]
        reports[family]=dict(training='B256' if family=='smol' else 'resident pair C1024',test='B2048 same deployment' if family=='smol' else 'separate target-only C4096 deployment',median_absolute_log_error=statistics.median(err) if err else None,rows=rows)
    return reports
