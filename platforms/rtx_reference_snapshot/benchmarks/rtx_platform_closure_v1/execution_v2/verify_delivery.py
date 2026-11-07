"""Reconstruct the panel estimator from compact native records without model execution."""
import csv,gzip,json,math,statistics
from pathlib import Path
root=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
records=[];ratios=[];economics=[];aa=[];session_gains=[]
for s in range(4):
    with gzip.open(root/f'time_evidence/time-{s}.json.gz','rt',encoding='utf-8') as f:d=json.load(f)
    assert d['status']=='TIMING_PASS' and d['normal_cleanup_returned'] and len(d['requests'])==32
    records+=d['requests'];local=[]
    for task in range(4):
        group={r['label']:r for r in d['requests'] if r['task']==task and r['category']=='measured'}
        assert set(group)=={'R','PQ_A','PQ_B','QB'}
        a,b,q,t=[group[k]['service_seconds'] for k in ('PQ_A','PQ_B','QB','R')]
        ratios.append(q/((a+b)/2));economics.append(q/t);aa.append((task,a/b));local.append(q/((a+b)/2))
    session_gains.append(math.prod(local)**.25)
primary=math.prod(ratios)**(1/16);econ=math.prod(economics)**(1/16)
imbalance=max(abs(math.prod(v for task,v in aa if task==i)**.25-1) for i in range(4))
data=read(root/'ANALYSIS.json')
assert abs(primary-data['primary_QB_dual_PQ'])<1e-12
assert abs(econ-data['QB_target_only'])<1e-12
assert abs(imbalance-data['largest_input_AA_imbalance'])<1e-12
passed=(1-primary)>max(.02,imbalance) and all(x<1 for x in session_gains)
assert passed==(data['screen']=='ESTABLISHED_PRACTICAL_PANEL_BENEFIT')
with (root/'ALL_SLOTS.csv').open(encoding='utf-8',newline='') as f:slots=list(csv.DictReader(f))
assert len(slots)==172 and sum(x['status']=='COMPLETED' for x in slots)==148
assert read(root/'FINAL_VALIDATION.json')['status']=='PASS'
print(json.dumps(dict(status='PASS',measured=64,warmups=64,primary=primary,QB_R=econ,AA=imbalance,
                      screen=data['screen'],all_slots=172,scope='independent compact-data reconstruction; no native execution')))
