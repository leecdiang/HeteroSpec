"""Reconstruct committed rows, conditional vectors and transactions from CAS."""
from array import array
from pathlib import Path
import argparse, json
from execute import ROOT, OLD, IDS, read, write, sha

def unpack(row, payload=None):
    endpoint=row['endpoint'];tokens=endpoint['ids'];assert len(tokens)==endpoint['length']==len(endpoint['eog'])
    assert tokens[-1]==endpoint['terminal_id'] and not any(endpoint['eog'][:-1])
    assert endpoint['stop_reason']==('EOG' if endpoint['eog'][-1] else 'CAP')
    expected={'target_initial':tokens[0]};committed=['target_initial'];emitted=[tokens[0]]
    if row['cycles']:
        base=len(row['target_caller_trace'][0]['ids']) if row['target_caller_trace'] else None
        base=row['cycles'][0]['base']
        for i,c in enumerate(row['cycles']):
            assert c['cycle']==i and c['base']==base and c['seed_id']==emitted[-1]
            assert c['batch_ids']==[emitted[-1],c['proposal']] and len(c['decisions'])==2
            match=int(c['proposal']==c['decisions'][0]);assert c['accepted']==match
            part=c['decisions'][:min(1+match,len(tokens)-len(emitted))]
            assert part==c['committed_ids'] and len(part)>0
            expected[f'draft_proposal/{i}']=c['proposal']
            for j,t in enumerate(c['decisions']):expected[f'target_verify/{i}/{j}']=t
            committed += [f'target_verify/{i}/{j}' for j in range(len(part))]
            emitted+=part;base+=1+match
            assert c['keep']==base and c['target_kv_max']==c['draft_kv_max']==base-1
        assert emitted==tokens
    else:
        for i,t in enumerate(tokens[1:],1):
            key=f'target_ordinary/{i}';expected[key]=t;committed.append(key)
    vec=row['vectors']
    if vec:
        assert set(vec)==set(expected)
        if payload:
            for k,m in vec.items():
                p=payload/m['path'];assert p.stat().st_size==151936*4 and sha(p)==m['sha256']
                a=array('f');a.frombytes(p.read_bytes());assert a.index(max(a))==expected[k]
    return [vec[k]['sha256'] for k in committed] if vec else []

def signature(row):
    return {k:row[k]['sha256'] for k in ('kv','initial_logits')}

def compare(index,unit):
    u=ROOT/'units'/unit
    slots=read(u/'JOB.json')['slots'];rows=read(u/'native/result.json')['requests']
    old=read(OLD/f'run-primary/B1-{index}/result.json')['requests'];ref=read(ROOT/f'units/original-{index}/native/result.json')['requests'][0]
    reference=unpack(ref);cells=[];pairs={}
    for s,r in zip(slots,rows,strict=True):
        v=unpack(r,u/'payload');first=next((i for i,(a,b) in enumerate(zip(v,reference)) if a!=b),None)
        token=next((i for i,(a,b) in enumerate(zip(r['endpoint']['ids'],ref['endpoint']['ids'])) if a!=b),None)
        baseline_state=old[2]['boundary'] if s['producer']=='P1' else old[5]['boundary']
        state=r.get('restored_boundary',r.get('boundary'))
        cell={'input':s['input_id'],'producer':s['producer'],'consumer':s['consumer'],'route':s['route'],'endpoint_equal':r['endpoint']==ref['endpoint'],'first_different_token':token,'committed_vectors':len(v),'first_different_committed_vector':first,'all_committed_equal':v==reference,'vs_historical_producer_boundary':signature(state)==signature(baseline_state) if state else None,'equals_historical_P1':signature(state)==signature(old[2]['boundary']) if state else None}
        if s['route']=='resumed':
            assert signature(state)==signature(next(x['boundary'] for x in rows if x['slot_id']==s['donor_slot_id']))
            pairs.setdefault(s['producer'],[]).append(r)
        cells.append(cell)
    return {'cells':cells,'PQ_QB_full_correspondence':{p:len(v)==2 and v[0]['cycles']==v[1]['cycles'] and v[0]['vectors']==v[1]['vectors'] for p,v in pairs.items()}}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('build');a.add_argument('index',type=int);args=a.parse_args()
    u=f'retained-{args.index}-{args.build}';result=compare(args.index,u);write(ROOT/'units'/u/'COMPARISON.json',result);print(json.dumps(result))

