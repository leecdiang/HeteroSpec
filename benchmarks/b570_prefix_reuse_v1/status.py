"""Compact read-only progress; does not launch or select work."""
from host import *
def status():
 completed=0;reserved=0;owned=0.;pending=[];stages={};reference_checks=[]
 for unit in sorted((ROOT/'units').iterdir()):
  if not (unit/'BUDGET.json').exists():continue
  b=read(unit/'BUDGET.json');reserved+=b['requests']
  path=unit/'native/result.json';n=read(path) if path.exists() else {};rpath=unit/'RECEIPT.json'
  if rpath.exists():
   r=read(rpath);owned+=r['owned_seconds'];done=sum(x.get('kind')!='admit' for x in read(unit/'JOB.json')['slots'][:len(n.get('records',[]))]);completed+=done;stages[b['stage']]=stages.get(b['stage'],0)+done
   if not r['success']:pending.append(dict(unit=unit.name,status='FAILED',error=n.get('error')))
   if unit.name.startswith('main-reference-') and len(n.get('records',[]))==2:
    a,z=n['records'];reference_checks.append(a['vectors']==z['vectors'] and a['endpoint']==z['endpoint'])
  else:pending.append(dict(unit=unit.name,status=n.get('status','starting'),completed_slots=len(n.get('records',[])),reserved=b['requests']))
 return dict(completed_requests=completed,reserved_requests=reserved,owned_seconds=round(owned,2),stages=stages,main_original_pairs_complete=len(reference_checks),main_original_pairs_equal=sum(reference_checks),pending=pending,source_policy_freeze=(ROOT/'SOURCE_POLICY_FREEZE.json').exists(),common_release=(ROOT/'COORDINATION_RELEASE.json').exists())
if __name__=='__main__':print(json.dumps(status()))
