"""Direct independent StageA parser; never imports executor comparisons."""
from pathlib import Path
import json,hashlib
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 errors=[];checks=0
 def ck(x,m):
  nonlocal checks;checks+=1
  if not x:errors.append(m)
 hist=load(R/'HISTORICAL_PARENTS.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);schedule=load(R/'A_SCHEDULE.json');records=[];details=[]
 for si,s in enumerate(schedule):
  for ri,inp in enumerate(s['inputs']):
   u=f'A/{si}/{ri}/{inp["id"]}';p=R/'raw'/hashlib.sha256(u.encode()).hexdigest()[:20]/'RESULT.json'
   ck(p.exists(),'missing '+u)
   if not p.exists():continue
   r=load(p);ck(r['unit_id']==u and not r['warm'] and r['config']==s['config'],'schedule '+u)
   for f,h in r['files'].items():ck(sha(R/f)==h,'payload '+f)
   raw=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ids=raw['ids'];flags=raw['eog'];ck(raw['prompt_ids']==inp['prompt_ids'],'input '+u)
   ck(len(ids)==len(flags)>0 and all(type(i)==int and 0<=i<151936 for i in ids),'vocab '+u);ck(flags==[i in eog for i in ids],'runtime EOG '+u)
   n=min(128,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)))
   ep=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n)
   ck(ep==r['endpoint'],'complete endpoint '+u)
   old=hist.get(inp['id']+'/'+s['config']['label']);bridge=None
   if old:
    bridge=all(ep[k]==old['endpoint'][k] for k in ['ids','eog','reason']);ck(bridge,'historical endpoint '+u)
    if 'raw_ids' in old:ck(ids==old['raw_ids'] and flags==old['raw_eog'],'historical raw array '+u)
   ref=hist[inp['id']+'/R_reference']['endpoint'];qualified=all(ep[k]==ref[k] for k in ['ids','eog','reason'])
   diff=next((i for i,(a,b) in enumerate(zip(ep['ids'],ref['ids'])) if a!=b),None)
   if diff is None and len(ep['ids'])!=len(ref['ids']):diff=min(len(ep['ids']),len(ref['ids']))
   details.append(dict(unit=u,task=inp['id'],label=s['config']['label'],round=s['config']['round'],historical_bridge=bridge,source='retained history' if old else 'new natural parent, observation switch only',R_qualified=qualified,first_difference=diff,raw_length=len(ids),endpoint_length=n,reason=ep['reason'],checkpoint_count=sum(f.endswith('.json') and '.cp-' in f for f in r['files'])))
   log=(R/'sessions'/r['session']/'stderr.log').read_text(encoding='utf8',errors='replace');ck('using device' in log and 'Intel(R) Arc(TM) B570 Graphics' in log and 'offloaded 37/37 layers to GPU' in log,'actual target B570 '+u)
   if s['config']['native']:ck('offloaded 29/29 layers to GPU' in log and log.count('(Intel(R) Arc(TM) B570 Graphics)')>=2,'actual target and draft B570 '+u)
   records.append((r,raw))
 for task in {d['task'] for d in details}:
  for label in {d['label'] for d in details if d['task']==task}:
   xs=[raw for r,raw in records if r['task']==task and r['config']['label']==label];ck(len(xs)==2,'two capture rounds '+task+'/'+label)
   if len(xs)==2:ck(xs[0]['ids']==xs[1]['ids'] and xs[0]['eog']==xs[1]['eog'],'capture switch raw stable '+task+'/'+label)
 ck(len(records)==48,'A48')
 result=dict(status='PASS' if not errors else 'BLOCKED_BRIDGE',checks=checks,errors=errors,nonwarm=len(records),expected=48,details=details,known_scientific_failures_retained=[d for d in details if not d['R_qualified']],new_parents=[d for d in details if d['historical_bridge'] is None],timing_scope='diagnostic; capture-off still has bounded checkpoints, no speed claim')
 save('A_VERIFICATION.json',result);print(result['status'],checks,errors[:10],flush=True);return result
if __name__=='__main__':main()
