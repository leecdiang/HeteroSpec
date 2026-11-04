"""Retained slots; never fits policy or releases test outputs after failed gates."""
from host import *
sys.path.insert(0,str(HERE.parent/'tpds_prefix_reuse_v1'))
import study,selector
def data():
 panel=read(ROOT/'panel.json');rows={r['id']:r for r in read(ROOT/'manifest.json')['rows']};return panel,rows
def cache_for(r,index,stage='calibration'):
 head=r['effective_head'];name=f'{stage}-seed-{index:02d}'
 n=run(name,'reference-01',[dict(kind='seed',ids=r['request_ids'],heads=[head])],'development')
 assert n['status']=='COMPLETE';z=n['records'][0]['states'][0]
 return dict(key=r['id'],path=str(ROOT/'units'/name/'native'/f'state-{head}.bin'),head=head,sha256=z['sha256'])
def slot(r,arm,heavy,**kw):
 d=dict(kind='service',id=r['id'],root_id=r['root_id'],ids=r['request_ids'],cache_key=r['id'],arm=arm,heavy=heavy,cap=128);d.update(kw);return d
def endpoint(r):return {k:v for k,v in r['endpoint'].items() if k!='state_sha256'}
def check_pair(a,b,heavy=True):
 return dict(endpoint_equal=endpoint(a)==endpoint(b),vectors_equal=(a['vectors']==b['vectors']) if heavy else None,state_equal=a['endpoint'].get('state_sha256')==b['endpoint'].get('state_sha256') if heavy else None)
def passed(v):return all(x is True or x is None for x in v.values())
def calibration_refs():
 panel,rows=data();records=[]
 for i,z in enumerate(panel['calibration']):
  r=rows[z['id']];entry=cache_for(r,i)
  slots=[slot(r,'S1',True,cache_key='empty'),slot(r,'S1',True)]
  n=run(f'cal-reference-{i:02d}','reference-01',slots,'calibration',cache=[entry]);assert n['status']=='COMPLETE'
  pair=check_pair(*n['records']);records.append(dict(id=r['id'],pair=pair,cache=entry));print('R_REPEAT',i,pair,flush=True)
 write(ROOT/'CALIBRATION_REFERENCES.json',records);assert all(passed(x['pair']) for x in records),'Original repeat/restore failure'
def qualification():
 panel,rows=data();refs=read(ROOT/'CALIBRATION_REFERENCES.json');out=[]
 for i,z in enumerate(panel['calibration']):
  r=rows[z['id']];entry=refs[i]['cache'];original=read(ROOT/'units'/f'cal-reference-{i:02d}'/'native/result.json')['records'][1]
  slots=[slot(r,a,h) for a in study.FIXED for h in (True,False)]
  n=run(f'cal-qualification-{i:02d}','candidate-01',slots,'calibration',cache=[entry]);assert n['status']=='COMPLETE'
  for j,a in enumerate(study.FIXED):
   heavy,off=n['records'][2*j:2*j+2];p=check_pair(original,heavy);control=check_pair(heavy,off,False)
   out.append(dict(id=r['id'],arm=a,reference=p,observer=control,passed=passed(p) and passed(control)));print('QUAL',i,a,out[-1]['passed'],flush=True)
 write(ROOT/'CALIBRATION_QUALIFICATION.json',out)
 assert all(r['passed'] for r in out),'Whole calibration qualification failed; no passing subset'
def calibration_timing():
 panel,rows=data();q=read(ROOT/'CALIBRATION_QUALIFICATION.json');assert len(q)==36 and all(r['passed'] for r in q)
 source=dict(worker=sha(HERE/'worker.cpp'),candidate=read(ROOT/'candidate-01/FILES.json'),reference=read(ROOT/'reference-01/FILES.json'),panel_sha256=study.digest(panel))
 source_sha=study.digest(source)
 if not (ROOT/'CALIBRATION_SOURCE.json').exists():write(ROOT/'CALIBRATION_SOURCE.json',source)
 else:assert read(ROOT/'CALIBRATION_SOURCE.json')==source
 refs=read(ROOT/'CALIBRATION_REFERENCES.json');cache=[x['cache'] for x in refs];records=[]
 for session in range(2):
  slots=[];meta=[]
  for i,z in enumerate(panel['calibration']):
   for pos in range(3):
    arm=study.FIXED[(i+session+pos)%3]
    for kind in ('warmup','measure'):
     m=dict(id=z['id'],root_id=z['root_id'],session=session,arm=arm,kind=kind,position=pos)
     slots.append(slot(rows[z['id']],arm,False,schedule=m));meta.append(m)
  n=run(f'cal-timing-session-{session}','candidate-01',slots,'calibration',cache=cache);assert n['status']=='COMPLETE'
  for m,r in zip(meta,n['records'],strict=True):
   i=next(i for i,z in enumerate(panel['calibration']) if z['id']==m['id']);ref=read(ROOT/'units'/f'cal-reference-{i:02d}'/'native/result.json')['records'][1]
   records.append(dict(m,seconds=r['seconds'],qualified=endpoint(ref)==endpoint(r),source_freeze_sha256=source_sha))
 costs=[read(p) for p in (ROOT/'units').glob('cal*/RECEIPT.json')]
 cal=dict(stage='calibration',panel_sha256=study.digest(panel),deployment_id=panel['deployment_id'],source_freeze_sha256=source_sha,calibration_total_seconds=sum(x['owned_seconds'] for x in costs),records=records)
 write(ROOT/'calibration.json',cal);policy=selector.fit(cal,panel);write(ROOT/'policy.json',policy)
 write(ROOT/'SOURCE_POLICY_FREEZE.json',dict(utc=utc(),status='NATIVE_CALIBRATION_SOURCE_POLICY_FROZEN',source=source,source_sha256=source_sha,policy=policy,policy_sha256=study.digest(policy),panel_sha256=study.digest(panel),calibration_sha256=sha(ROOT/'calibration.json'),qualification_sha256=sha(ROOT/'CALIBRATION_QUALIFICATION.json'),main_output_exposures=0,shared_test_gate='Require counterpart authentic freeze and exact cohort/token identity before launch'))
if __name__=='__main__':{'references':calibration_refs,'qualify':qualification,'calibrate':calibration_timing}[sys.argv[1]]()
