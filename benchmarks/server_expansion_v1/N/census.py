"""Offline geometry census of observed dense append heads; no token generation.

Input rows must come from an actually bound tokenizer/cache-state census, not
selected latency outcomes. This predicts grouping, never kernel equivalence.
"""
import argparse, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared'))
from experiment import read, save, require


def groups(head,width,padding):
    require(all(type(v) is int for v in (head,width,padding)) and head>=0 and width>=0 and padding>0,'Geometry')
    out=[]
    for i in range(width):
        extent=((head+i)//padding+1)*padding
        if out and out[-1][0]==extent:out[-1][1]+=1
        else:out.append([extent,1])
    return out


def calls(head,append,q,padding,rechunk):
    require(type(q) is int and q>0 and type(append) is int and append>=0,'Caller dimensions')
    out=[];done=0
    while done<append:
        if rechunk:
            width=min(q,append-done,padding-(head+done)%padding)
            out.append(width);done+=width
        else:
            width=min(q,append-done)
            out.extend(g[1] for g in groups(head+done,width,padding));done+=width
    return out


def census(data):
    require(data.get('no_latency_selection') is True and data.get('history_origin') in ('provided_conversation','reference_generated_development') and data.get('source_sha256') and data.get('tokenizer_sha256'),'Bind source/tokenizer and distinguish supplied history from exposed reference-generated development')
    seen=set();result=[]
    for r in data['rows']:
        key=(r['root'],r['turn']);require(key not in seen,'Duplicate turn');seen.add(key)
        if r.get('dense_seq0') is not True or r.get('prefix_reusable',True) is not True or r.get('capacity_admitted',True) is not True:
            result.append(dict(r,status='UNSUPPORTED_OR_REBUILD_REQUIRED',not_dropped_from_denominator=True));continue
        observed=r.get('head_observed') is True
        require(observed or r.get('head_source')=='token_geometry_prediction','Bind actual head or label static prediction')
        h,a,q,p=(r[k] for k in ('head','append','q','padding'))
        require(all(type(v) is int for v in (h,a,q,p)) and h>=0 and a>=0 and q>0 and p>0,'Invalid dimensions')
        w=calls(h,a,q,p,False);re=calls(h,a,q,p,True)
        outer=[];done=0
        while done<a:
            n=min(q,a-done);outer.append(n);done+=n
        require(sum(w)==sum(re)==sum(outer)==a,'Token conservation')
        bound=(a+q-1)//q+1
        if p%q==0:require(len(re)<=bound,'Rechunk bound broken')
        result.append(dict(r,status='NATIVE_HEAD' if observed else 'PREDICTED_HEAD_REQUIRES_NATIVE_CHECK',whole_fixed=w,whole_rechunk=re,local_outer=outer,
            different_ordered_sequences=w!=re,rechunk_extra_calls=len(re)-len(outer),
            active_local_split=any(len(groups(h+i,min(q,a-i),p))>1 for i in range(0,a,q))))
    return dict(rows=result,roots=len({r['root'] for r in result}),turns=len(result),
          eligible_geometry_turns=sum('whole_fixed' in r for r in result),
          predicted_only_turns=sum(r['status']=='PREDICTED_HEAD_REQUIRES_NATIVE_CHECK' for r in result),
          crossings=sum(r.get('active_local_split',False) for r in result),
          distinguishing_rechunk=sum(r.get('different_ordered_sequences',False) for r in result),
          not_performance_or_numerical_evidence=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs');p.add_argument('out');a=p.parse_args();save(a.out,census(read(a.inputs)))
