#!/usr/bin/env python3
"""Recompute finite intervention comparisons from full neutral ID arrays; CPU only.
Run in an unpacked anonymous evidence directory. This validates exports, not models,
raw trace provenance, binary identities, or absolute experiment timestamps.
"""
import collections, hashlib, json, os, subprocess, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def compare(a,b):
 ids0,ids1=a['ids'],b['ids']; equal=ids0==ids1 and a['endpoint']==b['endpoint']
 first=next((i for i,(x,y) in enumerate(zip(ids0,ids1)) if x!=y),None)
 if first is None and len(ids0)!=len(ids1): first=min(len(ids0),len(ids1))
 return dict(equal=equal,first_difference_zero_based=first,left_length=len(ids0),right_length=len(ids1),left_endpoint=a['endpoint'],right_endpoint=b['endpoint'],left_id=ids0[first] if first is not None and first<len(ids0) else None,right_id=ids1[first] if first is not None and first<len(ids1) else None)

def compute(records):
 by={}
 for a in records:
  assert a['endpoint'] in ('CAP128','limit','EOS'),a
  assert a['cap']==128 and isinstance(a['ids'],list) and all(type(i)==int for i in a['ids'])
  if a['endpoint'] in ('CAP128','limit'): assert len(a['ids'])>=128
  else: assert len(a['ids'])<=128 and a['inclusive_eog']
  key=(a['study'],a['task'],a['rep'],a['condition']); assert key not in by,key;by[key]=a
 assert len(by)==1005
 rows=[];groups=collections.defaultdict(lambda:collections.Counter())
 for study,task in sorted({(a['study'],a['task']) for a in records}):
  cohort=next(a['cohort'] for a in records if a['study']==study and a['task']==task)
  pairs={'prediction_before':('P0','N0'),'prediction_after':('P1','N1'),'reference_before':('N0','R'),'reference_after':('N1','R'),'output_unchanged':('N0','N1')}
  comps={name:[compare(by[study,task,r,left],by[study,task,r,right]) for r in (1,2,3)] for name,(left,right) in pairs.items()}
  for c in ('R','P0','P1','N0','N1'): assert all(compare(by[study,task,1,c],by[study,task,r,c])['equal'] for r in (2,3)),(study,task,c)
  counts={k:sum(x['equal'] for x in v) for k,v in comps.items()}; assert counts['prediction_before']==counts['prediction_after']==3
  before,after=counts['reference_before']==3,counts['reference_after']==3
  transition={ (True,True):'match_to_match',(False,True):'restored',(True,False):'new_deviation',(False,False):'persistent_deviation'}[before,after]
  rows.append(dict(study=study,cohort=cohort,task=task,repeat_stable=True,transition=transition,**counts,comparisons=comps))
  g=groups[study+'/'+cohort];g['tasks']+=1;g['arrays_per_condition']+=3;g[transition]+=1
  for k,v in counts.items():g[k]+=v
 assert len(rows)==67
 expected={'B570/exposed24':(24,72,60,72,20,4,0,0),'RTX/old19':(19,57,51,51,16,1,1,1),'RTX/new24':(24,72,66,66,22,0,0,2)}
 for k,v in expected.items():
  g=groups[k]; assert tuple(g[n] for n in ['tasks','arrays_per_condition','reference_before','reference_after','match_to_match','restored','new_deviation','persistent_deviation'])==v,(k,g)
 return dict(schema='unified-full-array-comparisons-v1',status='PASS',formal_arrays=len(records),task_units=len(rows),groups={k:dict(v) for k,v in groups.items()},task_rows=rows)

def main():
 manifest=json.loads((ROOT/'SHA256SUMS.json').read_text())
 for n,h in manifest.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts
  assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 result=compute(json.loads((ROOT/'FORMAL_ARRAYS.json').read_text())['records'])
 assert result==json.loads((ROOT/'DERIVED.json').read_text())
 raw=json.loads((ROOT/'B570_UNTRUNCATED_NATIVE.json').read_text())['units'];assert len(raw)==144
 formal={(a['task'],a['condition'],a['rep']):a for a in json.loads((ROOT/'FORMAL_ARRAYS.json').read_text())['records'] if a['study']=='B570'}
 totals=collections.Counter()
 for a in raw:
  f=formal[a['task'],a['condition'],a['repetition']];assert a['contract_ids']==f['ids'] and a['endpoint']==f['endpoint']
  assert a['ids'][:len(f['ids'])]==f['ids'] and len(a['ids'])-len(f['ids'])==a['raw_overshoot']==f['raw_overshoot']
  totals[a['condition']]+=a['raw_overshoot']
 assert totals=={'N0':60,'N1':63}
 # Historical package is byte-preserved. Its base verifier requires its old
 # exact file set, while v090 appends separate files and a second manifest.
 with tempfile.TemporaryDirectory() as d:
  full=Path(d)/'full';base=Path(d)/'base';full.mkdir();base.mkdir()
  with zipfile.ZipFile(ROOT/'historical-v0.9.0.zip') as z:z.extractall(full)
  hm=json.loads((full/'SHA256SUMS.json').read_text())
  for n,h in hm.items():
   raw=(full/n).read_bytes();assert hashlib.sha256(raw).hexdigest()==h,n
   (base/n).parent.mkdir(parents=True,exist_ok=True);(base/n).write_bytes(raw)
  (base/'SHA256SUMS.json').write_bytes((full/'SHA256SUMS.json').read_bytes())
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
  for p in (base/'verify.py',full/'verify_v090.py'):
   completed=subprocess.run(['python','-B',str(p)],cwd=p.parent,env=env,capture_output=True,text=True,check=True)
   print(completed.stdout)
 print(json.dumps(dict(status='PASS',formal_arrays=result['formal_arrays'],task_units=result['task_units'],groups=result['groups'],limits='Export arithmetic and retained historical package only; offline raw audits reported separately.')))
if __name__=='__main__':main()
