"""Old-input instrumentation and physical crossing controls; never main inputs."""
from campaign import *
def controls():
 old=read(OLD/'NATURAL_PANEL.json')['rows']
 r0=next(r for r in sorted(old,key=lambda r:r['id']) if len(r['prompt_ids'])>=320)
 r=dict(id='development/'+r0['id'],root_id='historical-not-OASST',request_ids=r0['prompt_ids'],effective_head=253)
 entry=cache_for(r,0,'development-crossing');checks=[]
 # Known-token rows change output projection shape and remain a labeled probe.
 slots=[slot(r,'S1',True,all_append_logits=True,phases=True,cap=1)]
 n=run('development-append-vectors-R','reference-01',slots,'development',cache=[entry]);assert n['status']=='COMPLETE';ref=n['records'][0]
 slots=[slot(r,a,True,all_append_logits=True,phases=True,cap=1) for a in study.FIXED]
 n=run('development-append-vectors-C','candidate-02',slots,'development',cache=[entry]);assert n['status']=='COMPLETE'
 for a,c in zip(study.FIXED,n['records'],strict=True):
  expected=study.plan(253,len(r['request_ids'])-253,a)
  actual=[{k:x[k] for k in ('head','width')} for x in c['append_calls']]
  require=actual==[{k:x[k] for k in ('head','width')} for x in expected]
  p=check_pair(ref,c);checks.append(dict(probe='all_known_rows_not_service',arm=a,native_plan_equal=require,comparison=p,passed=require and passed(p)))
 ss=[slot(r,'S1',h,phases=True) for h in (True,False)]
 nr=run('development-service-R','reference-01',ss,'development',cache=[entry]);assert nr['status']=='COMPLETE'
 ss=[slot(r,a,h,phases=True) for a in study.FIXED for h in (True,False)]
 nc=run('development-service-C','candidate-02',ss,'development',cache=[entry]);assert nc['status']=='COMPLETE'
 for j,a in enumerate(study.FIXED):
  c,off=nc['records'][j*2:j*2+2];p=check_pair(nr['records'][0],c);control=check_pair(c,off,False)
  checks.append(dict(probe='ordinary_service_flags',arm=a,comparison=p,observer=control,passed=passed(p) and passed(control)))
 write(ROOT/'DEVELOPMENT_CONTROLS.json',dict(utc=utc(),source_input_id=r0['id'],purpose='old-input physical crossing/owned-vector/observer qualification, excluded from scientific panel',head=253,checks=checks))
 assert all(x['passed'] for x in checks),'Retained development failure; no timing claim'
if __name__=='__main__':controls()
