"""Frozen finite-panel analysis and qualification gate; no native calls."""
import collections,csv,hashlib,json,math,statistics,sys
from pathlib import Path
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def gm(values):return math.exp(statistics.fmean(math.log(x) for x in values))
def gate(root):
    rows=[]
    for i in range(4):
        q=read(root/f'qual-{i}/result.json');assert q['status']=='QUALIFICATION_PASS'
        for r in q['requests']:
            if r['label']=='R':continue
            nodes=[n for n in r['geometry'] if n['name'].startswith('kq-') and n['op']=='MUL_MAT']
            layers={int(n['name'].rsplit('-',1)[1]) for n in nodes}
            assert layers==set(range(36)),('layers',i,r['label'],layers)
            expected=2 if r['label']=='QB' else 1
            assert all(n['ne'][0] in (256,512) and n['ne'][1:]==[1,32,expected] for n in nodes),('actual QK geometry',i,r['label'])
            assert all(n['sources'][0]['ne'][2]==8 and n['sources'][1]['ne'][2]==32 for n in nodes)
            assert r['target_physical_width_hist'].get('2',0)>0
            rows.append(dict(input_id=r['input_id'],arm=r['label'],target_layers=36,caller_rows=2,physical_attention_q=expected,
                             key_extents=sorted({n['ne'][0] for n in nodes}),state_and_logits='PASS'))
    result=dict(status='ALL_QUALIFIED',rows=rows,reference_type='NEW_PROSPECTIVE_REFERENCE; historical endpoints separately matched')
    (root/'QUALIFICATION_GATE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
def timing(root):
    gate(root);requests=[];blocks=[]
    for session in range(4):
        d=read(root/f'time-{session}/result.json');assert d['status']=='TIMING_PASS'
        assert len(d['requests'])==32
        for r in d['requests']:requests.append(dict(session=session,**r))
        for task in range(4):
            r={x['label']:x for x in d['requests'] if x['category']=='measured' and x['task']==task};assert len(r)==4
            a,b,q,t=[r[k]['service_seconds'] for k in ('PQ_A','PQ_B','QB','R')];dual=(a+b)/2
            blocks.append(dict(session=session,task=task,input_id=r['R']['input_id'],R=t,PQ_A=a,PQ_B=b,QB=q,
                               QB_dual_PQ=q/dual,QB_R=q/t,PQ_R=dual/t,PQ_A_PQ_B=a/b))
    inputs=[]
    for task in range(4):
        b=[x for x in blocks if x['task']==task]
        inputs.append(dict(task=task,input_id=b[0]['input_id'],QB_dual_PQ=gm(x['QB_dual_PQ'] for x in b),
                           QB_R=gm(x['QB_R'] for x in b),PQ_R=gm(x['PQ_R'] for x in b),PQ_A_PQ_B=gm(x['PQ_A_PQ_B'] for x in b)))
    ratio=gm(x['QB_dual_PQ'] for x in inputs);econ=gm(x['QB_R'] for x in inputs)
    imbalance=max(abs(x['PQ_A_PQ_B']-1) for x in inputs);threshold=max(.02,imbalance)
    sessions=[dict(session=s,QB_dual_PQ=gm(x['QB_dual_PQ'] for x in blocks if x['session']==s)) for s in range(4)]
    practical=(1-ratio)>threshold and all(x['QB_dual_PQ']<1 for x in sessions)
    result=dict(status='COMPLETE_FINITE_PANEL',measured=64,warmups=64,all_requests=len(requests),
        primary_QB_dual_PQ=ratio,reduction=1-ratio,largest_input_AA_imbalance=imbalance,engineering_threshold=threshold,
        sessions=sessions,inputs=inputs,screen='ESTABLISHED_PRACTICAL_PANEL_BENEFIT' if practical else 'NO_ESTABLISHED_PRACTICAL_LAYOUT_BENEFIT',
        QB_target_only=econ,PQ_target_only=gm(x['PQ_R'] for x in inputs),
        speculative_economics='REPAYS_ON_PANEL' if econ<1 else 'DOES_NOT_REPAY_ON_PANEL',
        E3='NOT_NEEDED_STOPPING_SCREEN' if not practical or econ>1.02 else 'CONSIDER_SPARSE_PROFILE',
        all_blocks_retained=True,equivalence_claim=False,population_inference=False)
    (root/'ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for name,data in [('BLOCKS.csv',blocks),('TIMING_TABLE.csv',[dict(session=x['session'],task=x['task'],input_id=x['input_id'],label=x['label'],category=x['category'],
              service_seconds=x['service_seconds'],request_seconds=x['request_seconds'],length=x['length'],stop_reason=x['stop_reason']) for x in requests])]:
        with (root/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    return result
if __name__=='__main__':print(json.dumps(gate(Path(sys.argv[2])) if sys.argv[1]=='gate' else timing(Path(sys.argv[2])),indent=2))
