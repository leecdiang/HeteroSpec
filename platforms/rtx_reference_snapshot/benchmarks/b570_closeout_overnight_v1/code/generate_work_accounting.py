"""CPU derivation of observed work; no executor imports or model requests."""
from pathlib import Path
import json,csv,hashlib,collections
ROOT=Path(__file__).parent
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def derive(root):
 rows=[]
 for path in sorted((root/'raw').glob('*/RESULT.json')):
  result=read(path);capture=next(root/name for name in result['files'] if name.endswith('/capture.json'))
  assert hashlib.sha256(capture.read_bytes()).hexdigest()==result['files'][str(capture.relative_to(root)).replace('\\','/')]
  raw=read(capture);work=raw['work'];trace=raw['trace'];metrics=result['metrics'];cfg=result['config'];graphs=[(call,g) for call in trace if call['event']=='decode' for g in call['graphs'] if g['tensor']=='embd']
  assert all(isinstance(v,int) and v>=0 for v in work.values())
  if trace:
   for role in ['target','draft']:assert sum(c['event']=='decode' and c['role']==role for c in trace)==work[role+'_calls']
  rows.append({'unit_id':result['unit_id'],'stage':result['unit_id'].split('/')[0],'task':result['task'],'label':cfg.get('label','LEGACY_FIXED_NATIVE_K2' if cfg['native'] else 'LEGACY_TARGET'),'k':cfg.get('k',2 if cfg['native'] else 0),'k_status':'declared' if 'k' in cfg else 'legacy fixed native k2 / no-draft target; pinned source contract','target_prefill_ub':cfg['prefill'],'target_continuation_ub':cfg['ub'],'cap':cfg.get('cap',128),'warm':result['warm'],'capture_enabled':cfg.get('capture',False),'drafted':metrics.get('drafted'),'accepted':metrics.get('accepted'),'accepted_over_drafted':metrics.get('accepted',0)/metrics['drafted'] if metrics.get('drafted',0)>0 else None,**work,'authentic_state_transfer_count':int(bool(raw['transfer'])),'observed_target_micrographs':sum(c['role']=='target' for c,g in graphs) if trace else None,'observed_draft_micrographs':sum(c['role']=='draft' for c,g in graphs) if trace else None,'synchronization_count':None,'synchronization_count_status':'MISSING: observer records caller/graph/KV mutations but not every synchronization; synchronization is included in frozen C++ timing boundary','capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest()})
 return sorted(rows,key=lambda r:r['unit_id'])
rows=derive(ROOT)
restore=Path(read(ROOT/'ARCHIVE_RESTORE.json')['restore'])
assert derive(restore)==rows,'Work derivation differs in clean restored evidence'
summary=collections.defaultdict(lambda:collections.Counter())
for row in rows:
 key=row['stage']+'/'+('warm' if row['warm'] else 'measured')
 for name in ['target_calls','draft_calls','target_caller_tokens','draft_caller_tokens','authentic_state_transfer_count']:summary[key][name]+=row[name]
 summary[key]['requests']+=1
 for name in ['drafted','accepted']:
  if row[name] is not None:summary[key][name]+=row[name]
payload={'schema':'heterospec.work-accounting.v1','model_forwards':0,'records':rows,'stage_totals':dict(summary),'clean_restored_derivation_identical':True,'records_checked':len(rows),'claims':['Caller counts are actual recorded CPU API calls, not kernel launches','Micrographs are embd-node observations in capture traces; capture-off values remain missing','Acceptance is accepted draft tokens / drafted tokens, not total output correctness','No synchronization counts inferred from source or timing']}
(ROOT/'WORK_ACCOUNTING.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
with (ROOT/'WORK_ACCOUNTING.csv').open('w',newline='',encoding='utf-8-sig') as output:
 writer=csv.DictWriter(output,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print({'records':len(rows),'restored_derivation_identical':True,'model_forwards':0},flush=True)
