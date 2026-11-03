"""Compare actual intermediate tensors at the first qualified/nonqualified boundary."""
from experiment import *
from collections import Counter
def observe(fam,C,B,q,cross,role,arms,capture=False,profile=False):
    point=next(p for p in read(PLAN)[config(fam,C)] if p['B']==B and p['q']==q and (len(p['groups'])>1)==cross)
    rows={}
    for a in arms:
        name=f'trace-{role}-{fam}-{C}-h{point["head"]}-q{q}-{a}-d{int(capture)}p{int(profile)}'
        s=slot(fam,C,point,a,True,True)
        n=run(name,role,job(fam,C,[s],dispatch=True,profile=profile,capture=capture),allow_failure=True)
        if not n.get('records'):continue
        u=ROOT/'units'/name;r=n['records'][0];log=(u/'SUPERVISOR.stderr.log').read_text(encoding='utf-8',errors='replace')
        region=log.split('TP_BEGIN ',1)[1].split('TP_END',1)[0]
        ds=Counter(x for x in region.splitlines() if x.startswith('TP_DISPATCH '))
        captures=[v for v in r['nodes'] if 'capture' in v]
        rows[a]=dict(unit=name,trace_calls=r['trace_calls'],dispatches=sum(ds.values()),kernels=dict(ds),captures=captures,
            projection=[x for x in region.splitlines() if x.startswith('HS_PROJECTION')][:4],attn=[x for x in region.splitlines() if x.startswith('HS_ATTENTION')][:2],
            layer0_nodes=[z for z in r['nodes'] if z.get('op') and z['name'].endswith('-0')],vectors=r['vectors'])
    put_once(ROOT/f'DIAG-{role}-{fam}-{C}-h{point["head"]}-q{q}-d{int(capture)}p{int(profile)}.json',rows)
    return rows
def inspect(rows):
    # np views follow the actual tensor byte strides and keep query columns separate.
    import numpy as np
    def value(row,c):
        buf=(ROOT/'units'/row['unit']/'native'/c['capture']).read_bytes()
        return np.ndarray(shape=c['ne'],dtype='<f4',buffer=buf,strides=c['nb'])
    for field in ('qk','prob','av','final'):
        p=rows['PQ'];b=rows['QB']
        left=[c for c in p['captures'] if c['name']==f'hs_pq_{field}-0']
        right=[c for c in b['captures'] if c['name']==f'hs_qb_{field}-0']
        if not left or not right:continue
        if field=='final':
            a=value(p,left[0]);bb=value(b,right[0]);print(field,a.shape,bb.shape,np.array_equal(a,bb),flush=True);continue
        a=np.concatenate([value(p,c) for c in left],axis=3);bb=value(b,right[0])
        print(field,a.shape,bb.shape,'different per row',np.sum(a.view('u4')!=bb.view('u4'),axis=(0,1,2)).tolist(),flush=True)
if __name__=='__main__':inspect(observe('smol',4096,256,8,False,'candidate-capture',['PQ','QB'],True))

